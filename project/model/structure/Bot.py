import threading
import time

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair


class Bot(MyJson):
    _DEBUG = True
    _VERBOSE = False
    PREFIX_ID = 'bot_'
    _TRADE_INDEX = 0
    _TRADE_INDEX_STOP = 40320
    _THREAD_NAME_BOT_BACKUP = 'bot_backup'

    def __init__(self, bkr: str, stg: str, configs: Map):
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param configs: holds additional configs for the Bot
                    configs[{Broker}]   => {dict} Broker configs
                    configs[{Strategy}] => {dict} Strategy's configs
        """
        super().__init__()
        self.__id = Bot.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(_MF.TIME_MILLISEC)
        self.__trading = False
        self.__broker = Broker.retrieve(bkr, Map(configs.get(bkr)))
        self.__strategy = None
        self._set_strategy(stg, configs)
        self.__pair = self.__strategy.get_pair()
        self.__last_backup = None
        self.__thread_backup = None

    def _set_strategy(self, stg_class: str, params: Map) -> None:
        # Put Pair
        pair_str = params.get(stg_class, Map.pair)
        params.put(Pair(pair_str), stg_class, Map.pair)
        exec(f"from model.structure.strategies.{stg_class}.{stg_class} import {stg_class}")
        self.__strategy = eval(f"{stg_class}.generate_strategy(stg_class, Map(params.get(stg_class)))")

    def get_id(self) -> str:
        return self.__id

    def get_settime(self) -> int:
        return self.__settime

    def _set_trading(self, is_trading: bool) -> None:
        self.__trading = is_trading

    def is_trading(self) -> bool:
        """
        To check if Bot is trading

        Returns:
        --------
        return: bool
            True if Bot is trading else False
        """
        return self.__trading

    def get_broker(self) -> Broker:
        return self.__broker

    def get_strategy(self) -> Strategy:
        return self.__strategy

    def get_pair(self) -> Pair:
        return self.__pair

    def _set_last_backup(self, last_backup: int) -> None:
        self.__last_backup = last_backup

    def get_last_backup(self) -> int:
        """
        To get the last time Bot have been backup\n
        Returns
        -------
        last_backup: int
            The last time Bot have been backup
        """
        return self.__last_backup

    def _reset_thread_backup(self) -> None:
        self.__thread_backup = None

    def _get_thread_backup(self) -> threading.Thread:
        """
        To get thread that run Bot's back up

        Returns:
        --------
        return: threading.Thread
            The thread that run Bot's back up
        """
        thread = self.__thread_backup
        if (thread is None) or (not thread.is_alive()):
            callback = self.backup
            call_class = self.__class__.__name__
            base_name = self._THREAD_NAME_BOT_BACKUP
            thread, output = _MF.wrap_thread(callback, call_class, base_name, repport=True)
            _MF.output(_MF.prefix() + output) if self._VERBOSE else None
            self.__thread_backup = thread
        return thread

    def start(self) -> None:
        """
        To start trade\n
        """
        self._set_trading(True)
        _stage = Config.get(Config.STAGE_MODE)
        bkr = self.get_broker()
        stg = self.get_strategy()
        bot_id = self.get_id()
        trade_index = Bot.get_trade_index()
        sleep_time = None
        nb_error = 0
        starttime = _MF.get_timestamp()
        _MF.output(f"{_MF.prefix()}Bot started to trade 🤖") if self._DEBUG else None
        while self.active():
            Bot._set_trade_index(trade_index)
            _MF.output(f"{_MF.prefix()}Bot '{bot_id}' Trade n°'{trade_index}' — {_MF.unix_to_date(_MF.get_timestamp())}") if self._VERBOSE else None
            try:
                sleep_time = stg.trade(bkr)
                nb_error = 0
                trade_index += 1
                thread_backup = self._get_thread_backup()
                thread_backup.start() if not thread_backup.is_alive() else None
            except Exception as error:
                nb_error += 1
                self.save_error(error, Bot.__name__, nb_error)
            if _stage != Config.STAGE_1:
                sleep_time = sleep_time if sleep_time is not None else Strategy.get_bot_sleep_time()
                unix_time = _MF.get_timestamp()
                start_date = _MF.unix_to_date(unix_time)
                end_date = _MF.unix_to_date(unix_time + sleep_time)
                sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                _MF.output(f"{_MF.prefix()}Bot '{bot_id}' sleep for '{sleep_time_str}' till '{start_date}'->'{end_date}'...") if self._VERBOSE else None
                time.sleep(sleep_time)
                sleep_time = None
            if _stage == Config.STAGE_1:
                _normal = '\033[0m'
                _cyan = '\033[36m'
                endtime = _MF.get_timestamp()
                n_trade = trade_index
                delta_time = endtime - starttime
                time_per_trade = f"{n_trade/delta_time}(trade/sec.)"
                trade_time = f"{delta_time/n_trade}(sec./trade)"
                run_time = _MF.delta_time(0, n_trade*60)
                _MF.output(_MF.prefix() + _cyan + f"{time_per_trade} — {trade_time} - {run_time}" + _normal) if self._DEBUG else None
        self.backup()
        _MF.output(f"{_MF.prefix()}Bot stoped to trade ☠️") if self._DEBUG else None

    def stop(self) -> None:
        self._set_trading(False)

    def active(self) -> bool:
        """
        To check if Bot still trading

        Returns:
        --------
        return: bool
            True if Bot still trading else False
        """
        stop_index = self.get_index_stop()
        trade_index = self.get_trade_index()
        _stage = Config.get_stage()
        if (_stage == Config.STAGE_1) and (stop_index is not None) and (trade_index > stop_index):
            active = False
        else:
            active = True
        active = self.is_trading() and active
        return active

    @staticmethod
    def _set_trade_index(index: int) -> None:
        if not isinstance(index, int):
            raise TypeError(f"The trade index must be of type '{int}', instead '{type(index)}'")
        Bot._TRADE_INDEX = index

    @staticmethod
    def update_trade_index(index: int) -> None:
        if Config.get_stage() != Config.STAGE_1:
            raise Exception(f"The trade index can be update only in stage '{Config.STAGE_1}', instead '{Config.get_stage()}'")
        Bot._set_trade_index(index)

    @staticmethod
    def get_trade_index() -> int:
        return Bot._TRADE_INDEX

    @staticmethod
    def get_index_stop() -> int:
        return Bot._TRADE_INDEX_STOP

    @classmethod
    def save_error(cls, error: Exception, from_class: str, nb_error: int = None) -> None:
        from traceback import format_exc
        red = "\033[31m"
        normal = "\033[0m"
        _MF.output(f"{_MF.prefix()}{red}Error from the '{from_class}' class (nb_error='{nb_error}'): "
              f"{error.__str__()} {normal}") if cls._DEBUG else None
        rows = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            "thread": _MF.thread_name(),
            "thread_infos": _MF.thread_infos(),
            'nb_error': nb_error,
            'from_class': from_class,
            "error_type": error.__class__.__name__,
            "message": error.__str__(),
            "trace": format_exc()
        }]
        fields = list(rows[0].keys())
        path = Config.get(Config.DIR_SAVE_BOT_ERRORS)
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    def backup(self) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        _start_date = Config.get(Config.START_DATE)
        path = Config.get(Config.DIR_DATABASE)
        file_name = f"{_start_date}|" + Config.get(Config.FILE_NAME_BOT_BACKUP).replace('$bot_ref', self.__str__())
        save_dir_path = path.replace('$stage', _stage).replace('$class', Bot.__name__)
        backup_path = f"{save_dir_path}{self.get_id()}/{file_name}"
        self._set_last_backup(_MF.get_timestamp())
        json_str = self.json_encode()
        FileManager.write(backup_path, json_str, binary=False, overwrite=True, make_dir=True)
        _MF.output(f"{_MF.prefix()}💾 Bot saved! ✅") if self._VERBOSE else None
        self._reset_thread_backup()

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        bkr = 'Binance'
        stg = 'MinMax'
        instance = Bot(bkr, stg, Map({
            bkr: {
                Map.public: '@json',
                Map.secret: '@json',
                Map.test_mode: True
            },
            stg: {
                Map.pair: '@json/@json',
                Map.maximum: None,
                Map.capital: 1,
                Map.rate: 1,
                Map.period: 0
            }
        }))
        exec(MyJson.get_executable())
        return instance

    def __str__(self) -> str:
        date = _MF.unix_to_date(int(self.get_settime() / 1000), _MF.FORMAT_D_H_M_S_FOR_FILE)
        bot_id = self.get_id()
        bkr_cls = self.get_broker().__class__.__name__
        stg_cls = self.get_strategy().__class__.__name__
        return f"{date}|{bot_id}|{bkr_cls}|{stg_cls}"

    def __repr__(self) -> str:
        return self.__str__() + f"({id(self)})"
