import unittest
from model.API.brokers.Binance.Binance import Binance
from model.tools.Map import Map


class TestBinance(unittest.TestCase):
    def setUp(self) -> None:
        self.api_pb = "val_api_pb"
        self.api_sk = "val_api_sk"
        self.test_mode = True
        self.params = Map({
            Map.api_pb: self.api_pb,
            Map.api_sk: self.api_sk,
            Map.test_mode: self.test_mode
        })

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


if __name__ == '__main__':
    unittest.main
