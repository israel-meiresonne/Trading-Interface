import unittest

from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction
from model.tools.Transactions import Transactions


class TestTransactions(unittest.TestCase, Transactions, Transaction):
    def setUp(self) -> None:
        self.pair = Pair('DOGE/USDT')
        pair = self.pair
        self.transacs1 = Transactions(pair)
        self.transac1 = Transaction(Transaction.TYPE_DEPOSIT, pair, Price(100, pair.get_right()), Price(10, pair.get_left()), Price(1, pair.get_right()))
        self.transac2 = Transaction(Transaction.TYPE_WITHDRAWAL, pair, Price(300, pair.get_right()), Price(30, pair.get_left()), Price(3, pair.get_right()))
        self.transac3 = Transaction(Transaction.TYPE_SELL, pair, Price(500, pair.get_right()), Price(50, pair.get_left()), Price(5, pair.get_right()))
        self.transac4 = Transaction(Transaction.TYPE_BUY, pair, Price(-700, pair.get_right()), Price(-70, pair.get_left()), Price(-7, pair.get_right()))

    def test_get_transaction(self) -> None:
        transacs = self.transacs1
        transac1 = self.transac1
        transac2 = self.transac2
        transac3 = self.transac3
        transac4 = self.transac4
        transacs.add(transac3)
        transacs.add(transac2)
        transacs.add(transac1)
        # Get Trannsaction
        exp2 = id(transac2)
        result2 = id(transacs.get_transaction(transac2.get_id()))
        self.assertEqual(exp2, result2)
        # id don't exist
        with self.assertRaises(IndexError):
            transacs.get_transaction(transac4.get_id())

    def test_add(self) -> None:
        transacs = self.transacs1
        transac1 = self.transac1
        transac1._set_execution_time(1)
        transac2 = self.transac2
        transac2._set_execution_time(2)
        transac3 = self.transac3
        transac3._set_execution_time(3)
        pair = Pair('BTC/USDT')
        transacx = Transaction(Transaction.TYPE_BUY, pair, Price(700, pair.get_right()), Price(70, pair.get_left()), Price(7, pair.get_right()))
        transacs.add(transac3)
        transacs.add(transac2)
        transacs.add(transac1)
        # Lenght
        exp2 = 3
        result2 = len(transacs._get_transactions().get_map())
        self.assertEqual(exp2, result2)
        # Transaction's id is in Transaction
        self.assertTrue(transac1.get_id() in transacs._get_transactions().get_keys())
        self.assertTrue(transac2.get_id() in transacs._get_transactions().get_keys())
        self.assertTrue(transac3.get_id() in transacs._get_transactions().get_keys())
        # Sorted from older to most recent
        exp2 = [1, 2, 3]
        result2 = [transac.get_execution_time() for transac_id, transac in transacs._get_transactions().get_map().items()]
        self.assertListEqual(exp2, result2)
        # Pair are different
        with self.assertRaises(ValueError):
            transacs.add(transacx)

    def test_remove_transaction(self) -> None:
        transacs = self.transacs1
        transac1 = self.transac1
        transac2 = self.transac2
        transac3 = self.transac3
        transacs.add(transac3)
        transacs.add(transac2)
        transacs.add(transac1)
        transacs.remove(transac2.get_id())
        exp2 = 2
        result2 =len(transacs.ids())
        self.assertEqual(exp2, result2)
        self.assertFalse(transac2.get_id() in transacs.ids())
    
    def test_sum(self) -> None:
        transacs = self.transacs1
        transac1 = self.transac1
        transac2 = self.transac2
        transac3 = self.transac3
        transac4 = self.transac4
        transac_list = [transac1, transac2, transac3, transac4]
        # Empty
        exp1 =  Map({
            Map.left: Price(0, transacs.get_pair().get_left()),
            Map.right: Price(0, transacs.get_pair().get_right()),
            Map.fee: Price(0, transacs.get_pair().get_right())
        })
        result1 = transacs.sum()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Not empty
        transacs.add(transac3)
        transacs.add(transac2)
        transacs.add(transac4)
        transacs.add(transac1)
        exp2 =  Map({
            Map.left: Price.sum([transac.get_left() for transac in transac_list]),
            Map.right: Price.sum([transac.get_right() for transac in transac_list]),
            Map.fee: Price.sum([transac.get_fee() for transac in transac_list])
        })
        result2 = transacs.sum()
        self.assertDictEqual(exp2.get_map(), result2.get_map())
    
    def test_json_encode_decode(self) -> None:
        transacs = self.transacs1
        transac1 = self.transac1
        transac4 = self.transac4
        transacs.add(transac1)
        transacs.add(transac4)
        json = transacs.json_encode()
        trasancs_decoded = MyJson.json_decode(json)
        self.assertIsInstance(trasancs_decoded, Transactions)
        self.assertNotEqual(id(transacs), id(trasancs_decoded))
        self.assertEqual(transacs.get_id(), trasancs_decoded.get_id())
        self.assertDictEqual(transacs.__dict__, trasancs_decoded.__dict__)
