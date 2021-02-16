from model.structure.database.ModelFeature import ModelFeature
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Map import Map
from model.tools.Order import Order


class BinanceOrder(Order):
    def __init__(self, odr_type: str, params: Map) -> None:
        super().__init__(odr_type, params)
        self.__api_request = None
        exec(f"self.{odr_type}()")

    def __set_api_request(self, rq: str) -> None:
        self.__api_request = rq

    def get_api_request(self) -> str:
        return self.__api_request

    def _set_market(self) -> None:
        mkt_prms = self._extract_market_params()
        self.__set_api_request(self._exract_market_request())
        self._set_params(mkt_prms)

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
            Map.newClientOrderId: None,
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
        self._set_params(mkt_prms)

    def _extract_stop_params(self) -> Map:
        """
        To extract params required for a stop Order\n
        :param params: where to extract params for a stop Order
        :return: params required for a stop Order
        """
        """
        # check params
        ks = [Map.pair, Map.move, Map.stop, Map.quantity]
        rtn = ModelFeature.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a stop Order")
        # check logic
        pr = params.get(Map.pair)
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        stop = params.get(Map.stop)
        stop_sbl = stop.get_asset().get_symbol()
        if stop_sbl != pr_r_sbl:
            raise ValueError(f"Stop price asset '{stop_sbl}' must the same "
                             f"that the right asset of the pair '{pr}'")
        qty = params.get(Map.quantity)
        qty_sbl = qty.get_asset().get_symbol()
        if qty_sbl != pr_l_sbl:
            raise ValueError(f"Quantity asset '{qty_sbl}' must the same "
                             f"that the left asset of the pair '{pr}'")
        """
        # Extract
        mkt_params = Map({
            Map.symbol: self.get_pair().get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY if self.get_move() == self.MOVE_BUY else BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_STOP,
            Map.quantity: self.get_quantity().get_value() if self.get_quantity() is not None else None,
            Map.stopPrice: self.get_stop_price().get_value(),
            Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.quoteOrderQty: None,
            Map.price: None,
            Map.newClientOrderId: None,
            Map.icebergQty: None,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL,
            Map.recvWindow: None
        })
        return mkt_params

    def generate_order(self) -> Map:
        prms = self._get_params()
        prms.put(prms.get(Map.symbol).upper(), Map.symbol)
        prms.put(prms.get(Map.side).upper(), Map.side)
        return Map(ModelFeature.clean(prms.get_map()))

    def handle_response(self, rsp: BrokerResponse) -> None:
        cont = rsp.get_content()
        self._set_status()
        self._set_execution_price()

    def generate_cancel_order(self) -> Map:
        odr_params = Map({
            Map.symbol: self.get_pair().get_merged_symbols().upper(),
            Map.orderId: self.get_broker_id(),
            Map.origClientOrderId: None,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
        })
        return odr_params
