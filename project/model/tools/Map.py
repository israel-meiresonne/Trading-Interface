class Map:
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
    # Binance
    api_pb = "api_pb"
    api_sk = "api_sk"
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
    # BinanceOrder
    move = "move"
    pair = "pair"
    market = "market"
    status = "status"
    transactTime = "transactTime"
    fee = "fee"
    # BinanceRequest
    period = "period"
    number = "number"
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

    def __init__(self, mp=None):
        mp = {} if mp is None else dict(mp)
        self.__map = mp

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
            ValueError("Kyes can't be empty")
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

    def __str__(self) -> str:
        return self.get_map().__str__()
