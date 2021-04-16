import unittest

from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.tools.Map import Map
from model.tools.Orders import Orders
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestOrders(unittest.TestCase, Orders):
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
            Map.quantity: Price(1 / 15, self.lsbl)
        })
        self.odr0 = BinanceOrder(self.TYPE_MARKET, self.odr0_prms)
        self.odr1 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odr2 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odrs = Map({
            "0": self.odr0,
            "1": self.odr1
        })
        self.odrs_obj = Orders()

    def test_get_order(self) -> None:
        # Get by Index
        self.odrs_obj.add_order(self.odr0)
        self.odrs_obj.add_order(self.odr1)
        self.odrs_obj.add_order(self.odr2)
        exp1 = id(self.odr2)
        result1 = id(self.odrs_obj.get_order(idx=2))
        self.assertEqual(exp1, result1)
        # Get by ID
        self.setUp()
        self.odrs_obj.add_order(self.odr0)
        self.odrs_obj.add_order(self.odr1)
        self.odrs_obj.add_order(self.odr2)
        id1 = self.odr1.get_id()
        exp2 = id(self.odr1)
        result2 = id(self.odrs_obj.get_order(odr_id=id1))
        self.assertEqual(exp2, result2)
        # Error: both param set
        self.setUp()
        with self.assertRaises(ValueError):
            self.odrs_obj.get_order(idx=0, odr_id=id1)
        # Error: none param set
        with self.assertRaises(ValueError):
            self.odrs_obj.get_order()
        # Error: unknown Index
        self.setUp()
        self.odrs_obj.add_order(self.odr0)
        self.odrs_obj.add_order(self.odr1)
        self.odrs_obj.add_order(self.odr2)
        with self.assertRaises(ValueError):
            self.odrs_obj.get_order(idx=5)
        # Error: unknown ID
        self.setUp()
        self.odrs_obj.add_order(self.odr0)
        self.odrs_obj.add_order(self.odr1)
        self.odrs_obj.add_order(self.odr2)
        with self.assertRaises(ValueError):
            self.odrs_obj.get_order(odr_id='hello')

    def test_sum_orders(self):
        # simple test
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(self.STATUS_COMPLETED)
        self.odr1._set_execution_price(self.exec_prc1)
        self.odr1._set_status(self.STATUS_COMPLETED)
        buy_amount = self.odr0_prms.get(Map.amount).get_value()
        sell_prc = self.exec_prc1.get_value()
        sum_r = (buy_amount / self.exec_prc0.get_value()) * sell_prc - buy_amount
        exp = Map({
            Map.left: Price(0, self.lsbl),
            Map.right: Price(sum_r, self.rsbl)
        })
        result = self._sum_orders(self.odrs)
        self.assertEqual(exp.get(Map.left), result.get(Map.left))
        self.assertEqual(exp.get(Map.right), result.get(Map.right))
        # all orders are not completed
        self.setUp()
        exp = Map({
            Map.left: Price(0, self.lsbl),
            Map.right: Price(0, self.rsbl)
        })
        result = self._sum_orders(self.odrs)
        self.assertEqual(exp.get(Map.left), result.get(Map.left))
        self.assertEqual(exp.get(Map.right), result.get(Map.right))
        # orders contain completed and not completed Order
        self.setUp()
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(self.STATUS_COMPLETED)
        exp = Map({
            Map.left: Price(1 / 15, self.lsbl),
            Map.right: Price(-1000, self.rsbl)
        })
        result = self._sum_orders(self.odrs)
        self.assertEqual(exp.get(Map.left), result.get(Map.left))
        self.assertEqual(exp.get(Map.right), result.get(Map.right))
        # orders is empty
        self.setUp()
        with self.assertRaises(ValueError):
            self._sum_orders(Map())

    def test_sum_orders_multiple_orders(self):
        # set up
        odrs = Orders()
        _max_dr = 0.005
        mkt = [
            420.230011,
            389.593994,
            437.164001,
            438.798004,
            437.747986,
            432.152008
        ]
        odr0_cap = 1000
        odr0 = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(odr0_cap, self.rsbl)
        }))
        odr1_val = mkt[0] * (1 - _max_dr)
        odr1_qty = odr0_cap / mkt[0]
        odr1 = BinanceOrder(self.TYPE_STOP, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: Price(odr1_val, self.rsbl),
            Map.quantity: Price(odr1_qty, self.lsbl)
        }))
        odr2_cap = odr1_val * odr1_qty
        odr2 = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(odr2_cap, self.rsbl)
        }))
        odr3_val = mkt[1] * (1 - _max_dr)
        odr3_qty = odr2_cap / mkt[1]
        odr3 = BinanceOrder(self.TYPE_STOP, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: Price(odr3_val, self.rsbl),
            Map.quantity: Price(odr3_qty, self.lsbl)
        }))
        odr4_cap = odr3_val * odr3_qty
        odr4 = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(odr4_cap, self.rsbl)
        }))
        odr5_val = mkt[2] * (1 - _max_dr)
        odr5_qty = odr4_cap / mkt[2]
        odr5 = BinanceOrder(self.TYPE_STOP, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: Price(odr5_val, self.rsbl),
            Map.quantity: Price(odr5_qty, self.lsbl)
        }))
        odr6_val = mkt[3] * (1 - _max_dr)
        odr6_qty = odr5_qty
        odr6 = BinanceOrder(self.TYPE_STOP, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: Price(odr6_val, self.rsbl),
            Map.quantity: Price(odr6_qty, self.lsbl)
        }))
        odr7_cap = odr6_qty
        odr7 = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.quantity: Price(odr7_cap, self.lsbl)
        }))
        odr8_cap = odr7_cap * mkt[4]
        odr8 = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(odr8_cap, self.rsbl)
        }))
        odr9_val = mkt[5] * (1 - _max_dr)
        odr9_qty = odr8_cap / mkt[5]
        odr9 = BinanceOrder(self.TYPE_STOP, Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: Price(odr9_val, self.rsbl),
            Map.quantity: Price(odr9_qty, self.lsbl)
        }))
        # Process
        odrs.add_order(odr0)
        odrs.add_order(odr1)
        odrs.add_order(odr2)
        odrs.add_order(odr3)
        odrs.add_order(odr4)
        odrs.add_order(odr5)
        odrs.add_order(odr6)
        odrs.add_order(odr7)
        odrs.add_order(odr8)
        odrs.add_order(odr9)
        odr0._set_execution_price(Price(mkt[0], self.rsbl))
        odr0._set_status(self.STATUS_COMPLETED)
        odr1._set_execution_price(odr1.get_stop_price())
        odr1._set_status(self.STATUS_COMPLETED)
        odr2._set_execution_price(Price(mkt[1], self.rsbl))
        odr2._set_status(self.STATUS_COMPLETED)
        odr3._set_execution_price(odr3.get_stop_price())
        odr3._set_status(self.STATUS_COMPLETED)
        odr4._set_execution_price(Price(mkt[2], self.rsbl))
        odr4._set_status(self.STATUS_COMPLETED)
        odr5._set_status(self.STATUS_CANCELED)
        odr6._set_status(self.STATUS_CANCELED)
        odr7._set_execution_price(Price(mkt[4], self.rsbl))
        odr7._set_status(self.STATUS_COMPLETED)
        odr8._set_execution_price(Price(mkt[5], self.rsbl))
        odr8._set_status(self.STATUS_COMPLETED)
        odr9._set_status(self.STATUS_CANCELED)
        print(odrs.get_sum().get(Map.left))
        print(odrs.get_sum().get(Map.right))
        print(odr0_cap + odrs.get_sum().get(Map.right).get_value())

    def test_get_last_execution(self):
        # One Completed
        odrs = Orders()
        odrs.add_order(self.odr0)
        odrs.add_order(self.odr1)
        odrs.add_order(self.odr2)
        self.odr0._set_status(self.STATUS_COMPLETED)
        exp = id(self.odr0)
        result = id(odrs.get_last_execution())
        self.assertEqual(exp, result)
        # Multiple Completed
        self.setUp()
        odrs = Orders()
        odrs.add_order(self.odr0)
        odrs.add_order(self.odr1)
        odrs.add_order(self.odr2)
        self.odr1._set_status(self.STATUS_COMPLETED)
        self.odr2._set_status(self.STATUS_COMPLETED)
        exp = id(self.odr2)
        result = id(odrs.get_last_execution())
        self.assertEqual(exp, result)


if __name__ == '__main__':
    unittest.main
