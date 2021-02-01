import unittest
from model.tools.Map import Map


class TestMap(unittest.TestCase, Map):
    def setUp(self) -> None:
        # keys
        self.key1 = "key1"
        self.key2 = "key2"
        self.key3 = "key3"
        self.key4 = "key4"
        # values
        self.val1 = "val1"
        self.val2 = "val2"
        self.val3 = "val3"
        self.val4 = "val4"
        self.mp1 = Map()
        self.mp2 = Map()
        self.mp2.put(self.val2, self.key1)
        self.mp2.put(self.val2, self.key2, self.key1)
        self.mp2.put(self.val2, self.key3, self.key1, self.key2)

    def tearDown(self) -> None:
        self.mp1 = Map()

    def test_put_one_value_in_deep_1(self):
        self.mp1.put(self.val1, self.key1)
        self.assertEqual(self.mp1.get(self.key1), self.val1)

    def test_put_multiple_values_in_deep_1(self):
        self.mp1.put(self.val1, self.key1)
        self.mp1.put(self.val2, self.key2)
        self.assertEqual(self.mp1.get(self.key1), self.val1)
        self.assertEqual(self.mp1.get(self.key2), self.val2)

    def test_update_value_in_deep_1(self):
        self.mp1.put(self.val1, self.key1)
        self.assertEqual(self.mp1.get(self.key1), self.val1)
        self.mp1.put(self.val2, self.key1)
        self.assertEqual(self.mp1.get(self.key1), self.val2)

    def test_put_one_value_in_multiple_deep(self):
        self.mp1.put(self.val1, self.key3, self.key1)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val1)

    def test_put_multiple_values_in_multiple_deep(self):
        self.mp1.put(self.val1, self.key3, self.key1)
        self.mp1.put(self.val2, self.key3, self.key2)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val1)
        self.assertEqual(self.mp1.get(self.key3, self.key2), self.val2)

    def test_update_value_in_multiple_deep(self):
        self.mp1.put(self.val1, self.key3, self.key1)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val1)
        self.mp1.put(self.val2, self.key3, self.key1)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val2)

    def test_update_value_in_multiple_deep_with_deeper_map(self):
        self.mp1.put(self.val1, self.key3, self.key1)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val1)
        self.mp1.put(self.val2, self.key3, self.key1, self.key2)
        self.assertEqual(self.mp1.get(self.key3, self.key1, self.key2), self.val2)

    def test_update_deeper_map_in_value(self):
        self.mp1.put(self.val1, self.key3, self.key1, self.key2)
        self.assertEqual(self.mp1.get(self.key3, self.key1, self.key2), self.val1)
        self.mp1.put(self.val2, self.key3, self.key1)
        self.assertEqual(self.mp1.get(self.key3, self.key1), self.val2)

    def test_get_keys(self):
        exp = [self.key1, self.key2, self.key3]
        result = self.mp2.get_keys()
        self.assertEqual(type(exp), type(result))
        self.assertListEqual(exp, result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
