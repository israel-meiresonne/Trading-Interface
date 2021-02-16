class Map:
    # keys
    msg = "msg"
    cs = "cs"
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
    GET = "GET"
    POST = "POST"
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
    # BinanceOrder
    move = "move"
    pair = "pair"
    market = "market"
    # BinanceRequest
    period = "period"
    number = "number"
    begin_time = "begin_time"
    end_time = "end_time"
    account = "account"
    timeout = "timeout"
    snapshotVos = "snapshotVos"
    data = "data"
    balance = "balance"
    asset = "asset"
    free = "free"
    # MinMax
    stop = "stop"
    # Order
    left = "left"
    right = "right"
    # Strategy
    capital = "capital"
    rate = "rate"

    def __init__(self, mp=None):
        mp = {} if mp is None else dict(mp)
        self.__map = mp

    def get_map(self):
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
                mp[key] = self.put_rec(mp[key], val, keys, 1)
            else:
                mp[key] = self.put_rec({}, val, keys, 1)

    def put_rec(self, mp: dict, val, keys: list, i: int):
        if i < len(keys):
            key = keys[i]
            if key in mp:
                i += 1
                mp[key] = self.put_rec(mp[key], val, keys, i)
            else:
                i += 1
                mp = {} if type(mp).__name__ != "dict" else mp
                mp[key] = self.put_rec({}, val, keys, i)
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
            val = self.get_rec(mp[key], keys, 1) if (
                    (type(mp).__name__ == "dict") and key in mp) else None
        return val

    def get_rec(self, mp: dict, keys: list, i: int):
        if i == (len(keys) - 1):
            key = keys[i]
            return mp[key] if ((type(mp).__name__ == "dict") and key in mp) else None
        else:
            key = keys[i]
            i += 1
            return self.get_rec(mp[key], keys, i) if ((type(mp).__name__ == "dict") and key in mp) else None

    def get_map(self) -> dict:
        return self.__map

    def get_keys(self) -> list:
        return list(self.__map.keys())
