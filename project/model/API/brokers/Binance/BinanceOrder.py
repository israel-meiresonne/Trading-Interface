from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair
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
        self._set_response(rsp)
        status_code = rsp.get_status_code()
        if status_code != 200:
            self._set_status(Order.STATUS_FAILED)
        else:
            self._update_order(rsp)
        # Backup
        from model.tools.Orders import Orders
        Orders.insert_order(Orders.SAVE_ACTION_HANDLE, self)

    def _update_order(self, rsp: BrokerResponse) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        pair = self.get_pair()
        r_symbol = pair.get_right().get_symbol()
        l_symbol = pair.get_left().get_symbol()
        # Extract From Rsp
        content = Map(rsp.get_content())
        status = self.convert_status(content.get(Map.status))
        exec_time = content.get(Map.transactTime) \
            if (status == Order.STATUS_PROCESSING) or (status == Order.STATUS_COMPLETED) else None
        """
        exec_qty = float(content.get(Map.executedQty))
        exec_qty_obj = Price(exec_qty, l_symbol) if exec_qty > 0 else None
        exec_amount = float(content.get(Map.cummulativeQuoteQty))
        exec_amount_obj = Price(exec_amount, r_symbol) if exec_amount > 0 else None
        """
        odr_bkr_id = content.get(Map.orderId)
        # Extract trade
        rsp_trades = content.get(Map.fills)
        move = self.get_move()
        trades = self._structure_trades(rsp_trades, pair, exec_time, odr_bkr_id, move) \
            if (rsp_trades is not None) and (len(rsp_trades) > 0) else None
        '''
        # Stages
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            pass
            # exec_price_val = content.get(Map.price)
            # fee_obj = Price(Order.FAKE_FEE, r_symbol) if exec_price_val is not None else None
        elif _stage == Config.STAGE_3:
            # Execution price
            """
            fills = content.get(Map.fills)
            # subexec = fills if fills is not None else None
            fills_ok = (fills is not None) and (len(fills) > 0)
            self._set_trades(fills) if fills_ok else None
            subexec_datas = self.resume_subexecution(fills) if fills_ok else None
            exec_price_val = subexec_datas.get(Map.price) if subexec_datas is not None else None
            fee_obj = subexec_datas.get(Map.fee) if subexec_datas is not None else None
            """
            rsp_trades = content.get(Map.fills)
            move = self.get_move()
            trades = self._structure_trades(rsp_trades, pair, exec_time, odr_bkr_id, move)
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        '''
        """
        if exec_price_val is not None:
           exec_price_obj = Price(exec_price_val, r_symbol)
        exec_price_obj = Price(exec_price_val, r_symbol) if exec_price_val is not None else None
        """
        # Update
        self._set_status(status)
        self._set_broker_id(odr_bkr_id) if self.get_broker_id() is None else None
        self._set_trades(trades) if trades is not None else None
        """
        self._set_execution_time(exec_time) if (self.get_execution_time() is None) and (exec_time is not None) else None
        self._set_execution_price(exec_price_obj) if self.get_execution_price() is None else None
        self._set_executed_quantity(exec_qty_obj) if self.get_executed_quantity() is None else None
        self._set_executed_amount(exec_amount_obj) if self.get_executed_amount() is None else None
        self._set_fee(fee_obj) if fee_obj is not None else None
        """

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

    '''
    @staticmethod
    def resume_subexecution(fills: list) -> Map:
        """
        To extract datas from sub-execution\n
                    [
                        {
                          "price": "4000.00000000",
                          "qty": "1.00000000",
                          "commission": "4.00000000",
                          "commissionAsset": "USDT"
                        }
                    ]\n
        :param fills: list of Binance's sub-executions
        :return: extracted datas\n
                 datas[Map.price]: {float}   | average execution price
                 datas[Map.fee]:   {Price}   | total fees
        """
        if len(fills) == 0:
            raise ValueError(f"The list of sub-executions can't be empty.")
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
        # nb_decimal = len(str(new_fills[0][Map.price]).split('.')[-1])  # - 1
        nb_decimal = _MF.get_nb_decimal(new_fills[0][Map.price])
        price_exec = round(price_sum, nb_decimal)
        symbol = fills[0][Map.commissionAsset]
        fees_obj = Price(fees, symbol)
        datas = Map({
            Map.price: price_exec,
            Map.fee: fees_obj
        })
        return datas
    '''

    @staticmethod
    def _structure_trades(rsp_trades: list, pair: Pair, exec_time: int, order_bkr_id: str, move: str) -> Map:
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
