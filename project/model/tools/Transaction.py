from typing import List

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class Transaction(MyJson):
    PREFIX_ID = 'transac_'
    TYPE_DEPOSIT = 'TYPE_DEPOSIT'
    TYPE_WITHDRAWAL = 'TYPE_WITHDRAWAL'
    TYPE_BUY = 'TYPE_BUY'
    TYPE_SELL = 'TYPE_SELL'
    _TYPES = [TYPE_DEPOSIT, TYPE_WITHDRAWAL, TYPE_BUY, TYPE_SELL]
    
    def __init__(self, type: str, pair: Pair, right: Price, left: Price, fee: Price) -> None:
        self._set_attributs()
        self._set_id()
        self._set_settime()
        self._set_transaction_type(type)
        self._set_pair(pair)
        self._set_right(right)
        self._set_left(left)
        self._set_transaction_fee(fee)
    
    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————
    
    def _set_attributs(self) -> None:
        self.__id = None
        self.__settime = None
        self.__execution_time = None
        self.__link = None
        self.__transaction_type = None
        self.__pair = None
        self.__right = None
        self.__left = None
        self.__transaction_fee = None

    def _set_id(self) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> None:
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

    def _set_execution_time(self, execution_time: int) -> None:
        self.__execution_time = execution_time
        
    def get_execution_time(self) -> int:
        """
        To get unix time of when the Transaction has been executed in millisecond

        Returns:
        --------
        return: int
            The unix time of when the Transaction has been executed
        """
        exec_time = self.__execution_time
        return exec_time if exec_time is not None else self.get_settime()

    def _get_link_original(self) -> List[str]:
        """
        To get List of Transaction ID linked to this Transaction

        Returns:
        --------
        return: List[str]
            List of Transaction ID linked to this Transaction
        """
        if self.__link is None:
            self.__link = [self.get_id()]
        return self.__link

    def get_link(self) -> List[str]:
        link = self._get_link_original()
        return link.copy()

    def _set_transaction_type(self, transaction_type: str) -> None:
        if transaction_type not in self.get_types():
            raise ValueError(f"This type is not supported {transaction_type}")
        self.__transaction_type = transaction_type
        
    def get_transaction_type(self) -> str:
        return self.__transaction_type

    def _set_pair(self, pair: Pair) -> None:
        if not isinstance(pair, Pair):
            raise ValueError(f"The pair '{pair}' must be of type Pair, instead '{type(pair)}': ")
        self.__pair = pair
        
    def get_pair(self) -> Pair:
        return self.__pair

    def _set_right(self, right: Price) -> None:
        if right.get_asset() != self.get_pair().get_right():
            raise ValueError(f"The right amount's Asset '{right}' must match Pair's right '{self.get_pair()}'")
        self.__right = right
        
    def get_right(self) -> Price:
        """
        To get Transaction amount in Transaction.pair’s right Asset

        Returns:
        --------
        return: Price
            The Transaction amount in Transaction.pair’s right Asset
        """
        return self.__right

    def _set_left(self, left: Price) -> None:
        if left.get_asset() != self.get_pair().get_left():
            raise ValueError(f"The left amount's Asset '{left}' must match Pair's left '{self.get_pair()}'")
        self.__left = left
        
    def get_left(self) -> Price:
        """
        To get Transaction amount in Transaction.pair’s left Asset

        Returns:
        --------
        return: Price
            The Transaction amount in Transaction.pair’s left Asset
        """
        return self.__left

    def _set_transaction_fee(self, fee: Price) -> None:
        if fee.get_asset() != self.get_pair().get_right():
            raise ValueError(f"The fee's Asset '{fee}' must match Transaction.pair's right Asset '{self.get_pair()}'")
        self.__transaction_fee = fee
        
    def get_transaction_fee(self) -> Price:
        """
        To get fee charged for the Transaction in Transaction.pair’s right Asset

        Returns:
        --------
        return: Price
            The fee charged for the Transaction in Transaction.pair’s right Asset
        """
        return self.__transaction_fee

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    def link(self, transaction: 'Transaction') -> None:
        self._get_link_original().append(transaction.get_id())
        transaction._get_link_original().append(self.get_id())
    
    def clone(self, type: str = None, pair: Pair = None, right: Price = None, left: Price = None, fee: Price = None) -> 'Transaction':
        """
        To copy this Transaction with a new id and new set time

        Return:
        -------
        return: Transaction
            This Transaction with a new id
        """
        clone = self.copy()
        clone._set_id()
        clone._set_settime()
        clone._set_type(type) if type is not None else None
        clone._set_pair(pair) if pair is not None else None
        clone._set_right(right) if right is not None else None
        clone._set_left(left) if left is not None else None
        clone._set_transaction_fee(fee) if fee is not None else None
        return clone

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER DOWN ——————————————————————————————————————————

    @staticmethod
    def get_types() -> list:
        return Transaction._TYPES
    
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————
    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Transaction(type=Transaction.TYPE_DEPOSIT, pair=Pair('@left/@right'), right=Price(10, '@right'), left=Price(100, '@left'), fee=Price(1, '@right'))
        exec(MyJson.get_executable())
        return instance
    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
