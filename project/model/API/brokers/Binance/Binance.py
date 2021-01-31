from random import random
from model.structure.Broker import Broker
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order


class Binance(Broker):
    def __init__(self, cfs: dict):
        pass

    def get_market_price(self) -> MarketPrice:
        mkpc = MarketPrice([random()*10, random()*10, random()*10,random()*10 ,random()*10])
        return mkpc

    def execute(self, odr: Order) -> None:
        pass

    def get_next_trade_time(self) -> int:
        return int(random()*10)

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



