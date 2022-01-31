from typing import Dict, Tuple

import numpy as np
from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceFakeOrder import BinanceFakeOrder
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.BrokerResponse import BrokerResponse
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from requests.models import Response


class BinanceFakeAPI(BinanceAPI):
    # Constants
    _DIR_STORAGE = Config.get(Config.DIR_STORAGE)
    _FILE_LOGS = Config.get(Config.DIR_SAVE_FAKE_API_RQ)
    _FILE_LOAD_ORDERS = Config.get(Config.FILE_FAKE_API_ORDERS)
    _DIR_EXCHANGE_INFOS = f"{_DIR_STORAGE}BinanceFakeAPI/requests/exchange_infos/"
    _DIR_TRADE_FEES = f"{_DIR_STORAGE}BinanceFakeAPI/requests/trade_fees/"
    # Variables
    _HISTORIES = None
    _INITIAL_INDEXES = None
    _ORDERS = None

    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION DOWN ———————————————————————————————————

    @staticmethod
    def reset() -> None:
        """
        To reset all variables
        """
        BinanceFakeAPI._HISTORIES = None
        BinanceFakeAPI._INITIAL_INDEXES = None
        BinanceFakeAPI._ORDERS = None

    @staticmethod
    def _get_stage() -> str:
        """
        To get actual stage

        Return:
        -------
        return: str
            The actual stage
        """
        return Config.get(Config.STAGE_MODE)

    @staticmethod
    def _get_file_path_load_orders() -> str:
        _cls = BinanceFakeAPI
        class_name = BinanceFakeAPI.__name__
        return _cls._FILE_LOAD_ORDERS.replace('$stage', _cls._get_stage()).replace('$class', class_name)

    @staticmethod
    def _load_market_history(merged_pair: str, period: int) -> np.ndarray:
        """
        To load a market history

        Parameters:
        -----------
        merged_pair: str
            Pair to load history of (in merged format)
        period: int
            Period to load history of (in second)

        Return:
        -------
        return: np.ndarray
            Market history of the given Pair for the given period
        """
        _cls = BinanceFakeAPI
        broker_name = BinanceAPI.__name__.replace('API', '')
        pair = Pair(_cls.symbol_to_pair(merged_pair))
        history = MarketPrice.load_marketprice(broker_name, pair, period, active_path=True)
        # Complete missing period
        history = _cls._duplicate_missing_rows(period, history)
        return history

    @staticmethod
    def _get_market_histories() -> Map:
        """
        To get market histories
        - format merged_pair: 'BTCUSDT' (= 'BTC/USDT')

        Return:
        -------
        return: Map
            Market histories
            Map[merged_pair.upper(){str}][period{int}]: np.ndarray
        """
        _cls = BinanceFakeAPI
        if _cls._HISTORIES is None:
            _cls._HISTORIES = Map()
        return _cls._HISTORIES

    def _set_market_history(merged_pair: str, period: int, update: bool, market_history: np.ndarray = None) -> None:
        """
        To set market history
        NOTE: funnction will stop if update=True and market_history=None

        Parameters:
        -----------
        merged_pair: str
            Pair to set history of (in merged format)
        period: int
            Period to set history of (in second)
        update: bool = False
            Set True if want to update existing market history
            else False
        market_history: np.ndarray = None
            New market history

        Raises:
        -------
        raise: ValueError
            If update=True and stage != Config.STAGE_2
        """
        def request_history(merged_pair: str, period: int) -> np.ndarray:
            period_str = _cls.convert_interval(period)
            response = _cls._socket_market_history(False, _cls.RQ_KLINES, Map({
                Map.symbol: merged_pair,
                Map.interval: period_str,
                Map.limit: _cls.CONSTRAINT_KLINES_MAX_PERIOD
            }))
            content = response.get_content()
            market_history = np.array(content)
            return market_history

        _cls = BinanceFakeAPI
        stage = _cls._get_stage()
        if update and (stage != Config.STAGE_2):
            raise ValueError(f"Can update market history only in stage '{Config.STAGE_2}', instead stage='{stage}'")
        if update and (market_history is None):
            return None
        if (market_history is not None) and (not isinstance(market_history, np.ndarray)):
            raise TypeError(f"The new market history must be of type '{np.ndarray}', instead type='{type(market_history)}'")
        merged_pair = merged_pair.upper()
        histories = _cls._get_market_histories()
        if stage == Config.STAGE_1:
            market_history = _cls._load_market_history(merged_pair, period)
            histories.put(market_history, merged_pair, period)
            # Fixe size
            _cls._fixe_market_history_time()
            # Check histories
            _cls._check_market_histories()
        elif stage == Config.STAGE_2:
            market_history = request_history(merged_pair, period) if market_history is None else market_history.copy()
            histories.put(market_history, merged_pair, period)
        else:
            raise Exception(f"This stage '{stage}' is not supported")

    @staticmethod
    def _get_market_history(merged_pair: str, period: int) -> np.ndarray:
        """
        To get market history

        Parameters:
        -----------
        merged_pair: str
            Pair to get history of (in merged format)
        period: int
            Period to get history of (in second)

        Return:
        -------
        return: np.ndarray
            Market history for the given pair and period
        """
        _cls = BinanceFakeAPI
        merged_pair = merged_pair.upper()
        histories = _cls._get_market_histories()
        history = histories.get(merged_pair, period)
        if history is None:
            _cls._set_market_history(merged_pair, period, update=False)
            history = histories.get(merged_pair, period)
        if history is None:
            raise Exception(f"The market history must be set before to access (pair='{merged_pair}', period='{period}'")
        return history

    @staticmethod
    def _set_initial_indexes() -> None:
        """
        To set initial indexes for market histories
        """
        def initial_index(max_period: int, period: int, max_n_period: int) -> int:
            return int(((max_period/period)*max_n_period - 1))

        _cls = BinanceFakeAPI
        broker_name = BinanceAPI.__name__.replace('API', '')
        periods = MarketPrice.history_periods(broker_name)
        max_period = max(periods)
        max_n_period = _cls.CONSTRAINT_KLINES_MAX_PERIOD
        _cls._INITIAL_INDEXES = Map({period: initial_index(max_period, period, max_n_period) for period in periods})

    @staticmethod
    def _get_initial_indexes() -> Map:
        """
        To get initial indexes for market histories

        Return:
        -------
        return: int
            Initial indexes for market histories
            Map[period{int}]: int
            NOTE: period keys are in second
        """
        _cls = BinanceFakeAPI
        _cls._set_initial_indexes() if _cls._INITIAL_INDEXES is None else None
        return _cls._INITIAL_INDEXES

    @staticmethod
    def _get_initial_index(period: int) -> int:
        """
        To get market history's initial index for the given period

        Parameters:
        -----------
        period: int
            Period to get index of (in second)

        Raises:
        -------
        raise: Exception
            if stage != Config.STAGE_1
        raise: ValueError
            if period don't has its initial index

        Return:
        -------
        return: int
            Market history's initial index
        """
        _cls = BinanceFakeAPI
        _cls.check_stage(Config.STAGE_1, message="Can get initial index only when stage='{}', instead stage='{}'")
        idxs = _cls._get_initial_indexes()
        if period not in idxs.get_keys():
            raise ValueError(f"This period '{period}' don't has its initial index")
        idx = idxs.get_map()[period]
        return idx

    @staticmethod
    def _save_orders() -> None:
        """
        To save all submitted orders
        """
        _cls = BinanceFakeAPI
        file_path = _cls._get_file_path_load_orders()
        orders = _cls._get_orders()
        json_str = orders.json_encode()
        FileManager.write(file_path, json_str, overwrite=True, make_dir=True)

    @staticmethod
    def load_orders() -> Map():
        """
        To load all submitted orders
        """
        _cls = BinanceFakeAPI
        orders = Map()
        file_path = _cls._get_file_path_load_orders()
        folder_path = FileManager.path_to_dir(file_path)
        files = FileManager.get_files(folder_path, make_dir=True)
        file_name = files[-1] if len(files) > 0 else None
        if file_name is not None:
            backup_file_path = folder_path + file_name
            json_str = FileManager.read(backup_file_path)
            content = _MF.catch_exception(MyJson.json_decode, _cls.__name__, repport=True, **{'json_str': json_str})
            orders = content if isinstance(content, Map) else orders
        return orders

    @staticmethod
    def _get_orders() -> Map:
        """
        To get submitted orders

        Return:
        -------
        return: Map
            Submitted orders
            Map[merged_pair.upper(){str}][BinanceFakeOrder.orderId{int}]:   {BinanceFakeOrder}
        """
        _cls = BinanceFakeAPI
        if _cls._ORDERS is None:
            _cls._ORDERS = _cls.load_orders()
        return _cls._ORDERS

    @staticmethod
    def _get_order_dict(merged_pair: str) -> Dict[int, BinanceFakeOrder]:
        """
        To get list of order

        Parameters:
        -----------
        merged_pair: str
           Pair of order to get (in merged format)

        Return:
        -------
        return: List[BinanceFakeOrder]
            Orders with the same pair
        """
        merged_pair = merged_pair.upper()
        orders = BinanceFakeAPI._get_orders().get(merged_pair)
        return orders if orders is not None else {}

    @staticmethod
    def _get_order(merged_pair: str, order_id: int) -> BinanceFakeOrder:
        """
        To get a submitted order

        Parameters:
        -----------
        merged_pair: str
            The pair or the order to get (in merged format)
        order_id: int
            Id of the order to get in API's system

        Return:
        -------
        return: BinanceFakeOrder
            A submitted order
        """
        _cls = BinanceFakeAPI
        order = _cls._get_orders().get(merged_pair, int(order_id))
        if order is None:
            raise ValueError(f"There's not order with this order_id '{order_id}'")
        return order

    @staticmethod
    def _add_order(order: BinanceFakeOrder) -> None:
        """
        To add new order

        Parameters:
        -----------
        order: BinanceFakeOrder
            The order to add
        """
        _cls = BinanceFakeAPI
        merged_pair = order.get_attribut(Map.symbol)
        orders = _cls._get_orders()
        order_id = order.get_attribut(Map.orderId)
        found = orders.get(merged_pair, order_id)
        if found is not None:
            raise Exception(f"There's already an order with this order_id '{order_id}' (new_order='{id(order)}', found_order='{id(found)}')")
        orders.put(order, merged_pair, order_id)

    # ——————————————————————————————————————————— STATIC GETTER/SETTER FUNCTION UP —————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION MARKET DOWN

    @staticmethod
    def update_market_history(merged_pair: str, period: int, market_history: np.ndarray) -> None:
        """
        To update a market history

        Parameters:
        -----------
        merged_pair: str
            The pair to update (in merged format)
        period: int
            Period to update (in second)
        market_history: np.ndarray
            The new market history

        Raises:
        -------
        raise: Exception
            if stage != Config.STAGE_2
        """
        _cls = BinanceFakeAPI
        _cls.check_stage(Config.STAGE_2)
        _cls.check_merged_pair(merged_pair)
        _cls.check_period(period)
        _cls._set_market_history(merged_pair, period, update=True, market_history=market_history)
        _cls._update_orders(merged_pair) if Config.get_stage() == Config.STAGE_2 else None

    @staticmethod
    def _index(period: int) -> int:
        """
        To get market history's index for the given period

        Parameters:
        -----------
        period: int
            Period to get index of (in second)

        Return:
        -------
        return: int
            Market history's index for the given period
        """
        _cls = BinanceFakeAPI
        stage = _cls._get_stage()
        if stage == Config.STAGE_1:
            from model.structure.Bot import Bot
            broker_name = BinanceAPI.__name__.replace('API', '')
            trade_index = Bot.get_trade_index()
            periods = MarketPrice.history_periods(broker_name)
            min_period = min(periods)
            trade_time = min_period*trade_index
            index = _cls._get_initial_index(period) + int(trade_time/period)
        elif stage == Config.STAGE_2:
            index = -1
        else:
            raise Exception(f"This stage '{stage}' is not supported")
        return index

    @staticmethod
    def _actual_market_datas(merged_pair: str) -> Map:
        """
        To get market history's most recent datas

        Paramers:
        ---------
        merged_pair: str
            The pair to get datas of (in merged format)

        Return:
        -------
        return: Map
            Market history's most recent datas
            Map[Map.time]:  int     # API's unix time (in milliseconds)
            Map[Map.start]: int     # market's open time (in milliseconds)
            Map[Map.open]:  float   # market's open price
            Map[Map.high]:  float   # market's high price
            Map[Map.low]:   float   # market's low price
            Map[Map.close]: float   # market's close price
            Map[Map.end]:   int     # market's close time (in milliseconds)
        """
        def get_most_recent_row(merged_pair: str) -> np.ndarray:
            broker_name = BinanceAPI.__name__.replace('API', '')
            periods = MarketPrice.history_periods(broker_name)
            min_period = min(periods)
            history = BinanceFakeAPI._get_market_history(merged_pair, min_period)
            idx = _cls._index(min_period)
            return history[idx], min_period

        _cls = BinanceFakeAPI
        recent_row, min_period = get_most_recent_row(merged_pair)
        stage = Config.get_stage()
        if stage == Config.STAGE_1:
            actual_time = recent_row[0]
        elif  stage == Config.STAGE_2:
            str_period = _cls.convert_interval(min_period)
            stream = _cls.generate_stream(_cls.RQ_KLINES, merged_pair, str_period)
            bws = _cls._get_socket([stream])
            actual_time = bws.get_stream_time(stream)
            actual_time = actual_time if actual_time is not None else recent_row[0]
        else:
            raise Exception(f"This stage '{stage}' is not supported")
        recent_datas = Map({
            Map.time: actual_time,
            Map.start: recent_row[0],
            Map.open: float(recent_row[1]),
            Map.high: float(recent_row[2]),
            Map.low: float(recent_row[3]),
            Map.close: float(recent_row[4]),
            Map.end: recent_row[6]
        })
        return recent_datas

    # ——————————————————————————————————————————— STATIC FUNCTION MARKET UP
    # ——————————————————————————————————————————— STATIC FUNCTION ORDER DOWN

    @staticmethod
    def _new_order(params: Map) -> BinanceFakeOrder:
        """
        To create a new order
        NOTE: add the order to list of orders

        Parameters:
        -----------
        params: Map
            Params submitted with a request

        Return:
        -------
        return: BinanceFakeOrder
            A new order
        """
        _cls = BinanceFakeAPI
        merged_pair = params.get(Map.symbol)
        market_datas = _cls._actual_market_datas(merged_pair)
        order = BinanceFakeOrder(params, market_datas)
        _cls._add_order(order)
        return order

    @staticmethod
    def _update_orders(merged_pair: str) -> None:
        """
        To try to execute all submitted orders

        Paramers:
        ---------
        merged_pair: str
            The pair of orders to update (in merged format)
        """
        _cls = BinanceFakeAPI
        merged_pair = merged_pair.upper()
        order_dict = _cls._get_order_dict(merged_pair)
        market_datas = _cls._actual_market_datas(merged_pair)
        for period, order in order_dict.copy().items():
            order.try_execute(market_datas)
        _cls._save_orders()

    # ——————————————————————————————————————————— STATIC FUNCTION ORDER UP
    # ——————————————————————————————————————————— STATIC FUNCTION REQUESTS DOWN

    @staticmethod
    def steal_request(request: str, params: Map) -> BrokerResponse:
        """
        To handle locally request to API

        Parameters:
        -----------
        request: str
            The request's name
        params: Map
            Params submitted with a the request

        Raises:
        -------
        raise: Exception
            if stage != Config.STAGE_1 and stage != Config.STAGE_2
        """
        _cls = BinanceFakeAPI
        if request == _cls.RQ_EXCHANGE_INFOS:
            datas = _cls._request_exchange_infos()
        elif request == _cls.RQ_TRADE_FEE:
            datas = _cls._request_trade_fees()
        elif request == _cls.RQ_KLINES:
            datas = _cls._request_kline(params)
            if (_cls._get_stage() == Config.STAGE_1):
                merged_pair = params.get(Map.symbol)
                _cls._update_orders(merged_pair)
        elif _MF.regex_match(_cls._ORDER_RQ_REGEX, request):
            datas = _cls._request_submit_order(params)
        elif request == _cls.RQ_CANCEL_ORDER:
            datas = _cls._request_cancel_order(params)
        elif request == _cls.RQ_ALL_ORDERS:
            datas = _cls._request_all_orders(params)
        elif request == _cls.RQ_ALL_TRADES:
            datas = _cls._request_all_trades(params)
        else:
            raise Exception(f"This request '{request}' is not supported")
        response = Response()
        response.status_code = 200
        response._content = _MF.json_encode(datas).encode()
        response.request = params
        # _cls._save_log(request, params)
        return BrokerResponse(response)

    @staticmethod
    def _request_exchange_infos() -> dict:
        """
        To load exchange's infos
        """
        _cls = BinanceFakeAPI
        _cls.check_stage(Config.STAGE_1)
        path = _cls.get_file_path(_cls._DIR_EXCHANGE_INFOS)
        content = FileManager.read(path)
        infos = _MF.json_decode(content)
        return infos

    @staticmethod
    def _request_trade_fees() -> list:
        """
        To load trade fees
        """
        _cls = BinanceFakeAPI
        _cls.check_stage(Config.STAGE_1)
        path = _cls.get_file_path(_cls._DIR_TRADE_FEES)
        content = FileManager.read(path)
        trade_fees = _MF.json_decode(content)
        return trade_fees

    @staticmethod
    def _request_kline(params: Map) -> list:
        """
        To get market prices

        Raises:
        -------
        raise: Exception
            if startTime or endTime are set

        Return:
        -------
        return: list
            Market prices
        """
        keys = params.get_keys()
        if (Map.endTime in keys) and (Map.startTime in keys):
            raise Exception(f"Params startTime or endTime can't be set")
        _cls = BinanceFakeAPI
        stage = Config.get_stage()
        merged_pair = params.get(Map.symbol)
        str_period = params.get(Map.interval)
        period = _cls.get_interval(str_period)
        limit = params.get(Map.limit)
        idx = _cls._index(period)
        history = BinanceFakeAPI._get_market_history(merged_pair, period)
        if stage == Config.STAGE_1:
            kline = history[:idx+1][-limit:]
        elif stage == Config.STAGE_2:
            kline = history[-limit:]
        else:
            raise Exception(f"This stage '{stage}' is not supported")
        return kline.tolist()

    @staticmethod
    def _request_submit_order(params: Map) -> dict:
        """
        To submit order request
        """
        _cls = BinanceFakeAPI
        order = _cls._new_order(params)
        merged_pair = order.get_attribut(Map.symbol)
        market_datas = _cls._actual_market_datas(merged_pair)
        order.try_execute(market_datas)
        _cls._save_orders()
        return order.to_dict()

    @staticmethod
    def _request_cancel_order(params: Map) -> dict:
        """
        To request to cancel an order
        """
        merged_pair = params.get(Map.symbol)
        order_id = params.get(Map.orderId)
        order = BinanceFakeAPI._get_order(merged_pair, order_id)
        order.cancel()
        return order.to_dict()

    @staticmethod
    def _request_all_orders(params: Map) -> list:
        """
        To get all submitted orders
        """
        merged_pair = params.get(Map.symbol)
        order_dict = BinanceFakeAPI._get_order_dict(merged_pair)
        all_orders = [order.to_dict() for _, order in order_dict.items()]
        return all_orders

    @staticmethod
    def _request_all_trades(params: Map) -> list:
        """
        To get trades of all submitted orders
        """
        _cls = BinanceFakeAPI
        merged_pair = params.get(Map.symbol)
        order_dict = BinanceFakeAPI._get_order_dict(merged_pair)
        all_trades = [order.get_attribut(Map.fills)[0] for _, order in order_dict.items() if order.get_attribut(Map.status) == _cls.STATUS_ORDER_FILLED]
        return all_trades

    # ——————————————————————————————————————————— STATIC FUNCTION REQUESTS UP
    # ——————————————————————————————————————————— STATIC FUNCTION TOOLS DOWN

    @staticmethod
    def get_file_path(dir_path: str) -> str:
        """
        To get path to file

        Parameters:
        -----------
        dir_path: str
            Directory where files are stored

        Return:
        -------
        return: str
            The last file of the directory (following name of files)
        """
        files = FileManager.get_files(dir_path, make_dir=True)
        file_path = dir_path + files[-1]
        return file_path

    @staticmethod
    def check_merged_pair(merged_pair: str) -> bool:
        """
        To check if the merged pair given is valid

        Parameters:
        -----------
        merged_pair: str
            The merged pair to check

        Return:
        -------
        return: bool
            True if the merged pair is valid else raise exception
        """
        BinanceFakeAPI.symbol_to_pair(merged_pair)
        return True

    @staticmethod
    def check_period(period: int) -> bool:
        """
        To check if the period given is valid

        Parameters:
        -----------
        period: intt
            The period to check

        Return:
        -------
        return: bool
            True if the period is valid else raise exception
        """
        BinanceFakeAPI.convert_interval(period)
        return True

    @staticmethod
    def check_stage(expected_stage: str, message: str = None) -> bool:
        """
        To check if the stage is valid

        Paramaters:
        -----------
        expected_stage: str
            The valid stage
        message: str
            The error message

        Return:
        -------
        return: bool
            True if the stage is valid else raise exception
        """
        message = message if message is not None else "The stage must be '{}', instead stage='{}'"
        stage = BinanceFakeAPI._get_stage()
        if stage != expected_stage:
            raise Exception(message.format(expected_stage, stage))
        return True

    @staticmethod
    def _duplicate_missing_rows(period: int, history: np.ndarray) -> np.ndarray:
        """
        To complete market hhistory's missing row
        NOTE: if a row miss it will copy the previous row and update its open and close time

        Parameters:
        -----------
        period: int
            The period interval between each row (in second)
        history: np.ndarray
            The market hhistory to complete

        Return:
        -------
        return: np.ndarray
            The given market hhistory completed
        """
        def complete(period_milli: int, history: np.ndarray, n_missings: np.ndarray, missing_idxs: np.ndarray) -> np.ndarray:
            idx = missing_idxs[0]
            n_missing = n_missings[idx]
            base_row = history[idx]
            to_insert = []
            for i in range(n_missing):
                new_row = base_row.copy()
                new_row[0] = base_row[0] + period_milli
                new_row[6] = base_row[6] + period_milli
                to_insert.append(new_row)
                base_row = new_row
            history = np.insert(history, idx+1, to_insert, axis=0)
            return history

        period_milli = int(period * 1000)
        miss_period = True
        while miss_period:
            diff_open_times = np.diff(history[:,0])
            n_missings = (diff_open_times/period_milli - 1).astype(int)
            missing_idxs = np.where(n_missings > 0)[0]
            miss_period = missing_idxs.shape[0] > 0
            if miss_period:
                history = complete(period_milli, history, n_missings, missing_idxs)
        return history

    @staticmethod
    def _fixe_market_history_time() -> None:
        """
        To add rows in market histories to make them start at the same open time
        """
        def get_older_open_time(histories: Map) -> int:
            older_time = None
            for merged_pair, histories_dict in histories.get_map().items():
                for period, history in histories_dict.items():
                    is_older = (older_time is None) or (history[0,0] < older_time)
                    older_time = history[0,0] if is_older else older_time
            return older_time

        _cls = BinanceFakeAPI
        histories = _cls._get_market_histories()
        older_open_time = get_older_open_time(histories)
        # Resize histories
        for merged_pair, histories_dict in histories.get_map().items():
            for period, history in histories_dict.items():
                correct_start = history[0,0] == older_open_time
                if not correct_start:
                    period_milli = int(period * 1000)
                    base_row = history[0]
                    new_rows = []
                    while base_row[0] > older_open_time:
                        new_row = base_row.copy()
                        new_row[0] = base_row[0] - period_milli
                        new_row[6] = base_row[6] - period_milli
                        new_rows.insert(0, new_row)
                        base_row = new_row
                    history = np.insert(history, 0, new_rows, axis=0)
                    histories.put(history, merged_pair, period)

    @staticmethod
    def _check_market_histories() -> None:
        """
        To check if market histories are correct

        Raises:
        -------
        raise: Exception
            If an history contains 2 rows with the same open or close time
        raise: Exception
            If in all histories, the intervals between each row's open and close time are not equal to history's period
        raise: Exception
            If all histories with the same period don't have the same older open and close time
        raise: Exception
            If all histories with the same period don't have the same number of row and column
        """
        def check_row_unique(merged_pair: str, period: int, history: np.ndarray) -> None:
            open_times = history[:,0]
            if len(dict.fromkeys(open_times)) != open_times.shape[0]:
                raise Exception(f"Market histories (merged_pair='{merged_pair}', period='{period}') can't contain rows with the same open time")
            close_times = history[:,6]
            if len(dict.fromkeys(close_times)) != close_times.shape[0]:
                raise Exception(f"This history (merged_pair='{merged_pair}', period='{period}') can't contain rows with the same close time")

        def check_intervals(merged_pair: str, period: int, history: np.ndarray) -> None:
            period_milli = int(period * 1000)
            open_times = history[:,0]
            diff_opens = np.diff(open_times)
            if diff_opens[diff_opens != period_milli].shape[0] > 0:
                raise Exception(f"Market histories (merged_pair='{merged_pair}', period='{period}') can't have intervals bewteen open times different of the period interval")

        def check_older(older_open: dict[int, int], older_close: dict[int, int], merged_pair: str, period: int, history: np.ndarray) -> None:
            if period not in [*older_open.keys(), *older_close.keys()]:
                older_open[period] = history[0,0]
                older_close[period] = history[0,6]
                return None
            if history[0,0] != older_open[period]:
                raise Exception(f"All histories  with the same period don't have the same older open time: (merged_pair='{merged_pair}', period='{period}')")
            if history[0,6] != older_close[period]:
                raise Exception(f"All histories  with the same period don't have the same older close time: (merged_pair='{merged_pair}', period='{period}')")

        def check_shape(n_row: dict[int, int], n_col: dict[int, int], merged_pair: str, period: int, history: np.ndarray) -> None:
            if (period not in [*n_row.keys(), *n_col.keys()]):
                n_row[period] = history.shape[0]
                n_col[period] = history.shape[1]
            if history.shape[0] != n_row[period]:
                raise Exception(f"All histories with the same period don't have the same number of row: (merged_pair='{merged_pair}', period='{period}')")
            if history.shape[1] != n_col[period]:
                raise Exception(f"All histories with the same period don't have the same number of column: (merged_pair='{merged_pair}', period='{period}')")

        _cls = BinanceFakeAPI
        histories = _cls._get_market_histories()
        older_open = {}
        older_close = {}
        n_row = {}
        n_col = {}
        for merged_pair, histories_dict in histories.get_map().items():
            for period, history in histories_dict.items():
                check_row_unique(merged_pair, period, history)
                check_intervals(merged_pair, period, history)
                check_older(older_open, older_close, merged_pair, period, history)
                check_shape(n_row, n_col, merged_pair, period, history)

    # ——————————————————————————————————————————— STATIC FUNCTION TOOLS UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
