import inspect
from model.structure.database.ModelFeature import ModelFeature as _MF
from websocket import WebSocketApp
from model.tools.Map import Map


class WebSocket:
    PREFIX_ID = 'ws_'
    _URL_MAX_LENGTH = 8190

    def __init__(self, url, header=None, cookie=None, subprotocols=None,
                 on_open=None, on_message=None, on_error=None,
                 on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None, get_mask_key=None, on_data=None) -> None:
        self.__id = None
        self.__settime = None
        self.__websocket = None
        self._set_id()
        self._set_settime()
        self._set_websocket(url, header=header, cookie=cookie, subprotocols=subprotocols,
                            on_open=on_open, on_message=on_message, on_error=on_error,
                            on_close=on_close, on_ping=on_ping, on_pong=on_pong,
                            on_cont_message=on_cont_message, get_mask_key=get_mask_key,
                            on_data=on_data)

    # ——————————————————————————————————————————— SELF GETTER/SETTER FUNCTION DOWN —————————————————————————————————————

    def _set_id(self) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> None:
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)

    def get_settime(self) -> int:
        return self.__settime

    def _set_websocket(self, url: str, **kwargs) -> WebSocketApp:
        def check_event_handler(f_event_handler) -> None:
            if(f_event_handler is not None) and (not inspect.isfunction(f_event_handler)) and (not inspect.ismethod(f_event_handler)):
                raise TypeError(
                    f"The event handler must be a function or a method, instead type='{type(f_event_handler)}' (handler='{f_event_handler}')")

        def check_params(f_url: str, **f_kwargs) -> None:
            f_params = Map(f_kwargs)
            # Check url
            if not isinstance(f_url, str):
                raise TypeError(
                    f"The url's type must be str, instead type='{type(f_url)}' (url='{f_url}')")
            if len(f_url) > self.get_url_max_length():
                url_max_length = self.get_url_max_length()
                url_length = len(f_url)
                raise ValueError(f"URL exceed max length allowed, url_legnth='{url_length}' > max_legnth='{url_max_length}'")
            # Check function to handle events
            f_event_handlers = [
                Map.on_open,
                Map.on_message,
                Map.on_error,
                Map.on_close,
                Map.on_ping,
                Map.on_pong,
                Map.on_cont_message,
                Map.get_mask_key,
                Map.on_data
            ]
            [check_event_handler(f_params.get(f_event_handler)) for f_event_handler in f_event_handlers]
            # Check header
            f_header = f_params.get(Map.header)
            if (f_header is not None) and (not isinstance(f_header, list)):
                raise TypeError(f"The header must be type list, instead type'{type(f_header)}'")

        check_params(url, **kwargs)
        self.__websocket = WebSocketApp(url, **kwargs)

    def _get_websocket(self) -> WebSocketApp:
        return self.__websocket

    def get_url(self) -> str:
        """
        To get WebSocket's url

        Returns:
        --------
        return: str
            WebSocket's url
        """
        return self._get_websocket().url

    def is_running(self) -> bool:
        """
        To check connection is active

        Returns:
        --------
        return: bool
            True if connection is active else False
        """
        ws = self._get_websocket()
        return ws.keep_running and (ws.sock is not None)

    # ——————————————————————————————————————————— SELF GETTER/SETTER FUNCTION UP ———————————————————————————————————————
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ———————————————————————————————————————————————————

    def run(self) -> None:
        """
        To establish connection
        """
        self._get_websocket().run_forever()

    def send(self, payload: str) -> None:
        """
        To send message to WebSocket

        Parameters:
        -----------
        payload: str
            The message to send (utf-8 string or unicode)
        """
        self._get_websocket().send(payload)

    def close(self) -> None:
        """
        To close connections
        """
        self._get_websocket().close()

    # ——————————————————————————————————————————— SELF FUNCTION UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION DOWN ———————————————————————————————————

    @staticmethod
    def get_url_max_length() -> int:
        """
        To get URL's max length allowed

        Returns:
        --------
        return: int
            URL's max length allowed
        """
        return WebSocket._URL_MAX_LENGTH

    @staticmethod
    def get_event_handlers() -> Map:
        """
        This function stand to provide doc of event function
        """
        def on_open(socket: WebSocketApp) -> None:
            """
            Callback object which is called at opening websocket.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            """
            pass

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
            pass

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
            pass

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
            pass

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
            pass

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
            pass

        def on_ping(socket: WebSocketApp, message: str) -> None:
            pass

        def on_pong(socket: WebSocketApp, message: str) -> None:
            pass

        def get_mask_key(socket: WebSocketApp) -> None:
            """
            A callable function to get new mask keys, see the
            WebSocket.set_mask_key's docstring for more information.\n
            Parameters
            ----------
            socket: WebSocketApp
                This class object.
            """
            pass

        event_handlers = Map({
            Map.on_open: on_open,
            Map.on_error: on_error,
            Map.on_close: on_close,
            Map.on_data: on_data,
            Map.on_message: on_message,
            Map.on_cont_message: on_cont_message,
            Map.on_ping: on_ping,
            Map.on_pong: on_pong,
            Map.get_mask_key: get_mask_key
            })
        return event_handlers

    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION UP —————————————————————————————————————
