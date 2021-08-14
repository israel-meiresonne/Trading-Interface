import unittest

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Orders import Orders
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestOrders(unittest.TestCase, Orders):
    def setUp(self) -> None:
        _initial_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.buy_amount = 100
        self.lsbl = "SNX"
        self.rsbl = "USDT"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.exec_prc0 = Price(20, self.rsbl)
        self.exec_prc1 = Price(20, self.rsbl)
        self.r_fake_fee = Price(Order.FAKE_FEE, self.rsbl)
        self.l_fake_fee = Price(Order.FAKE_FEE / self.exec_prc0, self.lsbl)
        self.odr0_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(self.buy_amount, self.rsbl)
        })
        self.odr1_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.quantity: Price(self.buy_amount / self.exec_prc0, self.lsbl) - self.l_fake_fee
        })
        self.odr0 = BinanceOrder(self.TYPE_MARKET, self.odr0_prms)
        self.odr1 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odr2 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odrs = Map({
            "0": self.odr0,
            "1": self.odr1
        })
        self.odrs_obj = Orders()
        # Config.update(Config.STAGE_MODE, _initial_stage)

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

    def execute_order(self, order: Order, exec_price: Price, fee: Price):
        qty_obj = order.get_quantity()
        amount_obj = order.get_amount()
        exec_qty = None
        exec_amount = None
        if qty_obj is not None:
            exec_qty = qty_obj
            exec_amount = Price(exec_price * qty_obj, order.get_pair().get_right().get_symbol())
        elif amount_obj is not None:
            exec_amount = amount_obj
            exec_qty = Price(exec_amount / exec_price, order.get_pair().get_left().get_symbol())
        order._set_status(self.STATUS_COMPLETED)
        order._set_broker_id(_MF.new_code())
        order._set_execution_time(_MF.get_timestamp(_MF.TIME_MILLISEC))
        order._set_execution_price(exec_price)
        order._set_executed_quantity(exec_qty)
        order._set_executed_amount(exec_amount)
        order._set_fee(fee)

    def test_sum_orders(self):
        # simple test
        self.execute_order(self.odr0, self.exec_prc0, self.r_fake_fee)
        self.execute_order(self.odr1, self.exec_prc1, self.r_fake_fee)
        fees = Price(len(self.odrs.get_map()) * Order.FAKE_FEE, self.odr0.get_pair().get_right().get_symbol())
        buy_amount = self.odr0_prms.get(Map.amount).get_value()
        sell_prc = self.exec_prc1.get_value()
        sum_r = (buy_amount / self.exec_prc0) * sell_prc - buy_amount - fees.get_value()
        exp1 = Map({
            Map.left: Price(0, self.lsbl),
            Map.right: Price(sum_r, self.rsbl),
            Map.fee: fees
        })
        result1 = self._sum_orders(self.odrs)
        self.assertEqual(exp1.get(Map.left), result1.get(Map.left))
        self.assertEqual(exp1.get(Map.right), result1.get(Map.right))
        self.assertEqual(exp1.get(Map.fee), result1.get(Map.fee))
        # all orders are not completed
        self.setUp()
        exp2 = Map({
            Map.left: Price(0, self.lsbl),
            Map.right: Price(0, self.rsbl),
            Map.fee: Price(0, self.rsbl)
        })
        result2 = self._sum_orders(self.odrs)
        self.assertEqual(exp2.get(Map.left), result2.get(Map.left))
        self.assertEqual(exp2.get(Map.right), result2.get(Map.right))
        self.assertEqual(exp2.get(Map.fee), result2.get(Map.fee))
        # orders contain completed and not completed Order
        self.setUp()
        self.execute_order(self.odr0, self.exec_prc0, self.r_fake_fee)
        exp3 = Map({
            Map.left: Price(self.buy_amount / self.exec_prc0, self.lsbl) - self.l_fake_fee,
            Map.right: -Price(self.buy_amount, self.rsbl),
            Map.fee: Price(Order.FAKE_FEE, self.rsbl)
        })
        result3 = self._sum_orders(self.odrs)
        self.assertEqual(exp3.get(Map.left), result3.get(Map.left))
        self.assertEqual(exp3.get(Map.right), result3.get(Map.right))
        self.assertEqual(exp3.get(Map.fee), result3.get(Map.fee))
        # orders is empty
        self.setUp()
        with self.assertRaises(ValueError):
            self._sum_orders(Map())

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

    def test_json_encode_decode(self) -> None:
        original_obj = self.odrs_obj
        original_obj.add_order(self.odr0)
        original_obj.add_order(self.odr1)
        original_obj.add_order(self.odr2)
        self.odr0._set_status(self.STATUS_COMPLETED)
        self.odr1._set_status(self.STATUS_FAILED)
        self.odr2._set_status(self.STATUS_CANCELED)
        original_obj.has_position()
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main
