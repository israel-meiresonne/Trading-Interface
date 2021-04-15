from abc import ABC, abstractmethod

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as ModelFeat, ModelFeature
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price
from model.tools.Request import Request


class Order(ABC, Request):
    PREFIX_ID = 'odr_'
    # Types
    TYPE_MARKET = "_set_market"
    TYPE_LIMIT = "_set_limit"
    TYPE_STOP = "_set_stop"
    # Moves
    MOVE_BUY = "MOVE_BUY"
    MOVE_SELL = "MOVE_SELL"
    # Status
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELED = "CANCELED"
    STATUS_FAILED = "FAILED"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_LIST = [
        STATUS_SUBMITTED,
        STATUS_PROCESSING,
        STATUS_COMPLETED,
        STATUS_CANCELED,
        STATUS_FAILED,
        STATUS_EXPIRED
    ]

    @abstractmethod
    def __init__(self, odr_type: str, params: Map):
        """
        Constructor\n
        :param odr_type: type of Order
        :param params: Order's params
                        params[Map.pair]        => {Pair}
                        params[Map.move]        => {str}
                        params[Map.market]      => {Price}
                        params[Map.limit]       => {Price}
                        params[Map.stop]        => {Price}
                        params[Map.quantity]    => {Price}
                        params[Map.amount]      => {Price}
        """
        super().__init__()
        self.__id = self.PREFIX_ID + ModelFeature.new_code()
        self.__broker_id = None
        self.__type = odr_type
        self.__status = None
        self.__move = params.get(Map.move)
        self.__pair = params.get(Map.pair)
        self.__market = None
        self.__limit = None
        self.__stop = None
        self.__quantity = None
        self.__amount = None
        self.__params = None
        self.__settime = ModelFeat.get_timestamp(ModelFeat.TIME_MILLISEC)
        self.__execution_price = None
        self.__subexecutions = None
        self.__execution_time = None
        self._set_order(params)

    def _set_order(self, params: Map) -> None:
        odr_type = self.get_type()
        if odr_type == self.TYPE_MARKET:
            self._check_market(params)
            self._set_quantity(params.get(Map.quantity))
            self._set_amount(params.get(Map.amount))
        elif odr_type == self.TYPE_STOP:
            self._check_stop(params)
            self._set_stop_price(params.get(Map.stop))
            self._set_quantity(params.get(Map.quantity))
            self._set_amount(params.get(Map.amount))

    @staticmethod
    def _check_market(params: Map) -> None:
        # Check Keys
        ks = [Map.pair, Map.move]
        rtn = ModelFeature.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a market Order")
        # Check Quantity and Amount
        qty = params.get(Map.quantity)
        amount = params.get(Map.amount)
        if (qty is None) and (amount is None):
            raise ValueError(f"The quantity or amount must be set to make a market Order")
        if (qty is not None) and (amount is not None):
            raise ValueError(f"The quantity and amount can both be set for a market Order")
        pr = params.get(Map.pair)
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        if (qty is not None) and (qty.get_asset().get_symbol() != pr_l_sbl):
            raise ValueError(f"The quantity's asset '{qty.get_asset().get_symbol()}' must"
                             f" be the same that the pair's left asset '{pr_l_sbl}'")
        if (amount is not None) and (amount.get_asset().get_symbol() != pr_r_sbl):
            raise ValueError(f"The amount's asset '{amount.get_asset().get_symbol()}' must"
                             f" be the same that the pair's right asset '{pr_l_sbl}'")

    @staticmethod
    def _check_stop(params: Map) -> None:
        # check params
        ks = [Map.pair, Map.move, Map.stop, Map.quantity]
        rtn = ModelFeature.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a stop Order")
        # check logic
        pr = params.get(Map.pair)
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        stop = params.get(Map.stop)
        stop_sbl = stop.get_asset().get_symbol()
        if stop_sbl != pr_r_sbl:
            raise ValueError(f"Stop price asset '{stop_sbl}' must the same "
                             f"that the right asset of the pair '{pr}'")
        qty = params.get(Map.quantity)
        qty_sbl = qty.get_asset().get_symbol()
        if qty_sbl != pr_l_sbl:
            raise ValueError(f"Quantity asset '{qty_sbl}' must the same "
                             f"that the left asset of the pair '{pr}'")

    def get_id(self) -> str:
        return self.__id

    def _set_broker_id(self, odr_id) -> None:
        if self.__broker_id is not None:
            raise Exception(f"The Order's broker id is already set")
        self.__broker_id = str(odr_id)

    def get_broker_id(self) -> str:
        return self.__broker_id

    def get_type(self) -> str:
        return self.__type

    def _set_status(self, status: str) -> None:
        if status not in self.STATUS_LIST:
            raise ValueError(f"This Order status '{status}' is not supported")
        hold = self.get_status()
        if hold == self.STATUS_COMPLETED \
                or hold == self.STATUS_CANCELED \
                or hold == self.STATUS_FAILED \
                or hold == self.STATUS_EXPIRED:
            raise Exception(f"This Order status '{hold}' can't be updated to '{status}' cause it's final")
        self.__status = status

    def get_status(self) -> str:
        return self.__status

    def get_move(self) -> str:
        return self.__move

    def get_pair(self) -> Pair:
        return self.__pair

    def _set_stop_price(self, stop: Price) -> None:
        self.__stop = stop

    def get_stop_price(self) -> Price:
        return self.__stop

    def _set_quantity(self, qty: Price) -> None:
        self.__quantity = qty

    def get_quantity(self) -> Price:
        return self.__quantity

    def _set_amount(self, amount: Price) -> None:
        self.__amount = amount

    def get_amount(self) -> Price:
        return self.__amount

    def _set_execution_price(self, prc: Price) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            pass
        elif _stage == Config.STAGE_3:
            subexec = self.get_subexecutions()
            if subexec is None:
                raise Exception("In stage 3, The sub-executions must be set before to set the execution price")
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        self.__execution_price = prc

    def get_execution_price(self) -> Price:
        if self.__execution_price is None:
            raise Exception("The execution price must be set")
        return self.__execution_price

    def _set_subexecutions(self, fills: list) -> None:
        """
        To set
        Usually an order is split by the Broker to sub-order to be fill easier
        :param fills: list of sub-order executed to execute the initial order
        """
        self.__subexecutions = fills

    def get_subexecutions(self) -> list:
        if self.__subexecutions is None:
            raise Exception("The subexecutions must be set")
        return self.__subexecutions

    def _set_execution_time(self, time: int) -> None:
        if self.__execution_time is not None:
            raise Exception(f"The execution time can't be updated.")
        self.__execution_time = int(time)

    def get_execution_time(self) -> int:
        if self.__execution_time is None:
            raise Exception("The execution time must be set")
        return self.__execution_time

    def _set_params(self, params: Map) -> None:
        self.__params = params

    def _get_params(self) -> Map:
        return self.__params

    def get_settime(self) -> int:
        return self.__settime

    @abstractmethod
    def _set_market(self) -> None:
        """
        To prepare a market order request\n
        :param params: params to make a market Order
                        params[Map.pair]    => {Pair}
                        params[Map.move]    => {str}
                        params[Map.quantity]=> {Price|None}
                        params[Map.amount]  => {Price|None}
        :Note : Map.quantity or Map.amount must be set
        """
        pass

    @abstractmethod
    def _set_limit(self) -> None:
        """
        To set a limit Order\n
        :param params: params to config a limit Order
        """
        pass

    @abstractmethod
    def _set_stop(self) -> None:
        """
        To prepare a stop order request\n
        :param params: params to config a stop Order
                        params[Map.pair]    => {Pair}
                        params[Map.move]    => {str}
                        params[Map.stop]    => {Price}  # in right asset
                        params[Map.quantity]=> {Price}  # in left asset
        """
        pass

    @abstractmethod
    def generate_order(self) -> Map:
        """
        To generate params for a Order request\n
        :return: params for a Order request
        """
        pass

    @abstractmethod
    def generate_cancel_order(self) -> Map:
        """
        To generate params to cancel the Order\n
        :return: params to cancel the Order
        """
        pass
