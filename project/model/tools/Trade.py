from typing import Dict, Tuple
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Trade(MyJson):
    PREFIX_ID = 'trade_'

    def __init__(self, buy_order: Order) -> None:
        self.__id =         self.PREFIX_ID + _MF.new_code()
        self.__settime =    _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        self.__buy_order =  None
        self.__sell_order = None
        self.__min_price =  None
        self.__max_price =  None
        self._set_buy_order(buy_order)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————

    def get_id(self) -> str:
        return self.__id

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def _set_buy_order(self, buy_order: Order) -> None:
        if buy_order.get_move() != Order.MOVE_BUY:
            raise ValueError(f"The buy order's move must be '{Order.MOVE_BUY}', instead '{buy_order.get_move()}'")
        self.__buy_order = buy_order

    def get_buy_order(self) -> Order:
        """
        To get the buy order used to take position

        Returns:
        --------
        return: Order
            The buy order used to take position
        """
        return self.__buy_order

    def reset_sell_order(self) -> None:
        self.__sell_order = None

    def set_sell_order(self, sell_order: Order) -> None:
        buy_order = self.get_buy_order()
        if buy_order is None:
            raise Exception(f"The buy order must be set first")
        if buy_order.get_pair() != sell_order.get_pair():
            raise ValueError(f"The sell order must share the same Pair than buy's '{buy_order.get_pair().__str__().upper()}', instead '{sell_order.get_pair().__str__().upper()}'")
        if sell_order.get_move() != Order.MOVE_SELL:
            raise ValueError(f"The sell order's move must be '{Order.MOVE_SELL}', instead '{sell_order.get_move()}'")
        self.__sell_order = sell_order

    def get_sell_order(self) -> Order:
        """
        To get the sell order used to take position

        Returns:
        --------
        return: Order
            The sell order used to take position
        """
        return self.__sell_order

    def _set_min_price(self, min_price: float) -> None:
        if not self.is_closed():
            raise Exception(f"The min price can't be set if Trade is not closed")
        self.__min_price = float(min_price) if not _MF.is_nan(min_price) else None

    def get_min_price(self) -> float:
        """
        To get min price reached since buy

        Returns:
        --------
        return: float
            Min price reached since buy
            NOTE: return None if Trade is not closed
        """
        min_price = self.__min_price
        return float('nan') if min_price is None else min_price

    def _set_max_price(self, max_price: float) -> None:
        if not self.is_closed():
            raise Exception(f"The max price can't be set if Trade is not closed")
        self.__max_price = float(max_price) if not _MF.is_nan(max_price) else None

    def get_max_price(self) -> float:
        """
        To get max price reached since buy

        Returns:
        --------
        return: float
            Max price reached since buy
            NOTE: return None if Trade is not closed
        """
        max_price = self.__max_price
        return float('nan') if max_price is None else max_price

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    def is_submitted(self) -> bool:
        """
        To check if buy and sell Order are submitted to Broker for execution
        NOTE: only check for the buy Order if the sell Order is not set

        Returns:
        --------
        return: bool
            True if all Order set are submitted to Broker else False
        """
        buy_order = self.get_buy_order()
        buy_is_submitted = buy_order.get_status() is not None
        sell_order = self.get_sell_order()
        sell_is_submitted = sell_order.get_status() is not None if sell_order is not None else True
        return buy_is_submitted and sell_is_submitted

    def is_executed(self, side: str) -> bool:
        """
        To check if buy or sell Order are executed

        Parameters:
        -----------
        side: str
            Name of order to check ['buy' or 'sell']

        Returns:
        --------
        return: bool
            True if Order is executed else False
        """
        if side == Map.buy:
            is_executed = self.get_buy_order().get_status() == Order.STATUS_COMPLETED
        elif side == Map.sell:
            sell_order = self.get_sell_order()
            is_executed = (sell_order is not None) and (sell_order.get_status() == Order.STATUS_COMPLETED)
        else:
            raise ValueError(f"Unkown Order side '{side}'")
        return is_executed

    def is_closed(self) -> bool:
        """
        To check if Trade's buy and sell Order are executed

        Returns:
        --------
        return: bool
            True if Trade's buy and sell Order are executed else False
        """
        return self.is_executed(Map.buy) and self.is_executed(Map.sell)

    def has_failed(self, side: str) -> Dict[str, bool]:
        """
        Check if buy or sell Order will never be executed because of any failure

        Parameters:
        -----------
        side: str
            Side of Order to check [Map.buy or Map.sell]

        Returns:
        --------
        return: bool
            True if the buy or sell Order have failed else False
        """
        fail_status = [Order.STATUS_FAILED, Order.STATUS_EXPIRED]
        if side == Map.buy:
            has_fails = self.get_buy_order().get_status() in fail_status
        elif side == Map.sell:
            sell_order = self.get_sell_order()
            has_fails = (sell_order is not None) and (sell_order.get_status() in fail_status)
        else:
            raise ValueError(f"Unkown Order side '{side}'")
        return has_fails

    def has_position(self) -> bool:
        """
        To check if Trade has bought a position and not sold it yet

        Returns:
        --------
        return: bool
            True if has position else False
        """
        return self.is_executed(Map.buy) and (not self.is_closed())

    def extrem_prices(self, broker: Broker) -> Map:
        """
        To get min & max price reached since buy

        Parameters:
        -----------
        broker: Broker
            Access to a broker's API

        Returns:
        --------
        return: Map
            Max & min price reached since buy
            map[Map.minimum]:   float   # The min price rached since buy
            map[Map.maximum]:   float   # The max price rached since buy
        """
        if self.is_executed(Map.buy) and (_MF.is_nan(self.get_min_price()) or _MF.is_nan(self.get_max_price())):
            buy_order = self.get_buy_order()
            pair = buy_order.get_pair()
            buy_time = int(buy_order.get_execution_time()/1000)
            sell_order = self.get_sell_order()
            sell_time = int(sell_order.get_execution_time()/1000) if self.is_executed(Map.sell) else _MF.get_timestamp()
            min_price, max_price = self._extrem_prices(broker, pair, buy_time, sell_time)
            if self.is_closed():
                self._set_min_price(min_price)
                self._set_max_price(max_price)
        else:
            min_price = self.get_min_price()
            max_price = self.get_max_price()
        return Map({
            Map.minimum: min_price,
            Map.maximum: max_price
        })

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @classmethod
    def _extrem_prices(cls, broker: Broker, pair: Pair, buy_time: int, sell_time: int) -> Tuple[float, float]:
        """
        To get min & max price reached since buy
        NOTE: return NAN if buy and sell time are in the same minute

        Parameters:
        -----------
        broker: Broker
            Access to a broker's API
        pair: Pair
            Trade's pair
        buy_time: int
            Buy time in second
        sell_time: int
            Buy time in second

        Returns:
        --------
        return: Tuple[float, float]
            Min & max price reached since buy
            tuple[0]:   float   # min price reached
            tuple[1]:   float   # max price reached
        """
        period_1min = broker.PERIOD_1MIN
        buy_time_1min = _MF.round_time(buy_time, period_1min)
        sell_time_1min = _MF.round_time(sell_time, period_1min)
        if buy_time_1min != sell_time_1min:
            marketprices = MarketPrice.marketprices(broker, pair, period_1min, endtime=sell_time_1min, starttime=buy_time_1min)
            final_time = sell_time_1min if sell_time_1min is not None else int(marketprices.iloc[-1,0]/1000)
            marketprices_position = marketprices.loc[(marketprices.iloc[:,0] > int(buy_time_1min*1000)) & ((marketprices.iloc[:,0] <= int(final_time*1000)))]
            min_price = float(marketprices_position.iloc[:,3].min())
            max_price = float(marketprices_position.iloc[:,2].max())
        else:
            min_price = float('nan')
            max_price = float('nan')
        return min_price, max_price

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        from model.API.brokers.Binance.Binance import Binance
        _class_token = MyJson.get_class_name_token()
        pair = Pair('JSON/@JSON')
        buy_order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(10, pair.get_right()),
            Map.stop: None,
            Map.limit: None
        })
        buy_order = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, buy_order_params)
        instance = Trade(buy_order)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————

