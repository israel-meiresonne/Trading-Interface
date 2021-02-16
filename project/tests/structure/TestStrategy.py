import unittest
from decimal import Decimal

from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.strategies.MinMax.MinMax import MinMax
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestStrategy(unittest.TestCase, Strategy):
    def setUp(self) -> None:
        self.sbl1 = "USDT"
        self.sbl2 = "BTC"
        self.pr = Pair(self.sbl2, self.sbl1)
        self.prc = Price(2013, self.sbl1)
        # Strategy
        self.stg_params = Map({
            Map.pair: self.pr,
            Map.capital: Price(2025, self.sbl1),
            Map.rate: 0.8
        })
        self.stg = MinMax(self.stg_params)

    def trade(self, bkr: Broker) -> None:
        pass

    def test_generate_real_capital(self):
        # Max capital and rate are set
        # —> capital < max capital
        capital1 = Price(500, self.sbl1)
        max_cap1 = Price(1000, self.sbl1)
        rate1 = Decimal('0.75')
        exp1 = Price(capital1.get_value() * rate1, self.sbl1)
        result1 = self._generate_real_capital(capital1, max_cap1, rate1)
        self.assertEqual(exp1, result1)
        # —> capital == max capital
        capital2 = Price(1000, self.sbl1)
        max_cap2 = Price(1000, self.sbl1)
        rate2 = Decimal('0.75')
        exp2 = Price(capital2.get_value() * rate2, self.sbl1)
        result2 = self._generate_real_capital(capital2, max_cap2, rate2)
        self.assertEqual(exp2, result2)
        # —> capital > max capital
        capital3 = Price(2000, self.sbl1)
        max_cap3 = Price(1000, self.sbl1)
        rate3 = Decimal('0.75')
        exp3 = Price(1000, self.sbl1)
        result3 = self._generate_real_capital(capital3, max_cap3, rate3)
        self.assertEqual(exp3, result3)
        # Max capital is set
        # —> capital < max capital
        capital4 = Price(200, self.sbl1)
        max_cap4 = Price(1000, self.sbl1)
        exp4 = Price(200, self.sbl1)
        result4 = self._generate_real_capital(capital4, max_cap4, None)
        self.assertEqual(exp4, result4)
        # —> capital == max capital
        capital5 = Price(1000, self.sbl1)
        max_cap5 = Price(1000, self.sbl1)
        exp5 = Price(1000, self.sbl1)
        result5 = self._generate_real_capital(capital5, max_cap5, None)
        self.assertEqual(exp5, result5)
        # —> capital < max capital
        capital6 = Price(3500, self.sbl1)
        max_cap6 = Price(1000, self.sbl1)
        exp6 = Price(1000, self.sbl1)
        result6 = self._generate_real_capital(capital6, max_cap6, None)
        self.assertEqual(exp6, result6)
        # Rate is set
        capital7 = Price(1000, self.sbl1)
        rate7 = Decimal('0.75')
        exp7 = Price(capital7.get_value() * rate7, self.sbl1)
        result7 = self._generate_real_capital(capital7, None, rate7)
        self.assertEqual(exp7, result7)
        # Neither capital and rate are set
        capital8 = Price(450, self.sbl1)
        with self.assertRaises(Exception):
            self._generate_real_capital(capital8, None, None)

    def test_check_max_capital(self):
        # Normal
        max_cap = Price(12, self.sbl1)
        rate = 0.8
        self.assertIsNone(self._check_max_capital(max_cap, rate))
        # Max capital and rate are both null
        with self.assertRaises(ValueError):
            self._check_max_capital(None, None)
        # Max capital = 0
        max_cap = Price(0, self.sbl1)
        with self.assertRaises(ValueError):
            self._check_max_capital(max_cap, None)
        # Max rate <= 0
        rate1 = 0
        rate2 = -1
        with self.assertRaises(ValueError):
            self._check_max_capital(None, rate1)
        with self.assertRaises(ValueError):
            self._check_max_capital(None, rate2)
        # Max rate > 1
        rate3 = 1.1
        with self.assertRaises(ValueError):
            self._check_max_capital(None, rate3)

    def test_retrieve(self):
        exp = MinMax.__name__
        stg_cls = MinMax.__name__
        params = Map({
            Map.pair: self.pr,
            Map.capital: self.prc,
            Map.rate: 0.90,
        })
        stg = self.retrieve(stg_cls, params)
        self.assertEqual(exp, stg.__class__.__name__)


if __name__ == '__main__':
    unittest.main
