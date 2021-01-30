from model.structure.database.ModelFeature import ModelFeature
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.Paire import Pair


class Bot(ModelFeature):
    SEPARATOR = "-"

    def __init__(self, bkr: str, stg: str, prcd: str, cfs: dict):
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param prcd: code of the pair to Trade, i.e.: "BTC/USDT"
        :param cfs: holds additional configs for the Bot
                    cfs[{Bot}]    => Bot configs
                    cfs[{Broker}] => Broker configs
        """
        cfs[bkr] = {} if bkr not in cfs else cfs[bkr]
        self.__id = Bot.__generate_id(bkr, stg, prcd)
        self.__broker = Broker.retrieve(bkr, cfs[bkr])
        self.__strategy = Strategy.retrieve(stg)
        self.__pair = Pair(prcd)

    def get_id(self):
        return self.__id

    def _get_broker(self):
        return self.__broker

    def _get_strategy(self):
        return self.__strategy

    def _get_pair(self):
        return self.__pair

    @staticmethod
    def __generate_id(bkr: str, stg: str, prcd: str):
        return bkr.lower() + Bot.SEPARATOR + stg.lower() + Bot.SEPARATOR + prcd.lower()
