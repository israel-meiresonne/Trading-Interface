from random import random

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.Broker import Broker
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order


class Binance(Broker):
    def __init__(self, cfgs: dict):
        ks = [Map.api_pb, Map.api_sk, Map.test_mode]
        for k in ks:
            if k not in cfgs:
                raise IndexError(f"Property '{k}' is required")
        cfgs_map = Map(cfgs)
        api_pb = cfgs_map.get(Map.api_pb)
        api_sk = cfgs_map.get(Map.api_sk)
        test_mode = cfgs_map.get(Map.test_mode)
        self.__binance_api = BinanceAPI(api_pb, api_sk, test_mode)

    def get_market_price(self) -> MarketPrice:
        mkpc = MarketPrice([random() * 10, random() * 10, random() * 10, random() * 10, random() * 10])
        return mkpc

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
