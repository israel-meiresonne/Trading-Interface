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


if __name__ == '__main__':
    unittest.main
