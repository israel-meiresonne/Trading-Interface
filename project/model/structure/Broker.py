from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from config.Config import Config


class Broker(ModelFeature):
    @abstractmethod
    def get_account_snapshot(self, bkr_rq: BrokerRequest) -> None:
        """
        To get a snapshot\n
        :param bkr_rq: holds params for the request
        :return: the result is stored the given BrokerRequest
        """
        pass

    @abstractmethod
    def get_market_price(self, bkr_rq: BrokerRequest) -> None:
        """
        To get the MarketPrice\n
        :param bkr_rq: holds parameters required
        """
        pass

    @abstractmethod
    def execute(self, odrs: Map) -> None:
        """
        To submit Order requests to Broker's API\n
        :param odrs: the Orders to execute
        """
        pass

    @abstractmethod
    def cancel(self, odr: Order) -> None:
        """
        To cancel an Order\n
        :param odr: the order to cancel
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
