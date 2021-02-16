from time import sleep
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
                    cfgs[{Bot}]         => {dict} Bot configs
                    cfgs[{Broker}]      => {dict} Broker configs
                    configs[{Strategy}] => {dict} Strategy's configs
        """
        super().__init__()
        self.__id = Bot._generate_id(bkr, stg, prcd)
        self.__pair = Pair(prcd)
        pr = self.__pair
        self.__broker = Broker.retrieve(bkr, Map(configs.get(bkr)))
        configs.put(pr, stg, Map.pair)
        cap = configs.get(stg, Map.capital)
        configs.put(Price(cap, pr.get_right().get_symbol()), stg, Map.capital)
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
        while not end:
            stg.trade(bkr)
            print("sleep 3 sec...")
            sleep(3)
            end = self.__stillActive()

    def __stillActive(self) -> bool:
        print("still trading...")
        return False

    @staticmethod
    def _generate_id(bkr: str, stg: str, prsbl: str) -> str:
        return bkr.lower() + Bot.SEPARATOR + stg.lower() + Bot.SEPARATOR + prsbl.lower()
