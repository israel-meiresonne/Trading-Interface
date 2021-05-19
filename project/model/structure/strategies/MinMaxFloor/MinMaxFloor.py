from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.strategies.Floor.Floor import Floor
from model.structure.strategies.MinMax.MinMax import MinMax
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Paire import Pair


class MinMaxFloor(Strategy):
    _CONST_MARKET_PRICE = "MARKET_PRICE"

    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:                       {Strategy.__init__()}   # Same structure
               params[Map.period]:              {int}   # Period interval in second
               params[Map.green][Map.period]:   {int}   # Period interval in second
               params[Map.red][Map.period]:     {int}   # Period interval in second
        """
        super().__init__(params)
        # self.__green_strategy = Strategy.generate_strategy(MinMax.__name__, Map(params.get(Map.green)))
        # self.__red_strategy = Strategy.generate_strategy(Floor.__name__, Map(params.get(Map.red)))
        self.__green_strategy = MinMax(Map(params.get(Map.green)))
        self.__red_strategy = Floor(Map(params.get(Map.red)))
        self.__best_period = params.get(Map.period)
        self.__active_strategy = None
        self.__configs = None
        self._init_strategies(params)

    def _init_strategies(self, params: Map) -> None:
        orders = self._get_orders()
        red_strategy = self.get_red_strategy()
        green_strategy = self.get_green_strategy()
        red_strategy._set_orders(orders)
        green_strategy._set_orders(orders)

    def _init_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            # Set Configs
            self._init_constants(bkr)

    def _init_constants(self, bkr: Broker) -> None:
        self.__configs = Map({
            self._CONST_MARKET_PRICE: Map({
                Map.pair: self.get_pair(),
                Map.period: self.get_best_period(),
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 100
            })
        })

    def _get_constants(self) -> Map:
        return self.__configs

    def _get_constant(self, k) -> [float, Map]:
        configs = self._get_constants()
        if k not in configs.get_keys():
            raise IndexError(f"There's  not constant for this key '{k}'")
        return configs.get(k)

    def get_best_period(self) -> int:
        return self.__best_period

    def get_green_strategy(self) -> MinMax:
        return self.__green_strategy

    def get_red_strategy(self) -> Floor:
        return self.__red_strategy

    def _set_active_strategy(self, strategy: Strategy) -> None:
        self.__active_strategy = strategy

    def get_active_strategy(self) -> Strategy:
        return self.__active_strategy

    def _get_market_price(self, bkr: Broker) -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        _bkr_cls = bkr.__class__.__name__
        mkt_params = self._get_constant(self._CONST_MARKET_PRICE)
        bkr_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_params)
        bkr.request(bkr_rq)
        return bkr_rq.get_market_price()

    def trade(self, bkr: Broker) -> None:
        self._init_strategy(bkr)
        market_price = self._get_market_price(bkr)
        # Switch
        self._switch_strategy(bkr, market_price)
        self.get_active_strategy().trade(bkr)

    def stop_trading(self, bkr: Broker) -> None:
        self.get_green_strategy().stop_trading(bkr)
        self.get_red_strategy().stop_trading(bkr)

    def _switch_strategy(self, bkr: Broker, market_price: MarketPrice) -> None:
        # Extract list
        closes = list(market_price.get_closes())
        closes.reverse()
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        # Switch
        trend = MarketPrice.get_super_trend_trend(closes, super_trends, -1)
        active_strategy = self.get_active_strategy()
        if trend == MarketPrice.SUPERTREND_RISING:
            green_strategy = self.get_green_strategy()
            if id(active_strategy) != id(green_strategy):
                self.get_red_strategy().stop_trading(bkr)
                self._set_active_strategy(green_strategy)
        elif trend == MarketPrice.SUPERTREND_DROPPING:
            red_strategy = self.get_red_strategy()
            if id(active_strategy) != id(red_strategy):
                self.get_green_strategy().stop_trading(bkr)
                self._set_active_strategy(red_strategy)
        else:
            raise Exception(f"Unknown trend '{trend}' of SuperTrend")

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'MinMaxFloor':
        keys = params.get_keys()
        new_params = Map({key: params.get(key) for key in keys if (key != Map.green) and (key != Map.red)})
        Strategy._generate_strategy_treat_params(new_params)
        # Set red params
        green_params = dict(new_params.get_map())
        green_params[Map.period] = params.get(Map.green, Map.period)
        # Set green params
        red_params = dict(new_params.get_map())
        red_params[Map.period] = params.get(Map.red, Map.period)
        # Set params
        new_params.put(green_params, Map.green)
        new_params.put(red_params, Map.red)
        return MinMaxFloor(new_params)

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        green_rates = MinMax.performance_get_rates(market_price)
        red_rates = Floor.performance_get_rates(market_price)
        rates = [*red_rates, *green_rates]
        return rates
