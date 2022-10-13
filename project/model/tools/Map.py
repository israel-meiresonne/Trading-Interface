from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.MyJson import MyJson


class Map(MyJson):
    PREFIX_ID = 'map_'
    # keys
    message = "message"
    index = "index"
    id = "id"
    date = "date"
    action = "action"
    request = "request"
    response = "response"
    minimum = "minimum"
    maximum = "maximum"
    mean = "mean"
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
    drop = "drop"
    neutral = "neutral"
    rise = "rise"
    middle = "middle"
    x = "x"
    theta = "theta"
    historic = "historic"
    coefficient = "coefficient"
    model = "model"
    shape = "shape"
    score = "score"
    thread = "thread"
    ready = "ready"
    submit = "submit"
    active = "active"
    stock = "stock"
    execution = "execution"
    callback = "callback"
    width = "width"
    zero = "zero"
    starttime = "starttime"
    endtime = "endtime"
    all = "all"
    stdev = "stdev"
    positive = "positive"
    negative = "negative"
    metric = "metric"
    link = "link"
    spot = "spot"
    position = "position"
    residue = "residue"
    option = "option"
    cancel = "cancel"
    value = "value"
    algo = "algo"
    # Binance
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
    tradeId = "tradeId"
    origClientOrderId = "origClientOrderId"
    clientOrderId = "clientOrderId"
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
    intervalNum = 'intervalNum'
    orderListId = "orderListId"
    quoteQty = "quoteQty"
    isBuyer = "isBuyer"
    isMaker = "isMaker"
    isBestMatch = "isBestMatch"
    isWorking = "isWorking"
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
    supertrend = "supertrend"
    psar = "psar"
    volume = "volume"
    macd = "macd"
    signal = "signal"
    histogram = "histogram"
    ema = "ema"
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
    # WebSocket
    on_open = "on_open"
    on_message = "on_message"
    on_error = "on_error"
    on_close = "on_close"
    on_ping = "on_ping"
    on_pong = "on_pong"
    on_cont_message = "on_cont_message"
    get_mask_key = "get_mask_key"
    on_data = "on_data"
    header = "header"
    stream = "stream"

    def __init__(self, my_map: dict = None):
        self.__id = self.PREFIX_ID + _MF.new_code()
        my_map = {} if my_map is None else dict(my_map)
        self.__map = my_map

    def get_id(self) -> str:
        return self.__id

    def _set_map(self, my_map: dict) -> None:
        self.__map = my_map

    def get_map(self) -> dict:
        return self.__map

    def put(self, val, *keys):
        nb = len(keys)
        if nb == 0:
            raise ValueError("Keys can't be empty")
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
                mp = {} if type(mp) != dict else mp
                mp[key] = self._put_rec({}, val, keys, i)
            return mp
        else:
            return val

    def get(self, *keys):
        nb = len(keys)
        if nb == 0:
            raise ValueError("Keys can't be empty")
        mp = self.get_map()
        if nb == 1:
            key = keys[0]
            val = mp[key] if ((type(mp) == dict) and key in mp) else None
        else:
            key = keys[0]
            val = self._get_rec(mp[key], keys, 1) if ((type(mp) == dict) and key in mp) else None
        return val

    def _get_rec(self, mp: dict, keys: tuple, i: int):
        if i == (len(keys) - 1):
            key = keys[i]
            return mp[key] if ((type(mp) == dict) and key in mp) else None
        else:
            key = keys[i]
            i += 1
            return self._get_rec(mp[key], keys, i) if ((type(mp) == dict) and key in mp) else None

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
