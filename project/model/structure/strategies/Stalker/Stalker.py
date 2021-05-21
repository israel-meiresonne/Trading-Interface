from typing import List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Paire import Pair
from model.tools.Price import Price


class Stalker(Strategy):
    _CONST_MARKET_PRICE = "MARKET_PRICE"
    _CONST_STALK_INTERVAL = 60 * 60
    _CONST_ALLOWED_PAIRS = None
    _CONST_MAX_STRATEGY = 3

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
        self.__pair = Pair(f'?/{right_symbol}')
        self.__next_stalk = None
        self.__transactions = None
        self.__max_strategy = Stalker._CONST_MAX_STRATEGY
        self.__strategy_class = params.get(Map.strategy)
        child_stg_params = params.get(Map.param)
        self._set_strategy_params(Map(child_stg_params))
        self.__active_strategies = None

    def get_max_strategy(self) -> int:
        return self.__max_strategy

    def _set_next_stalk(self, unix_time: int) -> None:
        self.__next_stalk = unix_time

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

    def get_active_strategies(self) -> Map:
        if self.__active_strategies is None:
            self.__active_strategies = Map()
        return self.__active_strategies

    def get_active_strategy(self, pair: Pair) -> Strategy:
        stgs = self.get_active_strategies()
        return stgs.get(pair.__str__())

    def _get_no_active_pairs(self, bkr: Broker) -> List[Pair]:
        allowed_pairs = Stalker._get_allowed_pairs(bkr)
        active_strategies = self.get_active_strategies()
        pair_strs = active_strategies.get_keys()
        no_active_pairs = [pair for pair in allowed_pairs if pair.__str__() not in pair_strs]
        no_active_pairs = [no_active_pairs[i] for i in range(len(no_active_pairs)) if i < 5]    # ❌
        # no_active_pairs.append(Pair('SUSD/USDT'))                                               # ❌
        # no_active_pairs.append(Pair('TRXDOWN/USDT'))                                            # ❌
        return no_active_pairs

    def _can_stalk(self) -> bool:
        active_strategies = self.get_active_strategies()
        max_strategy = self.get_max_strategy()
        max_reached = len(active_strategies.get_map()) >= max_strategy
        unix_time = _MF.get_timestamp()
        next_stalk = self.get_next_stalk()
        time_to_stalk = (next_stalk is None) or (unix_time >= next_stalk)
        return (not max_reached) and time_to_stalk

    def _stalk_market(self, bkr: Broker) -> None:
        _stg_cls = Stalker.__name__
        _bkr_cls = bkr.__class__.__name__
        max_strategy = self.get_max_strategy()
        active_strategies = self.get_active_strategies()
        pairs = self._get_no_active_pairs(bkr)
        perfs = Map()
        market_prices = Map()
        market_params = Map({
            Map.pair: None,
            Map.period: 60 * 60,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 1000
        })
        for pair in pairs:
            pair_str = pair.__str__()
            market_params.put(pair, Map.pair)
            market_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, market_params)
            bkr.request(market_rq)
            market_price = market_rq.get_market_price()
            perf = Strategy.get_performance(bkr, _stg_cls, market_price)
            perfs.put(perf.get_map(), pair_str)
            market_prices.put(market_price, pair_str)
        perfs_sorted = dict(sorted(perfs.get_map().items(), key=lambda row: row[1][Map.roi], reverse=True))
        for pair_str, perf in perfs_sorted.items():
            market_price = market_prices.get(pair_str)
            if Stalker._eligible(market_price):
                self._add_active_strategy(Pair(pair_str))
                if len(active_strategies.get_map()) >= max_strategy:
                    break
        next_stalk = _MF.get_timestamp() + self.get_stalk_interval()
        self._set_next_stalk(next_stalk)

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
        # Delete active Strategy
        del active_stgs.get_map()[pair_str]

    def trade(self, bkr: Broker) -> None:
        self._stalk_market(bkr) if self._can_stalk() else None
        self._manage_strategies(bkr)

    def _manage_strategies(self, bkr: Broker) -> None:
        active_stgs = self.get_active_strategies()
        for pair_str, active_stg in active_stgs.get_map().items():
            pair = active_stg.get_pair()
            market_price = self._get_market_price(bkr, pair)
            closes = list(market_price.get_closes())
            closes.reverse()
            super_trends = list(market_price.get_super_trend())
            super_trends.reverse()
            trend = MarketPrice.get_super_trend_trend(closes, super_trends, -1)
            if trend == MarketPrice.SUPERTREND_RISING:
                active_stg.trade(bkr)
            elif trend == MarketPrice.SUPERTREND_DROPPING:
                self._delete_active_strategy(bkr, pair)
            else:
                raise Exception(f"Unknown trend '{trend}' of SuperTrend.")

    def stop_trading(self, bkr: Broker) -> None:
        pass

    @staticmethod
    def get_stalk_interval() -> int:
        """
        To get interval (in second) between each market stalk\n
        :return: interval (in second) between each market stalk
        """
        return Stalker._CONST_STALK_INTERVAL

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
            Map.period: Stalker.get_stalk_interval(),
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
            # Stablecoin regex
            stablecoins = Config.get(Config.CONST_STABLECOINS)
            concat_stable = '|'.join(stablecoins)
            stablecoin_rgx = f'({concat_stable})/\w+$'
            # Fiat regex
            fiats = Config.get(Config.CONST_FIATS)
            concat_fiat = '|'.join(fiats)
            fiat_rgx = f'({concat_fiat})/\w+$'
            # Get pairs
            no_match = ['^\w+(up|down|bear|bull)\/\w+$', '^(bear|bull)/\w+$', '^\w*inch\w*/\w+$',fiat_rgx, stablecoin_rgx]
            match = ['^.+\/usdt']
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
        eligible = False
        # Extract closes
        closes = list(market_price.get_closes())
        closes.reverse()
        # Extract supertrend
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        trend = MarketPrice.get_super_trend_trend(closes, super_trends, -1)
        if trend == MarketPrice.SUPERTREND_RISING:
            super_trend_switchs = MarketPrice.get_super_trend_switchers(closes, super_trends)
            index_to_switch_index = super_trend_switchs.get_keys()
            last_red_close_index = index_to_switch_index[-1] - 1
            last_red_close = closes[last_red_close_index]
            super_trend = super_trends[-1]
            eligible = super_trend <= last_red_close
        return eligible

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


