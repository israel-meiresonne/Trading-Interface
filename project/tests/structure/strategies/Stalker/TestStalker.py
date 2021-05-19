import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.structure.strategies.Stalker.Stalker import Stalker
from model.tools.Map import Map
from model.tools.Paire import Pair


class TestStalker(unittest.TestCase, Stalker):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.stg = Stalker(Map({
            Map.pair: Pair('?/USDT'),
            Map.maximum: None,
            Map.capital: 20,
            Map.rate: 1,
            Map.number: 3,
            Map.strategy: MinMaxFloor.__name__,
            Map.param: {
                Map.pair: Pair('DOGE/USDT'),
                Map.maximum: None,
                Map.capital: 20,
                Map.rate: 1,
                Map.green: {Map.period: 60 * 5},
                Map.red: {Map.period: 60 * 5}
            }
        }))
        self.bkr = Broker.retrieve(Binance.__name__, Map({Map.api_pb: "api_pb",
                                                          Map.api_sk: "api_sk",
                                                          Map.test_mode: False
                                                          }))

    def test_add_active_strategy(self) -> None:
        pair = Pair('DOGE/USDT')
        stg = self.stg
        stg._add_active_strategy(pair)
        stgs = stg.get_active_strategies()
        exp_nb_stg = 1
        exp_stg_to_trade = stg.get_strategy_to_trade()
        new_stg = stg.get_active_strategy(pair)
        result_stg_pair = new_stg.get_pair()
        self.assertEqual(exp_nb_stg, len(stgs.get_map()))
        self.assertEqual(exp_stg_to_trade, new_stg.__class__.__name__)
        self.assertEqual(pair, result_stg_pair)
        # Active Strategy with pair already exist
        with self.assertRaises(ValueError):
            stg._add_active_strategy(pair)
        # Maxim Active Strategy already reached
        stg._add_active_strategy(Pair('ATM/USDT'))
        stg._add_active_strategy(Pair('PAX/USDT'))
        with self.assertRaises(Exception):
            stg._add_active_strategy(Pair('SNX/USDT'))

    def test_delete_active_strategy(self) -> None:
        pair1 = Pair('DOGE/USDT')
        pair2 = Pair('ATM/USDT')
        stg = self.stg
        bkr = self.bkr
        stg._add_active_strategy(pair1)
        stg._add_active_strategy(pair2)
        stg._add_active_strategy(Pair('PAX/USDT'))
        stgs = stg.get_active_strategies()
        exp_nb_active_stg = 1
        stg._delete_active_strategy(bkr, pair1)
        stg._delete_active_strategy(bkr, pair2)
        self.assertEqual(exp_nb_active_stg, len(stgs.get_map()))
        # Pair don't exit
        with self.assertRaises(ValueError):
            stg._delete_active_strategy(bkr, pair1)

    def test_stalke_market(self) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        print(self.stg._stalke_market(self.bkr))
        Config.update(Config.STAGE_MODE, _stage)


if __name__ == '__main__':
    unittest.main
