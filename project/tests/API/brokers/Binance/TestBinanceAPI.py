import unittest

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.Map import Map


class TestBinanceAPI(unittest.TestCase, BinanceAPI):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.rq = BinanceAPI.RQ_SYS_STATUS
        self.rq_with_required = BinanceAPI.RQ_KLINES
        self.prms_with_required = Map({
            Map.symbol: "BTCUSDT",
            Map.interval: "1m",
            Map.startTime: 1612197722624,
            Map.endTime: 1612197722624,
            Map.limit: 10
        })
        self.bapi_test = None # BinanceAPI("api_pb", "api_sk", True)
        self.bapi_prod = None # BinanceAPI("api_pb", "api_sk", False)

    def test_if_return_correct_config__get_request_config(self):
        exp = BinanceAPI._RQ_CONF[self.rq]
        result = self.get_request_config(self.rq)
        self.assertEqual(exp, result)

    def test_if_raise_erorr__get_request_config(self):
        with self.assertRaises(IndexError):
            self.get_request_config(4)

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
        path = Map(self.get_request_config(self.rq)).get(Map.path)
        endp = BinanceAPI._ENDPOINTS[Map.test][0]
        exp = endp + path
        result = self.bapi_test._generate_url(self.rq)
        self.assertEqual(exp, result)

    def test_mode_prod__generate_url(self):
        path = Map(self.get_request_config(self.rq)).get(Map.path)
        endp0 = BinanceAPI._ENDPOINTS[Map.api][0]
        exp1 = endp0 + path
        result1 = self.bapi_prod._generate_url(self.rq)
        self.assertEqual(exp1, result1)
        endp2 = BinanceAPI._ENDPOINTS[Map.api][2]
        exp2 = endp2 + path
        result2 = self.bapi_prod._generate_url(self.rq, 2)
        self.assertEqual(exp2, result2)

    def test_send_request(self):
        rq_cfg_map = BinanceAPI.get_request_config(self.rq_with_required)
        del rq_cfg_map[Map.method]
        with self.assertRaises(Exception):
            self.bapi_test._waitingroom(self.rq_with_required, self.prms_with_required)

    def test_get_interval(self):
        # value returned
        self.assertEqual(60, self.get_interval('1m'))
        self.assertEqual(60*3, self.get_interval('3m'))
        self.assertEqual(60*5, self.get_interval('5m'))
        self.assertEqual(50*15, self.get_interval('15m'))
        self.assertEqual(60*30, self.get_interval('30m'))
        self.assertEqual(60*60, self.get_interval('1h'))
        self.assertEqual(60*60*2, self.get_interval('2h'))
        self.assertEqual(60*60*4, self.get_interval('4h'))
        self.assertEqual(60*60*6, self.get_interval('6h'))
        self.assertEqual(60*60*8, self.get_interval('8h'))
        self.assertEqual(60*60*12, self.get_interval('12h'))
        self.assertEqual(60*60*24, self.get_interval('1d'))
        self.assertEqual(60*60*24*3, self.get_interval('3d'))
        self.assertEqual(60*60*24*7, self.get_interval('1w'))
        self.assertEqual(int(60*60*24*31.5), self.get_interval('1M'))
        # reference
        map_id = id(self._INTERVALS_INT)
        dict_id = id(self._INTERVALS_INT.get_map())
        new_map = self.get_intervals()
        new_map_id = id(new_map)
        new_dict_id = id(new_map.get_map())
        self.assertNotEqual(map_id, new_map_id)
        self.assertNotEqual(dict_id, new_dict_id)

    def test_convert_interval(self):
        # simple test
        prd1 = 60*20
        exp1 = self.INTERVAL_30MIN
        result1 = self.convert_interval(prd1)
        self.assertEqual(exp1, result1)
        # period = 0
        prd2 = 0
        exp2 = self.INTERVAL_1MIN
        result2 = self.convert_interval(prd2)
        self.assertEqual(exp2, result2)
        # period < 0
        prd3 = -1
        exp3 = self.INTERVAL_1MIN
        result3 = self.convert_interval(prd3)
        self.assertEqual(exp3, result3)
        # period > higher supported
        prd4 = 60*60*24*35
        exp4 = self.INTERVAL_1MONTH
        result4 = self.convert_interval(prd4)
        self.assertEqual(exp4, result4)

    def test_symbol_to_pair(self) -> None:
        symbol = 'BNBUSDT'
        exp1 = 'bnb/usdt'
        resul = BinanceAPI.symbol_to_pair(symbol)
        self.assertEqual(exp1, resul)

    def test_fixe_price(self) -> None:
        raise Exception("Must implement this test")

    def test_fixe_quantity(self) -> None:
        raise Exception("Must implement this test")

    def test_get_new_price(self) -> None:
        raise Exception("Must implement this test")

    def test_will_pass_filter(self) -> None:
        raise Exception("Must implement this test")


if __name__ == "__main__":
    unittest.main