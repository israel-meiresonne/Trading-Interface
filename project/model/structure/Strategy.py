from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature
from model.tools.FileManager import FileManager
from config.Config import Config


class Strategy(ModelFeature):
    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def list_strategies():
        """
        To get all available Strategy
        :return: list of available Strategy
        """
        p = Config.get(Config.DIR_STRATEGIES)
        return FileManager.get_dirs(p, False)

    @staticmethod
    def retrieve(stg: str):
        """
        To retrieve a Strategy
        :param stg: name of a Strategy
        :return: instance of a Strategy
        """
        exec("from model.structure.strategies."+stg+"."+stg+" import "+stg)
        return eval(stg+"()")

