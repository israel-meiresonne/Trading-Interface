import time
import unittest

import numpy as np
import pandas as pd

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Pair import Pair


class TestBinanceFakeAPI(unittest.TestCase, BinanceFakeAPI):
    def setUp(self) -> None:
        _MF.OUTPUT = True
        BinanceFakeAPI.reset()
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.initial_indexes = Map({
            60: 59999,
            180: 19999,
            300: 11999,
            900: 3999,
            1800: 1999,
            3600: 999
            })
        self.order_params = order_params = Map({
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quoteOrderQty": 78.6,
            "newClientOrderId": "odr_7j1b7ra4h6212041lk66",
            "timestamp": 1640724616332,
            "recvWindow": 6000,
            "signature": "e97202746a7193fbe95e37b38f1f3750eac81eb953077387f2c5a9246dbf0322"
        })

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None
    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
            self.BROKER = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.INIT_STAGE
            self.BROKER.close() if self.BROKER is not None else None
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self.BROKER

    def test_get_file_path_load_orders(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        session_id = Config.get(Config.SESSION_ID)
        exp = f"content/sessions/running/{session_id}/storage/STAGE_1/BinanceFakeAPI/orders/{session_id}_orders.json"
        result = BinanceFakeAPI._get_file_path_load_orders()
        self.assertEqual(exp, result)

    def test_load_market_histories(self) -> None:
        _cls = BinanceFakeAPI
        pair1 = Pair('BTC/USDT')
        merged_pair1 = pair1.format(Pair.FORMAT_MERGED).upper()
        pair2 = Pair('DOGE/USDT')
        merged_pair2 = pair2.format(Pair.FORMAT_MERGED).upper()
        merged_to_period = {
            merged_pair1: [60, 60*3],
            merged_pair2: [60*5, 60*15],
        }
        # Test load
        _cls.load_market_histories(merged_to_period)
        [[self.assertIsInstance(_cls._get_market_history(merged_pair, period), np.ndarray) for period in periods] for merged_pair, periods in merged_to_period.items()]
        # Don't load existing hsitories
        exp2 = id(_cls._get_market_history(merged_pair1, merged_to_period[merged_pair1][0]))
        _cls.load_market_histories(merged_to_period={merged_pair1: [merged_to_period[merged_pair1][0]]})
        result2 = id(_cls._get_market_history(merged_pair1, merged_to_period[merged_pair1][0]))
        self.assertEqual(exp2, result2)
        # Wrong pair
        with self.assertRaises(ValueError):
            _cls.load_market_histories(merged_to_period={'fake_merged': [merged_to_period[merged_pair1][0]]})
        # Wrong period
        with self.assertRaises(ValueError):
            _cls.load_market_histories(merged_to_period={merged_pair1: [23]})

    def test_load_market_history(self) -> None:
        pair = Pair('BTC/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED)
        period = 60*60
        period_milli = int(period * 1000)
        history = BinanceFakeAPI._load_market_history(merged_pair, period)
        self.assertIsInstance(history, np.ndarray)
        # Check interval between open time
        diff_open = np.diff(history[:,0])
        correct_open_diff = diff_open[diff_open == period_milli]
        self.assertTupleEqual(diff_open.shape, correct_open_diff.shape)
        # Check interval between close time
        """
        Can't test close time cause intervals between them aren't the same because of the deffinition of the close time
        definition(close time): time of the last transaction
        This mean that it's normal if the last open time don't match the last second of the period
        """

    def test_set_market_history(self) -> None:
        def test_instance(merged_pair: str, period: int) -> None:
            mkt = _cls._get_market_history(merged_pair, period)
            self.assertIsInstance(mkt, np.ndarray)
            self.assertEqual(id(mkt), id(_cls._get_market_history(merged_pair, period)))

        _cls = BinanceFakeAPI
        pair1 = Pair('BTC/USDT')
        merged_pair1 = pair1.format(Pair.FORMAT_MERGED)
        pair2 = Pair('DOGE/USDT')
        merged_pair2 = pair2.format(Pair.FORMAT_MERGED)
        period1 = 60
        period2 = 60*60
        '''
        # Stage 1
        '''
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        _cls._set_market_history(merged_pair1, period1, update=False)
        _cls._set_market_history(merged_pair2, period1, update=False)
        _cls._set_market_history(merged_pair2, period2, update=False)
        test_instance(merged_pair1, period1)
        test_instance(merged_pair2, period1)
        test_instance(merged_pair2, period2)
        '''
        # Stage 2
        '''
        # —— Test set
        Config.update(Config.STAGE_MODE, Config.STAGE_2)
        broker = self.broker_switch(on=True)
        _cls.reset()
        streams = []
        streams.append(Binance.generate_stream(Map({Map.pair: pair1, Map.period: period1})))
        streams.append(Binance.generate_stream(Map({Map.pair: pair2, Map.period: period1})))
        streams.append(Binance.generate_stream(Map({Map.pair: pair2, Map.period: period2})))
        broker.add_streams(streams)
        _cls._set_market_history(merged_pair1, period1, update=False)
        _cls._set_market_history(merged_pair2, period1, update=False)
        _cls._set_market_history(merged_pair2, period2, update=False)
        test_instance(merged_pair1, period1)
        test_instance(merged_pair2, period1)
        test_instance(merged_pair2, period2)
        # —— Test update
        market1_1 = _cls._get_market_history(merged_pair1, period1)
        _cls._set_market_history(merged_pair2, period2, update=True, market_history=market1_1)
        market2_2 = _cls._get_market_history(merged_pair2, period2)
        self.assertListEqual(market1_1.tolist(), market2_2.tolist())
        '''
        Raise errors
        '''
        # Wrong history type
        with self.assertRaises(TypeError):
            _cls._set_market_history(merged_pair2, period2, update=True, market_history={})
        # Stage 3
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        with self.assertRaises(Exception):
            _cls._set_market_history(merged_pair2, period2, update=False)
        # Can't update
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        with self.assertRaises(ValueError):
            _cls._set_market_history(merged_pair2, period2, update=True, market_history=market1_1)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        with self.assertRaises(ValueError):
            _cls._set_market_history(merged_pair2, period2, update=True, market_history=market1_1)
        self.broker_switch(on=False)

    def test_get_initial_indexes(self) -> None:
        _cls = BinanceFakeAPI
        exp = self.initial_indexes
        result = _cls._get_initial_indexes()
        self.assertEqual(exp, result)

    def test_get_initial_index(self) -> None:
        _cls = BinanceFakeAPI
        indexes = self.initial_indexes
        periods = indexes.get_keys()
        # Stage 1
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        for period, index in indexes.get_map().items():
            result = _cls._get_initial_index(period)
            self.assertIsInstance(result, int)
            self.assertEqual(index, result)
        # Index don't exist
        with self.assertRaises(ValueError):
            _cls._get_initial_index(2330)
        # Stage 2 & 3
        Config.update(Config.STAGE_MODE, Config.STAGE_2)
        with self.assertRaises(Exception):
            _cls._get_initial_index(periods[0])
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        with self.assertRaises(Exception):
            _cls._get_initial_index(periods[0])

    def test_get_orders(self) -> None:
        self.broker_switch(on=True)
        _cls = BinanceFakeAPI
        stages = [Config.STAGE_1, Config.STAGE_2]
        params = self.order_params
        for stages in stages:
            Config.update(Config.STAGE_MODE, stages)
            order = _cls._new_order(params)
            orders = _cls._get_orders()
            _cls._save_orders()
            _cls.reset()
            loaded_orders = _cls._get_orders()
            loaded_order = _cls._get_order(order.get_attribut(Map.symbol), order.get_attribut(Map.orderId))
            self.assertEqual(orders, loaded_orders)
            self.assertEqual(order, loaded_order)
            _cls.reset()
        self.broker_switch(on=False)

    def test_get_order_dict(self) -> None:
        _cls = BinanceFakeAPI
        params = self.order_params
        merged_pair = params.get(Map.symbol)
        self.assertDictEqual({}, _cls._get_order_dict(merged_pair))
        order = _cls._new_order(params)
        exp1 = {order.get_attribut(Map.orderId): order}
        result1 = _cls._get_order_dict(merged_pair)
        self.assertDictEqual(exp1, result1)

    def test_get_order(self) -> None:
        _cls = BinanceFakeAPI
        params = self.order_params
        merged_pair = params.get(Map.symbol)
        with self.assertRaises(ValueError):
            _cls._get_order(merged_pair, 'order_id')

    def test_index(self) -> None:
        _cls = BinanceFakeAPI
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        tests = pd.read_csv(FileManager.get_project_directory() + 'tests/datas/API/brokers/Binance/BinanceFakeAPI/test_index.csv')
        cols = tests.columns
        for i in range(tests.shape[0]):
            Bot.update_trade_index(i)
            for period in cols:
                if isinstance(period, int):
                    exp = tests.loc[i,period]
                    result = _cls._index(period)
                    self.assertEqual(exp, result)
        Config.update(Config.STAGE_MODE, Config.STAGE_2)
        self.assertEqual(-1, _cls._index(period))
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        with self.assertRaises(Exception):
            _cls._index(period)

    def test_actual_market_datas(self) -> None:
        self.broker_switch(on=True)
        _cls = BinanceFakeAPI
        pair = Pair('BTC/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED)
        min_period = 60
        min_period_milli = min_period*1000
        # Stage 1
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        market_datas1 = _cls._actual_market_datas(merged_pair)
        Bot.update_trade_index(1)
        market_datas2 = _cls._actual_market_datas(merged_pair)
        exp1 = min_period_milli
        result1 = market_datas2.get(Map.start) - market_datas1.get(Map.start)
        self.assertEqual(exp1, result1)
        self.assertEqual(market_datas2.get(Map.start), market_datas2.get(Map.time))
        # Stage 2
        Config.update(Config.STAGE_MODE, Config.STAGE_2)
        _cls.reset()
        # —— No socket event yet
        market_datas3 = _cls._actual_market_datas(merged_pair)
        event_time3 = market_datas3.get(Map.time)
        self.assertTrue(event_time3%min_period_milli ==  0)
        # —— Socket event happen
        time.sleep(5)
        market_datas4 = _cls._actual_market_datas(merged_pair)
        unix_time4 = _MF.get_timestamp(_MF.TIME_MILLISEC)
        event_time4 = market_datas4.get(Map.time)
        self.assertTrue((unix_time4 - event_time4) < min_period_milli)
        self.assertTrue(event_time4%min_period_milli > 0)
        # Stage 3
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        with self.assertRaises(Exception):
            _cls._actual_market_datas(merged_pair)
        self.broker_switch(on=False)

    def test_update_orders(self) -> None:
        _cls = BinanceFakeAPI
        params = self.order_params
        merged_pair = params.get(Map.symbol)
        order = _cls._new_order(params)
        exp1 = BinanceAPI.STATUS_ORDER_NEW
        result1 = order.get_attribut(Map.status)
        self.assertEqual(exp1, result1)
        _cls._update_orders(merged_pair)
        exp2 = BinanceAPI.STATUS_ORDER_FILLED
        result2 = order.get_attribut(Map.status)
        self.assertEqual(exp2, result2)

    def test_steal_request(self) -> None:
        pass

    def test_get_file_path(self) -> None:
        _cls = BinanceFakeAPI
        paths = {
            _cls._DIR_EXCHANGE_INFOS: 'content/storage/BinanceFakeAPI/requests/exchange_infos/2022-01-26_05.52.52_exchange_infos.json',
            _cls._DIR_TRADE_FEES: 'content/storage/BinanceFakeAPI/requests/trade_fees/2022-01-30_14.56.31_trade_fees.json'
        }
        for dir_path, file_path in paths.items():
            exp = file_path
            result = _cls.get_file_path(dir_path)
            self.assertEqual(exp, result)

    def test_request_exchange_infos(self) -> None:
        _cls = BinanceFakeAPI
        infos = _cls._request_exchange_infos()
        self.assertIsInstance(infos, dict)
        self.assertTrue(len(infos) > 0)

    def test_request_trade_fees(self) -> None:
        _cls = BinanceFakeAPI
        fees = _cls._request_trade_fees()
        self.assertIsInstance(fees, list)
        self.assertTrue(len(fees) > 0)

    def test_request_kline(self) -> None:
        def test_open_time(open_times: list, klines: np.ndarray) -> None:
            open_time = klines[-1][0]
            self.assertTrue(open_time not in open_times)
            open_times.append(open_time)

        self.broker_switch(True)
        _cls = BinanceFakeAPI
        n_periods = [1, 534, _cls.CONSTRAINT_KLINES_MAX_PERIOD]
        period_milli = 60*1000
        params = Map({"symbol": "BTCUSDT", "interval": "1m", Map.limit: 'x'})
        # Stage 1
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        open_times1 = []
        bot_index1 = 0
        for n_period in n_periods:
            Bot.update_trade_index(bot_index1)
            bot_index1 += 1
            params.put(n_period, Map.limit)
            klines = _cls._request_kline(params)
            test_open_time(open_times1, klines)
            n_kline = len(klines)
            self.assertIsInstance(klines, list)
            self.assertEqual(n_period, n_kline)
            n_increase = sum([1 for i in range(1, n_kline) if klines[i][0] > klines[i-1][0]])
            self.assertEqual((n_kline-1), n_increase)
        # Stage 2
        _cls.reset()
        Config.update(Config.STAGE_MODE, Config.STAGE_2)
        unix_time = _MF.get_timestamp(_MF.TIME_MILLISEC)
        for n_period in n_periods:
            params.put(n_period, Map.limit)
            klines = _cls._request_kline(params)
            n_kline = len(klines)
            self.assertIsInstance(klines, list)
            self.assertEqual(n_period, n_kline)
            n_increase = sum([1 for i in range(1, n_kline) if klines[i][0] > klines[i-1][0]])
            self.assertEqual((n_kline-1), n_increase)
            self.assertTrue((unix_time - klines[-1][0]) < period_milli)
        self.broker_switch(False)

    def test_request_submit_order(self) -> None:
        _cls = BinanceFakeAPI
        params = self.order_params
        response = _cls._request_submit_order(params)
        self.assertIsInstance(response, dict)
        self.assertEqual(BinanceAPI.STATUS_ORDER_FILLED, response[Map.status])
        self.assertTrue(len(response) > 0)

    def test_request_cancel_order(self) -> None:
        _cls = BinanceFakeAPI
        pair = Pair('BTC/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        submit_params = Map({
            "symbol": merged_pair,
            "side": "SELL",
            "type": "STOP_LOSS_LIMIT",
            "timeInForce": "GTC",
            "quantity": 92.0,
            "price": 0.8171,
            "stopPrice": 0.8171,
            "newClientOrderId": "odr_foa01274mk642l970y61",
            "newOrderRespType": "FULL",
            "timestamp": 1640724616925,
            "recvWindow": 6000,
            "signature": "d1eb9e2d3b4ba9c463a03f201fbd33e674f931911a741fec2c231f4983e51a66"
            })
        submit_response = _cls._request_submit_order(submit_params)
        orderId = submit_response[Map.orderId]
        cancel_params = Map({
            "symbol": merged_pair,
            "orderId": orderId,
            "timestamp": 1640726298569,
            "recvWindow": 6000,
            "signature": "6d90a1865f99dd20e79cc3ebdbb2f9724123915880bfa14b7667bb4da6c07a03"
            })
        cancel_response = _cls._request_cancel_order(cancel_params)
        self.assertIsInstance(cancel_response, dict)
        self.assertEqual(BinanceAPI.STATUS_ORDER_CANCELED, cancel_response[Map.status])
        self.assertTrue(len(cancel_response) > 0)

    def test_request_all_orders(self) -> None:
        _cls = BinanceFakeAPI
        pair = Pair('DOGE/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        submit_params = self.order_params
        submit_params.put(merged_pair, Map.symbol)
        orders_params = Map({
            "symbol": merged_pair,
            "startTime": 1640724617302,
            "timestamp": 1640724619605,
            "recvWindow": 6000,
            "signature": "530d5a65c90318a361f5b18430163c00f253648e433732c97471828ec2450088"
        })
        # Exist 0 order
        result1 = _cls._request_all_orders(orders_params)
        self.assertListEqual([], result1)
        # Exist 1 order
        submit_response1 = _cls._request_submit_order(submit_params)
        exp2 = [submit_response1]
        result2 = _cls._request_all_orders(orders_params)
        self.assertIsInstance(result2, list)
        self.assertIsInstance(result2[0], dict)
        self.assertEqual(exp2, result2)
        # Exist Multiple order
        submit_response2 = _cls._request_submit_order(submit_params)
        exp3 = [submit_response1, submit_response2]
        result3 = _cls._request_all_orders(orders_params)
        self.assertIsInstance(result3, list)
        self.assertIsInstance(result3[0], dict)
        self.assertEqual(exp3, result3)

    def test_request_all_trades(self) -> None:
        _cls = BinanceFakeAPI
        pair = Pair('ETH/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        submit_params = self.order_params
        submit_params.put(merged_pair, Map.symbol)
        trades_params = Map({
            "symbol": merged_pair,
            "startTime": 1640746295414,
            "timestamp": 1640749162237,
            "recvWindow": 6000,
            "signature": "c8dfd48f2285fd3411123c9bcfed7979afdee0593afafb6f74f41d933ba5d256"
            })
        # Exist 0 order
        result1 = _cls._request_all_trades(trades_params)
        self.assertListEqual([], result1)
        # Exist 1 order
        submit_response1 = _cls._request_submit_order(submit_params)
        exp2 = [submit_response1[Map.fills][0]]
        result2 = _cls._request_all_trades(trades_params)
        self.assertIsInstance(result2, list)
        self.assertIsInstance(result2[0], dict)
        self.assertEqual(exp2, result2)
        # Exist Multiple order
        submit_response2 = _cls._request_submit_order(submit_params)
        exp3 = [submit_response1[Map.fills][0], submit_response2[Map.fills][0]]
        result3 = _cls._request_all_trades(trades_params)
        self.assertIsInstance(result3, list)
        self.assertIsInstance(result3[0], dict)
        self.assertEqual(exp3, result3)
