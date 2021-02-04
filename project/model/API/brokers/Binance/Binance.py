from random import random

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.Broker import Broker
from model.tools.BrokerResponse import BrokerResponse
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
# from model.tools.Order import Order
from model.API.brokers.Binance.BinanceOrder import BinanceOrder


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
        self.__api = BinanceAPI(api_pb, api_sk, test_mode)

    def __get_api(self) -> BinanceAPI:
        return self.__api

    """
        [
          [
            1499040000000,      // Open time
            "0.01634790",       // Open
            "0.80000000",       // High
            "0.01575800",       // Low
            "0.01577100",       // Close
            "148976.11427815",  // Volume
            1499644799999,      // Close time
            "2434.19055334",    // Quote asset volume
            308,                // Number of trades
            "1756.87402397",    // Taker buy base asset volume
            "28.46694368",      // Taker buy quote asset volume
            "17928899.62484339" // Ignore.
          ]
        ]
    """
    def get_market_price(self, prms: dict) -> MarketPrice:
        rq = BinanceAPI.RQ_KLINES
        rq_cfgs_map = Map(BinanceAPI.get_request_config(rq))
        ks = rq_cfgs_map.get(Map.mandatory) + rq_cfgs_map.get(Map.params)
        rtn = self.keys_exist(ks, prms)
        if rtn is not None:
            raise ValueError(f"Param '{rtn}' is required")
        prms_map = Map({k: v for k, v in prms.items() if (v != "") and (v is not None)})
        api = self.__get_api()
        bkr_rsp = api.request_api(rq, prms_map)
        return MarketPrice(bkr_rsp.get_content())

    def execute(self, odr: BinanceOrder) -> BrokerResponse:
        return self.__get_api().request_api(odr.get_api_request(), Map(odr.generate_order()))

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
