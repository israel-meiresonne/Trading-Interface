import time
import threading
from typing import List

from websocket import WebSocketApp

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
    _CONST_MARKET_RESET_INTERVAL = 60 * 20  # in second
    _CONST_MAX_SIZE_SOCKET_LIST = 25
    _CONST_MAX_RETRY_ADD_NEW_STREAM = 10
    _CONST_MARKET_NETWORK_MAX_RETRY = 60 * 60
    _CONST_MAX_WAIT_START_SOCKET = 60
    _CONST_MAX_INTERVAL_TWO_SOCKET_RESPONSE = 30
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
    _NB_INSTANCE = None

    def __init__(self, streams: List[str], run_forever: bool = False):
        if BinanceSocket._NB_INSTANCE is not None:
            raise Exception("Can't instantiate more than 1 BinanceSocket")
        BinanceSocket._NB_INSTANCE = 1
        self.__url = None
        self.__streams = None
        self.__new_streams = None
        self.__restart = True
        self.__active = False
        self.__socket = None
        self.__socket_last_response = None
        self.__sockets = None
        self.__thread = None
        self._set_streams(streams)
        self._run_forever() if run_forever else None

    def _init_market_historics(self) -> None:
        """
        To retrieve market historic if there's new stream or if it's time to reset market historic of existing streams\n
        """
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
        api_keys = BinanceAPI.get_default_api_keys()
        test_mode = False
        rq = BinanceAPI.RQ_KLINES
        market_hists = self._get_market_historics()
        end = False
        i = 1
        while not end:
            try:
                bkr_rsp = BinanceAPI._waitingroom(test_mode, api_keys, rq, Map({
                    Map.symbol: symbol.upper(),
                    Map.interval: period_str,
                    Map.limit: BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD
                }))
                end = bkr_rsp.get_status_code() is not None
            except Exception as error:
                print(_MF.prefix() + f"Network error when getting market historic n°'{i}'")
                from model.structure.Bot import Bot
                Bot.save_error(error, BinanceSocket.__name__)
                current_thread = threading.current_thread()
                if BinanceSocket._THREAD_BASE_SOCKET_ON_MESSAGE_HANDLER in current_thread.name:
                    end = True
                else:
                    end = i > BinanceSocket._CONST_MARKET_NETWORK_MAX_RETRY
                    i += 1
                    time.sleep(1)
        content_market = bkr_rsp.get_content()
        market_hists.put(content_market, stream)

    @staticmethod
    def _get_market_historics() -> Map:
        if BinanceSocket._MARKET_HISTORIC is None:
            BinanceSocket._MARKET_HISTORIC = Map()
        return BinanceSocket._MARKET_HISTORIC

    def get_market_historic(self, stream: str) -> List[list]:
        market_hists = self._get_market_historics()
        market_hist = market_hists.get(stream)
        market_hist_copy = [row.copy() for row in market_hist]
        return market_hist_copy

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

    def add_streams(self, to_add_streams: List[str]) -> bool:
        """
        To add new streams\n
        Parameters
        ----------
        to_add_streams: List[str]
            Stream to add
        Returns
        -------
        stream_added: bool
            True if new stream is added else  False
        """
        stream_added = False
        old_streams = self.get_streams()
        new_streams = [stream for stream in to_add_streams if stream not in old_streams]
        if len(new_streams) > 0:
            new_streams_cleaned = _MF.remove_duplicates(new_streams)
            stream_added = self._manage_add_stream(new_streams_cleaned)
        return stream_added

    def _manage_add_stream(self, new_streams: List[str]) -> bool:
        _cls = BinanceSocket
        stream_added = False
        nb_pushed = len([self._push_new_stream(new_stream) for new_stream in new_streams])
        print(_MF.prefix() + f"Pushed '{nb_pushed}' new stream in new stream list")
        try:
            nb_added = 1
            for new_stream in new_streams:
                i = 1
                add_msg_str = f"{new_stream}({nb_added}/{nb_pushed})"
                while (new_stream not in self._get_market_historics().get_keys()) or (not self.is_active()):
                    print(_MF.prefix() + f"Waiting for new stream '{add_msg_str}' to be add "
                                         f"in market historic n°'{i}'...")
                    if i > _cls._CONST_MAX_RETRY_ADD_NEW_STREAM:
                        raise Exception(f"Max retry to add new stream '{add_msg_str}' in market historic")
                    else:
                        time.sleep(1)
                    i += 1
                print(_MF.prefix() + f"New stream '{add_msg_str}' added in market historic")
                nb_added += 1
            stream_added = True
        except Exception as error:
            from model.structure.Bot import Bot
            Bot.save_error(error, BinanceSocket.__name__)
        return stream_added

    def _reset_new_streams(self) -> None:
        self.__new_streams = None

    def get_new_streams(self) -> list:
        """
        To get list of new stream to add in running socket\n
        Returns
        -------
        new_streams: list
            List of new stream to add in running socket
        """
        if self.__new_streams is None:
            self.__new_streams = []
        return self.__new_streams

    def _push_new_stream(self, new_stream: str) -> None:
        """
        To push new stream in new streams list\n
        Parameters
        ----------
        new_stream: str
            Stream to add
        """
        new_streams = self.get_new_streams()
        new_streams.append(new_stream) if new_stream not in new_streams else None

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

        socket = WebSocketApp(url=url, header=header, cookie=cookie, subprotocols=subprotocols, on_open=on_open,
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

    def get_socket_url_streams(self) -> list:
        """
        To get list of streams in socket's url\n
        Returns
        -------
        streams: list
            List of streams in socket's url
        """
        socket = self.get_socket()
        url = socket.url
        base_url = BinanceSocket.get_base_url()
        single_path = BinanceSocket.get_single_steam_path()
        combined_path = BinanceSocket.get_combined_steam_path()
        streams = url.replace(base_url, '').replace(single_path, '').replace(combined_path, '').split('/')
        return streams

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
        max_interval = BinanceSocket._CONST_MAX_INTERVAL_TWO_SOCKET_RESPONSE
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
        running_socket_thread_name = None

        def generate_thread_socket_running() -> threading.Thread:
            print(f"{_MF.prefix()}Generating new Thread to run socket...") if BinanceSocket._DEBUG else None
            socket_thread_base = BinanceSocket._THREAD_BASE_SOCKET_RUNNING
            new_socket_thread = threading.Thread(target=self.get_socket().run_forever,
                                             name=_MF.generate_thread_name(socket_thread_base, 5))
            print(f"{_MF.prefix()}New Thread to run socket generated!") if BinanceSocket._DEBUG else None
            return new_socket_thread

        def reset_socket() -> threading.Thread:
            self.close()
            self._set_restart(can_restart=True)
            self._set_socket()
            return generate_thread_socket_running()

        def add_new_streams() -> None:
            old_socket_streams = self.get_streams()
            new_streams = list(self.get_new_streams())
            self._reset_new_streams()
            missing_streams = [stream for stream in new_streams if stream not in old_socket_streams]
            missing_streams_cleaned = _MF.remove_duplicates(missing_streams)
            new_socket_streams = [*old_socket_streams, *missing_streams_cleaned]
            self._set_streams(new_socket_streams)
            self._init_market_historics()

        socket_thread = generate_thread_socket_running()
        while self._can_restart():
            try:
                print(f"{prefix()}Managing socket...") if BinanceSocket._DEBUG else None
                print(f"{prefix()}" + '\033[35m' + _MF.thread_infos() + '\033[0m') if BinanceSocket._DEBUG else None
                if (not socket_thread.is_alive()) and (socket_thread.getName() != running_socket_thread_name):
                    # Is a new socket
                    print(f"{prefix()}Start socket runner thread") if BinanceSocket._DEBUG else None
                    socket_thread.start()
                    running_socket_thread_name = socket_thread.getName()
                elif not socket_thread.is_alive():
                    # Socket is dead
                    print(f"{prefix()}" + '\033[33m' + "Socket runner thread is dead... Generating a new one..."
                          + '\033[0m') \
                        if BinanceSocket._DEBUG else None
                    socket_thread = reset_socket()
                last_response = self.get_socket_last_response()
                response_date = _MF.unix_to_date(last_response) if last_response is not None else last_response
                print(f"{_MF.prefix()}Socket's last response: '{response_date}'") if BinanceSocket._DEBUG else None
                if self.socket_last_response_timeout():
                    print(f"{_MF.prefix()}"+'\033[33m' + '\033[4m' + "Socket response timeout reached!" + '\033[0m') \
                        if BinanceSocket._DEBUG else None
                    socket_thread = reset_socket()
                nb_new_stream = len(self.get_new_streams())
                if nb_new_stream > 0:
                    print(f"{_MF.prefix()}Adding '{nb_new_stream}' new streams...") if BinanceSocket._DEBUG else None
                    nb_stream = len(self.get_streams())
                    add_new_streams()
                    socket_thread = reset_socket()
                    nb_added_stream = len(self.get_streams()) - nb_stream
                    print(f"{_MF.prefix()}New streams added: '{nb_added_stream}'!") if BinanceSocket._DEBUG else None
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
    bnc_socket = BinanceSocket(streams, test_mode=False))
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
