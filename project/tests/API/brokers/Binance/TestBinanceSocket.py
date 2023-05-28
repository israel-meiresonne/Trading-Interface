import threading
import time
from typing import Tuple
import unittest
from random import random, shuffle

import numpy as np

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
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
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
        BinanceSocket._NB_INSTANCE = None
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
    # ——————————————————————————————————————————— CALLBACK EVENT DOWN

    def test_check_event_callback(self) -> None:
        bws = self.bws_multi
        streams = self.streams
        # Correct event name
        self.assertTrue(bws._check_event_callback(bws.EVENT_NEW_PERIOD, int, streams))
        # Unsupported event name
        with self.assertRaises(ValueError):
            bws._check_event_callback('wrong_event_name', int, streams)
        # No callable callback
        with self.assertRaises(TypeError):
            bws._check_event_callback(bws.EVENT_NEW_PRICE, 'no_callable', streams)
        # Wrong streams
        with self.assertRaises(TypeError):
            bws._check_event_callback(bws.EVENT_NEW_PRICE, int, 'not_list')
        with self.assertRaises(TypeError):
            bws._check_event_callback(bws.EVENT_NEW_PRICE, int, [1,2,3])

    def test_get_add_delete_event_streams(self) -> None:
        bws = self.bws_multi
        callback1 = lambda : 'callback1'
        callback_id_1 = self._new_event_callback_id(callback1)
        callback2 = lambda : 'callback2'
        callback_id_2 = self._new_event_callback_id(callback2)
        callback3 = lambda : 'callback3'
        callback_id_3 = self._new_event_callback_id(callback3)
        streams = self.streams[:3]
        event_new_period = self.EVENT_NEW_PERIOD
        event_new_price = self.EVENT_NEW_PRICE
        """
        Get
        """
        result1_1 = bws._get_event_streams()
        self.assertIsInstance(result1_1, Map)
        exp1_2 = result1_1
        result1_2 = bws._get_event_streams()
        self.assertEqual(exp1_2.get_id(), result1_2.get_id())
        self.assertEqual(id(exp1_2), id(result1_2))
        self.assertFalse(bws.exist_event_streams(event_new_period, callback1, streams))
        """
        Add
        """
        # Add success
        bws.add_event_streams(event_new_period, callback1, streams[:1])
        bws.add_event_streams(event_new_period, callback2, streams[:2])
        bws.add_event_streams(event_new_period, callback2, streams[:2]) # Hang twice the same function
        bws.add_event_streams(event_new_price, callback3, streams[:3])
        exp2_1 = Map({
            streams[0]: {
                event_new_period: {
                    callback_id_1: callback1,
                    callback_id_2: callback2
                },
                event_new_price: {
                    callback_id_3: callback3
                }
            },
            streams[1]: {
                event_new_period: {
                    callback_id_2: callback2
                },
                event_new_price: {
                    callback_id_3: callback3
                }
            },
            streams[2]: {
                event_new_price: {
                    callback_id_3: callback3
                }
            }
        })
        result2_1 = bws._get_event_streams()
        self.assertEqual(exp2_1, result2_1)
        self.assertTrue(bws.exist_event_streams(event_new_period, callback1, streams[:1]))
        self.assertTrue(bws.exist_event_streams(event_new_period, callback2, streams[:2]))
        self.assertTrue(bws.exist_event_streams(event_new_price, callback3, streams[:3]))
        """
        Remove
        """
        exp3_1 = Map({
            streams[0]: {
                event_new_period: {
                    # callback_id_1: callback1,
                    callback_id_2: callback2
                },
                # event_new_price: {
                #     callback_id_3: callback3
                # }
            },
            streams[1]: {
                event_new_period: {
                    callback_id_2: callback2
                },
                # event_new_price: {
                #     callback_id_3: callback3
                # }
            },
            # streams[2]: {
            #     event_new_price: {
            #         callback_id_3: callback3
            #     }
            # }
        })
        #
        bws.remove_event_streams(event_new_period, callback1, streams[:1])
        bws.remove_event_streams(event_new_price, callback3, streams[:3])
        bws.remove_event_streams(event_new_price, int, streams) # Don't exist
        result3_1 = bws._get_event_streams()
        self.assertEqual(exp3_1, result3_1)

    def debug_handling_callback_event(self) -> None:
        # BinanceSocket._VERBOSE = True
        bws = self.bws_multi
        b = _MF.C_BLUE
        n = _MF.S_NORMAL
        event_new_period = self.EVENT_NEW_PERIOD
        event_new_price = self.EVENT_NEW_PRICE
        pairs = MarketPrice.get_spot_pairs('Binance', Asset('usdt'))
        periods = [60, 60*5, 60*15]
        streams = Binance.generate_streams(pairs, periods)
        one_pair = Pair('BTC/USDT')
        one_stream = Binance.generate_stream(Map({Map.pair: one_pair, Map.period: 60}))
        # Callbacks
        prompt = lambda params : f" event={params[Map.event]}," + \
                f" event_time={_MF.unix_to_date(params[Map.time])}," + \
                f" pair={params[Map.pair]}," + \
                f" period={params[Map.period]}," + \
                f" close={params[Map.price][-1, 4]}," + \
                f" open_time={_MF.unix_to_date(params[Map.price][-1, 0])}," + \
                f" close_time={_MF.unix_to_date(params[Map.price][-1, 6])}"
        new_price_callback = lambda params : print(_MF.prefix() + f"{b}{prompt(params)}{n}")
        new_period_callback = lambda params : print(_MF.prefix() + f"{b}{prompt(params)}{n}")
        # btc_event = lambda params : new_price_callback(params)
        # Hang events
        bws.add_event_streams(event_new_price, new_price_callback, [one_stream])
        bws.add_event_streams(event_new_period, new_period_callback, [one_stream])
        #
        # bws.add_event_streams(event_new_period, new_period_callback, ['dogeusdt@kline_3m'])
        # bws.remove_event_streams(event_new_period, new_period_callback, ['dogeusdt@kline_3m'])
        # bws.add_event_streams(event_new_price, new_price_callback, ['dogeusdt@kline_3m'])
        # bws.remove_event_streams(event_new_price, new_price_callback, ['dogeusdt@kline_3m'])
        #
        # Start socket
        # bws.add_new_streams(streams[:10])
        # bws.add_new_streams([one_stream, *streams[:5]])
        bws.add_new_streams([one_stream])
        bws.run()
        _MF.console(**vars())
        bws.close()
        # self._VERBOSE = False

    # ——————————————————————————————————————————— CALLBACK EVENT UP

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

    def test_disable_market_history(self) -> None:
        bws = self.bws_multi
        stream = self.streams[0]
        bws._set_market_history(stream)
        market_history_np = bws.get_market_history_np(stream).copy()
        bws._disable_market_history(stream)
        history_np_desabled = bws.get_market_history_np(stream).copy()
        self.assertNotEqual(market_history_np.tolist(), history_np_desabled.tolist())
        n_row = market_history_np.shape[0]
        exp1 = np.full((n_row, 9), None)
        result1 = history_np_desabled[:, [1,2,3,4,5,7,8,9,10]]
        self.assertTupleEqual(exp1.shape, result1.shape)
        for i in range(exp1.shape[0]):
            for j in range(exp1.shape[1]):
                self.assertEqual(0, result1[i,j])

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

    def test_new_websocket_on_message_kline(self) -> None:
        def sleep_till_candle_start(period: int) -> None:
            unix_time = _MF.get_timestamp()
            last_candle_start = _MF.round_time(unix_time, period)
            next_candle_start = last_candle_start + period
            sleep_time = next_candle_start - unix_time
            time.sleep(sleep_time)

        def test_replacement(stream: str, bws: BinanceSocket, period: int) -> None:
            wait_time = 60 * 2
            i = 0
            screen = None
            replacement_succed = False
            sleep_till_candle_start(period)
            while i < wait_time:
                market_history = bws._get_market_histories().get(stream)
                if screen is None:
                    screen = {
                        Map.id: id(market_history),
                        Map.open: market_history[-1,0],
                        Map.price: market_history[-1,4]
                    }
                if (screen[Map.id] != id(market_history)) or (screen[Map.open] != market_history[-1,0]):
                    screen = None
                elif (screen[Map.id] == id(market_history)) and (screen[Map.open] == market_history[-1,0]) and (screen[Map.price] == market_history[-1,4]):
                    replacement_succed = True
                    break
                i += 1
                time.sleep(1)
            self.assertTrue(replacement_succed)

        def test_push_new_candle(stream: str, bws: BinanceSocket, period: int) -> None:
            period_milli = period * 1000
            wait_time = 60 * 5
            i = 0
            screen = None
            push_succed = False
            sleep_till_candle_start(period)
            while i < wait_time:
                market_history = bws._get_market_histories().get(stream)
                if screen is None:
                    screen = {
                        Map.id: id(market_history),
                        Map.open: market_history[-1,0],
                        Map.shape: market_history.shape[0]
                    }
                if (screen[Map.id] != id(market_history)) and (screen[Map.shape] == market_history.shape[0]):
                    screen = None
                elif (screen[Map.id] != id(market_history)) and (screen[Map.shape] < market_history.shape[0])\
                    and (screen[Map.open] == market_history[-2,0]) and ((screen[Map.open] + period_milli) == market_history[-1,0]):
                    push_succed = True
                    break
                i += 1
                time.sleep(1)
            self.assertTrue(push_succed)

        def test_reset_with_time(stream: str, bws: BinanceSocket) -> None:
            init_reset_interval = BinanceSocket._MARKET_RESET_INTEVAL
            BinanceSocket._MARKET_RESET_INTEVAL = 1
            wait_time = 60 * 4
            screen = None
            n_reset = 0
            reset_target = 3
            i = 0
            while (i < wait_time) and (n_reset < reset_target):
                market_history = bws._get_market_histories().get(stream)
                if screen is None:
                    screen = {
                        Map.id: id(market_history),
                        Map.open: market_history[-1,0],
                        Map.shape: market_history.shape[0]
                        }
                    reset_time = _MF.get_timestamp()
                    bws._get_market_reset_times().put(reset_time, stream)
                if (screen[Map.id] != id(market_history)) and (screen[Map.shape] < market_history.shape[0]):
                    screen = None
                elif (screen[Map.id] != id(market_history)) and (screen[Map.shape] == market_history.shape[0])\
                    and (screen[Map.open] == market_history[-1,0]):
                    n_reset += 1
                    screen = None
                i += 1
                time.sleep(1)
            self.assertEqual(reset_target, n_reset)
            BinanceSocket._MARKET_RESET_INTEVAL = init_reset_interval

        def test_reset_with_inconstant_open_times(stream: str, bws: BinanceSocket) -> None:
            wait_time = 60 * 2
            screen = None
            n_reset = 0
            reset_target = 3
            i = 0
            while (i < wait_time) and (n_reset < reset_target):
                market_history = bws._get_market_histories().get(stream)
                if screen is None:
                    screen = {
                        Map.id: id(market_history),
                        Map.open: market_history[-1,0],
                        Map.shape: market_history.shape[0]
                        }
                    market_history[-6:-2:2,0] = 0
                if (screen[Map.id] != id(market_history)) and (screen[Map.shape] < market_history.shape[0]):
                    screen = None
                elif (screen[Map.id] != id(market_history)) and (screen[Map.shape] == market_history.shape[0])\
                    and (screen[Map.open] == market_history[-1,0]):
                    n_reset += 1
                    screen = None
                i += 1
                time.sleep(1)
            self.assertEqual(reset_target, n_reset)
        
        def test_reset_with_incorrect_new_candle(stream: str, bws: BinanceSocket, period: int) -> None:
            period_milli = period * 1000
            wait_time = 60 * 2
            screen = None
            n_reset = 0
            reset_target = 3
            i = 0
            while (i < wait_time) and (n_reset < reset_target):
                market_history = bws._get_market_histories().get(stream)
                if screen is None:
                    screen = {
                        Map.id: id(market_history),
                        Map.open: market_history[-1,0],
                        Map.shape: market_history.shape[0]
                        }
                    market_history[:,0] = market_history[:,0] + 2*period_milli
                if (screen[Map.id] != id(market_history)) and (screen[Map.shape] < market_history.shape[0]):
                    screen = None
                elif (screen[Map.id] != id(market_history)) and (screen[Map.shape] == market_history.shape[0])\
                    and (screen[Map.open] == market_history[-1,0]):
                    n_reset += 1
                    screen = None
                i += 1
                time.sleep(1)
            self.assertEqual(reset_target, n_reset)

        rq = BinanceAPI.RQ_KLINES
        symbol = Pair('BTC/USDT').format(Pair.FORMAT_MERGED).lower()
        period = 60
        period_str = self.convert_interval(period)
        stream = self.generate_stream(rq, symbol, period_str)
        bws = BinanceSocket([stream])
        bws.run()
        # Replace most recent row with new price
        test_replacement(stream, bws, period)
        # Push new candle
        test_push_new_candle(stream, bws, period)
        # # Reset market history because of the reset time
        # bws._set_market_history(stream)
        # test_reset_with_time(stream, bws)
        # Reset market history because of open times are not constant
        bws._set_market_history(stream)
        test_reset_with_inconstant_open_times(stream, bws)
        # Reset market history because of new open time is not correct
        bws._set_market_history(stream)
        test_reset_with_incorrect_new_candle(stream, bws, period)
        # End
        bws.close()

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
        init_reset_interval = BinanceSocket._MARKET_RESET_INTEVAL
        BinanceSocket._MARKET_RESET_INTEVAL = -10
        bws._set_market_reset_time(streams[0])
        bws._set_market_reset_time(streams[1])
        self.assertTrue(bws._can_update_market_history(streams[0]))
        self.assertTrue(bws._can_update_market_history(streams[1]))
        BinanceSocket._MARKET_RESET_INTEVAL = init_reset_interval

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
            self.assertTrue(n_stream <= max_stream)
            url = self._generate_url(stream_group)
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

    def test_are_open_times_constant(self) -> None:
        def new_market_history(pair: Pair, period: int) -> Tuple[np.ndarray, str]:
            period_milli = period * 1000
            period_str = self.convert_interval(period)
            symbol = pair.format(Pair.FORMAT_MERGED)
            stream = self.generate_stream(self.RQ_KLINES, symbol, period_str)
            market_history = np.array([1602720000000 + i*period_milli for i in range(10)])
            market_history = market_history.reshape((market_history.shape[0], 1))
            return stream, market_history

        def delete_row(market_history: np.ndarray) -> np.ndarray:
            i = int(market_history.shape[0]/2)
            return np.delete(market_history, i, 0)

        def test(period: int, tests: list = [self.assertTrue, self.assertFalse]) -> None:
            stream, market_history = new_market_history(pair, period)
            tests[0](self.are_open_times_constant(stream, market_history))
            edited_market_history = delete_row(market_history)
            tests[1](self.are_open_times_constant(stream, edited_market_history))

        pair = Pair('BTC/USDT')
        # Normal
        period_1 = 60
        test(period_1)
        # period = 5min
        period_2 = 60 * 5
        test(period_2)
        # history's period > reset interval of market history
        period_3 = 60 * 60 * 6  # 6h
        test(period_3, tests=[self.assertTrue, self.assertTrue])

    def test_is_new_open_time_correct(self) -> None:
        def new_market_history(pair: Pair, period: int) -> Tuple[np.ndarray, str]:
            period_milli = period * 1000
            period_str = self.convert_interval(period)
            symbol = pair.format(Pair.FORMAT_MERGED)
            stream = self.generate_stream(self.RQ_KLINES, symbol, period_str)
            market_history = np.array([1602720000000 + i*period_milli for i in range(10)])
            market_history = market_history.reshape((market_history.shape[0], 1))
            return stream, market_history

        def get_new_row(market_history: np.ndarray) -> np.ndarray:
            return market_history[-1].copy().reshape((1,1))

        pair = Pair('BTC/USDT')
        period = 60 * 5
        period_milli = period * 1000
        stream, market_history = new_market_history(pair, period)
        # new_open_time == history_open_time
        new_row_1 = get_new_row(market_history)
        self.assertTrue(self.is_new_open_time_correct(stream, new_row_1, market_history))
        # new_open_time == (history_open_time + period)
        new_row_2 = get_new_row(market_history)
        new_row_2[-1,0] = new_row_2[-1,0] + period_milli
        self.assertTrue(self.is_new_open_time_correct(stream, new_row_2, market_history))
        # new_open_time == (history_open_time + 2*period)
        new_row_3 = get_new_row(market_history)
        new_row_3[-1,0] = (new_row_3[-1,0] + 2*period_milli)
        self.assertFalse(self.is_new_open_time_correct(stream, new_row_3, market_history))
        # new_open_time == (history_open_time - period)
        new_row_4 = get_new_row(market_history)
        new_row_4[-1,0] = new_row_4[-1,0] - period_milli
        self.assertFalse(self.is_new_open_time_correct(stream, new_row_4, market_history))

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
        pairs = [Pair('btc/usdt'), Pair('eth/usdt'), Pair('doge/usdt'), Pair('bnb/usdt')]
        period = 60
        streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
        bkr.add_streams(streams)
        _MF.console(**vars())
        self.broker_switch(False)
