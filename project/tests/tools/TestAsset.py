import unittest

from model.tools.Asset import Asset
from model.tools.MyJson import MyJson


class TestAsset(unittest.TestCase):
    def setUp(self) -> None:
        self.sbl1 = "USDT"
        self.sbl2 = "BTC"
        self.a1 = Asset(self.sbl1)

    def test_constructor(self):
        exp_sbl = "usdt"
        exp_name = None
        self.assertEqual(exp_sbl, self.a1.get_symbol())
        self.assertEqual(exp_name, self.a1.get_name())

    def test_json_instantiate(self) -> None:
        original_obj = self.a1
        json_str = original_obj.json_encode()
        decoded_obj = MyJson.json_decode(json_str)
        self.assertEqual(original_obj, decoded_obj)
        self.assertNotEqual(id(original_obj), id(decoded_obj))

    def test__eq__(self):
        # Equal
        a2 = Asset(self.sbl1)
        self.assertEqual(a2, self.a1)
        self.assertTrue(a2 == self.a1)
        self.assertNotEqual(id(a2), id(self.a1))
        # Different
        a3 = Asset(self.sbl2)
        self.assertNotEqual(id(a3), id(self.a1))
        self.assertTrue(a3 != self.a1)
        self.assertNotEqual(id(a3), id(self.a1))

