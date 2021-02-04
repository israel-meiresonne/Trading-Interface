from random import random

from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.Strategy import Strategy
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price

class MinMax(Strategy):
    def __init__(self):
        pass

    def get_order(self, mkpc: MarketPrice) -> Order:
        prms_map = {
            Map.pair: Pair("BTC", "USDT"),
            Map.move: Order.MOVE_BUY,
            Map.market: Price(round(random() * 1000, 2), "USDT"),
        }
        odr = BinanceOrder(Order.TYPE_MARKET, prms_map)
        return odr
