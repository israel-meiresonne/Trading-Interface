import unittest

from model.API.brokers.Binance.Binance import Binance
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice


class TestBrokerRequest(unittest.TestCase, BrokerRequest):
    def _set_market_price(self, prms: Map) -> None:
        pass

    def get_market_price(self) -> MarketPrice:
        pass

    def _set_account_snapshot(self, prms: Map) -> None:
        pass

    def get_account_snapshot(self) -> Map:
        pass

    def generate_request(self) -> Map:
        pass

    def test_get_request_class(self):
        bkr_cls = Binance.__name__
        exp = bkr_cls + self._SUFFIX_REQUEST
        result = BrokerRequest.get_request_class(bkr_cls)
        self.assertEqual(exp, result)


if __name__ == '__main__':
    unittest.main