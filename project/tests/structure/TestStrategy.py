import unittest

from config.Config import Config
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.strategies.MinMax.MinMax import MinMax
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestStrategy(unittest.TestCase, Strategy):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.sbl1 = "USDT"
        self.sbl2 = "BTC"
        self.pr = Pair(self.sbl2, self.sbl1)
        self.prc = Price(2013, self.sbl1)
        # Strategy
        self.stg_params = Map({
            Map.pair: self.pr,
            Map.capital: Price(2025, self.sbl1),
            Map.maximum: None,
            Map.rate: 0.8,
            Map.period: 60
        })
        self.stg = MinMax(self.stg_params)

    def trade(self, bkr: Broker) -> None:
        pass

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    def stop_trading(self, bkr: Broker) -> None:
        pass

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        pass

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
    
    def test_get_roi(self) -> None:
        pair = Pair('DOGE/USDT')
        right_symbol = pair.get_right().get_symbol()
        market_list = [
            ['0', '0', '0', '0', '1'],
            ['0', '0', '0', '0', '1'],
            ['0', '0', '0', '0', '1'],
            ['0', '0', '0', '0', '1']
        ]
        market_price = BinanceMarketPrice(market_list, '1m', pair)
        stg_params = Map({
            Map.pair: pair,
            Map.capital: Price(1000, right_symbol),
            Map.maximum: None,
            Map.rate: 1,
            Map.period: 60
        })
        stg = MinMax(stg_params)
        exp1 = 0
        result1 = stg.get_roi(market_price)
        self.assertEqual(exp1, result1)

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
