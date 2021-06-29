import unittest
from model.API.brokers.Binance.Binance import Binance
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
