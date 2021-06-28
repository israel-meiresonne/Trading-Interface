import time

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Pair import Pair


class Bot:
    PREFIX_ID = 'bot_'
    _TRADE_INDEX = 0    # 112800   # 0
    _TRADE_INDEX_STOP = None

    def __init__(self, bkr: str, stg: str, pair_str: str, configs: Map):
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param pair_str: code of the pair to Trade, i.e.: "BTC/USDT"
        :param configs: holds additional configs for the Bot
                    configs[{Bot}]      => {dict} Bot configs
                    configs[{Broker}]   => {dict} Broker configs
                    configs[{Strategy}] => {dict} Strategy's configs
        """
        super().__init__()
        self.__id = Bot.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(_MF.TIME_MILLISEC)
        self.__pair = Pair(pair_str)
        self.__broker = Broker.retrieve(bkr, Map(configs.get(bkr)))
        self._set_strategy(stg, configs)
        Bot.save_bot(self)

    def _set_strategy(self, stg_class: str, params: Map) -> None:
        """
        # Put Pair
        pr = self.get_pair()
        configs.put(pr, stg, Map.pair)
        # Put Maximum
        max_value = configs.get(stg, Map.maximum)
        max_obj = Price(max_value, pr.get_right().get_symbol()) if max_value is not None else None
        configs.put(max_obj, stg, Map.maximum)
        # Put Capital
        capital_value = configs.get(stg, Map.capital)
        capital_obj = Price(capital_value, pr.get_right().get_symbol())
        configs.put(capital_obj, stg, Map.capital)
        self.__strategy = Strategy.retrieve(stg, Map(configs.get(stg)))
        """
        # Put Pair
        pr = self.get_pair()
        params.put(pr, stg_class, Map.pair)
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
        while not end:
            Bot._set_trade_index(trade_index)
            print(f"{_MF.prefix()}Trade n°{trade_index} — {_MF.unix_to_date(_MF.get_timestamp())}")
            # Trade
            try:
                sleep_time = stg.trade(bkr)
                nb_error = 0
            except Exception as error:
                nb_error += 1
                if _stage != Config.STAGE_1:
                    self.save_error(error, Bot.__name__)
                else:
                    raise error
                if nb_error > limit_error:
                    raise error
            # Sleep
            if _stage != Config.STAGE_1:
                # Bot.save_bot(self)
                sleep_time = sleep_time if sleep_time is not None else Strategy.get_bot_sleep_time()
                unix_time = _MF.get_timestamp()
                start_date = _MF.unix_to_date(unix_time)
                end_date = _MF.unix_to_date(unix_time + sleep_time)
                sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                print(f"{_MF.prefix()}Bot sleep for '{sleep_time_str}'seconds till '{start_date}'->'{end_date}'...")
                time.sleep(sleep_time)
            end = self._still_active()
            trade_index += 1
            # """
            if (stop_index is not None) and (trade_index > stop_index):
                raise Exception(f"End code!🙂")
            # """

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
    def save_error(error: Exception, from_class: str) -> None:
        from traceback import format_exc
        red = "\033[31m"
        normal = "\033[0m"
        print(f"{_MF.prefix()}{red}Error fromm the {from_class} class: {error.__str__()} {normal}")
        rows = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            'from_class': from_class,
            "error_type": error.__class__.__name__,
            "message": error.__str__(),
            "trace": format_exc()
        }]
        fields = list(rows[0].keys())
        path = Config.get(Config.DIR_SAVE_BOT_ERRORS)
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite)

    @staticmethod
    def save_bot(bot: 'Bot') -> None:
        _stage = Config.get(Config.STAGE_MODE)
        _start_date = Config.get(Config.START_DATE)
        path = Config.get(Config.DIR_DATABASE)
        file_name = f"{_start_date}|" + Config.get(Config.FILE_NAME_BOT_BACKUP).replace('$bot_ref', bot.__str__())
        save_dir_path = path.replace('$stage', _stage).replace('$class', Bot.__name__)
        backup_path = save_dir_path + file_name
        FileManager.write(backup_path, bot, binary=True)
        print(f"{_MF.prefix()}💾 Bot saved! ✅")

    def __str__(self) -> str:
        date = _MF.unix_to_date(int(self.get_settime() / 1000), _MF.FORMAT_D_H_M_S_FOR_FILE)
        bot_id = self.get_id()
        bkr_cls = self.get_broker().__class__.__name__
        stg_cls = self.get_strategy().__class__.__name__
        return f"{date}|{bot_id}|{bkr_cls}|{stg_cls}"

    def __repr__(self) -> str:
        return self.__str__() + f"({id(self)})"
