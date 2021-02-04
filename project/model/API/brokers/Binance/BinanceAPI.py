# from datetime import datetime
# from time import time as time_time
from requests import get as rq_get
from requests import post as rq_post
from hmac import new as new_hmac
from hashlib import sha256 as hashlib_sha256

from model.structure.database.ModelFeature import ModelFeature as MDFT
from model.tools.Map import Map
from model.tools.BrokerResponse import BrokerResponse


class BinanceAPI:
    # Requests
    RQ_SYS_STATUS = "RQ_SYS_STATUS"
    RQ_EXCG_INFOS = "RQ_EXCG_INFOS"
    RQ_KLINES = "RQ_KLINES"
    RQ_ACCOUNT_SNAP = "RQ_ACCOUNT_SNAP"
    RQ_ORDER_LIMIT = "RQ_ORDER_LIMIT"
    RQ_ORDER_MARKET_qty = "RQ_ORDER_MARKET_qty"
    RQ_ORDER_MARKET_amount = "RQ_ORDER_MARKET_amount"
    RQ_ORDER_STOP_LOSS = "RQ_ORDER_STOP_LOSS"
    RQ_ORDER_STOP_LOSS_LIMIT = "RQ_ORDER_STOP_LOSS_LIMIT"
    RQ_ORDER_TAKE_PROFIT = "RQ_ORDER_TAKE_PROFIT"
    RQ_ORDER_TAKE_PROFIT_LIMIT = "RQ_ORDER_TAKE_PROFIT_LIMIT"
    RQ_ORDER_LIMIT_MAKER = "RQ_ORDER_LIMIT_MAKER"
    # Configs
    # __PATH_ORDER = "/api/v3/order"
    __PATH_ORDER = "/api/v3/order/test"
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
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    TYPE_MARKET = "MARKET"

    def __init__(self, api_pb: str, api_sk: str, test_mode: bool):
        self.__api_public_key = api_pb
        self.__api_secret_key = api_sk
        self.__test_mode = test_mode

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
        stamp = MDFT.get_time_stamps(MDFT.TIME_MILLISEC)
        prms_map.put(stamp, Map.timestamp)
        sgt = self.__generate_signature(prms_map.get_map())
        prms_map.put(sgt, Map.signature)

    def _check_params(self, rq: str, prms_map: Map) -> bool:
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

    def request_api(self, rq: str, prms_map: Map) -> BrokerResponse:
        """
        To config and send a request to the API\n
        :param rq: a supported request
        :param prms_map: params to send
        :return: API's response
        """
        rq_cfg = BinanceAPI.get_request_config(rq)
        self._check_params(rq, prms_map)
        if rq_cfg[Map.signed]:
            self.__sign(prms_map)
        return self._send_request(rq, prms_map)

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
        else:
            raise Exception(f"The request method {mtd} is not supported")
        return BrokerResponse(rsp)
