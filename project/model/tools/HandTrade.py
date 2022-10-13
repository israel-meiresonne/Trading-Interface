from typing import Callable
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Trade import Trade


class HandTrade(Trade):
    PREFIX_ID = 'handtrade_'

    def __init__(self, buy_order: Order, buy_function: Callable = None, sell_function: Callable = None) -> None:
        super().__init__(buy_order)
        self.__buy_function =   None
        self.__sell_function =  None
        self.set_buy_function(buy_function) if buy_function is not None else None
        self.set_sell_function(sell_function) if sell_function is not None else None

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————

    def set_buy_function(self, buy_function: Callable) -> None:
        if not callable(buy_function):
            raise ValueError(f"The buy function must be callable, instead '{buy_function}'(type={type(buy_function)})")
        self.__buy_function = buy_function.__name__

    def get_buy_function(self, to_call: object) -> Callable:
        """
        To get function to execute to buy position

        Parameters:
        -----------
        to_call: object
            Object or class to call

        Returns:
        --------
        return: Callable
            Function to execute to buy position
        """
        function_name = self.__buy_function
        return eval(f"to_call.{function_name}")

    def set_sell_function(self, sell_function: Callable) -> None:
        if not callable(sell_function):
            raise ValueError(f"The sell function must be callable, instead '{sell_function}'(type={type(sell_function)})")
        self.__sell_function = sell_function.__name__

    def get_sell_function(self, to_call: object) -> Callable:
        """
        To get function to execute to sell position

        Parameters:
        -----------
        to_call: object
            Object or class to call

        Returns:
        --------
        return: Callable
            Function to execute to sell position
        """
        function_name = self.__sell_function
        return eval(f"to_call.{function_name}")

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

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
        instance = HandTrade(buy_order)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————

