import unittest
from decimal import Decimal

from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.tools.MarketPrice import MarketPrice


class TestMarketPrice(unittest.TestCase, MarketPrice):
    def setUp(self) -> None:
        self.list = ['1', '2', '3', '4', '5']
        self.tuple = ('1', '2', '3', '4', '5')
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
            ['0', '0', '0', '0', self.list[0]],
            ['0', '0', '0', '0', self.list[1]],
            ['0', '0', '0', '0', self.list[2]],
            ['0', '0', '0', '0', self.list[3]],
            ['0', '0', '0', '0', self.list[4]]
        ]
        self.bnc_mkt = BinanceMarketPrice(self.bnc_list, "1m")
        self.bnc_mkt_u_u = BinanceMarketPrice(self.bnc_list_u_u, "1m")
        self.bnc_mkt_u_d = BinanceMarketPrice(self.bnc_list_u_d, "1m")
        self.bnc_mkt_d_u = BinanceMarketPrice(self.bnc_list_d_u, "1m")
        self.bnc_mkt_d_d = BinanceMarketPrice(self.bnc_list_d_d, "1m")
        self.bnc_mkt_flat = BinanceMarketPrice(self.bnc_list_flat, "1m")

    def tearDown(self) -> None:
        self.bnc_mkt = BinanceMarketPrice(self.list, "1m")

    def _convert_period(self, prd_time: str) -> int:
        return int(prd_time)

    def _get_closes(self) -> tuple:
        pass

    def get_close(self, prd: int) -> Decimal:
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
        self.bnc_mkt._set_collection(self.COLLECTION_CLOSES, self.list)
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
        prd_time = self.bnc_mkt_u_u._get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta/time
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
        prd_time = self.bnc_mkt_u_u._get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta/time
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
        exp = (Decimal(mkt[new_prd])/Decimal(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result < 0)
        self.assertEqual(exp, result)
        # positive
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 4
        exp = (Decimal(mkt[new_prd])/Decimal(mkt[old_prd])) - 1
        result = self.bnc_mkt_u_u._get_rate(new_prd, old_prd)
        self.assertTrue(result > 0)
        self.assertEqual(exp, result)
        # ∆ == 0
        self.setUp()
        mkt = list(self.closes_u_u)
        mkt.reverse()
        new_prd = 2
        old_prd = 2
        exp = (Decimal(mkt[new_prd])/Decimal(mkt[old_prd])) - 1
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
        prd_time = self.bnc_mkt_u_u._get_period_time()
        time = (old_prd - new_prd + 1) * prd_time
        exp = delta/time
        result = self.bnc_mkt_u_u.get_indicator(self.INDIC_MS)
        self.assertEqual(exp, result)

    def test_set_ds_avg(self):
        # uu
        mkt = list(self.closes_u_u)
        mkt.reverse()
        v1 = self.bnc_mkt_u_u._get_speed(3, 4)
        v2 = self.bnc_mkt_u_u._get_speed(1, 2)
        exp_u_u = (v1+v2)/2
        result_u_u = self.bnc_mkt_u_u.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_u_u, result_u_u)
        # ud
        self.setUp()
        mkt = list(self.closes_u_d)
        mkt.reverse()
        v1 = self.bnc_mkt_u_d._get_speed(2, 3)
        exp_u_d = v1/1
        result_u_d = self.bnc_mkt_u_d.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_u_d, result_u_d)
        # du
        self.setUp()
        mkt = list(self.closes_d_u)
        mkt.reverse()
        v1 = self.bnc_mkt_d_u._get_speed(1, 2)
        v2 = self.bnc_mkt_d_u._get_speed(3, 4)
        exp_d_u = (v1+v2)/2
        result_d_u = self.bnc_mkt_d_u.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_d_u, result_d_u)
        # dd
        self.setUp()
        mkt = list(self.closes_d_d)
        mkt.reverse()
        v1 = self.bnc_mkt_d_d._get_speed(2, 3)
        exp_d_d = v1/1
        result_d_d = self.bnc_mkt_d_d.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_d_d, result_d_d)
        # flat
        self.setUp()
        mkt = list(self.closes_flat)
        mkt.reverse()
        v1 = self.bnc_mkt_flat._get_speed(4, 6)
        exp_flat = v1/1
        result_flat = self.bnc_mkt_flat.get_indicator(self.INDIC_DS_AVG)
        self.assertEqual(exp_flat, result_flat)

    def test_set_ps_avg(self):
        # uu
        mkt = list(self.closes_u_u)
        mkt.reverse()
        v1 = self.bnc_mkt_u_u._get_speed(2, 3)
        exp_u_u = v1/1
        result_u_u = self.bnc_mkt_u_u.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_u_u, result_u_u)
        # ud
        self.setUp()
        mkt = list(self.closes_u_d)
        mkt.reverse()
        v1 = self.bnc_mkt_u_d._get_speed(1, 2)
        exp_u_d = v1/1
        result_u_d = self.bnc_mkt_u_d.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_u_d, result_u_d)
        # du
        self.setUp()
        mkt = list(self.closes_d_u)
        mkt.reverse()
        v1 = self.bnc_mkt_d_u._get_speed(2, 3)
        v2 = self.bnc_mkt_d_u._get_speed(4, 5)
        exp_d_u = (v1+v2)/2
        result_d_u = self.bnc_mkt_d_u.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_d_u, result_d_u)
        # dd
        self.setUp()
        mkt = list(self.closes_d_d)
        mkt.reverse()
        v1 = self.bnc_mkt_d_d._get_speed(1, 2)
        v2 = self.bnc_mkt_d_d._get_speed(3, 4)
        exp_d_d = (v1+v2)/2
        result_d_d = self.bnc_mkt_d_d.get_indicator(self.INDIC_PS_AVG)
        self.assertEqual(exp_d_d, result_d_d)
        # flat
        self.setUp()
        mkt = list(self.closes_flat)
        mkt.reverse()
        v1 = self.bnc_mkt_flat._get_speed(2, 4)
        v2 = self.bnc_mkt_flat._get_speed(6, 8)
        exp_flat = (v1+v2)/2
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
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u)-1]))
        exp1 = prc * Decimal(str((1+rate)))
        result1 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp1, result1)
        # rate negative
        rate = -0.1
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u)-1]))
        exp2 = prc * Decimal(str((1+rate)))
        result2 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp2, result2)
        # rate null
        rate = 0
        prc = Decimal(str(self.closes_d_u[len(self.closes_d_u)-1]))
        exp3 = prc * Decimal(str((1+rate)))
        result3 = self.bnc_mkt_d_u.get_futur_price(rate)
        self.assertEqual(exp3, result3)

    def test_print(self):
        from model.tools.FileManager import FileManager
        from config.Config import Config
        # date, close, index
        p = Config.get(Config.DIR_HISTORIC_PRICES)
        csv = FileManager.get_csv(p)
        mkt = [[row[k] for k in row] for row in csv]
        mkt2 = [[row[k] for k in row] for row in csv]
        bnc_mkt = BinanceMarketPrice(mkt, '1m')
        closes = bnc_mkt._get_closes()
        max_idx = bnc_mkt.get_maximums()
        fld_date = 'Date'
        fld_close = 'Close'
        fld_idx = 'Index'
        mkt2.reverse()
        max_rows = [{fld_date: mkt2[i][0], fld_close: closes[i], fld_idx: i} for i in max_idx]
        # min
        min_idx = bnc_mkt.get_minimums()
        min_rows = [{fld_date: mkt2[i][0], fld_close: closes[i], fld_idx: i} for i in min_idx]
        max_p = 'content/v0.01/print/maximums.csv'
        min_p = 'content/v0.01/print/minimums.csv'
        fields = list(max_rows[0].keys())
        FileManager.write_csv(max_p, fields, max_rows)
        FileManager.write_csv(min_p, fields, min_rows)



if __name__ == '__main__':
    unittest.main
