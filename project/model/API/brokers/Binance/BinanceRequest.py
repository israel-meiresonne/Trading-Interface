from decimal import Decimal

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.structure.database.ModelFeature import ModelFeature as ModelFeat
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.Price import Price


class BinanceRequest(BrokerRequest):
    CONV_ACCOUNT = Map({
        BrokerRequest.ACCOUNT_MAIN: BinanceAPI.ACCOUNT_TYPE_SPOT,
        BrokerRequest.ACCOUNT_MARGIN: BinanceAPI.ACCOUNT_TYPE_MARGIN,
        BrokerRequest.ACCOUNT_FUTUR: BinanceAPI.ACCOUNT_TYPE_FUTURES,
    })

    def __init__(self, rq: str, prms: Map):
        super().__init__(prms)
        self.__api_request = None
        exec(f'self.{rq}(prms)')

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
            Map.startTime: int(prms.get(Map.begin_time)) if prms.get(Map.begin_time) is not None else None,
            Map.endTime: int(prms.get(Map.end_time)) if prms.get(Map.end_time) is not None else None,
            Map.limit: int(prms.get(Map.number)) if prms.get(Map.number) is not None else None
        })
        self._set_request(request)

    def get_market_price(self) -> BinanceMarketPrice:
        request = self._get_request()
        rsp = self._get_response()
        return BinanceMarketPrice(rsp.get_content(), request.get(Map.interval))

    def _set_account_snapshot(self, prms: Map) -> None:
        ks = [Map.account]
        rtn = ModelFeat.keys_exist(ks, prms.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to get account snapshots")
        acnt = self._get_account_converter().get(prms.get(Map.account))
        if acnt is None:
            raise ValueError(f"This account '{prms.get(Map.account)}' is not supported")
        request = Map({
            Map.type: acnt,
            Map.startTime: int(prms.get(Map.begin_time)) if prms.get(Map.begin_time) is not None else None,
            Map.endTime: int(prms.get(Map.end_time)) if prms.get(Map.end_time) is not None else None,
            Map.limit: int(prms.get(Map.number)) if prms.get(Map.number) is not None else None,
            Map.recvWindow: int(prms.get(Map.timeout)) if prms.get(Map.timeout) is not None else None
        })
        self._set_request(request)

    def get_account_snapshot(self) -> Map:
        rsp = self._get_response()
        content = Map(rsp.get_content())
        blcs = content.get(Map.snapshotVos)[0][Map.data][Map.balance]
        accounts = Map({str(blc[Map.asset]).lower(): Price(Decimal(blc[Map.free]), blc[Map.asset]) for blc in blcs})
        return accounts

    def generate_request(self) -> Map:
        request = self._get_request()
        return Map(ModelFeat.clean(request.get_map()))
