import threading
import time
import unittest
from random import random, shuffle

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceSocket import BinanceSocket
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair
from model.tools.WebSocket import WebSocket


class TestBinanceSocket(unittest.TestCase, BinanceSocket):
    def setUp(self) -> None:
        _MF.OUTPUT = True
        rq = BinanceAPI.RQ_KLINES
        symbol1 = Pair('BTC/USDT').format(Pair.FORMAT_MERGED).lower()
        symbol2 = Pair('DOGE/USDT').format(Pair.FORMAT_MERGED).lower()
        symbol3 = Pair('SNX/USDT').format(Pair.FORMAT_MERGED).lower()
        period_str1 = BinanceAPI.get_intervals().get_keys()[0]
        period_str2 = BinanceAPI.get_intervals().get_keys()[1]
        period_str3 = BinanceAPI.get_intervals().get_keys()[2]
        stream1 = self.generate_stream(rq, symbol1, period_str1)
        stream2 = self.generate_stream(rq, symbol2, period_str2)
        stream3 = self.generate_stream(rq, symbol3, period_str3)
        self.streams = streams = [stream1, stream2, stream3]
        self.bws_single = BinanceSocket([stream1])
        BinanceSocket._NB_INSTANCE = None
        self.bws_multi = BinanceSocket(streams)
        BinanceSocket._NB_INSTANCE = None

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

    @staticmethod
    def fake_streams(n_stream: int) -> list:
        alphanum = list('abcdefghijklmnopqrstuvwxyz1234567890')
        streams = []
        period_strs = BinanceAPI.get_intervals().get_keys()
        rq = BinanceAPI.RQ_KLINES
        for i in range(n_stream):
            n = int(random()*10/2+2)
            shuffle(alphanum)
            symbol = ''.join(alphanum[:n])
            shuffle(period_strs)
            period_str = period_strs[0]
            stream = BinanceSocket.generate_stream(rq, symbol, period_str)
            streams.append(stream)
        return streams

    @staticmethod
    def ws_run(f_ws: WebSocket) -> threading.Thread:
        new_code = _MF.new_code()
        th1 = threading.Thread(target=f_ws.run, name=f'test_run_ws_{new_code}')
        th1.start()
        TestBinanceSocket.wait_for(f_ws.is_running, True)
        return th1

    @staticmethod
    def ws_close(f_ws: WebSocket) -> None:
        f_ws.close()
        TestBinanceSocket.wait_for(f_ws.is_running, False)

    @staticmethod
    def wait_for(callback, value) -> None:
        timeout = 10
        i = 0
        while (callback() != value) and (i < timeout):
            i += 1
            time.sleep(1)
        if i >= timeout:
            raise Exception(f"timeout: {callback.__str__()}=={value}")

    @staticmethod
    def console(**kwargs) -> None:
        kwargs = Map(kwargs)
        end = False
        while not end:
            cmd = input("Enter code:\n")
            end = cmd == 'quit'
            try:
                exec(cmd) if not end else None
            except Exception as e:
                print(e)

    # ——————————————————————————————————————————— TEST SELF FUNCTION DOWN ——————————————————————————————————————————————

    def test_urls_url(self) -> None:
        bws = self.bws_multi
        streams = bws.get_streams()
        fake_stream = self.fake_streams(1)[0]
        # WebSocket no running
        exp1 = Map()
        result1 = bws.urls()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        #
        self.assertIsNone(bws.url(streams[0]))
        # WebSocket running
        bws.run()
        time.sleep(len(streams))
        #
        ws_id = bws._get_websockets().get_keys()[0]
        ws_url = self._generate_url(streams)
        exp3 = Map({ws_id: ws_url})
        result3 = bws.urls()
        self.assertDictEqual(exp3.get_map(), result3.get_map())
        #
        exp4 = ws_url
        result4 = bws.url(streams[0])
        self.assertEqual(exp4, result4)
        with self.assertRaises(Exception):
            bws.url(fake_stream)
        bws.close()

    def test_add_delete_streams(self) -> None:
        bws = self.bws_multi
        new_streams1 = self.fake_streams(5)
        # New streams don't exist
        bws._add_streams(new_streams1)
        exp1 = [*self.streams, *new_streams1]
        exp1.sort()
        result1 = bws.get_streams()
        self.assertListEqual(exp1, result1)
        # New streams exist
        stream2 = self.fake_streams(1)[0]
        new_streams2 = [*new_streams1, stream2]
        bws._add_streams(new_streams2)
        exp2 = [*self.streams, *new_streams1, stream2]
        exp2.sort()
        result2 = bws.get_streams()
        self.assertListEqual(exp2, result2)
        # Delete streams
        bws._delete_streams([*new_streams1, *new_streams2])
        exp3 = self.streams
        result3 = bws.get_streams()
        self.assertListEqual(exp3, result3)

    def test_add_new_streams(self) -> None:
        bws = self.bws_multi
        new_streams1 = self.fake_streams(5)
        # New streams don't exist
        bws.add_new_streams(new_streams1)
        exp1 = new_streams1
        exp1.sort()
        result1 = bws.get_new_streams()
        self.assertListEqual(exp1, result1)
        # New streams exist
        stream2 = self.fake_streams(1)[0]
        new_streams2 = [*new_streams1, stream2]
        bws.add_new_streams(new_streams2)
        exp2 = [*new_streams1, stream2]
        exp2.sort()
        result2 = bws.get_new_streams()
        self.assertListEqual(exp2, result2)

    def test_add_delete_websocket(self) -> None:
        bws = self.bws_multi
        ws1 = WebSocket("wss://websocket.fake")
        ws2 = WebSocket("wss://websocket.fake")
        # Add
        bws._add_websocket(ws1)
        bws._add_websocket(ws2)
        exp1 = ws1.__dict__
        result1 = bws._get_websocket(ws1.get_id()).__dict__
        self.assertDictEqual(exp1, result1)
        exp2 = ws2.__dict__
        result2 = bws._get_websocket(ws2.get_id()).__dict__
        self.assertDictEqual(exp2, result2)
        # Delete
        bws._delete_websocket(ws1.get_id())
        bws._delete_websocket(ws2.get_id())
        self.assertIsNone(bws._get_websocket(ws1.get_id()))
        self.assertIsNone(bws._get_websocket(ws2.get_id()))

    def test_get_stream_time(self) -> None:
        bws = self.bws_single
        stream = bws.get_streams()[0]
        bws.run()
        event_times = []
        n_turn = 5
        # Update
        while len(event_times) < n_turn:
            event_time = bws.get_stream_time(stream)
            event_times.append(event_time) if isinstance(event_time, int) and (event_time not in event_times) else time.sleep(1)
        print([_MF.unix_to_date((event_time/1000), form=_MF.FORMAT_D_H_M_S_MS) for event_time in event_times])
        exp1 = n_turn
        result1 = len(event_times)
        self.assertEqual(exp1, result1)
        # Most recet event
        exp2 = bws.get_stream_time(stream)
        result2 = bws.stream_time()
        self.assertIsInstance(result2, int)
        self.assertEqual(exp2, result2)
        # Close
        bws.close()
        self.assertDictEqual({}, bws._get_stream_times().get_map())
    
    def test_stream_time(self) -> None:
        pass

    def test_set_get_market_history(self) -> None:
        bws = self.bws_multi
        streams = self.streams
        bws._set_market_history(streams[0])
        bws._set_market_history(streams[1])
        mkt1 = bws.get_market_history(streams[0])
        self.assertIsInstance(mkt1, list)
        mkt2 = bws.get_market_history(streams[1])
        self.assertIsInstance(mkt2, list)
        self.assertNotEqual(mkt1[0][4], mkt2[0][4])
        # Raise error
        fake_stream = self.fake_streams(1)[0]
        self.assertFalse(bws._set_market_history(fake_stream))
    
    def test_websocket_are_running(self) -> None:
        bws = self.bws_multi
        streams = self.streams
        url1 = self._generate_url([streams[0]])
        url2 = self._generate_url([streams[1]])
        ws1 = WebSocket(url1)
        ws2 = WebSocket(url2)
        # No WebSocket
        self.assertFalse(bws._websocket_are_running())
        # With WebSocket not running
        bws._add_websocket(ws1)
        bws._add_websocket(ws2)
        self.assertFalse(bws._websocket_are_running())
        # With running and not running WebSocket
        self.ws_run(ws1)
        self.assertFalse(bws._websocket_are_running())
        # With all WebSocket are running
        self.ws_run(ws2)
        self.assertTrue(bws._websocket_are_running())
        # Close one
        self.ws_close(ws1)
        self.assertFalse(bws._websocket_are_running())
        # Close all
        self.ws_close(ws2)
        self.assertFalse(bws._websocket_are_running())

    def test_new_websocket(self) -> None:
        bws = self.bws_single
        streams = bws.get_streams()
        ws = bws._new_websocket(streams)
        #
        self.assertDictEqual(ws.__dict__, bws._get_websocket(ws.get_id()).__dict__)
        exp2 = self._generate_url(streams)
        result2 = ws.get_url()
        self.assertEqual(exp2, result2)
        #
        self.ws_run(ws)
        self.ws_close(ws)

    def test_new_websockets(self) -> None:
        bws = self.bws_multi
        max_stream = self.get_websocket_max_stream()
        fake_streams = self.fake_streams(max_stream * 2)
        wss = bws._new_websockets(fake_streams)
        ws_streams = []
        for ws in wss:
            ws_streams = [*ws_streams, *self.url_to_streams(ws.get_url())]
        self.assertListEqual(fake_streams, ws_streams)

    def test_can_update_market_history(self) -> None:
        bws = self.bws_multi
        streams = bws.get_streams()
        # history don't exist
        self.assertTrue(bws._can_update_market_history(streams[0]))
        self.assertTrue(bws._can_update_market_history(streams[1]))
        # reset time not reached
        self.setUp()
        bws = self.bws_multi
        streams = bws.get_streams()
        bws._set_market_reset_time(streams[0])
        bws._set_market_reset_time(streams[1])
        self.assertFalse(bws._can_update_market_history(streams[0]))
        self.assertFalse(bws._can_update_market_history(streams[1]))
        # reset time reached
        self.setUp()
        bws = self.bws_multi
        streams = bws.get_streams()
        BinanceSocket._MARKET_RESET_INTEVAL = -10
        bws._set_market_reset_time(streams[0])
        bws._set_market_reset_time(streams[1])
        self.assertTrue(bws._can_update_market_history(streams[0]))
        self.assertTrue(bws._can_update_market_history(streams[1]))

    def test_update_market_history(self) -> None:
        bws = self.bws_multi
        streams = bws.get_streams()
        market_room = bws._get_room_market_update()
        # When thread don't exist AND stream not in queu
        bws._update_market_history(streams[0])
        th1 = bws._get_thread_market_update()
        self.assertTrue(streams[0] in market_room.get_tickets())
        self.assertTrue(th1.is_alive())
        # Thread already exist AND stream not in queu
        th2 = bws._get_thread_market_update()
        bws._update_market_history(streams[1])
        self.assertTrue(streams[1] in market_room.get_tickets())
        self.assertEqual(th1.getName(), th2.getName())
        self.assertEqual(id(th1), id(th2))
        self.assertTrue(th2.is_alive())
        # Stream already in queue
        bws._update_market_history(streams[2])
        bws._update_market_history(streams[2])
        exp3 = 1
        result3 = sum([1 for stream in market_room.get_tickets() if stream == streams[2]])
        self.assertEqual(exp3, result3)
        # Thread die
        self.wait_for(th1.is_alive, False)
        [self.assertIsInstance(bws.get_market_history(stream), list) for stream in streams]
        self.assertListEqual([], market_room.get_tickets())
        self.assertNotEqual(th1.getName(), bws._get_thread_market_update().getName())

    def test_manage_update_market_histories(self) -> None:
        def test(f_streams: list) -> None:
            [market_room.join_room(f_stream) for f_stream in f_streams]
            th1 = bws._get_thread_market_update()
            bws._manage_update_market_histories()
            th2 = bws._get_thread_market_update()
            self.assertNotEqual(th1.getName(), th2.getName())
            self.assertNotEqual(id(th1), id(th2))
            self.assertListEqual([], market_room.get_tickets())

        bws = self.bws_multi
        market_room = bws._get_room_market_update()
        # When history reseted
        streams = bws.get_streams()
        test(streams)
        [self.assertIsInstance(bws.get_market_history(stream), list) for stream in streams]
        # When fail to reset history
        fake_streams = self.fake_streams(5)
        test(fake_streams)
        with self.assertRaises(Exception):
            a = [self.assertIsNone(bws.get_market_history(fake_stream), list) for fake_stream in fake_streams]

    def test_run_close(self) -> None:
        def test_run(f_bws: BinanceSocket) -> None:
            new_streams1 = bws.get_new_streams()
            f_bws.run()
            self.wait_for(f_bws._websocket_are_running, True)
            new_streams1_1 = f_bws.get_new_streams()
            self.assertNotEqual(id(new_streams1), id(new_streams1_1))
            self.assertTrue(f_bws.is_running())
            reset_times = f_bws._get_market_reset_times().get_map()
            self.assertTrue(len(reset_times) > 0)
            [self.assertTrue(reset_time > 0) for _, reset_time in reset_times.items()]

        # Run
        bws = self.bws_multi
        test_run(bws)
        # console(bws)
        # Already running
        with self.assertRaises(Exception):
            bws.run()
        # Close
        time.sleep(5)
        bws.close()
        self.assertFalse(bws.is_running())
        self.assertTrue(len(bws._get_market_histories().get_map()) == 0)
        self.assertTrue(len(bws._get_market_reset_times().get_map()) == 0)
        # Restart
        test_run(bws)
        # Add new stream
        i = 0
        new_streams = []
        for pair_str in ["COTI/USDT", "ANT/USDT", "SUSHI/USDT"]:
            symbol = Pair(pair_str).format(Pair.FORMAT_MERGED).lower()
            period_str = BinanceAPI.get_intervals().get_keys()[i]
            stream = self.generate_stream(BinanceAPI.RQ_KLINES, symbol, period_str)
            new_streams.append(stream)
            i += 1
        wss1 = Map(bws._get_websockets().get_map().copy())
        bws.add_new_streams(new_streams)
        time.sleep(5)
        #
        exp1 = [*self.streams, *new_streams]
        exp1.sort()
        result1 = bws.get_streams()
        result1.sort()
        self.assertListEqual(exp1, result1)
        self.assertTrue(len(wss1.get_map()) > 0)
        #
        wss2 = bws._get_websockets()
        exp2 = '-'.join(wss1.get_keys())
        result2 = '-'.join(wss2.get_keys())
        self.assertNotEqual(exp2, result2)
        #
        last_ws = wss2.get(wss2.get_keys()[-1])
        exp3 = [*self.streams, *new_streams]
        exp3.sort()
        result3 = bws.url_to_streams(last_ws.get_url())
        result3.sort()
        self.assertListEqual(exp3, result3)
        # Add fake streams
        time.sleep(10)
        bws.close()

    def test_surcharge_run(self) -> None:
        pairs = MarketPrice.get_spot_pairs('Binance', Asset('USDT'))
        period_strs = BinanceAPI.get_intervals().get_keys()
        streams = []
        for pair in pairs:
            symbol = pair.format(Pair.FORMAT_MERGED).lower()
            pair_streams = [self.generate_stream(BinanceAPI.RQ_KLINES, symbol, period_str) for period_str in period_strs]
            streams = [
                *streams,
                *pair_streams
            ]
        bws = BinanceSocket([streams[0]])
        BinanceSocket._NB_INSTANCE = None
        bws.run()
        # bws.add_new_streams(streams[1:1050])
        bws.add_new_streams(streams[1:5])
        # time.sleep(5)
        bws.add_new_streams(streams[5:10])
        # self.console(**vars())
        # time.sleep(10)
        bws.close()

    # ——————————————————————————————————————————— TEST SELF FUNCTION UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— TEST STATIC FUNCTION DOWN ————————————————————————————————————————————

    def test_check_stream(self) -> None:
        # Correct stream
        stream1 = "btcusdt@kline_1M"
        self.assertTrue(self.check_stream(stream1))
        # Wrong stream
        stream2 = "btcusdt@kline_1Z"
        stream3 = "é'ds@kline_1M"
        with self.assertRaises(ValueError):
            self.check_stream(stream2)
        with self.assertRaises(ValueError):
            self.check_stream(stream3)
    
    def test_generate_stream(self) -> None:
        rq1 = BinanceAPI.RQ_KLINES
        symbol1 = Pair("BTC/USDT").format(Pair.FORMAT_MERGED).lower()
        period_str1 = "1w"
        exp1 = f"{symbol1}@kline_{period_str1}"
        result1 = self.generate_stream(rq1, symbol1, period_str1)
        self.assertEqual(exp1, result1)
        # Wrong request
        rq2 = BinanceAPI.RQ_24H_STATISTICS
        with self.assertRaises(ValueError):
            self.generate_stream(rq2, symbol1, period_str1)
        # Wrong string period
        period_str3 = 'hello'
        with self.assertRaises(ValueError):
            self.generate_stream(rq1, symbol1, period_str3)

    def test_split_stream(self) -> None:
        exp_symbol = Pair("BTC/USDT").format(Pair.FORMAT_MERGED).lower()
        exp_period_str = "1w"
        stream = "btcusdt@kline_1w"
        result_symbol, result_period_str = self.split_stream(stream)
        self.assertEqual(exp_symbol, result_symbol)
        self.assertEqual(exp_period_str, result_period_str)
    
    def test_group_streams(self) -> None:
        url_max = WebSocket.get_url_max_length()
        max_stream = self.get_websocket_max_stream()
        streams = self.fake_streams(url_max)
        stream_groups = self._group_streams(streams)
        for stream_group in stream_groups:
            n_stream = len(stream_group)
            # print(f"n_stream='{n_stream}' <= max_stream='{max_stream}'")
            self.assertTrue(n_stream <= max_stream)
            url = self._generate_url(stream_group)
            # print(f"url='{len(url)}' <= url_max='{url_max}'")
            self.assertTrue(len(url) <= url_max)

    def test_generate_url(self) -> None:
        separator = self.get_url_stream_separator()
        max_stream = self.get_websocket_max_stream()
        stream1 = "btcusdt@kline_1M"
        stream2 = "btcusdt@kline_1w"
        streams1 = [stream1, stream2]
        exp1 = self.get_url_base() + self.get_url_path_single_stream() + stream1
        result1 = self._generate_url([stream1])
        self.assertEqual(exp1, result1)
        exp2 = self.get_url_base() + self.get_url_path_multiple_stream() + separator.join(streams1)
        result2 = self._generate_url(streams1)
        self.assertEqual(exp2, result2)
        # Number of stream exceed max number allowed
        streams2 = [stream2 for i in range(max_stream * 2)]
        with self.assertRaises(ValueError):
            self._generate_url(streams2)

    def test_url_to_streams(self) -> None:
        streams = self.fake_streams(10)
        url = self._generate_url(streams)
        exp1 = streams
        result1 = self.url_to_streams(url)
        self.assertListEqual(exp1, result1)
        # Url has wrong type
        with self.assertRaises(TypeError):
            self.url_to_streams(url=15)

    # ——————————————————————————————————————————— TEST STATIC FUNCTION UP ——————————————————————————————————————————————
    # ——————————————————————————————————————————— DEBUG DOWN ———————————————————————————————————————————————————————————

    def debug_kline_event(self) -> None:
        def get_close(pair_str, period) -> float:
            mkt = MarketPrice.marketprice(bkr, Pair(pair_str), period, n_period=1000)
            return mkt.get_close()
        
        def add_stream(pair_str: str) -> None:
            stream = bkr.generate_stream(Map({Map.pair: Pair(pair_str), Map.period: period}))
            bkr.add_streams([stream])

        bkr = self.broker_switch(True)
        pair = Pair('hard/usdt')
        period = 60
        stream = bkr.generate_stream(Map({Map.pair: pair, Map.period: period}))
        bkr.add_streams([stream])
        _MF.console(**vars())
        self.broker_switch(False)
