import unittest

import pandas as pd

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair


class TestMarketPrice(unittest.TestCase, MarketPrice):
    def setUp(self) -> None:
        _MF.OUTPUT = True
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.pair1 = Pair('BTC/USDT')
        self.list = ['1', '2', '3', '4', '5']
        self.tuple = tuple(self.list)
        self.highs = ['11', '12', '13', '14', '15']
        self.lows = ['21', '22', '23', '24', '25']
        self.closes_u_u = ('2', '3', '1', '4', '2', '3')
        self.closes_u_d = ('2', '3', '1', '4', '2')
        self.closes_d_u = ('3', '2', '4', '1', '3', '2', '4')
        self.closes_d_d = ('3', '2', '4', '1', '2', '1')
        self.closes_flat = ('3', '3', '2', '2', '4', '4', '1', '1', '2', '2', '1', '1')
        self.bnc_list_u_u = [
            ['0', '0', '0', '0', self.closes_u_u[0]],
            ['0', '0', '0', '0', self.closes_u_u[1]],
            ['0', '0', '0', '0', self.closes_u_u[2]],
            ['0', '0', '0', '0', self.closes_u_u[3]],
            ['0', '0', '0', '0', self.closes_u_u[4]],
            ['0', '0', '0', '0', self.closes_u_u[5]]
        ]
        self.bnc_list_u_d = [
            ['0', '0', '0', '0', self.closes_u_d[0]],
            ['0', '0', '0', '0', self.closes_u_d[1]],
            ['0', '0', '0', '0', self.closes_u_d[2]],
            ['0', '0', '0', '0', self.closes_u_d[3]],
            ['0', '0', '0', '0', self.closes_u_d[4]]
        ]
        self.bnc_list_d_u = [
            ['0', '0', '0', '0', self.closes_d_u[0]],
            ['0', '0', '0', '0', self.closes_d_u[1]],
            ['0', '0', '0', '0', self.closes_d_u[2]],
            ['0', '0', '0', '0', self.closes_d_u[3]],
            ['0', '0', '0', '0', self.closes_d_u[4]],
            ['0', '0', '0', '0', self.closes_d_u[5]],
            ['0', '0', '0', '0', self.closes_d_u[6]]
        ]
        self.bnc_list_d_d = [
            ['0', '0', '0', '0', self.closes_d_d[0]],
            ['0', '0', '0', '0', self.closes_d_d[1]],
            ['0', '0', '0', '0', self.closes_d_d[2]],
            ['0', '0', '0', '0', self.closes_d_d[3]],
            ['0', '0', '0', '0', self.closes_d_d[4]],
            ['0', '0', '0', '0', self.closes_d_d[5]]
        ]
        self.bnc_list_flat = [
            ['0', '0', '0', '0', self.closes_flat[0]],
            ['0', '0', '0', '0', self.closes_flat[1]],
            ['0', '0', '0', '0', self.closes_flat[2]],
            ['0', '0', '0', '0', self.closes_flat[3]],
            ['0', '0', '0', '0', self.closes_flat[4]],
            ['0', '0', '0', '0', self.closes_flat[5]],
            ['0', '0', '0', '0', self.closes_flat[6]],
            ['0', '0', '0', '0', self.closes_flat[7]],
            ['0', '0', '0', '0', self.closes_flat[8]],
            ['0', '0', '0', '0', self.closes_flat[9]],
            ['0', '0', '0', '0', self.closes_flat[10]],
            ['0', '0', '0', '0', self.closes_flat[11]]
        ]
        self.bnc_list = [
            ['open_time', self.list[4], self.highs[0], self.lows[0], self.list[0]],
            ['open_time', self.list[3], self.highs[1], self.lows[1], self.list[1]],
            ['open_time', self.list[2], self.highs[2], self.lows[2], self.list[2]],
            ['open_time', self.list[1], self.highs[3], self.lows[3], self.list[3]],
            ['open_time', self.list[0], self.highs[4], self.lows[4], self.list[4]]
        ]
        self.bnc_mkt = BinanceMarketPrice(self.bnc_list, "1m", self.pair1)
        self.bnc_mkt_u_u = BinanceMarketPrice(self.bnc_list_u_u, "1m", self.pair1)
        self.bnc_mkt_u_d = BinanceMarketPrice(self.bnc_list_u_d, "1m", self.pair1)
        self.bnc_mkt_d_u = BinanceMarketPrice(self.bnc_list_d_u, "1m", self.pair1)
        self.bnc_mkt_d_d = BinanceMarketPrice(self.bnc_list_d_d, "1m", self.pair1)
        self.bnc_mkt_flat = BinanceMarketPrice(self.bnc_list_flat, "1m", self.pair1)
        # RSI
        self.rsi_vals = [38.04, 36.47, 36.67, 36.91, 36.76, 36.76, 37.14, 37.72, 38.33, 37.74, 37.74, 37.42, 38.66,
                         39.10,
                         38.94, 39.28, 39.29, 40.03, 40.06, 40.53, 40.26]
        # Super Trend
        self.sptrend_mkt_list = self._datas_super_trend()
        self.sptrend_bnc_mkt = BinanceMarketPrice(self.sptrend_mkt_list, '1m', self.pair1)

    @staticmethod
    def _datas_super_trend() -> list:
        p = "tests/datas/tools/TestMarketPrice/SuperTrend.csv"
        csv = FileManager.get_csv(p)
        mkt_list = [[int(line[Map.date]), '0', line[Map.high], line[Map.low], line[Map.close]] for line in csv]
        return mkt_list

    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None

    def broker_switch(self, on: bool = False, stage: str = Config.STAGE_1) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, stage)
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

    def get_opens(self) -> tuple:
        pass

    def get_closes(self) -> tuple:
        pass

    def get_close(self, prd=0) -> float:
        pass

    def get_highs(self) -> tuple:
        pass

    def get_lows(self) -> tuple:
        pass

    def get_times(self) -> tuple:
        pass

    def get_time(self, prd=0) -> int:
        pass

    def get_volumes(self, side: str) -> tuple:
        pass

    def test_reset_collections(self) -> None:
        broker = self.broker_switch(True)
        pair = Pair('BTC/USDT')
        period = 60*5
        n_period = broker.get_max_n_period()
        marketprice = MarketPrice.marketprice(broker, pair, period, n_period)
        closes = marketprice.get_closes()
        rsi = marketprice.get_rsis()
        macd = marketprice.get_macd()
        collections = marketprice._get_collections()
        self.assertEqual(5, len([1 for _, collection in collections.get_map().items() if collection is not None]))
        marketprice.reset_collections()
        self.assertEqual(0, len([1 for _, collection in collections.get_map().items() if collection is not None]))
        self.broker_switch(False)

    def test_set_collection(self):
        # unsupported collection key
        with self.assertRaises(IndexError):
            self.bnc_mkt._set_collection("unsupported_key", self.tuple)
        # collection already exist
        self.tearDown()
        self.bnc_mkt._set_collection(self.COLLECTION_CLOSES, self.tuple)
        with self.assertRaises(Exception):
            self.bnc_mkt._set_collection(self.COLLECTION_CLOSES, self.tuple)
        # list converted into tuple
        self.tearDown()
        self.bnc_mkt._set_collection(self.COLLECTION_CLOSES, tuple(self.list))
        type_expt = type(tuple())
        list_result = type(
            self.bnc_mkt._get_collection(self.COLLECTION_CLOSES))
        self.assertEqual(type_expt, list_result)

    def test_get_collection(self):
        # unsupported collection key
        with self.assertRaises(IndexError):
            self.bnc_mkt._get_collection("unsupported_key")
        # supported collection key not set
        self.assertIsNone(self.bnc_mkt._get_collection(self.COLLECTION_CLOSES))

    def test_opens(self):
        # it work
        exp0 = [float(v) for v in self.tuple]
        # exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_opens()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_opens())
        self.assertEqual(exp1, result1)

    def test_closes(self):
        # it work
        exp0 = [float(v) for v in self.tuple]
        exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_closes()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_closes())
        self.assertEqual(exp1, result1)

    def test_get_highs(self):
        # it work
        exp0 = [float(v) for v in self.highs]
        exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_highs()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_highs())
        self.assertEqual(exp1, result1)

    def test_get_lows(self):
        # it work
        exp0 = [float(v) for v in self.lows]
        exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_lows()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_lows())
        self.assertEqual(exp1, result1)

    def test_get_negative_closes(self):
        self.list.reverse()
        exp = tuple((-float(v) for v in self.list))
        result = self.bnc_mkt._get_negative_closes()
        self.assertTupleEqual(exp, result)

    def test_get_maximums(self):
        #
        exp_u_u = (2, 4)
        result_u_u = self.bnc_mkt_u_u.get_maximums()
        self.assertTupleEqual(exp_u_u, result_u_u)
        #
        self.setUp()
        exp_u_d = (1, 3)
        result_u_d = self.bnc_mkt_u_d.get_maximums()
        self.assertTupleEqual(exp_u_d, result_u_d)
        #
        self.setUp()
        exp_d_u = (2, 4)
        result_d_u = self.bnc_mkt_d_u.get_maximums()
        self.assertTupleEqual(exp_d_u, result_d_u)
        #
        self.setUp()
        exp_d_d = (1, 3)
        result_d_d = self.bnc_mkt_d_d.get_maximums()
        self.assertTupleEqual(exp_d_d, result_d_d)
        # flat maximum
        self.setUp()
        exp_flat = (2, 6)
        result_flat = self.bnc_mkt_flat.get_maximums()
        self.assertTupleEqual(exp_flat, result_flat)

    def test_get_minimums(self):
        #
        exp_u_u = (1, 3)
        result_u_u = self.bnc_mkt_u_u.get_minimums()
        self.assertTupleEqual(exp_u_u, result_u_u)
        #
        self.setUp()
        exp_u_d = (2,)
        result_u_d = self.bnc_mkt_u_d.get_minimums()
        self.assertTupleEqual(exp_u_d, result_u_d)
        #
        self.setUp()
        exp_d_u = (1, 3, 5)
        result_d_u = self.bnc_mkt_d_u.get_minimums()
        self.assertTupleEqual(exp_d_u, result_d_u)
        #
        self.setUp()
        exp_d_d = (2, 4)
        result_d_d = self.bnc_mkt_d_d.get_minimums()
        self.assertTupleEqual(exp_d_d, result_d_d)
        # flat maximum
        self.setUp()
        exp_flat = (4, 8)
        result_flat = self.bnc_mkt_flat.get_minimums()
        self.assertTupleEqual(exp_flat, result_flat)

    def test_get_extremums(self):
        exp_d_u = list((1, 3, 5)) + list((2, 4))
        exp_d_u.sort()
        exp_d_u = tuple(exp_d_u)
        result = self.bnc_mkt_d_u._get_extremums()
        self.assertTupleEqual(exp_d_u, result)

    def test_get_rsis(self):
        mkt = [[0, 0, 0, 0, float(str(val))] for val in self.rsi_vals]
        bnc_mkt = BinanceMarketPrice(mkt, '1m', self.pair1)
        rsis = bnc_mkt.get_rsis()
        """
        closes = list(bnc_mkt.get_closes())
        for i in range(len(closes)):
            print(f"{closes[i]}: {rsis[i]}")
        """
        exp = id(rsis)
        result = id(bnc_mkt.get_rsis())
        self.assertEqual(exp, result)

    def test_get_rsi(self):
        mkt = [[0, 0, 0, 0, float(str(val))] for val in self.rsi_vals]
        bnc_mkt = BinanceMarketPrice(mkt, '1m', self.pair1)
        rsis = bnc_mkt.get_rsis()
        exp = rsis[0]
        result = bnc_mkt.get_rsi()
        self.assertEqual(exp, result)
        self.assertEqual(rsis[1], bnc_mkt.get_rsi(1))

    def test_get_ema(self) -> None:
        bkr = self.broker_switch(True)
        pair = Pair('BTC/USDT')
        period = 60 * 60
        n_period = bkr.get_max_n_period()
        marketprices = MarketPrice.marketprice(bkr, pair, period, n_period)
        ema = marketprices.get_ema(n_period=200)
        closes = marketprices.get_closes()
        merged = [[closes[i], ema[i]] for i in range(len(closes))]
        print(_MF.json_encode(merged))
        self.broker_switch(False)

    def test_get_roc(self) -> None:
        bkr = self.broker_switch(True, stage = Config.STAGE_2)
        pair = Pair('BTC/USDT')
        period = 60 * 15
        n_period = bkr.get_max_n_period()
        marketprices = MarketPrice.marketprice(bkr, pair, period, n_period)
        roc = marketprices.get_roc(window=15)
        closes = marketprices.get_closes()
        open_times = marketprices.get_times()
        output_list = [f"{_MF.unix_to_date(open_times[i])}: close='{closes[i]}', roc='{roc[i]}'" for i in range(10)]
        print(_MF.json_encode(output_list))
        self.broker_switch(False)

    def test_get_delta_price(self):
        # correct result
        exp = float(self.closes_u_u[-2]) - float(self.closes_u_u[-3])
        result = self.bnc_mkt_u_u.get_delta_price(1, 2)
        self.assertEqual(exp, result)
        # new > old period
        with self.assertRaises(ValueError):
            self.bnc_mkt_u_u.get_delta_price(2, 1)
        # invalid period
        with self.assertRaises(IndexError):
            self.bnc_mkt_u_u.get_delta_price(100, 101)

    def test_get_speed(self):
        # ('2', '3', '1', '4', '2', '3')
        # negative
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 1
        old_prd = 4
        delta = float(mkt[new_prd]) - float(mkt[old_prd])
        prd_time = self.bnc_mkt_u_u.get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta / time
        result = self.bnc_mkt_u_u._get_speed(new_prd, old_prd)
        self.assertTrue(result < 0)
        self.assertEqual(exp, result)
        # positive
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 0
        old_prd = 3
        delta = float(mkt[new_prd]) - float(mkt[old_prd])
        prd_time = self.bnc_mkt_u_u.get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta / time
        result = self.bnc_mkt_u_u._get_speed(new_prd, old_prd)
        self.assertTrue(result > 0)
        self.assertEqual(exp, result)

    def test_get_rate(self):
        # ('2', '3', '1', '4', '2', '3')
        # negative
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 1
        old_prd = 4
        exp = (float(mkt[new_prd]) / float(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result < 0)
        self.assertEqual(exp, result)
        # positive
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 4
        exp = (float(mkt[new_prd]) / float(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result > 0)
        self.assertEqual(exp, result)
        # ∆ == 0
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 2
        exp = (float(mkt[new_prd]) / float(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result == 0)
        self.assertEqual(exp, result)
        # new_prd > old_prd
        with self.assertRaises(ValueError):
            self.bnc_mkt_u_u._get_rate(50, 0)
        # periods don't exist
        with self.assertRaises(IndexError):
            self.bnc_mkt_u_u._get_rate(0, 200)

    def test_set_ms(self):
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 0
        old_prd = 1
        delta = float(mkt[new_prd]) - float(mkt[old_prd])
        prd_time = self.bnc_mkt_u_u.get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta / time
        result = self.bnc_mkt_u_u.get_indicator(self.INDIC_MS)
        self.assertEqual(exp, result)

    def test_set_ds_avg(self):
        # uu
        mkt = list(self.closes_u_u)
        mkt.reverse()
        v1 = self.bnc_mkt_u_u._get_speed(3, 4)
        v2 = self.bnc_mkt_u_u._get_speed(1, 2)
        exp_u_u = (v1 + v2) / 2
        result_u_u = self.bnc_mkt_u_u.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_u_u, result_u_u)
        # ud
        self.setUp()
        mkt = list(self.closes_u_d)
        mkt.reverse()
        v1 = self.bnc_mkt_u_d._get_speed(2, 3)
        exp_u_d = v1 / 1
        result_u_d = self.bnc_mkt_u_d.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_u_d, result_u_d)
        # du
        self.setUp()
        mkt = list(self.closes_d_u)
        mkt.reverse()
        v1 = self.bnc_mkt_d_u._get_speed(1, 2)
        v2 = self.bnc_mkt_d_u._get_speed(3, 4)
        exp_d_u = (v1 + v2) / 2
        result_d_u = self.bnc_mkt_d_u.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_d_u, result_d_u)
        # dd
        self.setUp()
        mkt = list(self.closes_d_d)
        mkt.reverse()
        v1 = self.bnc_mkt_d_d._get_speed(2, 3)
        exp_d_d = v1 / 1
        result_d_d = self.bnc_mkt_d_d.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_d_d, result_d_d)
        # flat
        self.setUp()
        mkt = list(self.closes_flat)
        mkt.reverse()
        v1 = self.bnc_mkt_flat._get_speed(4, 6)
        exp_flat = v1 / 1
        result_flat = self.bnc_mkt_flat.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_flat, result_flat)

    def test_set_ps_avg(self):
        # uu
        mkt = list(self.closes_u_u)
        mkt.reverse()
        v1 = self.bnc_mkt_u_u._get_speed(2, 3)
        exp_u_u = v1 / 1
        result_u_u = self.bnc_mkt_u_u.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_u_u, result_u_u)
        # ud
        self.setUp()
        mkt = list(self.closes_u_d)
        mkt.reverse()
        v1 = self.bnc_mkt_u_d._get_speed(1, 2)
        exp_u_d = v1 / 1
        result_u_d = self.bnc_mkt_u_d.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_u_d, result_u_d)
        # du
        self.setUp()
        mkt = list(self.closes_d_u)
        mkt.reverse()
        v1 = self.bnc_mkt_d_u._get_speed(2, 3)
        v2 = self.bnc_mkt_d_u._get_speed(4, 5)
        exp_d_u = (v1 + v2) / 2
        result_d_u = self.bnc_mkt_d_u.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_d_u, result_d_u)
        # dd
        self.setUp()
        mkt = list(self.closes_d_d)
        mkt.reverse()
        v1 = self.bnc_mkt_d_d._get_speed(1, 2)
        v2 = self.bnc_mkt_d_d._get_speed(3, 4)
        exp_d_d = (v1 + v2) / 2
        result_d_d = self.bnc_mkt_d_d.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_d_d, result_d_d)
        # flat
        self.setUp()
        mkt = list(self.closes_flat)
        mkt.reverse()
        v1 = self.bnc_mkt_flat._get_speed(2, 4)
        v2 = self.bnc_mkt_flat._get_speed(6, 8)
        exp_flat = (v1 + v2) / 2
        result_flat = self.bnc_mkt_flat.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_flat, result_flat)

    def test_set_dr(self):
        # normal
        exp_d_d = self.bnc_mkt_d_d._get_rate(0, 1)
        result_d_d = self.bnc_mkt_d_d.get_indicator(self.INDIC_DR)
        self.assertEqual(exp_d_d, result_d_d)
        # flat
        self.setUp()
        exp_flat = self.bnc_mkt_flat._get_rate(0, 2)
        result_flat = self.bnc_mkt_flat.get_indicator(self.INDIC_DR)
        self.assertEqual(exp_flat, result_flat)
        # last extremum is not a max
        self.setUp()
        with self.assertRaises(Exception):
            self.bnc_mkt_u_u.get_indicator(self.INDIC_DR)

    def test_get_futur_price(self):
        # rate positive
        rate = 0.1
        prc = float(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp1 = prc * float(str((1 + rate)))
        result1 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp1, result1)
        # rate negative
        rate = -0.1
        prc = float(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp2 = prc * float(str((1 + rate)))
        result2 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp2, result2)
        # rate null
        rate = 0
        prc = float(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp3 = prc * float(str((1 + rate)))
        result3 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp3, result3)

    def test_get_slope(self):
        # Negative
        exp_1 = -2
        mkt_list_1 = [
            ['0', '0', '0', '0', '6'],
            ['0', '0', '0', '0', '4'],
            ['0', '0', '0', '0', '2'],
            ['0', '0', '0', '0', '0']
        ]
        mkt_1 = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        result_1 = mkt_1.get_slope(0, 3)
        self.assertEqual(exp_1, result_1)
        # Positive
        self.setUp()
        exp_2 = 0.5
        mkt_list_2 = [
            ['0', '0', '0', '0', '-1.5'],
            ['0', '0', '0', '0', '-1'],
            ['0', '0', '0', '0', '-0.5'],
            ['0', '0', '0', '0', '0']
        ]
        mkt_2 = BinanceMarketPrice(mkt_list_2, '1m', self.pair1)
        result_2 = mkt_2.get_slope(0, 3)
        self.assertEqual(exp_2, result_2)

    def test_get_slopes(self):
        nb_prd = self._NB_PRD_SLOPES
        nb_row = 20
        mkt_list_1 = [['0', '0', '0', '0', str(i)] for i in range(nb_row)]
        exp1 = []
        for i in range(nb_row):
            if i < nb_prd - 1:
                exp1.append(None)
                continue
            exp1.append(1)
        exp1.reverse()
        exp1 = tuple(exp1)
        mkt = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        result1 = mkt.get_slopes()
        self.assertTupleEqual(exp1, result1)
        # Negative
        mkt_list_1 = [['0', '0', '0', '0', str(i)] for i in range(-1, -nb_row, -1)]
        exp2 = []
        for i in range(-1, -nb_row, -1):
            if i > -nb_prd:
                exp2.append(None)
                continue
            exp2.append(-1.0)
        exp2.reverse()
        exp2 = tuple(exp2)
        mkt = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        result2 = mkt.get_slopes()
        self.assertTupleEqual(exp2, result2)
        # Same instance
        exp3 = id(result2)
        result3 = id(mkt.get_slopes())
        self.assertEqual(exp3, result3)

    def test_get_slopes_avg(self):
        # Same slopes
        nb_slp_prd = 5
        nb_avg_prd = 5
        nb_none = nb_slp_prd + nb_avg_prd - 2
        nb_row = 20
        mkt_list_1 = [['0', '0', '0', '0', str(i)] for i in range(nb_row)]
        mkt1 = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        exp1 = [1.0 for i in range(20 - nb_none)]
        exp1 = tuple(exp1 + [None for i in range(nb_none)])
        result1 = mkt1.get_slopes_avg(nb_avg_prd, nb_slp_prd)
        self.assertTupleEqual(exp1, result1)
        # Different slopes
        nb_slp_prd = 2
        nb_avg_prd = 5
        vals = [1, 2, 3, 3, 2, 1, 1, 2, 3]
        exp2 = (0.8, 0.6, 0.6, 0.8, None, None, None, None, None)
        mkt_list_1 = [['0', '0', '0', '0', str(v)] for v in vals]
        mkt2 = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        result2 = mkt2.get_slopes_avg(nb_avg_prd, nb_slp_prd)
        self.assertTupleEqual(exp2, result2)

    def test_get_super_trend(self) -> None:
        raise Exception("Must implement this test")
    """
    # SuperTrend
    def test_get_super_trend(self):
        tab1 = [None, None, None, None, None, None, None, None, None, None, 57910.948, 57910.948, 57910.948, 57910.948,
                57910.948, 57638.36600000001, 57696.29, 57721.372, 57721.372, 57721.372, 57721.372, 57721.372,
                57721.372, 57721.372, 57721.372, 57971.126000000004, 57924.64200000001, 57924.64200000001,
                57924.64200000001, 57924.64200000001, 57924.64200000001, 57924.64200000001, 57924.64200000001,
                57924.64200000001, 57924.64200000001, 57924.64200000001]
        none_tab = [v for v in tab1 if v is None]
        val_tab = [Decimal(str(round(v, 3))) for v in tab1 if v is not None]
        exp0 = none_tab + val_tab
        exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.sptrend_bnc_mkt.get_super_trend()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.sptrend_bnc_mkt.get_super_trend())
        self.assertEqual(exp1, result1)

    def test_get_super_trend_ups(self):
        tab1 = [None, None, None, None, None, None, None, None, None, None, 57910.948, 57910.948, 57910.948, 57910.948,
                57910.948, 57910.948, 58217.329999999994, 58213.258, 58184.628000000004, 58130.013, 58089.347, 58038.22,
                57984.26200000001, 57984.26200000001, 57984.26200000001, 57971.126000000004, 57924.64200000001,
                57924.64200000001, 57924.64200000001, 57924.64200000001, 57924.64200000001, 57924.64200000001,
                57924.64200000001, 57924.64200000001, 57924.64200000001, 57924.64200000001]
        none_tab = [v for v in tab1 if v is None]
        val_tab = [Decimal(str(round(v, 3))) for v in tab1 if v is not None]
        exp0 = tuple(none_tab + val_tab)
        result0 = self.sptrend_bnc_mkt.get_super_trend_ups()
        print(exp0)
        print(result0)
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.sptrend_bnc_mkt.get_super_trend_ups())
        self.assertEqual(exp1, result1)

    def test_get_super_trend_downs(self):
        tab1 = [None, None, None, None, None, None, None, None, None, None, 57409.07200000001, 57442.691000000006,
                57530.93400000001, 57583.928, 57608.558, 57638.36600000001, 57696.29, 57721.372, 57721.372, 57721.372,
                57721.372, 57721.372, 57721.372, 57721.372, 57721.372, 57721.372, 57434.868, 57434.868,
                57447.924999999996, 57522.786, 57589.458999999995, 57606.001000000004, 57606.001000000004,
                57606.001000000004, 57606.001000000004, 57606.001000000004]
        none_tab = [v for v in tab1 if v is None]
        val_tab = [Decimal(str(round(v, 3))) for v in tab1 if v is not None]
        exp0 = tuple(none_tab + val_tab)
        result0 = self.sptrend_bnc_mkt.get_super_trend_downs()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.sptrend_bnc_mkt.get_super_trend_downs())
        self.assertEqual(exp1, result1)

    def test_get_true_range_avg(self):
        tab1 = [None, None, None, None, None, None, None, None, None, None, 83.64599999999919, 89.59299999999931,
                95.6169999999991, 93.20899999999892, 91.84399999999951, 88.57799999999915, 86.83999999999942,
                81.98099999999977, 79.03600000000006, 84.3510000000002, 84.31400000000068, 77.67500000000072,
                72.17400000000052, 72.96300000000119, 73.54900000000126, 78.19200000000129, 81.62900000000081,
                85.26300000000046, 89.42000000000044, 84.19800000000104, 88.38199999999998, 91.63799999999974,
                93.41800000000003, 96.82799999999915, 103.41599999999889, 107.10999999999913]
        none_tab = [v for v in tab1 if v is None]
        val_tab = [Decimal(str(round(v, 3))) for v in tab1 if v is not None]
        exp0 = tuple(none_tab + val_tab)
        result0 = self.sptrend_bnc_mkt.get_true_range_avg()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.sptrend_bnc_mkt.get_true_range_avg())
        self.assertEqual(exp1, result1)

    def test_get_true_range(self):
        # it work
        tab1 = (72.52999999999884, 59.29000000000087, 72.97000000000116, 69.46999999999389, 96.26000000000204,
                91.36000000000058, 101.54000000000087, 95.48999999999796, 97.54999999999563, 80.0, 132.0,
                119.52999999999884, 48.88999999999942, 55.81999999999971, 63.599999999998545, 73.9800000000032,
                52.950000000004366, 66.04000000000087, 150.6999999999971, 79.63000000000466, 65.61000000000058,
                64.5199999999968, 56.78000000000611, 61.68000000000029, 110.02999999999884, 108.34999999999854,
                89.29000000000087, 107.61000000000058, 98.4800000000032, 121.46999999999389, 98.16999999999825,
                82.31999999999971, 90.87999999999738, 127.55999999999767, 146.97000000000116)
        tab1 = [round(v, 2) for v in tab1]
        exp0 = [None]
        tab2 = [Decimal(str(v)) for v in tab1 if v is not None]
        exp0 = tuple(exp0 + tab2)
        result0 = self.sptrend_bnc_mkt.get_true_range()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.sptrend_bnc_mkt.get_true_range())
        self.assertEqual(exp1, result1)
    """

    def test_set_actual_slope(self):
        # Last extremum is maximum
        exp_1 = -2
        mkt_list_1 = [
            ['0', '0', '0', '0', '6'],
            ['0', '0', '0', '0', '3'],
            ['0', '0', '0', '0', '4'],
            ['0', '0', '0', '0', '5'],
            ['0', '0', '0', '0', '6'],
            ['0', '0', '0', '0', '4'],
            ['0', '0', '0', '0', '2'],
            ['0', '0', '0', '0', '0']
        ]
        mkt_1 = BinanceMarketPrice(mkt_list_1, '1m', self.pair1)
        result_1 = mkt_1.get_indicator(self.INDIC_ACTUAL_SLOPE)
        self.assertEqual(exp_1, result_1)
        # Last extremum is minimum
        self.setUp()
        exp_2 = 0.5
        mkt_list_2 = [
            ['0', '0', '0', '0', '2'],
            ['0', '0', '0', '0', '3'],
            ['0', '0', '0', '0', '1'],
            ['0', '0', '0', '0', '0'],
            ['0', '0', '0', '0', '-1.5'],
            ['0', '0', '0', '0', '-1'],
            ['0', '0', '0', '0', '-0.5'],
            ['0', '0', '0', '0', '0']
        ]
        mkt_2 = BinanceMarketPrice(mkt_list_2, '1m', self.pair1)
        result_2 = mkt_2.get_indicator(self.INDIC_ACTUAL_SLOPE)
        self.assertEqual(exp_2, result_2)

    def test_get_peak(self) -> None:
        raise Exception("Must implement this test")

    def test_get_buy_period(self) -> None:
        raise Exception("Must implement this test")

    def test_get_peak_since_buy(self) -> None:
        raise Exception("Must implement this test")

    def test_get_super_trend_trend(self) -> None:
        raise Exception("Must implement this test")

    def test_get_super_trend_switchers(self) -> None:
        closes = [10, 7, 8, 11, 10, 13, 9, 10, 5, 7, 10, 8, 12, 7, 9, 5, 8, 7, 10, 8, 5]
        supers = [14, 11, 12, 7, 6, 9, 13, 14, 9, 3, 6, 4, 16, 11, 13, 1, 4, 3, 14, 12, 9]
        exp1 = {
            0: self.SUPERTREND_DROPPING,
            3: self.SUPERTREND_RISING,
            6: self.SUPERTREND_DROPPING,
            9: self.SUPERTREND_RISING,
            12: self.SUPERTREND_DROPPING,
            15: self.SUPERTREND_RISING,
            18: self.SUPERTREND_DROPPING
        }
        result1 = self.get_super_trend_switchers(closes, supers)
        self.assertDictEqual(exp1, result1.get_map())
        # With NAN value
        """
        closes = [10, 7, 8, 11, 10, 13, 9, 10, 5, 7, 10, 8, 12, 7, 9, 5, 8, 7, 10, 8, 5]
        supers = ["NAN", "NAN", "NAN", 7, 6, 9, 13, 14, 9, 3, 6, 4, 16, 11, 13, 1, 4, 3, 14, 12, 9]
        exp2 = {
            0: self.SUPERTREND_DROPPING,
            3: self.SUPERTREND_RISING,
            6: self.SUPERTREND_DROPPING,
            9: self.SUPERTREND_RISING,
            12: self.SUPERTREND_DROPPING,
            15: self.SUPERTREND_RISING,
            18: self.SUPERTREND_DROPPING
        }
        result2 = self.get_super_trend_switchers(closes, supers)
        self.assertDictEqual(exp2, result2.get_map())
        """

    def test_get_psar_trend(self) -> None:
        closes = [4, 6, 5, 8, 6, 11, 13, 12, 13, 18, 15, 14, 5, 19, 18, 9, 8, 6, 7, 4, 3]
        psar = [2, 4, 3, 6, 4, 9, 11, 10, 11, float('nan'), 17, 17, 8, 17, 16, 11, 10, 8, 9, 6, 5]
        nb = len(closes)
        exp1 = MarketPrice.PSAR_RISING
        exp2 = MarketPrice.PSAR_DROPPING
        result1 = MarketPrice.get_psar_trend(closes, psar, 0)
        result2 = MarketPrice.get_psar_trend(closes, psar, -1)
        result3 = MarketPrice.get_psar_trend(closes, psar, -12)
        self.assertEqual(exp1, result1)
        self.assertEqual(exp2, result2)
        self.assertIsNone(result3)
        self.assertEqual(MarketPrice.PSAR_RISING, MarketPrice.get_psar_trend(closes, psar, -nb))
        self.assertEqual(MarketPrice.PSAR_DROPPING, MarketPrice.get_psar_trend(closes, psar, nb - 1))
        # Different size
        with self.assertRaises(ValueError):
            MarketPrice.get_psar_trend([closes[i] for i in range(len(closes)) if i > 0], psar, 5)
        with self.assertRaises(ValueError):
            MarketPrice.get_psar_trend(closes, [psar[i] for i in range(len(psar)) if i > 0], 9)
        # Index out
        with self.assertRaises(IndexError):
            MarketPrice.get_psar_trend(closes, psar, 21)
        with self.assertRaises(IndexError):
            MarketPrice.get_psar_trend(closes, psar, -30)
        with self.assertRaises(IndexError):
            MarketPrice.get_psar_trend(closes, psar, -nb - 1)

    def test_marketprices(self) -> None:
        bkr = self.broker_switch(on=True, stage=Config.STAGE_3)
        unix_time = _MF.get_timestamp()
        pair = Pair('BTC/USDT')
        period = 60*60
        # endtime = _MF.round_time(unix_time, period)
        # starttime = _MF.round_time((unix_time - (period*900)*3), period)
        starttime = int(_MF.date_to_unix('2021-03-23 0:00:00'))
        endtime = int(_MF.date_to_unix('2021-05-24 12:00:00'))
        marketprices = MarketPrice.marketprices(bkr, pair, period, endtime, starttime)
        # Interval of followed open times equal period
        n_error = sum([1 if ((marketprices.iloc[i,0] - marketprices.iloc[i-1,0])%period != 0) else 0 for i in range(1, marketprices.shape[0])])
        self.assertEqual(0, n_error)
        # First and last open times are correct
        exp2 = starttime
        result2 = int(marketprices.iloc[0,0]/1000)
        self.assertEqual(exp2, result2)
        exp3 = endtime
        result3 = int(marketprices.iloc[-1,0]/1000)
        self.assertEqual(exp3, result3)
        self.broker_switch(on=False)

    def test_save_marketprices(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_3)
        pairs = [Pair('BTC/USDT'), Pair('DOGE/USDT')]
        periods = [60*30, 60*60]
        endtime = _MF.get_timestamp()
        starttime = endtime - periods[-1]*900*3
        MarketPrice.download_marketprices(broker, pairs, periods, endtime, starttime)
        self.broker_switch(on=False)

    def test_load_marketprice(self) -> None:
        broker_name = 'Binance'
        pair = Pair('BTC/USDT')
        fake_pair = Pair('FAKE/PAIR')
        period = 60*60
        # Active history
        marketprice1 = MarketPrice.load_marketprice(broker_name, pair, period, active_path=True)
        self.assertIsInstance(marketprice1, pd.DataFrame)
        # Stock history
        marketprice2 = MarketPrice.load_marketprice(broker_name, pair, period, active_path=False)
        self.assertIsInstance(marketprice2, pd.DataFrame)
        # Same history
        self.assertListEqual(marketprice1.to_numpy().tolist(), marketprice2.to_numpy().tolist())
        # No supported Active pair
        with self.assertRaises(ValueError):
            MarketPrice.load_marketprice(broker_name, fake_pair, period, active_path=True)
        # No supported Stock pair
        with self.assertRaises(ValueError):
            MarketPrice.load_marketprice(broker_name, fake_pair, period, active_path=False)

    def test_exist_history(self) -> None:
        broker_name = 'Binance'
        pair = self.pair1
        # Exist
        period1 = 60
        self.assertTrue(self.exist_history(broker_name, pair, period1))
        # Don't exist
        period1 = 3
        self.assertFalse(self.exist_history(broker_name, pair, period1))

    def test_file_path_market_history(self) -> None:
        _cls = MarketPrice
        broker_name = 'Binance'
        pair = Pair('BTC/USDT')
        str_pair = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        period = 60*60
        # Stock file path
        exp1 = f'content/storage/MarketPrice/histories/stock/Binance/{str_pair}/3600.csv'
        result1 = _cls.file_path_market_history(broker_name, pair, period, active_path=False)
        self.assertEqual(exp1, result1)
        # Active file path
        exp2 = f'content/storage/MarketPrice/histories/active/Binance/{str_pair}/3600.csv'
        result2 = _cls.file_path_market_history(broker_name, pair, period, active_path=True)
        self.assertEqual(exp2, result2)

    def test_dir_path_market_history(self) -> None:
        _cls = MarketPrice
        broker_name = 'Binance'
        pair = Pair('BTC/USDT')
        str_pair = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        # Stock directory path
        exp1 = f'content/storage/MarketPrice/histories/stock/Binance/{str_pair}/'
        result1 = _cls.dir_path_market_history(broker_name, pair, active_path=False)
        self.assertEqual(exp1, result1)
        # Active directory path
        exp2 = f'content/storage/MarketPrice/histories/active/Binance/{str_pair}/'
        result2 = _cls.dir_path_market_history(broker_name, pair, active_path=True)
        self.assertEqual(exp2, result2)

    def test_dir_path_pair(self) -> None:
        _cls = MarketPrice
        broker_name = 'Binance'
        # Stock directory path
        exp1 = f'content/storage/MarketPrice/histories/stock/Binance/'
        result1 = _cls.dir_path_pair(broker_name, active_path=False)
        self.assertEqual(exp1, result1)
        # Active directory path
        exp1 = f'content/storage/MarketPrice/histories/active/Binance/'
        result1 = _cls.dir_path_pair(broker_name, active_path=True)
        self.assertEqual(exp1, result1)

    def test_history_pairs(self) -> None:
        broker_name = 'Binance'
        self.assertListEqual([], MarketPrice.history_pairs(broker_name, active_path=True))
        pairs = MarketPrice.history_pairs(broker_name, active_path=False)
        self.assertIsInstance(pairs[0], Pair)

    def test_history_periods(self) -> None:
        broker_name = 'Binance'
        periods = MarketPrice.history_periods(broker_name)
        self.assertIsInstance(periods, list)
        self.assertIsInstance(periods[0], int)

    def test_last_extremum_index(self) -> None:
        values = [7, -6, 10, 7, 2, 9, -2, -1, -6, 6, 5, -3, 1, 7, -10, 3, -10, 10, -8, -6]
        zeros = [2, -9, -4, 7, 2, -1, -7, 0, -4, 3, 4, -8, 10, 9, -9, 7, -1, 9, -10, -10]
        n_row = len(values)
        # Exclude 0 peak
        exp0 = 17
        result0 = self.last_extremum_index(values, zeros, 1, excludes=[])
        self.assertEqual(exp0, result0)
        # Exclude 1 peak
        excludes1 = [-1]
        exp1 = 9
        result1 = self.last_extremum_index(values, zeros, 1, excludes=excludes1)
        self.assertEqual(exp1, result1)
        # Exclude 2 peaks
        excludes2 = [-1, exp1]
        exp2 = 5
        result2 = self.last_extremum_index(values, zeros, 1, excludes2)
        self.assertEqual(exp2, result2)
        # Get last minimum
        exp3 = 16
        result3 = self.last_extremum_index(values, zeros, -1)
        self.assertEqual(exp3, result3)
        # Get last zero
        exp4 = 4
        result4 = self.last_extremum_index(values, zeros, 0)
        self.assertEqual(exp4, result4)
        # Wrong  extremum
        with self.assertRaises(ValueError):
            result4 = self.last_extremum_index(values, zeros, 2)

    def test_mean_candle_variation(self) -> None:
        opens = [10,6,3,10,1,10,5,7,1,3]
        closes = [4,1,7,1,9,2,3,3,8,8]
        candle_means = MarketPrice.mean_candle_variation(opens, closes)
        # Normal usage
        exp1 = Map({
            Map.all: {Map.mean: 1.39, Map.stdev: 3.35, Map.number: 10},
            Map.positive: {Map.mean: 4.5, Map.stdev: 3.49, Map.number: 4},
            Map.negative: {Map.mean: -0.68, Map.stdev: 0.19, Map.number: 6}
        })
        result1 = Map({k: {k2: round(v2, 2) for k2, v2 in v.items()} for k, v in candle_means.get_map().items()})
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Lists have different size
        with self.assertRaises(ValueError):
            MarketPrice.mean_candle_variation(opens[:-3], closes)
        # Not enougth candle
        result2 = Map({k: {k2: None for k2, v2 in v.items()} for k, v in candle_means.get_map().items()})
        {k: [self.assertIsNone(v2) for _, v2 in v.items()] for k, v in result2.get_map().items()}

    def test_mean_candle_sequence(self) -> None:
        opens = [2,8,9,10,4,11,18,6,12,13,17,4,7,3,2,17,7,16,6,10,4,14]
        closes = [20,7,11,15,16,1,6,9,8,7,14,18,7,13,13,17,4,2,15,5,7,11]
        mean_sequences = MarketPrice.mean_candle_sequence(opens, closes)
        # Normal usage
        exp1 = Map({
            Map.positive: 1.43,
            Map.negative: 1.67
        })
        result1 = Map({k: round(v, 2) for k, v in mean_sequences.get_map().items()})
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Lists have different size
        with self.assertRaises(ValueError):
            MarketPrice.mean_candle_sequence(opens[:-3], closes)


if __name__ == '__main__':
    unittest.main
