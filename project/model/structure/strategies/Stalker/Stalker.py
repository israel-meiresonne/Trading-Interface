import time
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


class Stalker(Strategy, MyJson):
    # _CONST_MARKET_PERIOD = 60 * 60      # in second
    _CONST_MARKET_PERIOD = 60 * 15  # in second
    _CONST_STALK_FREQUENCY = 60         # in second
    _CONST_STALKER_BOT_SLEEP_TIME = 10  # in second
    _CONST_ALLOWED_PAIRS = None
    _CONST_MAX_STRATEGY = 20
    _CONST_MAX_LOSS_RATE = -0.01
    _CONST_FLOOR_COEF = 0.05
    _CONST_MIN_FLOOR_COEF = 0.01
    _THREAD_BASE_MARKET_STALKING = 'market_stalking'
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
        self.__max_strategy = Stalker._CONST_MAX_STRATEGY
        self.__strategy_class = params.get(Map.strategy)
        child_stg_params = params.get(Map.param)
        self._set_strategy_params(Map(child_stg_params))
        self.__active_strategies = None
        self.__next_blacklist_clean = None
        self.__blacklist = None
        self.__stalk_thread = None
        self.__active_rois = None
        self.__market_analyse = None
        self.__fees = None

    def get_max_strategy(self) -> int:
        return self.__max_strategy

    def _set_next_stalk(self, unix_time: int) -> None:
        """
        stg_params = self.get_strategy_params()
        period = stg_params.get(Map.period)
        min_stalk_interval = Stalker.get_minimum_stalk_interval()
        stalk_interval = min_stalk_interval if (period is None) or (period <= min_stalk_interval) else period
        if Stalker._get_stage() == Config.STAGE_1:
            trade_index = Stalker._get_trade_index()
            stalk_trade_interval = int(stalk_interval / 60)
            index_rounded = int(trade_index / stalk_trade_interval) * stalk_trade_interval
            next_stalk = index_rounded + stalk_trade_interval
        else:
            # if (period is None) or (period <= min_stalk_interval):
            if stalk_interval == min_stalk_interval:
                unix_rounded = int(unix_time / min_stalk_interval) * min_stalk_interval
                next_stalk = unix_rounded + min_stalk_interval
            else:
                unix_rounded = int(unix_time / period) * period
                next_stalk = unix_rounded + period
        self.__next_stalk = next_stalk
        """
        stalk_frequency = Stalker.get_stalk_frequency()
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
            raise ValueError(f"Fee must be in Stalker's '{right_asset}' right asset, instead '{fee}'")
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

    def _delete_active_strategy(self, bkr: Broker, pair: Pair) -> None:
        active_stgs = self.get_active_strategies()
        pair_str = pair.__str__()
        if pair_str not in active_stgs.get_keys():
            raise ValueError(f"There's no active Strategy with this pair '{pair_str.upper()}' to delete.")
        stg = active_stgs.get(pair_str)
        # Sell all positions
        stg.stop_trading(bkr)
        # Add new transaction
        actual_capital = stg.get_actual_capital()
        final_capital = actual_capital.get(Map.right)
        self._add_transaction(final_capital)
        # Add new fee
        fee = stg.get_fee()
        self._add_fee(fee)
        # Delete active Strategy
        del active_stgs.get_map()[pair_str]
        self._delete_active_roi(pair)

    def _set_next_blacklist_clean(self) -> None:
        """
        To set the next time to empty the blacklist\n
        """
        stalk_period = Stalker.get_stalk_period()
        if Stalker._get_stage() == Config.STAGE_1:
            trade_index = Stalker._get_trade_index()
            stalk_period_minute = int(stalk_period / 60)
            index_rounded = int(trade_index / stalk_period_minute) * stalk_period_minute
            next_blacklist_clean = index_rounded + stalk_period_minute
        else:
            unix_time = _MF.get_timestamp()
            round_time = _MF.round_time(unix_time, stalk_period)
            next_blacklist_clean = round_time + stalk_period
        self.__next_blacklist_clean = next_blacklist_clean

    def get_next_blacklist_clean(self) -> int:
        return self.__next_blacklist_clean

    def get_blacklist(self) -> List[Pair]:
        next_clean = self.get_next_blacklist_clean()
        unix_time = _MF.get_timestamp() if Stalker._get_stage() != Config.STAGE_1 else Stalker._get_trade_index()
        if (self.__blacklist is None) or ((next_clean is not None) and (unix_time >= next_clean)):
            self.__blacklist = []
            self.__next_blacklist_clean = None
        return self.__blacklist

    def _blacklist_pair(self, pair: Pair) -> None:
        """
        To blacklist a new pair\n
        :param pair: Pair to blacklist
        """
        blacklist = self.get_blacklist()
        if pair in blacklist:
            raise ValueError(f"This pair '{pair.__str__().upper()}' already exist in blacklist.")
        blacklist.append(pair)
        self._set_next_blacklist_clean()

    def _get_no_active_pairs(self, bkr: Broker) -> List[Pair]:
        allowed_pairs = Stalker._get_allowed_pairs(bkr)
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
        thread_name = _MF.generate_thread_name(Stalker._THREAD_BASE_MARKET_STALKING, 5)
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
                self._set_market_analyse(broker)
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
            Bot.save_error(e, Stalker.__name__)

    def _stalk_market(self, bkr: Broker) -> None:
        """
        To stalk the market\n
        :param bkr: Access to a Broker's  API
        """
        _cls = Stalker
        print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_BACK_CYAN + _cls._TO_REMOVE_STYLE_BLACK + "Star stalking:".upper() + _cls._TO_REMOVE_STYLE_NORMAL)
        _stg_cls = Stalker.__name__
        _bkr_cls = bkr.__class__.__name__
        pairs = self._get_no_active_pairs(bkr)
        nb_pair = len(pairs)    # ❌
        print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_PURPLE + f"Stalk of '{nb_pair}' unused pairs:" + _cls._TO_REMOVE_STYLE_NORMAL)
        perfs = Map()
        market_prices = Map()
        stalk_period = self.get_stalk_period()
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
            if Stalker._eligible(market_price):
                print(f"{_MF.prefix()}" + _cls._TO_REMOVE_STYLE_PURPLE + f"Add new active Strategy: '{pair_str.upper()}'" + _cls._TO_REMOVE_STYLE_NORMAL)
                self._add_active_strategy(Pair(pair_str))
                if self.max_active_strategies_reached():
                    break
        # Backup
        # self._save_market_stalk(Map(perfs_sorted), market_prices) if len(perfs_sorted) > 0 else None

    def _set_market_analyse(self, bkr: Broker) -> None:
        _color_cyan = Stalker._TO_REMOVE_STYLE_CYAN
        _normal = Stalker._TO_REMOVE_STYLE_NORMAL
        _color_green = Stalker._TO_REMOVE_STYLE_GREEN
        print(f"{_MF.prefix()}" + _color_cyan + f"Start analyse of market..." + _normal)
        market_analyse = MarketPrice.analyse_market_trend(bkr)
        print(f"{_MF.prefix()}" + _color_cyan + f"End analyse of market" + _normal)
        self.__market_analyse = market_analyse
        print(f"{_MF.prefix()}" + _color_green + f"Market analyse updated!" + _normal)

    def get_market_analyse(self) ->  Map:
        return self.__market_analyse

    def _get_sleep_time(self) -> int:
        sleep_interval = self.get_bot_sleep_time()
        unix_time = _MF.get_timestamp()
        time_rounded = _MF.round_time(unix_time, sleep_interval)
        next_rounded_time = time_rounded + sleep_interval
        new_sleep_time = next_rounded_time - unix_time
        return new_sleep_time if new_sleep_time > 0 else 0

    def get_active_rois(self) -> Map:
        if self.__active_rois is None:
            self.__active_rois = Map()
        return self.__active_rois

    def get_active_roi(self, pair: Pair) -> float:
        return self.get_active_rois().get(pair.__str__())

    def _update_active_roi(self, pair: Pair, roi: float) -> None:
        self.get_active_rois().put(roi, pair.__str__())

    def _delete_active_roi(self, pair: Pair) -> None:
        active_rois = self.get_active_rois()
        pair_str = pair.__str__()
        if pair_str not in active_rois.get_keys():
            raise KeyError(f"There's not active roi for this pair '{pair}'")
        del active_rois.get_map()[pair_str]

    def _bellow_floor(self, strategy: Strategy, market_price: MarketPrice, market_trend: str) -> bool:
        pair = strategy.get_pair()
        roi = strategy.get_roi(market_price)
        last_roi = self.get_active_roi(pair)
        last_floor = Stalker._floor(last_roi, market_trend)
        bellow_floor = (last_floor is not None) and (roi < last_floor)
        return bellow_floor

    @staticmethod
    def _floor(roi: float, market_trend: str) -> float:
        """
        To get floor of the given roi\n
        NOTE:
                if roi is None:                             => floor = None\n
                if (rising and roi < floor_coef):           => floor = None\n
                if (rising and roi >= floor_coef):          => floor = float\n
                if (dropping and roi < 0.01):               => floor = None\n
                if (dropping and roi in [0.01, floor_coef[):=> floor = float\n
        Parameters
        ----------
        roi: float
            Roi to use
        market_trend: str
            Market's trend
        Returns
        -------
        floor: float
            Floor of the given roi
        """
        if not isinstance(market_trend, str):
            raise ValueError(f"Market's trend must be type str, instead '{market_trend}({type(market_trend)})'")
        floor_coef = Stalker.get_floor_coef()
        min_floor_coef = Stalker.get_min_floor_coef()
        if (roi is not None) and (roi >= min_floor_coef):
            if roi >= floor_coef:
                floor = _MF.round_time(roi, floor_coef)
            else:
                floor = _MF.round_time(roi, min_floor_coef)
        else:
            floor = None
        return floor

    def trade(self, bkr: Broker) -> int:
        self._launch_stalking(bkr) if self._can_launch_stalking() else None
        self._manage_trades(bkr)
        return self._get_sleep_time()

    def _manage_trades(self, bkr: Broker) -> None:
        _cls = Stalker
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
        pairs_to_delete = []    # ❌
        pair_closes = Map()     # ❌
        rows = []               # ❌
        print(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Star manage strategies "
                                                              f"({len(active_stgs_copy.get_map())}):".upper() + _normal)
        self._manage_trades_add_streams(bkr, active_stgs_copy)
        market_analyse = self.get_market_analyse()
        market_trend = MarketPrice.get_market_trend(bkr, analyse=market_analyse) if market_analyse is not None else '—'
        market_analyse = Map() if market_analyse is None else market_analyse
        for pair_str, active_stg in active_stgs_copy.get_map().items():
            print(f"{_MF.prefix()}" + _color_cyan + f"Managing pair '{pair_str.upper()}'..." + _normal)
            # Prepare active Strategy
            pair = active_stg.get_pair()
            has_position = active_stg._has_position()
            market_price = self._get_market_price(bkr, pair)
            # Prepare closes
            closes = list(market_price.get_closes())
            closes.reverse()
            pair_closes.put(closes, pair_str)    # ❌
            # Prepare SuperTrends
            supertrends = list(market_price.get_super_trend())
            supertrends.reverse()
            supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -1)
            supertrend_rising = supertrend_trend == MarketPrice.SUPERTREND_RISING
            # Prepare Psars
            psars = list(market_price.get_psar())
            psars.reverse()
            psar_trend = MarketPrice.get_psar_trend(closes, psars, -1)
            psar_rising = psar_trend == MarketPrice.PSAR_RISING
            # Prepare capital
            bellow_floor = self._bellow_floor(active_stg, market_price, market_trend)
            stg_roi = active_stg.get_roi(market_price)
            max_loss_rate = Stalker.get_max_loss()
            stg_roi_bellow_limit = stg_roi <= max_loss_rate
            last_roi = self.get_active_roi(pair)
            floor_coef = Stalker.get_floor_coef()
            last_floor = Stalker._floor(last_roi, market_trend)
            # Fee
            fee = active_stg.get_fee()
            initial_capital = active_stg._get_capital()
            actual_capital = active_stg.get_actual_capital_merged(market_price)
            fee_initial_capital_rate = fee / initial_capital
            fee_actual_capital = fee / actual_capital
            row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.pair: pair,
                Map.roi: f"{round(stg_roi * 100, 2)}%",
                'fee': fee,
                'initial_capital': initial_capital,
                'actual_capital': actual_capital,
                'fee_initial_capital_rate': _MF.rate_to_str(fee_initial_capital_rate),
                'fee_actual_capital': _MF.rate_to_str(fee_actual_capital),
                'max_loss': f"{round(max_loss_rate * 100, 2)}%",
                'roi_bellow_limit': stg_roi_bellow_limit,
                'has_position': has_position,
                'floor_coef': f"{round(floor_coef * 100, 2)}%",
                'last_roi': f"{round(last_roi * 100, 2)}%" if last_roi is not None else '—',
                'last_floor': f"{round(last_floor * 100, 2)}%" if last_floor is not None else '—',
                'market_trend': market_trend,
                'supertrend_trend': supertrend_trend,
                'supertrend_rising': supertrend_rising,
                'psar_trend': psar_trend,
                'psar_rising': psar_rising,
                Map.close: closes[-1],
                Map.super_trend: supertrends[-1],
                'psar': psars[-1]
            }
            rows.append(row)
            # Trade
            if bellow_floor:
                self._delete_active_strategy(bkr, pair)
                self._blacklist_pair(pair)
                print(f"{_MF.prefix()}" + _color_yellow + f"Pair '{pair_str.upper()}' is BELLOW its last FLOOR "
                                                          f"(floor coef ('{floor_coef*100}%'): "
                                                          f"roi='{round(stg_roi*100, 2)}%' <= '{last_floor*100}%')."
                                                          f"" + _normal)
                continue
            else:
                self._update_active_roi(pair, stg_roi)
                last_roi_str = f"{round(last_roi * 100, 2)}%" if last_roi is not None else '—'
                print(f"{_MF.prefix()}" + _color_green + f"Pair '{pair_str.upper()}' UPDATED its active roi from "
                                                         f"'{last_roi_str}'->'{round(stg_roi*100, 2)}%'"
                                                         f"" + _normal)
            if stg_roi_bellow_limit:
                self._delete_active_strategy(bkr, pair)
                self._blacklist_pair(pair)
                print(f"{_MF.prefix()}" + _color_purple + f"Pair '{pair_str.upper()}' is BLACKLISTED (max loss ({max_loss_rate*100}%): "
                                      f"{round(stg_roi*100, 2)}% <= {max_loss_rate*100}%)." + _normal)
            elif supertrend_rising and psar_rising:
                active_stg.trade(bkr)
                print(f"{_MF.prefix()}" + _color_green + f"Pair {pair_str.upper()} trade with SUCCESS." + _normal)
            elif supertrend_rising and (not psar_rising):
                if has_position:
                    active_stg.stop_trading(bkr)
                    print(f"{_MF.prefix()}" + _color_yellow + f"Pair {pair_str.upper()} is SUSPENDED." + _normal)
                else:
                    print(f"{_MF.prefix()}" + _color_yellow + f"Pair {pair_str.upper()} is ALREADY SUSPENDED." + _normal)
            elif not supertrend_rising:
                self._delete_active_strategy(bkr, pair)
                pairs_to_delete.append(pair_str)
                print(f"{_MF.prefix()}" + _color_red + f"Pair {pair_str.upper()} is DELETED (Supertrend dropping)." + _normal)
            else:
                raise Exception(f"Unknown state. ("
                                f"stg_roi_bellow_limit: '{stg_roi_bellow_limit}'\n"
                                f"has_position: '{has_position}'\n"
                                f"supertrend_rising: '{supertrend_rising}'\n"
                                f"psar_rising: '{psar_rising}')")
        self._save_state(pair_closes, pairs_to_delete, market_trend, market_analyse)
        Stalker._save_moves(rows) if len(rows) > 0 else None

    def _manage_trades_add_streams(self, bkr: Broker, active_stgs_copy: Map) -> None:
        pair_strs = active_stgs_copy.get_keys()
        pairs = [active_stgs_copy.get(pair_str).get_pair() for pair_str in pair_strs]
        stalk_period = Stalker.get_stalk_period()
        stalker_streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: stalk_period})) for pair in pairs]
        bkr.add_streams(stalker_streams)
        child_period = self.get_strategy_params().get(Map.period)
        stalker_streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: child_period})) for pair in pairs]
        bkr.add_streams(stalker_streams)

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
    def get_stalk_period() -> int:
        """
        To get interval (in second) between each market stalk\n
        :return: interval (in second) between each market stalk
        """
        return Stalker._CONST_MARKET_PERIOD

    @staticmethod
    def get_stalk_frequency() -> int:
        return Stalker._CONST_STALK_FREQUENCY

    @staticmethod
    def get_max_loss() -> float:
        return Stalker._CONST_MAX_LOSS_RATE

    @staticmethod
    def get_floor_coef() -> float:
        return Stalker._CONST_FLOOR_COEF

    @staticmethod
    def get_min_floor_coef() -> float:
        return Stalker._CONST_MIN_FLOOR_COEF

    @staticmethod
    def _get_market_price(bkr: Broker, pair: Pair) -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        _bkr_cls = bkr.__class__.__name__
        mkt_params = Map({
            Map.pair: pair,
            Map.period: Stalker.get_stalk_period(),
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 100
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
        if Stalker._CONST_ALLOWED_PAIRS is None:
            if Stalker._get_stage() == Config.STAGE_1:
                path = Config.get(Config.DIR_MARKET_HISTORICS)
                _bkr_cls = bkr.__class__.__name__
                full_path = path.replace('$broker', _bkr_cls).replace('$pair/', '')
                pair_folders = FileManager.get_dirs(full_path)
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
            Stalker._CONST_ALLOWED_PAIRS = [Pair(pair_str) for pair_str in pair_strs]
        return Stalker._CONST_ALLOWED_PAIRS

    @staticmethod
    def _eligible(market_price: MarketPrice) -> bool:
        """
        To check if a pair is interesting to trade\n
        ACTUAL CONDITION: actual trend is green AND super_trend <= last_red_close\n
        :param market_price: Market price historic
        :return: True if pair is interesting else False
        """
        # Extract closes
        closes = list(market_price.get_closes())
        closes.reverse()
        # Extract supertrend
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        trend = MarketPrice.get_super_trend_trend(closes, super_trends, -1)
        prev_trend = MarketPrice.get_super_trend_trend(closes, super_trends, -2)
        eligible = (trend == MarketPrice.SUPERTREND_RISING) and (prev_trend == MarketPrice.SUPERTREND_DROPPING)
        return eligible

    @staticmethod
    def get_bot_sleep_time() -> int:
        return Stalker._CONST_STALKER_BOT_SLEEP_TIME

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'Stalker':
        """
        To generate a new Strategy\n
        :param stg_class: Class name of the Strategy to generate
        :param params: params
                       params[*]:               {Strategy.generate_strategy()}  # Same structure that params required in
                       params[Map.strategy]:    {str}       # Class name of Strategy to use
                       params[Map.param]:       {dict}      # Params for Strategy  to use
        :return: instance of a Strategy
        """
        pair = params.get(Map.pair)
        maximum = params.get(Map.maximum)
        capital = params.get(Map.capital)
        right_symbol = pair.get_right().get_symbol()
        new_params = Map({
            Map.pair: pair,
            Map.maximum: Price(maximum, right_symbol) if maximum is not None else None,
            Map.capital: Price(capital, right_symbol),
            Map.rate: params.get(Map.rate),
            Map.strategy: params.get(Map.strategy),
            Map.param: params.get(Map.param)
        })
        return Stalker(new_params)

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
        _class_token = MyJson.get_class_name_token()
        instance = Stalker(Map({
            Map.pair: Pair('@json/@json'),
            Map.maximum: None,
            Map.capital: 0,
            Map.rate: 1,
            Map.strategy: '@json',
            Map.param: {
                Map.maximum: None,
                Map.capital: 0,
                Map.rate: 1,
                Map.period: 1,
            }
        }))
        exec(MyJson.get_executable())
        return instance

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
            if (Stalker._get_stage() != Config.STAGE_1) and (next_stalk is not None) else next_stalk
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
        path = path.replace('$class', Stalker.__name__)
        fields = list(rows[0].keys())
        rows.insert(0, {fields[0]: rows[0][Map.date], **{field: '⬇️ ——— ⬇️' for field in fields if field != fields[0]}})
        FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)
