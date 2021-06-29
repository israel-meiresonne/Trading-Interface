import unittest

from model.structure.strategies.Floor.Floor import Floor
from model.tools.Map import Map
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestFloor(unittest.TestCase, Floor):
    def setUp(self) -> None:
        self.pair1 = Pair('BTC/USDT')
        self.left_symbol1 = self.pair1.get_left().get_symbol()
        self.right_symbol1 = self.pair1.get_right().get_symbol()
        self.stg_params1 = Map({
            Map.pair: self.pair1,
            Map.maximum: Price(1000000, self.right_symbol1),
            Map.capital: Price(15000, self.right_symbol1),
            Map.rate: 1,
            Map.period: 60 * 5
        })
        self.stg1 = Floor(self.stg_params1)

    def test_json_encode_decode(self) -> None:
        original_obj = self.stg1
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main()
