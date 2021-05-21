import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.structure.strategies.Stalker.Stalker import Stalker
from model.tools.Map import Map
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestStalker(unittest.TestCase, Stalker):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.pair1 = Pair('?/USDT')
        right_symbol = self.pair1.get_right().get_symbol()
        self.capital1 = Price(15000, right_symbol)
        self.stg_param1 = Map({
            Map.pair: self.pair1,
            Map.maximum: None,
            Map.capital: self.capital1,
            Map.rate: 1,
            Map.number: 3,
            Map.strategy: MinMaxFloor.__name__,
            Map.param: {
                Map.pair: Pair('DOGE/USDT'),
                Map.maximum: None,
                Map.capital: Price(20, right_symbol),
                Map.rate: 1,
                Map.green: {Map.period: 60 * 5},
                Map.red: {Map.period: 60 * 5}
            }
        })
        self.stg = Stalker(self.stg_param1)
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
        exp_stg_to_trade = stg.get_strategy_class()
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
        pair3 = Pair('PAX/USDT')
        stg = self.stg
        bkr = self.bkr
        # Delete well Strategy
        stg._add_active_strategy(pair1)
        stg._add_active_strategy(pair2)
        stg._add_active_strategy(pair3)
        stgs = stg.get_active_strategies()
        exp_nb_active_stg = 1
        stg._delete_active_strategy(bkr, pair1)
        stg._delete_active_strategy(bkr, pair2)
        self.assertEqual(exp_nb_active_stg, len(stgs.get_map()))
        # Pair don't exit
        with self.assertRaises(ValueError):
            stg._delete_active_strategy(bkr, pair1)
        # capital for new Strategy is updated
        self.setUp()
        stg = self.stg
        bkr = self.bkr
        stg._add_active_strategy(pair1)
        stg._add_active_strategy(pair2)
        stg._add_active_strategy(pair3)
        stg._delete_active_strategy(bkr, pair2)
        stgs = stg.get_active_strategies()
        nb_active_stg = len(stgs.get_map())
        max_stg = stg.get_max_strategy()
        # +++
        stg_params = self.stg_param1
        initial_capital = stg_params.get(Map.capital)
        right_symbol = initial_capital.get_asset().get_symbol()
        exp1 = Price((initial_capital.get_value() - initial_capital/max_stg*nb_active_stg) / (max_stg - nb_active_stg),
                     right_symbol
                     )
        result1 = stg._get_strategy_capital()
        self.assertEqual(exp1, result1)

    def test_add_transaction(self) -> None:
        stg = self.stg
        # Add Price with different Asset
        with self.assertRaises(ValueError):
            stg._add_transaction(Price(3, 'BTC'))

    def test_get_total_capital(self) -> None:
        stg = self.stg
        right_symbol = self.pair1.get_right().get_symbol()
        # No transaction
        exp1 = self.capital1
        result1 = stg._get_total_capital()
        self.assertEqual(exp1, result1)
        # With reduce transactions
        amount1 = Price(-1000, right_symbol)
        amount2 = Price(-3000, right_symbol)
        stg._add_transaction(amount1)
        stg._add_transaction(amount2)
        exp2 = self.capital1 + amount1 + amount2
        result2 = stg._get_total_capital()
        self.assertEqual(exp2, result2)

    def test_get_strategy_capital(self) -> None:
        right_symbol = 'USDT'
        capital = Price(15000, right_symbol)
        max_stg = 3
        stg_params = Map(self.stg_param1.get_map())
        stg_params.put(capital, Map.capital)
        stg = Stalker(stg_params)
        # No active Strategy
        exp1 = Price(capital / max_stg, right_symbol)
        result1 = stg._get_strategy_capital()
        self.assertEqual(exp1, result1)
        # 2 active Strategy
        stg._add_active_strategy(Pair('DOGE/USDT'))
        stg._add_active_strategy(Pair('ONG/USDT'))
        exp2 = Price(capital / max_stg, right_symbol)
        result2 = stg._get_strategy_capital()
        self.assertEqual(exp2, result2)
        # Max active Strategy reached
        stg._add_active_strategy(Pair('TRU/USDT'))
        with self.assertRaises(ZeroDivisionError):
            stg._get_strategy_capital()

    def test_generate_strategy(self) -> None:
        pair = Pair('?/USDT')
        stg = Stalker.generate_strategy(Stalker.__name__, Map({
            Map.pair: pair,
            Map.maximum: None,
            Map.capital: 50000,
            Map.rate: 1,
            Map.strategy: MinMaxFloor.__name__,
            Map.param: {
                Map.pair: pair,
                Map.maximum: None,
                Map.capital: 150000,
                Map.rate: 1,
                Map.period: 60 * 60,
                Map.green: {Map.period: 60 * 5},
                Map.red: {Map.period: 60 * 5}
            },
        }))
        stg._add_active_strategy(Pair('DOGE/USDT'))
        stg._get_total_capital()
        stg._get_strategy_capital()

    """
    def test_stalke_market(self) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        print(self.stg._stalk_market(self.bkr))
        Config.update(Config.STAGE_MODE, _stage)
    """


if __name__ == '__main__':
    unittest.main
