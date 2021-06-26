import unittest

from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.tools.Map import Map
from model.tools.Pair import Pair


class TestMinMaxFloor(unittest.TestCase, MinMaxFloor):
    def setUp(self) -> None:
        pass

    def test_generate_strategy(self) -> None:
        green_period = 60 * 15
        red_period = 60 * 5
        params = Map({
            Map.pair: Pair('DOGE/USDT'),
            Map.maximum: None,
            Map.capital: 1000,
            Map.rate: 1,
            Map.green: {
                Map.maximum: None,
                Map.capital: 1000,
                Map.rate: 1,
                Map.period: green_period
            },
            Map.red: {
                Map.maximum: None,
                Map.capital: 1000,
                Map.rate: 1,
                Map.period: red_period
            }
        })
        stg = MinMaxFloor.generate_strategy(MinMaxFloor.__name__, params)
        green_stg = stg.get_green_strategy()
        red_stg = stg.get_red_strategy()
        # Test Pair references
        self.assertEqual(id(stg.get_pair()), id(green_stg.get_pair()))
        self.assertEqual(id(stg.get_pair()), id(red_stg.get_pair()))
        # Test Orders references
        self.assertEqual(id(stg._get_orders()), id(green_stg._get_orders()))
        self.assertEqual(id(stg._get_orders()), id(red_stg._get_orders()))
        # Test Periods
        self.assertEqual(green_stg.get_best_period(), green_period)
        self.assertEqual(red_stg.get_best_period(), red_period)
        # Test capital value
        self.assertEqual(stg._get_capital(), green_stg._get_capital())
        self.assertEqual(stg._get_capital(), red_stg._get_capital())


if __name__ == '__main__':
    unittest.main