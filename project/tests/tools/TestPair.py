import unittest
from model.tools.Asset import Asset
from model.tools.Pair import Pair


class TestPair(unittest.TestCase, Pair):
    def setUp(self) -> None:
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        self.prsbl = self.lsbl + "/" + self.rsbl
        self.exp_lasset = Asset(self.lsbl)
        self.exp_rasset = Asset(self.rsbl)
        self.pr = Pair(self.lsbl, self.rsbl)

    def test_constructor_with_one_param(self):
        pr = Pair(self.prsbl)
        self.assertDictEqual(self.exp_lasset.__dict__, pr.get_left().__dict__)
        self.assertDictEqual(self.exp_rasset.__dict__, pr.get_right().__dict__)

    def test_constructor_with_two_params(self):
        pr = Pair(self.lsbl, self.rsbl)
        self.assertDictEqual(self.exp_lasset.__dict__, pr.get_left().__dict__)
        self.assertDictEqual(self.exp_rasset.__dict__, pr.get_right().__dict__)

    def test_get_merges_symbols(self):
        exp = (self.lsbl + self.rsbl).lower()
        self.assertEqual(exp, self.pr.get_merged_symbols())

    def test__str__(self):
        exp = (self.lsbl + self._get_separator() + self.rsbl).lower()
        self.assertEqual(exp, self.pr.__str__())


if __name__ == "__main__":
    unittest.main