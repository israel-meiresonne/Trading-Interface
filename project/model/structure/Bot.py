from threading import Thread
from typing import Callable, Dict, List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class Bot(MyJson):
    _DEBUG =                True
    _VERBOSE =              False
    PREFIX_ID =             'bot_'
    _TRADE_INDEX =          0
    _THREAD_TRADE =         'trade'
    _THREAD_BACKUP =        'bot_backup'
    _TIMEOUT_THREAD_STOP =  60*2
    SLEEP_DEFAULT_TRADE =   60

    def __init__(self, capital: Price, strategy_class: Callable, broker_class: Callable, pair: Pair = None):
        self.__id =                 None
        self.__settime =            None
        self.__strategy =            None
        self.__threads =            None
        self.__backup =             None
        self._set_id()
        self._set_settime()
        self._set_strategy(strategy_class, capital, broker_class, pair)
        self._set_threads()

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————

    def _set_id(self) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> str:
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def _set_strategy(self, strategy_class: Callable, capital: Price, broker_class: Callable, pair: Pair = None) -> None:
        self.__strategy = strategy_class(capital, broker_class, pair)

    def get_strategy(self) -> Strategy:
        return self.__strategy

    def _set_threads(self) -> None:
        self.__threads = {
            self._THREAD_TRADE:  {
                Map.status: False,
                Map.thread: None,
                Map.callback: self._manage_trade.__name__
            },
            self._THREAD_BACKUP: {
                Map.status: False,
                Map.thread: None,
                Map.callback: self._manage_backup.__name__
            }
        }

    def _get_threads(self) -> Dict[str, Thread]:
        """
        To get list of thread managed

        Returns:
        --------
        return: List[Thread]
            List of thread managed
        """
        return self.__threads

    def _get_thread_callback(self, thread_name: str) -> Callable:
        callback_str = self._get_threads()[thread_name][Map.callback]
        return eval(f'self.{callback_str}')

    def _reset_thread(self, thread_name: str) -> None:
        self._get_threads()[thread_name][Map.thread] = None

    def _get_thread(self, thread_name: str) -> Thread:
        """
        To get the thread of the given name

        Parameters:
        -----------
        thread_name: str
            The base name of the thread to get

        Returns:
        --------
        return: List[Thread]
            Thread of the given name
        """
        threads = self._get_threads()
        thread = threads[thread_name][Map.thread]
        if thread is None:
            callback = self._get_thread_callback(thread_name)
            thread, output = _MF.wrap_thread(callback, self.__class__.__name__, thread_name)
            threads[thread_name][Map.thread] = thread
            _MF.output(output) if self._VERBOSE else None
        return thread

    def _set_thread_on(self, thread_name: str, on: bool) -> None:
        """
        To start or stop thread of the given name

        Parameters:
        -----------
        thread_name: str
            The base name of the thread to start/stop
        on: bool
            Set True to start the thread else False to stop it
        """
        if not isinstance(on, bool):
            raise TypeError(f"The thread state must be of type '{bool}', instead '{on}({type(on)})'")
        self._get_threads()[thread_name][Map.status] = on
        thread = self._get_thread(thread_name)
        if on:
            thread.start() if not thread.is_alive() else None
        elif not on and thread.is_alive():
            _MF.wait_while(thread.is_alive, False, self._TIMEOUT_THREAD_STOP, Exception(f"Time to stop thread '{thread.name}' is out"))
            self._reset_thread(thread_name)

    def _is_thread_on(self, thread_name: str) -> bool:
        return self._get_threads()[thread_name][Map.status]

    def set_broker(self, broker: Broker) -> None:
        self.get_strategy().set_broker(broker)

    def _set_backup(self, backup: str) -> None:
        if not isinstance(backup, str):
            raise TypeError(f"The backup must be of type '{str}', instead '{type(backup)}'")
        self.__backup = backup

    def _reset_backup(self) -> None:
        self.__backup = None

    def _get_backup(self) -> str:
        return self.__backup

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    def start(self) -> None:
        """
        To start trading
        """
        self._set_thread_on(self._THREAD_TRADE, on=True)

    def stop(self) -> None:
        """
        To stop trading
        """
        strategy = self.get_strategy()
        self._set_thread_on(self._THREAD_TRADE, on=False)
        strategy.stop()
        self.backup(force=True)

    def _manage_trade(self) -> None:
        """
        To manage trade
        """
        def keep_looping(trade_index: int, stop_index: int) -> bool:
            can_loop = self._is_thread_on(self._THREAD_TRADE)
            if stage == Config.STAGE_1:
                can_loop = can_loop and (trade_index < stop_index)
            return can_loop
        stage = Config.get(Config.STAGE_MODE)
        trade_index = self.get_trade_index()
        stop_index = self.get_index_stop()
        start_end_time = self.get_start_end_time()
        prefix = _MF.prefix
        # Start Strategy
        strategy = self.get_strategy()
        # strategy.add_streams()
        """
        strategy.set_stalk_on(on=True)
        strategy.set_position_on(on=True)
        strategy.set_market_analyse_on(on=True)
        """
        # Prepare loop
        starttime = _MF.get_timestamp()
        while keep_looping(trade_index, stop_index):
            Bot._set_trade_index(trade_index)
            sleep_interval = _MF.catch_exception(strategy.trade, self.__class__.__name__)
            if sleep_interval is not None:
                trade_index += 1
                self.backup()
            unix_time = _MF.get_timestamp()
            if stage in [Config.STAGE_2, Config.STAGE_3]:
                sleep_interval = self.SLEEP_DEFAULT_TRADE if sleep_interval is None else sleep_interval
                sleep_time = _MF.sleep_time(unix_time, sleep_interval)
                sleep_message = f"Bot sleep for {sleep_time}sec. from '{_MF.unix_to_date(unix_time)}' to '{_MF.unix_to_date(unix_time + sleep_time)}'" if self._DEBUG else None
                _MF.static_output(prefix() + sleep_message)
                _MF.sleep(sleep_time)
            elif stage == Config.STAGE_1:
                current_time = start_end_time[Map.start] + trade_index * 60
                current_date = _MF.unix_to_date(current_time)
                loop_message = f"Trade on '{current_date}' == Speed {(stop_index - trade_index)/(unix_time - starttime)}(Trades/sec.)"
                _MF.static_output(_MF.loop_progression(starttime, trade_index, stop_index, loop_message))
            else:
                raise Exception(f"Unkown stage '{stage}'")
        self.backup()
        self._reset_thread(self._THREAD_TRADE)
        strategy.set_stalk_on(on=False)
        """
        strategy.set_position_on(on=True)
        strategy.set_market_analyse_on(on=True)
        """
        _MF.output(prefix() + "Bot stopped ☠️")

    def _manage_backup(self) -> None:
        """
        To manage backup
        """
        self.backup()

    def _json_encode_to_dict(self) -> dict:
        attributes = self.__dict__.copy()
        for attribute, value in attributes.items():
            if Map.backup in attribute:
                attributes[attribute] = None
        return attributes

    def backup(self, force: bool = False) -> None:
        backup = self._get_backup()
        json_str = self.json_encode()
        if force or (backup != json_str):
            bot_id = self.get_id()
            bot_file_path = self.get_path_file_backup(bot_id)
            FileManager.write(bot_file_path, json_str, overwrite=True, make_dir=True)
            self._set_backup(json_str)

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @classmethod
    def get_path_file_backup(cls, bot_id: str) -> str:
        """
        To get file path to where Bot are stored

        Returns:
        --------
        return: str
            File path to where Bot are stored
        """
        file_pattern = Config.get(Config.FILE_SAVE_BOT)
        stage = Config.get(Config.STAGE_MODE)
        path_file = file_pattern.replace('$id', bot_id).replace('$stage', stage).replace('$class', cls.__name__)
        return path_file

    @classmethod
    def get_path_dir_hands(cls) -> str:
        """
        To get path directory to where all Bot are stored
        """
        fake_id = "fake_id"
        bot_file_path = cls.get_path_file_backup(fake_id)
        splitted = bot_file_path.split('/')
        path_dir_bots = '/'.join(splitted[:-2]) + '/'
        return path_dir_bots

    @classmethod
    def list_bot_ids(cls) -> List[str]:
        """
        To list id of Bot available to load

        Returns:
        --------
        return: List[str]
            List id of Bot available to load
        """
        path_dir_bots = cls.get_path_dir_hands()
        bot_ids = FileManager.get_dirs(path_dir_bots, make_dir=True)
        return bot_ids

    @classmethod
    def load(cls, bot_id: str) -> 'Bot':
        """
        To load the most recent backup

        Parameters:
        -----------
        bot_id: str
            ID of the Bot to load

        Returns:
        --------
        return: Bot
            Bot of the given ID
        """
        file_path = cls.get_path_file_backup(bot_id)
        dir_path = FileManager.path_to_dir(file_path)
        backup_files = _MF.catch_exception(FileManager.get_files, cls.__name__, **{Map.path: dir_path})
        if (backup_files is None) or len(backup_files) == 0:
            raise Exception(f"There's not '{cls.__name__}' backup with this id '{bot_id}'")
        most_recent_file_path = dir_path + backup_files[-1]
        json_str = FileManager.read(most_recent_file_path)
        bot = MyJson.json_decode(json_str)
        return bot

    @classmethod
    def _set_trade_index(cls, index: int) -> None:
        if not isinstance(index, int):
            raise TypeError(f"The trade index must be of type '{int}', instead '{type(index)}'")
        cls._TRADE_INDEX = index

    @classmethod
    def update_trade_index(cls, index: int) -> None:
        if Config.get_stage() != Config.STAGE_1:
            raise Exception(f"The trade index can be update only in stage '{Config.STAGE_1}', instead '{Config.get_stage()}'")
        cls._set_trade_index(index)

    @classmethod
    def get_trade_index(cls) -> int:
        return cls._TRADE_INDEX

    @classmethod
    def get_start_end_time(cls) -> dict[str, int]:
        start_end_time = Config.get(Config.FAKE_API_START_END_TIME)
        return start_end_time.copy()

    @classmethod
    def get_index_stop(cls) -> int:
        start_end_time = cls.get_start_end_time()
        starttime = start_end_time[Map.start]
        endtime = start_end_time[Map.end]
        return int((endtime - starttime)/60)

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

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Bot.__new__(Bot)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
    # ——————————————————————————————————————————— OVERWRITE PYTHON DOWN ————————————————————————————————————————————————

    def __str__(self) -> str:
        date = _MF.unix_to_date(int(self.get_settime() / 1000), _MF.FORMAT_D_H_M_S_FOR_FILE)
        bot_id = self.get_id()
        broker_str = self.get_strategy().get_broker_class()
        strategy_str = self.get_strategy().__class__.__name__
        return f"{date}|{bot_id}|{broker_str}|{strategy_str}"

    def __repr__(self) -> str:
        return self.__str__() + f"({id(self)})"

    # ——————————————————————————————————————————— OVERWRITE PYTHON UP ——————————————————————————————————————————————————
