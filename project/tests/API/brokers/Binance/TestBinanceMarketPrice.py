import unittest

from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice


class TestBinanceMarketPrice(unittest.TestCase, BinanceMarketPrice):
    def setUp(self) -> None:
        self.closes = ('3', '3', '2', '2', '4', '4', '1', '1', '2', '2', '1', '1')
        self.times = (5, 6, 7, 8, 9, 10)
        self.mkt_list = [
            [self.times[0], '0', '0', '0', self.closes[0]],
            [self.times[1], '0', '0', '0', self.closes[1]],
            [self.times[2], '0', '0', '0', self.closes[2]],
            [self.times[3], '0', '0', '0', self.closes[3]],
            [self.times[4], '0', '0', '0', self.closes[4]],
            [self.times[5], '0', '0', '0', self.closes[5]]
        ]
        self.mkt = BinanceMarketPrice(self.mkt_list, '1m')

    def test_get_times(self):
        exp = list(self.times)
        exp.reverse()
        exp = tuple(exp)
        result = self.mkt.get_times()
        self.assertTupleEqual(exp, result)

    def test_get_time(self):
        # Take the first
        exp_1 = self.times[len(self.times)-1]
        result_1 = self.mkt.get_time()
        self.assertEqual(exp_1, result_1)
        # Take in the middle
        exp_2 = self.times[-3]
        result_2 = self.mkt.get_time(2)
        self.assertEqual(exp_2, result_2)


if __name__ == '__main__':
    unittest.main
