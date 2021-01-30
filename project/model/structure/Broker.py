from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature
from model.tools.FileManager import FileManager
from config.Config import Config


class Broker(ModelFeature):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def list_paires(self=None) -> list:
        """
        To get all Pair that can be trade with the Broker
        :return: list of available Broker
        """
        pass

    @staticmethod
    def list_brokers():
        """
        To get all available Broker
        :return: list of available Broker
        """
        p = Config.get(Config.DIR_BROKERS)
        return FileManager.get_dirs(p, False)

    @staticmethod
    def retrieve(bkr: str, cfs: dict):
        """
        To get access to a Broker
        :param bkr: name of a supported Broker
        :param cfs: additional configs for the Broker
        :return: access to a Broker
        """
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+"(cfs)")
