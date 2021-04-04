import unittest
from decimal import Decimal

from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice


class TestMarketPrice(unittest.TestCase, MarketPrice):
    def setUp(self) -> None:
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
        self.bnc_mkt = BinanceMarketPrice(self.bnc_list, "1m")
        self.bnc_mkt_u_u = BinanceMarketPrice(self.bnc_list_u_u, "1m")
        self.bnc_mkt_u_d = BinanceMarketPrice(self.bnc_list_u_d, "1m")
        self.bnc_mkt_d_u = BinanceMarketPrice(self.bnc_list_d_u, "1m")
        self.bnc_mkt_d_d = BinanceMarketPrice(self.bnc_list_d_d, "1m")
        self.bnc_mkt_flat = BinanceMarketPrice(self.bnc_list_flat, "1m")
        # RSI
        self.rsi_vals = [38.04, 36.47, 36.67, 36.91, 36.76, 36.76, 37.14, 37.72, 38.33, 37.74, 37.74, 37.42, 38.66,
                         39.10,
                         38.94, 39.28, 39.29, 40.03, 40.06, 40.53, 40.26]
        # Super Trend
        self.sptrend_mkt_list = self.datas_super_trend()
        self.sptrend_bnc_mkt = BinanceMarketPrice(self.sptrend_mkt_list, '1m')

    def datas_super_trend(self) -> list:
        p = "tests/datas/tools/TestMarketPrice/SuperTrend.csv"
        csv = FileManager.get_csv(p)
        mkt_list = [[int(line[Map.date]), '0', line[Map.high], line[Map.low], line[Map.close]] for line in csv]
        return mkt_list

    def tearDown(self) -> None:
        self.bnc_mkt = BinanceMarketPrice(self.list, "1m")

    def get_opens(self) -> tuple:
        pass

    def get_closes(self) -> tuple:
        pass

    def get_close(self, prd=0) -> Decimal:
        pass

    def get_highs(self) -> tuple:
        pass

    def get_lows(self) -> tuple:
        pass

    def get_times(self) -> tuple:
        pass

    def get_time(self, prd=0) -> int:
        pass

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

    # def test_get_indicator(self):

    def test_opens(self):
        # it work
        exp0 = [Decimal(v) for v in self.tuple]
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
        exp0 = [Decimal(v) for v in self.tuple]
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
        exp0 = [Decimal(v) for v in self.highs]
        # exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_highs()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_highs())
        self.assertEqual(exp1, result1)

    def test_get_lows(self):
        # it work
        exp0 = [Decimal(v) for v in self.lows]
        # exp0.reverse()
        exp0 = tuple(exp0)
        result0 = self.bnc_mkt.get_lows()
        self.assertTupleEqual(exp0, result0)
        # Still the same reference
        exp1 = id(result0)
        result1 = id(self.bnc_mkt.get_lows())
        self.assertEqual(exp1, result1)

    def test_get_negative_closes(self):
        self.list.reverse()
        exp = tuple((-Decimal(v) for v in self.list))
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
        mkt = [[0, 0, 0, 0, Decimal(str(val))] for val in self.rsi_vals]
        bnc_mkt = BinanceMarketPrice(mkt, '1m')
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
        mkt = [[0, 0, 0, 0, Decimal(str(val))] for val in self.rsi_vals]
        bnc_mkt = BinanceMarketPrice(mkt, '1m')
        rsis = bnc_mkt.get_rsis()
        exp = rsis[0]
        result = bnc_mkt.get_rsi()
        self.assertEqual(exp, result)
        self.assertEqual(rsis[1], bnc_mkt.get_rsi(1))

    def test_get_delta_price(self):
        # correct result
        exp = Decimal(self.closes_u_u[-2]) - Decimal(self.closes_u_u[-3])
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
        delta = Decimal(mkt[new_prd]) - Decimal(mkt[old_prd])
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
        delta = Decimal(mkt[new_prd]) - Decimal(mkt[old_prd])
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
        exp = (Decimal(mkt[new_prd]) / Decimal(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result < 0)
        self.assertEqual(exp, result)
        # positive
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 4
        exp = (Decimal(mkt[new_prd]) / Decimal(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result > 0)
        self.assertEqual(exp, result)
        # ∆ == 0
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 2
        exp = (Decimal(mkt[new_prd]) / Decimal(mkt[old_prd])) - 1
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
        delta = Decimal(mkt[new_prd]) - Decimal(mkt[old_prd])
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
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp1 = prc * Decimal(str((1 + rate)))
        result1 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp1, result1)
        # rate negative
        rate = -0.1
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp2 = prc * Decimal(str((1 + rate)))
        result2 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp2, result2)
        # rate null
        rate = 0
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u) - 1]))
        exp3 = prc * Decimal(str((1 + rate)))
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
        mkt_1 = BinanceMarketPrice(mkt_list_1, '1m')
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
        mkt_2 = BinanceMarketPrice(mkt_list_2, '1m')
        result_2 = mkt_2.get_slope(0, 3)
        self.assertEqual(exp_2, result_2)

    def test_get_slopes(self):
        nb_prd = 5
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
        mkt = BinanceMarketPrice(mkt_list_1, '1m')
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
        mkt = BinanceMarketPrice(mkt_list_1, '1m')
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
        mkt1 = BinanceMarketPrice(mkt_list_1, '1m')
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
        mkt2 = BinanceMarketPrice(mkt_list_1, '1m')
        result2 = mkt2.get_slopes_avg(nb_avg_prd, nb_slp_prd)
        self.assertTupleEqual(exp2, result2)

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
    #

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
        mkt_1 = BinanceMarketPrice(mkt_list_1, '1m')
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
        mkt_2 = BinanceMarketPrice(mkt_list_2, '1m')
        result_2 = mkt_2.get_indicator(self.INDIC_ACTUAL_SLOPE)
        self.assertEqual(exp_2, result_2)

    def test_get_peak(self) -> None:
        raise Exception("Must implement this test")

    def test_get_buy_period(self) -> None:
        raise Exception("Must implement this test")

    def test_get_peak_since_buy(self) -> None:
        raise Exception("Must implement this test")


if __name__ == '__main__':
    unittest.main
