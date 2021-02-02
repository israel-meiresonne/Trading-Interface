import unittest
from model.API.brokers.Binance.Binance import Binance
from model.tools.Map import Map


class TestBinance(unittest.TestCase):
    def setUp(self) -> None:
        self.api_pb = "val_api_pb"
        self.api_sk = "val_api_sk"
        self.test_mode = True
        self.cfgs = {
            Map.api_pb: self.api_pb,
            Map.api_sk: self.api_sk,
            Map.test_mode: self.test_mode
        }

    def test_constructor(self):
        Binance(self.cfgs)

    def test_constructor_raise_error(self):
        miss_pk = dict(self.cfgs)
        del miss_pk[Map.api_pb]
        miss_sk = dict(self.cfgs)
        del miss_sk[Map.api_sk]
        miss_mode = dict(self.cfgs)
        del miss_mode[Map.test_mode]
        with self.assertRaises(IndexError):
            Binance(miss_pk)
        with self.assertRaises(IndexError):
            Binance(miss_sk)
        with self.assertRaises(IndexError):
            Binance(miss_mode)


if __name__ == '__main__':
    unittest.main
