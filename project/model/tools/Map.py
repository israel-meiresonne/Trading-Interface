from model.tools.MyJson import MyJson


class Map(MyJson):
    # keys
    msg = "msg"
    cs = "cs"
    index = "index"
    id = "id"
    date = "date"
    action = "action"
    request = "request"
    response = "response"
    maximum = "maximum"
    GET = "GET"
    POST = "POST"
    real = "real"
    buy = "buy"
    sell = "sell"
    transaction = "transaction"
    roi = "roi"
    rank = "rank"
    sum = "sum"
    order = "order"
    trade = "trade"
    green = "green"
    red = "red"
    strategy = "strategy"
    param = "param"
    broker = "broker"
    public = "public"
    secret = "secret"
    # Binance
    # api_pb = "api_pb" => public
    # api_sk = "api_sk" => secret
    test_mode = "test_mode"
    # BinanceAPI
    signed = "signed"
    path = "path"
    mandatory = "mandatory"
    params = "params"
    method = "method"
    DELETE = "DELETE"
    type = "type"
    timestamp = "timestamp"
    startTime = "startTime"
    endTime = "endTime"
    limit = "limit"
    recvWindow = "recvWindow"
    symbol = "symbol"
    interval = "interval"
    signature = "signature"
    api = "api"
    test = "test"
    websocket = "websocket"
    side = "side"
    timeInForce = "timeInForce"
    quantity = "quantity"
    amount = "amount"
    price = "price"
    quoteOrderQty = "quoteOrderQty"
    newClientOrderId = "newClientOrderId"
    stopPrice = "stopPrice"
    icebergQty = "icebergQty"
    newOrderRespType = "newOrderRespType"
    orderId = "orderId"
    origClientOrderId = "origClientOrderId"
    timezone = "timezone"
    serverTime = "serverTime"
    weight = "weight"
    second = "second"
    day = "day"
    rateLimits = "rateLimits"
    symbols = "symbols"
    filters = "filters"
    baseAsset = "baseAsset"
    quoteAsset = "quoteAsset"
    filterType = "filterType"
    price_filter = "price_filter"
    minPrice = "minPrice"
    maxPrice = "maxPrice"
    tickSize = "tickSize"
    market_lot_size = "market_lot_size"
    lot_size = "lot_size"
    minQty = "minQty"
    maxQty = "maxQty"
    stepSize = "stepSize"
    taker = "taker"
    maker = "maker"
    takerCommission = "takerCommission"
    makerCommission = "makerCommission"
    fromId = "fromId"
    # BinanceOrder
    move = "move"
    pair = "pair"
    market = "market"
    status = "status"
    transactTime = "transactTime"
    fee = "fee"
    start = "start"
    end = "end"
    # BinanceRequest
    period = "period"
    number = "number"
    start_time = "start_time"
    begin_time = "begin_time"
    end_time = "end_time"
    account = "account"
    timeout = "timeout"
    snapshotVos = "snapshotVos"
    data = "data"
    balances = "balances"
    asset = "asset"
    free = "free"
    # BinanceResponse
    fills = "fills"
    qty = "qty"
    commission = "commission"
    commissionAsset = "commissionAsset"
    origQty = "origQty"
    executedQty = "executedQty"
    updateTime = "updateTime"
    cummulativeQuoteQty = "cummulativeQuoteQty"
    # MarketPrice
    time = "time"
    close = "close"
    open = "open"
    high = "high"
    low = "low"
    rsi = "rsi"
    tsi = "tsi"
    super_trend = "super_trend"
    volume = "volume"
    # MinMax
    stop = "stop"
    # Order
    left = "left"
    right = "right"
    # Strategy
    capital = "capital"
    rate = "rate"
    # ModelFeature
    slope = "slope"
    yaxis = "yaxis"
    correlation = "correlation"
    pvalue = "pvalue"
    stderr = "stderr"

    def __init__(self, my_map: dict = None):
        my_map = {} if my_map is None else dict(my_map)
        self.__map = my_map

    def _set_map(self, my_map: dict) -> None:
        self.__map = my_map

    def get_map(self) -> dict:
        return self.__map

    def put(self, val, *keys):
        nb = len(keys)
        ValueError("Keys can't be empty") if nb <= 0 else None
        key = keys[0]
        mp = self.get_map()
        if nb == 1:
            mp[key] = val
        else:
            if key in mp:
                mp[key] = self._put_rec(mp[key], val, keys, 1)
            else:
                mp[key] = self._put_rec({}, val, keys, 1)

    def _put_rec(self, mp: dict, val, keys: tuple, i: int):
        if i < len(keys):
            key = keys[i]
            if key in mp:
                i += 1
                mp[key] = self._put_rec(mp[key], val, keys, i)
            else:
                i += 1
                mp = {} if type(mp).__name__ != "dict" else mp
                mp[key] = self._put_rec({}, val, keys, i)
            return mp
        else:
            return val

    def get(self, *keys):
        nb = len(keys)
        if nb <= 0:
            ValueError("Keys can't be empty")
        mp = self.get_map()
        if nb == 1:
            key = keys[0]
            val = mp[key] if (
                    (type(mp).__name__ == "dict") and key in mp) else None
        else:
            key = keys[0]
            val = self._get_rec(mp[key], keys, 1) if (
                    (type(mp).__name__ == "dict") and key in mp) else None
        return val

    def _get_rec(self, mp: dict, keys: tuple, i: int):
        if i == (len(keys) - 1):
            key = keys[i]
            return mp[key] if ((type(mp).__name__ == "dict") and key in mp) else None
        else:
            key = keys[i]
            i += 1
            return self._get_rec(mp[key], keys, i) if ((type(mp).__name__ == "dict") and key in mp) else None

    def get_keys(self) -> list:
        return list(self.__map.keys())

    def sort(self, reverse: bool = False) -> None:
        """
        To order Map from lower key to higher\n
        :param reverse: Set True to sort in descending (High -> Low) else False to sort in ascending (Low -> High)
        """
        my_map = self.get_map()
        self._set_map(dict(sorted(my_map.items(), key=lambda row: row[0], reverse=reverse)))

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Map({'@json': '@json'})
        exec(MyJson.get_executable())
        return instance

    def __str__(self) -> str:
        return self.get_map().__str__()

    def __repr__(self) -> str:
        return self.__str__()
