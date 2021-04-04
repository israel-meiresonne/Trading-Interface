import unittest
from math import pi as _pi

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

    def test_list_slice(self):
        begin = 3
        end = 7
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        exp = [4, 5, 6, 7, 8]
        result = self.list_slice(vals, begin, end)
        self.assertListEqual(exp, result)
        # end >= begin
        with self.assertRaises(ValueError):
            self.list_slice(vals, 4, 1)
        # end or begin is negative
        with self.assertRaises(IndexError):
            self.list_slice(vals, -4, 1)
        # end or begin is negative
        with self.assertRaises(IndexError):
            self.list_slice(vals, 4, len(vals)+1)

    def test_get_slope(self):
        raise Exception("Must implement this test")

    def test_get_slopes(self):
        # Same slopes
        nb_prd = 3
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        exp1 = [None, None, 1, 1, 1, 1, 1, 1, 1]
        result1 = self.get_slopes(vals, nb_prd)
        self.assertListEqual(exp1, result1)
        # Different slopes
        nb_prd = 2
        values = [1, 2, 3, 3, 2, 1, 1, 2, 3]
        exp = [None, 1, 1, 0, -1, -1, 0, 1, 1]
        result = self.get_slopes(values, nb_prd)
        self.assertListEqual(exp, result)

    def test_get_average(self):
        nb_prd = 3
        xs = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        exp1 = [None, None, 2, 3, 4, 5, 6, 7, 8]
        result1 = self.get_averages(xs, nb_prd)
        self.assertListEqual(exp1, result1)
        # less or one period
        with self.assertRaises(ValueError):
            self.get_averages(xs, 1)

    def test_slope_to_degree(self):
        slope0 = 1
        exp0 = 45
        result0 = self.slope_to_degree(slope0)
        self.assertEqual(exp0, result0)


if __name__ == '__main__':
    unittest.main
