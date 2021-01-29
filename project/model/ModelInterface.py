from abc import ABC, abstractmethod

from model.tools.Map import Map


class ModelInterface(ABC):
    def __init__(self):
        self.log_id = "xxx"

    @abstractmethod
    def create_bot(self, broker: str, strategy: str, buy_code: str, sell_code: str, config_map: Map) -> None:
        """
        To create a new Bot\n
        :param broker:      name of a supported Broker
        :param strategy:    name of a supported Strategy
        :param buy_code:    code of the supported Currency to buy
        :param sell_code:   code of the supported Currency to buy
        :param config_map:  holds additional config for the Bot
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
