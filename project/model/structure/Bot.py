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
    PREFIX_ID = 'bot_'
    _TRADE_INDEX = 0
    _TRADE_INDEX_STOP = 500

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
        self.__broker = Broker.retrieve(bkr, Map(configs.get(bkr)))
        self.__strategy = None
        self._set_strategy(stg, configs)
        self.__pair = self.__strategy.get_pair()
        self.__last_backup = None

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

    def start(self) -> None:
        """
        To start trade\n
        """
        _stage = Config.get(Config.STAGE_MODE)
        bkr = self.get_broker()
        stg = self.get_strategy()
        end = False
        trade_index = Bot.get_trade_index()
        sleep_time = None
        nb_error = 0
        limit_error = 60
        stop_index = Bot.get_index_stop()
        print(f"{_MF.prefix()}Bot started to trade...")
        bot_id = self.get_id()
        while not end:
            Bot._set_trade_index(trade_index)
            print(f"{_MF.prefix()}Bot '{bot_id}' Trade n°'{trade_index}' — {_MF.unix_to_date(_MF.get_timestamp())}")
            # Trade
            try:
                sleep_time = stg.trade(bkr)
                nb_error = 0
            except Exception as error:
                nb_error += 1
                if _stage != Config.STAGE_1:
                    self.save_error(error, Bot.__name__, nb_error)
                else:
                    raise error
                """
                if nb_error > limit_error:
                    raise error
                """
            # Sleep
            if _stage != Config.STAGE_1:
                try:
                    self.backup()
                except Exception as error:
                    nb_error += 1
                    self.save_error(error, Bot.__name__, nb_error)
                sleep_time = sleep_time if sleep_time is not None else Strategy.get_bot_sleep_time()
                unix_time = _MF.get_timestamp()
                start_date = _MF.unix_to_date(unix_time)
                end_date = _MF.unix_to_date(unix_time + sleep_time)
                sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                print(f"{_MF.prefix()}Bot '{bot_id}' sleep for '{sleep_time_str}' till '{start_date}'->'{end_date}'...")
                time.sleep(sleep_time)
                sleep_time = None
            end = self._still_active()
            trade_index += 1
            # Stop stage1
            if (_stage == Config.STAGE_1) and (stop_index is not None) and (trade_index > stop_index):
                raise Exception(f"End code!🙂")

    @staticmethod
    def _still_active() -> bool:
        print(f"{_MF.prefix()}still trading...")
        return False

    @staticmethod
    def _set_trade_index(index: int) -> None:
        Bot._TRADE_INDEX = index

    @staticmethod
    def get_trade_index() -> int:
        return Bot._TRADE_INDEX

    @staticmethod
    def get_index_stop() -> int:
        return Bot._TRADE_INDEX_STOP

    @staticmethod
    def save_error(error: Exception, from_class: str, nb_error: int = None) -> None:
        from traceback import format_exc
        red = "\033[31m"
        normal = "\033[0m"
        print(f"{_MF.prefix()}{red}Error fromm the '{from_class}' class (nb_error='{nb_error}'): "
              f"{error.__str__()} {normal}")
        rows = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
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
        print(f"{_MF.prefix()}💾 Bot saved! ✅")

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
