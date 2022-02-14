import time
from abc import ABC, abstractmethod
from threading import Thread
from types import FunctionType
from typing import List, Tuple

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
from model.structure.Strategy import Strategy
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class StalkerClass(Strategy, MyJson, ABC):
    _CONST_STALK_FREQUENCY = 30             # in second
    _STALKER_BOT_DELFAULT_SLEEP_TIME = 10
    _STALKER_BOT_SLEEP_TIME = 10            # in second
    _CONST_MAX_STRATEGY = 20
    _BLACKLIST_TIME = 60 * 3                # in second
    _PAIR_MANAGER_NB_PERIOD = 100
    _REGEX_PAIR = r'\?\/[A-z\d]+'
    _THREAD_NAME_STALK_PARENT = 'stalk_parent'
    _THREAD_NAME_STALK_CHILD = 'stalk_child'
    _THREAD_NAME_MARKET_ANALYSE = 'market_analysing'
    _THREAD_NAME_MANAGE_TRADE = 'manage_trade_$pair'
    _GLOBAL_SAVE_INTERVAL = 10              # in second
    _STALK_N_THREAD = 5 if Config.get_stage() in [Config.STAGE_2, Config.STAGE_3] else 1
    # Color
    _TO_REMOVE_STYLE_UNDERLINE = '\033[4m'
    _TO_REMOVE_STYLE_NORMAL = '\033[0m'
    _TO_REMOVE_STYLE_BLACK = '\033[30m'
    _TO_REMOVE_STYLE_RED = '\033[31m'
    _TO_REMOVE_STYLE_GREEN = '\033[32m'
    _TO_REMOVE_STYLE_CYAN = '\033[36m'
    _TO_REMOVE_STYLE_PURPLE = '\033[35m'
    _TO_REMOVE_STYLE_YELLOW = '\033[33m'
    _TO_REMOVE_STYLE_BLUE = '\033[34m'
    _TO_REMOVE_STYLE_BACK_CYAN = '\033[46m'

    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:               {Strategy.__init__()}   # Same structure
               params[Map.period]:      {dict}                  # The period to stalk
               params[Map.strategy]:    {str}                   # Class name of Strategy to use
               params[Map.param]:       {dict}                  # Params for child Strategy to use
        """
        ks = [Map.period, Map.strategy, Map.param]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required")
        super().__init__(params)
        self.__next_stalk = None
        self.__max_strategy = None
        self.__strategy_class = None
        self.__strategy_params = None
        self.__active_strategies = None
        self._next_blacklist_clean = None
        self.__blacklist = None
        self.__stalk_thread = None
        self.__analyse_thread = None
        self.__market_analyse = None
        self._allowed_pairs = None
        self.__thread_manage_trade = None
        self.__deleted_childs = None
        self.__last_global_save = None
        # Prepare
        pair = self.get_pair()
        max_stg = self._CONST_MAX_STRATEGY
        stg_class = params.get(Map.strategy)
        child_stg_params = params.get(Map.param)
        # Set
        self._set_pair(pair)
        self._set_max_strategy(max_stg)
        self._set_strategy_class(stg_class)
        self._set_strategy_params(Map(child_stg_params))

    def _set_pair(self, pair: Pair) -> None:
        regex = self.get_regex_pair()
        pair_str = pair.format(Pair.FORMAT_SLASH)
        if not _MF.regex_match(regex, pair_str):
            raise ValueError(f"Pair must match regex '{regex}', instead '{pair_str}'")
        super()._set_pair(pair)
    
    def _set_max_strategy(self, max_strategy: int) -> None:
        if max_strategy <= 0:
            raise ValueError(f"Max active Strategy must be > 0, instead '{max_strategy}'")
        self.__max_strategy = max_strategy

    def get_max_strategy(self) -> int:
        return self.__max_strategy

    def _set_next_stalk(self, unix_time: int) -> None:
        stalk_frequency = self.get_stalk_frequency()
        round_time = _MF.round_time(unix_time, stalk_frequency)
        next_stalk = round_time + stalk_frequency
        self.__next_stalk = next_stalk

    def get_next_stalk(self) -> int:
        return self.__next_stalk

    def get_children_total(self, bkr: Broker) -> Price:
        """
        To get sum of children Strategy's total value
        NOTE: children_total = sum(children.wallet.get_total())

        Returns:
        --------
        return: Price
            Children Strategy's total value
        """
        r_asset = self.get_pair().get_right()
        stgs = self.get_active_strategies()
        stg_total = Price.sum([stg.get_wallet().get_total(bkr) for pair_str, stg in stgs.get_map().items()])
        return stg_total if stg_total is not None else Price(0, r_asset)

    def get_total(self, bkr: Broker) -> Price:
        """
        To get Strategy's total value
        NOTE: total = Stalker.wallet.get_total() + sum(children.wallet.get_total())

        Returns:
        --------
        return: Price
            Strategy's total value
        """
        stk_total = self.get_wallet().get_total(bkr)
        stg_total = self.get_children_total(bkr)
        total = stk_total + stg_total
        return total

    def get_fee(self) -> Price:
        """
        To get all fee charged on active and closed Strategy
        NOTE: fee is on StalkerClass.pair's right Asset

        Returns:
        --------
        return: Price
            All fee charged on active and closed Strategy
        """
        stk_fee = self.get_wallet().spot_fee()
        stgs = self.get_active_strategies()
        stg_fee = Price.sum([stg.get_wallet().trade_fee() for pair_str, stg in stgs.get_map().items()])
        fee = stk_fee + stg_fee if stg_fee is not None else stk_fee
        return fee
    
    def _get_strategy_capital(self) -> Price:
        """
        To get initial capital for new child Strategy
        NOTE: if max active Strategy is reached: strategy_capital == 0

        Returns:
        --------
        return: Price
            The initial capital for new Strategy
        """
        buy_capital = self.get_wallet().buy_capital()
        r_asset = buy_capital.get_asset()
        max_stg = self.get_max_strategy()
        stgs = self.get_active_strategies()
        remaining = max_stg - len(stgs.get_map())
        price_value = buy_capital/remaining if remaining > 0 else 0
        stg_capital = Price(price_value, r_asset)
        return stg_capital
    
    def _set_strategy_class(self, strategy_class: str) -> None:
        stgs_class = self.list_strategies()
        if strategy_class not in stgs_class:
            raise ValueError(f"This Strategy '{strategy_class}' don't exist")
        self.__strategy_class = strategy_class

    def get_strategy_class(self) -> str:
        """
        To get class name of the Strategy to trade\n
        :return: class name of the Strategy to trade
        """
        return self.__strategy_class

    def _set_strategy_params(self, params: Map) -> None:
        params.put(None, Map.pair)
        del params.get_map()[Map.pair]
        params.put(None, Map.capital)
        del params.get_map()[Map.capital]
        params.put(None, Map.maximum)
        del params.get_map()[Map.maximum]
        params.put(None, Map.rate)
        del params.get_map()[Map.rate]
        self.__strategy_params = params

    def get_strategy_params(self) -> Map:
        return self.__strategy_params

    def max_active_strategies_reached(self) -> bool:
        """
        To check if collection of active Strategy is full\n
        :return: True if the max Strategy manageable is reached else False
        """
        max_strategy = self.get_max_strategy()
        active_strategies = self.get_active_strategies()
        return len(active_strategies.get_map()) >= max_strategy

    def get_active_strategies(self) -> Map:
        if self.__active_strategies is None:
            self.__active_strategies = Map()
        return self.__active_strategies

    def get_active_strategy(self, pair: Pair) -> Strategy:
        stgs = self.get_active_strategies()
        return stgs.get(pair.__str__())

    def _add_active_strategy(self, pair: Pair) -> None:
        def prepare_stg_param(params: Map) -> None:
            params.put(pair, Map.pair)
            stg_capital = self._get_strategy_capital()
            params.put(stg_capital.get_value(), Map.capital)

        def add_stg(stg: Strategy) -> None:
            stk_wallet = self.get_wallet()
            child_wallet = stg.get_wallet()
            child_pair = stg.get_pair()
            child_initial = child_wallet.get_initial()
            # Add residue
            l_asset = child_pair.get_left()
            residue = stk_wallet.get_position(l_asset)
            child_wallet.add_position(residue)
            # Withdraw from Stalker
            stk_wallet.withdraw(child_initial)
            stk_wallet.remove_position(residue)

        max_strategy = self.get_max_strategy()
        active_strategies = self.get_active_strategies()
        if len(active_strategies.get_map()) >= max_strategy:
            nb_active = len(active_strategies.get_map())
            raise Exception(f"The max active strategy is already reached ({nb_active}/{max_strategy}).")
        pair_strs = active_strategies.get_keys()
        pair_str = pair.__str__()
        if pair_str in pair_strs:
            raise ValueError(f"There's already an active Strategy for this pair '{pair_str.upper()}'.")
        # Generate new Strategy
        stg_class = self.get_strategy_class()
        stg_params = self.get_strategy_params()
        prepare_stg_param(stg_params)
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        new_stg = eval(f"{stg_class}.generate_strategy(stg_class, stg_params)")
        # Add Strategy
        add_stg(new_stg)
        active_strategies.put(new_stg, pair_str)

    def _delete_active_strategy(self, bkr: Broker, pair: Pair) -> None:
        def delete_stg(stg: Strategy) -> None:
            stk_wallet = self.get_wallet()
            stg_wallet = stg.get_wallet()
            l_asset = stg.get_pair().get_left()
            # Update StalkerClass.wallet
            stg_spot = stg_wallet.get_spot()
            residue = stg_wallet.get_position(l_asset)
            fee = stg_wallet.trade_fee()
            stk_wallet.deposit(stg_spot, fee)
            stk_wallet.add_position(residue)
            # Update TraderClass.wallet
            stg_wallet.withdraw(stg_spot)
            stg_wallet.remove_position(residue)

        active_stgs = self.get_active_strategies()
        pair_str = pair.__str__()
        if pair_str not in active_stgs.get_keys():
            raise ValueError(f"There's no active Strategy with this pair '{pair_str.upper()}' to delete.")
        active_stg = active_stgs.get(pair_str)
        # Sell all positions
        active_stg.stop_trading(bkr)
        # Delete active Strategy
        delete_stg(active_stg)
        del active_stgs.get_map()[pair_str]
        self.get_deleted_childs().append(pair_str)

    def _reset_deleted_childs(self) -> None:
        self.__deleted_childs = None

    def get_deleted_childs(self) -> List[Pair]:
        """
        To get list of pair deleted since last save
        NOTE: list if reset when deletes are saved in database

        Returns:
        --------
        return: List[Pair]
            List of pair deleted since last save
        """
        if self.__deleted_childs is None:
            self.__deleted_childs = []
        return self.__deleted_childs

    def _reset_next_blacklist_clean(self) -> None:
        self._next_blacklist_clean = None

    def _set_next_blacklist_clean(self, blacklist_time: int) -> None:
        """
        To set the next time to empty the blacklist\n
        Parameters
        ----------
        blacklist_time: int
            The time to blacklist pair
        """
        if self._get_stage() == Config.STAGE_1:
            trade_index = self._get_trade_index()
            stalk_period_minute = int(blacklist_time / 60)
            index_rounded = int(trade_index / stalk_period_minute) * stalk_period_minute
            next_blacklist_clean = index_rounded + stalk_period_minute
        else:
            unix_time = _MF.get_timestamp()
            round_time = _MF.round_time(unix_time, blacklist_time)
            next_blacklist_clean = round_time + blacklist_time
        self._next_blacklist_clean = next_blacklist_clean

    def get_next_blacklist_clean(self) -> int:
        return self._next_blacklist_clean

    def get_blacklist(self) -> List[Pair]:
        next_clean = self.get_next_blacklist_clean()
        unix_time = _MF.get_timestamp() if self._get_stage() != Config.STAGE_1 else self._get_trade_index()
        if (self.__blacklist is None) or ((next_clean is not None) and (unix_time >= next_clean)):
            self.__blacklist = []
            self._reset_next_blacklist_clean()
        return self.__blacklist

    def _blacklist_pair(self, pair: Pair, blacklist_time: int = None) -> None:
        """
        To blacklist a new pair\n
        :param pair: Pair to blacklist
        """
        blacklist_time = self.get_blacklist_time() if blacklist_time is None else blacklist_time
        blacklist = self.get_blacklist()
        if pair in blacklist:
            raise ValueError(f"This pair '{pair.__str__().upper()}' already exist in blacklist.")
        blacklist.append(pair)
        self._set_next_blacklist_clean(blacklist_time)

    def _set_global_save_time(self) -> None:
        self.__last_global_save = _MF.get_timestamp()

    def _get_global_save_time(self) -> None:
        if self.__last_global_save is None:
            self.__last_global_save = 0
        return self.__last_global_save

    def _can_save_global(self) -> bool:
        last_save = self._get_global_save_time()
        interval = self._GLOBAL_SAVE_INTERVAL
        next_save = _MF.round_time(last_save, interval) + interval
        unix_time = _MF.get_timestamp()
        return unix_time >= next_save


    # —————————————————————————————————————————————— THREAD TRADE DOWN

    def _get_threads_manage_trade(self) -> Map:
        """
        To get collection of thread managing trade of child Strategy

        Returns:
        --------
        return: Map
            Collection of thread managing trade of child Strategy
            Map[Pair{str}]: {Thread}
        """
        if self.__thread_manage_trade is None:
            self.__thread_manage_trade = Map()
        return self.__thread_manage_trade

    def _reset_thread_manage_trade(self, pair: Pair) -> None:
        """
        To reset thread that manage trade of child Strategy

        Parameters:
        -----------
        pair: Pair
            Child Strategy's trading Pair
        """
        child_threads = self._get_threads_manage_trade()
        pair_str = pair.__str__()
        if pair_str in child_threads.get_keys():
            del child_threads.get_map()[pair_str]

    def _get_thread_manage_trade(self, pair: Pair) -> Thread:
        """
        To get thread that manage trade of child Strategy

        Parameters:
        -----------
        pair: Pair
            Child Strategy's trading Pair

        Returrns:
        ---------
        return: Thread
            Thread that manage trade of child Strategy
        """
        def new_thread(f_pair: Pair) -> Thread:
            f_child = self.get_active_strategy(f_pair)
            f_wrap = _MF.catch_exception
            f_wrap_kwargs = {
                'callback': self._manage_trade,
                'call_class': self.__class__.__name__,
                'repport': True,
                'bkr': self.get_broker(),
                'child': f_child
                }
            f_base_name = self._THREAD_NAME_MANAGE_TRADE.replace('$pair', f_pair.format(Pair.FORMAT_MERGED).upper())
            thread, output = _MF.generate_thread(target=f_wrap, base_name=f_base_name, **f_wrap_kwargs)
            _MF.output(f"{_MF.prefix()}{output}")
            return thread

        threads = self._get_threads_manage_trade()
        pair_str = pair.__str__()
        thread = threads.get(pair_str)
        if (thread is None) or (not thread.is_alive()):
            thread = new_thread(pair)
            threads.put(thread, pair_str)
        return thread
    
    # —————————————————————————————————————————————— THREAD TRADE UP
    # —————————————————————————————————————————————— STALK MARKET DOWN

    def _get_no_active_pairs(self, bkr: Broker) -> List[Pair]:
        allowed_pairs = self._get_allowed_pairs(bkr)
        active_strategies = self.get_active_strategies()
        pair_strs = active_strategies.get_keys()
        blacklist = self.get_blacklist()
        no_active_pairs = [pair for pair in allowed_pairs
                           if (pair.__str__() not in pair_strs) and (pair not in blacklist)]
        return no_active_pairs

    def is_stalking(self) -> bool:
        """
        To get if class is stalking market\n
        Returns
        -------
        is_stalking: bool
            True if class is stalking market else False
        """
        stalk_thread = self.get_stalk_thread()
        return (stalk_thread is not None) and stalk_thread.is_alive()

    def _set_stalk_thread(self, stalk_thread: Thread) -> None:
        self.__stalk_thread = stalk_thread

    def get_stalk_thread(self) -> Thread:
        """
        To get Thread where class is stalking the market\n
        Returns
        -------
        stalk_thread: Thread
            Thread where class is stalking the market
        """
        return self.__stalk_thread

    @staticmethod
    def _wrap_thread(target: FunctionType, base_name: str, call_class: str, repport: bool = True, target_params: dict = {}) -> Thread:
        wrap = _MF.catch_exception
        wrap_kwargs = {
            'callback': target,
            'call_class': call_class,
            'repport': repport,
            **target_params
            }
        thread, output = _MF.generate_thread(target=wrap, base_name=base_name, **wrap_kwargs)
        _MF.output(f"{_MF.prefix()}{output}")
        return thread

    def _launch_stalking(self, bkr: Broker) -> None:
        """
        To launch market stalking in its own Thread\n
        """
        def new_stalk_thread() -> Thread:
            f_params = {
                'target': self._manage_stalking,
                'base_name': self._THREAD_NAME_STALK_PARENT,
                'call_class': self.__class__.__name__,
                'repport': True,
                'target_params': {Map.broker: bkr}
            }
            return self._wrap_thread(**f_params)

        last_stalk_thread = self.get_stalk_thread()
        if (last_stalk_thread is not None) and last_stalk_thread.is_alive():
            raise Exception("Can start a stalk thread while an other is working.")
        stalk_thread = new_stalk_thread()
        self._set_stalk_thread(stalk_thread)
        stalk_thread.start()

    def _can_launch_stalking(self) -> bool:
        """
        To check if all conditions are met to stalk the market\n
        :return: True if all conditions are met else False
        """
        max_reached = self.max_active_strategies_reached()
        return not (max_reached or self.is_stalking())

    def _keep_stalkig(self) -> bool:
        """
        To get if class ca continue to stalk market\n
        Returns
        -------
        keep_stalkig: bool
            True to continue to stalk else False
        """
        stage = Config.get_stage()
        if stage in [Config.STAGE_2, Config.STAGE_3]:
            max_reached = self.max_active_strategies_reached()
            keep_stalkig = (not max_reached) and self.is_stalking()
        elif stage == Config.STAGE_1:
            keep_stalkig = False
        return keep_stalkig

    def _manage_stalking(self, broker: Broker) -> None:
        def try_sleep(next_stalk: int, end_time: int) -> None:
            sleep_time = (next_stalk - end_time) if end_time < next_stalk else None
            if sleep_time is not None:
                sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                start_sleep = _MF.unix_to_date(end_time)
                end_sleep = _MF.unix_to_date(next_stalk)
                _MF.output(f"{_MF.prefix()}Stalking Manager sleep for '{sleep_time_str}': '{start_sleep}'->'{end_sleep}'")
                time.sleep(sleep_time)

        _MF.output(f"{_MF.prefix()}Start Managing Stalking.")
        keep_stalkig = True
        while keep_stalkig:
            _MF.output(f"{_MF.prefix()}Managing Stalking...")
            _MF.output(_MF.prefix() + '\033[35m' + _MF.thread_infos() + '\033[0m')
            start_time = _MF.get_timestamp()
            self._set_next_stalk(start_time)
            self._stalk_market(broker)
            next_stalk = self.get_next_stalk()
            end_time = _MF.get_timestamp()
            keep_stalkig = self._keep_stalkig()
            if not keep_stalkig:
                continue
            else:
                try_sleep(next_stalk, end_time)
        _MF.output(f"{_MF.prefix()}End Managing Stalking.")

    def _stalk_market(self, broker: Broker) -> None:
        """
        To stalk the market

        Parameters:
        -----------
        broker: Broker
            Access to a Broker's API
        """
        _normal = self._TO_REMOVE_STYLE_NORMAL
        _black = self._TO_REMOVE_STYLE_BLACK
        _purple = self._TO_REMOVE_STYLE_PURPLE
        _back_cyan = self._TO_REMOVE_STYLE_BACK_CYAN
        pfx = _MF.prefix
        def new_thread(f_pair_group: List[Pair]) -> Thread:
            f_params = {
                'target': self._stalk_market_thread,
                'base_name': self._THREAD_NAME_STALK_CHILD,
                'call_class': self.__class__.__name__,
                'repport': True,
                'target_params': {Map.broker: broker, 'pairs': f_pair_group}
            }
            return self._wrap_thread(**f_params)

        def add_streams()  -> None:
            streams = [broker.generate_stream(Map({Map.pair: pair, Map.period: stalk_period})) for pair in pairs]
            broker.add_streams(streams)

        def group_pairs(pairs: List[Pair]) -> List[List[Pair]]:
            n_thread = self.get_stalk_n_thread()
            groups = {}
            n_pair = len(pairs)
            for i in range(1, n_pair+1):
                mod = i%n_thread
                next_pair = pairs[i-1]
                if mod in groups:
                    groups[mod].append(next_pair)
                else:
                    groups[mod] = [next_pair]
            return list(groups.values())

        _MF.output(pfx() + _back_cyan + _black + "Star stalking:".upper() + _normal)
        pairs = self._get_no_active_pairs(broker)
        stalk_period = self.get_period()
        add_streams()
        pair_groups = group_pairs(pairs)
        threads = []
        starttime = _MF.get_timestamp()
        _MF.output(pfx() + _purple + f"Stalk '{len(pairs)}' pairs in '{len(pair_groups)}' groups" + _normal)
        for pair_group in pair_groups:
            thread = new_thread(pair_group)
            thread.start()
            threads.append(thread)
        [thread.join() for thread in threads]
        endtime = _MF.get_timestamp()
        delta_time = _MF.delta_time(starttime, endtime)
        _MF.output(pfx() + _purple + f"End stalking in '{delta_time}'" + _normal)

    def _stalk_market_thread(self, broker: Broker, pairs: List[Pair]) -> None:
        _normal = self._TO_REMOVE_STYLE_NORMAL
        _cyan = self._TO_REMOVE_STYLE_CYAN
        _green = self._TO_REMOVE_STYLE_GREEN
        pfx = _MF.prefix
        n_period = broker.get_max_n_period()
        stalk_period = self.get_period()
        n_pair = len(pairs)
        repports = []
        i = 1
        for pair in pairs:
            max_not_reached = not self.max_active_strategies_reached()
            eligible = False
            if max_not_reached:
                marketprice = MarketPrice.marketprice(broker, pair, stalk_period, n_period)
                eligible, repport = self._eligible(marketprice, broker)
                repports.append(repport)
            _MF.output(pfx() + _cyan + f"[{i}/{n_pair}]Pair '{pair.__str__().upper()}' eligible: {eligible}" + _normal)
            if max_not_reached and eligible:
                self._add_active_strategy(pair)
                _MF.output(pfx() + _green + f"Add new Strategy: '{pair.__str__().upper()}'" + _normal)
            if self.max_active_strategies_reached():
                break
            i += 1
        self._save_market_stalk(repports)

    # —————————————————————————————————————————————— STALK MARKET UP
    # —————————————————————————————————————————————— ANALYSE MARKET DOWN

    def _set_market_analyse(self, market_analyse: Map) -> None:
        self.__market_analyse = market_analyse

    def get_market_analyse(self) ->  Map:
        return self.__market_analyse

    def _set_analyse_thread(self, analyse_thread: Thread) -> None:
        self.__analyse_thread = analyse_thread

    def get_analyse_thread(self) -> Thread:
        return self.__analyse_thread

    def is_analysing(self) -> bool:
        analyse_thread = self.get_analyse_thread()
        return (analyse_thread is not None) and analyse_thread.is_alive()

    def _launch_analyse(self, broker: Broker) -> None:
        """
        To launch market analyse on its own Thread\n
        """
        def new_analyse_thread() -> Thread:
            f_params = {
                'target': self._analyse_market,
                'base_name': self._THREAD_NAME_MARKET_ANALYSE,
                'call_class': self.__class__.__name__,
                'repport': True,
                'target_params': {Map.broker: broker}
            }
            return self._wrap_thread(**f_params)

        last_analyse_thread = self.get_analyse_thread()
        if (last_analyse_thread is not None) and last_analyse_thread.is_alive():
            raise Exception("Can start an analyse thread while an other is working.")
        analyse_thread = new_analyse_thread()
        self._set_analyse_thread(analyse_thread)
        analyse_thread.start()

    def _analyse_market(self, broker: Broker) -> None:
        _color_cyan = self._TO_REMOVE_STYLE_CYAN
        _normal = self._TO_REMOVE_STYLE_NORMAL
        _color_green = self._TO_REMOVE_STYLE_GREEN
        _color_black = self._TO_REMOVE_STYLE_BLACK
        _back_cyan = self._TO_REMOVE_STYLE_BACK_CYAN
        _MF.output(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Start analyse of market:" + _normal)
        market_analyse = MarketPrice.analyse_market_trend(broker)
        _MF.output(f"{_MF.prefix()}" + _color_cyan + f"End analyse of market" + _normal)
        self._set_market_analyse(market_analyse)
        _MF.output(f"{_MF.prefix()}" + _color_green + f"Market analyse updated!" + _normal)

    # ——————————————————————————————————————————————— ANALYSE MARKET UP

    def _get_sleep_time(self) -> int:
        n_stg = len(self.get_active_strategies().get_map())
        sleep_interval = self.get_bot_sleep_time() if n_stg != 0 else StalkerClass._STALKER_BOT_DELFAULT_SLEEP_TIME
        unix_time = _MF.get_timestamp()
        time_rounded = _MF.round_time(unix_time, sleep_interval)
        next_rounded_time = time_rounded + sleep_interval
        new_sleep_time = next_rounded_time - unix_time
        return new_sleep_time if new_sleep_time > 0 else 0

    def trade(self, bkr: Broker) -> int:
        self._update_nb_trade()
        self._set_broker(bkr) if self.get_broker() is None else None
        self.get_wallet().reset_marketprices()
        self.add_streams(bkr) if self._get_trade_index() == 0 else None
        self._launch_stalking(bkr) if self._can_launch_stalking() else None
        self._launch_analyse(bkr) if bkr.is_active() and (not self.is_analysing()) else None
        self.get_stalk_thread().join() if Config.get_stage() == Config.STAGE_1 else None
        self._manage_trades(bkr)
        if Config.get_stage() == Config.STAGE_1:
            threads = list(self._get_threads_manage_trade().get_map().values())
            [thread.join() for thread in threads]
        return self._get_sleep_time()

    def _manage_trades(self, bkr: Broker) -> None:
        _cls = self
        _normal = _cls._TO_REMOVE_STYLE_NORMAL
        _color_black = _cls._TO_REMOVE_STYLE_BLACK
        _color_cyan = _cls._TO_REMOVE_STYLE_CYAN
        _color_green = _cls._TO_REMOVE_STYLE_GREEN
        _color_purple = _cls._TO_REMOVE_STYLE_PURPLE
        _color_red = _cls._TO_REMOVE_STYLE_RED
        _color_yellow = _cls._TO_REMOVE_STYLE_YELLOW
        _back_cyan = _cls._TO_REMOVE_STYLE_BACK_CYAN
        #
        active_stgs_copy = Map(self.get_active_strategies().get_map())
        pairs_to_delete = self.get_deleted_childs()
        _MF.output(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Star manage strategies "
                                                              f"({len(active_stgs_copy.get_map())}):".upper() + _normal)
        self._manage_trades_add_streams(bkr, active_stgs_copy)
        market_analyse = self.get_market_analyse()
        market_trend = MarketPrice.get_market_trend(bkr, analyse=market_analyse) if market_analyse is not None else '—'
        market_analyse = Map() if market_analyse is None else market_analyse
        for _, child in active_stgs_copy.get_map().items():
            child_pair = child.get_pair()
            child_thread = self._get_thread_manage_trade(child_pair)
            child_thread.start() if not child_thread.is_alive() else None
        self._save_global(pairs_to_delete, market_trend, market_analyse) if self._can_save_global() else None

    @abstractmethod
    def _manage_trade(self, bkr: Broker, child: TraderClass) -> None:
        pass

    def _manage_trades_add_streams(self, bkr: Broker, active_stgs_copy: Map) -> None:
        pair_strs = active_stgs_copy.get_keys()
        pairs = [active_stgs_copy.get(pair_str).get_pair() for pair_str in pair_strs]
        stalk_period = self.get_period()
        stalker_streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: stalk_period})) for pair in pairs]
        bkr.add_streams(stalker_streams)
        child_period = self.get_strategy_params().get(Map.period)
        stalker_streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: child_period})) for pair in pairs]
        bkr.add_streams(stalker_streams)

    def add_streams(self, broker: Broker) -> None:
        _normal = self._TO_REMOVE_STYLE_NORMAL
        _color_cyan = self._TO_REMOVE_STYLE_CYAN
        _color_green = self._TO_REMOVE_STYLE_GREEN
        _color_black = self._TO_REMOVE_STYLE_BLACK
        _back_cyan = self._TO_REMOVE_STYLE_BACK_CYAN
        _MF.output(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Start Adding streams to socket:" + _normal)
        # Add streams
        streams = self._add_streams_get_streams(broker)
        nb_stream = len(streams)
        start_time = _MF.get_timestamp()
        duration_time = start_time + nb_stream
        start_date = _MF.unix_to_date(start_time)
        duration_date = _MF.unix_to_date(duration_time)
        duration_str = f"{int(nb_stream / 60)}min.{nb_stream % 60}sec."
        _MF.output(f"{_MF.prefix()}" + _color_cyan + f"Adding '{nb_stream}' streams for '{duration_str}' till"
                                                f" '{start_date}'->'{duration_date}'" + _normal)
        broker.add_streams(streams)
        end_time = _MF.get_timestamp()
        duration = end_time - start_time
        real_duration_str = f"{int(duration / 60)}min.{duration % 60}sec."
        _MF.output(f"{_MF.prefix()}" + _color_green + f"End adding '{nb_stream}' streams for '{real_duration_str}'"
                                                 f" (estimated:'{duration_str}')" + _normal)

    def _add_streams_periods(self) -> list:
        return [
            # MarketPrice.get_period_market_analyse(),
            self.get_period(),
            self.get_strategy_params().get(Map.period),
            Wallet.get_period()
        ]

    def _add_streams_get_streams(self, broker: Broker) -> List[str]:
        """
        To get list of stream to request to Broker
        """
        pairs = self._get_allowed_pairs(broker)
        stg_pairs = [Pair(pair_str) for pair_str in self.get_active_strategies().get_keys()]
        pairs = [
            *pairs,
            *[stg_pair for stg_pair in stg_pairs if stg_pair not in pairs]            
        ]
        periods = self._add_streams_periods()
        periods = list(dict.fromkeys(periods))
        periods.sort()
        streams = []
        for period in periods:
            streams = [
                *streams,
                *[broker.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
            ]
        """
        # Add streams for market analyse
        market_analyse_period = MarketPrice.get_period_market_analyse()
        # wallet_period = Wallet.get_period()
        spot_pairs = MarketPrice.get_spot_pairs(broker.__class__.__name__, self.get_pair().get_right())
        spot_pairs = [spot_pair for spot_pair in spot_pairs if spot_pair not in pairs]
        for spot_pair in spot_pairs:
            wallet_stream = broker.generate_stream(Map({Map.pair: spot_pair, Map.period: wallet_period}))
            spot_stream = broker.generate_stream(Map({Map.pair: spot_pair, Map.period: market_analyse_period}))
            streams.append(wallet_stream)
            streams.append(spot_stream)
        """
        streams = list(dict.fromkeys(streams))
        streams.sort()
        return streams

    def stop_trading(self, bkr: Broker) -> None:
        pass

    @staticmethod
    def _get_stage() -> str:
        return Config.get(Config.STAGE_MODE)

    @staticmethod
    def _get_trade_index() -> int:
        from model.structure.Bot import Bot
        return Bot.get_trade_index()

    @staticmethod
    def get_stalk_frequency() -> int:
        return StalkerClass._CONST_STALK_FREQUENCY

    @staticmethod
    def get_blacklist_time() -> float:
        return StalkerClass._BLACKLIST_TIME
    
    @staticmethod
    def get_regex_pair() -> str:
        return StalkerClass._REGEX_PAIR

    def _get_market_price(self, bkr: Broker, pair: Pair, period: int = None, nb_period: int = _PAIR_MANAGER_NB_PERIOD) \
            -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        _bkr_cls = bkr.__class__.__name__
        period = self.get_period() if period is None else period
        mkt_params = Map({
            Map.pair: pair,
            Map.period: period,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: nb_period
        })
        bkr_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_params)
        bkr.request(bkr_rq)
        return bkr_rq.get_market_price()

    def _get_allowed_pairs(self, bkr: Broker) -> List[Pair]:
        """
        To get pair allowed to trade with this Strategy\n
        :param bkr: Access to Broker's API
        :return: Pair allowed to trade with this Strategy
                 Map[index{int}]:   {Pair}
        """
        pass

    @abstractmethod
    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> Tuple[bool, dict]:
        """
        To check if a pair is interesting to trade\n
        
        Parameters
        ----------
        market_price: market_price
            Market price historic
        broker: Broker
            Access to Broker's API
        Returns
        -------
        eligible: bool
            True if pair is interesting else False
        """
        pass

    @staticmethod
    def get_bot_sleep_time() -> int:
        return StalkerClass._STALKER_BOT_SLEEP_TIME

    @staticmethod
    @abstractmethod
    def generate_strategy(stg_class: str, params: Map) -> 'StalkerClass':
        pass

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        rates = []
        closes = list(market_price.get_closes())
        closes.reverse()
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        switchers = MarketPrice.get_super_trend_switchers(closes, super_trends)
        nb_period = len(closes)
        switch_periods = switchers.get_keys()
        for i in range(len(switch_periods)):
            period = switch_periods[i]
            trend = switchers.get(period)
            if trend == MarketPrice.SUPERTREND_RISING:
                end_trend_period = switch_periods[i + 1] if period != switch_periods[-1] else (nb_period - 1)
                buy_close = closes[period]
                sell_close = closes[end_trend_period]
                rate = sell_close / buy_close - 1
                rates.append(rate)
        return rates

    @staticmethod
    def get_stalk_n_thread() -> int:
        """
        To get number of thread through which to stalk market

        Returns:
        --------
        return: int
            Number of thread through which to stalk market
        """
        return StalkerClass._STALK_N_THREAD

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        pass

    # ——————————————— SAVE DOWN ———————————————

    def _save_global(self, to_delete_pairs: List[str], market_trend: str, market_analyse: Map) -> None:
        pair = self.get_pair()
        bkr = self.get_broker()
        stk_wallet = self.get_wallet()
        active_stgs = self.get_active_strategies()
        #
        next_stalk = self.get_next_stalk()
        next_stalk_date = _MF.unix_to_date(next_stalk) \
            if (self._get_stage() != Config.STAGE_1) and (next_stalk is not None) else next_stalk
        #
        initial_capital = stk_wallet.get_initial()
        stk_spot = stk_wallet.get_spot()
        stk_residue = stk_wallet.get_all_position_value(bkr)
        total_capital = self.get_total(bkr)
        childs_total_capital = self.get_children_total(bkr)
        child_initial_capital = self._get_strategy_capital()
        # Roi
        roi = (total_capital / initial_capital - 1)
        settime = int(self.get_settime()/1000)
        unix_time = _MF.get_timestamp()
        roi_day = (roi/(unix_time-settime)) * 60 * 60 * 24
        run_time = _MF.delta_time(settime, unix_time)
        # Residue
        residue_init_capital_rate = stk_residue/initial_capital
        residue_total_capital_rate = stk_residue/total_capital
        #
        next_clean = self.get_next_blacklist_clean()
        analyse_empty = len(market_analyse.get_map()) == 0
        rise = f"{round(market_analyse.get(MarketPrice.MARKET_TREND_RISING)*100, 2)}%" if not analyse_empty else '—'
        drop = f"{round(market_analyse.get(MarketPrice.MARKET_TREND_DROPPING) * 100, 2)}%" if not analyse_empty else '—'
        # Fees
        total_fee = self.get_fee()
        fee_init_capital_rate = total_fee / initial_capital
        fee_total_capital_rate = total_fee / total_capital
        # Print
        row = {
            Map.index: self._get_trade_index(),
            Map.trade: self.get_nb_trade(),
            Map.id: self.get_id(),
            Map.date: _MF.unix_to_date(unix_time),
            Map.pair: pair,
            Map.strategy: self.get_strategy_class(),
            'next_stalk': next_stalk_date if next_stalk_date is not None else '—',
            'market_trend': market_trend,
            'total_pair': market_analyse.get(Map.rise) + market_analyse.get(Map.drop) if not analyse_empty else '—',
            'nb_rising': market_analyse.get(Map.rise),
            'nb_dropping': market_analyse.get(Map.drop),
            'rising': rise,
            'dropping': drop,
            'initial_capital': initial_capital,
            'total_capital': total_capital,
            'stk_spot': stk_spot,
            'stk_residue': stk_residue,
            'residue_init_capital_rate': _MF.rate_to_str(residue_init_capital_rate),
            'residue_total_capital_rate': _MF.rate_to_str(residue_total_capital_rate),
            'total_fee': total_fee,
            'fee_init_capital_rate': _MF.rate_to_str(fee_init_capital_rate),
            'fee_total_capital_rate': _MF.rate_to_str(fee_total_capital_rate),
            'childs_total_capital': childs_total_capital,
            'child_initial_capital': child_initial_capital,
            Map.roi: _MF.rate_to_str(roi),
            'roi_day': _MF.rate_to_str(roi_day),
            'run_time': run_time,
            'nb_active_strategies': len(active_stgs.get_map()),
            'max_strategy': self.get_max_strategy(),
            'active_strategies': _MF.json_encode(active_stgs.get_keys()),
            'deleted_strategies': _MF.json_encode(to_delete_pairs),
            'next_blacklist_clean': _MF.unix_to_date(next_clean) if next_clean is not None else '—',
            'blacklist': self.get_blacklist()
        }
        rows = [row]
        fields = list(row.keys())
        path = Config.get(Config.DIR_SAVE_GLOBAL_STATE)
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)
        self._reset_deleted_childs()
        self._set_global_save_time()

    def _save_market_stalk(self, datas: List[dict]) -> None:
        date = _MF.unix_to_date(_MF.get_timestamp())
        thread_name = _MF.thread_name()
        rows = []
        for data in datas:
            row = {
                Map.date: date,
                Map.thread: thread_name,
                **data
            }
            rows.append(row)
        path = Config.get(Config.DIR_SAVE_MARKET_STALK)
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    @staticmethod
    def _save_moves(rows: List[dict]) -> None:
        path = Config.get(Config.DIR_SAVE_GLOBAL_MOVES)
        path = path.replace('$class', StalkerClass.__name__)
        fields = list(rows[0].keys())
        rows.insert(0, {fields[0]: rows[0][Map.date], **{field: '⬇️ ——— ⬇️' for field in fields if field != fields[0]}})
        FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)
