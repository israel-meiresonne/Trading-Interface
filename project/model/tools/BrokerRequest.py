from abc import ABC, abstractmethod

from config.Config import Config
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Request import Request


class BrokerRequest(ABC, Request):
    # Const
    _SUFFIX_REQUEST = Request.__name__
    # Requests
    RQ_MARKET_PRICE = "_set_market_price"
    RQ_ACCOUNT_SNAP = "_set_account_snapshot"
    # Accounts
    ACCOUNT_MAIN = "ACCOUNT_MAIN"
    ACCOUNT_MARGIN = "ACCOUNT_MARGIN"
    ACCOUNT_FUTUR = "ACCOUNT_FUTUR"

    def __init__(self, prms: Map):
        self.__params = prms
        self.__request = None

    def _set_request(self, request: Map) -> None:
        self.__request = request

    def _get_request(self) -> Map:
        return self.__request

    @abstractmethod
    def _set_market_price(self, prms: Map) -> None:
        """
        To prepare a market prices request\n
        :param prms: params required to request MarketPrice to Broker
                         prms[Map.pair]         => {str}
                         prms[Map.period]       => {int}  # in second
                         prms[Map.begin_time]   => {int|None}
                         prms[Map.end_time]     => {int|None}
                         prms[Map.number]       => {int|None}  # number of period
        """
        pass

    @abstractmethod
    def get_market_price(self) -> MarketPrice:
        """
        To get market prices\n
        :return: the market prices
        """
        pass

    @abstractmethod
    def _set_account_snapshot(self, prms: Map) -> None:
        """
        To prepare a account snapshot request\n
        :param prms: params required
                     prms[Map.account]      => {string}
                     prms[Map.begin_time]   => {int|None}
                     prms[Map.end_time]     => {int|None}
                     prms[Map.number]       => {int|None}
                     prms[Map.timeout]      => {int|None}
        """
        pass

    @abstractmethod
    def get_account_snapshot(self) -> Map:
        """
        To get account snapshot\n
        :return: account
                 Map[symbol{str}] => {Price}
        """
        pass

    @abstractmethod
    def generate_request(self) -> Map:
        """
        To generate  params for to submit request to a Broker's API\n
        :return: params required for Broker's API request
        """
        pass

    @staticmethod
    def get_request_class(bkr_cls: str) -> str:
        """
        To generate the class name of Broker's Request class inheriting of BrokerRequest\n
        :param bkr_cls: a Broker's class name
        :return: the class name of Broker's Request class
        """
        path = Config.get(Config.DIR_BROKERS)
        dirs = FileManager.get_dirs(path, False)
        if bkr_cls not in dirs:
            raise IndexError(f"This Broker '{bkr_cls}' is not supported")
        suffix = BrokerRequest._SUFFIX_REQUEST
        return bkr_cls + suffix
