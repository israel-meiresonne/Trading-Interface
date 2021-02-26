import unittest
from decimal import Decimal

from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.strategies.MinMax.MinMax import MinMax
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestMinMax(unittest.TestCase, MinMax, Order):
    def setUp(self) -> None:
        self.rsbl = "USDT"
        self.lsbl = "BTC"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.max_cap = Price(2025, self.rsbl)
        self.capital1 = Price(1000, self.rsbl)
        self.rate1 = 0.90
        # Strategy
        self.stg_params = Map({
            Map.pair: self.pr,
            Map.capital: self.max_cap,
            Map.rate: self.rate1
        })
        self.stg = MinMax(self.stg_params)
        self.configs = Map({
            self._CONF_MAKET_PRICE: Map({
                Map.pair: self.pr,
                Map.period: 60,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 20
            })
        })
        # Broker
        self.bkr = Binance(Map({
            Map.api_pb: "api_pb",
            Map.api_sk: "api_sk",
            Map.test_mode: True
        }))
        # Orders
        self.real_capital1 = self.capital1.get_value() * Decimal(self.rate1)
        self.exec_prc0 = Price(15000, self.rsbl)
        self.exec_prc1 = Price(30000, self.rsbl)
        self.odr0_prms = Map({
            Map.pair: self.pr,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(self.real_capital1, self.rsbl)
        })
        self.buy_qty = self.real_capital1 / self.exec_prc0.get_value()
        self.odr1_prms = Map({
            Map.pair: self.pr,
            Map.move: Order.MOVE_SELL,
            Map.quantity: Price(self.buy_qty, self.lsbl)
        })
        self.odr0 = BinanceOrder(Order.TYPE_MARKET, self.odr0_prms)
        self.odr1 = BinanceOrder(Order.TYPE_MARKET, self.odr1_prms)
        # MarketPrice
        self.bnc_list_u_u = [
            ['0', '0', '0', '0', 7500],
            ['0', '0', '0', '0', 7500],
            ['0', '0', '0', '0', 7500],
            ['0', '0', '0', '0', 750],
            ['0', '0', '0', '0', 7500],
            ['0', '0', '0', '0', self.exec_prc0.get_value()]
        ]
        self.bnc_mkt_u_u = BinanceMarketPrice(self.bnc_list_u_u, "1m")

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

    def test_get_buy_capital(self):
        # orders is empty
        self.stg._set_capital(self.capital1)
        exp1 = Price(900, self.rsbl)
        result1 = self.stg._get_buy_capital()
        self.assertEqual(exp1, result1)
        # orders not empty
        self.setUp()
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.odr1._set_execution_price(self.exec_prc1)
        self.odr1._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        exp2 = Price(1800, self.rsbl)
        result2 = self.stg._get_buy_capital()
        self.assertEqual(exp2, result2)
        # Just buy without sell
        self.setUp()
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        exp3 = Price(0, self.rsbl)
        result3 = self.stg._get_buy_capital()
        self.assertEqual(exp3, result3)

    def test_get_sell_quantity(self):
        # orders is empty
        self.stg._set_capital(self.capital1)
        exp1 = Price(0, self.lsbl)
        result1 = self.stg._get_sell_quantity()
        self.assertEqual(exp1, result1)
        # orders not empty
        self.setUp()
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.odr1._set_execution_price(self.exec_prc1)
        self.odr1._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        exp2 = Price(0, self.lsbl)
        result2 = self.stg._get_sell_quantity()
        self.assertEqual(exp2, result2)
        # Just buy without sell
        self.setUp()
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        exp3 = Price(0.06, self.lsbl)
        result3 = self.stg._get_sell_quantity()
        self.assertEqual(exp3, result3)

    def test_has_position(self):
        # No Order
        self.assertFalse(self.stg._has_position())
        # Last Order is buy not  completed
        self.setUp()
        self.stg._add_order(self.odr0)
        self.assertFalse(self.stg._has_position())
        # Last Order is buy completed
        self.setUp()
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.assertTrue(self.stg._has_position())
        # Last Order is sell not completed followed by buy completed
        self.setUp()
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        self.assertTrue(self.stg._has_position())
        # Last Order is sell completed followed by buy completed
        self.setUp()
        self.odr1._set_status(Order.STATUS_COMPLETED)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        self.stg._add_order(self.odr1)
        self.assertFalse(self.stg._has_position())

    def test_get_market_price(self):
        self.stg._set_configs(self.configs)
        exp = Binance.__name__ + MarketPrice.__name__
        result = self.stg._get_market_price(self.bkr).__class__.__name__
        self.assertEqual(exp, result)

    def test_new_buy_order(self):
        self.stg._set_capital(self.capital1)
        exp_type = self.bkr.__class__.__name__ + Order.__name__
        exp_move = Order.MOVE_BUY
        exp_amount = Price(900, self.rsbl)
        exp_oder_type = Order.TYPE_MARKET
        odr = self.stg._new_buy_order(self.bkr)
        result_type = odr.__class__.__name__
        result_move = odr.get_move()
        result_amount = odr.get_amount()
        result_oder_type = odr.get_type()
        result_id = id(self.stg._get_orders().get_order(0))
        self.assertEqual(exp_type, result_type)
        self.assertEqual(exp_oder_type, result_oder_type)
        self.assertEqual(exp_move, result_move)
        self.assertEqual(exp_amount, result_amount)
        self.assertEqual(id(odr), result_id)

    def test_new_sell_order(self):
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        exp_type = self.bkr.__class__.__name__ + Order.__name__
        exp_move = Order.MOVE_SELL
        exp_qty = Price(0.06, self.lsbl)
        exp_oder_type = Order.TYPE_MARKET
        odr = self.stg._new_sell_order(self.bkr)
        result_type = odr.__class__.__name__
        result_move = odr.get_move()
        result_qty = odr.get_quantity()
        result_oder_type = odr.get_type()
        result_id = id(self.stg._get_orders().get_order(1))
        self.assertEqual(exp_type, result_type)
        self.assertEqual(exp_oder_type, result_oder_type)
        self.assertEqual(exp_move, result_move)
        self.assertEqual(exp_qty, result_qty)
        self.assertEqual(id(odr), result_id)

    def test_new_secure_order(self):
        _max_dr = Decimal('-0.005')
        self.stg._set_configs(Map({
            self._CONF_MAX_DR: Decimal(_max_dr)
        }))
        self.stg._set_capital(self.capital1)
        self.odr0._set_execution_price(self.exec_prc0)
        self.odr0._set_status(Order.STATUS_COMPLETED)
        self.stg._add_order(self.odr0)
        exp_type = self.bkr.__class__.__name__ + Order.__name__
        exp_move = Order.MOVE_SELL
        exp_qty = Price(0.06, self.lsbl)
        exp_stop = Price(self.exec_prc0.get_value() * (1 + _max_dr), self.rsbl)
        exp_oder_type = Order.TYPE_STOP
        odr = self.stg._new_secure_order(self.bkr, self.bnc_mkt_u_u)
        result_type = odr.__class__.__name__
        result_move = odr.get_move()
        result_qty = odr.get_quantity()
        result_oder_type = odr.get_type()
        result_stop = odr.get_stop_price()
        result_id = id(self.stg._get_orders().get_order(1))
        self.assertEqual(exp_type, result_type)
        self.assertEqual(exp_oder_type, result_oder_type)
        self.assertEqual(exp_stop, result_stop)
        self.assertEqual(exp_move, result_move)
        self.assertEqual(exp_qty, result_qty)
        self.assertEqual(id(odr), result_id)

    def test_try_buy(self):
        self.stg._set_configs(self.configs)
        exp = type(Map())
        result = self.stg._try_buy(self.bkr, self.bnc_mkt_u_u)
        self.assertEqual(exp, type(result))

    def test_try_sell(self):
        self.stg._set_configs(self.configs)
        self.stg._set_secure_order(self.odr1)
        exp = type(Map())
        result = self.stg._try_sell(self.bkr, self.bnc_mkt_u_u)
        self.assertEqual(exp, type(result))


if __name__ == '__main__':
    unittest.main
