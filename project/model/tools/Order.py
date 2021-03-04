from abc import ABC, abstractmethod

from model.structure.database.ModelFeature import ModelFeature as ModelFeat, ModelFeature
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price
from model.tools.Request import Request


class Order(ABC, Request):
    __ID = 0
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
        self.__id = str(self.__ID)
        self.__broker_id = self.__id
        Order.__ID += 1
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
        self.__set_time = ModelFeat.get_timestamp(ModelFeat.TIME_MILLISEC)
        self.__execution_price = None
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

    def get_broker_id(self) -> str:
        return self.__broker_id

    def get_type(self) -> str:
        return self.__type

    def _set_status(self, status: str) -> None:
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
        self.__execution_price = prc

    def get_execution_price(self) -> Price:
        if self.__execution_price is None:
            raise Exception("The execution price must be set")
        return self.__execution_price

    def _set_execution_time(self, time: int) -> None:
        self.__execution_time = int(time)

    def get_execution_time(self) -> int:
        if self.__execution_time is None:
            raise Exception("The execution time must be set")
        return self.__execution_time

    def _set_params(self, params: Map) -> None:
        self.__params = params

    def _get_params(self) -> Map:
        return self.__params

    def get_set_time(self) -> int:
        return self.__set_time

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

    '''
    @staticmethod
    def sum_orders(odrs: Map) -> Map:
        """
        To sum orders executed\n
        :param odrs: collection of Order
        :exception ValueError: if collection of order is empty
        :return: amount stilling in each asset
                 Map[Map.left]  => {Price}
                 Map[Map.right] => {Price}
        """
        if len(odrs.get_map()) <= 0:
            raise ValueError("The collection of Order can't be empty")
        ks = odrs.get_keys()
        pr = odrs.get(ks[0]).get_pair()
        pr_str = pr.__str__
        lspot = 0
        rspot = 0
        for _, odr in odrs.get_map().items():
            if pr_str != odr.get_pair().__str__:
                raise Exception(f"All Order must have the same pair of asset: {pr_str}!={odr.get_pair().__str__}")
            if odr.get_status() == Order.STATUS_COMPLETED:
                move = odr.get_move()
                exct = odr.get_execution_price()
                if move == Order.MOVE_BUY:
                    if odr.get_quantity() is not None:
                        qty = odr.get_quantity()
                        lspot += qty.get_value()
                        rspot -= exct.get_value() * qty.get_value()
                    elif odr.get_amount() is not None:
                        amnt = odr.get_amount()
                        lspot += amnt.get_value() / exct.get_value()
                        rspot -= amnt.get_value()
                    else:
                        raise Exception("Unknown Order state")
                elif move == Order.MOVE_SELL:
                    if odr.get_quantity() is not None:
                        qty = odr.get_quantity()
                        lspot -= qty.get_value()
                        rspot += exct.get_value() * qty.get_value()
                    elif odr.get_amount():
                        amnt = odr.get_amount()
                        lspot -= amnt.get_value() / exct.get_value()
                        rspot += amnt.get_value()
                    else:
                        raise Exception("Unknown Order state")
                else:
                    raise Exception("Unknown Order move")
        odrs_sum = Map({
            Map.left: Price(lspot, pr.get_left().get_symbol()),
            Map.right: Price(rspot, pr.get_right().get_symbol())
        })
        return odrs_sum
    '''