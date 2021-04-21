from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Map import Map
from model.tools.Order import Order
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
            # Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
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
        self._set_status(self.STATUS_SUBMITTED)
        from model.tools.Orders import Orders
        Orders.insert_order(Orders.SAVE_ACTION_GENERATE, self)
        return Map(ModelFeature.clean(prms.get_map()))

    def generate_cancel_order(self) -> Map:
        odr_params = Map({
            Map.symbol: self.get_pair().get_merged_symbols().upper(),
            Map.orderId: self.get_broker_id(),
            Map.origClientOrderId: None,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
        })
        return odr_params

    def handle_response(self, rsp: BrokerResponse) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        content = Map(rsp.get_content())
        status = content.get(Map.status)
        exec_time = content.get(Map.transactTime)
        odr_bkr_id = content.get(Map.orderId)
        # Stages
        prc_obj = None
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            prc_val = content.get(Map.price)
        elif _stage == Config.STAGE_3:
            # Execution price
            subexec = content.get(Map.fills)
            subexec = subexec if subexec is not None else []
            self._set_subexecutions(subexec)
            subexec_datas = self.resume_subexecution(subexec) if len(subexec) > 0 else None
            prc_val = subexec_datas.get(Map.price) if subexec_datas is not None else None
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        if prc_val is not None:
            prc_obj = Price(prc_val, self.get_pair().get_right().get_symbol())
        # Update
        self._set_broker_id(odr_bkr_id) if self.get_broker_id() is None else None
        self._set_status(self.convert_status(status))
        self._set_execution_price(prc_obj)
        self._set_execution_time(exec_time) if exec_time is not None else None
        # Backup
        from model.tools.Orders import Orders
        Orders.insert_order(Orders.SAVE_ACTION_HANDLE, self)

    @staticmethod
    def _get_status_converter() -> Map:
        return BinanceOrder.CONV_STATUS

    @staticmethod
    def convert_status(api_status: str) -> str:
        _cls = BinanceOrder
        converter = _cls._get_status_converter()
        if api_status not in converter.get_keys():
            raise ValueError(f"This status '{api_status}' is not supported")
        return _cls.CONV_STATUS.get(api_status)

    @staticmethod
    def resume_subexecution(fills: list) -> Map:
        """
        To extract datas from sub-execution\n
        :param fills: list of Binance's sub-executions
        [
            {
              "price": "4000.00000000",
              "qty": "1.00000000",
              "commission": "4.00000000",
              "commissionAsset": "USDT"
            }
        ]
        :return: extracted datas
        datas[Map.price]: {float}   | average execution price
        datas[Map.fee]:   {Price}   | total fees
        """
        if len(fills) == 0:
            raise ValueError(f"The lis of sub-executions can't be empty")
        qty_total = 0
        fees = 0
        new_fills = []
        for row in fills:
            price = float(row[Map.price])
            qty = float(row[Map.qty])
            qty_total += qty
            fee = float(row[Map.commission])
            fees += fee
            new_row = {
                Map.price: price,
                Map.qty: qty,
                Map.commission: fee
            }
            new_fills.append(new_row)
        price_rates = [(row[Map.qty]/qty_total)*row[Map.price] for row in new_fills]
        price_sum = sum(price_rates)
        nb_decimal = len(str(new_fills[0][Map.price]).split('.')[-1]) - 1
        price_exec = round(price_sum, nb_decimal)
        symbol = fills[0][Map.commissionAsset]
        fees_obj = Price(fees, symbol)
        datas = Map({
            Map.price: price_exec,
            Map.fee: fees_obj
        })
        return datas
