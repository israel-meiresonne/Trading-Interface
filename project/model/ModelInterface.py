from abc import ABC, abstractmethod

from model.structure.database.ModelFeature import ModelFeature as _MF


class ModelInterface(ABC):
    def __init__(self):
        self.__id =         None
        self.__settime =    None
        self._set_id()
        self._set_settime()

    def _set_id(self) -> None:
        self.__id = self.__class__.__name__.lower() + '_' + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> str:
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime


    @abstractmethod
    def new_bot(self, capital_num: float, asset_str: str, strategy_str: str, broker_str: str, pair_str: str = None) -> str:
        """
        To create a new Bot

        Parameters:
        -----------
        capital_num: float
            The numeric value of the capital
        asset_str: str
            The Asset in witch the capital is expressed
        strategy_str: str
            The class name of the Strategy to use with Bot
        broker_str: str
            The class name of the Broker to use
        pair_str: str = None
            The only Pair to trade.
            NOTE: if set to None then Bot will stalk all available Pair

        Returns:
        --------
        retturns: str
            The id of the new Bot created
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
