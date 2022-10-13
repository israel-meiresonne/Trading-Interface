from abc import abstractmethod, ABC
from typing import List

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from config.Config import Config
from model.tools.Pair import Pair

class Broker(ABC):
    PERIOD_1MIN =   60
    PERIOD_5MIN =   PERIOD_1MIN * 5
    PERIOD_15MIN =  PERIOD_1MIN * 15
    PERIOD_30MIN =  PERIOD_1MIN * 30
    PERIOD_1H =     PERIOD_1MIN * 60
    PERIOD_6H =     PERIOD_1H * 6

    @abstractmethod
    def is_active(self) ->  bool:
        """
        To check if Broker is available to receive requests\n
        Returns
        -------
        is_active: bool
            True if the Broker is active else False
        """
        pass

    @abstractmethod
    def request(self, bkr_rq: BrokerRequest) -> None:
        """
        To submit a request to Broker's API\n
        :param bkr_rq: holds params for the request
        NOTE: The response is stored in the BrokerRequest
        """
        pass

    @abstractmethod
    def get_trade_fee(self, pair: Pair) -> Map:
        """
        To get trade fees of the given Pair from Binance's API\n
        :param pair: the pair to get the trade fees
        :return: trade fees of the given Pair
        """
        pass

    @abstractmethod
    def execute(self, order: Order) -> None:
        """
        To submit Order to Broker's API\n
        :param order: the Order to execute
        """
        pass

    @abstractmethod
    def cancel(self, order: Order) -> None:
        """
        To cancel an Order\n
        :param order: the order to cancel
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
    def add_streams(self, new_streams: List[str]) -> None:
        """
        To add new steams in Broker's socket\n
        Parameters
        ----------
        new_streams: List[str]
            List of new stream
        """
        pass

    @staticmethod
    @abstractmethod
    def get_pairs(match: List[str] = None, no_match: List[str] = None) -> List[str]:
        """
        To get pairs available in Broker's API\n
        :param match: Include only pair that match this list of regex
        :param no_match: Exclude all pair that match this list of regex
        :return: Pairs available in Broker's API
        """
        pass

    @staticmethod
    @abstractmethod
    def get_max_n_period() -> int:
        """
        To get max number of period that can be request to Broker's API

        Returns:
        --------
        return: int
            Max number of period that can be request to Broker's API
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_stream(params: Map) -> str:
        """
        To generate a Broker stream\n
        Parameters
        ----------
        params: Map
            Param to adjust following Broker's needs

        Returns
        -------
        stream: str
            Broker stream
        """
        pass

    @classmethod
    @abstractmethod
    def generate_streams(cls, pairs: Pair, periods: List[int]) -> List[str]:
        """
        To generate Broker streams

        Parameters
        ----------
        pairs: Pair
            Pair to combine with period
        periods: List[int]
            Period to combine with pairs

        Returns
        -------
        stream: str
            Broker streams
        """
        pass

    @classmethod
    @abstractmethod
    def period_to_str(cls, period: int) -> str:
        """
        To convert period into strig format

        Parameters:
        -----------
        period: int
            Period to convert

        Returns:
        --------
        return: str
            Period in string format
        """
        pass

    @staticmethod
    @abstractmethod
    def close() -> None:
        """
        To close connections with Broker's API\n
        """
        pass

    @staticmethod
    @abstractmethod
    def list_paires() -> list:
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
        path = Config.get(Config.DIR_BROKERS)
        return FileManager.get_dirs(path, special=False)

    @staticmethod
    def retrieve(bkr: str, configs: Map):
        """
        To get access to a Broker\n
        :param bkr: name of a supported Broker
        :param configs: additional configs for the Broker
        :return: access to a Broker
        """
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+"(configs)")

    @staticmethod
    def generate_broker_request(broker_class: str, request_enum: str, request_params: Map) -> BrokerRequest:
        """
        To generate a new BrokerRequest\n
        :param broker_class: Class name of the Broker where the request will be submitted
        :param request_enum: Name of the request (enum from BrokerRequest.RQ_{*} )
        :param request_params: Params of the request
        :return: an instance of BrokerRequest's children (i.e: BinanceRequest, KrakenRequest, etc...)
        """
        _bkr_rq_cls = BrokerRequest.get_request_class(broker_class)
        exec(f"from model.API.brokers.{broker_class}.{_bkr_rq_cls} import {_bkr_rq_cls}")
        bkr_rq = eval(_bkr_rq_cls + f"('{request_enum}', request_params)")
        return bkr_rq
