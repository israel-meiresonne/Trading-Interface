from abc import ABC, abstractmethod
from typing import Callable, List
from config.Config import Config

from model.structure.Hand import Hand
from model.tools.FileManager import FileManager
from model.tools.Pair import Pair
from model.tools.Price import Price

class Strategy(Hand, ABC):
    PREFIX_ID =     "strategy_"
    _SLEEP_TRADE =  10
    _MAX_POSITION = 5

    def __init__(self, capital: Price, broker_class: Callable, pair: Pair = None) -> None:
        self.__pair =           None
        self.__sleep_trade =    None
        super().__init__(capital, broker_class)
        if pair is not None:
            self._set_pair(pair)
            super().set_max_position(1)
        self.set_sleep_trade(self._SLEEP_TRADE)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN —————————————————————————————————————————

    def set_max_position(self, max_position: int) -> None:
        if self.get_pair() is not None:
            raise Exception(f"Can't update max position when attribut Strategy.pair is set")
        super().set_max_position(max_position)

    def get_broker_pairs(self) -> List[Pair]:
        pair = self.get_pair()
        if pair is not None:
            pairs = [pair]
        else:
            pairs = super().get_broker_pairs()
        return pairs

    def _set_pair(self, pair: Pair) -> None:
        capital = self.get_wallet().get_initial()
        if pair.get_right() != capital.get_asset():
            raise TypeError(f"The pair's right Asset '{pair.__str__().upper()}' must match capital's Asset '{capital}'")
        self.__pair = pair

    def get_pair(self) -> Pair:
        """
        To get the only pair allowed to trade

        Return:
        -------
        return: Pair
            Pair to trade
        """
        return self.__pair

    def set_sleep_trade(self, sleep_time: float) -> None:
        if not isinstance(sleep_time, (int, float)):
            raise TypeError(f"The trade's sleep time most be of types {' or '.join((int, float))}, intsead '{sleep_time}(type={sleep_time})'")
        self.__sleep_trade = sleep_time

    def get_sleep_trade(self) -> float:
        """
        To get interval between two trade
        """
        return self.__sleep_trade

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ———————————————————————————————————————————
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————

    @abstractmethod
    def trade(self) -> int:
        """
        To automatically buy and/or sell positions

        Return:
        -------
        return: int
            The sleep time before the next call of this function
        """
        pass

    # ——————————————————————————————————————————— SELF FUNCTION UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        To get all available Strategy

        Returns:
        --------
        :return: List[str]
            List of available Strategy
        """
        path = Config.get(Config.DIR_STRATEGIES)
        return FileManager.get_dirs(path)

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
