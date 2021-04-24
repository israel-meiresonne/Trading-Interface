from time import sleep

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price


class Bot(ModelFeature):
    SEPARATOR = "-"

    def __init__(self, bkr: str, stg: str, prcd: str, configs: Map):
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param prcd: code of the pair to Trade, i.e.: "BTC/USDT"
        :param configs: holds additional configs for the Bot
                    configs[{Bot}]      => {dict} Bot configs
                    configs[{Broker}]   => {dict} Broker configs
                    configs[{Strategy}] => {dict} Strategy's configs
        """
        super().__init__()
        self.__id = Bot._generate_id(bkr, stg, prcd)
        self.__pair = Pair(prcd)
        self.__broker = Broker.retrieve(bkr, Map(configs.get(bkr)))
        """
        configs.put(pr, stg, Map.pair)
        cap_val = configs.get(stg, Map.capital)
        cap_prc = Price(cap_val, pr.get_right().get_symbol()) if cap_val is not None else None
        configs.put(cap_prc, stg, Map.capital)
        self.__strategy = Strategy.retrieve(stg, Map(configs.get(stg)))
        """
        self._set_strategy(stg, configs)

    def _set_strategy(self, stg: str, configs: Map) -> None:
        # Put Pair
        pr = self._get_pair()
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

    def get_id(self) -> str:
        return self.__id

    def _get_broker(self) -> Broker:
        return self.__broker

    def _get_strategy(self) -> Strategy:
        return self.__strategy

    def _get_pair(self) -> Pair:
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
        sleep_time = 5  # 60
        _stage = Config.get(Config.STAGE_MODE)
        while not end:
            print(f"Trade n°{i}")
            stg.trade(bkr)
            if _stage != Config.STAGE_1:
                print(f"Bot sleep for {sleep_time}seconds...")
                sleep(sleep_time)
            end = self._still_active()
            i += 1
            # if i == 2:
            #     raise Exception("End Code!🙂")

    @staticmethod
    def _still_active() -> bool:
        print("still trading...")
        return False

    @staticmethod
    def _generate_id(bkr: str, stg: str, prsbl: str) -> str:
        return bkr.lower() + Bot.SEPARATOR + stg.lower() + Bot.SEPARATOR + prsbl.lower()
