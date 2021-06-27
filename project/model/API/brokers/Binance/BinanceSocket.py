import time
import threading
from typing import List

from websocket import WebSocketApp, enableTrace

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map


class BinanceSocket(BinanceAPI):
    _DEBUG = True
    _VERBOSE = False
    _BASE_URL = 'wss://stream.binance.com:9443'
    _PATH_SINGLE_STEAM = '/ws/'
    _PATH_COMBINED_STEAM = '/stream?streams='
    _STREAM_FORMAT_KLINE = '$symbol@kline_$interval'
    # Constants
    _CONST_MARKET_RESET_INTERVAL = 60 * 10              # in second
    _CONST_MAX_SIZE_SOCKET_LIST = 25
    _CONST_MAX_RETRY_ADD_NEW_STREAM = 60
    _CONST_MARKET_NETWORK_MAX_RETRY = 60 * 60
    _CONST_MAX_WAIT_START_SOCKET = 60
    _CONST_MAX_INTERVAL_TWO_SERVER_RESPONSE = 60
    _CONST_ADD_STREAM_TICKET_TOKEN = '_stream_ticket_'
    _CONST_ADD_STREAM_TICKET_REGEX = f'^.+{_CONST_ADD_STREAM_TICKET_TOKEN}.+$'
    _THREAD_BASE_SOCKET_ON_MESSAGE_HANDLER = 'socket_on_message_handler'
    _THREAD_BASE_SOCKET_MANAGER = 'socket_manager'
    _THREAD_BASE_SOCKET_RUNNING = 'socket_running'
    # Variables
    _MARKET_HISTORIC = None
    """
    # Stream format: 'dogeusdt@kline_1h'
    _MARKET_HISTORIC[binance_stream{str}]:    {List[List[str|float]]}
    """
    _MARKET_RESET_BOOK = None
    """
    # Stream format: 'dogeusdt@kline_1h'
    _MARKET_RESET_BOOK[binance_stream{str}]:    {int} # Next time to reset market historic for the stream
    """
    _ADD_STREAM_QUEUE = None

    def __init__(self, streams: List[str], api: BinanceAPI, run_forever: bool = False):
        self.__api = api
        self.__url = None
        self.__streams = None
        self.__restart = True
        self.__active = False
        self.__socket = None
        self.__socket_last_response = None
        self.__sockets = None
        self.__thread = None
        self._set_streams(streams)
        self._run_forever() if run_forever else None

    def _init_market_historics(self) -> None:
        # prelude = _MF.prefix() if thread_prelude is None else thread_prelude
        streams = self.get_streams()
        market_hists = self._get_market_historics()
        unix_time = _MF.get_timestamp()
        for stream in streams:
            next_reset_time = BinanceSocket.get_next_reset_time(stream)
            if (stream not in market_hists.get_keys()) or (unix_time >= next_reset_time):
                BinanceSocket.update_next_reset_time(stream)
                symbol, period_str = BinanceSocket.split_stream(stream)
                # """
                if BinanceSocket._DEBUG:
                    historic_setted = None
                    historic_reset = None
                    if stream not in market_hists.get_keys():
                        print(f"{_MF.prefix()}Set market historic for stream '{stream}'")
                        historic_setted = True
                    elif unix_time >= next_reset_time:
                        print(f"{_MF.prefix()}Reset market historic for stream '{stream}'")
                        historic_reset = True
                self._init_market_historic(stream, symbol, period_str)
                if BinanceSocket._DEBUG:
                    if (historic_setted is not None) and historic_setted:
                        print(f"{_MF.prefix()}End Set market historic for stream '{stream}'")
                    elif (historic_reset is not None) and historic_reset:
                        print(f"{_MF.prefix()}End Reset market historic for stream '{stream}'")
                # """

    def _init_market_historic(self, stream: str, symbol: str, period_str: str) -> None:
        api = self.get_api()
        rq = BinanceAPI.RQ_KLINES
        market_hists = self._get_market_historics()
        end = False
        i = 1
        while not end:
            try:
                bkr_rsp = api._send_request(rq, Map({
                Map.symbol: symbol.upper(),
                Map.interval: period_str,
                Map.limit: BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD
            }))
                end = bkr_rsp.get_status_code() is not None
            except Exception as error:
                print(_MF.prefix() + f"Network error when getting market historic n°'{i}'")
                from model.structure.Bot import Bot
                Bot.save_error(error, BinanceSocket.__name__)
                end = i > BinanceSocket._CONST_MARKET_NETWORK_MAX_RETRY
                i += 1
                time.sleep(1)
        content_market = bkr_rsp.get_content()
        market_hists.put(content_market, stream)

    def _get_market_historics(self) -> Map:
        if BinanceSocket._MARKET_HISTORIC is None:
            BinanceSocket._MARKET_HISTORIC = Map()
        return BinanceSocket._MARKET_HISTORIC

    def get_market_historic(self, stream: str) -> List[list]:
        market_hists = self._get_market_historics()
        market_hist = market_hists.get(stream)
        market_hist_copy = [row.copy() for row in market_hist]
        """
        if market_hist is None:
            max_retry = BinanceSocket._CONST_MAX_RETRY_GET_MARKET
            i = 0
            while (i < max_retry) and (market_hist is None):
                time_time(1) if i != 0 else None
                # print(f"{_MF.prefix()}get_market_historic's retry n°'{i+1}'.")
                market_hist = market_hists.get(stream)
                i += 1
                # time_time(1)
            if market_hist is None:
                raise Exception(f"Exceed maximum retry '{max_retry}' to get market historic for stream '{stream}'.")
        """
        return market_hist_copy

    def get_api(self) -> BinanceAPI:
        return self.__api

    def get_url(self) -> str:
        """
        To get Binance's web socket url\n
        """
        return self.__url

    def _generate_url(self) -> str:
        _cls = BinanceSocket
        streams = self.get_streams()
        url = _cls.get_base_url()
        nb = len(streams)
        if nb == 1:
            url_path = _cls.get_single_steam_path()
            url += url_path + streams[0]
        elif nb > 1:
            url_path = _cls.get_combined_steam_path()
            streams_str = '/'.join(streams)
            url += url_path + streams_str
        self.__url = url
        return url

    def _set_streams(self, streams: List[str]) -> None:
        if len(streams) < 1:
            nb = len(streams)
            raise Exception(f"The number of stream must be >= 1, instead '{nb}'.")
        self.__streams = streams

    def get_streams(self) -> List[str]:
        return self.__streams

    def add_streams(self, new_stream: str) -> bool:
        """
        To add new streams\n
        Parameters
        ----------
        new_stream: str
            Streams to add

        Returns
        -------
        stream_added: bool
            True if new stream is added else  False
        """
        # stream_added = False
        streams = self.get_streams()
        if new_stream in streams:
            raise ValueError(f"This stream '{new_stream}' already exist")
        else:
            stream_added = self._manage_add_stream(new_stream)
        return stream_added

    def _manage_add_stream(self, new_stream: str) -> bool:
        _cls = BinanceSocket
        stream_added = False
        stream_queue_ticket = _cls._join_add_stream_queue(new_stream)
        ticket_prefix = f"{stream_queue_ticket}| "
        print(_MF.prefix() + ticket_prefix + f"Get ticket to add new stream '{new_stream}'")
        try:
            i = 1
            while not _cls._my_turn_to_add_stream(stream_queue_ticket):
                print(_MF.prefix() + ticket_prefix + f"Waiting to add new stream '{new_stream}'")
                i += 1
                time.sleep(1)
                if i > _cls._CONST_MAX_RETRY_ADD_NEW_STREAM:
                    raise Exception(f"Max retry to add new stream '{new_stream}', ticket='{stream_queue_ticket}'")
            self._execute_add_streams(new_stream)
            _cls._quit_add_stream_queue(stream_queue_ticket)
            print(_MF.prefix() + ticket_prefix + f"Added new stream '{new_stream}'")
            stream_added = True
        except Exception as error:
            from model.structure.Bot import Bot
            Bot.save_error(error, BinanceSocket.__name__)
            _cls._quit_add_stream_queue(stream_queue_ticket)
        return stream_added

    def _execute_add_streams(self, new_stream: str) -> None:
        self.close()
        self.get_streams().append(new_stream)
        # streams = [*olds_streams, *to_add_streams]
        # streams
        # self._set_streams(streams)
        self._run_forever()

    def _set_restart(self, can_restart: bool) -> None:
        if not isinstance(can_restart, bool):
            raise ValueError(f"Params must be boolean, instead '{can_restart}'({type(can_restart)}).")
        self.__restart = can_restart

    def _can_restart(self) -> bool:
        """
        To get if class can restart when websocket perform a close event\n
        Returns
        -------
        restart: bool
            Set True to restart websocket on close event else False to still socket closed
        """
        return self.__restart

    def _set_active(self, is_started: bool) -> None:
        if not isinstance(is_started, bool):
            raise ValueError(f"New value must be boolean, instead '{is_started}'(type='{type(is_started)}')")
        self.__active = is_started

    def is_active(self) -> bool:
        """
        To get if websocket connection is active\n
        Returns
        -------
        active: bool
            True if connection is active else False
        """
        socket = self.get_socket()
        return self.__active and socket.keep_running and (socket.sock is not None)

    def _set_socket(self) -> None:
        print(f"{_MF.prefix()}Creating new socket...")
        _cls = BinanceSocket
        url = self._generate_url()
        header = None
        cookie = None
        subprotocols = None
        # thread_id = f"thread_{_MF.new_code()[0:5]}|"

        def on_open(socket: WebSocketApp) -> None:
            """
            Callback object which is called at opening websocket.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            """
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_open: connection established...") if BinanceSocket._DEBUG else None
            self._set_active(True)

        def on_error(socket: WebSocketApp, error: Exception) -> None:
            """
            Callback object which is called when we get error.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            error: Exception
                The exception object raised
            """
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_error: {error}") if BinanceSocket._DEBUG else None
            # from model.structure.Bot import Bot
            # Bot.save_error(error, BinanceSocket.__name__)

        def on_close(socket: WebSocketApp, status_code: int, close_msg: str) -> None:
            """
            Callback object which is called when connection is closed.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            status_code: int
                The close status code
            close_msg: str
                The close msg
            """
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_close: connection closed.") if BinanceSocket._DEBUG else None
            self._set_active(False)
            # self._reset_socket()
            self._reset_socket_last_response()

        def on_data(socket: WebSocketApp, message: str, data_type: str, flag: int) -> None:
            """
            Callback object which is called when a message received.\n
            This is called before on_message or on_cont_message,
            and then on_message or on_cont_message is called.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            message: str
                UTF-8 string which we get from the server.
            data_type: str
                The data type. ABNF.OPCODE_TEXT or ABNF.OPCODE_BINARY will be came.
            flag: int
                The continue flag. if 0, the data continue to next frame data
            """
            # date = _MF.prefix() + thread_id
            # print(f"{_MF.prefix()}on_data: '{message}'") if _cls._VERBOSE else None
            self._set_socket_last_response()

        def on_message(socket: WebSocketApp, message: str) -> None:
            """
            Callback object which is called when received data.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            message: str
                UTF-8 data received from the server
            """
            # date = _MF.prefix() + thread_id
            message_obj = _MF.json_decode(message)
            # prelude = f"{_MF.prefix()}on_message: "
            # print(f"{prelude}{type(message_obj)}, {len(message_obj)}")

            def print_status(status: str, **params) -> None:
                if False:
                    params = Map(params)
                    stream = params.get('stream')
                    next_reset_time = params.get('next_reset_time')
                    thread_ref = params.get('thread_ref')
                    rows = [{
                        Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                        'thread_ref': thread_ref,
                        Map.status: status,
                        'stream': stream,
                        'next_reset_time': _MF.unix_to_date(next_reset_time) if next_reset_time is not None else next_reset_time,
                        'message': message,  # params.get('message'),
                        'last_row': params.get('last_row'),
                        'new_row': params.get('new_row'),
                        'market_hists': self.get_market_historic(stream),
                        'stream_market_hist': params.get('stream_market_hist')
                    }]
                    fields = list(rows[0].keys())
                    path = f'content/v0.01/tests/{Config.get(Config.START_DATE)}/{BinanceSocket.__name__}.csv'
                    FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)
                    # print(f"{_MF.prefix()}|{thread_ref}|🖨 File print! ✅")

            def update_market_historic(market_row: dict) -> None:
                rq = BinanceAPI.RQ_KLINES
                symbol = market_row['s'].lower()
                period_str = market_row['k']['i']
                stream = BinanceSocket.generate_stream(rq, symbol, period_str)
                # thread_ref = f'tread_stream_{stream}_' + _MF.new_code(13)
                # thread_prelude = f"{prelude}|{thread_ref}| "
                # print(f"{_MF.prefix()}stream={stream}") if BinanceSocket._VERBOSE else None
                market_hists = self._get_market_historics()
                unix_time = _MF.get_timestamp()
                next_reset_time = BinanceSocket.get_next_reset_time(stream)
                print_status('initial', **vars())
                # Set or Reset market historic
                if unix_time >= next_reset_time:
                    BinanceSocket.update_next_reset_time(stream)
                    self._init_market_historics()
                print_status('after market Set|Reset', **vars())
                # Add new row historic
                new_row = [
                    market_row['k']['t'],    # 0.  Open time
                    market_row['k']['o'],    # 1.  Open
                    market_row['k']['h'],    # 2.  High
                    market_row['k']['l'],    # 3.  Low
                    market_row['k']['c'],    # 4.  Close
                    market_row['k']['v'],    # 5.  Base asset volume (right)
                    market_row['k']['T'],    # 6.  Close time
                    market_row['k']['q'],    # 7.  Quote asset volume (left)
                    market_row['k']['n'],    # 8.  Number of trades
                    market_row['k']['V'],    # 9.  Taker buy base asset volume
                    market_row['k']['Q'],    # 10. low
                    market_row['k']['B'],    # 11. low
                ]
                _MARKET_VERBOSE = _MF.prefix() + f"Stream time (stream='{stream}') (close='{new_row[4]}'): "\
                                                 f"'{new_row[0]}'->'{_MF.unix_to_date(int(new_row[0]/1000))}'"
                print(_MARKET_VERBOSE) if BinanceSocket._VERBOSE else None
                stream_market_hist = market_hists.get(stream)
                last_row = stream_market_hist[-1]
                if new_row[0] == last_row[0]:
                    # print(f"{thread_prelude}Replace market historic's last row: (new_row[0] == last_row[0] => '{new_row[0]}' == '{last_row[0]}')")
                    stream_market_hist[-1] = new_row
                else:
                    # print(f"{thread_prelude}Append new row in market historic: (new_row[0] != last_row[0] => '{new_row[0]}' != '{last_row[0]}')")
                    del stream_market_hist[0]
                    stream_market_hist.append(new_row)
                print_status('after market Replace|Append', **vars())

            def root_stream() -> None:
                if len(self.get_streams()) == 1:
                    update_market_historic(_MF.json_decode(message))
                else:
                    update_market_historic(_MF.json_decode(message)[Map.data])

            thread_name_on_msg = _MF.generate_thread_name(_cls._THREAD_BASE_SOCKET_ON_MESSAGE_HANDLER)
            threading.Thread(target=root_stream, name=thread_name_on_msg).start()

        def on_cont_message(socket: WebSocketApp, message: str, flag: int) -> None:
            """
            Callback object which is called when a continuation
            frame is received.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            message: str
                UTF-8 string which we get from the server.
            flag: int
                The continue flag. if 0, the data continue to next frame data
            """
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_cont_message") if _cls._VERBOSE else None

        def on_ping(socket: WebSocketApp, message: str) -> None:
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_ping: {message}") if _cls._VERBOSE else None

        def on_pong(socket: WebSocketApp, message: str) -> None:
            # date = _MF.prefix() + thread_id
            print(f"{_MF.prefix()}on_pong: {message}") if _cls._VERBOSE else None

        def get_mask_key(socket: WebSocketApp) -> None:
            """
            A callable function to get new mask keys, see the
            WebSocket.set_mask_key's docstring for more information.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            """
            # date = _MF.prefix() + thread_id
            # print(f"{date}get_mask_key")
            pass

        # enableTrace(True)
        socket = WebSocketApp(url, header=header, cookie=cookie, subprotocols=subprotocols, on_open=on_open,
                              on_message=on_message, on_error=on_error, on_close=on_close,
                              on_cont_message=on_cont_message, on_data=on_data, on_ping=on_ping, on_pong=on_pong,
                              get_mask_key=get_mask_key)
        self.__socket = socket
        self._set_active(False)
        self._push_socket(socket)
        print(f"{_MF.prefix()}New socket created!")

    def get_socket(self) -> WebSocketApp:
        # self._set_socket() if self.__socket is None else None
        return self.__socket

    def _push_socket(self, socket: WebSocketApp) -> None:
        self.get_sockets().append(socket)

    def get_sockets(self) -> List[WebSocketApp]:
        """
        To get get all socket ever created\n
        Returns
        """
        self.__sockets = [] if self.__sockets is None else self.__sockets
        return self.__sockets

    def _maintain_sockets(self) -> None:
        sockets = self.get_sockets()
        nb = len(sockets)
        max_size = BinanceSocket._CONST_MAX_SIZE_SOCKET_LIST
        if nb > max_size:
            del sockets[max_size:nb]

    def _reset_socket_last_response(self) -> None:
        self.__socket_last_response = None

    def _set_socket_last_response(self) -> None:
        """
        To sate the time of the last message received from the socket
        """
        unix_time = _MF.get_timestamp()
        self.__socket_last_response = unix_time

    def get_socket_last_response(self) -> int:
        return self.__socket_last_response

    def socket_last_response_timeout(self) -> bool:
        """"
        To check if the socket server keep sending message\n
        Returns
        ———————
        keep_responding: bool
            True if server keep responding else False
        """
        unix_time = _MF.get_timestamp()
        max_interval = BinanceSocket._CONST_MAX_INTERVAL_TWO_SERVER_RESPONSE
        last_response = self.get_socket_last_response()
        return (last_response is not None) and (unix_time > (last_response + max_interval))

    def _generate_thread_socket_manager(self) -> threading.Thread:
        print(f"{_MF.prefix()}Generating new Thread to manage socket...") if BinanceSocket._DEBUG else None
        thread_name_socket_manager = _MF.generate_thread_name(BinanceSocket._THREAD_BASE_SOCKET_MANAGER, 5)
        new_thread = threading.Thread(target=self._manage_run, name=thread_name_socket_manager)
        self._set_thread(new_thread)
        print(f"{_MF.prefix()}New Thread to manage socket generated!") if BinanceSocket._DEBUG else None
        return new_thread

    def _set_thread(self, thread: threading.Thread) -> None:
        """
        To set socket's thread\n
        Parameters
        ----------
        thread: Thread
            Thread where socket is run
        """
        self.__thread = thread

    def get_thread(self) -> threading.Thread:
        return self.__thread

    def _run_forever(self) -> None:
        """"
        sockopt = None
        sslopt = None
        ping_interval = 0
        ping_timeout = None
        ping_payload = ""
        http_proxy_host = None
        http_proxy_port = None
        http_no_proxy = None
        http_proxy_auth = None
        skip_utf8_validation = False
        host = None
        origin = None
        dispatcher = None
        suppress_origin = False
        proxy_type = None
        """
        self._init_market_historics()
        self._set_restart(can_restart=True)
        # thread_name_socket_manager = _MF.generate_thread_name(BinanceSocket._THREAD_BASE_SOCKET_MANAGER, 5)
        # th1 = threading.Thread(target=self._manage_run, name=thread_name_socket_manager)
        # self._set_thread(th1)
        th1 = self._generate_thread_socket_manager()
        self._set_socket()
        th1.start()
        i = 1
        while not self.is_active():
            print(f"{_MF.prefix()}Waiting for websocket to start n°'{i}'...") \
                if BinanceSocket._DEBUG else None
            i += 1
            if i % BinanceSocket._CONST_MAX_WAIT_START_SOCKET == 0:
                print(f"{_MF.prefix()}" + '\033[33m' + f"Max retry to start socket reached '{i}'" + '\033[0m')
                self.close()
                self._set_restart(can_restart=True)
                th1 = self._generate_thread_socket_manager()
                self._set_socket()
                th1.start()
            else:
                time.sleep(1)

    def _manage_run(self) -> None:
        prefix = _MF.prefix
        print(f"{prefix()}Start socket Manager") if BinanceSocket._DEBUG else None

        def generate_thread_socket_running() -> threading.Thread:
            print(f"{_MF.prefix()}Generating new Thread to run socket...") if BinanceSocket._DEBUG else None
            socket_thread_base = BinanceSocket._THREAD_BASE_SOCKET_RUNNING
            new_socket_thread = threading.Thread(target=self.get_socket().run_forever,
                                             name=_MF.generate_thread_name(socket_thread_base, 5))
            print(f"{_MF.prefix()}New Thread to run socket generated!") if BinanceSocket._DEBUG else None
            return new_socket_thread

        socket_thread = generate_thread_socket_running()

        def reset_socket() -> threading.Thread:
            self.close()
            self._set_restart(can_restart=True)
            self._set_socket()
            return generate_thread_socket_running()
        while self._can_restart():
            try:
                print(f"{prefix()}Managing socket...") if BinanceSocket._DEBUG else None
                print(f"{prefix()}" + '\033[35m' + _MF.thread_infos() + '\033[0m') if BinanceSocket._DEBUG else None
                socket_thread.start() if not socket_thread.is_alive() else None
                last_response = self.get_socket_last_response()
                response_date = _MF.unix_to_date(last_response) if last_response is not None else last_response
                print(f"{_MF.prefix()}Socket's last response: '{response_date}'") if BinanceSocket._DEBUG else None
                if self.socket_last_response_timeout():
                    print(f"{_MF.prefix()}"+'\033[33m' + '\033[4m' + "Socket response timeout reached!" + '\033[0m') \
                        if BinanceSocket._DEBUG else None
                    socket_thread = reset_socket()
            except Exception as socket_error:
                from model.structure.Bot import Bot
                Bot.save_error(socket_error, BinanceSocket.__name__)
                print(f"{prefix()}" + '\033[33m' + "Socket Manager crashed... Try restart new one..." + '\033[0m') \
                    if BinanceSocket._DEBUG else None
                socket_thread = reset_socket()
            time.sleep(1)
        print(f"{prefix()}End socket Manager.") if BinanceSocket._DEBUG else None

    def close(self) -> None:
        print(f"{_MF.prefix()}Ask to close socket...") if BinanceSocket._DEBUG else None
        self._set_restart(can_restart=False)
        self._reset_socket_last_response()
        socket = self.get_socket()
        socket.close()
        self._close_sockets()   # if self.is_active() else None
        self._set_active(False)
        self._maintain_sockets()
        print(f"{_MF.prefix()}All socket closed") if BinanceSocket._DEBUG else None

    def _close_sockets(self) -> None:
        sockets = self.get_sockets()
        closed = False
        i = 0
        while not closed:
            print(f"{_MF.prefix()}Waiting for websocket to close n°'{i}'...") \
                if (i != 0) and BinanceSocket._DEBUG else None
            a = [socket.close() for socket in sockets]
            close_status = [1 for socket in sockets if socket.keep_running or (socket.sock is not None)]
            closed = sum(close_status) == 0
            i += 1
            time.sleep(1) if not closed else None

    def _generate_close_message(self) -> str:
        streams = self.get_streams()
        close_message = {
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": 312
        }
        return _MF.json_encode(close_message)   # .encode('utf8')

    @staticmethod
    def get_base_url() -> str:
        return BinanceSocket._BASE_URL

    @staticmethod
    def get_single_steam_path() -> str:
        return BinanceSocket._PATH_SINGLE_STEAM

    @staticmethod
    def get_combined_steam_path() -> str:
        return BinanceSocket._PATH_COMBINED_STEAM

    @staticmethod
    def get_stream_format_kline() -> str:
        return BinanceSocket._STREAM_FORMAT_KLINE

    @staticmethod
    def split_stream(stream: str) -> tuple:
        stream_format = BinanceSocket.get_stream_format_kline()
        stream_format_base = stream_format.replace(f'${Map.symbol}', '').replace(f'${Map.interval}', '')
        stream_tuple = tuple(stream.split(stream_format_base))
        return stream_tuple

    @staticmethod
    def get_market_reset_interval() -> int:
        return BinanceSocket._CONST_MARKET_RESET_INTERVAL

    @staticmethod
    def generate_next_reset_time(time: int = None) -> int:
        reset_interval = BinanceSocket.get_market_reset_interval()
        unix_time = _MF.get_timestamp() if time is None else time
        unix_time_rounded = _MF.round_time(unix_time, reset_interval)
        next_reset = unix_time_rounded + reset_interval
        return next_reset

    @staticmethod
    def get_market_reset_book() -> Map:
        if BinanceSocket._MARKET_RESET_BOOK is None:
            BinanceSocket._MARKET_RESET_BOOK = Map()
        return BinanceSocket._MARKET_RESET_BOOK

    @staticmethod
    def get_next_reset_time(stream: str) -> int:
        reset_book = BinanceSocket.get_market_reset_book()
        next_reset_time = reset_book.get(stream)
        return next_reset_time

    @staticmethod
    def update_next_reset_time(stream: str) -> None:
        """
        To update the next time to reset market historic for the given stream\n
        Parameters
        ----------
        stream: str
            A active stream
        """
        next_reset = BinanceSocket.generate_next_reset_time()
        reset_book = BinanceSocket.get_market_reset_book()
        reset_book.put(next_reset, stream)

    @staticmethod
    def _get_add_stream_queue() -> list:
        if BinanceSocket._ADD_STREAM_QUEUE is None:
            BinanceSocket._ADD_STREAM_QUEUE = []
        return BinanceSocket._ADD_STREAM_QUEUE

    @staticmethod
    def _join_add_stream_queue(stream: str) -> str:
        """
        To join the queue to add new stream\n
        Parameters
        ----------
        stream: str
            Stream to add
        Returns
        -------
        ticket: str
            Stream ticket to wait your turn
        """
        ticket_token = BinanceSocket._CONST_ADD_STREAM_TICKET_TOKEN
        stream_queue_ticket = stream + ticket_token + _MF.new_code()[0:10]
        BinanceSocket._get_add_stream_queue().append(stream_queue_ticket)
        return stream_queue_ticket

    @staticmethod
    def _my_turn_to_add_stream(stream_queue_ticket: str) -> bool:
        """
        Check if stream ticket can add its stream to list of stream\n
        Parameters
        ----------
        stream_queue_ticket: str
            Stream ticket to check
        Returns
        -------
        is_my_turn: bool
            True if it's your turn else False
        """
        BinanceSocket._check_add_stream_queue(stream_queue_ticket)
        add_stream_queue = BinanceSocket._get_add_stream_queue()
        return stream_queue_ticket == add_stream_queue[0]

    @staticmethod
    def _quit_add_stream_queue(stream_queue_ticket: str) -> bool:
        """
        Remove ticket from add stream queue\n
        Parameters
        ----------
        stream_queue_ticket: str
            The stream ticket to remove form add stream queue

        Returns
        -------
        removed: str
            True if stream ticket removed with success else False
        """
        BinanceSocket._check_add_stream_queue(stream_queue_ticket)
        if not BinanceSocket._my_turn_to_add_stream(stream_queue_ticket):
            raise ValueError(f"It's not your turn '{stream_queue_ticket}'")
        add_stream_queue = BinanceSocket._get_add_stream_queue()
        add_stream_queue.pop(0)
        return stream_queue_ticket not in add_stream_queue

    @staticmethod
    def _check_add_stream_queue(stream_queue_ticket: str) -> None:
        add_stream_queue = BinanceSocket._get_add_stream_queue()
        if len(add_stream_queue) == 0:
            raise Exception(f"The add_stream_queue list is empty (stream_ticket='{stream_queue_ticket}')")
        ticket_regex = BinanceSocket._CONST_ADD_STREAM_TICKET_REGEX
        if not _MF.regex_match(ticket_regex, stream_queue_ticket):
            raise Exception(f"Stream queue ticket '{stream_queue_ticket}' must match ticket format '{ticket_regex}'")
        if stream_queue_ticket not in add_stream_queue:
            ValueError(f"Stream queue ticket '{stream_queue_ticket}' "
                       f"don't exist in add_stream_queue list '{add_stream_queue}'")

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
        if rq != BinanceAPI.RQ_KLINES:
            raise ValueError(f"Can't generate stream for this request '{rq}'.")
        stream_format = BinanceSocket.get_stream_format_kline()
        symbol = symbol.lower()
        # interval = rq_params.get(Map.interval)
        stream = stream_format.replace(f'${Map.symbol}', symbol).replace(f'${Map.interval}', period_str)
        return stream


if __name__ == '__main__':
    '''
    BinanceSocket._VERBOSE = True
    Config.update(Config.STAGE_MODE, Config.STAGE_2)
    rq = BinanceAPI.RQ_KLINES
    rq_params = Map({
        Map.symbol: 'DOGEUSDT',
        Map.interval: '1m'
    })
    symbol = 'DOGEUSDT'
    period_str = '1m'
    streams = [
        # BinanceSocket.generate_stream(rq, 'ADAUSDT', '1m'),
        # BinanceSocket.generate_stream(rq, 'ACMUSDT', '1m')#,
        BinanceSocket.generate_stream(rq, 'BTCUSDT', '1m')
    ]
    pk_k = 'mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5'
    sk_k = 'xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr'
    bnc_socket = BinanceSocket(streams, BinanceAPI(api_pb=pk_k, api_sk=sk_k, test_mode=False))
    bnc_socket._run_forever()
    th1 = bnc_socket.get_thread()
    end = False
    while not end:
        # print(f'{_MF.prefix()}is_alive', th1.is_alive())
        entry = input('Enter command control:\n').lower()
        if entry == 'end':
            bnc_socket.close()
            end = True
        elif entry == 'close':
            print(f'{_MF.prefix()}life before', th1.is_alive())
            bnc_socket.close()
            print(f'{_MF.prefix()}life after', th1.is_alive())
        elif entry == 'status':
            print(f'{_MF.prefix()}is_alive', th1.is_alive())
        elif entry == 'start':
            bnc_socket._run_forever()
            th1 = bnc_socket.get_thread()
            print('ran forever')
        elif entry == 'add':
            new_streams = input('Enter streams:\n')
            bnc_socket.add_streams(new_streams)
        elif entry == 'call':
            call_end = False
            while not call_end:
                try:
                    my_exec = input('Enter the function to call')
                    exec(my_exec)
                    # retured_value = exec(my_exec)
                    # print(f"returned value: '{retured_value}'")
                except Exception as e:
                    print(f"Exception: '{e}'")
    '''
    # symbol, period_str = BinanceSocket.split_stream('aaveusdt@kline_5m')
    # print(symbol, period_str)
