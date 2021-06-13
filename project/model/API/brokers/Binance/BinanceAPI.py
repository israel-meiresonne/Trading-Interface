from typing import List, Any

from requests import get as rq_get, Response
from requests import post as rq_post
from requests import delete as rq_delete
from hmac import new as new_hmac
from hashlib import sha256 as hashlib_sha256

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Paire import Pair
from model.tools.Price import Price


class BinanceAPI:
    # Const
    ORDER_TEST_PATH = "/api/v3/order/test"
    ORDER_REAL_PATH = "/api/v3/order"
    # Requests
    RQ_SYS_STATUS = "RQ_SYS_STATUS"
    RQ_EXCHANGE_INFOS = "RQ_EXCHANGE_INFOS"
    RQ_KLINES = "RQ_KLINES"
    RQ_ACCOUNT_SNAP = "RQ_ACCOUNT_SNAP"
    RQ_TRADE_FEE = "RQ_TRADE_FEE"
    RQ_24H_STATISTICS = "RQ_24H_STATISTICS"
    # Orders
    RQ_ALL_ORDERS = "RQ_ALL_ORDERS"
    RQ_ALL_TRADES = "RQ_ALL_TRADES"
    RQ_CANCEL_ORDER = "RQ_CANCEL_ORDER"
    RQ_ORDER_LIMIT = "RQ_ORDER_LIMIT"
    RQ_ORDER_MARKET_qty = "RQ_ORDER_MARKET_qty"
    RQ_ORDER_MARKET_amount = "RQ_ORDER_MARKET_amount"
    RQ_ORDER_STOP_LOSS = "RQ_ORDER_STOP_LOSS"
    RQ_ORDER_STOP_LOSS_LIMIT = "RQ_ORDER_STOP_LOSS_LIMIT"
    RQ_ORDER_TAKE_PROFIT = "RQ_ORDER_TAKE_PROFIT"
    RQ_ORDER_TAKE_PROFIT_LIMIT = "RQ_ORDER_TAKE_PROFIT_LIMIT"
    RQ_ORDER_LIMIT_MAKER = "RQ_ORDER_LIMIT_MAKER"
    # Configs
    __PATH_ORDER = None
    _RQ_CONF = {
        RQ_SYS_STATUS: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/sapi/v1/system/status",
            Map.mandatory: [],
            Map.params: []
        },
        RQ_EXCHANGE_INFOS: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/api/v3/exchangeInfo",
            Map.mandatory: [],
            Map.params: []
        },
        RQ_ACCOUNT_SNAP: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/sapi/v1/accountSnapshot",
            Map.mandatory: [
                Map.type
            ],
            Map.params: [
                Map.startTime,
                Map.endTime,
                Map.limit,
                Map.recvWindow
            ]
        },
        RQ_KLINES: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/api/v3/klines",
            Map.mandatory: [
                Map.symbol,
                Map.interval
            ],
            Map.params: [
                Map.startTime,
                Map.endTime,
                Map.limit
            ]
        },
        RQ_TRADE_FEE: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/sapi/v1/asset/tradeFee",
            Map.mandatory: [
                # Map.timestamp | automatically added in BinanceAPI.__sign()
            ],
            Map.params: [
                Map.symbol,
                Map.recvWindow
            ]
        },
        RQ_24H_STATISTICS: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/api/v3/ticker/24hr",
            Map.mandatory: [],
            Map.params: [Map.symbol]
        },
        RQ_ALL_ORDERS: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/api/v3/allOrders",
            Map.mandatory: [
                Map.symbol
                # Map.timestamp | automatically added in BinanceAPI.__sign()
            ],
            Map.params: [
                Map.orderId,
                Map.startTime,
                Map.endTime,
                Map.limit,
                Map.recvWindow
            ]
        },
        RQ_ALL_TRADES: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/api/v3/myTrades",
            Map.mandatory: [
                Map.symbol
                # Map.timestamp | automatically added in BinanceAPI.__sign()
            ],
            Map.params: [
                Map.fromId,
                Map.startTime,
                Map.endTime,
                Map.limit,
                Map.recvWindow
            ]
        },
        RQ_CANCEL_ORDER: {
            Map.signed: True,
            Map.method: Map.DELETE,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.orderId
            ],
            Map.params: [
                Map.origClientOrderId,
                Map.newClientOrderId,
                Map.recvWindow
            ]
        },
        RQ_ORDER_LIMIT: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.timeInForce,
                Map.quantity,
                Map.price,
            ],
            Map.params: [
                Map.quoteOrderQty,
                Map.newClientOrderId,
                Map.stopPrice,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow,
            ]
        },
        RQ_ORDER_MARKET_qty: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.quantity
            ],
            Map.params: [
                # Map.timeInForce,
                Map.quoteOrderQty,
                Map.price,
                Map.newClientOrderId,
                Map.stopPrice,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow,
            ]
        },
        RQ_ORDER_MARKET_amount: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.quoteOrderQty
            ],
            Map.params: [
                # Map.timeInForce,
                Map.quantity,
                Map.price,
                Map.newClientOrderId,
                Map.stopPrice,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow,
            ]
        },
        RQ_ORDER_STOP_LOSS: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.quantity,
                Map.stopPrice
            ],
            Map.params: [
                # Map.timeInForce,
                Map.quoteOrderQty,
                Map.price,
                Map.newClientOrderId,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow
            ]
        },
        RQ_ORDER_STOP_LOSS_LIMIT: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.timeInForce,
                Map.quantity,
                Map.price,
                Map.stopPrice
            ],
            Map.params: [
                Map.quoteOrderQty,
                Map.newClientOrderId,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow
            ]
        },
        RQ_ORDER_TAKE_PROFIT: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.quantity,
                Map.price
            ],
            Map.params: [
                Map.timeInForce,
                Map.quoteOrderQty,
                Map.newClientOrderId,
                Map.stopPrice,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow
            ]
        },
        RQ_ORDER_TAKE_PROFIT_LIMIT: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.timeInForce,
                Map.quantity,
                Map.price,
                Map.stopPrice
            ],
            Map.params: [
                Map.quoteOrderQty,
                Map.newClientOrderId,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow
            ]
        },
        RQ_ORDER_LIMIT_MAKER: {
            Map.signed: True,
            Map.method: Map.POST,
            Map.path: __PATH_ORDER,
            Map.mandatory: [
                Map.symbol,
                Map.side,
                Map.type,
                Map.quantity,
                Map.price
            ],
            Map.params: [
                Map.timeInForce,
                Map.quoteOrderQty,
                Map.newClientOrderId,
                Map.stopPrice,
                Map.icebergQty,
                Map.newOrderRespType,
                Map.recvWindow
            ]
        }
    }
    # endpoints
    _ENDPOINTS = {
        Map.api: [
            "https://api.binance.com",
            "https://api1.binance.com",
            "https://api2.binance.com",
            "https://api3.binance.com"
        ],
        Map.test: [
            "https://testnet.binance.vision"
        ],
        Map.websocket: []
    }
    # ENUM
    ''' ACCOUNT '''
    ACCOUNT_TYPE_SPOT = "SPOT"
    ACCOUNT_TYPE_MARGIN = "MARGIN"
    ACCOUNT_TYPE_FUTURES = "FUTURES"
    ''' MOVE '''
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    ''' ORDER TYPE '''
    TYPE_MARKET = "MARKET"
    TYPE_STOP = "STOP_LOSS"
    TYPE_LIMIT = "LIMIT"
    TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TYPE_TAKE_PROFIT = "TAKE_PROFIT"
    TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    TYPE_LIMIT_MAKER = "LIMIT_MAKER"
    ''' ORDER STATUS '''
    STATUS_ORDER_NEW = "NEW"
    STATUS_ORDER_PARTIALLY = "PARTIALLY_FILLED"
    STATUS_ORDER_FILLED = "FILLED"
    STATUS_ORDER_CANCELED = "CANCELED"
    STATUS_ORDER_PENDING_CANCEL = "PENDING_CANCEL"
    STATUS_ORDER_REJECTED = "REJECTED"
    STATUS_ORDER_EXPIRED = "EXPIRED"
    ''' TIME FORCE '''
    TIME_FRC_GTC = "GTC"
    TIME_FRC_IOC = "IOC"
    TIME_FRC_FOK = "FOK"
    ''' RESPONSE TYPE '''
    RSP_TYPE_ACK = "ACK"
    RSP_TYPE_RESULT = "RESULT"
    RSP_TYPE_FULL = "FULL"
    ''' INTERVALS '''
    _INTERVALS_INT = Map({
        '1m': 60,
        '3m': 60*3,
        '5m': 60*5,
        '15m': 60*15,
        '30m': 60*30,
        '1h': 60*60,
        '2h': 60*60*2,
        '4h': 60*60*4,
        '6h': 60*60*6,
        '8h': 60*60*8,
        '12h': 60*60*12,
        '1d': 60*60*24,
        '3d': 60*60*24*3,
        '1w': 60*60*24*7,
        '1M': int(60*60*24*31.5)
    })
    INTERVAL_1MIN = '1m'
    INTERVAL_30MIN = '30m'
    INTERVAL_1MONTH = '1M'
    # Constraints
    CONSTRAINT_KLINES_MAX_PERIOD = 1000
    CONSTRAINT_LIMIT = 1000
    CONSTRAINT_RECVWINDOW = 60000
    CONSTRAINT_SNAP_ACCOUT_MIN_LIMIT = 5
    CONSTRAINT_SNAP_ACCOUT_MAX_LIMIT = 30
    CONSTRAINT_ALL_TRADES_MAX_LIMIT = 1000  # Default is 500
    # API Constants
    _CONSTANT_DEFAULT_RECVWINDOW = 5000 + 1000
    _EXCHANGE_INFOS = None
    _TRADE_FEES = None
    """
    _TRADE_FEES[symbol{str}][Map.symbol]:     {str}   # Symbol Format: 'bnbusdt' (= bnb/usdt)
    _TRADE_FEES[symbol{str}][Map.taker]:      {float}
    _TRADE_FEES[symbol{str}][Map.maker]:      {float}
    """
    _SYMBOL_TO_PAIR = None
    # Variables
    _SOCKET = None

    def __init__(self, api_pb: str, api_sk: str, test_mode: bool):
        """
        Constructor\n
        :param api_pb: API's public key
        :param api_sk: API's secret key
        :param test_mode: set True to call test API else False to call production API
        """
        # self.__id = 'binance_api_' + str(_MF.get_timestamp(_MF.TIME_MILLISEC))
        self.__api_public_key = api_pb
        self.__api_secret_key = api_sk
        self.__test_mode = test_mode
        if (type(test_mode) == bool) and (not test_mode):
            BinanceAPI.__PATH_ORDER = self.ORDER_REAL_PATH
        else:
            BinanceAPI.__PATH_ORDER = self.ORDER_TEST_PATH
        self._update_order_config()
        self._set_exchange_infos()
        self._set_trade_fees() if self._get_trade_fees() is None else None

    def _update_order_config(self) -> None:
        rq_configs = self.__get_request_configs()
        for rq, config in rq_configs.items():
            if config[Map.path] is None:
                config[Map.path] = self.__PATH_ORDER

    def _set_exchange_infos(self) -> None:
        """
        To get exchange info from Broker's API\n
        """
        if BinanceAPI._EXCHANGE_INFOS is None:
            bkr_rsp = self.request_api(self.RQ_EXCHANGE_INFOS, Map())
            content = Map(bkr_rsp.get_content())
            time_zone = content.get(Map.timezone)
            time = content.get(Map.serverTime)
            ratelimits = content.get(Map.rateLimits)
            limits = Map({
                Map.weight: ratelimits[0],
                Map.second: ratelimits[1],
                Map.day: ratelimits[2]
            })
            symbols = content.get(Map.symbols)
            symbols_infos = Map({Pair(row[Map.baseAsset], row[Map.quoteAsset]).__str__(): row for row in symbols})
            for symbol, infos in symbols_infos.get_map().items():
                for k, v in infos.items():
                    if k == Map.filters:
                        filters = {row[Map.filterType].lower(): row for row in v}
                        symbols_infos.put(filters, symbol, k)
            BinanceAPI._EXCHANGE_INFOS = Map({
                Map.timezone: time_zone,
                Map.time: time,
                Map.limit: limits.get_map(),
                Map.symbol: symbols_infos.get_map()
            })

    def _set_trade_fees(self) -> None:
        if BinanceAPI._TRADE_FEES is not None:
            raise Exception(f"Trade fees are already set.")
        rsp = self.request_api(self.RQ_TRADE_FEE, Map())
        fees_list = rsp.get_content()
        fees = Map()
        for row in fees_list:
            symbol = row[Map.symbol].lower()
            fee = {
                Map.pair: symbol,
                Map.taker: float(row[Map.takerCommission]),
                Map.maker: float(row[Map.makerCommission])
            }
            fees.put(fee, symbol)
        BinanceAPI._TRADE_FEES = fees

    def __get_endpoint(self, i: int) -> str:
        endps = BinanceAPI.__get_endpoints()
        test = self.__is_test_mode()
        if test and (i not in range(len(endps[Map.test]))):
            raise IndexError(f"There is no test endpoint with this index '{i}'")
        elif (not test) and (i not in range(len(endps[Map.api]))):
            raise IndexError(f"There is no production endpoint with this index '{i}'")
        return endps[Map.test][i] if test else endps[Map.api][i]

    def __get_api_public_key(self) -> str:
        """
        To get API's public key\n
        :return: API's public key
        """
        return self.__api_public_key

    def __is_test_mode(self) -> bool:
        return self.__test_mode

    def __get_api_secret_key(self) -> str:
        """
        To get API's secret key\n
        :return: API's secret key
        """
        return self.__api_secret_key

    def _set_socket(self, streams: List[str]) -> None:
        from model.API.brokers.Binance.BinanceSocket import BinanceSocket
        socket = BinanceSocket(streams, self)
        socket.run_forever()
        BinanceAPI._SOCKET = socket

    def _get_socket(self, streams: List[str]) -> Any:
        socket = BinanceAPI._SOCKET
        if socket is None:
            self._set_socket(streams)
        else:
            socket.add_streams(streams)
        return BinanceAPI._SOCKET

    def close_socket(self) -> None:
        """
        To close streams of Binance's websocket\n
        """
        socket = self._get_socket([])
        socket.close()

    def __generate_headers(self) -> dict:
        """
        To generate a headers for a request to the API\n
        :return: header for a request to the API
        """
        return {"X-MBX-APIKEY": self.__get_api_public_key()}

    def _generate_url(self, rq: str, i=0) -> str:
        """
        To generate a url with a test or production API and a endpoint\n
        :param rq: a supported request
        :param i: index of a test or production API
        :return: url where to send the given request
        """
        endp = self.__get_endpoint(i)
        rq_config = self.get_request_config(rq)
        path = rq_config[Map.path]
        return endp + path

    def __generate_signature(self, prms: dict) -> str:
        """
        To generate a HMAC SHA256 signature with the data to send\n
        :param prms: data to send to Binance's API
        :return: a HMAC SHA256 signature generated with the data to send
        """
        qr_str = "&".join([f"{k}={prms[k]}" for k in prms])
        return new_hmac(self.__get_api_secret_key().encode('utf-8'), qr_str.encode('utf-8'), hashlib_sha256).hexdigest()

    def __sign(self, params: Map) -> None:
        """
        To sign the request with the private key and params\n
        :param params: params of a request
        """
        # ds_map.put(recvWindow, Map.recvWindow)
        stamp = _MF.get_timestamp(_MF.TIME_MILLISEC) - 1000
        params.put(stamp, Map.timestamp)
        time_out = params.get(Map.recvWindow)
        new_time_out = time_out + 1000 if time_out is not None else BinanceAPI._CONSTANT_DEFAULT_RECVWINDOW
        params.put(new_time_out, Map.recvWindow)
        sgt = self.__generate_signature(params.get_map())
        params.put(sgt, Map.signature)

    def request_api(self, rq: str, params: Map) -> BrokerResponse:
        """
        To config and send a request to the API\n
        :param rq: a supported request
        :param params: params to send
        :return: API's response
        """
        _stage = Config.get(Config.STAGE_MODE)
        self._check_params(rq, params)
        rq_excluded = [BinanceAPI.RQ_EXCHANGE_INFOS, BinanceAPI.RQ_TRADE_FEE]
        if _stage == Config.STAGE_1:
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            return BinanceFakeAPI.steal_request(rq, params)
        if (_stage == Config.STAGE_2) and (rq not in rq_excluded):
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            if rq == self.RQ_KLINES:
                rsp = self._send_market_historics_request(rq, params)
                pair_merged = params.get(Map.symbol)
                period_str = params.get(Map.interval)
                period_milli = int(BinanceAPI.get_interval(period_str) * 1000)
                BinanceFakeAPI.add_market_historic(pair_merged, period_milli, rsp.get_content())
                BinanceFakeAPI.steal_request(rq, params)
                return rsp
            else:
                return BinanceFakeAPI.steal_request(rq, params)
        # rq_cfg = self.get_request_config(rq)
        # self._check_params(rq, params)
        """
        if rq_cfg[Map.signed]:
            self.__sign(params)
        """
        start_time = params.get(Map.startTime)
        end_time = params.get(Map.endTime)
        if (rq == BinanceAPI.RQ_KLINES) and (end_time is None) and (start_time is None):
            rsp = self._send_market_historics_request(rq, params)
        else:
            rsp = self._send_request(rq, params)
        return rsp

    def _send_request(self, rq: str, params: Map) -> BrokerResponse:
        """
        To send a request to the API\n
        :param rq: a supported request
        :param params: params to send
        :return: API's response
        """
        _stage = Config.get(Config.STAGE_MODE)
        rq_cfg = BinanceAPI.get_request_config(rq)
        if rq_cfg[Map.signed]:
            self.__sign(params)
        hdrs = self.__generate_headers()
        url = self._generate_url(rq)
        mtd = rq_cfg[Map.method]
        if mtd == Map.GET:
            rsp = rq_get(url, params.get_map(), headers=hdrs)
        elif mtd == Map.POST:
            rsp = rq_post(url, params.get_map(), headers=hdrs)
        elif mtd == Map.DELETE:
            ds = params.get_map()
            url += '?' + '&'.join([f'{k}={v}' for k, v in ds.items()])
            rsp = rq_delete(url, headers=hdrs)
        else:
            raise Exception(f"The request method {mtd} is not supported")
        bkr_rsp = BrokerResponse(rsp)
        # Backup Down
        self._save_response(rq, params, rsp)
        # Backup Up
        # rsp_status = bkr_rsp.get_status_code()
        # if rsp_status != 200:
        #    raise Exception(f"(status code: {rsp_status}): {bkr_rsp.get_content()}")
        return bkr_rsp

    def _send_market_historics_request(self, rq: str, params: Map) -> BrokerResponse:
        from model.API.brokers.Binance.BinanceSocket import BinanceSocket
        symbol = params.get(Map.symbol)
        period_str = params.get(Map.interval)
        streams = [BinanceSocket.generate_stream(rq, symbol, period_str)]
        stream = streams[0]
        bnc_socket = self._get_socket(streams)
        market_historic = bnc_socket.get_market_historic(stream)
        rsp = Response()
        if isinstance(market_historic, list):
            limit = params.get(Map.limit)
            if limit is not None:
                market_historic = market_historic[0:limit]
            rsp.status_code = 200
            rsp.reason = 'OK'
            rsp._content = _MF.json_encode(market_historic).encode()
            rsp.url = bnc_socket.get_url()
            rsp.request = params.get_map()
            rsp.request = {
                Map.method: Map.websocket,
                'headers': bnc_socket.get_socket().header
                # 'headers': bnc_socket.get_socket().sock.headers
            }
        else:
            rsp.status_code = 0000
            rsp.reason = 'BinanceSocket'
            rsp._content = {'comment': "Can't get market historic from websocket."}
        # Backup Down
        self._save_response(rq, params, rsp)
        return BrokerResponse(rsp)

    @staticmethod
    def _get_exchange_infos() -> Map:
        """
        To get exchange's infos\n
        :return: exchange's infos
                 Map[Map.timezone]: {str}   # ex: "UTC"
                 Map[Map.time]:     {int}
                 Map[Map.limit][Map.weight][Map.rateLimitType]: {str}
                 Map[Map.limit][Map.weight][Map.interval]:      {str}
                 Map[Map.limit][Map.weight][Map.intervalNum]:   {int}
                 Map[Map.limit][Map.weight][Map.limit]:         {int}
                 Map[Map.limit][Map.second][Map.rateLimitType]: {str}
                 Map[Map.limit][Map.second][Map.interval]:      {str}
                 Map[Map.limit][Map.second][Map.intervalNum]:   {int}
                 Map[Map.limit][Map.second][Map.limit]:         {int}
                 Map[Map.limit][Map.day][Map.rateLimitType]:    {str}
                 Map[Map.limit][Map.day][Map.interval]:         {str}
                 Map[Map.limit][Map.day][Map.intervalNum]:      {int}
                 Map[Map.limit][Map.day][Map.limit]:            {int}
                 Map[Map.symbol][Pair.__str__()][Map.filters][Map.price_filter]:         {dict}  # Symbol format: 'btc/usdt'
                 Map[Map.symbol][Pair.__str__()][Map.filters][Map.lot_size]:             {dict}
                 Map[Map.symbol][Pair.__str__()][Map.filters][Map.market_lot_size]:      {dict}
                 Map[Map.symbol][Pair.__str__()][Map.iceberg_parts]:        {dict}
                 Map[Map.symbol][Pair.__str__()][Map.percent_price]:        {dict}
                 Map[Map.symbol][Pair.__str__()][Map.min_notional]:         {dict}
                 Map[Map.symbol][Pair.__str__()][Map.max_num_orders]:       {dict}
                 Map[Map.symbol][Pair.__str__()][Map.max_num_algo_orders]:  {dict}
                 Map[Map.symbol][Pair.__str__()]["symbol": "ETHBTC",
                                                "status": "TRADING",
                                                "baseAsset": "ETH",
                                                "baseAssetPrecision": 8,
                                                "quoteAsset": "BTC",
                                                "quotePrecision": 8,
                                                "quoteAssetPrecision": 8,
                                                "orderTypes": [
                                                    "LIMIT",
                                                    "LIMIT_MAKER",
                                                    "MARKET",
                                                    "STOP_LOSS",
                                                    "STOP_LOSS_LIMIT",
                                                    "TAKE_PROFIT",
                                                    "TAKE_PROFIT_LIMIT"
                                                ],
                                                "icebergAllowed": true,
                                                "ocoAllowed": true,
                                                "isSpotTradingAllowed": true,
                                                "isMarginTradingAllowed": true,
                                                "filters": [],  # ❌ changed
                                                "permissions": [
                                                    "SPOT",
                                                    "MARGIN"
                                                ]
                 ]
        """
        if BinanceAPI._EXCHANGE_INFOS is None:
            raise Exception(f"Exchange's infos is not set")
        return BinanceAPI._EXCHANGE_INFOS

    @staticmethod
    def get_exchange_info(*keys):
        ex_infos = BinanceAPI._get_exchange_infos()
        info = ex_infos.get(*keys)
        """
        if info is None:
            keys_str = "', '".join(keys)
            raise IndexError(f"This key(s) ['{keys_str}'] don't exist in exchange's infos.")
        """
        return info

    @staticmethod
    def _get_trade_fees() -> Map:
        return BinanceAPI._TRADE_FEES

    @staticmethod
    def get_trade_fee(pair: Pair) -> dict:
        """
        To get trade fees of the given Pair from Binance's API\n
        :param pair: the pair to get the trade fees
        :return: trade fees of the given Pair
        """
        fees = BinanceAPI._get_trade_fees()
        if fees is None:
            raise Exception(f"Trade fees must be set before. (pair: '{pair}')")
        fee = fees.get(pair.get_merged_symbols())
        if fee is None:
            raise ValueError(f"Binance's API don't support this pair '{pair}'.")
        return fee

    @staticmethod
    def _set_symbol_to_pair() -> None:
        infos = BinanceAPI._get_exchange_infos()
        symbols = infos.get(Map.symbol)
        symbol_to_pair = Map()
        for pair, row in symbols.items():
            symbol = row[Map.symbol].lower()
            symbol_to_pair.put(pair, symbol)
        symbol_to_pair.sort()
        BinanceAPI._SYMBOL_TO_PAIR = symbol_to_pair

    @staticmethod
    def _get_symbol_to_pair() -> Map:
        if BinanceAPI._SYMBOL_TO_PAIR is None:
            BinanceAPI._set_symbol_to_pair()
        return Map(dict(BinanceAPI._SYMBOL_TO_PAIR.get_map()))

    @staticmethod
    def symbol_to_pair(symbol: str) -> str:
        """
        To convert Binance symbol to System pair\n
        i.e: 'BNBUSDT'|'bnbusdt' => 'bnb/usdt'\n
        :param symbol: The symbol to convert
        :return: the symbol converted
        """
        convertor = BinanceAPI._get_symbol_to_pair()
        return convertor.get(symbol.lower())

    @staticmethod
    def get_pairs(match: List[str] = None, no_match: List[str] = None) -> list:
        symbol_to_pair = BinanceAPI._get_symbol_to_pair()
        pair_strs = [pair_str for symbol, pair_str in symbol_to_pair.get_map().items()]
        if match is not None:
            regex_match = '|'.join(match)
            pair_strs = [pair_str for pair_str in pair_strs if _MF.regex_match(regex_match, pair_str)]
        if no_match is not None:
            regex_no_match = '|'.join(no_match)
            pair_strs = [pair_str for pair_str in pair_strs if not _MF.regex_match(regex_no_match, pair_str)]
        return pair_strs

    @staticmethod
    def __get_request_configs() -> dict:
        return BinanceAPI._RQ_CONF

    @staticmethod
    def get_request_config(rq: str) -> dict:
        """
        To get config of the supported request given\n
        :param rq: a supported request
        :exception IndexError: given request is not supported
        :return: config of the given request
        """
        rq_configs = BinanceAPI.__get_request_configs()
        if rq not in rq_configs:
            raise IndexError(f"This request '{rq}' is not supported")
        return rq_configs[rq]

    @staticmethod
    def __get_endpoints() -> dict:
        return BinanceAPI._ENDPOINTS

    @staticmethod
    def get_intervals() -> Map:
        return Map(BinanceAPI._INTERVALS_INT.get_map())

    @staticmethod
    def get_interval(period_str: str) -> int:
        """
        To convert Binance's string interval to second, i.e.: '1m' => 60, '1h' => 3600,...\n
        :param period_str: Binance interval
        :return: Interval in minute
        """
        if period_str not in BinanceAPI._INTERVALS_INT.get_keys():
            raise IndexError(f"This interval '{period_str}' is not supported")
        return BinanceAPI._INTERVALS_INT.get(period_str)

    @staticmethod
    def convert_interval(prd: int) -> str:
        """
        To convert a period time in second to a period interval supported by the API\n
        :param prd: the period time (in second) to convert
        :return: period interval supported by the API
        """
        intrs = BinanceAPI.get_intervals()
        ks = intrs.get_keys()
        nb = len(ks)
        intr = ks[nb - 1]
        for i in range(nb):
            v = intrs.get(ks[i])
            if v >= prd:
                intr = ks[i]
                break
        return intr

    @staticmethod
    def _check_params(rq: str, prms_map: Map) -> bool:
        """
        To check if the given params are correct for the request\n
        :param rq:a supported request
        :param prms_map:params for the request
        :exception IndexError: if mess required params
        :exception Exception: there is params not available for this request
        :return:True if all params are correct else raise IndexError
        """
        rq_cfg = BinanceAPI.get_request_config(rq)
        prms = prms_map.get_map()
        mdtr = rq_cfg[Map.mandatory]
        for k in mdtr:
            if k not in prms:
                raise IndexError(f"This request '{rq}' require the parameter '{k}'")
        rq_prms = rq_cfg[Map.params]
        for k, _ in prms.items():
            if (k not in mdtr) and (k not in rq_prms):
                raise Exception(f"This param '{k}' is not available for this request '{rq}'")
        return True

    @staticmethod
    def fixe_price(pair: Pair, price: Price) -> Price:
        """
        To fixe price to pass Broker's price filters\n
        :param pair: the pair traded
        :param price: the price to fixe
        :return: the new price fixed
        """
        price_filter = Map(BinanceAPI.get_exchange_info(Map.symbol, pair.__str__(), Map.filters, Map.price_filter))
        price_val = price.get_value()
        _min_price = float(price_filter.get(Map.minPrice))
        if (_min_price != 0) and (price_val < _min_price):
            raise ValueError(f"For trade pair '{pair.__str__().upper()}', the minimum price"
                             f" is '{Price(_min_price, price.get_asset().get_symbol())}', instead '{Price}'.")
        _max_price = float(price_filter.get(Map.maxPrice))
        if (_max_price != 0) and (price_val > _max_price):
            raise ValueError(f"For trade pair '{pair.__str__().upper()}', the maximum price"
                             f" is '{Price(_max_price, price.get_asset().get_symbol())}', instead '{Price}'.")
        _tick_size = float(price_filter.get(Map.tickSize))
        if _tick_size != 0:
            new_price_val = BinanceAPI._get_new_price(price_val, _tick_size, _min_price)
            valid = BinanceAPI._will_pass_filter(new_price_val, _tick_size, _min_price)
            if not valid:
                raise Exception(f"the new price will not pass API's price filter, "
                                f"('price':{price_val}, 'tickSize': {_tick_size}, 'min_price': {_min_price}), "
                                f"'new_price': {new_price_val}).")
        else:
            new_price_val = price_val
        return Price(new_price_val, price.get_asset().get_symbol())

    @staticmethod
    def fixe_quantity(pair: Pair, quantity: Price, is_market_order: bool) -> Price:
        """
        To fixe price to pass Broker's price filters\n
        :param pair: the pair traded
        :param quantity: the price to fixe
        :param is_market_order: set True if the quantity is for a market Order else set False
        :return: the new price fixed
        """
        if is_market_order:
            qty_filter = Map(BinanceAPI.get_exchange_info(Map.symbol, pair.__str__(), Map.filters, Map.market_lot_size))
        else:
            qty_filter = Map(BinanceAPI.get_exchange_info(Map.symbol, pair.__str__(), Map.filters, Map.lot_size))
        if len(qty_filter.get_map()) == 0:
            return quantity
        qty_val = quantity.get_value()
        _min_qty = float(qty_filter.get(Map.minQty))
        if (_min_qty != 0) and (qty_val < _min_qty):
            raise ValueError(f"For trade pair '{pair.__str__().upper()}', the minimum price"
                             f" is '{Price(_min_qty, quantity.get_asset().get_symbol())}', instead '{Price}'.")
        _max_qty = float(qty_filter.get(Map.maxQty))
        if (_max_qty != 0) and (qty_val > _max_qty):
            raise ValueError(f"For trade pair '{pair.__str__().upper()}', the maximum price"
                             f" is '{Price(_max_qty, quantity.get_asset().get_symbol())}', instead '{Price}'.")
        _step_size = float(qty_filter.get(Map.stepSize))
        if _step_size != 0:
            new_qty_val = BinanceAPI._get_new_price(qty_val, _step_size, _min_qty)
            valid = BinanceAPI._will_pass_filter(new_qty_val, _step_size, _min_qty)
            if not valid:
                raise Exception(f"the new price will not pass API's price filter, "
                                f"('price':{qty_val}, 'tickSize': {_step_size}, 'min_price': {_min_qty}), "
                                f"'new_price': {new_qty_val}).")
        else:
            new_qty_val = qty_val
        return Price(new_qty_val, quantity.get_asset().get_symbol())

    @staticmethod
    def _get_new_price(value: float, _step: [int, float], _min: [int, float]) -> float:
        """
        To generate a new value that will pass Binance API's filters\n
        :param value: the value to convert
        :param _step: the step size
        :param _min: the minimum value allowed
        :return: a new value that will pass Binance API's filters
        """
        """
        nb_tick_in = int((value - _min) / _step)
        new_value = nb_tick_in * _step + _min
        nb_decimal = _MF.get_nb_decimal(value)
        return round(new_value, nb_decimal)
        """
        value = float(value)
        nb_tick_in = int((value - _min) / _step)
        new_value = nb_tick_in * _step + _min
        nb_decimal = _MF.get_nb_decimal(value)
        return float(round(new_value, nb_decimal))

    @staticmethod
    def _will_pass_filter(new_value: float, _step: [int, float], _min: [int, float]) -> bool:
        """
        To check if the new value will pass Binance API's filter\n
        :param new_value: the new value generated  with «BinanceAPI._get_new_price()»
        :param _step: the step size
        :param _min: the minimum value allowed
        :return: True if will pass Broker's filter else False
        """
        """
        rest = (new_value - _min) % _step
        rounded = round(rest, 1)
        return rounded == 0
        """
        """
        nb_decimal = _MF.get_nb_decimal(new_value)
        nb_step = round((round((new_value - _min), nb_decimal) / _step), nb_decimal)
        decimal = float(str(nb_step).split(".")[-1])
        return decimal == 0
        """
        new_value = float(new_value)
        nb_decimal = _MF.get_nb_decimal(new_value)
        nb_step = round((round((new_value - _min), nb_decimal) / _step), nb_decimal)
        decimal = float(str(nb_step).split(".")[-1])
        return decimal == 0

    @staticmethod
    def _save_response(rq: str, params: Map, rsp: Response) -> None:
        from model.tools.FileManager import FileManager
        _cls = BinanceAPI
        p = Config.get(Config.DIR_SAVE_API_RSP)
        content_json = rsp.content.decode('utf-8')
        content = _MF.json_decode(content_json)
        if (rq == BinanceAPI.RQ_KLINES) and isinstance(content, list):
            content_json = _MF.json_encode({'request': rq, 'length': len(content)}).encode()
        request_method = rsp.request[Map.method] if isinstance(rsp.request, dict) else rsp.request.__dict__[Map.method]
        request_header = _MF.json_encode(dict(rsp.request["headers"])) \
            if isinstance(rsp.request, dict) else _MF.json_encode(dict(rsp.request.__dict__["headers"]))
        row = {
            Map.time: _MF.unix_to_date(_MF.get_timestamp()),
            Map.request: rq,
            Map.method: request_method,
            "status_code": rsp.status_code,
            "reason": rsp.reason,
            "url": rsp.url,
            "request_headers": request_header,
            "response_headers": _MF.json_encode(dict(rsp.headers)),
            "request_content": _MF.json_encode(params.get_map()),    # rsp.request.__dict__["body"],
            "response_content": content_json
        }
        rows = [row]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
