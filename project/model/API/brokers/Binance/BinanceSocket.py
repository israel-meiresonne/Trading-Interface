import threading
import time
from typing import List, Tuple

import numpy as np
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.WaitingRoom import WaitingRoom
from model.tools.WebSocket import WebSocket


class BinanceSocket(BinanceAPI):
    _DEBUG = True
    _VERBOSE = False
    _NB_INSTANCE = None
    # API CONSTRAINTS
    _REGEX_STREAM = r'^[\w]+@kline_\d{1,2}[dhmMw]$'
    _FORMAT_STREAM = f'${Map.symbol}@kline_${Map.interval}'
    _WEBSOCKET_MAX_STREAM = 1024
    _URL_BASE = 'wss://stream.binance.com:9443'
    _URL_PATH_SINGLE_STREAM = '/ws/'
    _URL_PATH_MULTIPLE_STREAM = '/stream?streams='
    _URL_STREAM_SEPARATOR = '/'
    # Class CONSTRAINTS
    _MARKET_RESET_INTEVAL = 60 * 30
    _RESTART_INTERVAL_RUN_MANAGER = 60
    _THREAD_NAME_UPDATE_MARKET = 'market_update_manager'
    _THREAD_NAME_RUN_MANGER = 'run_manager'
    _THREAD_NAME_RUN_ADD_STREAM = 'run_add_stream'
    _THREAD_NAME_WEBSOCKET_MANGER = 'websocket_manager'
    _THREAD_NAME_WEBSOCKET_EVENT_HANDLER = 'websocket_event_handler'
    _WEBSOCKET_RUN_TIMEOUT = 10

    def __init__(self, streams: list):
        if BinanceSocket._NB_INSTANCE is not None:
            raise Exception("Can't instantiate more than 1 BinanceSocket")
        BinanceSocket._NB_INSTANCE = 1
        self.__running = False
        self.__streams = None
        self.__new_streams = None
        self.__websockets = None
        self.__market_histories = None
        self.__room_market_update = None
        self.__thread_market_update = None
        self.__room_call_market_update = None
        self.__market_reset_times = None
        self.__thread_run_manager = None
        self._set_streams(streams)

    # ——————————————————————————————————————————— SELF GETTER/SETTER FUNCTION DOWN —————————————————————————————————————

    def _turn_on(self) -> None:
        """
        To set BinanceSocket's connection status to 'active'
        """
        self.__running = True

    def _turn_off(self) -> None:
        """
        To set BinanceSocket's connection status to 'no active'
        """
        self.__running = False

    def is_running(self) -> bool:
        """
        To check if connection to WebSocket is established and maintained

        Returns:
        --------
        return: bool
            True if connection to WebSocket is active else None
        """
        return self.__running

    def _reset_streams(self) -> None:
        self.__streams = None

    def _set_streams(self, streams: list) -> None:
        if len(streams) == 0:
            raise ValueError("The list of stream can't be empty")
        streams = [stream for stream in streams if self.check_stream(stream)]
        streams.sort()
        self.__streams = streams

    def get_streams(self) -> list:
        """
        To get list of stream open in WebSocket

        Returns:
        --------
        return: list
            List of stream open
        """
        return self.__streams.copy()

    def _add_streams(self, new_streams: list) -> None:
        """
        To add new streams in this.streams

        Parameters:
        --------
        new_streams: list
            List of streams to add
        """
        streams = self.__streams
        [streams.append(new_stream) for new_stream in new_streams if new_stream not in streams]
        streams.sort()

    def _delete_streams(self, to_deletes: list) -> None:
        """
        To delete streams from this.streams

        Parameters:
        -----------
        to_deletes: list
            Streams to delete
        """
        streams = self.__streams
        for stream in to_deletes:
            if stream in streams:
                idx = streams.index(stream)
                del streams[idx]

    def _reset_new_streams(self) -> None:
        self.__new_streams = None

    def get_new_streams(self) -> list:
        """
        To get list of new stream to open in WebSocket

        Returns:
        --------
        return: list
            List of new stream to open in WebSocket
        """
        if self.__new_streams is None:
            self.__new_streams = []
        return self.__new_streams

    def add_new_streams(self, new_streams: list) -> None:
        """
        To add new streams in WebSocket

        Parameters:
        -----------
        new_streams: list
            List of stream to add
        """
        [self.check_stream(new_stream) for new_stream in new_streams]
        streams = self.get_streams()
        old_new_streams = self.get_new_streams()
        [old_new_streams.append(new_stream) for new_stream in new_streams if (new_stream not in old_new_streams) and (new_stream not in streams)]
        old_new_streams.sort()

    def _get_websockets(self) -> Map:
        """
        To get Collection of active WebSocket

        Returns:
        --------
        return: Map
            Collection of active WebSocket
            Map[WebSocket.id]: {WebSocket}
        """
        if self.__websockets is None:
            self.__websockets = Map()
        return self.__websockets

    def _get_websocket(self, websocket_id: str) -> WebSocket:
        """
        To get a WebSocket

        Parameters:
        -----------
        websocket_id: str
            Id of a WebSocket
        
        Returns:
        --------
        return: WebSocket
            A WebSocket
        """
        return self._get_websockets().get(websocket_id)

    def _add_websocket(self, websocket: WebSocket) -> None:
        """
        To add a new WebSocket

        Parameters:
        -----------
        websocket: WebSocket
            WebSocket to add
        """
        self._get_websockets().put(websocket, websocket.get_id())

    def _delete_websocket(self, websocket_id: str) -> None:
        """
        To close and delete WebSocket

        Parameters:
        -----------
        websocket_id: str
            Id of a WebSocket
        """
        wss = self._get_websockets()
        if websocket_id in wss.get_keys():
            ws = wss.get(websocket_id)
            ws.close()
            del wss.get_map()[websocket_id]
            del ws

    def _reset_market_histories(self) -> None:
        self.__market_histories = None

    def _get_market_histories(self) -> Map:
        """
        To get list of market histories
        NOTE: market histories are sorted from older (top) to newest (bottom)

        Returns:
        --------
        return: Map
            List of market histories
            Map[stream{str}]:   {Numpy.ndarray}
        """
        if self.__market_histories is None:
            self.__market_histories = Map()
        return self.__market_histories

    def _set_market_history(self, stream: str, raise_error: bool = True) -> bool:
        """
        To set market history for the given stream
        NOTE: send request to API

        Parameters:
        -----------
        stream: str
            Stream to treat
        raise_error: bool = True
            Set True to raise errors occured else False to handle errors

        Returns:
        --------
        return: bool
            True if market history is set else False if process fail
        """
        is_success = False
        api_keys = BinanceAPI.get_default_api_keys()
        test_mode = False
        rq = BinanceAPI.RQ_KLINES
        symbol, period_str = self.split_stream(stream)
        # Get market history
        try:
            params = Map({
                Map.symbol: symbol.upper(),
                Map.interval: period_str,
                Map.limit: BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD
            })
            bkr_rsp = BinanceAPI._waitingroom(test_mode, api_keys, rq, params)
            status_code = bkr_rsp.get_status_code()
            is_success = (status_code is not None) and (status_code == 200)
        except Exception as error:
            _MF.output(_MF.prefix() + '\033[31m' +
                  "Network error when getting market history" + '\033[0m')
            from model.structure.Bot import Bot
            Bot.save_error(error, BinanceSocket.__name__)
            if raise_error:
                raise Exception(f"Failed to set market history for stream: '{stream}'")
        # Update market history
        if is_success:
            market_history = bkr_rsp.get_content()
            martket_np = np.array(market_history, dtype=np.float64)
            self._get_market_histories().put(martket_np, stream)
        # End
        return is_success

    def get_market_history(self, stream: str) -> list:
        """
        To get market history for the given stream

        Returns:
        --------
        return: list
            The market history for the given stream
        """
        self.check_stream(stream)
        market_histories = self._get_market_histories()
        market_history = market_histories.get(stream)
        return market_history.tolist()

    def _reset_room_market_update(self) -> None:
        market_room = self.__room_market_update
        streams = market_room.get_tickets()
        [market_room.quit_room(stream) for stream in streams]
        self.__room_market_update = None
        del market_room

    def _get_room_market_update(self) -> WaitingRoom:
        """
        To get queue of stream asking to update their market history
        NOTE: tickets for room are streams matching stream forrmat\n
        Returns:
        --------
        return: WaitingRoom
            List of stream asking to update their market history
        """
        if self.__room_market_update is None:
            self.__room_market_update = WaitingRoom('update-market-history')
        return self.__room_market_update

    def _reset_room_call_market_update(self) -> None:
        call_room = self.__room_call_market_update
        tickets = call_room.get_tickets()
        [call_room.quit_room(ticket) for ticket in tickets]
        self.__room_call_market_update = None
        del call_room

    def _get_room_call_market_update(self) -> WaitingRoom:
        """
        To get queue of call of function that create and start thread that manage update of market histories

        Returns:
        --------
        reeturn: WaitingRoom
            Queue of call of function that create and start thread that manage update of market histories
        """
        if self.__room_call_market_update is None:
            self.__room_call_market_update = WaitingRoom('function-call-update-market-history')
        return self.__room_call_market_update

    def _reset_thread_market_update(self) -> None:
        self.__thread_market_update = None

    def _get_thread_market_update(self) -> threading.Thread:
        """
        To get thread that mannage update of maket histories\n
        Returns:
        --------
        return: threading.Thread
            The thread that mannage update of maket histories
        """
        if self.__thread_market_update is None:
            base_name = self._THREAD_NAME_UPDATE_MARKET
            new_thread = self._generate_thread(
                self._manage_update_market_histories, base_name, output=True)
            self.__thread_market_update = new_thread
        return self.__thread_market_update

    def _reset_market_reset_times(self) -> None:
        self.__market_reset_times = None

    def _get_market_reset_times(self) -> Map:
        """
        To get list of next reset time (in second) of market history for each stream

        Returns:
        --------
        return: Map
            List of next reset time (in second)
            Map[stream{str}]: {int}
        """
        if self.__market_reset_times is None:
            self.__market_reset_times = Map()
        return self.__market_reset_times

    def _set_market_reset_time(self, stream: str) -> None:
        """
        To set next reset time (in second) of market history for the given stream

        Parameters:
        -----------
        stream: str
            Stream to use to set reset time
        """
        interval = self.get_market_reset_interval()
        unix_time = _MF.get_timestamp()
        next_reset = unix_time + interval
        self._get_market_reset_times().put(next_reset, stream)

    def _get_market_reset_time(self, stream: str) -> int:
        """
        To get next reset time (in second) of market history of the given stream

        Parameters:
        -----------
        stream: str
            Stream to use to get reset time

        Returns:
        --------
        return: int
            Next reset time (in second) of the given stream
            NOTE: reset_time = 0 If reset time don't exist
        """
        reset_time = self._get_market_reset_times().get(stream)
        reset_time = 0 if reset_time is None else reset_time
        return reset_time

    def _reset_thread_run_manager(self) -> None:
        self.__thread_run_manager = None

    def _get_thread_run_manager(self) -> threading.Thread:
        """
        To get thread that manage BinanceSocket's connection to Binance's websocket API

        Returns:
        --------
        return: threading.Thread
            Thread that manage BinanceSocket's connection
        """
        if self.__thread_run_manager is None:
            base_name = self._THREAD_NAME_RUN_MANGER
            new_thread = self._generate_thread(
                self._manage_run, base_name, output=True)
            self.__thread_run_manager = new_thread
        return self.__thread_run_manager

    # ——————————————————————————————————————————— SELF GETTER/SETTER FUNCTION UP ———————————————————————————————————————
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ———————————————————————————————————————————————————
    # ——————————————————————————————————————————— OTHER DOWN

    def urls(self) -> Map:
        """
        To get urls of active WebSocket

        Returns:
        --------
        return: Map
            Urls of active WebSocket else empty collection if no websocket is running
            Map[WebSocket.id]: {str}
        """
        wss = self._get_websockets()
        urls = Map()
        for ws_id, ws in wss.get_map().items():
            urls.put(ws.get_url(), ws_id)
        return urls
    
    def url(self, stream: str) -> str:
        """
        To get URL of the websocket cotaining the given stream

        Parameters:
        -----------
        stream: str
            Stream in socket's URL

        Returns:
        --------
        return: str
            URL of the websocket cotaining the given stream else None if no websocket is running
        """
        self.check_stream(stream)
        urls = self.urls()
        found = None
        if len(urls.get_map()) > 0:
            for _, url in urls.get_map().items():
                if stream in url:
                    found = url
                    break
            if found is None:
                raise Exception(f"There's no URL with this stream '{stream}'")
        return found

    def _load_streams(self) -> None:
        """
        To prepare streams to add in WebSocket
        1. push this.new_streams in this.streams
        2. reset this.new_streams
        """
        new_streams = self.get_new_streams().copy()
        self._reset_new_streams()
        self._add_streams(new_streams)

    def all_streams(self) -> list:
        """
        To get all streams
        - Merge list of streams added and streams to add
        - Remove duplicates

        Returns:
        --------
        return: list
            All streams
        """
        all_streams = [*self.get_streams(), *self.get_new_streams()]
        return _MF.remove_duplicates(all_streams)

    def _websocket_are_running(self) -> bool:
        """
        To check if all WebSocket established and are maintaining a connection
        
        Returns:
        --------
        return: bool
            True if all WebSocket established and are maintaining a connection else False
        """
        wss = self._get_websockets()
        not_running = [1 for _, ws in wss.get_map().items() if not ws.is_running()]
        are_running = (len(wss.get_map()) > 0) and (sum(not_running) == 0)
        return are_running

    def _new_websocket(self, streams: list) -> WebSocket:
        """
        To create new WebSocket

        Parameters:
        -----------
        streams: list
            Streams to use in URL

        Returns:
        --------
        return: WebSocket
            New WebSocket using given streams
        """
        from websocket import WebSocketApp

        def on_open(socket: WebSocketApp) -> None:
            _MF.output(f"{_MF.prefix()}on_open: connection established...") if BinanceSocket._DEBUG else None

        def on_error(socket: WebSocketApp, error: Exception) -> None:
            _MF.output(f"{_MF.prefix()}on_error: {error}") if BinanceSocket._DEBUG else None

        def on_close(socket: WebSocketApp, status_code: int, close_msg: str) -> None:
            _MF.output(f"{_MF.prefix()}on_close: connection closed.") if BinanceSocket._DEBUG else None

        def on_data(socket: WebSocketApp, message: str, data_type: str, flag: int) -> None:
            unix_date = _MF.unix_to_date(_MF.get_timestamp())
            _MF.output(f"{_MF.prefix()}on_data: last response '{unix_date}'.") if BinanceSocket._VERBOSE else None

        def on_message(socket: WebSocketApp, message: str) -> None:
            def kline(pay_load: dict) -> None:
                def milli_to_date(milli) -> str:
                    return _MF.unix_to_date(int(milli/1000))
                
                def compare_time() -> str:
                    equal = new_row[-1][0] == market_hist[-1][0]
                    return f"new_row(Time) == market_hist(Time) ('{equal}'): '{milli_to_date(new_row[-1][0])}' == '{milli_to_date(market_hist[-1][0])}'"
                
                def print_end() -> None:
                    _MF.output(f"{_MF.prefix()}kline: new close[-1] '{new_row[-1, 4]}'.") if BinanceSocket._VERBOSE else None
                    _MF.output(f"{_MF.prefix()}kline: history close[-1] '{market_hists.get(stream)[-1, 4]}'.") if BinanceSocket._VERBOSE else None
                    _MF.output(f"{_MF.prefix()}kline: history close[-2] '{market_hists.get(stream)[-2, 4]}'.") if BinanceSocket._VERBOSE else None

                rq = BinanceAPI.RQ_KLINES
                symbol = pay_load['s']
                period_str = pay_load['k']['i']
                stream = self.generate_stream(rq, symbol, period_str)
                if self._can_update_market_history(stream) \
                    and (stream not in self._get_room_market_update().get_tickets()):
                    self._update_market_history(stream)
                else:
                    new_row = [
                        pay_load['k']['t'],    # 0.  Open time
                        pay_load['k']['o'],    # 1.  Open Price
                        pay_load['k']['h'],    # 2.  High Price
                        pay_load['k']['l'],    # 3.  Low Price
                        pay_load['k']['c'],    # 4.  Close Price
                        pay_load['k']['v'],    # 5.  Base asset volume (right)
                        pay_load['k']['T'],    # 6.  Close time
                        pay_load['k']['q'],    # 7.  Quote asset volume (left)
                        pay_load['k']['n'],    # 8.  Number of trades
                        pay_load['k']['V'],    # 9.  Taker buy base asset volume
                        pay_load['k']['Q'],    # 10. Taker buy quote asset volume
                        pay_load['k']['B'],    # 11. Ignore
                        ]
                    market_hists = self._get_market_histories()
                    market_hist = market_hists.get(stream)
                    new_row = np.array(new_row, dtype=np.float64)
                    new_row = new_row.reshape((1, market_hist.shape[1]))
                    print(_MF.prefix() + compare_time()) if BinanceSocket._VERBOSE else None
                    if new_row[-1][0] == market_hist[-1][0]:   # compare open time
                        print(_MF.prefix() + f"REPLACE LAST") if BinanceSocket._VERBOSE else None
                        market_hist[-1] = new_row
                    else:
                        print(_MF.prefix() + f"RESET ALL") if BinanceSocket._VERBOSE else None
                        new_market_hist = np.vstack((market_hist, new_row))
                        market_hists.put(new_market_hist, stream)
                    print_end() if BinanceSocket._VERBOSE else None

            def root_event(event: str, pay_load: dict) -> None:
                if event == 'kline':
                    kline(pay_load)
                else:
                    raise ValueError(f"on_message: this event '{event}' is not supported (message='{message}')")

            def handle_event() -> None:
                decoded = _MF.json_decode(message)
                n_row = len(decoded)
                if (n_row == 2) and (Map.stream in decoded) and (Map.data in decoded):
                    pay_load = decoded[Map.data]
                elif 'e' in decoded:
                    pay_load = decoded
                else:
                    raise ValueError(f"on_message: can't handle event's message: '{message}'")
                event = pay_load['e']
                root_event(event, pay_load)

            base_name = self._THREAD_NAME_WEBSOCKET_EVENT_HANDLER
            self._generate_thread(handle_event, base_name, output=False).start()

        # Create WebSocket
        url = self._generate_url(streams)
        handlers = {
            Map.on_open: on_open,
            Map.on_message: on_message,
            Map.on_error: on_error,
            Map.on_close: on_close,
            Map.on_data: on_data
        }
        ws = WebSocket(url, **handlers)
        self._add_websocket(ws)
        return ws

    def _new_websockets(self, streams: list) -> List[WebSocket]:
        """
        To create and get list of new WebSocket

        Parameters:
        -----------
        streams: list
            Streams to use

        Returns:
        --------
        return: List[WebSocket]
            List of new WebSocket
        """
        stream_groups = self._group_streams(streams)
        wss = []
        for streams in stream_groups:
            ws = self._new_websocket(streams)
            wss.append(ws)
        return wss

    # ——————————————————————————————————————————— OTHER UP
    # ——————————————————————————————————————————— MARKET HISTORY DOWN

    def _can_update_market_history(self, stream: str) -> bool:
        """
        To check if market history of the given stream can be updated

        Parameters:
        -----------
        stream: str
            Stream to treat with

        Returns:
        --------
        return: int
            True if market history can be updated else False
        """
        reset_time = self._get_market_reset_time(stream)
        unix_time = _MF.get_timestamp()
        return unix_time >= reset_time

    def _update_market_history(self, stream: str) -> None:
        """
        To update market history\n
        Parameters:
        -----------
        stream: str
            Stream to update market history for
        """
        call_room = self._get_room_call_market_update()
        ticket = call_room.join_room()
        while not call_room.my_turn(ticket):
            time.sleep(0.1)
        if self._can_update_market_history(stream):
            thread_market = self._get_thread_market_update()
            market_room = self._get_room_market_update()
            if thread_market.is_alive():
                market_room.join_room(stream) if stream not in market_room.get_tickets() else None
            else:
                market_room.join_room(stream)
                thread_market.start()
        call_room.treat_ticket(ticket) if ticket in call_room.get_tickets() else None

    def _manage_update_market_histories(self) -> None:
        """
        To manage update of market histories
        """
        market_room = self._get_room_market_update()
        while market_room.next() is not None:
            stream = market_room.next()
            is_success = self._set_market_history(stream, raise_error=False)
            self._set_market_reset_time(stream) if is_success else None
            market_room.treat_ticket(stream) if stream in market_room.get_tickets() else None
        self._reset_thread_market_update()

    # ——————————————————————————————————————————— MARKET HISTORY UP
    # ——————————————————————————————————————————— MANAGE RUN DOWN

    def run(self) -> None:
        """
        To establish connection to stream through WebSocket
        """
        def prepare_market_histories() -> None:
            self._load_streams()
            streams = self.get_streams()
            for stream in streams:
                if self._set_market_history(stream, raise_error=True):
                    self._set_market_reset_time(stream)

        if self.is_running():
            raise Exception("Connection is already active")
        prepare_market_histories()
        self._turn_on()
        wait_time = 0
        max_wait_time = self.get_run_restart_interval()
        while not self._websocket_are_running():
            if (wait_time == 0) or (wait_time % max_wait_time == 0):
                self._reset_thread_run_manager()
                thread_run = self._get_thread_run_manager()
                thread_run.start()
            else:
                time.sleep(1)
            wait_time += 1

    def close(self) -> None:
        """
        To close WebSocket connections
        """
        self._turn_off()
        self._reset_room_call_market_update()
        self._reset_room_market_update()
        self._reset_market_histories()
        self._reset_market_reset_times()
        # self._reset_streams()

    def _manage_run(self) -> None:
        """
        To manage to connection to Binance's websocket API
        """
        _normal = '\033[0m'
        _purple = '\033[35m'
        _yellow = '\033[33m'
        _green = '\033[32m'
        _red = '\033[31m'
        def output(key: str, **kwargs) -> str:
            if key ==  "A":
                _MF.output(f"{pfx()}" + _purple + _MF.thread_infos() + _normal) if BinanceSocket._DEBUG else None
            elif key == "B":
                # WebSocket
                wss = self._get_websockets()
                n_wss = len(wss.get_map())
                n_running = len([1 for _, ws in wss.get_map().items() if ws.is_running()])
                # Market Call Room
                n_call = len(self._get_room_call_market_update().get_tickets())
                # Market Room
                n_market_reset = len(self._get_room_market_update().get_tickets())
                msg = f"Running_WebSocket: ({n_running}/{n_wss}) == Call_Room: ({n_call}) == Update_Room: ({n_market_reset})"
                _MF.output(f"{pfx()}" + _purple + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "C0":
                n_closed = kwargs[Map.close]
                msg = f"Maintaining connection of '{n_closed}' closed WebSocket..."
                _MF.output(f"{pfx()}" + _yellow + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "C1":
                msg = "End maintain of connection"
                _MF.output(f"{pfx()}" + _green + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "D0":
                streams = kwargs[Map.stream]
                n_stream = len(streams)
                msg = f"Adding '{n_stream}' new stream: {streams}"
                _MF.output(f"{pfx()}" + _yellow + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "D1":
                streams = kwargs[Map.stream]
                n_stream = len(streams)
                failed = kwargs[Map.market]
                run_stopped = kwargs[Map.stop]
                msg = f"Failed to add '{n_stream}' new stream: reason (failed={failed}, stop_signal='{run_stopped}')"
                _MF.output(f"{pfx()}" + _red + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "D2":
                streams = kwargs[Map.stream]
                n_stream = len(streams)
                msg = f"End add of '{n_stream}' new stream: {streams}"
                _MF.output(f"{pfx()}" + _green + msg + _normal) if BinanceSocket._DEBUG else None
            elif key == "E0":
                n_socket = kwargs[Map.close]
                msg = f"Closed '{n_socket}' sockets"
                _MF.output(f"{pfx()}" + _green + msg + _normal) if BinanceSocket._DEBUG else None

        def thread_websocket_manager(f_websocket: WebSocket) -> threading.Thread:
            base_name = self._THREAD_NAME_WEBSOCKET_MANGER
            return self._generate_thread(f_websocket.run, base_name, output=True)

        def thread_add_streams() -> threading.Thread:
            base_name = self._THREAD_NAME_RUN_ADD_STREAM
            return self._generate_thread(add_streams, base_name, output=True)

        def run_websockets(f_wss: List[WebSocket]) -> None:
            def are_running(f_wss: List[WebSocket], f_n_wss: int) -> bool:
                return sum([1 for f_ws in f_wss if f_ws.is_running()]) == f_n_wss

            n_wss = len(f_wss)
            for ws in f_wss:
                ws_thread = thread_websocket_manager(ws)
                ws_thread.start()
            i = 0
            timeout = self.get_websocket_run_timeout()
            while (not are_running(f_wss, n_wss)) and (i <= timeout):
                time.sleep(1)
                i += 1
            if i >= timeout:
                raise Exception(f"Can't run websockets")

        def establish_connection() -> None:
            """
            To Create new WebSocket and run them
            """
            # self._load_streams()
            streams  = self.get_streams()
            wss = self._new_websockets(streams)
            run_websockets(wss)

        def maintain_connection() -> None:
            """
            To relunch closed WebSocket
            """
            def get_closeds() -> List[WebSocket]:
                f_wss = self._get_websockets()
                return [f_ws for _, f_ws in f_wss.get_map().items() if not f_ws.is_running()]

            ws_closeds = get_closeds()
            output("C0", **{Map.close: len(ws_closeds)})
            [ws.close() for ws in ws_closeds]
            run_websockets(ws_closeds)
            output("C1")

        def add_streams() -> None:
            """
            To add new stream
            """
            def get_last_websocket() -> WebSocket:
                f_wss = self._get_websockets()
                f_ws_ids = f_wss.get_keys()
                f_last_ws = f_wss.get(f_ws_ids[-1])
                return f_last_ws

            new_streams = self.get_new_streams().copy()
            output('D0', **{Map.stream: new_streams})
            self._load_streams()
            # Load market histories
            faileds = [new_stream for new_stream in new_streams if (not self.is_running()) or (not self._set_market_history(new_stream, raise_error=False))]
            failed = (len(faileds) > 0)
            run_stopped = (not self.is_running())
            if failed or run_stopped:
                output('D1', **{Map.stream: new_streams,
                                Map.market: failed,
                                Map.stop: run_stopped
                                })
                self._delete_streams(new_streams)
                return None
            # Close last WebSocket
            last_ws = get_last_websocket()
            url_streams = self.url_to_streams(last_ws.get_url())
            self._delete_websocket(last_ws.get_id())
            # Run new WebSocket
            real_new_streams = _MF.remove_duplicates([*url_streams, *new_streams])
            real_new_streams.sort()
            new_wss = self._new_websockets(real_new_streams)
            run_websockets(new_wss)
            thd_add_streams = None
            output('D2', **{Map.stream: real_new_streams})

        def close_connection() -> None:
            """
            To close WebSocket
            """
            wss = self._get_websockets()
            ws_ids = wss.get_keys()
            n_closed = len([self._delete_websocket(ws_id) for ws_id in ws_ids if wss.get(ws_id).is_running()])
            output("E0", **{Map.close: n_closed})

        pfx = _MF.prefix
        thd_add_streams = None
        while self.is_running():
            output("A")
            output("B")
            if not self._websocket_are_running():
                establish_connection() if (len(self._get_websockets().get_map()) == 0) else maintain_connection()
            if (len(self.get_new_streams()) > 0) and ((thd_add_streams is None) or (not thd_add_streams.is_alive())):
                thd_add_streams = thread_add_streams()
                thd_add_streams.start()
            time.sleep(1)
        # End
        close_connection()
        self._reset_thread_run_manager()

    # ——————————————————————————————————————————— MANAGE RUN UP
    # ——————————————————————————————————————————— SELF FUNCTION UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION DOWN ———————————————————————————————————

    @staticmethod
    def get_regex_stream() -> str:
        return BinanceSocket._REGEX_STREAM

    @staticmethod
    def get_market_reset_interval() -> int:
        """
        To get time interval between each reset of market history

        Returns:
        --------
        return: int
        """
        return BinanceSocket._MARKET_RESET_INTEVAL

    @staticmethod
    def get_format_stream() -> str:
        return BinanceSocket._FORMAT_STREAM

    @staticmethod
    def get_run_restart_interval() -> int:
        """
        To get time to wait (in second) to establish connection or generate a new thread to retry

        Returns:
        --------
        returns: int
            Time to wait (in second) to establish connection
        """
        return BinanceSocket._RESTART_INTERVAL_RUN_MANAGER

    @staticmethod
    def get_websocket_max_stream() -> int:
        """
        To get max number of stream allowed in a WebSocket connection

        Returns:
        --------
        return: int
            The max number of stream allowed in a WebSocket connection
        """
        return BinanceSocket._WEBSOCKET_MAX_STREAM

    @staticmethod
    def get_websocket_run_timeout() -> int:
        """
        TO get time to wait for WebSocket to run

        Returns:
        --------
        return: int
            Time to wait for WebSocket to run
        """
        return BinanceSocket._WEBSOCKET_RUN_TIMEOUT

    @staticmethod
    def get_url_base() -> str:
        """
        To get URL without any path

        Returns:
        --------
        return: str
            URL without any path
        """
        return BinanceSocket._URL_BASE

    @staticmethod
    def get_url_path_single_stream() -> str:
        """
        To get URL's path for a one stream connection

        Returns:
        --------
        return: str
            URL's path for a one stream connection
        """
        return BinanceSocket._URL_PATH_SINGLE_STREAM

    @staticmethod
    def get_url_path_multiple_stream() -> str:
        """
        To get URL's path for a multiple stream connection

        Returns:
        --------
        return: str
            URL's path for a multiple stream connection
        """
        return BinanceSocket._URL_PATH_MULTIPLE_STREAM

    @staticmethod
    def get_url_stream_separator() -> str:
        """
        To get separator to place between URL's streams

        Returns:
        --------
        return: str
            Separator to place between URL's streams
        """
        return BinanceSocket._URL_STREAM_SEPARATOR

    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION UP —————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @staticmethod
    def check_stream(stream: str) -> bool:
        """
        To check if given stream match the correct format

        Parameters:
        -----------
        stream: str
            The stream to check

        Raises:
        -------
        raise: ValueError
            If stream don't match the correct format

        Returns:
        --------
        return: bool
            True if given stream match the correct format else raise Exception
        """
        regex = BinanceSocket.get_regex_stream()
        match_format = _MF.regex_match(regex, stream)
        if not match_format:
            raise ValueError(
                f"The stream '{stream}' must match regex '{regex}'")
        return match_format

    @staticmethod
    def generate_stream(rq: str, symbol: str, period_str: str) -> str:
        """
        To generate Binance stream\n
        Parameters
        ----------
        rq: str
            The request
        symbol: str
            Binance's symbol, i.e.: 'DOGEUSDT', 'BTCEUR', etc...
        period_str: str
            Period interval in string, i.e.: '1m', '1M', '3d', etc...
        Returns
        -------
        stream: str
            Binance stream
        """
        _cls = BinanceSocket
        _cls_parent = BinanceAPI
        if rq != BinanceAPI.RQ_KLINES:
            raise ValueError(f"Can't generate stream for this request '{rq}'.")
        if period_str not in _cls_parent.get_intervals().get_keys():
            raise ValueError(f"This period '{period_str}' is not supported")
        stream_format = _cls.get_format_stream()
        symbol = symbol.lower()
        stream = stream_format.replace(f'${Map.symbol}', symbol).replace(f'${Map.interval}', period_str)
        _cls.check_stream(stream)
        return stream

    @staticmethod
    def _generate_thread(target, base_name: str, output: bool = False) -> threading.Thread:
        _cls = BinanceSocket
        thread_name = _MF.generate_thread_name(base_name, 5)
        wrap = _MF.catch_exception
        kwargs = {
            'callback': target,
            'call_class': _cls.__name__,
            'repport': True
            }
        new_thread = threading.Thread(target=wrap, name=thread_name, kwargs=kwargs)
        _MF.output(f"{_MF.prefix()}New Thread '{thread_name}'!"
              ) if output and _cls._DEBUG else None
        return new_thread

    @staticmethod
    def split_stream(stream: str) -> Tuple[str, str]:
        """
        To get stream's symbol and period (in string)

        Parameters:
        -----------
        stream: str
            The stream to split

        Returns:
        --------
        retrun: Tuple[str, str]
            Stream's symbol and period
            Tuple[0]:   {str}   # stream's symbol
            Tuple[1]:   {str}   # stream's period in string
        """
        BinanceSocket.check_stream(stream)
        stream_format = BinanceSocket.get_format_stream()
        format_separator = stream_format.replace(f'${Map.symbol}', '').replace(
            f'${Map.interval}', '')
        symbol, period_str = tuple(stream.split(format_separator))
        return (symbol, period_str)

    @staticmethod
    def _group_streams(streams: list) -> List[list]:
        """
        To group streams following API's URL constraints

        Parameters:
        -----------
        streams: list
            Streams to group

        Returns:
        --------
        return: List[list]
            List of group of streams
        """
        _cls = BinanceSocket
        streams = streams.copy()
        url_max = WebSocket.get_url_max_length()
        url_base = _cls.get_url_base() + _cls.get_url_path_multiple_stream()
        max_stream = _cls.get_websocket_max_stream()
        separator_len = len(_cls.get_url_stream_separator())
        stream_groups = []
        while len(streams) != 0:
            stream_group = []
            remain_char = url_max - len(url_base)
            while (len(streams) != 0) and (remain_char > 0) and (len(stream_group) < max_stream):
                stream = streams[0]
                remain_char -= (len(stream) + separator_len)
                if remain_char >= 0:
                    stream_group.append(stream)
                    idx = streams.index(stream)
                    del streams[idx]
            stream_groups.append(stream_group)
        return stream_groups

    @staticmethod
    def _generate_url(streams: list) -> str:
        """
        To generate URL for WebSocket

        Parameters:
        -----------
        streams: list
            List of streams to place in URL

        Returns:
        --------
        return: str
            URL for WebSocket
        """
        _cls = BinanceSocket
        n_stream = len(streams)
        if not (1 <= n_stream <= _cls.get_websocket_max_stream()):
            max_stream = _cls.get_websocket_max_stream()
            raise ValueError(f"The number of stream in URL must be in domain [1, '{max_stream}'], instead n_streams='{n_stream}'")
        url = _cls.get_url_base()
        if n_stream == 1:
            url_path = _cls.get_url_path_single_stream()
            url += url_path + streams[0]
        elif n_stream > 1:
            url_path = _cls.get_url_path_multiple_stream()
            separator = _cls.get_url_stream_separator()
            streams_str = separator.join(streams)
            url += url_path + streams_str
        return url

    @staticmethod
    def url_to_streams(url: str) -> list:
        """
        To extract stream from URL

        Parameters:
        -----------
        url: str
            URL containing stream
        
        Returns:
        --------
        return: list
            List of streams from URL
        """
        _cls = BinanceSocket
        if not isinstance(url, str):
            raise TypeError(f"The url must be of type string, instead type='{type(url)}'")
        base_url = _cls.get_url_base()
        single_path = _cls.get_url_path_single_stream()
        combined_path = _cls.get_url_path_multiple_stream()
        separator = _cls.get_url_stream_separator()
        streams = url.replace(base_url, '').replace(single_path, '').replace(combined_path, '').split(separator)
        return streams

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
