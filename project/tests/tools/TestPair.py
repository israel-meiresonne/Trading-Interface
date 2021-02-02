import unittest
from model.tools.Asset import Asset
from model.tools.Paire import Pair


class TestPair(unittest.TestCase):
    def setUp(self) -> None:
        self.bcd = "BTC"
        self.scd = "USDT"
        self.prcd = self.bcd + "/" + self.scd
        self.exp_basst = Asset(self.bcd)
        self.exp_sasst = Asset(self.scd)

    def test_constructor_with_one_param(self):
        pr = Pair(self.prcd)
        self.assertDictEqual(self.exp_basst.__dict__, pr.get_to_buy().__dict__)
        self.assertDictEqual(self.exp_sasst.__dict__, pr.get_to_sell().__dict__)

    def test_constructor_with_two_params(self):
        pr = Pair(self.bcd, self.scd)
        self.assertDictEqual(self.exp_basst.__dict__, pr.get_to_buy().__dict__)
        self.assertDictEqual(self.exp_sasst.__dict__, pr.get_to_sell().__dict__)


if __name__ == "__main__":
    unittest.main