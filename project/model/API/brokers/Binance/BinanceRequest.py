from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.database.ModelFeature import ModelFeature as ModelFeat
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class BinanceRequest(BrokerRequest, MyJson):
    CONV_ACCOUNT = Map({
        BrokerRequest.ACCOUNT_MAIN: BinanceAPI.ACCOUNT_TYPE_SPOT,
        BrokerRequest.ACCOUNT_MARGIN: BinanceAPI.ACCOUNT_TYPE_MARGIN,
        BrokerRequest.ACCOUNT_FUTURE: BinanceAPI.ACCOUNT_TYPE_FUTURES,
    })

    def __init__(self, rq: str, params: Map):
        super().__init__(params)
        self.__api_request = None
        exec(f'self.{rq}(params)')

    def _get_account_converter(self) -> Map:
        return self.CONV_ACCOUNT

    def _set_market_price(self, prms: Map) -> None:
        ks = [Map.pair, Map.period, Map.number]
        rtn = ModelFeat.keys_exist(ks, prms.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to get market prices")
        request = Map({
            Map.symbol: prms.get(Map.pair).get_merged_symbols().upper(),
            Map.interval: BinanceAPI.convert_interval(prms.get(Map.period)),
            Map.startTime: int(prms.get(Map.begin_time)) * 1000 if prms.get(Map.begin_time) is not None else None,
            Map.endTime: int(prms.get(Map.end_time)) * 1000 if prms.get(Map.end_time) is not None else None,
            Map.limit: int(prms.get(Map.number)) if prms.get(Map.number) is not None else None
        })
        self._set_endpoint(BinanceAPI.RQ_KLINES)
        self._set_request(request)

    def get_market_price(self) -> BinanceMarketPrice:
        result = self._get_result()
        if result is None:
            request = self._get_request()
            params = self.get_params()
            rsp = self._get_response()
            result = BinanceMarketPrice(rsp.get_content(), request.get(Map.interval), params.get(Map.pair))
            self._set_result(result)
        return result

    def _set_account_snapshot(self, prms: Map) -> None:
        ks = [Map.account]
        rtn = ModelFeat.keys_exist(ks, prms.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to get account snapshots")
        account = self._get_account_converter().get(prms.get(Map.account))
        if account is None:
            raise ValueError(f"This account '{prms.get(Map.account)}' is not supported")
        startime = int(prms.get(Map.begin_time)) if prms.get(Map.begin_time) is not None else None
        endtime = int(prms.get(Map.end_time)) if prms.get(Map.end_time) is not None else None
        if (startime is not None) and (endtime is not None) and (endtime <= startime):
            raise ValueError(f"The endtime '{endtime}' must be greater that the starttime '{startime}'.")
        limit = int(prms.get(Map.number)) if prms.get(Map.number) is not None else None
        if (limit is not None) \
                and ((limit < BinanceAPI.CONSTRAINT_SNAP_ACCOUT_MIN_LIMIT)
                     or (limit > BinanceAPI.CONSTRAINT_SNAP_ACCOUT_MAX_LIMIT)):
            _min_limit = BinanceAPI.CONSTRAINT_SNAP_ACCOUT_MIN_LIMIT
            _max_limit = BinanceAPI.CONSTRAINT_SNAP_ACCOUT_MAX_LIMIT
            raise ValueError(f"The limit number of snapshot returned per request must be"
                             f" between [{_min_limit}, {_max_limit}], instead '{limit}'.")
        recvwindow = int(prms.get(Map.timeout)) if prms.get(Map.timeout) is not None else None
        if (recvwindow is not None) and (recvwindow > BinanceAPI.CONSTRAINT_RECVWINDOW):
            raise Exception(f"The max time out to wait for a request response is '{BinanceAPI.CONSTRAINT_RECVWINDOW}',"
                            f" instead '{recvwindow}'.")
        request = Map({
            Map.type: account,
            Map.startTime: startime,
            Map.endTime: endtime,
            Map.limit: limit,
            Map.recvWindow: recvwindow
        })
        self._set_endpoint(BinanceAPI.RQ_ACCOUNT_SNAP)
        self._set_request(request)

    def get_account_snapshot(self) -> Map:
        accounts = self._get_result()
        if accounts is None:
            accounts = Map()
            rsp = self._get_response()
            content = Map(rsp.get_content())
            for snap in content.get(Map.snapshotVos):
                time = snap[Map.updateTime]
                balances = snap[Map.data][Map.balances]
                account = {str(balance[Map.asset]).lower(): Price(balance[Map.free],
                                                                      balance[Map.asset]) for balance in balances}
                accounts.put(account, Map.account, time)
            accounts.put(content.get_map(), Map.response)
            self._set_result(accounts)
        return accounts

    def _set_24h_statistics(self, params: Map) -> None:
        pair = params.get(Map.pair)
        request = Map({
            Map.symbol: pair.get_merged_symbols().upper() if pair is not None else None
        })
        self._set_endpoint(BinanceAPI.RQ_24H_STATISTICS)
        self._set_request(request)

    def get_24h_statistics(self) -> Map:
        stats = self._get_result()
        if stats is None:
            stats = Map()
            rsp = self._get_response()
            content = rsp.get_content()
            if isinstance(content, dict):
                content = [content]
            for row in content:
                pair = BinanceAPI.symbol_to_pair(row[Map.symbol].lower())
                stat = {
                    Map.pair: pair,
                    Map.price: float(row['priceChange']),
                    Map.rate: float(row['priceChangePercent']),
                    Map.low: float(row['lowPrice']),
                    Map.high: float(row['highPrice']),
                    Map.volume: {
                        Map.left: float(row['volume']),
                        Map.right: float(row['quoteVolume'])
                    },
                    Map.time: {
                        Map.start: row['openTime'],
                        Map.end: row['closeTime']
                    }
                }
                stats.put(stat, pair)
            stats.sort()
            self._set_result(stats)
        return stats

    def _set_orders(self, prms: Map) -> None:
        ks = [Map.pair]
        rtn = ModelFeat.keys_exist(ks, prms.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to get all Order datas.")
        odr_id = prms.get(Map.id)
        starttime = prms.get(Map.begin_time)
        endtime = prms.get(Map.end_time)
        if (odr_id is not None) and ((starttime is not None) or (endtime is not None)):
            raise ValueError(f"The Order's id can't be set when starttime or endtime are set.")
        limit = prms.get(Map.limit)
        if (limit is not None) and (limit > BinanceAPI.CONSTRAINT_LIMIT):
            raise ValueError(f"The number limit of Order returned per request is '{BinanceAPI.CONSTRAINT_LIMIT}',"
                            f" instead '{limit}'.")
        recvwindow = prms.get(Map.timeout)
        if (recvwindow is not None) and (recvwindow > BinanceAPI.CONSTRAINT_RECVWINDOW):
            raise ValueError(f"The max time to wait for a request response is '{BinanceAPI.CONSTRAINT_RECVWINDOW}',"
                            f" instead '{recvwindow}'.")
        request = Map({
            Map.symbol: prms.get(Map.pair).get_merged_symbols().upper(),
            Map.orderId: odr_id,
            Map.startTime: starttime,
            Map.endTime: endtime,
            Map.limit: limit,
            Map.recvWindow: recvwindow
        })
        self._set_endpoint(BinanceAPI.RQ_ALL_ORDERS)
        self._set_request(request)

    def get_orders(self) -> Map:
        result = self._get_result()
        if result is None:
            result = Map()
            rsp = self._get_response()
            content = rsp.get_content()
            for row in content:
                odr_id = str(row[Map.orderId])
                status = BinanceOrder.convert_status(row[Map.status])
                move = BinanceOrder.convert_order_move(row[Map.side])
                exec_qty = float(row[Map.executedQty])
                exec_amount = float(row[Map.cummulativeQuoteQty])
                exec_price = None
                if (status == Order.STATUS_PROCESSING) or (status == Order.STATUS_COMPLETED):
                    exec_price = exec_amount / exec_qty
                odr = {
                    Map.symbol: row[Map.symbol],
                    Map.id: odr_id,
                    Map.price: exec_price,
                    Map.quantity: float(row[Map.origQty]),
                    Map.qty: exec_qty if exec_qty > 0 else None,
                    Map.amount: exec_amount if exec_amount > 0 else None,
                    Map.status: status,
                    Map.type: row[Map.type],
                    Map.move: move,
                    Map.time: row[Map.updateTime],
                    Map.response: row
                }
                result.put(odr, odr_id)
            self._set_result(result)
        return result

    def _set_trades(self, params: Map) -> None:
        ks = [Map.pair]
        rtn = ModelFeat.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to request executed trades.")
        limit = params.get(Map.limit)
        if (limit is not None) and (not (1 <= limit <= BinanceAPI.CONSTRAINT_ALL_TRADES_MAX_LIMIT)):
            max_limit = BinanceAPI.CONSTRAINT_ALL_TRADES_MAX_LIMIT
            raise ValueError(f"The number of trade to return is outside "
                             f"the domain [1, {max_limit}], instead '{limit}'")
        timeout = params.get(Map.timeout)
        if (timeout is not None) and (not (1 <= timeout <= BinanceAPI.CONSTRAINT_RECVWINDOW)):
            max_timeout = BinanceAPI.CONSTRAINT_RECVWINDOW
            raise ValueError(f"The max time to wait for a request's response is outside "
                             f"the domain [1, {max_timeout}], instead '{timeout}'")
        request = Map({
            Map.symbol: params.get(Map.pair).get_merged_symbols().upper(),
            Map.fromId: params.get(Map.id),
            Map.startTime: params.get(Map.begin_time),
            Map.endTime: params.get(Map.end_time),
            Map.limit: limit,
            Map.recvWindow: timeout
        })
        self._set_endpoint(BinanceAPI.RQ_ALL_TRADES)
        self._set_request(request)

    def get_trades(self) -> Map:
        result = self._get_result()
        if result is None:
            result = Map()
            rsp = self._get_response()
            content = rsp.get_content()
            for row in content:
                odr_bkr_id = str(row[Map.orderId])
                trade_id = str(row[Map.id])
                pair_str = BinanceAPI.symbol_to_pair(row[Map.symbol].lower())
                pair = Pair(pair_str)
                right_symbol = pair.get_right().get_symbol()
                struc = {
                    Map.time: row[Map.time],
                    Map.pair: pair,
                    Map.order: odr_bkr_id,
                    Map.trade: trade_id,
                    Map.price: Price(row[Map.price], right_symbol),
                    Map.quantity: Price(row[Map.qty], pair.get_left().get_symbol()),
                    Map.amount: Price(row[Map.quoteQty], right_symbol),
                    Map.fee: Price(row[Map.commission], row[Map.commissionAsset]),
                    Map.buy: row[Map.isBuyer],
                    Map.maker: row[Map.isMaker]
                }
                result.put(struc, odr_bkr_id, trade_id)
            self._set_result(result)
        return result

    def generate_request(self) -> Map:
        request = self._get_request()
        return Map(ModelFeat.clean(request.get_map()))

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = BinanceRequest(BrokerRequest.RQ_MARKET_PRICE, Map({
            Map.pair: Pair('@json/@json'),
            Map.period: 1,
            Map.begin_time: 0,
            Map.end_time: 2,
            Map.number: 1,
        }))
        exec(MyJson.get_executable())
        return instance
