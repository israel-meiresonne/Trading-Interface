import unittest

from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestOrder(unittest.TestCase, Order):
    def setUp(self) -> None:
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.exec_prc0 = Price(15000, self.rsbl)
        self.exec_prc1 = Price(20000, self.rsbl)
        self.odr0_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(1000, self.rsbl)
        })
        self.odr1_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.quantity: Price(1/15, self.lsbl)
        })
        self.odr0 = BinanceOrder(self.TYPE_MARKET, self.odr0_prms)
        self.odr1 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odrs = Map({
            "0": self.odr0,
            "1": self.odr1
        })

    def _set_market(self) -> None:
        pass

    def _set_limit(self) -> None:
        pass

    def _set_stop(self) -> None:
        pass

    def generate_order(self) -> Map:
        pass

    def generate_cancel_order(self) -> Map:
        pass


if __name__ == '__main__':
    unittest.main