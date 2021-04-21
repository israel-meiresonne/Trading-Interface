from abc import abstractmethod

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Orders import Orders
from model.tools.Paire import Pair
from model.tools.Price import Price


class Strategy(ModelFeature):
    @abstractmethod
    def __init__(self, prms: Map):
        """
        Constructor\n
        :param prms: params
                     prms[Map.pair]     => {Pair}
                     prms[Map.maximum]  => {Price|None} # maximum of capital to use (if set, maximum > 0)
                     prms[Map.capital]  => {Price}      # initial capital
                     prms[Map.rate]     => {float|None} # ]0,1]
        :Note : Map.capital and Map.rate can't both be None
        """
        super().__init__()
        ks = [Map.pair, Map.maximum, Map.capital, Map.rate]
        rtn = ModelFeature.keys_exist(ks, prms.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required")
        pr = prms.get(Map.pair)
        max_cap = prms.get(Map.maximum)
        rate = prms.get(Map.rate)
        self._check_max_capital(max_cap, rate)
        # capital = Price(prms.get(Map.capital), pr)
        self.__pair = pr
        self.__capital = prms.get(Map.capital)
        self.__max_capital = max_cap
        self.__rate = None if rate is None else rate
        self.__orders = Orders()

    def get_pair(self) -> Pair:
        return self.__pair

    def _set_capital(self, cap: Price) -> None:
        self.__capital = cap

    def _get_capital(self) -> Price:
        cap = self.__capital
        if cap is None:
            raise Exception("The capital available is not set")
        max_cap = self.get_max_capital()
        rate = self.get_rate()
        return self._generate_real_capital(cap, max_cap, rate)

    @staticmethod
    def _generate_real_capital(cap: Price, max_cap: Price, rate: float) -> Price:
        """
        To generate the real capital available to trade by using the max capital and the capital rate\n
        :param cap: the capital available in account
        :param max_cap: the max capital available to trade
        :param rate: the rate of the capital available in account to trade  with
        :return: the real capital available to trade
        """
        if (rate is not None) and (max_cap is not None):
            real_cap = cap.get_value() * rate
            real_cap = max_cap.get_value() if real_cap > max_cap.get_value() else real_cap
        elif max_cap is not None:
            real_cap = max_cap.get_value() if cap.get_value() > max_cap.get_value() else cap.get_value()
        elif rate is not None:
            real_cap = cap.get_value() * rate
        else:
            raise Exception(f"Unknown state for max capital '{max_cap}' and rate '{rate}'")
        return Price(real_cap, cap.get_asset().get_symbol())

    def get_max_capital(self) -> Price:
        return self.__max_capital

    def get_rate(self) -> float:
        return self.__rate

    def _get_orders(self) -> Orders:
        return self.__orders

    def _add_order(self, odr: Order) -> None:
        self._get_orders().add_order(odr)

    def _update_orders(self, bkr: Broker, mkt: MarketPrice) -> None:
        """
        To update Orders\n
        :param bkr: access to a Broker's API
        :param mkt: market's prices
        """
        self._get_orders().update(bkr, mkt)

    @abstractmethod
    def trade(self, bkr: Broker) -> None:
        """
        To perform a trade\n
        :param bkr: access to a Broker's API
        """
        pass

    @staticmethod
    def _check_max_capital(max_cap: Price, rate: float) -> None:
        """
        To check if the max capital available and the rate is correct\n
        :param max_cap: the max capital available to invest
        :param rate: the rate of the capital to invest
        """
        if (max_cap is None) and (rate is None):
            raise ValueError(f"The max capital and the capital rate can't both be null")
        if (max_cap is not None) and (max_cap.get_value() <= 0):
            raise ValueError(f"The max capital can't be set at zero")
        if (rate is not None) and (rate <= 0 or rate > 1):
            raise ValueError(f"The capital rate '{rate}' must be between 0 and 1 (]0,1])")

    @staticmethod
    def list_strategies() -> list:
        """
        To get all available Strategy\n
        :return: list of available Strategy
        """
        p = Config.get(Config.DIR_STRATEGIES)
        return FileManager.get_dirs(p, False)

    @staticmethod
    def retrieve(stg: str, prms: Map):
        """
        To retrieve a Strategy\n
        :param stg: name of a Strategy
        :param prms: params
        :return: instance of a Strategy
        """
        exec("from model.structure.strategies."+stg+"."+stg+" import "+stg)
        return eval(stg+"(prms)")
