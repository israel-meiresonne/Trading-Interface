import copy
from typing import Any, Tuple

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class BinanceFakeOrder(MyJson):
    _IDS = []
    _NO_API_ATTRIBUTS = [Map.ready, Map.submit, Map.param, Map.market]

    def __init__(self, params: Map, market_datas: Map) -> None:
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        self.__symbol = params.get(Map.symbol).upper()
        self.__type = params.get(Map.type)
        self.__side = params.get(Map.side)
        self.__status = BinanceAPI.STATUS_ORDER_NEW
        self.__orderId = self.new_id()
        self.__clientOrderId = params.get(Map.newClientOrderId)
        self.__origClientOrderId = None
        self.__orderListId = -1
        self.__price = params.get(Map.price)
        self.__stopPrice = params.get(Map.stopPrice)
        self.__origQty = params.get(Map.quantity)
        self.__icebergQty = params.get(Map.icebergQty)
        self.__executedQty = 0
        self.__cummulativeQuoteQty = 0
        self.__timeInForce = params.get(Map.timeInForce)
        self.__time = None
        self.__isWorking = None
        self.__updateTime = None
        self.__transactTime = None
        self.__fills = None
        # Not API Attributs
        self.__ready = False    # Set True if order is reeady be executed else False
        self.__submit = None    # Market's close price at order's creation
        self.__param = Map(params.get_map())
        self.__market = Map(market_datas.get_map())
        self._set_attributs()

    def _set_attributs(self) -> None:
        market_datas = self.get_attribut(Map.market)
        market_close_price = market_datas.get(Map.close)
        market_time = market_datas.get(Map.time)
        self._set_attribut(Map.time, market_time)
        self._set_attribut(Map.updateTime, market_time)
        self._set_attribut(Map.submit, market_close_price)

    def get_attribut(self, attribut: str) -> Any:
        """
        To get any attribut
        """
        key = self._attribut_key(attribut)
        return self.__dict__[key]

    def _set_attribut(self, attribut: str, value: Any) -> None:
        """
        To set anyy attribut
        """
        key = self._attribut_key(attribut)
        self.__dict__[key] = value

    def is_buyer(self) -> bool:
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        side = self.get_attribut(Map.side)
        if side == BinanceAPI.SIDE_BUY:
            isBuyer = True
        elif side == BinanceAPI.SIDE_SELL:
            isBuyer = False
        else:
            raise ValueError(f"This side '{side}' is not supported")
        return isBuyer

    def try_execute(self, market_datas: Map) -> None:
        """
        To try to execute the order
        """
        from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
        def limit_reached(is_buyer: bool, close_price: float) -> None:
            limit_price = self.get_attribut(Map.price)
            return (is_buyer and (close_price <= limit_price)) or ((not is_buyer) and (close_price >= limit_price))

        _api = BinanceFakeAPI
        if self.get_attribut(Map.status) not in [_api.STATUS_ORDER_NEW, _api.STATUS_ORDER_PARTIALLY]:
            return None
        # Attributs
        order_type = self.get_attribut(Map.type)
        is_buyer = self.is_buyer()
        # Market
        market_close_price = market_datas.get(Map.close)
        # Check
        if order_type == _api.TYPE_MARKET:
            self._set_attribut(Map.ready, True)
            self._execute(market_datas)
        elif order_type == _api.TYPE_STOP_LOSS:
            stop_price = self.get_attribut(Map.stopPrice)
            if (is_buyer and (market_close_price >= stop_price)) or ((not is_buyer) and (market_close_price <= stop_price)):
                self._set_attribut(Map.ready, True)
                self._execute(market_datas)
        elif order_type == _api.TYPE_LIMIT:
            if limit_reached(is_buyer, market_close_price):
                self._set_attribut(Map.ready, True)
                self._execute(market_datas)
        elif order_type == _api.TYPE_STOP_LOSS_LIMIT:
            def stop_reached(close_price: float) -> bool:
                """
                To stop price is reached
                NOTE: stop price is reached if market's price come through the stop price
                """
                submit_price = self.get_attribut(Map.submit)
                stop_price = self.get_attribut(Map.stopPrice)
                is_stop_reached = (close_price <= stop_price) if (submit_price >= stop_price) else (close_price >= stop_price)
                return is_stop_reached

            if (not self.get_attribut(Map.ready)) and stop_reached(market_close_price):
                self._set_attribut(Map.ready, True)
            if self.get_attribut(Map.ready):
                if limit_reached(is_buyer, market_close_price):
                    self._execute(market_datas)
        else:
            raise Exception(f"This order type '{order_type}' is not supported")

    def _execute(self, market_datas: Map) -> None:
        """
        To execute the order
        """
        from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
        def execution_values(exec_price: float, asked_amount: float, asked_quantity: float) -> Tuple[float, float]:
            if asked_quantity is not None:
                exec_quantity = asked_quantity
                exec_amount = exec_quantity * exec_price
            else:
                exec_amount = asked_amount
                exec_quantity = exec_amount/exec_price
            return exec_amount, exec_quantity

        def execution_fee(fee_rate: float, exec_amount: float, exec_quantity: float, is_buyer: bool, pair: Pair) -> Tuple[float, Asset]:
            if is_buyer:
                fee = exec_quantity * fee_rate
                fee_asset = pair.get_left()
            else:
                fee = exec_amount * fee_rate
                fee_asset = pair.get_right()
            return Price(fee, fee_asset).get_value(), fee_asset

        if not self.get_attribut(Map.ready):
            order_type = self.get_attribut(Map.type)
            raise Exception(
                f"Order of type '{order_type}' is not ready to be executed")
        _api = BinanceFakeAPI
        # Attributs
        order_type = self.get_attribut(Map.type)
        merged_pair = self.get_attribut(Map.symbol)
        pair = Pair(_api.symbol_to_pair(merged_pair))
        is_buyer = self.is_buyer()
        # Fees
        fees_rates = _api.get_trade_fee(pair)
        # Market
        market_close_price = market_datas.get(Map.close)
        market_unix_time = market_datas.get(Map.time)
        if order_type == _api.TYPE_MARKET:
            is_maker = False
            exec_price = market_close_price
        elif order_type == _api.TYPE_STOP_LOSS:
            is_maker = False
            exec_price = market_close_price
        elif order_type in [_api.TYPE_LIMIT, _api.TYPE_STOP_LOSS_LIMIT]:
            is_maker = True
            exec_price = self.get_attribut(Map.price)
        else:
            raise Exception(f"This order type '{order_type}' is not supported")
        request_params = self.get_attribut(Map.param)
        asked_quantity = request_params.get(Map.quantity)
        asked_amount = request_params.get(Map.quoteOrderQty)
        exec_amount, exec_quantity = execution_values(exec_price, asked_amount, asked_quantity)
        fee_rate = fees_rates.get(Map.maker) if is_maker else fees_rates.get(Map.taker)
        fee, fee_asset = execution_fee(fee_rate, exec_amount, exec_quantity, is_buyer, pair)
        trade_id = self.new_id()
        fills = [{
            Map.symbol: merged_pair,
            Map.id: trade_id,
            Map.orderId: self.get_attribut(Map.orderId),
            Map.tradeId: trade_id,
            Map.orderListId: -1,
            Map.price: exec_price,
            Map.qty: exec_quantity,
            Map.commission: fee,
            Map.commissionAsset: fee_asset.__str__().upper(),
            Map.quoteQty: exec_amount,
            Map.time: market_unix_time,
            Map.isBuyer: is_buyer,
            Map.isMaker: is_maker,
            Map.isBestMatch: None
        }]
        self._set_attribut(Map.fills, fills)
        self._set_attribut(Map.status, _api.STATUS_ORDER_FILLED)
        self._set_attribut(Map.origQty, exec_quantity)
        self._set_attribut(Map.executedQty, exec_quantity)
        self._set_attribut(Map.cummulativeQuoteQty, exec_amount)
        self._set_attribut(Map.updateTime, market_unix_time)
        self._set_attribut(Map.transactTime, market_unix_time)

    def cancel(self) -> dict:
        """
        To cancel the order

        Return:
        -------
        return: dict
            The order's canceled state in API's format
        """
        from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
        _api = BinanceFakeAPI
        status = self.get_attribut(Map.status)
        if status != _api.STATUS_ORDER_NEW:
            raise Exception(f"Can't cancel an order with this status '{status}'")
        new_id = f"cancel_{_MF.new_code()}"
        old_id = self.get_attribut(Map.clientOrderId)
        self._set_attribut(Map.origClientOrderId, old_id)
        self._set_attribut(Map.clientOrderId, new_id)
        self._set_attribut(Map.status, _api.STATUS_ORDER_CANCELED)
        return self.to_dict()

    def to_dict(self) -> dict:
        """
        To convert order to dict in API format
        """
        attributs = self.attribut_to_values()
        for key in self._NO_API_ATTRIBUTS:
            del attributs[key]
        return attributs

    def attribut_to_values(self) -> dict[str, Any]:
        """
        To get dict with name of attributs and their values
        """
        class_key = self._class_key()
        attribut_dict = self.__dict__
        attributs = {key.replace(class_key, ''): value for key, value in attribut_dict.items()}
        return attributs

    @staticmethod
    def new_id() -> int:
        _cls = BinanceFakeOrder
        new_id = None
        while not new_id:
            new_id = _MF.get_timestamp(_MF.TIME_MILLISEC)
            new_id = None if new_id in _cls._IDS else new_id
        _cls._IDS.append(new_id)
        return new_id

    @staticmethod
    def _class_key() -> str:
        """
        To get prefix of keys in __dic__
        """
        class_name = BinanceFakeOrder.__name__
        return f"_{class_name}__"

    @staticmethod
    def _attribut_key(attribut: str) -> str:
        """
        To generate key to access order's attribut through's dict
        """
        class_key = BinanceFakeOrder._class_key()
        return class_key + attribut

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        params = Map({Map.symbol: 'xxx'})
        market_datas = Map({Map.close: -1})
        instance = BinanceFakeOrder(params, market_datas)
        exec(MyJson.get_executable())
        return instance
