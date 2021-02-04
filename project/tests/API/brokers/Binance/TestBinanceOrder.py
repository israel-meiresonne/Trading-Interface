import unittest

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestBinanceOrder(unittest.TestCase, BinanceOrder):
    def setUp(self) -> None:
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.prc1 = Price(250, self.rsbl)
        self.prc2 = Price(10, self.lsbl)
        self.mkt_prms1 = {
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.market: self.prc1,
        }
        self.mkt_prms1_extracted = {
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
            Map.quoteOrderQty: self.prc1.get_value()
        }
        self.mkt_prms2 = {
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.market: self.prc2,
        }
        self.mkt_prms2_extracted = {
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
            Map.quantity: self.prc2.get_value()
        }

    def test_constructor_market(self):
        BinanceOrder(BinanceOrder.TYPE_MARKET, self.mkt_prms1)

    def test_extract_market_params(self):
        exp1 = self.mkt_prms1_extracted
        result1 = self._extract_market_params(self.mkt_prms1)
        self.assertDictEqual(exp1, result1)

        self.setUp()
        self.mkt_prms1_extracted[Map.side] = BinanceAPI.SIDE_SELL
        exp3 = self.mkt_prms1_extracted
        self.mkt_prms1[Map.move] = self.MOVE_SELL
        result3 = self._extract_market_params(self.mkt_prms1)
        self.assertDictEqual(exp3, result3)

        self.setUp()
        exp2 = self.mkt_prms2_extracted
        result2 = self._extract_market_params(self.mkt_prms2)
        self.assertDictEqual(exp2, result2)

        self.setUp()
        self.mkt_prms2_extracted[Map.side] = BinanceAPI.SIDE_SELL
        exp4 = self.mkt_prms2_extracted
        self.mkt_prms2[Map.move] = self.MOVE_SELL
        result4 = self._extract_market_params(self.mkt_prms2)
        self.assertDictEqual(exp4, result4)

    def test_raise_excepion_extract_market_params(self):
        # miss pair
        del self.mkt_prms1[Map.pair]
        with self.assertRaises(ValueError):
            self._extract_market_params(self.mkt_prms1)
        # miss move
        self.setUp()
        del self.mkt_prms1[Map.move]
        with self.assertRaises(ValueError):
            self._extract_market_params(self.mkt_prms1)
        # miss market
        self.setUp()
        del self.mkt_prms1[Map.market]
        with self.assertRaises(ValueError):
            self._extract_market_params(self.mkt_prms1)

    def test_exract_market_request(self):
        exp1 = BinanceAPI.RQ_ORDER_MARKET_amount
        result1 = self._exract_market_request(self.mkt_prms1_extracted)
        self.assertEqual(exp1, result1)

        exp2 = BinanceAPI.RQ_ORDER_MARKET_qty
        result2 = self._exract_market_request(self.mkt_prms2_extracted)
        self.assertEqual(exp2, result2)

    def test_raise_exception__exract_market_request(self):
        # quantity and quoteOrderQty both set
        self.mkt_prms1_extracted[Map.quantity] = self.prc2.get_value()
        with self.assertRaises(ValueError):
            self._exract_market_request(self.mkt_prms1_extracted)
        # quantity and quoteOrderQty not set
        self.setUp()
        del self.mkt_prms1_extracted[Map.quoteOrderQty]
        with self.assertRaises(ValueError):
            self._exract_market_request(self.mkt_prms1_extracted)


if __name__ == '__main__':
    unittest.main
