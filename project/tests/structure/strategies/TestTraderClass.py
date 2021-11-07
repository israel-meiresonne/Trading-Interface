import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.Map import Map
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestTraderClass(unittest.TestCase):
    _BROKER = None
    def setUp(self) -> None:
        stg_params = Map({
            Map.pair: Pair('DOGE/USDT'),
            Map.period: 60 * 5,
            Map.capital: Price(1000, 'USDT'),
            Map.maximum: None,
            Map.rate: 1
        })
        self.stg = Icarus(stg_params)

    def tearDownClass(self) -> None:
        self.broker_switch(False)

    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.init_stage = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
            self._BROKER = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.init_stage
            self._BROKER.close()
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self._BROKER

    def test_get_marketprice(self) -> None:
        bkr = self.broker_switch(True)
        stg = self.stg
        stg._set_broker(bkr)
        stg_period = stg.get_period()
        n_period = 10
        period = 60
        marketprice_1 = stg.get_marketprice(stg_period, n_period)
        marketprice_2 = stg.get_marketprice(period)
        # MarketPrice 1
        self.assertEqual(stg.get_pair(), marketprice_1.get_pair())
        self.assertEqual(n_period, len(marketprice_1.get_closes()))
        # MarketPrice 2
        self.assertEqual(stg.get_pair(), marketprice_2.get_pair())
        self.assertEqual(stg.get_marketprice_n_period(), len(marketprice_2.get_closes()))
        # List of MarketPrice
        marketprices = stg._get_marketprices()
        exp1 = Map({
            stg_period: marketprice_1,
            period: marketprice_2,
        })
        self.assertEqual(exp1, marketprices)
        # Same instance
        exp2 = stg.get_marketprice(period)
        self.assertEqual(id(exp2), id(marketprice_2))
        self.broker_switch(False)
