from requests import get as rq_get
from requests import post as rq_post
from requests import delete as rq_delete
from hmac import new as new_hmac
from hashlib import sha256 as hashlib_sha256

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as ModelFeat
from model.tools.Map import Map
from model.tools.BrokerResponse import BrokerResponse


class BinanceAPI:
    # Const
    ORDER_TEST_PATH = "/api/v3/order/test"
    ORDER_REAL_PATH = "/api/v3/order"
    # Requests
    RQ_SYS_STATUS = "RQ_SYS_STATUS"
    RQ_EXCG_INFOS = "RQ_EXCG_INFOS"
    RQ_KLINES = "RQ_KLINES"
    RQ_ACCOUNT_SNAP = "RQ_ACCOUNT_SNAP"
    # Orders
    RQ_ALL_ORDERS = "RQ_ALL_ORDERS"
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
            Map.path: "/wapi/v3/systemStatus.html",
            Map.mandatory: [],
            Map.params: []
        },
        RQ_EXCG_INFOS: {
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
                Map.timeInForce,
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
        '15m': 50*15,
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
    CONSTRAINT_LIMIT = 1000
    CONSTRAINT_RECVWINDOW = 60000
    CONSTRAINT_SNAP_ACCOUT_MIN_LIMIT = 5
    CONSTRAINT_SNAP_ACCOUT_MAX_LIMIT = 30

    def __init__(self, api_pb: str, api_sk: str, test_mode: bool):
        """
        Constructor\n
        :param api_pb: API's public key
        :param api_sk: API's secret key
        :param test_mode: set True to call test API else False to call production API
        """
        self.__id = 'binance_api_' + str(ModelFeat.get_timestamp(ModelFeat.TIME_MILLISEC))
        self.__api_public_key = api_pb
        self.__api_secret_key = api_sk
        self.__test_mode = test_mode
        if (type(test_mode) == bool) and (not test_mode):
            self.__PATH_ORDER = self.ORDER_REAL_PATH
        else:
            self.__PATH_ORDER = self.ORDER_TEST_PATH

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
        rq_cfgs = BinanceAPI.__get_request_configs()
        if rq not in rq_cfgs:
            raise IndexError(f"This request '{rq}' is not supported")
        return rq_cfgs[rq]

    @staticmethod
    def __get_endpoints() -> dict:
        return BinanceAPI._ENDPOINTS

    def __get_endpoint(self, i: int) -> str:
        endps = BinanceAPI.__get_endpoints()
        test = self.__is_test_mode()
        if test and (i not in range(len(endps[Map.test]))):
            raise IndexError(f"There is no test endpoint with this index '{i}'")
        elif (not test) and (i not in range(len(endps[Map.api]))):
            raise IndexError(f"There is no production endpoint with this index '{i}'")
        return endps[Map.test][i] if test else endps[Map.api][i]

    def get_id(self) -> str:
        return self.__id

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

    @staticmethod
    def get_intervals() -> Map:
        return Map(BinanceAPI._INTERVALS_INT.get_map())

    @staticmethod
    def get_interval(k) -> int:
        if k not in BinanceAPI._INTERVALS_INT.get_keys():
            raise IndexError(f"This interval '{k}' is not supported")
        return BinanceAPI._INTERVALS_INT.get(k)

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
        rq_cfg = BinanceAPI.get_request_config(rq)
        path = rq_cfg[Map.path]
        return endp + path

    def __generate_signature(self, prms: dict) -> str:
        """
        To generate a HMAC SHA256 signature with the data to send\n
        :param prms: data to send to Binance's API
        :return: a HMAC SHA256 signature generated with the data to send
        """
        qr_str = "&".join([f"{k}={prms[k]}" for k in prms])
        return new_hmac(self.__get_api_secret_key().encode('utf-8'), qr_str.encode('utf-8'), hashlib_sha256).hexdigest()

    def __sign(self, prms_map: Map) -> None:
        """
        To sign the request with the private key and params\n
        :param prms_map: params of a request
        """
        # ds_map.put(recvWindow, Map.recvWindow)
        stamp = ModelFeat.get_timestamp(ModelFeat.TIME_MILLISEC)
        prms_map.put(stamp, Map.timestamp)
        sgt = self.__generate_signature(prms_map.get_map())
        prms_map.put(sgt, Map.signature)

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

    def request_api(self, rq: str, params: Map) -> BrokerResponse:
        """
        To config and send a request to the API\n
        :param rq: a supported request
        :param params: params to send
        :return: API's response
        """
        stage = Config.get(Config.STAGE_MODE)
        if stage == Config.STAGE_1:
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            return BinanceFakeAPI.steal_request(self.get_id(), rq, params)
        if stage == Config.STAGE_2:
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            log_id = self.get_id()
            if rq == self.RQ_KLINES:
                rq_cfg = self.get_request_config(rq)
                self._check_params(rq, params)
                if rq_cfg[Map.signed]:
                    self.__sign(params)
                rsp = self._send_request(rq, params)
                BinanceFakeAPI.set_backup(log_id, rsp.get_content())
                BinanceFakeAPI.steal_request(log_id, rq, params)
                return rsp
            else:
                return BinanceFakeAPI.steal_request(log_id, rq, params)
        rq_cfg = self.get_request_config(rq)
        self._check_params(rq, params)
        if rq_cfg[Map.signed]:
            self.__sign(params)
        rsp = self._send_request(rq, params)
        return rsp

    def _send_request(self, rq: str, prms_map: Map) -> BrokerResponse:
        """
        To send a request to the API\n
        :param rq: a supported request
        :param prms_map: params to send
        :return: API's response
        """
        rq_cfg = BinanceAPI.get_request_config(rq)
        hdrs = self.__generate_headers()
        url = self._generate_url(rq)
        mtd = rq_cfg[Map.method]
        if mtd == Map.GET:
            rsp = rq_get(url, prms_map.get_map(), headers=hdrs)
        elif mtd == Map.POST:
            rsp = rq_post(url, prms_map.get_map(), headers=hdrs)
        elif mtd == Map.DELETE:
            ds = prms_map.get_map()
            url += '?' + '&'.join([f'k={v}' for k, v in ds.items()])
            rsp = rq_delete(url, headers=hdrs)
        else:
            raise Exception(f"The request method {mtd} is not supported")
        bkr_rsp = BrokerResponse(rsp)
        rsp_status = bkr_rsp.get_status_code()
        if rsp_status != 200:
            raise Exception(f"(status code: {rsp_status}): {bkr_rsp.get_content()}")
        return bkr_rsp
