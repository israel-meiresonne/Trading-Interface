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
    RQ_ORDERS = "_set_orders"
    RQ_24H_STATISTICS = "_set_24h_statistics"
    # Accounts
    ACCOUNT_MAIN = "ACCOUNT_MAIN"
    ACCOUNT_MARGIN = "ACCOUNT_MARGIN"
    ACCOUNT_FUTURE = "ACCOUNT_FUTURE"

    def __init__(self, prms: Map):
        super().__init__()
        self.__params = prms
        self.__endpoint = None
        self.__request = None
        self.__result = None

    def _set_endpoint(self, endpoint: str) -> None:
        self.__endpoint = endpoint

    def get_endpoint(self) -> str:
        if self.__endpoint is None:
            raise Exception(f"The API's endpoint must be set first")
        return self.__endpoint

    def _set_request(self, request: Map) -> None:
        self.__request = request

    def _get_request(self) -> Map:
        return self.__request

    def _set_result(self, result) -> None:
        self.__result = result

    def _get_result(self):
        return self.__result

    @abstractmethod
    def _set_market_price(self, prms: Map) -> None:
        """
        To prepare a market prices request\n
        :param prms: params required to request MarketPrice to Broker
                         prms[Map.pair]         => {Pair}
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
                 Map[Map.account][time{int}][symbol{str}]:  {Price}
                 Map[Map.response]:                         {list}  | API's response
        """
        pass

    @abstractmethod
    def _set_24h_statistics(self, params: Map) -> None:
        """
        To prepare 24h statistics request\n
        :param params: params required
               params[Map.pair]:  {Pair|None}  # If None it will request all symbol
        """
        pass

    @abstractmethod
    def get_24h_statistics(self) -> Map:
        """
        To get statistics of the last 24h on a pair (or all pair if not symbol given)\n
        :return: statistics of the last 24h of a pair or all pair
                 # symbol Format: 'btc/usdt'
                 Map[symbol{str}][Map.symbol]:              {str}   # symbol Format: 'btc/usdt'
                 Map[symbol{str}][Map.price]:               {float} # Price change
                 Map[symbol{str}][Map.rate]:                {float} # Rate change
                 Map[symbol{str}][Map.low]:                 {float} # Lower price
                 Map[symbol{str}][Map.high]:                {float} # Higher price
                 Map[symbol{str}][Map.volume][Map.left]:    {float} # Volume in left asset
                 Map[symbol{str}][Map.volume][Map.right]:   {float} # Volume in right asset
                 Map[symbol{str}][Map.time][Map.start]:     {float} # Start time
                 Map[symbol{str}][Map.time][Map.end]:       {float} # End time
        """
        pass

    @abstractmethod
    def _set_orders(self, prms: Map) -> None:
        """
        To prepare request to get datas about submitted Orders\n
        :param prms: params required
                     prms[Map.symbol]:      {string}
                     prms[Map.id]:          {string|None}    # an Order's id
                     prms[Map.begin_time]:  {int|None}
                     prms[Map.end_time]:    {int|None}
                     prms[Map.limit]:       {int|None}
                     prms[Map.timeout]:     {int|None}
        """
        pass

    @abstractmethod
    def get_orders(self) -> Map:
        """
        To get datas about submitted Orders\n
        :return: datas about submitted Orders
                 orders[order_id{string}][          # Broker's Order id
                    Map.symbol:     {string}
                    Map.id:         {string}        # Broker's Order id
                    Map.price:      {float|None}    # execution price
                    Map.quantity:   {float}         # submitted quantity
                    Map.qty:        {float|None}    # executed quantity
                    Map.amount:     {float|None}    # amount spent to execute the submitted quantity
                    Map.status:     {string}        # Order's status converted to System's status for Order
                    Map.type:       {string}        # Order's execution type (Market, Limit, etc...)
                    Map.move:       {string}        # Buy | Sell (Order.Move_*)
                    Map.time:       {int}           # execution unix time
                 ]
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
        To generate class name of Broker's request class (format: {Broker}Request)\n
        :param bkr_cls: a Broker's class name
        :return: the class name of Broker's Request class
        """
        path = Config.get(Config.DIR_BROKERS)
        dirs = FileManager.get_dirs(path, False)
        if bkr_cls not in dirs:
            raise IndexError(f"This Broker '{bkr_cls}' is not supported")
        suffix = BrokerRequest._SUFFIX_REQUEST
        return bkr_cls + suffix
