import time
from abc import ABC, abstractmethod
from threading import Thread, active_count as threading_active_count
from typing import List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class StalkerClass(Strategy, MyJson, ABC):
    _CONST_STALK_FREQUENCY = 60         # in second
    _CONST_STALKER_BOT_SLEEP_TIME = 10  # in second
    _CONST_ALLOWED_PAIRS = None
    _CONST_MAX_STRATEGY = 20
    _BLACKLIST_TIME = 60 * 3  # in second
    _PAIR_MANAGER_NB_PERIOD = 100
    _THREAD_NAME_MARKET_STALKING = 'market_stalking'
    _THREAD_NAME_MARKET_ANALYSE = 'market_analysing'
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
               params[Map.strategy]:    {str}                   # Class name of Strategy to use
               params[Map.param]:       {dict}                  # Params for Strategy  to use
               params[Map.period]:      {dict}                  # The period to stalk
        """
        ks = [Map.strategy, Map.param]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required")
        super().__init__(params)
        right_symbol = self.get_pair().get_right().get_symbol()
        self._set_pair(Pair(f'?/{right_symbol}'))
        self.__next_stalk = None
        self.__transactions = None
        self.__max_strategy = self._CONST_MAX_STRATEGY
        self.__strategy_class = params.get(Map.strategy)
        child_stg_params = params.get(Map.param)
        self._set_strategy_params(Map(child_stg_params))
        self.__active_strategies = None
        self._next_blacklist_clean = None
        self.__blacklist = None
        self.__stalk_thread = None
        self.__analyse_thread = None
        self.__market_analyse = None
        self.__fees = None

    def get_max_strategy(self) -> int:
        return self.__max_strategy

    def _set_next_stalk(self, unix_time: int) -> None:
        stalk_frequency = self.get_stalk_frequency()
        round_time = _MF.round_time(unix_time, stalk_frequency)
        next_stalk = round_time + stalk_frequency
        self.__next_stalk = next_stalk

    def get_next_stalk(self) -> int:
        return self.__next_stalk

    def get_transactions(self) -> Map:
        """
        To get transaction historic\n
        Note: trace historic of final capital of Strategy added (negative transaction)
        and deleted (positive transaction)\n
        :return: transaction historic
                 Map[time_stamps{int}]: {List[Price]}   # List of transaction add in the same time in millisecond
        """
        if self.__transactions is None:
            unix_time = _MF.get_timestamp(_MF.TIME_MILLISEC)
            init_capital = self._get_capital()
            self.__transactions = Map({unix_time: [init_capital]})
        return self.__transactions

    def _add_transaction(self, amount: Price) -> None:
        """
        To add a new transaction to the transaction historic\n
        :param amount: Amount of the new transaction to add
        """
        if amount.get_asset() != self.get_pair().get_right():
            stg_asset_str = self.get_pair().get_right().__str__().upper()
            amount_asset_str = amount.get_asset().__str__().upper()
            raise ValueError(f"The amount to add in as transaction must be in the same Asset than the Strategy's "
                             f"'{stg_asset_str}', instead '{amount_asset_str}'.")
        transacts = self.get_transactions()
        unix_time = _MF.get_timestamp(_MF.TIME_MILLISEC)
        transact_list = transacts.get(unix_time)
        transacts.put([amount], unix_time) if transact_list is None else transact_list.append(amount)

    def get_fees(self) -> Map:
        """
        To get all fees charged on closed strategies\n
        Returns
        -------
        fees: Map
            All fees charged on closed strategies
        """
        if self.__fees is None:
            self.__fees = Map()
        return self.__fees

    def get_fee(self) -> Price:
        fees = self.get_fees()
        fees_list = [Price.sum(fee_list) for add_time, fee_list in fees.get_map().items()]
        sum_closed_fee = Price.sum(fees_list)
        stgs = self.get_active_strategies()
        stg_fees = [stg.get_fee() for pair_str, stg in stgs.get_map().items()]
        sum_active_stg = Price.sum(stg_fees)
        if (sum_closed_fee is not None) and (sum_active_stg is not None):
            fee = sum_closed_fee + sum_active_stg
        elif sum_closed_fee is not None:
            fee = sum_closed_fee
        elif sum_active_stg is not None:
            fee = sum_active_stg
        else:
            fee = Price(0, self.get_pair().get_right().get_symbol())
        return fee

    def _add_fee(self, fee: Price) -> None:
        if fee.get_asset() != self.get_pair().get_right():
            right_asset = self.get_pair().get_right()
            raise ValueError(f"Fee must be in StalkerClass's '{right_asset}' right asset, instead '{fee}'")
        fees = self.get_fees()
        unix_time = _MF.get_timestamp(_MF.TIME_MILLISEC)
        fee_list = fees.get(unix_time)
        fees.put([fee], unix_time) if fee_list is None else fee_list.append(fee)

    def _get_total_capital(self) -> Price:
        """
        To get total capital available to trade\n
        NOTE: this capital will be split  between Strategy
        :return: total capital available
        """
        transacts = self.get_transactions()
        amounts = []
        for unix_time, transact_list in transacts.get_map().items():
            amounts.append(Price.sum(transact_list))
        total_capital = Price.sum(amounts)
        return total_capital

    def _get_strategy_capital(self) -> Price:
        """
        To get initial capital for new Strategy\n
        :return: initial capital for new Strategy
        """
        total_capital = self._get_total_capital()
        right_symbol = total_capital.get_asset().get_symbol()
        max_stg = self.get_max_strategy()
        stgs = self.get_active_strategies()
        max_new_stg = max_stg - len(stgs.get_map())
        stg_capital = Price(total_capital / max_new_stg, right_symbol)
        return stg_capital

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
        params.put(1, Map.rate)
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
        max_strategy = self.get_max_strategy()
        active_strategies = self.get_active_strategies()
        if len(active_strategies.get_map()) >= max_strategy:
            nb_active = len(active_strategies.get_map())
            raise Exception(f"The active strategy is already reached ({nb_active}/{max_strategy}).")
        pair_strs = active_strategies.get_keys()
        pair_str = pair.__str__()
        if pair_str in pair_strs:
            raise ValueError(f"There's already an active Strategy for this pair '{pair_str.upper()}'.")
        # Get new Strategy's class name
        stg_class = self.get_strategy_class()
        # Update new Strategy's params
        stg_params = self.get_strategy_params()
        stg_params.put(pair, Map.pair)
        stg_capital = self._get_strategy_capital()
        stg_params.put(stg_capital.get_value(), Map.capital)
        # Add new transaction
        self._add_transaction(-stg_capital)
        # Generate new Strategy
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        new_stg = eval(f"{stg_class}.generate_strategy(stg_class, stg_params)")
        active_strategies.put(new_stg, pair_str)

    def _delete_active_strategy(self, bkr: Broker, pair: Pair, marketprice: MarketPrice) -> None:
        active_stgs = self.get_active_strategies()
        pair_str = pair.__str__()
        if pair_str not in active_stgs.get_keys():
            raise ValueError(f"There's no active Strategy with this pair '{pair_str.upper()}' to delete.")
        stg = active_stgs.get(pair_str)
        # Sell all positions
        stg.stop_trading(bkr)
        # Add new transaction
        # actual_capital = stg.get_actual_capital()
        # final_capital = actual_capital.get(Map.right)
        # self._add_transaction(final_capital)
        final_capital = stg.get_actual_capital_merged(marketprice)
        self._add_transaction(final_capital)
        # Add new fee
        fee = stg.get_fee()
        self._add_fee(fee)
        # Delete active Strategy
        del active_stgs.get_map()[pair_str]

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

    def _get_no_active_pairs(self, bkr: Broker) -> List[Pair]:
        allowed_pairs = self._get_allowed_pairs(bkr)
        active_strategies = self.get_active_strategies()
        pair_strs = active_strategies.get_keys()
        blacklist = self.get_blacklist()
        no_active_pairs = [pair for pair in allowed_pairs
                           if (pair.__str__() not in pair_strs) and (pair not in blacklist)]
        # no_active_pairs = [no_active_pairs[i] for i in range(len(no_active_pairs)) if i < 10]   # ❌
        # no_active_pairs.append(Pair('SUSD/USDT'))                                               # ❌
        # no_active_pairs.append(Pair('TRXDOWN/USDT'))                                            # ❌
        # no_active_pairs = [Pair('DOGE/USDT')]                                                   # ❌
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

    def _launch_stalking(self, bkr: Broker) -> None:
        """
        To launch market stalking in its own Thread\n
        """
        last_stalk_thread = self.get_stalk_thread()
        if (last_stalk_thread is not None) and last_stalk_thread.is_alive():
            raise Exception("Can start a stalk thread while an other is working.")
        thread_name = _MF.generate_thread_name(self._THREAD_NAME_MARKET_STALKING, 5)
        stalk_thread = Thread(target=self._manage_stalking, kwargs={Map.broker: bkr}, name=thread_name)
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
        max_reached = self.max_active_strategies_reached()
        return (not max_reached) and self.is_stalking()

    def _manage_stalking(self, broker: Broker) -> None:
        print(f"{_MF.prefix()}Start Managing Stalking.")
        try:
            while self._keep_stalkig():
                print(f"{_MF.prefix()}Managing Stalking...")
                print(_MF.prefix() + '\033[35m' + _MF.thread_infos() + '\033[0m')
                start_time = _MF.get_timestamp()
                self._set_next_stalk(start_time)
                self._stalk_market(broker)
                next_stalk = self.get_next_stalk()
                end_time = _MF.get_timestamp()
                sleep_time = (next_stalk - end_time) if end_time < next_stalk else None
                if sleep_time is not None:
                    sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                    start_sleep = _MF.unix_to_date(end_time)
                    end_sleep = _MF.unix_to_date(next_stalk)
                    print(f"{_MF.prefix()}Stalking Manager sleep for '{sleep_time_str}': '{start_sleep}'->'{end_sleep}'")
                    time.sleep(sleep_time)
            print(f"{_MF.prefix()}End Managing Stalking.")
        except Exception as e:
            from model.structure.Bot import Bot
            Bot.save_error(e, self.__class__.__name__)

    def _stalk_market(self, bkr: Broker) -> None:
        """
        To stalk the market\n
        :param bkr: Access to a Broker's  API
        """
        _cls = self
        print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_BACK_CYAN + _cls._TO_REMOVE_STYLE_BLACK + "Star stalking:".upper() + _cls._TO_REMOVE_STYLE_NORMAL)
        _stg_cls = self.__class__.__name__
        _bkr_cls = bkr.__class__.__name__
        pairs = self._get_no_active_pairs(bkr)
        nb_pair = len(pairs)    # ❌
        print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_PURPLE + f"Stalk of '{nb_pair}' unused pairs:" + _cls._TO_REMOVE_STYLE_NORMAL)
        perfs = Map()
        market_prices = Map()
        stalk_period = self.get_period()
        market_params = Map({
            Map.pair: None,
            # Map.period: 60 * 60,
            Map.period: stalk_period,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 1000
        })
        # Get performance
        streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: stalk_period})) for pair in pairs]
        bkr.add_streams(streams)
        cpt = 1     # ❌
        for pair in pairs:
            print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_CYAN
                  + f"[{cpt}/{nb_pair}].Getting {pair.__str__().upper()}'s performance for 1000 intervals of 1 hour."
                  + _cls._TO_REMOVE_STYLE_NORMAL)
            cpt += 1
            pair_str = pair.__str__()
            market_params.put(pair, Map.pair)
            market_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, market_params)
            bkr.request(market_rq)
            market_price = market_rq.get_market_price()
            perf = Strategy.get_performance(bkr, _stg_cls, market_price)
            perfs.put(perf.get_map(), pair_str)
            market_prices.put(market_price, pair_str)
        # Sort performances
        perfs_sorted = dict(sorted(perfs.get_map().items(), key=lambda row: row[1][Map.roi], reverse=True))
        # Add new active Strategy
        for pair_str, perf in perfs_sorted.items():
            market_price = market_prices.get(pair_str)
            if self._eligible(market_price, bkr):
                print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_PURPLE + f"Add new active Strategy: '{pair_str.upper()}'" + _cls._TO_REMOVE_STYLE_NORMAL)
                self._add_active_strategy(Pair(pair_str))
                if self.max_active_strategies_reached():
                    break
        # Backup
        # self._save_market_stalk(Map(perfs_sorted), market_prices) if len(perfs_sorted) > 0 else None

    # —————————————————————————————————————————————— ANALYSE MARKET DOWN ———————————————————————————————————————————————

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
        last_analyse_thread = self.get_analyse_thread()
        if (last_analyse_thread is not None) and last_analyse_thread.is_alive():
            raise Exception("Can start an analyse thread while an other is working.")
        thread_name = _MF.generate_thread_name(self._THREAD_NAME_MARKET_ANALYSE, 5)
        analyse_thread = Thread(target=self._analyse_market, kwargs={Map.broker: broker}, name=thread_name)
        self._set_analyse_thread(analyse_thread)
        analyse_thread.start()

    def _analyse_market(self, broker: Broker) -> None:
        _color_cyan = self._TO_REMOVE_STYLE_CYAN
        _normal = self._TO_REMOVE_STYLE_NORMAL
        _color_green = self._TO_REMOVE_STYLE_GREEN
        _color_black = self._TO_REMOVE_STYLE_BLACK
        _back_cyan = self._TO_REMOVE_STYLE_BACK_CYAN
        print(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Start analyse of market:" + _normal)
        market_analyse = MarketPrice.analyse_market_trend(broker)
        print(f"{_MF.prefix()}" + _color_cyan + f"End analyse of market" + _normal)
        self._set_market_analyse(market_analyse)
        print(f"{_MF.prefix()}" + _color_green + f"Market analyse updated!" + _normal)

    # ——————————————————————————————————————————————— ANALYSE MARKET UP ————————————————————————————————————————————————

    def _get_sleep_time(self) -> int:
        sleep_interval = self.get_bot_sleep_time()
        unix_time = _MF.get_timestamp()
        time_rounded = _MF.round_time(unix_time, sleep_interval)
        next_rounded_time = time_rounded + sleep_interval
        new_sleep_time = next_rounded_time - unix_time
        return new_sleep_time if new_sleep_time > 0 else 0

    def trade(self, bkr: Broker) -> int:
        self._update_nb_trade()
        self.add_streams(bkr) if self._get_trade_index() == 0 else None
        self._launch_stalking(bkr) if self._can_launch_stalking() else None
        self._launch_analyse(bkr) if bkr.is_active() and (not self.is_analysing()) else None
        self._manage_trades(bkr)
        return self._get_sleep_time()

    @abstractmethod
    def _manage_trades(self, bkr: Broker) -> None:
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
        print(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Start Adding streams to socket:" + _normal)
        pairs = self._get_allowed_pairs(broker)
        stg_pairs = [Pair(pair_str) for pair_str in self.get_active_strategies().get_keys()]
        pairs = [
            *pairs,
            *[stg_pair for stg_pair in stg_pairs if stg_pair not in pairs]
        ]
        periods = [
            MarketPrice.get_period_market_analyse(),
            self.get_period(),
            self.get_strategy_params().get(Map.period)
        ]
        periods.sort()
        nb_stream = len(pairs) * len(periods)
        start_time = _MF.get_timestamp()
        duration_time = start_time + nb_stream
        start_date = _MF.unix_to_date(start_time)
        duration_date = _MF.unix_to_date(duration_time)
        duration_str = f"{int(nb_stream / 60)}min.{nb_stream % 60}sec."
        print(f"{_MF.prefix()}" + _color_cyan + f"Adding '{nb_stream}' streams for '{duration_str}' till"
                                                f" '{start_date}'->'{duration_date}'" + _normal)
        streams = []
        for period in periods:
            streams = [
                *streams,
                *[broker.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
            ]
        streams = list(dict.fromkeys(streams))
        broker.add_streams(streams)
        end_time = _MF.get_timestamp()
        duration = end_time - start_time
        real_duration_str = f"{int(duration / 60)}min.{duration % 60}sec."
        print(f"{_MF.prefix()}" + _color_green + f"End adding '{nb_stream}' streams for '{real_duration_str}'"
                                                 f" (estimated:'{duration_str}')" + _normal)

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

    @staticmethod
    def _get_allowed_pairs(bkr: Broker) -> List[Pair]:
        """
        To get pair allowed to trade with this Strategy\n
        :param bkr: Access to Broker's API
        :return: Pair allowed to trade with this Strategy
                 Map[index{int}]:   {Pair}
        """
        if StalkerClass._CONST_ALLOWED_PAIRS is None:
            if StalkerClass._get_stage() == Config.STAGE_1:
                path = Config.get(Config.DIR_MARKET_HISTORICS)
                _bkr_cls = bkr.__class__.__name__
                full_path = path.replace('$broker', _bkr_cls).replace('$pair/', '')
                pair_folders = FileManager.get_dirs(full_path, make_dir=True)
                from model.API.brokers.Binance.BinanceAPI import BinanceAPI
                pair_strs = [BinanceAPI.symbol_to_pair(_MF.regex_replace('%.+$', '', pair_folder))
                             for pair_folder in pair_folders]
            else:
                # Stablecoin regex
                stablecoins = Config.get(Config.CONST_STABLECOINS)
                concat_stable = '|'.join(stablecoins)
                stablecoin_rgx = f'({concat_stable})/\w+$'
                # Fiat regex
                fiats = Config.get(Config.CONST_FIATS)
                concat_fiat = '|'.join(fiats)
                fiat_rgx = rf'({concat_fiat})/\w+$'
                # Get pairs
                no_match = [
                    r'^\w+(up|down|bear|bull)\/\w+$',
                    r'^(bear|bull)/\w+$',
                    r'^\w*inch\w*/\w+$',
                    fiat_rgx,
                    stablecoin_rgx,
                    r'BCHSV/\w+$'
                ]
                match = [r'^.+\/usdt']
                pair_strs = bkr.get_pairs(match=match, no_match=no_match)
            StalkerClass._CONST_ALLOWED_PAIRS = [Pair(pair_str) for pair_str in pair_strs]
        return StalkerClass._CONST_ALLOWED_PAIRS
        # return [StalkerClass._CONST_ALLOWED_PAIRS[i] for i in range(len(StalkerClass._CONST_ALLOWED_PAIRS)) if i < 10]

    @abstractmethod
    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> bool:
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
        return StalkerClass._CONST_STALKER_BOT_SLEEP_TIME

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
    def json_instantiate(object_dic: dict) -> object:
        pass

    # ——————————————— SAVE DOWN ———————————————

    def _save_state(self, pair_to_closes: Map, to_delete_pairs: List[str], market_trend: str, market_analyse: Map) \
            -> None:
        def rate_to_str(rate: float) -> str:
            return f"{round(rate * 100, 2)}%"

        path = Config.get(Config.DIR_SAVE_GLOBAL_STATE)
        pair = self.get_pair()
        right_symbol = pair.get_right().get_symbol()
        active_stgs = self.get_active_strategies()
        next_stalk = self.get_next_stalk()
        next_stalk_date = _MF.unix_to_date(next_stalk) \
            if (self._get_stage() != Config.STAGE_1) and (next_stalk is not None) else next_stalk
        lefts = []
        rights = []
        for pair_str, active_stg in active_stgs.get_map().items():
            closes = pair_to_closes.get(pair_str)
            if closes is not None:
                actual_capital = active_stg.get_actual_capital()
                actual_left = actual_capital.get(Map.left)
                left = Price(actual_left * closes[-1], right_symbol)
                right = actual_capital.get(Map.right)
                lefts.append(left)
                rights.append(right)
        initial_capital = self._get_capital()
        total_left = Price.sum(lefts) if len(lefts) > 0 else Price(0, right_symbol)
        total_right = Price.sum(rights) if len(rights) > 0 else Price(0, right_symbol)
        total_capital_available = self._get_total_capital()
        total_capital = total_capital_available + total_right + total_left
        capital_allocation_size = self._get_strategy_capital() \
            if not self.max_active_strategies_reached() else total_capital_available
        roi = (total_capital / initial_capital - 1)
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
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
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
            'total_fee': total_fee,
            'fee_init_capital_rate': rate_to_str(fee_init_capital_rate),
            'fee_total_capital_rate': rate_to_str(fee_total_capital_rate),
            'total_capital_available': total_capital_available,
            'capital_allocation_size': capital_allocation_size,
            'allocated_capital': total_right + total_left,
            'allocated_left': total_left,
            'allocated_right': total_right,
            Map.roi: f"{round(roi * 100, 2)}%",
            'nb_active_strategies': len(active_stgs.get_map()),
            'max_strategy': self.get_max_strategy(),
            'active_strategies': _MF.json_encode(active_stgs.get_keys()),
            'deleted_strategies': _MF.json_encode(to_delete_pairs),
            'next_blacklist_clean': _MF.unix_to_date(next_clean) if next_clean is not None else '—',
            'blacklist': self.get_blacklist()
        }
        rows = [row]
        fields = list(row.keys())
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    def _save_market_stalk(self, perfs: Map, market_prices: Map) -> None:
        path = Config.get(Config.DIR_SAVE_MARKET_STALK)
        rows = []
        date = _MF.unix_to_date(_MF.get_timestamp())
        for pair_str, perf in perfs.get_map().items():
            market_price = market_prices.get(pair_str)
            eligible = self._eligible(market_price)
            row = {
                Map.date: date,
                Map.pair: pair_str.upper(),
                'eligible': eligible,
                **perf
            }
            rows.append(row)
        fields = list(rows[0].keys())
        separator = {fields[0]: date, **{field: '⬇️ ——— ⬇️' for field in fields if field != fields[0]}}
        rows.insert(0, separator)
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    @staticmethod
    def _save_moves(rows: List[dict]) -> None:
        path = Config.get(Config.DIR_SAVE_GLOBAL_MOVES)
        path = path.replace('$class', StalkerClass.__name__)
        fields = list(rows[0].keys())
        rows.insert(0, {fields[0]: rows[0][Map.date], **{field: '⬇️ ——— ⬇️' for field in fields if field != fields[0]}})
        FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)
