import unittest

from config.Config import Config
from model.structure.Bot import Bot
from model.tools.Map import Map
from model.tools.Pair import Pair


class TestBot(unittest.TestCase, Bot):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.bkr = "Binance"
        self.stg = "MinMax"
        self.pair_str = "BTC/USDT"
        self.pair = Pair(self.pair_str)
        self.bkr_params = {
            Map.public: 'public_key',
            Map.secret: 'secret_key',
            Map.test_mode: True
        }
        self.stg_params = {
            Map.pair: self.pair_str,
            Map.maximum: 1000000,
            Map.capital: 15000,
            Map.rate: 0.9,
            Map.period: 60
        }
        self.bot1 = Bot(self.bkr, self.stg, Map({
            self.bkr: self.bkr_params,
            self.stg: self.stg_params
        }))

    def test_json_encode_decode(self) -> None:
        original_obj = self.bot1
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main(verbosity=2)
