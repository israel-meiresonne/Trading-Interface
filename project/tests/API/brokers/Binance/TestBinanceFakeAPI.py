import time
import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.Pair import Pair


class TestBinanceFakeAPI(unittest.TestCase, BinanceFakeAPI):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None
    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
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

    def test_get_time(self) -> None:
        broker = self.broker_switch(True)
        _cls = BinanceFakeAPI
        pair = Pair('RAMP/USDT')
        pair_merged = pair.format(Pair.FORMAT_MERGED)
        end = False
        while not end:
            api_time = int(_cls._get_time(pair_merged)/1000)
            close = _cls._get_actual_close(pair_merged)
            text = f"api_time='{_MF.unix_to_date(api_time)}' == close='{close}'"
            print(_MF.prefix() + text)
            time.sleep(1)
        self.broker_switch(False)
