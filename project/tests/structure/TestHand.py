import time
import unittest
from typing import Tuple

import pandas as pd

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Hand import Hand
from model.tools.Asset import Asset
from model.tools.FileManager import FileManager
from model.tools.HandTrade import HandTrade
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Orders import Orders
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction


class TestHand(unittest.TestCase, Hand):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        Hand._MAX_POSITION = 5
        self.pair1 = pair1 = Pair('BTC/USDT')
        # Hand
        self.capital = capital = Price(1000, pair1.get_right())
        self.hand = hand = Hand(capital, Binance)
        # HandTrade1
        self.buy_amount1 = buy_amount1 = Price(100, pair1.get_right())
        self.buy_order1, self.buy_order_params1 = self.new_buy_order(pair1, buy_amount1)
        buy_order1 = self.buy_order1
        self.hand_trade1 = HandTrade(buy_order1, hand.condition_true, hand.condition_true)
        # HandTrade2
        self.pair2 = pair2 = Pair(Asset('DOGE'), pair1.get_right())
        self.buy_amount2 = buy_amount2 = Price(100, pair2.get_right())
        self.buy_order2, self.buy_order_params2 = self.new_buy_order(pair2, buy_amount2)
        buy_order2 = self.buy_order2
        self.hand_trade2 = HandTrade(buy_order2, hand.condition_true, hand.condition_true)

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

    def buy_function(self) -> bool:
        return True

    def sell_function(self) -> bool:
        return True

    def new_buy_order(self, pair: Pair, buy_amount: Price) -> Tuple[Order, Map]:
        buy_order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: buy_amount,
            Map.stop: None,
            Map.limit: None
        })
        buy_order = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, buy_order_params)
        return buy_order, buy_order_params

    def new_sell_order(self, pair: Pair, sell_quantity: Price) -> Tuple[Order, Map]:
        sell_order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: sell_quantity,
            Map.stop: None,
            Map.limit: None
        })
        sell_order = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, sell_order_params)
        return sell_order, sell_order_params

    def execute_order(self, order: Order) -> None:
        move = order.get_move()
        exec_coef = 10 if (move == Order.MOVE_BUY) else 3
        unix_time = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        back_time = exec_coef*Broker.PERIOD_1MIN*1000
        order._set_execution_time(unix_time - back_time)
        order._set_status(Order.STATUS_COMPLETED)

    def test_set_broker_class(self) -> None:
        # Not callable
        with self.assertRaises(ValueError):
            Hand(self.capital, 'not_callable')

    def test_is_set_get_reset_broker(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        hand = self.hand
        # Get
        # ••• Not set
        with self.assertRaises(Exception):
            hand.get_broker()
        self.assertFalse(hand.is_broker_set())
        # ••• Set
        hand.set_broker(broker)
        exp2 = broker
        result2 = hand.get_broker()
        self.assertEqual(exp2, result2)
        self.assertTrue(hand.is_broker_set())
        # ••• Reset
        hand.reset_broker()
        with self.assertRaises(Exception):
            hand.get_broker()
        self.assertFalse(hand.is_broker_set())
        # broker is wrong type
        with self.assertRaises(TypeError):
            hand.set_broker('no_broker')
        # End
        self.broker_switch(on=False)

    def test_set_max_position(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        hand = self.hand
        hand.set_broker(broker)
        pair1 = self.pair1
        pair2 = self.pair2
        pair3 = Pair('ETH/USDT')
        hand.set_broker(broker)
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2, pair3]]
        broker.add_streams(streams)
        # Success
        exp1 = 3
        hand.set_max_position(exp1)
        result1 = hand.get_max_position()
        self.assertEqual(exp1, result1)
        # Max is float
        with self.assertRaises(TypeError):
            hand.set_max_position(4.5)
        # New max is bellow the number of position holds
        hand.buy(pair1, Order.TYPE_MARKET)
        hand.buy(pair2, Order.TYPE_MARKET)
        with self.assertRaises(ValueError):
            hand.set_max_position(1)
        # Don't remain empty position
        hand.buy(pair3, Order.TYPE_MARKET)
        with self.assertRaises(Exception):
            hand.set_max_position(10)
        # End
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def test_is_max_position_reached(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        hand = self.hand
        hand.set_broker(broker)
        hand.set_max_position(2)
        pair1 = self.pair1
        pair2 = self.pair2
        hand.set_broker(broker)
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2]]
        broker.add_streams(streams)
        # Still free position
        self.assertFalse(hand.is_max_position_reached())
        # Positions are fulled
        hand.buy(pair1, Order.TYPE_MARKET)
        hand.buy(pair2, Order.TYPE_MARKET)
        self.assertTrue(hand.is_max_position_reached())
        # End
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def test_get_add_remove_positions(self) -> None:
        hand = self.hand
        hand_trade1 = self.hand_trade1
        hand_trade2 = self.hand_trade2
        # dict is empty
        exp1 = {}
        result1 = hand.get_positions()
        self.assertDictEqual(exp1, result1)
        self.assertEqual(0, len(result1))
        # Add position
        hand._add_position(hand_trade1)
        hand._add_position(hand_trade2)
        with self.assertRaises(ValueError):
            hand._add_position(self.hand_trade2)
        # Get position
        exp3 = hand_trade1
        result3 = hand.get_position(hand_trade1.get_buy_order().get_pair())
        self.assertEqual(exp3, result3)
        with self.assertRaises(ValueError):
            hand.get_position(Pair('wrong/pair'))
        # Remove position
        hand._remove_position(hand_trade1.get_buy_order().get_pair())
        exp4 = {hand_trade2.get_buy_order().get_pair().__str__(): hand_trade2}
        result4 = hand.get_positions()
        self.assertDictEqual(exp4, result4)
        with self.assertRaises(ValueError):
            hand._remove_position(hand_trade1.get_buy_order().get_pair())

    def test_get_add_mark_propositions(self) -> None:
        hand = self.hand
        pair1 = Pair('ETH/USDT')
        pair2 = Pair('BNB/USDT')
        # Get positions
        new_positions = hand.get_propositions()
        self.assertIsInstance(new_positions, pd.DataFrame)
        # Add position
        # ••• Pair don't exist in
        hand._add_proposition(pair1)
        hand._add_proposition(pair2)
        exp1 = [pair1.__str__(), pair2.__str__()]
        result1 = list(hand.get_propositions()[Map.pair])
        self.assertListEqual(exp1, result1)
        # ••• Pair exist in
        hand._add_proposition(pair1)
        hand._add_proposition(pair2)
        exp1_2 = exp1
        result1_2 = list(hand.get_propositions()[Map.pair])
        self.assertListEqual(exp1_2, result1_2)
        # ••• Existing columns of Pair are complet
        hand._mark_proposition(pair1, True)
        hand._mark_proposition(pair2, False)
        hand._add_proposition(pair1)
        hand._add_proposition(pair2)
        exp1_3 = [*exp1, *exp1]
        result1_3 = list(hand.get_propositions()[Map.pair])
        self.assertListEqual(exp1_3, result1_3)
        # Mark new position
        exp3 = [True, False, None, None]
        result3 = list(hand.get_propositions()[Map.buy])
        self.assertListEqual(exp3, result3)
        # ••• Mark last added
        hand._mark_proposition(pair2, True)
        exp3_2 = [True, False, None, True]
        result3_2 = list(hand.get_propositions()[Map.buy])
        self.assertListEqual(exp3_2, result3_2)

    def test_get_add_move_closed_positions(self) -> None:
        hand = self.hand
        hand_trade1 = self.hand_trade1
        pair1 = self.pair1
        hand_trade2 = self.hand_trade2
        pair2 = self.pair2
        # Get closed positions
        exp1 = []
        result1 = hand.get_closed_positions()
        self.assertListEqual(exp1, result1)
        # Raise error
        with self.assertRaises(ValueError):
            hand._move_closed_position(pair1)
        # Move closed position
        # ••• Prepare
        hand._add_position(hand_trade1)
        hand._add_position(hand_trade2)
        hand_trade1.get_buy_order()._set_status(Order.STATUS_COMPLETED)
        sell_order1, sell_order_params = self.new_sell_order(pair1, Price(10, pair1.get_left()))
        hand_trade1.set_sell_order(sell_order1)
        hand_trade1.get_sell_order()._set_status(Order.STATUS_COMPLETED)
        # ••• Test
        hand._move_closed_position(pair1)
        exp2 = {pair2.__str__(): hand_trade2}
        result2 = hand.get_positions()
        self.assertEqual(exp2, result2)
        exp2_2 = [hand_trade1]
        result2_2 = hand.get_closed_positions()
        self.assertEqual(exp2_2, result2_2)

    def test_get_orders_map(self) -> None:
        hand = self.hand
        hand_trade1 = self.hand_trade1
        pair1 = self.pair1
        hand_trade2 = self.hand_trade2
        pair2 = self.pair2
        # No position
        exp1 = Map()
        result1 = hand._get_orders_map()
        result1_2 = hand._get_orders_ref_id()
        self.assertEqual(exp1, result1)
        self.assertIsInstance(result1_2, str)
        # New position added
        # ••• buy Order only
        hand._add_position(hand_trade1)
        orders2 = Orders()
        orders2.add_order(hand_trade1.get_buy_order())
        exp2 = Map({
            pair1.__str__(): orders2
            })
        result2 = hand._get_orders_map()
        not_exp2_1 = result1_2
        result2_1 = hand._get_orders_ref_id()
        self.assertEqual(exp2, result2)
        self.assertIsInstance(result2_1, str)
        self.assertNotEqual(not_exp2_1, result2_1)
        # ••• Same result
        exp2_2 = exp2
        result2_2 = hand._get_orders_map()
        exp2_2_1 = result2_1
        result2_2_1 = hand._get_orders_ref_id()
        self.assertEqual(exp2_2, result2_2)
        self.assertIsInstance(result2_2_1, str)
        self.assertEqual(exp2_2_1, result2_2_1)
        # ••• Sell Order
        sell_order2_3, sell_order_param2_3 = self.new_sell_order(pair1, Price(10, pair1.get_left()))
        hand_trade1.set_sell_order(sell_order2_3)
        hand._add_position(hand_trade2)
        buy_orders2_3 = Orders()
        buy_orders2_3.add_order(hand_trade1.get_buy_order())
        buy_orders2_3.add_order(hand_trade1.get_sell_order())
        sell_orders2_3 = Orders()
        sell_orders2_3.add_order(hand_trade2.get_buy_order())
        exp2_3 = Map({
            pair1.__str__(): buy_orders2_3,
            pair2.__str__(): sell_orders2_3
            })
        result2_3 = hand._get_orders_map()
        not_exp2_3_1 = result2_1
        result2_3_1 = hand._get_orders_ref_id()
        self.assertEqual(exp2_3, result2_3)
        self.assertIsInstance(result2_3_1, str)
        self.assertNotEqual(not_exp2_3_1, result2_3_1)
        # ••• Same result
        exp2_4 = exp2_3
        result2_4 = hand._get_orders_map()
        exp2_4_1 = result2_3_1
        result2_4_1 = hand._get_orders_ref_id()
        self.assertEqual(exp2_4, result2_4)
        self.assertIsInstance(result2_4_1, str)
        self.assertEqual(exp2_4_1, result2_4_1)

    def test_position_capital(self) -> None:
        capital = self.capital
        hand = self.hand
        max_position = hand.get_max_position()
        r_asset = capital.get_asset()
        hand_trade1 = self.hand_trade1
        buy_order1 = hand_trade1.get_buy_order()
        pair1 = buy_order1.get_pair()
        l_asset1 = pair1.get_left()
        transaction1 = Transaction(Transaction.TYPE_BUY, pair1, buy_order1.get_amount(), Price(10, l_asset1), Price(1, r_asset))
        # No position
        exp1 = Price(capital/max_position, r_asset)
        result1 = hand._position_capital()
        self.assertEqual(exp1, result1)
        # Hols position
        hand._add_position(hand_trade1)
        # ••• Buy Order not executed yet
        exp2 = exp1
        result2 = hand._position_capital()
        self.assertEqual(exp2, result2)
        # ••• Buy Order executed
        self.execute_order(buy_order1)
        hand.get_wallet().buy(transaction1)
        n_active_position = 1
        exp2_2 = Price((capital - transaction1.get_right())/(max_position - n_active_position), r_asset)
        result2_2 = hand._position_capital()
        self.assertEqual(exp2_2, result2_2)

    def test_update_orders(self) -> None:
        pass

    def test_update_stalk_file(self) -> None:
        pass

    def debug_manage_positions(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        pair1 = self.pair1
        pair2 = self.pair2
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2]]
        broker.add_streams(streams)
        # No position
        hand = self.hand
        hand.set_broker(broker)
        hand.set_position_on(True)
        sleep_time = 1.5*self._SLEEP_POSITION
        print(_MF.prefix() + f"test_manage_positions sleep for '{sleep_time}'sec.")
        time.sleep(sleep_time)
        # With position
        hand.buy(pair1, Order.TYPE_MARKET)
        hand.buy(pair2, Order.TYPE_MARKET)
        sleep_time = 3.5*self._SLEEP_POSITION
        print(_MF.prefix() + f"test_manage_positions sleep for '{sleep_time}'sec.")
        time.sleep(sleep_time)
        # Sell Position 1
        hand.sell(pair1, Order.TYPE_MARKET)
        sleep_time = 3.5*self._SLEEP_POSITION
        print(_MF.prefix() + f"test_manage_positions sleep for '{sleep_time}'sec.")
        # Sell Position 2
        hand.sell(pair2, Order.TYPE_MARKET)
        sleep_time = 3.5*self._SLEEP_POSITION
        print(_MF.prefix() + f"test_manage_positions sleep for '{sleep_time}'sec.")
        time.sleep(sleep_time)
        hand.set_position_on(False)
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def _stalk_condition_test(self, pair: Pair, marketprices: Map) -> Tuple[bool, dict]:
        return True, {Map.date: _MF.unix_to_date(_MF.get_timestamp()), Map.id: self.hand.get_id()}

    def debug_stalk_market(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        hand = self.hand
        hand._get_stalk_functions().append(self._stalk_condition_test)
        hand.set_broker(broker)
        hand.add_streams()
        hand.set_stalk_on(True)
        _MF.console(**vars())
        hand.set_stalk_on(False)
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def debug_analyse_market(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        hand = self.hand
        hand.set_broker(broker)
        hand.add_streams()
        hand._analyse_market(Map())
        _MF.console(**vars())
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def test_buy_sell_cancel(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        hand = self.hand
        capital = self.capital
        pair1 = self.pair1
        pair2 = self.pair2
        r_asset = pair1.get_right()
        hand.set_broker(broker)
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2]]
        broker.add_streams(streams)
        # Buy position
        position_capital1 = hand._position_capital()
        hand.buy(pair1, Order.TYPE_MARKET)
        exp1 = capital - position_capital1
        result1 = hand.get_wallet().buy_capital()
        self.assertIsInstance(hand.get_position(pair1), HandTrade)
        self.assertEqual(round(exp1.get_value(), 0), round(result1.get_value(), 0))
        self.assertTrue(hand.get_position(pair1).has_position())
        # Sell position
        # ••• Holds position to sell
        hand.sell(pair1, Order.TYPE_MARKET)
        exp2 = capital
        result2 = hand.get_wallet().buy_capital()
        self.assertIsInstance(hand.get_position(pair1), HandTrade)
        self.assertEqual(round(exp2.get_value(), 0), round(result2.get_value(), 0))
        self.assertTrue(hand.get_position(pair1).is_closed())
        # ••• Don't holds position to sell
        hand._move_closed_position(pair1)
        with self.assertRaises(Exception):
            hand.sell(pair1, Order.TYPE_MARKET)
        # ••• The sell Order is already set
        hand.buy(pair1, Order.TYPE_MARKET)
        hand.sell(pair1, Order.TYPE_STOP_LIMIT, stop=Price(10, r_asset), limit=Price(2, r_asset))
        with self.assertRaises(Exception):
            hand.sell(pair1, Order.TYPE_MARKET)
        # Cancel
        self.setUp()
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        hand = self.hand
        hand.set_broker(broker)
        # ••• Cancel Buy
        hand.buy(pair1, Order.TYPE_LIMIT, limit=Price(2, r_asset))
        result3 = hand.get_position(pair1)
        hand.cancel(pair1)
        with self.assertRaises(ValueError):
            hand.get_position(pair1)
        self.assertEqual(Order.STATUS_CANCELED, result3.get_buy_order().get_status())
        # ••• Cancel Sell
        hand.buy(pair2, Order.TYPE_MARKET)
        hand.sell(pair2, Order.TYPE_STOP_LIMIT, stop=Price(10, r_asset), limit=Price(2, r_asset))
        result3_2 = hand.get_position(pair2)
        sell_order3_2 = result3_2.get_sell_order()
        hand.cancel(pair2)
        self.assertIsNone(result3_2.get_sell_order())
        self.assertEqual(Order.STATUS_CANCELED, sell_order3_2.get_status())
        self.assertTrue(result3_2.has_position())
        # Wrong pair
        wrong_pair = Pair(pair1.get_left(), 'wrong_right')
        with self.assertRaises(ValueError):
            hand.buy(wrong_pair, Order.TYPE_MARKET)
        # End
        self.broker_switch(on=False)

    def test_try_submit(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        hand = self.hand
        capital = self.capital
        buy_amount1 = self.buy_amount1
        hand.set_broker(broker)
        hand_trade1 = self.hand_trade1
        pair1 = self.pair1
        hand_trade2 = self.hand_trade2
        pair2 = self.pair2
        sell_order2, _ = self.new_sell_order(pair2, Price(10, pair2.get_left()))
        hand_trade2.set_sell_order(sell_order2)
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2]]
        broker.add_streams(streams)
        # Not sell Order
        hand._try_submit(hand_trade1)
        exp1 = capital - buy_amount1
        resul1 = hand.get_wallet().buy_capital()
        self.assertTrue(hand_trade1.has_position())
        self.assertEqual(round(exp1.get_value(), 0), round(resul1.get_value(), 0))
        # Has sell Order
        hand._try_submit(hand_trade2)
        self.assertTrue(hand_trade2.is_executed(Map.buy))
        self.assertTrue(hand_trade2.is_executed(Map.sell))
        # End
        self.broker_switch(on=False)

    def test_backup_load(self) -> None:
        hand = self.hand
        hand.backup()
        _MF.wait_while(FileManager.is_writting,  False, 10, to_raise=Exception("Time out to wait end of writting"))
        # Backup exist
        hand_id = hand.get_id()
        loaded = hand.load(hand_id)
        self.assertEqual(hand._get_backup(), loaded.json_encode())
        # Backup don't exist
        with self.assertRaises(Exception):
            self.load('fake_id')

    def test_json_encode_decode(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        hand = self.hand
        hand.set_broker(broker)
        pair1 = self.pair1
        pair2 = self.pair2
        streams = [broker.generate_stream(Map({Map.period: period_1min, Map.pair: pair})) for pair in [pair1, pair2]]
        broker.add_streams(streams)
        hand.buy(pair1, Order.TYPE_MARKET)
        hand.sell(pair1, Order.TYPE_MARKET)
        hand.buy(pair2, Order.TYPE_MARKET)
        hand._get_orders_map()
        pair3 = Pair('BNB/USDT')
        pair4 = Pair('ETH/USDT')
        hand._add_proposition(pair3)
        hand._add_proposition(pair4)
        hand._mark_proposition(pair4, have_bought=True)
        #
        original_obj = hand
        # test_exec = self.get_executable_test_json_encode_decode()
        # exec(test_exec)
        original_obj._set_backup(original_obj.json_encode())
        json_str = original_obj.json_encode()
        decoded_obj = self.json_decode(json_str)
        original_obj.reset_broker()
        original_obj._reset_orders_map()
        original_obj._reset_backup()
        exp1 = original_obj.get_propositions().to_dict('records')
        result1 = decoded_obj.get_propositions().to_dict('records')
        self.assertListEqual(exp1, result1)
        original_obj._reset_new_positions()
        decoded_obj._reset_new_positions()
        self.assertEqual(original_obj, decoded_obj)
        self.assertNotEqual(id(original_obj), id(decoded_obj))
        # End
        self.broker_switch(on=False)

    def test_get_path_file_backup(self) -> None:
        session_id = Config.get(Config.SESSION_ID)
        start_date = Config.get(Config.START_DATE)
        stage = Config.get(Config.STAGE_MODE)
        fake_id = 'fake_id'
        exp1 = f'content/sessions/running/{session_id}/storage/{stage}/{Hand.__name__}/{fake_id}/{start_date}||{fake_id}||hand_backup.json'
        result1 = Hand.get_path_file_backup(fake_id)
        self.assertEqual(exp1, result1)

    def test_get_path_dir_hands(self) -> None:
        session_id = Config.get(Config.SESSION_ID)
        stage = Config.get(Config.STAGE_MODE)
        exp1 = f'content/sessions/running/{session_id}/storage/{stage}/{Hand.__name__}/'
        result1 = Hand.get_path_dir_hands()
        self.assertEqual(exp1, result1)

    def test_get_path_file_stalk(self) -> None:
        session_id = Config.get(Config.SESSION_ID)
        condition = self._stalk_condition_1
        exp = f'content/sessions/running/{session_id}/datas/active/{session_id}/{session_id}_f_market_stalk-_stalk_condition_1.csv'
        result = self.get_path_file_stalk(condition)
        self.assertEqual(exp, result)

    def test_get_path_file_market_trend(self) -> None:
        session_id = Config.get(Config.SESSION_ID)
        period_str = '1h'
        exp = f'content/sessions/running/{session_id}/view/Hand/analyse/{period_str}/{session_id}_{period_str}_market_trend_view.csv'
        result = self.get_path_file_market_trend(period_str)
        self.assertEqual(exp, result)
