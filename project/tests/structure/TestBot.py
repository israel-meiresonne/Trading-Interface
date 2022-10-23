import unittest

from config.Config import Config
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.strategies.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestBot(unittest.TestCase, Bot):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        # Import Strategy
        strategy_name = Strategy.list_strategies()[0]
        exec(_MF.get_import(strategy_name))
        strategy_class = eval(strategy_name)
        # Import Broker
        broker_name = Broker.list_brokers()[0]
        exec(_MF.get_import(broker_name))
        broker_class = eval(broker_name)
        # Bor1
        self.capital1 = capital1 = Price(1000, 'USDT')
        self.pair1 = pair1 = Pair('BTC', capital1.get_asset())
        self.bot1 = bot1 = Bot(capital1, strategy_class, broker_class)
        self.bot2 = bot2 = Bot(capital1, strategy_class, broker_class, pair1)

    def test_json_encode_decode(self) -> None:
        for original_obj in [self.bot1, self.bot2]:
            test_exec = self.get_executable_test_json_encode_decode()
            exec(test_exec)


if __name__ == '__main__':
    unittest.main(verbosity=2)
