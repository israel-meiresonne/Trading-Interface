import unittest
from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker

from model.structure.strategies.IcarusStalker.IcarusStalker import IcarusStalker
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair

class TestIcarusStalker(unittest.TestCase, IcarusStalker):
    def setUp(self) -> None:
        pass

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
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self.BROKER

    def test_sort_stalk_marketprices(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        pair1 = Pair('BTC/USDT')
        pair2 = Pair('BCH/USDT')
        pair3 = Pair('DOGE/USDT')
        pair4 = Pair('BURGER/USDT')
        pairs = [pair1, pair2, pair3, pair4]
        period = 60*15
        n_period = broker.get_max_n_period()
        streams = [broker.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
        broker.add_streams(streams)
        marketprices = []
        for pair in pairs:
            marketprice = MarketPrice.marketprice(broker, pair, period, n_period)
            marketprices.append(marketprice)
        marketprices_sorted = self._sort_stalk_marketprices(marketprices)
        exp1 = '|'.join([pair.__str__() for pair in pairs])
        result1 = '|'.join([marketprice_sorted.get_pair().__str__() for marketprice_sorted in marketprices_sorted])
        self.assertNotEqual(exp1, result1)
        # End
        self.broker_switch(on=False, stage=Config.STAGE_2)
