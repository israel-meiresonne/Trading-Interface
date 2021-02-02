from random import random

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.Broker import Broker
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order


class Binance(Broker):
    def __init__(self, cfgs: dict):
        ks = [Map.api_pb, Map.api_sk, Map.test_mode]
        rtn = self.keys_exist(ks, cfgs)
        if rtn is not None:
            raise IndexError(f"Property '{rtn}' is required")
        cfgs_map = Map(cfgs)
        api_pb = cfgs_map.get(Map.api_pb)
        api_sk = cfgs_map.get(Map.api_sk)
        test_mode = cfgs_map.get(Map.test_mode)
        self.__binance_api = BinanceAPI(api_pb, api_sk, test_mode)

    def __get_binance_api(self) -> BinanceAPI:
        return self.__binance_api

    def get_market_price(self, prms: dict) -> MarketPrice:
        rq = BinanceAPI.RQ_KLINES
        rq_cfgs_map = Map(BinanceAPI.get_request_config(rq))
        ks = rq_cfgs_map.get(Map.mandatory) + rq_cfgs_map.get(Map.params)
        rtn = self.keys_exist(ks, prms)
        if rtn is not None:
            raise IndexError(f"Param '{rtn}' is required")
        prms_map = Map({k: v for k, v in prms.items() if (v != "") and (v is not None)})
        api = self.__get_binance_api()
        bkr_rsp = api.request_api(rq, prms_map)
        return MarketPrice(bkr_rsp.get_content())

    def execute(self, odr: Order) -> None:
        pass

    def get_next_trade_time(self) -> int:
        return int(random() * 10)

    @staticmethod
    def list_paires() -> list:
        prs = [
            "BTC/USDT",
            "BTC/BNB",
            "ETH/USDT",
            "ETH/BNB",
            "EGLD/USDT"
        ]
        return prs
