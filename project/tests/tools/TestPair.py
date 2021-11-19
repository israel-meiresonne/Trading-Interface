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

    def test_constructor_with_one_param(self) -> None:
        pr = Pair(self.prsbl)
        self.assertDictEqual(self.exp_lasset.__dict__, pr.get_left().__dict__)
        self.assertDictEqual(self.exp_rasset.__dict__, pr.get_right().__dict__)

    def test_constructor_with_two_params(self) -> None:
        # Params are string
        pr = Pair(self.lsbl, self.rsbl)
        self.assertDictEqual(self.exp_lasset.__dict__, pr.get_left().__dict__)
        self.assertDictEqual(self.exp_rasset.__dict__, pr.get_right().__dict__)
        # Params are Asset
        left = self.exp_lasset
        right = self.exp_rasset
        pair = Pair(left, right)
        self.assertEqual(left, pair.get_left())
        self.assertEqual(right, pair.get_right())

    def test_get_merges_symbols(self) -> None:
        exp = (self.lsbl + self.rsbl).lower()
        self.assertEqual(exp, self.pr.get_merged_symbols())
    
    def test_format(self) -> None:
        pair = self.pr
        exp1 = f"{pair.get_left()}%{pair.get_right()}"
        result1 = pair.format(f"{Pair.LEFT}%{Pair.RIGHT}")
        self.assertEqual(exp1, result1)

    def test_json_encode_decode(self) -> None:
        original_obj = self.pr
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)

    def test__str__(self):
        exp = (self.lsbl + self._get_separator() + self.rsbl).lower()
        self.assertEqual(exp, self.pr.__str__())


if __name__ == "__main__":
    unittest.main