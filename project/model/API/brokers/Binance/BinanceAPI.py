from abc import ABC
from time import sleep
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
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.RateLimit import RateLimit
from model.tools.WaitingRoom import WaitingRoom


class BinanceAPI(ABC):
    _DEBUG = True
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
    _NOT_VIP_REQUESTS = [RQ_KLINES]
    # Configs
    __PATH_ORDER = None
    _RQ_CONF = {
        RQ_SYS_STATUS: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/sapi/v1/system/status",
            Map.weight: 0,
            Map.mandatory: [],
            Map.params: []
        },
        RQ_EXCHANGE_INFOS: {
            Map.signed: False,
            Map.method: Map.GET,
            Map.path: "/api/v3/exchangeInfo",
            Map.weight: 10,
            Map.mandatory: [],
            Map.params: []
        },
        RQ_ACCOUNT_SNAP: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/sapi/v1/accountSnapshot",
            Map.weight: 1,
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
            Map.weight: 1,
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
            Map.weight: 1,
            Map.mandatory: [
                # Map.timestamp | automatically added in BinanceAPI._sign()
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
            Map.weight: 40,     # real limit is 1 per symbol, this is the max weight
            Map.mandatory: [],
            Map.params: [Map.symbol]
        },
        RQ_ALL_ORDERS: {
            Map.signed: True,
            Map.method: Map.GET,
            Map.path: "/api/v3/allOrders",
            Map.weight: 10,
            Map.mandatory: [
                Map.symbol
                # Map.timestamp | automatically added in BinanceAPI._sign()
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
            Map.weight: 10,
            Map.mandatory: [
                Map.symbol
                # Map.timestamp | automatically added in BinanceAPI._sign()
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
            Map.weight: 2,
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
    _CONSTANT_DEFAULT_API_KEY_PUBLIC = Config.get(Config.API_KEY_BINANCE_PUBLIC)
    _CONSTANT_DEFAULT_API_KEY_SECRET = Config.get(Config.API_KEY_BINANCE_SECRET)
    _CONSTANT_DEFAULT_RECVWINDOW = 5000 + 1000
    _CONSTANT_KLINES_DEFAULT_NB_PERIOD = 500
    _EXCHANGE_INFOS = None
    _TRADE_FEES = None
    _LIMIT_INTERVAL_TO_SECOND = Map({
        'SECOND': 1,
        'MINUTE': 60,
        'HOUR': 60 * 60,
        'DAY': 60 * 60 * 24
    })
    """
    _TRADE_FEES[symbol{str}][Map.symbol]:     {str}   # Symbol Format: 'bnbusdt' (= bnb/usdt)
    _TRADE_FEES[symbol{str}][Map.taker]:      {float}
    _TRADE_FEES[symbol{str}][Map.maker]:      {float}
    """
    _SYMBOL_TO_PAIR = None
    # Variables
    _ORDER_RQ_REGEX = r'^RQ_ORDER.*$'
    _TEST_MODE = None
    _SOCKET = None
    _WAITINGROOM = None
    _WAITINGROOM_SLEEP_TIME = 1
    _RATELIMIT_REQUEST =  None
    _RATELIMIT_ORDER_INSTANT =  None
    _RATELIMIT_ORDER_DAILY =  None
    _RATELIMIT_MAX_LIMIT = 0.9

    @staticmethod
    def _set_path_in_request_order_config() -> None:
        rq_configs = BinanceAPI._get_request_configs()
        for rq, config in rq_configs.items():
            if config[Map.path] is None:
                config[Map.path] = BinanceAPI.__PATH_ORDER

    @staticmethod
    def _set_exchange_infos() -> None:
        """
        To get exchange info from Binance's API\n
        """
        bkr_rsp = BinanceAPI._send_local_request(False, BinanceAPI.RQ_EXCHANGE_INFOS, Map())
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

    @staticmethod
    def _send_local_request(test_mode: bool, rq: str, params: Map) -> BrokerResponse:
        api_keys = BinanceAPI.get_default_api_keys()
        public_key = api_keys.get(Map.public)
        secret_key = api_keys.get(Map.secret)
        bkr_rsp = BinanceAPI.request_api(test_mode, public_key, secret_key, rq, params)
        return bkr_rsp

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
        BinanceAPI._set_exchange_infos() if BinanceAPI._EXCHANGE_INFOS is None else None
        return BinanceAPI._EXCHANGE_INFOS

    @staticmethod
    def get_exchange_info(*keys):
        ex_infos = BinanceAPI._get_exchange_infos()
        info = ex_infos.get(*keys)
        return info

    @staticmethod
    def _set_trade_fees() -> None:
        rsp = BinanceAPI._send_local_request(False, BinanceAPI.RQ_TRADE_FEE, Map())
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

    @staticmethod
    def get_trade_fees() -> Map:
        BinanceAPI._set_trade_fees() if BinanceAPI._TRADE_FEES is None else None
        return BinanceAPI._TRADE_FEES

    @staticmethod
    def get_trade_fee(pair: Pair) -> dict:
        """
        To get trade fees of the given Pair from Binance's API\n
        :param pair: the pair to get the trade fees
        :return: trade fees of the given Pair
        """
        fees = BinanceAPI.get_trade_fees()
        if fees is None:
            raise Exception(f"Trade fees must be set before. (pair: '{pair}')")
        fee = fees.get(pair.get_merged_symbols())
        if fee is None:
            raise ValueError(f"Binance's API don't support this pair '{pair}'.")
        return fee

    @staticmethod
    def get_default_api_keys() -> Map:
        """
        To get default keys for Binance's API\n
        Returns
        -------
        api_keys: Map
            Default keys for Binance's API
        """
        return Map({
            Map.public: BinanceAPI._CONSTANT_DEFAULT_API_KEY_PUBLIC,
            Map.secret: BinanceAPI._CONSTANT_DEFAULT_API_KEY_SECRET
        })

    @staticmethod
    def _get_endpoint(i: int) -> str:
        endps = BinanceAPI._get_endpoints()
        test = BinanceAPI._test_mode()
        if test and (i not in range(len(endps[Map.test]))):
            raise IndexError(f"There is no test endpoint with this index '{i}'")
        elif (not test) and (i not in range(len(endps[Map.api]))):
            raise IndexError(f"There is no production endpoint with this index '{i}'")
        return endps[Map.test][i] if test else endps[Map.api][i]

    @staticmethod
    def _set_test_mode(test_mode: bool) -> None:
        if not isinstance(test_mode, bool):
            raise ValueError(f"Type of test mode must be bool, instead '{type(test_mode)}'")
        BinanceAPI._TEST_MODE = test_mode

    @staticmethod
    def _test_mode() -> bool:
        """
        To check if environment is on test mode or real mode\n
        Returns
        -------
        test_mode: bool
            True if environment is on test mode else False
        """
        return BinanceAPI._TEST_MODE

    @staticmethod
    def _set_socket(streams: List[str]) -> None:
        from model.API.brokers.Binance.BinanceSocket import BinanceSocket
        socket = BinanceSocket(streams, run_forever=True)
        BinanceAPI._SOCKET = socket

    @staticmethod
    def _get_socket(new_streams: List[str]) -> Any:
        socket = BinanceAPI._SOCKET
        if socket is None:
            BinanceAPI._set_socket(new_streams)
        else:
            socket.add_streams(new_streams)
        return BinanceAPI._SOCKET

    @staticmethod
    def add_streams(new_streams: List[str]) -> None:
        BinanceAPI._get_socket(new_streams)

    @staticmethod
    def generate_stream(rq: str, symbol: str, period_str: str) -> str:
        """
        To generate Binance stream\n
        Parameters
        ----------
        rq: str
            The request
        symbol: str
            Binance's symbol, i.e.: 'DOGEUSDT', 'BTCEUR', etc...
        period_str: str
            Period interval in string, i.e.: '1m', '1M', '3d', etc...
        Returns
        -------
        stream: str
            Binance stream
        """
        if rq != BinanceAPI.RQ_KLINES:
            raise ValueError(f"Can't generate stream for this request '{rq}'.")
        from model.API.brokers.Binance.BinanceSocket import BinanceSocket
        stream_format = BinanceSocket.get_stream_format_kline()
        symbol = symbol.lower()
        stream = stream_format.replace(f'${Map.symbol}', symbol).replace(f'${Map.interval}', period_str)
        return stream

    @staticmethod
    def close_socket() -> None:
        """
        To close Binance's websocket\n
        """
        BinanceAPI._SOCKET.close()

    @staticmethod
    def _generate_headers(api_keys: Map) -> dict:
        """"
        To generate a headers for a request to the API\n
        Parameters
        ----------
        api_keys: Map
            Public and Secret key for Binance's API
        Returns
        -------
        headers: str
            header for a request to the API
        """
        return {"X-MBX-APIKEY": api_keys.get(Map.public)}

    @staticmethod
    def _generate_url(rq: str, i=0) -> str:
        """
        To generate a url with a test or production API and a endpoint\n
        :param rq: a supported request
        :param i: index of a test or production API
        :return: url where to send the given request
        """
        if BinanceAPI.__PATH_ORDER is None:
            test_mode = BinanceAPI._test_mode()
            if not test_mode:
                BinanceAPI.__PATH_ORDER = BinanceAPI.ORDER_REAL_PATH
            else:
                BinanceAPI.__PATH_ORDER = BinanceAPI.ORDER_TEST_PATH
            BinanceAPI._set_path_in_request_order_config()
        endpoint = BinanceAPI._get_endpoint(i)
        rq_config = BinanceAPI.get_request_config(rq)
        path = rq_config[Map.path]
        return endpoint + path

    @staticmethod
    def _generate_signature(api_keys: Map, params: dict) -> str:
        """
        To generate a HMAC SHA256 signature with the data to send\n
        Parameters
        ----------
        api_keys: Map
            Public and Secret key for Binance's API
        params: Map
            Request's params to send

        Returns
        -------
        signature: str
            A HMAC SHA256 signature generated with the private key and params to send
        """
        qr_str = "&".join([f"{k}={params[k]}" for k in params])
        return new_hmac(api_keys.get(Map.secret).encode('utf-8'), qr_str.encode('utf-8'), hashlib_sha256).hexdigest()

    @staticmethod
    def _sign(api_keys: Map, params: Map) -> None:
        """
        To sign the request with the private key and params\n
        Parameters
        ----------
        api_keys: Map
            Public and Secret key for Binance's API
        params: Map
            Request's params to send
        """
        stamp = _MF.get_timestamp(_MF.TIME_MILLISEC) - 1000
        params.put(stamp, Map.timestamp)
        time_out = params.get(Map.recvWindow)
        new_time_out = time_out + 1000 if time_out is not None else BinanceAPI._CONSTANT_DEFAULT_RECVWINDOW
        params.put(new_time_out, Map.recvWindow)
        sgt = BinanceAPI._generate_signature(api_keys, params.get_map())
        params.put(sgt, Map.signature)

    @staticmethod
    def request_api(test_mode: bool, public_key: str, secret_key: str, rq: str, params: Map) -> BrokerResponse:
        """
        To format and send a request to Binance's API\n
        Parameters
        ----------
        test_mode: bool
            Set True to use Binance's test API else False for the real one
        public_key: str
            A public key for Binance's API
        secret_key: str
            A secret key for Binance's API
        rq: str
            A supported request (i.e.: BinanceAPI.RQ_{...})
        params: Map
            Request's params to send
        Returns
        -------
        broker_response: BrokerResponse
            Binance's API response
        """
        api_keys = BinanceAPI.format_api_keys(public_key, secret_key)
        _stage = Config.get(Config.STAGE_MODE)
        BinanceAPI._check_params(rq, params)
        rq_excluded = [BinanceAPI.RQ_EXCHANGE_INFOS, BinanceAPI.RQ_TRADE_FEE]
        if _stage == Config.STAGE_1:
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            return BinanceFakeAPI.steal_request(rq, params)
        if (_stage == Config.STAGE_2) and (rq not in rq_excluded):
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            if rq == BinanceAPI.RQ_KLINES:
                rsp = BinanceAPI._send_market_historics_request(test_mode, rq, params)
                pair_merged = params.get(Map.symbol)
                period_str = params.get(Map.interval)
                period_milli = int(BinanceAPI.get_interval(period_str) * 1000)
                BinanceFakeAPI.add_market_historic(pair_merged, period_milli, rsp.get_content())
                BinanceFakeAPI.steal_request(rq, params)
                return rsp
            else:
                return BinanceFakeAPI.steal_request(rq, params)
        start_time = params.get(Map.startTime)
        end_time = params.get(Map.endTime)
        if (rq == BinanceAPI.RQ_KLINES) and (end_time is None) and (start_time is None):
            rsp = BinanceAPI._send_market_historics_request(test_mode, rq, params)
        else:
            rsp = BinanceAPI._waitingroom(test_mode, api_keys, rq, params)
        return rsp

    @staticmethod
    def get_waitingroom() -> WaitingRoom:
        if BinanceAPI._WAITINGROOM is None:
            name = f"{BinanceAPI.__name__}_Send_Request"
            BinanceAPI._WAITINGROOM = WaitingRoom(name)
        return BinanceAPI._WAITINGROOM

    @staticmethod
    def get_max_limit_rate() -> float:
        return BinanceAPI._RATELIMIT_MAX_LIMIT

    @staticmethod
    def limit_interval_to_second(limit_interval: str) -> int:
        time_second = BinanceAPI._LIMIT_INTERVAL_TO_SECOND.get(limit_interval)
        if time_second is None:
            raise ValueError(f"Unknown limit interval '{limit_interval}'")
        return time_second

    @staticmethod
    def get_ratelimit_request() -> RateLimit:
        if BinanceAPI._RATELIMIT_REQUEST is None:
            rq_limit = BinanceAPI.get_exchange_info(Map.limit, Map.weight)
            unit_interval = BinanceAPI.limit_interval_to_second(rq_limit[Map.interval])
            limit = int(rq_limit[Map.limit] * BinanceAPI.get_max_limit_rate())
            interval = unit_interval * rq_limit[Map.intervalNum]
            BinanceAPI._RATELIMIT_REQUEST = RateLimit(limit, interval)
        return BinanceAPI._RATELIMIT_REQUEST

    @staticmethod
    def get_ratelimit_order_instant() -> RateLimit:
        if BinanceAPI._RATELIMIT_ORDER_INSTANT is None:
            order_sec_limit = BinanceAPI.get_exchange_info(Map.limit, Map.second)
            unit_interval = BinanceAPI.limit_interval_to_second(order_sec_limit[Map.interval])
            limit = int(order_sec_limit[Map.limit] * BinanceAPI.get_max_limit_rate())
            interval = unit_interval * order_sec_limit[Map.intervalNum]
            BinanceAPI._RATELIMIT_ORDER_INSTANT = RateLimit(limit, interval)
        return BinanceAPI._RATELIMIT_ORDER_INSTANT

    @staticmethod
    def get_ratelimit_order_daily() -> RateLimit:
        if BinanceAPI._RATELIMIT_ORDER_DAILY is None:
            rq_day_limit = BinanceAPI.get_exchange_info(Map.limit, Map.day)
            unit_interval = BinanceAPI.limit_interval_to_second(rq_day_limit[Map.interval])
            limit = int(rq_day_limit[Map.limit] * BinanceAPI.get_max_limit_rate())
            interval = unit_interval * rq_day_limit[Map.intervalNum]
            BinanceAPI._RATELIMIT_ORDER_DAILY = RateLimit(limit, interval)
        return BinanceAPI._RATELIMIT_ORDER_DAILY

    @staticmethod
    def can_send_request(rq: str) -> bool:
        _cls = BinanceAPI
        can_send = True
        weight = _cls._get_request_configs()[rq][Map.weight]
        rq_ratelimit = _cls.get_ratelimit_request()
        order_instant_ratelimit = _cls.get_ratelimit_order_instant()
        order_daily_ratelimit = _cls.get_ratelimit_order_daily()
        if weight > rq_ratelimit.get_remaining_weight():
            can_send = False
        if can_send and (_MF.regex_match(_cls._ORDER_RQ_REGEX, rq) or (rq == _cls.RQ_CANCEL_ORDER)):
            if weight > order_instant_ratelimit.get_remaining_weight():
                can_send = False
            if can_send and weight > order_daily_ratelimit.get_remaining_weight():
                limit = order_daily_ratelimit.get_limit()
                raise Exception(f"BinanceAPI's daily limit '{limit}' for Order request is reached")
        return can_send

    @staticmethod
    def get_limits_sleep_time(rq: str) -> int:
        _cls = BinanceAPI
        rq_ratelimit = _cls.get_ratelimit_request()
        order_instant_ratelimit = _cls.get_ratelimit_order_instant()
        sleep_time = rq_ratelimit.get_remaining_time()
        if _MF.regex_match(_cls._ORDER_RQ_REGEX, rq) or (rq == _cls.RQ_CANCEL_ORDER):
            order_sleep_time = order_instant_ratelimit.get_remaining_time()
            sleep_time = sleep_time if sleep_time >= order_sleep_time else order_sleep_time
        return sleep_time

    @staticmethod
    def _add_weight(rq: str) -> None:
        _cls = BinanceAPI
        weight = _cls._get_request_configs()[rq][Map.weight]
        rq_ratelimit = _cls.get_ratelimit_request()
        order_instant_ratelimit = _cls.get_ratelimit_order_instant()
        order_daily_ratelimit = _cls.get_ratelimit_order_daily()
        rq_ratelimit.add_weight(weight)
        if _MF.regex_match(_cls._ORDER_RQ_REGEX, rq) or (rq == _cls.RQ_CANCEL_ORDER):
            order_instant_ratelimit.add_weight(weight)
            order_daily_ratelimit.add_weight(weight)

    @staticmethod
    def _update_limits(rq: str, response: BrokerResponse) -> None:
        _cls = BinanceAPI
        rq_ratelimit = _cls.get_ratelimit_request()
        order_instant_ratelimit = _cls.get_ratelimit_order_instant()
        order_daily_ratelimit = _cls.get_ratelimit_order_daily()
        header = response.get_headers()
        # Update request
        key_rq_header = 'x-mbx-used-weight-1m'
        rq_header_weight = int(header[key_rq_header] if key_rq_header in header else header['X-SAPI-USED-IP-WEIGHT-1M'])
        rq_ratelimit_weight = rq_ratelimit.get_weight()
        if (rq_ratelimit_weight is not None) and (rq_ratelimit_weight != rq_header_weight):
            rq_ratelimit.update_weight(rq_header_weight)
        # Update order
        if _MF.regex_match(_cls._ORDER_RQ_REGEX, rq) or (rq == _cls.RQ_CANCEL_ORDER):
            # Instant order
            header_instant_weight = int(header['x-mbx-order-count-10s'])
            order_instant_weight  = order_instant_ratelimit.get_weight()
            if (order_instant_weight is not None) and (order_instant_weight != header_instant_weight):
                order_instant_ratelimit.update_weight(header_instant_weight)
            # Daily order
            header_daily_weight = int(header['x-mbx-order-count-1d'])
            order_daily_weight = order_daily_ratelimit.get_weight()
            if (order_daily_weight is not None) and (order_daily_weight != header_daily_weight):
                order_daily_ratelimit.update_weight(header_daily_weight)

    @staticmethod
    def _waitingroom(test_mode: bool, api_keys: Map, rq: str, params: Map) -> BrokerResponse:
        _cls = BinanceAPI
        is_vip = rq not in _cls._NOT_VIP_REQUESTS
        if is_vip:
            response = _cls._send_request(test_mode, api_keys, rq, params)
        else:
            def time_to_str(time: int) -> str:
                return f"{int(time / 60)}min.{time % 60}sec."
            def room_size(waitingroom: WaitingRoom) -> int:
                return len(waitingroom.get_tickets())
            waitingroom = _cls.get_waitingroom()
            ticket = waitingroom.join_room()
            join_unix_time = _MF.get_timestamp()
            print(f"{_MF.prefix()}Join room"
                  f" (size='{room_size(waitingroom)}', ticket=" + '\033[34m' + f"'{ticket}'" + '\033[0m') \
                if _cls._DEBUG else None
            try:
                room_sleep_time = _cls._WAITINGROOM_SLEEP_TIME
                while not waitingroom.my_turn(ticket):
                    sleep(room_sleep_time)
                while not _cls.can_send_request(rq):
                    limits_sleep_time = _cls.get_limits_sleep_time(rq)
                    if isinstance(limits_sleep_time, int):
                        unix_time = _MF.get_timestamp()
                        unix_date = _MF.unix_to_date(unix_time)
                        wakeup_date = _MF.unix_to_date(unix_time + limits_sleep_time)
                        limits_sleep_time_str = time_to_str(limits_sleep_time)
                        print(f"{_MF.prefix()}\033[33mCan't send request, sleep for '{limits_sleep_time_str}'"
                              f" from '{unix_date}'->'{wakeup_date}'"
                              f" (size='{room_size(waitingroom)}', ticket=" + '\033[34m' + f"'{ticket}'" + '\033[0m') \
                            if _cls._DEBUG else None
                    sleep(limits_sleep_time) if isinstance(limits_sleep_time, int) else None
                response = _cls._send_request(test_mode, api_keys, rq, params)
            except Exception as error:
                waitingroom.quit_room(ticket)
                wait_time_str = time_to_str(_MF.get_timestamp() - join_unix_time)
                print(f"{_MF.prefix()}\033[31mQuit room in '{wait_time_str}'"
                      f" (size='{room_size(waitingroom)}', ticket='{ticket}'" + '\033[0m') if _cls._DEBUG else None
                raise error
            waitingroom.treat_ticket(ticket)
            wait_time_str = time_to_str(_MF.get_timestamp() - join_unix_time)
            print(f"{_MF.prefix()}\033[32mTicket treated in '{wait_time_str}'"
                  f" (size='{room_size(waitingroom)}', ticket=" + '\033[34m' + f"'{ticket}'" + '\033[0m') \
                if _cls._DEBUG else None
        return response

    @staticmethod
    def _send_request(test_mode: bool, api_keys: Map, rq: str, params: Map) -> BrokerResponse:
        """
        To send a request to the API\n
        Parameters
        ----------
        test_mode: bool
            Set True to use Binance's test API else False for the real one
        api_keys: Map
            Public and Secret key for Binance's API
                api_keys[Map.public]:   {str}   # API Public key
                api_keys[Map.secret]:   {str}   # API Secret key
        rq: str
            A supported request (i.e.: BinanceAPI.RQ_{...})
        params: Map
            Request's params to send
        Returns
        -------
        broker_response: BrokerResponse
            Binance's API response
        """
        _cls = BinanceAPI
        _cls._set_test_mode(test_mode)
        _stage = Config.get(Config.STAGE_MODE)
        rq_cfg = _cls.get_request_config(rq)
        if rq_cfg[Map.signed]:
            _cls._sign(api_keys, params)
        headers = _cls._generate_headers(api_keys)
        url = _cls._generate_url(rq)
        method = rq_cfg[Map.method]
        if method == Map.GET:
            rsp = rq_get(url, params.get_map(), headers=headers)
        elif method == Map.POST:
            rsp = rq_post(url, params.get_map(), headers=headers)
        elif method == Map.DELETE:
            ds = params.get_map()
            url += '?' + '&'.join([f'{k}={v}' for k, v in ds.items()])
            rsp = rq_delete(url, headers=headers)
        else:
            raise Exception(f"The request method {method} is not supported")
        bkr_rsp = BrokerResponse(rsp)
        # Manage weight
        try:
            if rq != _cls.RQ_EXCHANGE_INFOS:
                _cls._add_weight(rq)
                _cls._update_limits(rq, bkr_rsp)
        except Exception as error:
            _cls._save_response(rq, params, rsp)
            raise error
        # Backup Down
        _cls._save_response(rq, params, rsp)
        return bkr_rsp

    @staticmethod
    def _send_market_historics_request(test_mode: bool, rq: str, params: Map) -> BrokerResponse:
        BinanceAPI._set_test_mode(test_mode)
        symbol = params.get(Map.symbol)
        period_str = params.get(Map.interval)
        stream = BinanceAPI.generate_stream(rq, symbol, period_str)
        bnc_socket = BinanceAPI._get_socket([stream])
        market_historic = bnc_socket.get_market_historic(stream)
        rsp = Response()
        rsp.request = {
            Map.method: Map.websocket,
            'headers': bnc_socket.get_socket().header
        }
        if isinstance(market_historic, list):
            limit = params.get(Map.limit)
            if limit is not None:
                new_market_historic = market_historic[-limit:len(market_historic)]
            else:
                limit = BinanceAPI._CONSTANT_KLINES_DEFAULT_NB_PERIOD
                new_market_historic = market_historic[-limit:len(market_historic)]
            rsp.status_code = 200
            rsp.reason = 'OK'
            rsp._content = _MF.json_encode(new_market_historic).encode()
            rsp.url = bnc_socket.get_url()
        else:
            rsp.status_code = 0000
            rsp.reason = 'BinanceSocket fail'
            rsp_content = {'comment': "Can't get market historic from websocket.", 'data_returned': market_historic}
            rsp._content = _MF.json_encode(rsp_content)
        return BrokerResponse(rsp)

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
    def _get_request_configs() -> dict:
        return BinanceAPI._RQ_CONF

    @staticmethod
    def get_request_config(rq: str) -> dict:
        """
        To get config of the supported request given\n
        :param rq: a supported request
        :exception IndexError: given request is not supported
        :return: config of the given request
        """
        rq_configs = BinanceAPI._get_request_configs()
        if rq not in rq_configs:
            raise IndexError(f"This request '{rq}' is not supported")
        return rq_configs[rq]

    @staticmethod
    def _get_endpoints() -> dict:
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
        if not isinstance(prd, int):
            raise ValueError(f"The period to convert must be type int, instead '{prd}({type(prd)})'")
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
    def format_api_keys(public_key: str, secret_key: str) -> Map:
        return Map({Map.public: public_key, Map.secret: secret_key})

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
        content = _MF.json_decode(content_json) if isinstance(content_json, str) else None
        if (rq == _cls.RQ_KLINES) and isinstance(content, list):
            new_content = {
                'request': rq,
                'length': len(content),
                Map.symbol: params.get(Map.symbol),
                'last_row_close': content[-1][4]
            }
            content_json = _MF.json_encode(new_content).encode()
        request_method = rsp.request[Map.method] if isinstance(rsp.request, dict) else rsp.request.__dict__[Map.method]
        request_header = _MF.json_encode(dict(rsp.request["headers"])) \
            if isinstance(rsp.request, dict) else _MF.json_encode(dict(rsp.request.__dict__["headers"]))
        exchange_is_set = isinstance(_cls._EXCHANGE_INFOS, Map)
        request_weight = _cls.get_ratelimit_request().get_weight() if exchange_is_set else '—'
        order_instant_weight = _cls.get_ratelimit_order_instant().get_weight() if exchange_is_set else '—'
        order_daily_weight = _cls.get_ratelimit_order_daily().get_weight() if exchange_is_set else '—'
        row = {
            Map.time: _MF.unix_to_date(_MF.get_timestamp()),
            Map.request: rq,
            Map.method: request_method,
            "status_code": rsp.status_code,
            "reason": rsp.reason,
            'elapsed': _MF.float_to_str(rsp.elapsed.total_seconds()) if rsp.elapsed is not None else '—',
            'request_weight': request_weight,
            'order_instant_weight': order_instant_weight,
            'order_daily_weight': order_daily_weight,
            "url": rsp.url,
            "request_headers": request_header,
            "response_headers": _MF.json_encode(dict(rsp.headers)),
            "request_content": _MF.json_encode(params.get_map()),
            "response_content": content_json
        }
        rows = [row]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite, make_dir=True)
