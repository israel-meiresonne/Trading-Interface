import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.strategies.MinMax.MinMax import MinMax
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestMinMax(unittest.TestCase, MinMax, Order):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.rsbl = "USDT"
        self.lsbl = "BTC"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.max_cap = Price(2025, self.rsbl)
        self.capital1 = Price(1000, self.rsbl)
        self.rate1 = 0.90
        # Strategy
        self.stg_params = Map({
            Map.pair: self.pr,
            Map.maximum: None,
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
        self.real_capital1 = self.capital1.get_value() * self.rate1
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
        self.bnc_mkt_u_u = BinanceMarketPrice(self.bnc_list_u_u, "1m", self.pr)
        # test_get_peak_since_buy
        cap = 1000
        prc = Price(cap, self.rsbl)
        vals = [9, 5, 6, 12, 3, 10, 4, 2, 0, 7]
        times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9.5]
        times = [t * 60 for t in times]
        self.mkt_list = [
            [times[0], 'O', '0', '0', vals[0]],
            [times[1], 'O', '0', '0', vals[1]],
            [times[2], 'O', '0', '0', vals[2]],
            [times[3], 'O', '0', '0', vals[3]],
            [times[4], 'O', '0', '0', vals[4]],
            [times[5], 'O', '0', '0', vals[5]],
            [times[6], 'O', '0', '0', vals[6]],
            [times[7], 'O', '0', '0', vals[7]],
            [times[8], 'O', '0', '0', vals[8]],
            [times[9], 'O', '0', '0', vals[9]]
        ]
        self.stg1 = MinMax(Map({
            Map.pair: self.pr,
            Map.maximum: None,
            Map.capital: prc,
            Map.rate: 0.9
        }))
        self.mkt = BinanceMarketPrice(list(self.mkt_list), '1m', self.pr)
        self.odr2 = BinanceOrder(Order.TYPE_MARKET, Map({
            Map.pair: self.pr,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(cap, self.rsbl)
        }))
        self.stg1._add_order(self.odr2)
        self.odr2._set_status(Order.STATUS_SUBMITTED)

    def _set_market(self) -> None:
        pass

    def _set_limit(self) -> None:
        pass

    def _set_stop(self) -> None:
        pass

    def _set_stop_limit(self) -> None:
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
        _max_dr = -0.005
        self.stg._set_configs(Map({
            self._CONF_MAX_DR: _max_dr
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
        raise Exception("Must implement this test")

    def test_try_sell(self):
        raise Exception("Must implement this test")

    def test_get_performance(self) -> None:
        """
        path = Config.get(Config.DIR_HISTORIC_BNB)
        csv = FileManager.get_csv(path)
        market_list = [[row[Map.time], row[Map.open], row[Map.high], row[Map.low], row[Map.close]] for row in csv]
        bnc_market = BinanceMarketPrice(market_list, "1m", Pair('BNB/USDT'))
        """
        _old_path = Config.get(Config.DIR_MARKET_HISTORICS)
        path = Config.get(Config.DIR_HISTORIC_BNB)
        Config.update(Config.DIR_MARKET_HISTORICS, path)
        bnc = Binance(Map({
            Map.api_pb: 'my_public',
            Map.api_sk: 'my_sk',
            Map.test_mode: True
        }))
        bnc_rq = BinanceRequest(BinanceRequest.RQ_MARKET_PRICE, Map({
            Map.pair: Pair('BNB/USDT'),
            Map.period: 60,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 999
        }))
        bnc.request(bnc_rq)
        bnc_market = bnc_rq.get_market_price()
        super_trends = list(bnc_market.get_super_trend())
        super_trends.reverse()
        closes = list(bnc_market.get_closes())
        closes.reverse()
        perfs = MinMax.get_performance(bnc, MinMax.__name__, bnc_market)
        # ROI
        exp1 = round(0.00786293204696, 4)
        result1 = round(perfs.get(Map.roi), 4)
        self.assertEqual(exp1, result1)
        Config.update(Config.DIR_MARKET_HISTORICS, _old_path)


if __name__ == '__main__':
    unittest.main
