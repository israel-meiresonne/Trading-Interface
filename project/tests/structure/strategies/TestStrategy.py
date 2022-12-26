import unittest
from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker

from model.structure.strategies.Strategy import Strategy
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair
from model.tools.Price import Price

class StrategyChild(Strategy):
    def trade(self) -> int:
        pass

    @classmethod
    def constructor(cls) -> 'StrategyChild':
        return cls.__new__(cls)

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, buy_conditions: list, sell_conditions: list) -> None:
        pass

class TestStrategy(unittest.TestCase, StrategyChild):
    def setUp(self) -> None:
        self.pair1 = pair1 = Pair('BTC/USDT')
        self.r_asset = r_asset = pair1.get_right()
        self.capital = capital = Price(1000, r_asset)
        self.broker_class = broker_class = Binance
        # Strategy
        self.strategy1 = StrategyChild(capital, broker_class)
        self.strategy2 = StrategyChild(capital, broker_class, pair1)

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None

    def broker_switch(self, on: bool = False, stage: str = Config.STAGE_1) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, stage)
            self.BROKER = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.INIT_STAGE
            self.BROKER.close() if self.BROKER is not None else None
            Config.update(Config.STAGE_MODE, init_stage) if init_stage is not None else None
        return self.BROKER

    def test_set_max_position(self) -> None:
        strategy1 = self.strategy1
        strategy2 = self.strategy2
        # Pair is not set
        exp1 = 3
        strategy1.set_max_position(exp1)
        result1 = strategy1.get_max_position()
        self.assertEqual(exp1, result1)
        # Pair is set
        with self.assertRaises(Exception):
            strategy2.set_max_position(10)

    def test_get_broker_pairs(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        period_1min = Broker.PERIOD_1MIN
        broker_str = self.broker_class.__name__
        r_asset = self.r_asset
        strategy1 = self.strategy1
        strategy1.set_broker(broker)
        strategy2 = self.strategy2
        strategy2.set_broker(broker)
        pair1 = self.pair1
        streams = broker.generate_streams([pair1], [period_1min])
        broker.add_streams(streams)
        # Pair is not set
        exp1 = MarketPrice.get_spot_pairs(broker_str, r_asset)
        result1 = strategy1.get_broker_pairs()
        self.assertListEqual(exp1, result1)
        # Pair is set
        exp2 = [pair1]
        result2 = strategy2.get_broker_pairs()
        self.assertListEqual(exp2, result2)
        # End
        self.broker_switch(on=False, stage=Config.STAGE_2)

    def test_set_pair(self) -> None:
        strategy1 = self.strategy1
        strategy2 = self.strategy2
        pair1 = self.pair1
        # Pair is not set
        result1 = strategy1.get_pair()
        self.assertIsNone(result1)
        # Pair is set
        exp2 = pair1
        result2 = strategy2.get_pair()
        self.assertEqual(exp2, result2)
        # Set Pair
        strategy1._set_pair(pair1)
        exp3 = pair1
        result3 = strategy1.get_pair()
        self.assertEqual(exp3, result3)
        # Reset
        self.setUp()
        strategy1 = self.strategy1
        strategy2 = self.strategy2
        pair2 = Pair('BTC/BUSD')
        # Wrong right Asset
        with self.assertRaises(TypeError):
            strategy1._set_pair(pair2)

    def test_set_sleep_trade(self) -> None:
        strategy1 = self.strategy1
        # Normal
        exp1 = 23031997
        strategy1.set_sleep_trade(exp1)
        result1 = strategy1.get_sleep_trade()
        self.assertEqual(exp1, result1)
        # Wront type
        with self.assertRaises(TypeError):
            strategy1.set_sleep_trade(str(exp1))

    def test_get_path_backtest_file(self) -> None:
        session_id = Config.get(Config.SESSION_ID)
        child_class_name = StrategyChild.__name__
        files_dir = f'content/sessions/running/{session_id}/backtest_{child_class_name}/'
        backtest_file =         [f'{files_dir}{session_id}_backtest.csv',               StrategyChild.get_path_backtest_file(Map.test)]
        trade_file =            [f'{files_dir}{session_id}_trades.csv',                 StrategyChild.get_path_backtest_file(Map.trade)]
        buy_condition_file =    [f'{files_dir}{session_id}_condition_{Map.buy}.csv',    StrategyChild.get_path_backtest_file(Map.condition, **{Map.side: Map.buy})]
        sell_condition_file =   [f'{files_dir}{session_id}_condition_{Map.sell}.csv',   StrategyChild.get_path_backtest_file(Map.condition, **{Map.side: Map.sell})]
        self.assertEqual(backtest_file[0],          backtest_file[1])
        self.assertEqual(trade_file[0],             trade_file[1])
        self.assertEqual(buy_condition_file[0],     buy_condition_file[1])
        self.assertEqual(sell_condition_file[0],    sell_condition_file[1])
        # Unkwon file
        with self.assertRaises(ValueError):
            StrategyChild.get_path_backtest_file('Unkwon_file')