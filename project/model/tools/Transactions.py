from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction


class Transactions(MyJson):
    PREFIX_ID = 'transacs_'

    def __init__(self, pair: Pair) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        self.__pair = pair
        self.__transactions = None
    
    def get_id(self) -> str:
        return self.__id

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def get_pair(self) -> Pair:
        return self.__pair
    
    def _get_transactions(self) -> Map:
        if self.__transactions is None:
            self.__transactions = Map()
        return self.__transactions

    def get_transaction(self, transac_id: str) -> Transaction:
        transacs = self._get_transactions()
        if transac_id not in transacs.get_keys():
            raise IndexError(f"This Transaction id don't exist: '{transac_id}'")
        return transacs.get(transac_id)
    
    def ids(self) -> list[str]:
        """
        To get list of id of Transaction

        Returns:
        --------
        return: list[str]
            List of id of Transaction
        """
        return self._get_transactions().get_keys()
    
    def add(self, transaction: Transaction) -> None:
        transaction.get_pair().are_same(self.get_pair())
        transacs = self._get_transactions()
        transacs.put(transaction, transaction.get_id())
        self._sort()
    
    def remove(self, transac_id: str) -> None:
        transacs = self._get_transactions()
        transacs.get_map().pop(transac_id, None)
    
    def _sort(self) -> None:
        transacs = self._get_transactions()
        self.__transactions = Map(sorted(transacs.get_map().items(), key=lambda row: row[1].get_execution_time()))    
    
    def sum(self) -> Map:
        """
        To sum right, left and fee amount of Transaction

        Returns:
        --------
        return: Map
            [Map.left]: sum of Transaction's left amount
            [Map.right]: sum of Transaction's right amount
            [Map.fee]: sum of Transaction's fee amount
        """
        transacs = self._get_transactions()
        pair = self.get_pair()
        rights = [Price(0, pair.get_right())]
        lefts = [Price(0, pair.get_left())]
        fees = [Price(0, pair.get_right())]
        for transac_id, transac in transacs.get_map().items():
            rights.append(transac.get_right())
            lefts.append(transac.get_left())
            fees.append(transac.get_transaction_fee())
        transac_sum = Map({
            Map.left: Price.sum(lefts),
            Map.right: Price.sum(rights),
            Map.fee: Price.sum(fees)
        })
        return transac_sum

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Transactions(Pair('@left/@right'))
        exec(MyJson.get_executable())
        return instance
