from abc import ABC, abstractmethod

from model.structure.Bot import Bot
from model.structure.database.ModelFeature import ModelFeature as _MF


class ModelInterface(ABC):
    def __init__(self, prefix: str):
        self.log_id = prefix + _MF.new_code()
        self.__settime = _MF.get_timestamp(_MF.TIME_MILLISEC)

    @abstractmethod
    def create_bot(self, bkr: str, stg: str, prcd: str, configs: dict) -> Bot:
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param prcd: code of the pair to Trade, i.e.: "BTC/USDT"
        :param configs: holds additional configs for the Bot
                        configs[{Bot}]      => Bot's configs
                        configs[{Broker}]   => Broker's configs
                        configs[{Strategy}] => Strategy's configs
        :return: The Bot just created
        """
        pass

    @abstractmethod
    def get_log_id(self) -> str:
        """
        To get the id of the log session\n
        :return: id of the log session
        """
        pass

    @abstractmethod
    def start_bot(self, bot_id: str) -> None:
        """
         To turn on the Bot with the given bot_id\n
         :param bot_id: id of a Bot
        """
        pass

    @abstractmethod
    def stop_bot(self, bot_id: str) -> None:
        """
         To turn off the Bot with the given bot_id\n
         :param bot_id: id of a Bot\n
        """
        pass

    @abstractmethod
    def stop_bots(self) -> None:
        """
         To turn off all active Bot\n
        """
        pass

    @classmethod
    @abstractmethod
    def close_brokers(cls) -> None:
        """
        To close connection of all Broker
        """
        pass
