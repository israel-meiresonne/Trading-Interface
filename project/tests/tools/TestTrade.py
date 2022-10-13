import time
import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Trade import Trade


class TestTrade(unittest.TestCase, Trade, Order):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.pair = pair = Pair('BTC/USDT')
        # Buy
        self.buy_amount = buy_amount = Price(100, pair.get_right())
        self.buy_order_params = buy_order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: buy_amount,
            Map.stop: None,
            Map.limit: None
        })
        self.buy_order = buy_order = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, buy_order_params)
        # Sell
        self.sell_quantity = sell_quantity = Price(100, pair.get_left())
        self.sell_order_params = sell_order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: sell_quantity,
            Map.stop: None,
            Map.limit: None
        })
        self.sell_order = sell_order = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, sell_order_params)

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None

    def broker_switch(self, on: bool = False, stage: str = Config.STAGE_1) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, stage)
            self.BROKER = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.INIT_STAGE
            self.BROKER.close() if self.BROKER is not None else None
            Config.update(Config.STAGE_MODE, init_stage) if init_stage is not None else None
        return self.BROKER

    def _set_market(self) -> None:
        pass

    def _set_limit(self) -> None:
        pass

    def _set_stop_loss(self) -> None:
        pass

    def _set_stop_limit(self) -> None:
        pass

    def generate_order(self) -> Map:
        pass

    def generate_cancel_order(self) -> Map:
        pass

    def test_set_buy_sell_order(self) -> None:
        buy_order = self.buy_order
        sell_order = self.sell_order
        # Set buy Order
        trade = Trade(buy_order)
        exp1 = buy_order
        result1 = trade.get_buy_order()
        self.assertEqual(id(exp1), id(result1))
        self.assertEqual(exp1.get_id(), result1.get_id())
        # Wrong move
        with self.assertRaises(ValueError):
            Trade(sell_order)
        # Set sell Order
        trade.set_sell_order(sell_order)
        exp2 = sell_order
        result2 = trade.get_sell_order()
        self.assertEqual(id(exp2), id(result2))
        self.assertEqual(exp2.get_id(), result2.get_id())
        # Buy order must be set
        """
        self.setUp()
        buy_order2 = self.buy_order
        sell_order2 = self.sell_order
        trade2 = Trade(buy_order2)
        trade2.__buy_order = None
        with self.assertRaises(Exception):
            trade2.set_sell_order(sell_order2)
        """
        # Wrong Pair
        buy_order3 = self.buy_order
        pair = Pair('DOGE/USDT')
        trade3 = Trade(buy_order3)
        sell_order_params = self.sell_order_params
        sell_order_params.put(pair, Map.pair)
        sell_order_params.put(Price(100, pair.get_left()), Map.quantity)
        sell_order3 = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, sell_order_params)
        with self.assertRaises(ValueError):
            trade3.set_sell_order(sell_order3)
        # Wrong move
        trade4 = Trade(buy_order3)
        with self.assertRaises(ValueError):
            trade4.set_sell_order(buy_order)

    def test_is_executed(self) -> None:
        buy_order = self.buy_order
        sell_order = self.sell_order
        trade = Trade(buy_order)
        # Not excuted
        self.assertFalse(trade.is_executed(Map.buy))
        self.assertFalse(trade.is_executed(Map.sell))
        # Not excuted and sell Order is set
        trade.set_sell_order(sell_order)
        self.assertFalse(trade.is_executed(Map.buy))
        self.assertFalse(trade.is_executed(Map.sell))
        # Buy Order is executed
        buy_order._set_status(Order.STATUS_COMPLETED)
        self.assertTrue(trade.is_executed(Map.buy))
        self.assertFalse(trade.is_executed(Map.sell))
        # Buy and Sell Order are executed
        sell_order._set_status(Order.STATUS_COMPLETED)
        self.assertTrue(trade.is_executed(Map.buy))
        self.assertTrue(trade.is_executed(Map.sell))

    def test_is_closed_and_has_position(self) -> None:
        buy_order = self.buy_order
        sell_order = self.sell_order
        trade = Trade(buy_order)
        # Buy Order set but not executed
        self.assertFalse(trade.is_closed())
        self.assertFalse(trade.has_position())
        # Buy Order is executed
        buy_order._set_status(Order.STATUS_COMPLETED)
        self.assertFalse(trade.is_closed())
        self.assertTrue(trade.has_position())
        # Sell Order is set but not executed
        trade.set_sell_order(sell_order)
        self.assertFalse(trade.is_closed())
        self.assertTrue(trade.has_position())
        # Sell Order is executed
        sell_order._set_status(Order.STATUS_COMPLETED)
        self.assertTrue(trade.is_closed())
        self.assertFalse(trade.has_position())

    def test_extrem_prices(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        buy_order = self.buy_order
        sell_order = self.sell_order
        period_1min = broker.PERIOD_1MIN
        trade = Trade(buy_order)
        # No position
        min_price, max_price = trade.extrem_prices(broker).get_map().values()
        self.assertTrue(_MF.is_nan(min_price))
        self.assertTrue(_MF.is_nan(trade.get_min_price()))
        self.assertTrue(_MF.is_nan(max_price))
        self.assertTrue(_MF.is_nan(trade.get_max_price()))
        with self.assertRaises(Exception):
            trade._set_min_price(-1)
        with self.assertRaises(Exception):
            trade._set_max_price(-1)
        # Holds position
        buy_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 5*period_1min*1000)
        buy_order._set_status(Order.STATUS_COMPLETED)
        min_price2, max_price2 = trade.extrem_prices(broker).get_map().values()
        self.assertTrue(min_price2 > 0)
        self.assertTrue(_MF.is_nan(trade.get_min_price()))
        self.assertTrue(max_price2 > 0)
        self.assertTrue(_MF.is_nan(trade.get_max_price()))
        with self.assertRaises(Exception):
            trade._set_min_price(-1)
        with self.assertRaises(Exception):
            trade._set_max_price(-1)
        # Closed position
        time.sleep(10)
        trade.set_sell_order(sell_order)
        sell_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 2*period_1min*1000)
        sell_order._set_status(Order.STATUS_COMPLETED)
        min_price3, max_price3 = trade.extrem_prices(broker).get_map().values()
        self.assertTrue(min_price3 > 0)
        self.assertEqual(min_price3, trade.get_min_price())
        self.assertTrue(max_price3 > 0)
        self.assertEqual(max_price3, trade.get_max_price())
        # Same values
        unix_time = _MF.get_timestamp()
        sleep_time = _MF.round_time(unix_time, period_1min) + period_1min - unix_time
        print(_MF.prefix() + f"test_extrem_prices: sleep for '{sleep_time}'sec.")
        time.sleep(sleep_time)
        min_price4, max_price4 = trade.extrem_prices(broker).get_map().values()
        self.assertEqual(min_price4, trade.get_min_price())
        self.assertEqual(max_price4, trade.get_max_price())
        # End
        self.broker_switch(on=False)

    def test__extrem_prices(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        pair = self.pair
        # Normal
        buy_time = _MF.date_to_unix('2022-09-14 02:31:30')
        sell_time = _MF.date_to_unix('2022-09-14 02:42:15')
        min_price, max_price = Trade._extrem_prices(broker, pair, buy_time, sell_time)
        max_exp1 = 20473.74
        min_exp1 = 20368.97
        self.assertEqual(max_exp1, max_price)
        self.assertEqual(min_exp1, min_price)
        # Buy and sell time are in the same minute
        buy_time2 = buy_time
        sell_time2 = buy_time2 + 10 # add 10sec.
        min_price2, max_price2 = Trade._extrem_prices(broker, pair, buy_time2, sell_time2)
        self.assertTrue(_MF.is_nan(min_price2))
        self.assertTrue(_MF.is_nan(max_price2))
        # Sell time candle is not closed
        sell_time3 = _MF.get_timestamp()
        buy_time3 = sell_time3 - broker.PERIOD_1MIN*2
        min_price3, max_price3 = Trade._extrem_prices(broker, pair, buy_time3, sell_time3)
        marketprice = MarketPrice.marketprice(broker, pair, period=broker.PERIOD_1MIN, n_period=5, starttime=buy_time3)
        self.assertTrue(min_price3 in marketprice.get_lows())
        self.assertTrue(max_price3 in marketprice.get_highs())
        # End
        self.broker_switch(on=False)

    def test_json_encode_decode(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        buy_order = self.buy_order
        sell_order = self.sell_order
        period_1min = broker.PERIOD_1MIN
        trade = Trade(buy_order)
        buy_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 5*period_1min*1000)
        buy_order._set_status(Order.STATUS_COMPLETED)
        trade.set_sell_order(sell_order)
        sell_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 2*period_1min*1000)
        sell_order._set_status(Order.STATUS_COMPLETED)
        min_price3, max_price3 = trade.extrem_prices(broker).get_map().values()
        original_obj = trade
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)
        # End
        self.broker_switch(on=False)

