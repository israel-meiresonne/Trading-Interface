from typing import List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Paire import Pair


class Stalker(Strategy):
    _ALLOWED_PAIRS = None
    """
    Map[index{int}]:    {Pair}   # pair format: 'doge/usdt'
    """

    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:               {Strategy.__init__()}   # Same structure
               params[Map.number]:      {int}                   # Max number of active Strategy to manage in same time
               params[Map.strategy]:    {str}                   # Class name of Strategy to use
               params[Map.param]:       {dict}                  # Params for Strategy  to use
        """
        ks = [Map.number, Map.strategy, Map.param]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required")
        super().__init__(params)
        self.__pair = None
        self.__max_strategy = params.get(Map.number)
        self.__strategy_to_trade = params.get(Map.strategy)
        self.__strategy_params = Map(params.get(Map.param))
        self.__active_strategies = None
        """
        self.__active_strategies = Map({
            Pair('DOGE/USDT').__str__(): 'strategy',
            Pair('JUV/USDT').__str__(): 'strategy'
        })
        """

    def get_max_strategy(self) -> int:
        return self.__max_strategy

    def get_strategy_to_trade(self) -> str:
        return self.__strategy_to_trade

    def get_strategy_params(self) -> Map:
        return self.__strategy_params

    def get_active_strategies(self) -> Map:
        if self.__active_strategies is None:
            self.__active_strategies = Map()
        return self.__active_strategies

    def get_active_strategy(self, pair: Pair) -> Strategy:
        stgs = self.get_active_strategies()
        return stgs.get(pair.__str__())

    @staticmethod
    def _get_allowed_pairs(bkr: Broker) -> List[Pair]:
        """
        To get pair allowed to trade with this Strategy\n
        :param bkr: Access to Broker's API
        :return: Pair allowed to trade with this Strategy
        """
        if Stalker._ALLOWED_PAIRS is None:
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
            Stalker._ALLOWED_PAIRS = [Pair(pair_str) for pair_str in pair_strs]
        return Stalker._ALLOWED_PAIRS

    def _get_no_active_pairs(self, bkr: Broker) -> List[Pair]:
        allowed_pairs = Stalker._get_allowed_pairs(bkr)
        active_strategies = self.get_active_strategies()
        pair_strs = active_strategies.get_keys()
        no_active_pairs = [pair for pair in allowed_pairs if pair.__str__() not in pair_strs]
        no_active_pairs = [no_active_pairs[i] for i in range(len(no_active_pairs)) if i < 5]    # ❌
        # no_active_pairs.append(Pair('SUSD/USDT'))                                               # ❌
        # no_active_pairs.append(Pair('TRXDOWN/USDT'))                                            # ❌
        return no_active_pairs

    def _stalke_market(self, bkr: Broker) -> None:
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
        stg_class = self.get_strategy_to_trade()
        stg_params = self.get_strategy_params()
        stg_params.put(pair, Map.pair)
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        new_stg = eval(f"{stg_class}.generate_strategy(stg_class, stg_params)")
        active_strategies.put(new_stg, pair_str)

    def _delete_active_strategy(self, bkr: Broker, pair: Pair) -> None:
        active_strategies = self.get_active_strategies()
        pair_str = pair.__str__()
        if pair_str not in active_strategies.get_keys():
            # raise ValueError(f"Can't delete active Strategy with this pair '{pair_str.upper()}' cause don't exist.")
            raise ValueError(f"There's no active Strategy with this pair '{pair_str.upper()}' to delete.")
        strategy = active_strategies.get(pair_str)
        strategy.stop_trading(bkr)
        del active_strategies.get_map()[pair_str]

    def trade(self, bkr: Broker) -> None:
        pass

    def stop_trading(self, bkr: Broker) -> None:
        pass

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'Stalker':
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
        Strategy._generate_strategy_treat_params(params)
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        return eval(f"{stg_class}(params)")

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


