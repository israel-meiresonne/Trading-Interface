import unittest

from model.tools.MyJson import MyJson
from model.tools.Price import Price


class TestPrice(unittest.TestCase, Price):
    def setUp(self) -> None:
        self.symbol1 = "USDT"
        self.symbol2 = "BTC"
        self.price1 = Price(1, self.symbol1)
        self.price2 = Price(2, self.symbol1)
        self.price3 = Price(3, self.symbol2)
        self.price4 = Price(4, self.symbol2)

    def test_sum(self) -> None:
        symbol = 'USDT'
        prices = [
            Price(1, symbol),
            Price(2, symbol),
            Price(-3, symbol)
        ]
        exp1 = Price(0, symbol)
        result1 = Price.sum(prices)
        self.assertEqual(exp1, result1)
        # No Price to sum
        self.assertIsNone(Price.sum([]))

    def test_json_encode_decode(self) -> None:
        original_obj = self.price1
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)

    def test__add__(self) -> None:
        exp1 = Price(self.price1.get_value() + self.price2.get_value(), self.symbol1)
        result1 = self.price1 + self.price2
        self.assertEqual(exp1, result1)
        # Other is float|int
        self.setUp()
        with self.assertRaises(ValueError):
            self.price1 + 1
        with self.assertRaises(ValueError):
            self.price1 + 3.4
        # Different Symbol
        self.setUp()
        with self.assertRaises(ValueError):
            self.price1 + self.price3

    def test__sub__(self) -> None:
        exp1 = Price(self.price1.get_value() - self.price2.get_value(), self.symbol1)
        result1 = self.price1 - self.price2
        self.assertEqual(exp1, result1)
        # Other is float|int
        self.setUp()
        with self.assertRaises(ValueError):
            self.price1 - 1
        with self.assertRaises(ValueError):
            self.price1 - 3.4
        # Different Symbol
        self.setUp()
        with self.assertRaises(ValueError):
            self.price1 - self.price3

    def test__mul__(self) -> None:
        # Price X Price
        exp1 = self.price1.get_value() * self.price2.get_value()
        result1 = self.price1 * self.price2
        self.assertEqual(exp1, result1)
        # Price X int
        self.setUp()
        exp2 = self.price1.get_value() * 3
        result2 = self.price1 * 3
        self.assertEqual(exp2, result2)
        # int X Price
        self.setUp()
        exp3 = 4 * self.price1.get_value()
        result3 = 4 * self.price1
        self.assertEqual(exp3, result3)

    def test__truediv__(self) -> None:
        # Price / Price
        exp1 = self.price1.get_value() / self.price2.get_value()
        result1 = self.price1 / self.price2
        self.assertEqual(exp1, result1)
        # Price / int
        self.setUp()
        exp2 = self.price1.get_value() / 3
        result2 = self.price1 / 3
        self.assertEqual(exp2, result2)
        # int / Price
        self.setUp()
        exp3 = 4 / self.price2.get_value()
        result3 = 4 / self.price2
        self.assertEqual(exp3, result3)

    def test__neg__(self) -> None:
        symbol = "SNX"
        price = Price(15, symbol)
        exp1 = Price(-price.get_value(), symbol)
        result1 = -price
        self.assertEqual(exp1, result1)
        self.assertNotEqual(id(price), id(result1))


if __name__ == '__main__':
    unittest.main