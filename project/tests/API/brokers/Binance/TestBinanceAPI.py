import unittest

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.Map import Map


class TestBinanceAPI(unittest.TestCase, BinanceAPI):
    def setUp(self) -> None:
        self.rq = BinanceAPI.RQ_SYS_STATUS
        self.rq_with_required = BinanceAPI.RQ_KLINES
        self.prms_with_required = Map({
            Map.symbol: "BTCUSDT",
            Map.interval: "1m",
            Map.startTime: 1612197722624,
            Map.endTime: 1612197722624,
            Map.limit: 10
        })
        self.bapi_test = BinanceAPI("api_pb", "api_sk", True)
        self.bapi_prod = BinanceAPI("api_pb", "api_sk", False)

    def test_if_return_correct_config__get_request_config(self):
        exp = BinanceAPI._RQ_CONF[self.rq]
        result = self._get_request_config(self.rq)
        self.assertEqual(exp, result)

    def test_if_raise_erorr__get_request_config(self):
        with self.assertRaises(IndexError):
            self._get_request_config(4)

    def test_if_return_true__check_params(self):
        self.assertTrue(self._check_params(self.rq_with_required, self.prms_with_required))

    def test_when_miss_required_param__check_params(self):
        del self.prms_with_required.get_map()[Map.symbol]
        with self.assertRaises(IndexError):
            self._check_params(self.rq_with_required, self.prms_with_required)

    def test_given_not_available_param__check_params(self):
        self.prms_with_required.put(4000, Map.recvWindow)
        with self.assertRaises(Exception):
            self._check_params(self.rq_with_required, self.prms_with_required)

    def test_when_miss_not_required_param__check_params(self):
        hold_keys = self.prms_with_required.get_keys()
        del self.prms_with_required.get_map()[hold_keys[len(hold_keys)-1]]
        new_keys = self.prms_with_required.get_keys()
        exp_keys = list(hold_keys)
        del exp_keys[len(exp_keys)-1]
        self.assertLess(len(new_keys), len(hold_keys))
        self.assertListEqual(exp_keys, new_keys)
        self.assertTrue(self._check_params(self.rq_with_required, self.prms_with_required))

    def test_mode_test__generate_url(self):
        path = Map(self._get_request_config(self.rq)).get(Map.path)
        endp = BinanceAPI._ENDPOINTS[Map.test][0]
        exp = endp + path
        result = self.bapi_test._generate_url(self.rq)
        self.assertEqual(exp, result)

    def test_mode_prod__generate_url(self):
        path = Map(self._get_request_config(self.rq)).get(Map.path)
        endp0 = BinanceAPI._ENDPOINTS[Map.api][0]
        exp1 = endp0 + path
        result1 = self.bapi_prod._generate_url(self.rq)
        self.assertEqual(exp1, result1)
        endp2 = BinanceAPI._ENDPOINTS[Map.api][2]
        exp2 = endp2 + path
        result2 = self.bapi_prod._generate_url(self.rq, 2)
        self.assertEqual(exp2, result2)

    def test__send_request(self):
        rq_cfg_map = BinanceAPI._get_request_config(self.rq_with_required)
        del rq_cfg_map[Map.method]
        with self.assertRaises(Exception):
            self.bapi_test._send_request(self.rq_with_required, self.prms_with_required)


if __name__ == "__main__":
    unittest.main