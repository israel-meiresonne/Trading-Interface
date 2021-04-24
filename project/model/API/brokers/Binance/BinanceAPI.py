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
    # API Constants
    _EXCHANGE_INFOS = None

    def __init__(self, api_pb: str, api_sk: str, test_mode: bool):
        """
        Constructor\n
        :param api_pb: API's public key
        :param api_sk: API's secret key
        :param test_mode: set True to call test API else False to call production API
        """
        self.__id = 'binance_api_' + str(_MF.get_timestamp(_MF.TIME_MILLISEC))
        self.__api_public_key = api_pb
        self.__api_secret_key = api_sk
        self.__test_mode = test_mode
        if (type(test_mode) == bool) and (not test_mode):
            BinanceAPI.__PATH_ORDER = self.ORDER_REAL_PATH
        else:
            BinanceAPI.__PATH_ORDER = self.ORDER_TEST_PATH
        self._update_order_config()
        self._set_exchange_infos()

    def _update_order_config(self) -> None:
        rq_configs = self.__get_request_configs()
        for rq, config in rq_configs.items():
            if config[Map.path] is None:
                config[Map.path] = self.__PATH_ORDER

    def _set_exchange_infos(self) -> None:
        """
        To get exchange info from Broker's API\
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
                 Map[Map.symbol][Pair.__str__()][Map.price_filter]:         {dict}
                 Map[Map.symbol][Pair.__str__()][Map.lot_size]:             {dict}
                 Map[Map.symbol][Pair.__str__()][Map.market_lot_size]:      {dict}
                 Map[Map.symbol][Pair.__str__()][Map.iceberg_parts]:        {dict}
                 Map[Map.symbol][Pair.__str__()][Map.percent_price]:        {dict}
                 Map[Map.symbol][Pair.__str__()][Map.min_notional]:         {dict}
                 Map[Map.symbol][Pair.__str__()][Map.max_num_orders]:       {dict}
                 Map[Map.symbol][Pair.__str__()][Map.max_num_algo_orders]:  {dict}
        """
        if BinanceAPI._EXCHANGE_INFOS is None:
            raise Exception(f"Exchange's infos is not set")
        return BinanceAPI._EXCHANGE_INFOS

    @staticmethod
    def get_exchange_info(*keys):
        ex_infos = BinanceAPI._get_exchange_infos()
        info = ex_infos.get(*keys)
        if info is None:
            keys_str = "', '".join(keys)
            raise IndexError(f"This key(s) ['{keys_str}'] don't exist in exchange's infos.")
        return info

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

    def __sign(self, prms_map: Map) -> None:
        """
        To sign the request with the private key and params\n
        :param prms_map: params of a request
        """
        # ds_map.put(recvWindow, Map.recvWindow)
        stamp = _MF.get_timestamp(_MF.TIME_MILLISEC)
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
        _stage = Config.get(Config.STAGE_MODE)
        if _stage == Config.STAGE_1:
            from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
            return BinanceFakeAPI.steal_request(self.get_id(), rq, params)
        if _stage == Config.STAGE_2:
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
        _stage = Config.get(Config.STAGE_MODE)
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
            url += '?' + '&'.join([f'{k}={v}' for k, v in ds.items()])
            rsp = rq_delete(url, headers=hdrs)
        else:
            raise Exception(f"The request method {mtd} is not supported")
        bkr_rsp = BrokerResponse(rsp)
        rsp_status = bkr_rsp.get_status_code()
        # Backup Down
        self._save_response(rq, rsp)
        # Backup Up
        if rsp_status != 200:
            raise Exception(f"(status code: {rsp_status}): {bkr_rsp.get_content()}")
        return bkr_rsp

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
    def _get_new_price(value, _step, _min) -> float:
        """
        To generate a new value that will pass Binance API's filters\n
        :param value: the value to convert
        :param _step: the step size
        :param _min: the minimum value allowed
        :return: a new value that will pass Binance API's filters
        """
        nb_tick_in = int((value - _min) / _step)
        new_value = nb_tick_in * _step + _min
        nb_decimal = _MF.get_nb_decimal(value)
        return round(new_value, nb_decimal)  # if nb_decimal is not None else round(new_value)

    @staticmethod
    def _will_pass_filter(new_value, _step, _min) -> bool:
        """
        To check if the new value will pass Binance API's filter\n
        :param new_value: the new value generated  with «BinanceAPI._get_new_price()»
        :param _step: the step size
        :param _min: the minimum value allowed
        :return: True if will pass Broker's filter else False
        """
        rest = (new_value - _min) % _step
        rounded = round(rest, 1)
        return rounded == 0

    @staticmethod
    def _save_response(rq: str, rsp: Response) -> None:
        from model.tools.FileManager import FileManager
        _cls = BinanceAPI
        p = Config.get(Config.DIR_SAVE_API_RSP)
        row = {
            Map.request: rq,
            Map.method: rsp.request.__dict__[Map.method],
            "status_code": rsp.status_code,
            "reason": rsp.reason,
            "url": rsp.url,
            "request_headers": _MF.json_encode(dict(rsp.request.__dict__["headers"])),
            "response_headers": _MF.json_encode(dict(rsp.headers)),
            "response_content": rsp.content,
            "request_content": rsp.request.__dict__["body"]
        }
        rows = [row]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
