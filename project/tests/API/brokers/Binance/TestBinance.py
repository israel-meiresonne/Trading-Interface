import unittest
from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.Map import Map


class TestBinance(unittest.TestCase, Binance):
    def setUp(self) -> None:
        self.api_pb = "val_api_pb"
        self.api_sk = "val_api_sk"
        self.test_mode = True
        self.params = Map({
            Map.public: self.api_pb,
            Map.secret: self.api_sk,
            Map.test_mode: self.test_mode
        })
        # self.bnc = Binance(self.params)

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None

    def broker_switch(self, on: bool = False) -> Binance:
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

    def test_constructor(self):
        # Constructor work
        Binance(self.params)
        # Miss public key
        self.setUp()
        del self.params.get_map()[Map.api_pb]
        with self.assertRaises(IndexError):
            Binance(self.params)
        # Miss secret key
        self.setUp()
        del self.params.get_map()[Map.api_sk]
        with self.assertRaises(IndexError):
            Binance(self.params)
        # Miss test mode
        self.setUp()
        del self.params.get_map()[Map.test_mode]
        with self.assertRaises(IndexError):
            Binance(self.params)

    def test_get_pairs(self) -> None:
        bnc = self.broker_switch(True)
        excludes = BinanceAPI.get_exclude_assets()
        pairs = bnc.get_pairs()
        exists = []
        for exclude in excludes:
            exists = [
                *exists,
                *[pair for pair in pairs if exclude in pair]
                ]
        exp = []
        result = exists
        self.assertListEqual(exp, result)
        self.broker_switch(False)

    def test_json_encode_decode(self) -> None:
        original_obj = Binance(Map({
            Map.public: 'public_key',
            Map.secret: 'private_key',
            Map.test_mode: True
        }))
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main
