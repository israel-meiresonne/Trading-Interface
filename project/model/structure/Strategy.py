from abc import ABC, abstractmethod
from typing import List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Orders import Orders
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class Strategy(ABC):
    PREFIX_ID = 'stg_'
    _CONST_BOT_SLEEP_TIME = 60
    _PERFORMANCE_INIT_CAPITAL = 100
    _TOP_ASSET = None
    _TOP_ASSET_MAX = 25

    @abstractmethod
    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
                     params[Map.pair]:       {Pair}
                     params[Map.period]:     {int|None}
                     params[Map.capital]:    {Price}        # Initial capital
                     params[Map.maximum]:    {Price|None}   # Maximum of capital to use (if set, maximum > 0)
                     params[Map.rate]:       {float|None}   # ]0,1]
        """
        ks = [Map.pair, Map.capital]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required")
        super().__init__()
        self.__id = None
        self.__settime = None
        self.__period = None
        self.__nb_trade = None
        self.__broker = None
        self.__orders = None
        self.__wallet = None
        period = params.get(Map.period)
        pair = params.get(Map.pair)
        max_cap = params.get(Map.maximum)
        cap_rate = params.get(Map.rate)
        capital = params.get(Map.capital)
        self._set_id()
        self._set_settime()
        self._set_pair(pair)
        self._set_period(period)
        self._set_wallet(capital)
        self._set_max_capital(max_cap) if max_cap is not None else None
        self._set_capital_rate(cap_rate) if cap_rate is not None else None

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————

    def _set_id(self) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> None:
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def _set_pair(self, pair: Pair) -> None:
        self.__pair = pair

    def get_pair(self) -> Pair:
        return self.__pair

    def _set_period(self, period) -> None:
        self.__period = period

    def get_period(self) -> int:
        """
        To get period interval to request\n
        Returns
        -------
        period: int
            Period interval to request
        """
        return self.__period

    def get_nb_trade(self) -> int:
        """
        To get nb of call done of the function .trade()\n
        NOTE: function .trade() must call ._update_nb_trade()
        Returns
        -------
        nb_trade: int
            Nb of call done of the function .trade()
        """
        if self.__nb_trade is None:
            self.__nb_trade = 0
        return self.__nb_trade

    def _reset_broker(self) -> None:
        self.__broker = None

    def _set_broker(self, bkr: Broker) -> None:
        self.__broker = bkr

    def get_broker(self) -> Broker:
        return self.__broker

    def _get_orders(self) -> Orders:
        if self.__orders is None:
            self.__orders = Orders()
        return self.__orders

    def _set_wallet(self, capital: Price) -> None:
        self.__wallet = Wallet(capital)

    def get_wallet(self) -> Wallet:
        return self.__wallet

    def _set_max_capital(self, max_capital: Price) -> None:
        self.get_wallet().set_max_buy(max_capital)

    def _set_capital_rate(self, capital_rate: float) -> None:
        self.get_wallet().set_buy_rate(capital_rate)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    def _update_nb_trade(self) -> None:
        """
        To increase the number of trade done\n
        """
        self.__nb_trade = self.get_nb_trade() + 1

    def _add_order(self, odr: Order) -> None:
        self._get_orders().add_order(odr)

    def _update_orders(self, bkr: Broker) -> None:
        """
        To update Orders\n
        NOTE: Also push new Order executed in Wallet

        Parameters:
        -----------
        bkr: Broker
            Access to a Broker's API
        """
        odrs = self._get_orders()
        executed = odrs.update(bkr)
        wallet = self.get_wallet()
        for odr_id in executed:
            odr = odrs.get_order(odr_id=odr_id)
            move = odr.get_move()
            if move == Order.MOVE_BUY:
                wallet.buy(odr)
            elif move == Order.MOVE_SELL:
                wallet.sell(odr)
            else:
                raise ValueError(f"This Order move '{move}' is not supported")

    def _has_position(self) -> bool:
        """
        Check if holding a left position\n
        :return: True if holding else False
        """
        odrs = self._get_orders()
        return odrs.has_position()

    @abstractmethod
    def trade(self, bkr: Broker) -> int:
        """
        To perform a trade\n
        :param bkr: access to a Broker's API
        :return: time to wait till the next trade
        """
        pass

    @abstractmethod
    def stop_trading(self, bkr: Broker) -> None:
        """
        To cancel pending Order and sell all positions\n
        :param bkr: access to a Broker's API
        """
        pass

    def _json_encode_prepare(self) -> None:
        self._reset_broker()

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION STATIC DOWN —————————————————————————————————————————————————

    @staticmethod
    @abstractmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    @staticmethod
    def get_performance_init_capital() -> float:
        return Strategy._PERFORMANCE_INIT_CAPITAL

    @staticmethod
    @abstractmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        """
        To get list of roi rate realized following the Strategy's trade rule\n
        :param market_price: Market historic
        :return:
        """
        pass

    @staticmethod
    def get_bot_sleep_time() -> int:
        sleep_time = Strategy._CONST_BOT_SLEEP_TIME
        unix_time = _MF.get_timestamp()
        round_time = _MF.round_time(unix_time, sleep_time)
        wakeup_time = round_time + sleep_time
        new_sleep_time = int(wakeup_time - unix_time)
        return new_sleep_time
    
    @staticmethod
    def _market_price(bkr: Broker, pair: Pair, period: int, n_period: int, starttime: int = None, endtime: int = None) -> MarketPrice:
        """
        To request MarketPrice to Broker

        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pair: Pair
            Pair to get market prices for
        period: int
            The period interval to request
        n_period: int
            The number of period to retrieve
        starttime: int
            The older time
        endtime: int
            The most recent time

        Returns
        -------
        return: MarketPrice
            MarketPrice from Broker's API
        """
        _bkr_cls = bkr.__class__.__name__
        mkt_params = Map({
            Map.pair: pair,
            Map.period: period,
            Map.begin_time: starttime,
            Map.end_time: endtime,
            Map.number: n_period
        })
        bkr_rq = bkr.generate_broker_request(
            _bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_params)
        bkr.request(bkr_rq)
        return bkr_rq.get_market_price()

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'Strategy':
        """
        To generate a new Strategy\n
        :param stg_class: A Strategy's class name
        :param params: params
                       params[Map.pair]:       {Pair}
                       params[Map.maximum]:    {float|None} # maximum of capital to use (if set, maximum > 0)
                       params[Map.capital]:    {float}      # initial capital
                       params[Map.rate]:       {float|None} # ]0,1]
        :return: instance of a Strategy
        """
        '''
        pair = params.get(Map.pair)
        right_symbol = pair.get_right().get_symbol()
        # Put Maximum
        max_value = params.get(Map.maximum)
        max_obj = Price(max_value, right_symbol) if max_value is not None else None
        params.put(max_obj, Map.maximum)
        # Put Capital
        capital_value = params.get(Map.capital)
        capital_obj = Price(capital_value, right_symbol)
        params.put(capital_obj, Map.capital)
        '''
        Strategy._generate_strategy_treat_params(params)
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        return eval(f"{stg_class}(params)")

    @staticmethod
    def _generate_strategy_treat_params(params: Map) -> None:
        pair = params.get(Map.pair)
        right_symbol = pair.get_right().get_symbol()
        # Put Maximum
        max_value = params.get(Map.maximum)
        max_obj = Price(max_value, right_symbol) if max_value is not None else None
        params.put(max_obj, Map.maximum)
        # Put Capital
        capital_value = params.get(Map.capital)
        capital_obj = Price(capital_value, right_symbol)
        params.put(capital_obj, Map.capital)

    @staticmethod
    def get_performance(bkr: Broker, stg_class: str, market_price: MarketPrice) -> Map:
        """
        To get Strategy's performance\n
        :param bkr: Access to a Broker's API
        :param stg_class: A Strategy's class name
        :param market_price: Market historic
        :return: Strategy's performance
                 Map[Map.roi]:          {float}
                 Map[Map.day]:          {float}                                     # Roi per day
                 Map[Map.fee]:          {float}
                 Map[Map.rate]:         {Strategy.performance_get_rates()}          # Same structure
                 Map[Map.transaction]:  {Strategy._performance_get_transactions()}  # Same structure
        """
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        initial_capital = Strategy.get_performance_init_capital()
        pair = market_price.get_pair()
        fees = bkr.get_trade_fee(pair)
        fee_rate = fees.get(Map.taker)
        closes = list(market_price.get_closes())
        closes.reverse()
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        rates = eval(f"{stg_class}.performance_get_rates(market_price)")
        transactions = eval(f"{stg_class}._performance_get_transactions(initial_capital, rates, fees)")
        last_transac = transactions[-1]
        roi = last_transac.get(Map.capital) / initial_capital - 1
        nb_period = len(closes)
        period = market_price.get_period_time()
        roi_per_day = roi/(nb_period * period) * 60 * 60 * 24
        perf = Map({
            Map.roi: roi,
            Map.day: roi_per_day,
            Map.fee: fee_rate,
            Map.rate: rates,
            Map.transaction: transactions,
        })
        return perf

    @staticmethod   # Strategy
    def _performance_get_transactions(initial_capital: float, rates: List[float], fees: Map) -> List[dict]:
        """
        To get a simulation of multiple trade for each rate give including Order fee\n
        :param initial_capital: Initial capital to use for simulation
        :param rates: Rate from Strategy.performance_get_rates()
        :param fees: Order fee rate charged for taker and maker
        :return: transaction historic for each rate given
        """
        transactions = []
        fee_rate = fees.get(Map.taker)
        # Initialize First Capital
        transaction1 = Map()
        transaction1.put(initial_capital, Map.capital)
        transaction1.put(None, Map.buy)
        transaction1.put(None, Map.sell)
        transaction1.put(initial_capital * fee_rate, Map.fee)
        transactions.append(transaction1.get_map())
        for rate in rates:
            last_transac = transactions[-1]
            # Add Buy Transaction
            last_capital = last_transac.get(Map.capital)
            last_fee = last_transac.get(Map.fee)
            buy_transac = Map()
            buy = last_capital - last_fee
            sell_fee = buy * fee_rate
            buy_transac.put(buy, Map.capital)
            buy_transac.put(buy, Map.buy)
            buy_transac.put(sell_fee, Map.fee)
            transactions.append(buy_transac.get_map())
            # Add Sell Transaction
            sell_transact = Map()
            sell = buy * (1 + rate) - sell_fee
            buy_fee = sell * fee_rate
            sell_transact.put(sell, Map.capital)
            sell_transact.put(sell, Map.sell)
            sell_transact.put(buy_fee, Map.fee)
            transactions.append(sell_transact.get_map())
        return transactions

    @staticmethod
    def list_strategies() -> list:
        """
        To get all available Strategy\n
        :return: list of available Strategy
        """
        path = Config.get(Config.DIR_STRATEGIES)
        return FileManager.get_dirs(path, special=False)

    @staticmethod   # Broker
    def get_top_asset(bkr: Broker, stg_class: str, period: int, nb_period: int, maximum: int = _TOP_ASSET_MAX) -> Map:
        """
        To get ranking of pair with the best performance\n
        Criteria: volume (in usd stablecoin), the ROI for the given Strategy\n
        :param bkr: Access to a Broker's API
        :param stg_class: A Strategy's class name
        :param period: Period interval to use to rank following the ROI
        :param nb_period: Number of period to use
        :param maximum: Max pair rank
        :return: ranking of pair with the best performance
                 Map[rank{int}][*]:                     {MinMax.get_top_period()}   # Same structure than this function
                 Map[rank{int}][Map.volume]:            {float}                 # Transaction volume in last 24h
                 Map[rank{int}][Map.rank][Map.sum]:     {float}                 # Sum rank
                 Map[rank{int}][Map.rank][Map.roi]:     {int}                   # Roi rank
                 Map[rank{int}][Map.rank][Map.volume]:  {int}                   # Volume rank
        """
        if Strategy._TOP_ASSET is None:
            top_volume = Strategy.get_top_volume(bkr, maximum)
            pairs = [row[Map.pair] for rank, row in top_volume.get_map().items()]
            top_roi = Strategy.get_top_roi(bkr, stg_class, pairs, period, nb_period)
            structures = []
            for pair in pairs:
                volume_rank = Strategy.extract_rank(top_volume, Map.pair, pair)
                roi_rank = Strategy.extract_rank(top_roi, Map.pair, pair)
                """
                for rank, volume_struc in top_volume.get_map().items():
                    if volume_struc[Map.pair] == pair:
                        volume_rank = rank
                        break
                for rank, roi_struc in top_roi.get_map().items():
                    if roi_struc[Map.pair] == pair:
                        roi_rank = rank
                        break
                """
                volume = top_volume.get(volume_rank, Map.volume)
                rank_sum = volume_rank + roi_rank
                structure = Map(top_roi.get(roi_rank))
                structure.put(volume,       Map.volume)
                structure.put(rank_sum,     Map.rank, Map.sum)
                structure.put(roi_rank,     Map.rank, Map.roi)
                structure.put(volume_rank,  Map.rank, Map.volume)
                structures.append(structure.get_map())
            top_asset = sorted(structures,
                               key=lambda row: (row[Map.rank][Map.sum], row[Map.rank][Map.roi], row[Map.rank][Map.volume]))
            top_asset_keyed = Map({idx: top_asset[idx] for idx in range(len(top_asset))})
            Strategy._save_top_asset(stg_class, top_asset_keyed)
            Strategy._TOP_ASSET = top_asset_keyed
        return Strategy._TOP_ASSET

    @staticmethod   # Broker
    def extract_rank(top: Map, key: str, match) -> int:
        top_rank = None
        for rank, top_struc in top.get_map().items():
            if top_struc[key] == match:
                top_rank = rank
                break
        if top_rank is None:
            raise ValueError(f"There's not value that match '{match}' for this key '{key}': \n top: {top}")
        return top_rank

    @staticmethod   # Broker
    def get_top_roi(bkr: Broker, stg_class: str, pairs: List[Pair], period: int, nb_period: int) -> Map:
        """
        To get ranking of the given pairs following their ROI for the  given Strategy\n
        :param bkr: Access to a Broker's API
        :param stg_class: A Strategy's class name
        :param pairs: The pair to rank
        :param period: Period interval to use to evaluate ROI
        :param nb_period: Number of period to use
        :return: ranking of the given pairs following their ROI
                 Map[rank{int}][*]: {MinMax.get_top_period()} # Same structure than this function
        """
        structures = []
        periods = [period]
        for pair in pairs:
            structure = Strategy.get_top_period(bkr, stg_class, pair, periods, nb_period)
            structures.append(structure.get_map())
        structures_sorted = sorted(structures, key=lambda row: row[Map.period][0][Map.day], reverse=True)
        top_roi = Map({idx: structures_sorted[idx] for idx in range(len(structures_sorted))})
        return top_roi

    @staticmethod   # Broker
    def get_top_period(bkr: Broker, stg_class: str, pair: Pair, periods: List[int], nb_period: int) -> Map():
        """
        To get ranking of a pair following it's ROI/day for a given Strategy\n
        :param bkr: Access to a Broker's API
        :param stg_class: A Strategy's class name
        :param pair: The pair to get ROI
        :param periods: Period interval in second for witch to evaluate ROI (i.e: [60] or [60, 60*3, 60*5])
        :param nb_period: Number of period to get from Broker's API to evaluate ROI
        :return: ranking of a pair following it's ROI/day
                 Map[Map.pair]:                                     {Pair}
                 Map[Map.fee]:                                      {float} # The fee charged for each transaction
                 Map[Map.number]:                                   {int}   # The number of period retrieve from
                                                                              Broker's API
                 Map[Map.period][rank{int}][Map.period]:            {int}   # Period in second
                 Map[Map.period][rank{int}][Map.roi]:               {float} # Roi evaluated with the given Strategy for
                                                                              this period
                 Map[Map.period][rank{int}][Map.day]:               {float} # ROI per day
                 Map[Map.period][rank{int}][Map.transaction]:       {dict}  # Result from
                                                                              Strategy.get_performance()
                 Map[Map.period][rank{int}][Map.rate]:              {List}  # Result from
                                                                              Strategy.performance_get_rates()
                 Map[Map.period][rank{int}][Map.rank][Map.sum]:     {int}   # Sum of period's rank and roi's rank
                 Map[Map.period][rank{int}][Map.rank][Map.roi]:     {int}   # Rank of top roi
                 Map[Map.period][rank{int}][Map.rank][Map.period]:  {int}   # Rank of this period in top interval
                                                                              (lower -> Higher)
        """
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        _bkr_cls = bkr.__class__.__name__
        # Sort intervals
        periods.sort()
        top_intervals = {periods[rank]: rank for rank in range(len(periods))}
        # Sort prepare top period's structure
        fees = bkr.get_trade_fee(pair)
        fee = fees.get(Map.taker)
        top_periods = []
        structures = Map({
            Map.pair: pair,
            # Map.pair: pair.__str__(),
            Map.fee: fee,
            Map.number: nb_period,
            Map.period: top_periods
        })
        mkt_rq_params = Map({
            Map.pair: pair,
            Map.period: None,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: nb_period
        })
        for period in periods:
            print(f"Getting {pair.__str__().upper()}'s performance for {nb_period} intervals of "
                  f"'{int(period / 60)} minutes'.")
            mkt_rq_params.put(period, Map.period)
            bkr_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_rq_params)
            bkr.request(bkr_rq)
            market_price = bkr_rq.get_market_price()
            perf = eval(f"{stg_class}.get_performance(bkr, stg_class, market_price)")
            roi = perf.get(Map.roi)
            roi_per_sec = roi / (period * nb_period)
            roi_per_h = roi_per_sec * 60 * 60
            roi_per_day = roi_per_h * 24
            top_period = {
                Map.period: market_price.get_period_time(),
                Map.roi: roi,
                Map.day: roi_per_day,
                Map.transaction: perf.get(Map.transaction),
                Map.rate: perf.get(Map.rate),
                Map.rank: {
                    Map.sum: None,
                    Map.period: top_intervals[period],
                    Map.roi: None
                }
            }
            top_periods.append(top_period)
        # structures.put(perf_periods, Map.period)  # Already put by reference
        top_roi = sorted(top_periods, key=lambda row: row[Map.day], reverse=True)
        for roi_rank in range(len(top_roi)):
            struc = top_roi[roi_rank]
            period_rank = struc[Map.rank][Map.period]
            struc[Map.rank][Map.sum] = period_rank + roi_rank
            struc[Map.rank][Map.roi] = roi_rank
        top_periods_sorted = sorted(top_periods, key=lambda row: (row[Map.rank][Map.sum], row[Map.rank][Map.period]))
        top_periods_keyed = {idx: top_periods_sorted[idx] for idx in range(len(top_periods_sorted))}
        structures.put(top_periods_keyed, Map.period)
        return structures

    @staticmethod   # Broker
    def get_top_volume(bkr: Broker, maximum: int = _TOP_ASSET_MAX) -> Map():
        """
        To get ranking of pairs with the higher trading volume in last 24h\n
        Note: Ordered from the higher to the lower
        Note: Volume are right asset in stablecoin asset
        :param bkr: Access to a Broker's API
        :param maximum: Number of pair to get
        :return: ranking of pairs with the higher trading volume in last 24h
                 Map[rank{int}][Map.pair]:      {Pair}
                 Map[rank{int}][Map.volume]:    {float} # In right asset
        """
        _bkr_cls = bkr.__class__.__name__
        bkr_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_24H_STATISTICS, Map())
        bkr.request(bkr_rq)
        stats_24h = bkr_rq.get_24h_statistics()
        stablecoins = Config.get(Config.CONST_STABLECOINS)
        concat_stable = '|'.join(stablecoins)
        regex_right = f"^\w+/({concat_stable})$"
        regex_left = f"^{concat_stable}/({concat_stable})$"
        # Get pair with USD stablecoin as right asset AND no USD stablecoin in left
        stats_24h_clean = {pair_str: row for pair_str, row in stats_24h.get_map().items()
                           if _MF.regex_match(regex_right, pair_str) and not _MF.regex_match(regex_left, pair_str)}
        # Sort dict from higher to lower volume
        stats_24h_sorted = dict(sorted(stats_24h_clean.items(),
                                       key=lambda row: row[1][Map.volume][Map.right], reverse=True))
        # Keep only one sample of each left asset
        stats_24h_no_duplic = {}
        lefts = []
        for pair_str, row in stats_24h_sorted.items():
            left = Pair(pair_str).get_left().get_symbol()
            if left not in lefts:
                stats_24h_no_duplic[pair_str] = row
                lefts.append(left)
        # Build top_volume
        pairs = list(stats_24h_no_duplic.keys())
        top_volume = Map({int(idx): {Map.pair: Pair(stats_24h_no_duplic[pairs[idx]][Map.pair]),
                                     Map.volume: stats_24h_no_duplic[pairs[idx]][Map.volume][Map.right]
                                     }
                          for idx in range(len(pairs)) if idx < maximum}
                         )
        return top_volume

    @staticmethod
    def _save_top_asset(stg_class: str, top_asset: Map) -> None:
        rows = []
        date = _MF.unix_to_date(_MF.get_timestamp())
        for rank, struc in top_asset.get_map().items():
            row = {
                Map.date: date,
                "strategy": stg_class,
                Map.rank: rank,
                f"{Map.rank}_{Map.sum}": struc[Map.rank][Map.sum],
                f"{Map.rank}_{Map.roi}": struc[Map.rank][Map.roi],
                f"{Map.rank}_{Map.volume}": struc[Map.rank][Map.volume],
                Map.pair: struc[Map.pair],
                f"{Map.period}_minutes": struc[Map.period][0][Map.period] / 60,
                Map.fee: struc[Map.fee],
                f"{Map.number}_{Map.period}": struc[Map.number],
                Map.roi: struc[Map.period][0][Map.roi],
                Map.day: struc[Map.period][0][Map.day],
                Map.volume: struc[Map.volume],
                Map.transaction: _MF.json_encode(struc[Map.period][0][Map.transaction]),
                Map.rate: _MF.json_encode(struc[Map.period][0][Map.rate])
            }
            rows.append(row)
        path = Config.get(Config.DIR_SAVE_TOP_ASSET)
        fields = list(rows[0].keys())
        FileManager.write_csv(path, fields, rows, overwrite=False)

    # ——————————————————————————————————————————— FUNCTION STATIC UP ———————————————————————————————————————————————————
