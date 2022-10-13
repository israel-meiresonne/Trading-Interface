import unittest

from model.tools.Asset import Asset
from model.tools.MyJson import MyJson


class TestAsset(unittest.TestCase, Asset):
    def setUp(self) -> None:
        self.sbl1 = "USDT"
        self.sbl2 = "BTC"
        self.a1 = Asset(self.sbl1)

    def test_constructor(self):
        exp_sbl = "usdt"
        exp_name = None
        self.assertEqual(exp_sbl, self.a1.get_symbol())
        self.assertEqual(exp_name, self.a1.get_name())

    def test_json_encode_decode(self) -> None:
        original_obj = self.a1
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)

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

    def test__hash__(self) -> None:
        asset1_str = 'btc'
        asset = Asset(asset1_str)
        #
        exp1 = asset1_str.__hash__()
        result1 = asset.__hash__()
        self.assertEqual(exp1, result1)
        #
        exp1_2 = {asset1_str: asset}
        result1_2 = {asset: asset}
        self.assertDictEqual(exp1_2, result1_2)
        self.assertEqual(result1_2[asset], asset)
        self.assertEqual(result1_2[asset1_str], asset)

