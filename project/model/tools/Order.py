from abc import ABC, abstractmethod


class Order(ABC):
    TYPE_MARKET = "_set_market"
    TYPE_LIMIT = "_set_limit"
    TYPE_STOP = "_set_stop"
    MOVE_BUY = "MOVE_BUY"
    MOVE_SELL = "MOVE_SELL"

    def __init__(self, tp: str, params):
        """
        Constructor\n
        :param tp: type of Order
        :param params: Order's params
                        params[Map.pair]        => {pair}
                        params[Map.move]        => {str}
                        params[Map.market]      => {Price}
                        params[Map.limit]       => {Price}
                        params[Map.stop]        => {Price}
                        # params[Map.rate]        => {int}
        """
        self.__type = None
        self.__status = None
        self.__move = None
        self.__pair = None
        self.__market = None
        self.__limit = None
        self.__stop = None
        self.__quantity = None
        self.__amount = None
        # self.max_rate = None
        self.__params = None

    def _set_params(self, params: dict):
        self.__params = params

    def _get_params(self) -> dict:
        return self.__params

    @abstractmethod
    def _set_market(self, params: dict) -> None:
        """
        To set a market Order\n
        :param params: params to config a market Order
        """
        pass

    @abstractmethod
    def _set_limit(self, params: dict) -> None:
        """
        To set a limit Order\n
        :param params: params to config a limit Order
        """
        pass

    @abstractmethod
    def _set_stop(self, params: dict) -> None:
        """
        To set a stop Order\n
        :param params: params to config a stop Order
        """
        pass

    @abstractmethod
    def generate_order(self) -> dict:
        """
        To generate params for a Order request
        :return: params for a Order request
        """
        pass
