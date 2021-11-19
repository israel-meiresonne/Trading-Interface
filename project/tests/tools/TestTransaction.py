import unittest

from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction


class TestTransaction(unittest.TestCase, Transaction):
    def setUp(self) -> None:
        self.pair = Pair('DOGE/USDT')
        pair = self.pair
        self.right = Price(15, pair.get_right())
        right = self.right
        self.left = Price(5, pair.get_left())
        left = self.left
        self.fee = Price(right*0.001, pair.get_right())
        fee = self.fee
        self.transac1 = Transaction(Transaction.TYPE_DEPOSIT, pair, right, left, fee)
        self.transac2 = Transaction(Transaction.TYPE_WITHDRAWAL, pair, right, left, fee)
    
    def test_get_link(self) -> None:
        transac = self.transac1
        self.assertNotEqual(id(transac._get_link_original()), id(transac.get_link()))
    
    def test_set_type(self) -> None:
        pair = self.pair
        right = self.right
        left = self.left
        fee = self.fee
        with self.assertRaises(ValueError):
            Transaction("hello", pair, right, left, fee)

    def test_set_right(self) -> None:
        pair = self.pair
        right = Price(15, pair.get_left())
        left = self.left
        fee = self.fee
        with self.assertRaises(ValueError):
            Transaction(Transaction.TYPE_DEPOSIT, pair, right, left, fee)

    def test_set_left(self) -> None:
        pair = self.pair
        right = self.right
        left = Price(15, pair.get_right())
        fee = self.fee
        with self.assertRaises(ValueError):
            Transaction(Transaction.TYPE_DEPOSIT, pair, right, left, fee)

    def test_set_fee(self) -> None:
        pair = self.pair
        right = self.right
        left = self.left
        fee = Price(15, pair.get_left())
        with self.assertRaises(ValueError):
            Transaction(Transaction.TYPE_DEPOSIT, pair, right, left, fee)
    
    def test_link(self) -> None:
        trasanc1 = self.transac1
        trasanc2 = self.transac2
        trasanc1.link(trasanc2)
        self.assertTrue(trasanc1.get_id() in trasanc1.get_link())
        self.assertTrue(trasanc1.get_id() in trasanc2.get_link())
        self.assertTrue(trasanc2.get_id() in trasanc2.get_link())
        self.assertTrue(trasanc2.get_id() in trasanc1.get_link())
    
    def test_clone(self) -> None:
        def correct_attribut(t:Transaction, c: Transaction) -> None:
            self.assertNotEqual(t.get_id(), c.get_id())
            self.assertNotEqual(t.get_settime(), c.get_settime())
            self.assertEqual(t.get_type(), c.get_type())
            self.assertEqual(t.get_pair(), c.get_pair())
            self.assertEqual(t.get_right(), c.get_right())
            self.assertEqual(t.get_left(), c.get_left())
            self.assertEqual(t.get_fee(), c.get_fee())
        transac = self.transac1
        # Clone is correct
        clone1 = transac.clone()
        correct_attribut(transac, clone1)
        # Clone have been updated
        transac_type = Transaction.TYPE_SELL
        pair = Pair('hello/fresh')
        right = Price(200, pair.get_right())
        left = Price(20, pair.get_left())
        fee = Price(2, pair.get_right())
        clone2 = transac.clone(type=transac_type, pair=pair, right=right, left=left, fee=fee)
        self.assertNotEqual(transac.get_id(), clone2.get_id())
        self.assertNotEqual(transac.get_settime(), clone2.get_settime())
        self.assertEqual(transac_type, clone2.get_type())
        self.assertEqual(pair, clone2.get_pair())
        self.assertEqual(right, clone2.get_right())
        self.assertEqual(left, clone2.get_left())
        self.assertEqual(fee, clone2.get_fee())
    
    def test_json_encode_decode(self) -> None:
        trasanc = self.transac1
        trasanc.get_link()
        json = trasanc.json_encode()
        trasanc_decoded = MyJson.json_decode(json)
        self.assertIsInstance(trasanc_decoded, Transaction)
        self.assertNotEqual(id(trasanc), id(trasanc_decoded))
        self.assertEqual(trasanc.get_id(), trasanc_decoded.get_id())
        self.assertDictEqual(trasanc.__dict__, trasanc_decoded.__dict__)
