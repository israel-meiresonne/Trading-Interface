import unittest
from model.structure.database.ModelFeature import ModelFeature


class TestModelFeature(unittest.TestCase, ModelFeature):
    def test_keys_exist(self) -> None:
        d = {"a": 1, "b": None, "c": "3", "d": ""}
        ks = ['a', 'b', 'c', 'd']
        self.assertIsNone(self.keys_exist(ks, d))

    def test_if_dict_miss_key__keys_exist(self):
        d = {"a": 1, "b": None, "c": "3"}
        ks = ['a', 'b', 'c', 'd']
        exp = 'd'
        result = self.keys_exist(ks, d)
        self.assertEqual(exp, result)

    def test_if_list_miss_key__keys_exist(self):
        d = {"a": 1, "b": None, "c": "3", "d": ""}
        ks = ['a', 'b', 'c']
        self.assertIsNone(self.keys_exist(ks, d))

    def test_clean_dict(self) -> None:
        d = {"a": 1, "b": None, "c": "3", "d": ""}
        exp = {'a': 1, 'c': '3'}
        result = self.clean(d)
        self.assertDictEqual(exp, result)

    def test_clean_list(self) -> None:
        d = ['a', None, 'c', '']
        exp = ['a', 'c']
        result = self.clean(d)
        self.assertListEqual(exp, result)

    def test_clean_raise_error(self) -> None:
        with self.assertRaises(ValueError):
            self.clean(4)

    def test_get_maximums(self):
        d = [1, 4, 2, 6, 6, 3, 7, 7]
        exp = (1, 3)
        result = self.get_maximums(d)
        self.assertTupleEqual(exp, result)

    def test_get_minimums(self):
        d = [1, 4, 2, 6, 3, 3, 7, 5, 5]
        exp = (2, 4)
        result = self.get_minimums(d)
        self.assertTupleEqual(exp, result)

    def test_get_maximum(self):
        # Interval 1
        #      0  1  2  3  4  5  6  7  8
        ds0 = [1, 4, 2, 6, 3, 3, 7, 5, 5]
        exp0 = 6
        result0 = self.get_maximum(ds0, 0, 8)
        self.assertEqual(exp0, result0)
        # Interval 2
        ds1 = [1, 4, 2, 6, 3, 3, 7, 5, 5]
        exp1 = 3
        result1 = self.get_maximum(ds1, 2, 4)
        self.assertEqual(exp1, result1)
        # There's no maximum
        ds2 = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        result2 = self.get_maximum(ds2, 3, 6)
        self.assertIsNone(result2)
        # max_idx is out of bound
        with self.assertRaises(IndexError):
            self.get_maximum(ds2, 0, len(ds2)+1)
        # min_idx >= max_idx
        with self.assertRaises(ValueError):
            self.get_maximum(ds2, 5, 5)
        with self.assertRaises(ValueError):
            self.get_maximum(ds2, 6, 5)


if __name__ == '__main__':
    unittest.main
