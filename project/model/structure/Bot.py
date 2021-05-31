from time import sleep

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price


class Bot(_MF):
    SEPARATOR = "-"

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
        self.__id = Bot._generate_id(bkr, stg, pair_str)
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

    def _get_broker(self) -> Broker:
        return self.__broker

    def _get_strategy(self) -> Strategy:
        return self.__strategy

    def get_pair(self) -> Pair:
        return self.__pair

    def start(self) -> None:
        """
        To start trade
        """
        bkr = self._get_broker()
        stg = self._get_strategy()
        end = False
        print("Bot started to trade...")
        i = 0
        sleep_time = None
        _stage = Config.get(Config.STAGE_MODE)
        nb_error = 0
        limit_error = 60
        while not end:
            print(f"Trade n°{i} — {_MF.unix_to_date(_MF.get_timestamp())}")
            # Trade
            try:
                sleep_time = stg.trade(bkr)
                nb_error = 0
            except Exception as error:
                nb_error += 1
                if _stage != Config.STAGE_1:
                    self._save_error(error)
                else:
                    raise error
                if nb_error > limit_error:
                    raise error
            # Sleep
            if _stage != Config.STAGE_1:
                Bot.save_bot(self)
                sleep_time = sleep_time if sleep_time is not None else Strategy.get_bot_sleep_time()
                unix_time = _MF.get_timestamp()
                start_date = _MF.unix_to_date(unix_time)
                end_date = _MF.unix_to_date(unix_time + sleep_time)
                sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
                print(f"Bot sleep for '{sleep_time_str}'seconds till '{start_date}'->'{end_date}'...")
                sleep(sleep_time)
            end = self._still_active()
            i += 1

    @staticmethod
    def _still_active() -> bool:
        print("still trading...")
        return False

    '''
    def get_period_ranking(self) -> Map:
        bkr = self._get_broker()
        pair = self.get_pair()
        return self._get_strategy().get_period_ranking(bkr, pair)

    def set_best_period(self, best: int) -> None:
        self._get_strategy().set_best_period(best)
    '''

    @staticmethod
    def _generate_id(bkr: str, stg: str, prsbl: str) -> str:
        return bkr.lower() + Bot.SEPARATOR + stg.lower() + Bot.SEPARATOR + prsbl.lower()

    @staticmethod
    def _save_error(error: Exception) -> None:
        from model.tools.FileManager import FileManager
        from traceback import format_exc
        orange = "\033[93m"
        normal = "\033[0m"
        print(orange + error.__str__() + normal)
        rows = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            "class": error.__class__.__name__,
            "message": error.__str__(),
            "trace": format_exc()
        }]
        fields = list(rows[0].keys())
        path = Config.get(Config.DIR_SAVE_BOT_ERRORS)
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite)

    @staticmethod
    def save_bot(bot: 'Bot') -> None:
        from pickle import Pickler
        start_date = Config.get(Config.START_DATE)
        path = '/Users/israelmeiresonne/Library/Mobile Documents/com~apple~CloudDocs/Documents/ROQUETS/apolloXI/' \
               f'i&meim projects/apollo21/versions/v0.1/apollo21/project/content/v0.01/database/stage2/' \
               f'{start_date}_bot_backup.data'
        with open(path, 'wb') as file:
            record = Pickler(file)
            record.dump(bot)
        print('💾 Bot saved! ✅')
