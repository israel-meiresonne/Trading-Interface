import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.structure.strategies.Stalker.Stalker import Stalker
from model.tools.Map import Map
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestStalker(unittest.TestCase, Stalker):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.pair1 = Pair('?/USDT')
        right_symbol = self.pair1.get_right().get_symbol()
        self.capital1 = Price(15000, right_symbol)
        self.max_stg1 = 3
        self.child_stg_period1 = 60 * 30
        self.child_stg_period2 = 60 * 15
        self.child_stg_period3 = 60 * 1
        self.stg_param1 = Map({
            Map.pair: self.pair1,
            Map.maximum: None,
            Map.capital: self.capital1,
            Map.rate: 1,
            Map.number: self.max_stg1,
            Map.strategy: MinMaxFloor.__name__,
            Map.param: {
                Map.pair: Pair('DOGE/USDT'),
                Map.maximum: None,
                Map.capital: Price(20, right_symbol),
                Map.rate: 1,
                Map.period: self.child_stg_period1,
                Map.green: {Map.period: self.child_stg_period2},
                Map.red: {Map.period: self.child_stg_period3}
            }
        })
        self.stg = Stalker(self.stg_param1)
        self.bkr = Broker.retrieve(Binance.__name__, Map({Map.api_pb: "api_pb",
                                                          Map.api_sk: "api_sk",
                                                          Map.test_mode: False
                                                          }))

    def test_active_strategies_is_full(self) -> None:
        stg_params = self.stg_param1
        stg_params.put(3, Map.number)
        init_max_stg = Stalker._CONST_MAX_STRATEGY
        Stalker._CONST_MAX_STRATEGY = 3
        stg = Stalker(stg_params)
        # False with any active Strategy
        result1 = stg.active_strategies_is_full()
        self.assertFalse(result1)
        # False with some active Strategy
        stg._add_active_strategy(Pair('DOGE/USDT'))
        stg._add_active_strategy(Pair('FIS/USDT'))
        result2 = stg.active_strategies_is_full()
        self.assertFalse(result2)
        # True
        stg._add_active_strategy(Pair('TRU/USDT'))
        result3 = stg.active_strategies_is_full()
        self.assertTrue(result3)
        Stalker._CONST_MAX_STRATEGY = init_max_stg

    def test_set_next_stalk(self) -> None:
        unix_time = 1621164878              # GMT: 16/05/21 11h34:38
        unix_rounded = 1621164600           # GMT: 16/05/21 11h30:00
        # Map.period is set in child Strategy
        period = self.child_stg_period1
        exp1 = unix_rounded + period        # + 15min => 16/05/21 11h45:00
        self.stg._set_next_stalk(unix_time)
        result1 = self.stg.get_next_stalk()
        self.assertEqual(exp1, result1)
        # Map.period of child Strategy is bellow Stalker's minimum stalk interval
        self.setUp()
        self.stg_param1.put(1, Map.param, Map.period)
        stg2 = Stalker(self.stg_param1)
        exp2 = unix_rounded + Stalker.get_minimum_stalk_interval()
        stg2._set_next_stalk(unix_time)
        result2 = stg2.get_next_stalk()
        self.assertEqual(exp2, result2)
        # Map.period is not set in child Strategy
        self.setUp()
        del self.stg_param1.get(Map.param)[Map.period]
        stg3 = Stalker(self.stg_param1)
        exp3 = unix_rounded + Stalker.get_minimum_stalk_interval()
        stg3._set_next_stalk(unix_time)
        result3 = stg3.get_next_stalk()
        self.assertEqual(exp3, result3)

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

    def test_blacklist_pair(self) -> None:
        pair1 = Pair('DOGE/USDT')
        pair2 = Pair('BTC/USDT')
        pair3 = Pair('DOGE/USDT')
        pair4 = Pair('UNFI/USDT')
        stg = self.stg
        stg._blacklist_pair(pair1)
        stg._blacklist_pair(pair2)
        blacklist = stg.get_blacklist()
        self.assertTrue(pair1 in blacklist)     # same pair and reference
        self.assertTrue(pair3 in blacklist)     # same pair only
        self.assertFalse(pair4 in blacklist)    # different pair
        # Pair already exist (same pair and reference)
        with self.assertRaises(ValueError):
            stg._blacklist_pair(pair1)
        # Pair already exist (same pair only)
        with self.assertRaises(ValueError):
            stg._blacklist_pair(pair3)

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

    def test_json_encode_decode(self) -> None:
        original_obj = self.stg
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main
