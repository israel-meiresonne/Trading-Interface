from abc import abstractmethod

from model.structure.database.ModelFeature import ModelFeature
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from config.Config import Config
from model.tools.Paire import Pair


class Broker(ModelFeature):
    @abstractmethod
    def request(self, bkr_rq: BrokerRequest) -> None:
        """
        To submit a request to Broker's API\n
        :param bkr_rq: holds params for the request
        NOTE: The response is stored in the BrokerRequest
        """
        pass

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
        p = Config.get(Config.DIR_BROKERS)
        return FileManager.get_dirs(p, False)

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
    def new_broker_request(bkr_cls: str, request_enum: str, request_params: Map) -> BrokerRequest:
        _bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
        exec(f"from model.API.brokers.{bkr_cls}.{_bkr_rq_cls} import {_bkr_rq_cls}")
        bkr_rq = eval(_bkr_rq_cls + f"('{request_enum}', request_params)")
        return bkr_rq
