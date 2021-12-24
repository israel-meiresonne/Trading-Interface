import threading
import time
import unittest

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.WebSocket import WebSocket
from websocket import WebSocketApp


class TestWebSocket(unittest.TestCase, WebSocket):
    def setUp(self) -> None:
        self.url = 'wss://stream.binance.com:9443/ws/btcusdt@kline_1m'

    def test_constructor(self) -> None:
        url = self.url
        # Normal
        WebSocket(url)
        # Use event handler
        handlers = self.get_event_handlers()
        WebSocket(url, **handlers.get_map())
        # one event handler has wrong type
        for event_k, event in handlers.get_map().items():
            cp_handlers = handlers.get_map().copy()
            cp_handlers[event_k] = 'hello'
            with self.assertRaises(TypeError):
                WebSocket(url, **cp_handlers)
        # header has wrong type
        with self.assertRaises(TypeError):
            WebSocket(url, header='hello')
        # url has wrong type
        with self.assertRaises(TypeError):
            WebSocket(url=15)
        # url too long
        to_long = '/'.join(["hello" for i in range(self.get_url_max_length())])
        with self.assertRaises(ValueError):
            WebSocket(url=to_long)

    def test_run_close(self) -> None:
        def get_events() -> dict:
            f_events = {
                Map.on_open: 0,
                Map.on_close: 0,
                Map.on_data: 0
                }
            return f_events

        def wait_event(event_key) -> None:
            timeout = 10
            i = 0
            while (events[event_key] != 1) and (i < timeout):
                i += 1
                time.sleep(1)
            if i >= timeout:
                raise Exception(f"Event don't reached: '{event_key}'")

        def on_open(socket: WebSocketApp) -> None:
            print(f"{_MF.prefix()}on_open: connection established")
            events[Map.on_open] = 1

        def on_close(socket: WebSocketApp, status_code: int, close_msg: str) -> None:
            print(f"{_MF.prefix()}on_close('{status_code}'): '{close_msg}'")
            events[Map.on_close] = 1

        def on_data(socket: WebSocketApp, message: str, data_type: str, flag: int) -> None:
            decoded = _MF.json_decode(message)
            output = f"on_data('{data_type}'): '{message}'" if ("e" not in decoded) else Map(decoded).get("e")
            print(_MF.prefix() + output)
            events[Map.on_data] = 1
        
        def send_messages(ws: WebSocket) -> None:
            end = False
            while not end:
                cmd = input("Enter code:\n")
                end = cmd == 'quit'
                try:
                    exec(cmd) if not end else None
                except Exception as e:
                    print(e)

        def test_run(ws: WebSocket) -> None:
            th1 = threading.Thread(target=ws.run, name='test_run_ws')
            th1.start()
            wait_event(Map.on_open)
            self.assertTrue(ws.is_running())
            wait_event(Map.on_data)
            self.assertEqual(url, ws.get_url())
            # send_messages(ws)
            ws.close()
            wait_event(Map.on_close)
            self.assertFalse(ws.is_running())
            self.assertFalse(th1.is_alive())

        events = get_events()
        url = self.url
        ws = WebSocket(url, on_open=on_open, on_close=on_close, on_data=on_data)
        test_run(ws)
        # Re-run same instance
        events = get_events()
        test_run(ws)
