import unittest

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.database.ModelFeature import ModelFeature
from model.tools.Map import Map
from model.tools.Paire import Pair


class TestBinanceRequest(unittest.TestCase, BinanceRequest):
    def setUp(self) -> None:
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.timestamp = ModelFeature.get_timestamp()
        self.week = 3600*24*7
        self.prd = 60
        self.nb_prd = 10
        self.timeout = 100
        # market price
        self.mkt_prc_params = Map({
            Map.pair: self.pr,
            Map.period: self.prd,
            Map.begin_time: self.timestamp,
            Map.end_time: self.timestamp - self.week,
            Map.number: self.nb_prd,
        })
        self.mkt_prc_request = Map({
            Map.symbol: self.pr.get_merged_symbols().upper(),
            Map.interval: BinanceAPI.convert_interval(self.prd),
            Map.startTime: self.timestamp,
            Map.endTime: self.timestamp - self.week,
            Map.limit: self.nb_prd
        })
        # snap
        self.snap_prms = Map({
            Map.account: self.ACCOUNT_MAIN,
            Map.begin_time: self.timestamp - self.week,
            Map.end_time: self.timestamp,
            Map.number: self.nb_prd,
            Map.timeout: self.timeout
        })
        self.snap_prms_request = Map({
            Map.type: BinanceAPI.ACCOUNT_TYPE_SPOT,
            Map.startTime: self.timestamp - self.week,
            Map.endTime: self.timestamp,
            Map.limit: self.nb_prd,
            Map.recvWindow: self.timeout
        })

    def test_set_market_price(self):
        # set request
        exp_params1 = self.mkt_prc_request
        bnc_rq_mkt1 = BinanceRequest(self.RQ_MARKET_PRICE, self.mkt_prc_params)
        reseult_params1 = bnc_rq_mkt1.generate_request()
        self.assertDictEqual(exp_params1.get_map(), reseult_params1.get_map())
        # not required is None
        self.setUp()
        del self.mkt_prc_request.get_map()[Map.startTime]
        del self.mkt_prc_request.get_map()[Map.endTime]
        del self.mkt_prc_request.get_map()[Map.limit]
        exp_params2 = self.mkt_prc_request
        self.mkt_prc_params.put(None, Map.begin_time)
        self.mkt_prc_params.put(None, Map.end_time)
        self.mkt_prc_params.put(None, Map.number)
        bnc_rq_mkt2 = BinanceRequest(self.RQ_MARKET_PRICE, self.mkt_prc_params)
        reseult_params2 = bnc_rq_mkt2.generate_request()
        self.assertDictEqual(exp_params2.get_map(), reseult_params2.get_map())
        # miss param
        self.setUp()
        del self.mkt_prc_params.get_map()[Map.number]
        with self.assertRaises(ValueError):
            BinanceRequest(self.RQ_MARKET_PRICE, self.mkt_prc_params)

    def test_set_account_snapshot(self):
        # set request
        exp1 = self.snap_prms_request
        bnc_snap1 = BinanceRequest(self.RQ_ACCOUNT_SNAP, self.snap_prms)
        result1 = bnc_snap1.generate_request()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # not required is None
        self.setUp()
        del self.snap_prms_request.get_map()[Map.startTime]
        del self.snap_prms_request.get_map()[Map.endTime]
        del self.snap_prms_request.get_map()[Map.limit]
        del self.snap_prms_request.get_map()[Map.recvWindow]
        exp2 = self.snap_prms_request
        self.snap_prms.put(None, Map.begin_time)
        self.snap_prms.put(None, Map.end_time)
        self.snap_prms.put(None, Map.number)
        self.snap_prms.put(None, Map.timeout)
        bnc_snap2 = BinanceRequest(self.RQ_ACCOUNT_SNAP, self.snap_prms)
        result2 = bnc_snap2.generate_request()
        self.assertDictEqual(exp2.get_map(), result2.get_map())
        # miss required param
        self.setUp()
        del self.snap_prms.get_map()[Map.account]
        with self.assertRaises(ValueError):
            BinanceRequest(self.RQ_ACCOUNT_SNAP, self.snap_prms)
        # unknown account
        self.setUp()
        self.snap_prms.put("unknown_account", Map.account)
        with self.assertRaises(ValueError):
            BinanceRequest(self.RQ_ACCOUNT_SNAP, self.snap_prms)

    def test_handle_response(self):
        raise Exception("Must implement this test")


if __name__ == '__main__':
    unittest.main