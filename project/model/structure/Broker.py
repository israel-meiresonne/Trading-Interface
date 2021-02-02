from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature
from model.tools.FileManager import FileManager
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from config.Config import Config


class Broker(ModelFeature):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_market_price(self) -> MarketPrice:
        """
        To get the MarketPrice\n
        :return: the current MarketPrice
        """
        pass

    @abstractmethod
    def execute(self, odr: Order) -> None:
        """
        To excute a trade Order\n
        :param odr: Order to execute
        """
        pass

    @abstractmethod
    def get_next_trade_time(self) -> int:
        """
        To get the time to wait before the next trade to avoid API ban\n
        :return: the time to wait before the next trade
        """
        pass

    @abstractmethod
    def list_paires(self=None) -> list:
        """
        To get all Pair that can be trade with the Broker\n
        :return: list of available Broker
        """
        pass

    @staticmethod
    def list_brokers():
        """
        To get all available Broker\n
        :return: list of available Broker
        """
        p = Config.get(Config.DIR_BROKERS)
        return FileManager.get_dirs(p, False)

    @staticmethod
    def retrieve(bkr: str, cfgs: dict):
        """
        To get access to a Broker\n
        :param bkr: name of a supported Broker
        :param cfgs: additional configs for the Broker
        :return: access to a Broker
        """
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+"(cfgs)")
