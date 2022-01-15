from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class BinanceOrder(Order):
    CONV_STATUS = Map({
        BinanceAPI.STATUS_ORDER_NEW: Order.STATUS_SUBMITTED,
        BinanceAPI.STATUS_ORDER_PARTIALLY: Order.STATUS_PROCESSING,
        BinanceAPI.STATUS_ORDER_FILLED: Order.STATUS_COMPLETED,
        BinanceAPI.STATUS_ORDER_CANCELED: Order.STATUS_CANCELED,
        BinanceAPI.STATUS_ORDER_PENDING_CANCEL: Order.STATUS_CANCELED,
        BinanceAPI.STATUS_ORDER_REJECTED: Order.STATUS_FAILED,
        BinanceAPI.STATUS_ORDER_EXPIRED: Order.STATUS_EXPIRED
    })
    _CONV_ORDER_MOVE = Map({
        BinanceAPI.SIDE_BUY: Order.MOVE_BUY,
        BinanceAPI.SIDE_SELL: Order.MOVE_SELL
    })

    def __init__(self, odr_type: str, params: Map) -> None:
        super().__init__(odr_type, params)
        self.__api_request = None
        exec(f"self.{odr_type}()")

    def _set_limit_price(self, limit: Price) -> None:
        self._limit = BinanceAPI.fixe_price(self.get_pair(), limit)

    def _set_stop_price(self, stop: Price) -> None:
        self._stop = BinanceAPI.fixe_price(self.get_pair(), stop)

    def _set_quantity(self, quanty: Price) -> None:
        pair = self.get_pair()
        new_qty = BinanceAPI.fixe_quantity(pair, quanty, False)
        is_market_order = self.get_type() == self.TYPE_MARKET
        self._quantity = BinanceAPI.fixe_quantity(pair, new_qty, is_market_order) if is_market_order else new_qty

    def __set_api_request(self, rq: str) -> None:
        self.__api_request = rq

    def get_api_request(self) -> str:
        return self.__api_request

    def _set_market(self) -> None:
        mkt_prms = self._extract_market_params()
        self.__set_api_request(self._exract_market_request())
        self._set_request_params(mkt_prms)

    def _extract_market_params(self) -> Map:
        """
        To extract params required for a market Order\n
        :return: params required for a market Order
                        params[Map.symbol]              => {str}
                        params[Map.side]                => {str}
                        params[Map.type]                => "MARKET"
                        params[Map.quantity]            => {float}
                        params[Map.quoteOrderQty]       => {float}
                        params[Map.newClientOrderId]    => {str|None}
                        params[Map.recvWindow]          => {int|None}
        """
        # convert
        mkt_prms = Map({
            Map.symbol: self.get_pair().get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY if self.get_move() == self.MOVE_BUY else BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.quantity: self.get_quantity().get_value() if self.get_quantity() is not None else None,
            Map.quoteOrderQty: self.get_amount().get_value() if self.get_amount() is not None else None,
            Map.newClientOrderId: self.get_id(),
            Map.recvWindow: None
        })
        return mkt_prms

    def _exract_market_request(self) -> str:
        qty = self.get_quantity()
        amount = self.get_amount()
        if (qty is not None) and (amount is not None):
            raise ValueError(f"Params '{Map.quantity}' or '{Map.quoteOrderQty}' can't both be set")
        if qty is not None:
            rq = BinanceAPI.RQ_ORDER_MARKET_qty
        elif amount is not None:
            rq = BinanceAPI.RQ_ORDER_MARKET_amount
        else:
            raise ValueError(f"Params '{Map.quantity}' or '{Map.quoteOrderQty}' must be set")
        return rq

    def _set_limit(self) -> None:
        pass

    def _set_stop(self) -> None:
        mkt_prms = self._extract_stop_params()
        self.__set_api_request(BinanceAPI.RQ_ORDER_STOP_LOSS)
        self._set_request_params(mkt_prms)

    def _extract_stop_params(self) -> Map:
        """
        To extract params required for a stop Order\n
        :param params: where to extract params for a stop Order
        :return: params required for a stop Order
        """
        # Extract
        mkt_params = Map({
            Map.symbol: self.get_pair().get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY if self.get_move() == self.MOVE_BUY else BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_STOP,
            Map.quantity: self.get_quantity().get_value() if self.get_quantity() is not None else None,
            Map.stopPrice: self.get_stop_price().get_value(),
            # Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.quoteOrderQty: None,
            Map.price: None,
            Map.newClientOrderId: self.get_id(),
            Map.icebergQty: None,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL,
            Map.recvWindow: None
        })
        return mkt_params

    def _set_stop_limit(self) -> None:
        mkt_prms = self._extract_stop_limit_params()
        self.__set_api_request(BinanceAPI.RQ_ORDER_STOP_LOSS_LIMIT)
        self._set_request_params(mkt_prms)

    def _extract_stop_limit_params(self) -> Map:
        """
        To extract params required for a stop limit Order\n
        :return: params required for a stop limit Order
        """
        api_params = Map({
            # Mandatory Down
            Map.symbol: self.get_pair().get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY if self.get_move() == self.MOVE_BUY else BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_STOP_LOSS_LIMIT,
            Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.quantity: self.get_quantity().get_value(),
            Map.price: self.get_limit_price().get_value(),
            Map.stopPrice: self.get_stop_price().get_value(),
            # Mandatory Up
            Map.quoteOrderQty: None,
            Map.newClientOrderId: self.get_id(),
            Map.icebergQty: None,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL,
            Map.recvWindow: None
        })
        return api_params

    def generate_order(self) -> Map:
        prms = self._get_request_params()
        prms.put(prms.get(Map.symbol).upper(), Map.symbol)
        prms.put(prms.get(Map.side).upper(), Map.side)
        # self._set_status(self.STATUS_SUBMITTED)
        # Backup
        from model.tools.Orders import Orders
        Orders.insert_order(Orders.SAVE_ACTION_GENERATE, self)
        return Map(_MF.clean(prms.get_map()))

    def generate_cancel_order(self) -> Map:
        cancel_params = Map({
            Map.symbol: self.get_pair().get_merged_symbols().upper(),
            Map.orderId: self.get_broker_id(),
            Map.origClientOrderId: None,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
        })
        self._set_cancel_request_params(cancel_params)
        # Backup
        from model.tools.Orders import Orders
        Orders.insert_order(Orders.SAVE_ACTION_CANCEL, self)
        return Map(_MF.clean(cancel_params.get_map()))

    def handle_response(self, rsp: BrokerResponse) -> None:
        from model.tools.Orders import Orders
        self._set_response(rsp)
        status_code = rsp.get_status_code()
        if status_code != 200:
            self._set_status(Order.STATUS_FAILED)
        else:
            self._update_order(rsp)
        # Backup
        Orders.insert_order(Orders.SAVE_ACTION_HANDLE, self)

    def _update_order(self, rsp: BrokerResponse) -> None:
        pair = self.get_pair()
        # Extract From Rsp
        content = Map(rsp.get_content())
        status = self.convert_status(content.get(Map.status))
        exec_time = content.get(Map.transactTime) \
            if (status == Order.STATUS_PROCESSING) or (status == Order.STATUS_COMPLETED) else None
        odr_bkr_id = content.get(Map.orderId)
        # Extract trade
        rsp_trades = content.get(Map.fills)
        move = self.get_move()
        trades = self._structure_trades(rsp_trades, pair, exec_time, odr_bkr_id, move) \
            if (rsp_trades is not None) and (len(rsp_trades) > 0) else None
        # Update
        self._set_broker_id(odr_bkr_id) if self.get_broker_id() is None else None
        self._set_trades(trades) if trades is not None else None
        self._set_status(status)

    @staticmethod
    def _get_status_converter() -> Map:
        return BinanceOrder.CONV_STATUS

    @staticmethod
    def convert_status(api_status: str) -> str:
        """
        To convert Binance's Order status into System's\n
        :param api_status: Binance's Order status
        :return: Binance's Order status into System's
        """
        _cls = BinanceOrder
        converter = _cls._get_status_converter()
        if api_status not in converter.get_keys():
            raise ValueError(f"This Order status '{api_status}' is not supported.")
        return _cls.CONV_STATUS.get(api_status)

    @staticmethod
    def convert_order_move(side: str) -> str:
        """
        To convert Binance's Order move (buy & sell) into System's\n
        :param side: Binance's Order move
        :return: Binance's Order move into System's
        """
        converter = BinanceOrder._CONV_ORDER_MOVE
        if side not in converter.get_keys():
            raise ValueError(f"This Order move '{side}' is not supported.")
        return converter.get(side)

    @staticmethod
    def _structure_trades(rsp_trades: list, pair: Pair, exec_time: int, order_bkr_id: str, move: str) -> Map:
        """
        To structure trade generated by Broker to execute the Order
        NOTE: usualy, Broker split Order into multiple trade

        Parameters:
        -----------
        rsp_trades: list
            List of trade returned by Broker
        pair: Pair
            Pair traded
        exec_time: int
            Order's excution time
        order_bkr_id: str
            Order's id in Broker's System
        move: str
            Order.[MOVE_BUY, MOVE_SELL]

        Return:
        -------
        return: Map
            Structured collection of executed trades
                Map[trade_id][*]:   {BrokerRequest.get_trades()}    # Same format
        """
        trades = Map()
        is_buy = None
        if move == Order.MOVE_BUY:
            is_buy = True
        elif move == Order.MOVE_SELL:
            is_buy = False
        else:
            raise ValueError(f"Unknown Order move '{move}'.")
        for i in range(len(rsp_trades)):
            trade_id = f"{order_bkr_id}_{i}"
            rsp_trade = rsp_trades[i]
            fee_symbol = rsp_trade[Map.commissionAsset]
            left_symbol = pair.get_left().get_symbol()
            right_symbol = pair.get_right().get_symbol()
            exec_price = Price(rsp_trade[Map.price], right_symbol)
            exec_quantity = Price(rsp_trade[Map.qty], left_symbol)
            exec_amount = Price(exec_price * exec_quantity, right_symbol)
            fee = Price(rsp_trade[Map.commission], fee_symbol)
            trade = {
                Map.pair: pair,
                Map.order: order_bkr_id,
                Map.trade: None,
                Map.price: exec_price,
                Map.quantity: exec_quantity,
                Map.amount: exec_amount,
                Map.fee: fee,
                Map.time: exec_time,
                Map.buy: is_buy,
                Map.maker: None
            }
            trades.put(trade, trade_id)
        return trades

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = BinanceOrder(Order.TYPE_MARKET, Map({
            Map.pair: Pair('@json/@json'),
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(0, '@json')
        }))
        exec(MyJson.get_executable())
        return instance
