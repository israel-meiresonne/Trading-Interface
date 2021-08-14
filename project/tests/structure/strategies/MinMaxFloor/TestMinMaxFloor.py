import unittest

from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.tools.Map import Map
from model.tools.Pair import Pair


class TestMinMaxFloor(unittest.TestCase, MinMaxFloor):
    def setUp(self) -> None:
        self.pair1 = Pair('BTC/USDT')
        self.left_symbol1 = self.pair1.get_left().get_symbol()
        self.right_symbol1 = self.pair1.get_right().get_symbol()
        self.stg_params1 = Map({
            Map.pair: self.pair1,
            Map.maximum: 1000000,
            Map.capital: 15000,
            Map.rate: 1,
            Map.period: 60 * 60,
            Map.green: {Map.period: 60 * 5},
            Map.red: {Map.period: 60 * 3}
        })
        self.stg1 = MinMaxFloor.generate_strategy(MinMaxFloor.__name__, self.stg_params1)

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

    def test_json_encode_decode(self) -> None:
        original_obj = self.stg1
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main