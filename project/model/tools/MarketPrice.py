from abc import ABC, abstractmethod
from typing import Union

import numpy as np
import pandas as pd
from pandas_ta import supertrend as _supertrend
from ta.momentum import RSIIndicator
from ta.momentum import TSIIndicator
from ta.utils import _ema
from scipy.signal import find_peaks

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair


class MarketPrice(ABC):
    # Indicators
    INDIC_MS = "_set_ms"
    INDIC_DR = "_set_dr"
    INDIC_PS_AVG = "_set_ps_avg"
    INDIC_DS_AVG = "_set_ds_avg"
    INDIC_ACTUAL_SLOPE = "_set_actual_slope"
    INDIC_RNRP = "_set_rnrp"
    # Collections
    COLLECTION_OPENS = "COLLECTION_OPENS"
    COLLECTION_CLOSES = "COLLECTION_CLOSES"
    COLLECTION_NEG_CLOSES = "COLLECTION_NEG_CLOSES"
    COLLECTION_HIGHS = "COLLECTION_HIGHS"
    COLLECTION_LOWS = "COLLECTION_LOWS"
    COLLECTION_TIMES = "COLLECTION_TIMES"
    COLLECTION_MINS = "COLLECTION_MINS"
    COLLECTION_MAXS = "COLLECTION_MAXS"
    COLLECTION_EXTREMS = "COLLECTION_EXTREMS"
    COLLECTION_RSIS = "COLLECTION_RSIS"
    COLLECTION_TSIS = "COLLECTION_TSIS"
    COLLECTION_TSIS_EMAS = "COLLECTION_TSIS_EMAS"
    COLLECTION_SLOPES = "COLLECTION_SLOPES"
    COLLECTION_SLOPES_DEG = "COLLECTION_SLOPES_DEG"
    COLLECTION_SLOPES_AVG = "COLLECTION_SLOPES_AVG"
    COLLECTION_SUPER_TREND = "COLLECTION_SUPER_TREND"
    COLLECTION_SUPER_TREND_RSIS = "COLLECTION_SUPER_TREND_RSIS"
    COLLECTION_SUPER_TREND_UPS = "COLLECTION_SUPER_TREND_UPS"
    COLLECTION_SUPER_TREND_DOWNS = "COLLECTION_SUPER_TREND_DOWNS"
    COLLECTION_TRUE_RANGE_AVG = "COLLECTION_TRUE_RANGE_AVG"
    COLLECTION_TRUE_RANGE = "COLLECTION_TRUE_RANGE"
    _NB_PRD_RSIS = 14
    _NB_PRD_SLOPES = 7
    _NB_PRD_SLOPES_AVG = 7
    _NB_PRD_TRUE_RANGE_AVG = 7
    _COEF_SUPER_TREND = 3
    _NB_PRD_SLOW_TSI = 25
    _NB_PRD_FAST_TSI = 13
    SUPERTREND_RISING = "TREND_RISING"
    SUPERTREND_DROPING = "TREND_DROPING"

    @abstractmethod
    def __init__(self, mkt: list, prd_time: int, pair: Pair):
        """
        Constructor\n
        :param mkt: market prices.
        NOTE: market prices must be ordered from the newest to the older
        """
        self.__market = mkt
        self.__period_time = prd_time
        self.__pair = pair
        self.__indicators = Map()
        self.__collections = Map({
            self.COLLECTION_OPENS: None,
            self.COLLECTION_CLOSES: None,
            self.COLLECTION_NEG_CLOSES: None,
            self.COLLECTION_HIGHS: None,
            self.COLLECTION_LOWS: None,
            self.COLLECTION_TIMES: None,
            self.COLLECTION_MINS: None,
            self.COLLECTION_MAXS: None,
            self.COLLECTION_EXTREMS: None,
            self.COLLECTION_RSIS: None,
            self.COLLECTION_TSIS: None,
            self.COLLECTION_TSIS_EMAS: None,
            self.COLLECTION_SLOPES: None,
            self.COLLECTION_SLOPES_DEG: None,
            self.COLLECTION_SLOPES_AVG: None,
            self.COLLECTION_SUPER_TREND: None,
            self.COLLECTION_SUPER_TREND_RSIS: None,
            self.COLLECTION_SUPER_TREND_UPS: None,
            self.COLLECTION_SUPER_TREND_DOWNS: None,
            self.COLLECTION_TRUE_RANGE_AVG: None,
            self.COLLECTION_TRUE_RANGE: None
        })
        # Backup
        stage = Config.get(Config.STAGE_MODE)
        self._save_market(self.get_market()) if stage != Config.STAGE_1 else None

    def get_market(self) -> tuple:
        return tuple(self.__market)

    def get_period_time(self) -> int:
        return self.__period_time

    def get_pair(self) -> Pair:
        return self.__pair

    def __get_collections(self) -> Map:
        return self.__collections

    # def _set_collection(self, k: str, e: Union[list, tuple]) -> None:
    def _set_collection(self, k: str, e: tuple) -> None:
        """
        To set a new collection in collections\n
        :param k: key where to store the collection
        :param e: collection to put
        :exception Exception: if the collection in the given key is already set
        """
        coll = self._get_collection(k)
        if coll is not None:
            raise Exception(f"This collection '{k}' is already set")
        self.__get_collections().put(tuple(e), k)
        # self.__get_collections().put(e, k)

    def _get_collection(self, k) -> tuple:
        """
        To get the collection at the given key\n
        :param k: key where to get the collection
        :exception IndexError: if the given key is not supported
        :return: the collection at the given key
        """
        colls = self.__get_collections()
        if k not in colls.get_keys():
            raise IndexError(f"This collection key '{k}' is not supported")
        return colls.get(k)

    def __set_indicator(self, k, v) -> None:
        self._get_indicators().put(float(v), k)

    def _get_indicators(self) -> Map:
        return self.__indicators

    def get_indicator(self, ind: str) -> float:
        inds = self._get_indicators()
        eval(f"self.{ind}()") if ind not in inds.get_keys() else None
        return inds.get(ind)

    @abstractmethod
    def get_opens(self) -> tuple:
        """
        To get list of market price at open\n
        :return: list of market price at open
                 list[index] => {float}
        """
        pass

    @abstractmethod
    def get_closes(self) -> tuple:
        """
        To get list of market price at close\n
        :return: list of market price at close
                 list[index] => {float}
        """
        pass

    def get_close(self, prd=0) -> float:
        """
        To get close price at the given period\n
        :param prd: the period where to get the price
        :return: the close price at the given period
        """
        closes = self.get_closes()
        if prd >= len(closes):
            raise ValueError(f"This period '{prd}' don't exist in market's closes")
        return closes[prd]

    @abstractmethod
    def get_highs(self) -> tuple:
        """
        To get market's higher prices\n
        :return: market's higher price for each period
        """
        pass

    @abstractmethod
    def get_lows(self) -> tuple:
        """
        To get market's lower prices\n
        :return: market's lower price for each period
        """
        pass

    @abstractmethod
    def get_times(self) -> tuple:
        """
        To get unix time of market prices\n
        :return: unix time of market prices
        """
        pass

    @abstractmethod
    def get_time(self, prd=0) -> int:
        """
        To get the unix market time in second for the given period\n
        :param prd: period to get market time
        :raise IndexError: if given period is out of set of periods
        :return: market price's unix time
        """
        pass

    def _get_negative_closes(self) -> tuple:
        neg_closes = self._get_collection(self.COLLECTION_NEG_CLOSES)
        if neg_closes is None:
            closes = self.get_closes()
            neg_closes = tuple((-v for v in closes))
            self._set_collection(self.COLLECTION_NEG_CLOSES, neg_closes)
        return neg_closes

    def get_maximums(self) -> tuple:
        """
        To get indexes of all maximum\n
        :return: indexes of all maximum
        """
        maxs = self._get_collection(self.COLLECTION_MAXS)
        if maxs is None:
            closes = self.get_closes()
            xs = np.array(closes)
            maxs = tuple(find_peaks(xs)[0])
            self._set_collection(self.COLLECTION_MAXS, maxs)
        return maxs

    def get_minimums(self) -> tuple:
        """
        To get indexes of all minimum\n
        :return: indexes of all minimum
        """
        mins = self._get_collection(self.COLLECTION_MINS)
        if mins is None:
            neg_closes = self._get_negative_closes()
            ys = np.array(neg_closes)
            mins = tuple(find_peaks(ys)[0])
            self._set_collection(self.COLLECTION_MINS, mins)
        return mins

    def _get_extremums(self) -> tuple:
        """
        To get indexes of all maximum and minimum\n
        :return: indexes of all maximum and minimum
        """
        exts = self._get_collection(self.COLLECTION_EXTREMS)
        if exts is None:
            maxs = self.get_maximums()
            mins = self.get_minimums()
            exts = list(maxs) + list(mins)
            exts.sort()
            exts = tuple(exts)
            self._set_collection(self.COLLECTION_EXTREMS, exts)
        return exts

    """
    def get_super_extremums(self) -> tuple:
        closes = self.get_closes()
        mins = list(self.get_minimums())
        # min_vals = [closes[prd] for prd in mins]
        maxs = list(self.get_maximums())
        # max_vals = [closes[prd] for prd in maxs]
        return tuple(_MF.get_super_extremums(mins, maxs))
    """

    def get_rsis(self, nb_prd: int = _NB_PRD_RSIS) -> tuple:
        """
        To get collection of RSI\n
        :param nb_prd: number of period to use to generate each RSI point
        :return: RSI generated with the market's prices
        """
        rsis = self._get_collection(self.COLLECTION_RSIS)
        if rsis is None:
            closes = list(self.get_closes())
            closes.reverse()
            """
            pd_ser = pd.Series(np.array(closes))
            rsis_obj = RSIIndicator(pd_ser, nb_prd)
            rsis_series = rsis_obj.rsi()
            rsis = rsis_series.to_list()
            """
            rsis = self.rsis(nb_prd, closes)
            rsis = [float(str(v)) for v in rsis]
            rsis.reverse()
            rsis = tuple(rsis)
            self._set_collection(self.COLLECTION_RSIS, rsis)
        return rsis

    def get_rsi(self, prd: int = 0) -> float:
        rsis = self.get_rsis()
        if prd >= len(rsis):
            raise ValueError(f"This period '{prd}' don't exist in RSI collection")
        return rsis[prd]

    # TSI DOWN
    def get_tsis(self, nb_prd_slow: int = _NB_PRD_SLOW_TSI, nb_prd_fast: int = _NB_PRD_FAST_TSI,
                 use_nan: bool = False) -> tuple:
        k = self.COLLECTION_TSIS
        tsis = self._get_collection(k)
        if tsis is None:
            closes = list(self.get_closes())
            closes.reverse()
            """
            pd_series = pd.Series(np.array(closes))
            tsis_obj = TSIIndicator(pd_series, nb_prd_slow, nb_prd_fast, not use_nan)
            tsis_series = tsis_obj.tsi()
            tsis = tsis_series.to_list()
            """
            tsis = self.tsis(nb_prd_slow, nb_prd_fast, use_nan, closes)
            tsis = [float(str(v)) for v in tsis]
            tsis.reverse()
            tsis = tuple(tsis)
            self._set_collection(k, tsis)
        return tsis

    def get_tsis_emas(self, nb_prd_slow: int = _NB_PRD_SLOW_TSI, nb_prd_fast: int = _NB_PRD_FAST_TSI,
                      use_nan: bool = False) -> tuple:
        """
        To get the EMA of the TSI indicator\n
        :param nb_prd_slow: number of period used in TSI
        :param nb_prd_fast: number of period used in TSI & EMA(TSI)
        :param use_nan: set True to use NaN value before nb_period index else its fill result of calculated values
        :return: EMA of the TSI indicator
        """
        k = self.COLLECTION_TSIS_EMAS
        tsis_emas = self._get_collection(k)
        if tsis_emas is None:
            tsis = list(self.get_tsis(nb_prd_slow, nb_prd_fast, use_nan))
            tsis.reverse()
            pd_series = pd.Series(np.array(tsis))
            tsis_emas = _ema(pd_series, nb_prd_fast, not use_nan)
            tsis_emas = tsis_emas.to_list()
            tsis_emas = [float(str(v)) for v in tsis_emas]
            tsis_emas.reverse()
            tsis_emas = tuple(tsis_emas)
            self._set_collection(k, tsis_emas)
        return tsis_emas
    # TSI UP

    def get_delta_price(self, new_prd=0, old_prd=1) -> float:
        """
        To get variation between two periods\n
        :param new_prd: the most recent period
        :param old_prd: the older period
        :return: variation between two given periods
        """
        if new_prd > old_prd:
            raise ValueError(f"The most recent period '{new_prd}' must be bellow the older one '{old_prd}'")
        closes = self.get_closes()
        sz = len(closes)
        if old_prd >= sz:
            raise IndexError(
                f"The the older period '{old_prd}' is out of bounds '{sz - 1}'")
        return closes[new_prd] - closes[old_prd]

    def _get_speed(self, new_prd: int, old_prd: int) -> float:
        prd_time = self.get_period_time()
        delta = self.get_delta_price(new_prd, old_prd)
        time = (old_prd - new_prd + 1) * prd_time
        return delta / time

    def _get_rate(self, new_prd: int, old_prd: int) -> float:
        """
        To get the variation rate between two periods\n
        :param new_prd: the most recent period
        :param old_prd: the older period
        :return: the variation rate between two periods
        """
        if new_prd > old_prd:
            raise ValueError(f"The most recent period '{new_prd}' must be bellow the older one '{old_prd}'")
        closes = self.get_closes()
        nb = len(closes)
        if old_prd >= nb:
            raise IndexError(f"Period '{old_prd}' don't exit in market of '{nb - 1}' periods")
        return closes[new_prd] / closes[old_prd] - 1

    def get_futur_price(self, rate: float) -> float:
        """
        To apply a rate variation on the most recent price\n
        :param rate: the rate to apply ]-∞,+∞[
        :return: price*(1+rate)
        """
        closes = self.get_closes()
        return closes[0] * float(str(1 + rate))

    # SLOPES
    def get_slope(self, new_prd: int, old_prd: int) -> float:
        closes = self.get_closes()
        nb = len(closes)
        if (new_prd >= nb) and (old_prd >= nb):
            raise ValueError(f"The most recent period '{new_prd}' or the older '{old_prd}' "
                             f"is out of closes's periods '{nb}'")
        if old_prd <= new_prd:
            raise ValueError(f"The most recent period '{new_prd}' must be bellow the older '{old_prd}'")
        y = []
        for i in range(new_prd, old_prd + 1):
            y.append(float(str(closes[i])))
        y.reverse()
        return _MF.get_slope(y).get(Map.slope)

    def get_slopes(self, nb_prd: int = _NB_PRD_SLOPES) -> tuple:
        """
        To get slopes of market closes\n
        :param nb_prd: number of period to use to evaluate each slope
        :return: market closes's list of slopes
        """
        slopes = self._get_collection(self.COLLECTION_SLOPES)
        if slopes is None:
            ys = [float(v) for v in self.get_closes()]
            ys.reverse()
            slopes = _MF.get_slopes(ys, nb_prd)
            slopes.reverse()
            slopes = tuple(slopes)
            self._set_collection(self.COLLECTION_SLOPES, slopes)
        return slopes

    def get_slopes_degree(self, nb_prd: int = _NB_PRD_SLOPES) -> tuple:
        k = self.COLLECTION_SLOPES_DEG
        degs = self._get_collection(k)
        if degs is None:
            degs = []
            slopes = self.get_slopes(nb_prd)
            for v in slopes:
                deg = _MF.slope_to_degree(v) if v is not None else None
                degs.append(deg)
            # degs = tuple(_MF.slope_to_degree(s) for s in slopes)
            degs = tuple(degs)
            self._set_collection(k, degs)
        return degs

    def get_slopes_avg(self, nb_avg_prd: int = _NB_PRD_SLOPES_AVG, nb_slp_prd: int = None) -> tuple:
        """
        To get slopes average\n
        :param nb_slp_prd: number of period to use to evaluate each slope
        :param nb_avg_prd: number of period to use to evaluate each average
        :return: list of slope average
        """
        slp_avg = self._get_collection(self.COLLECTION_SLOPES_AVG)
        if slp_avg is None:
            slopes = self.get_slopes(nb_slp_prd) if nb_slp_prd is not None else self.get_slopes()
            nones = [v for v in slopes if v is None]
            positive_slps = [abs(v) for v in slopes if v is not None]
            positive_slps.reverse()
            slp_avg = _MF.get_averages(positive_slps, nb_avg_prd)
            slp_avg.reverse()
            slp_avg += nones
            slp_avg = tuple(slp_avg)
            self._set_collection(self.COLLECTION_SLOPES_AVG, slp_avg)
        return slp_avg

    def get_slope_avg(self, prd: int = 0) -> float:
        avgs = self.get_slopes_avg()
        if prd >= len(avgs):
            raise ValueError(f"This period '{prd}' don't exist in the Slope average collection")
        return avgs[prd]

    # SuperTrend DOWN
    '''
    def get_super_trend(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG, coef: float = _COEF_SUPER_TREND) -> tuple:
        """
        To get the Super Trend indicator\n
        :param nb_prd: number of period to use for ach average
        :param coef: coefficient  to adjust downs values
        :return: the Super Trend indicator
        """
        k = self.COLLECTION_SUPER_TREND
        supers = self._get_collection(k)
        if supers is None:
            supers = []
            closes = list(self.get_closes())
            closes.reverse()
            ups = self.get_super_trend_ups(nb_prd, coef)
            downs = self.get_super_trend_downs(nb_prd, coef)
            for i in range(len(closes)):
                if ups[i] is None:
                    supers.append(None)
                    continue
                spr = ups[i] if ((supers[i - 1] == ups[i - 1]) and (closes[i] < ups[i])) \
                                or ((supers[i - 1] == downs[i - 1]) and (closes[i] < downs[i])) else None
                if spr is None:
                    spr = downs[i] if ((supers[i - 1] == ups[i - 1]) and (closes[i] > ups[i])) \
                                      or ((supers[i - 1] == downs[i - 1]) and (closes[i] > downs[i])) else None
                supers.append(spr)
            supers.reverse()
            supers = tuple(supers)
            self._set_collection(k, supers)
        return supers
    @staticmethod
    def _to_pd_serie(vs: list) -> pd.Series:
        return pd.Series(np.array(vs))
    '''

    def get_super_trend(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG, coef: float = _COEF_SUPER_TREND) -> tuple:
        """
        To get the Super Trend indicator\n
        :param nb_prd: number of period to use for ach average
        :param coef: coefficient  to adjust downs values
        :return: the Super Trend indicator
        """
        k = self.COLLECTION_SUPER_TREND
        supers = self._get_collection(k)
        if supers is None:
            closes = list(float(v) for v in self.get_closes())
            closes.reverse()
            # pd_closes = pd.Series(np.array(closes))
            highs = list(float(v) for v in self.get_highs())
            highs.reverse()
            # pd_highs = pd.Series(np.array(highs))
            lows = list(float(v) for v in self.get_lows())
            lows.reverse()
            # pd_lows = pd.Series(np.array(lows))
            supers = self.super_trend(nb_prd, coef, closes, highs, lows)
            supers = [float(str(v)) for v in supers]
            supers.reverse()
            supers = tuple(supers)
            self._set_collection(k, supers)
        return supers

    def get_super_trend_rsis(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG, coef: float = _COEF_SUPER_TREND) -> tuple:
        k = self.COLLECTION_SUPER_TREND_RSIS
        super_rsis = self._get_collection(k)
        if super_rsis is None:
            # RSI Close
            rsis_closes = list(self.get_rsis(nb_prd))
            rsis_closes.reverse()
            rsis_closes = [float(v) for v in rsis_closes]
            # RSI High
            highs = list(self.get_highs())
            highs.reverse()
            highs = [float(v) for v in highs]
            rsis_highs = self.rsis(nb_prd, highs)
            # RSI Low
            lows = list(self.get_lows())
            lows.reverse()
            lows = [float(v) for v in lows]
            rsis_lows = self.rsis(nb_prd, lows)
            super_rsis = self.super_trend(nb_prd, coef, rsis_closes, rsis_highs, rsis_lows)
            super_rsis.reverse()
            super_rsis = tuple(super_rsis)
            self._set_collection(k, super_rsis)
        return super_rsis

    '''
    def get_super_trend_tsis(self, nb_prd_slow: int = _NB_PRD_SLOW_TSI, nb_prd_fast: int = _NB_PRD_FAST_TSI,
                             # use_nan: bool = False, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG,
                             use_nan: bool = False, nb_prd: int = _NB_PRD_SLOW_TSI,
                             coef: float = _COEF_SUPER_TREND) -> tuple:
        # nb_prd_slow: int, nb_prd_fast: int, use_nan: bool
        # TSI Close
        tsis_closes = list(self.get_tsis(nb_prd))
        tsis_closes.reverse()
        tsis_closes = [float(v) for v in tsis_closes]
        # TSI High
        highs = list(self.get_highs())
        highs.reverse()
        highs = [float(v) for v in highs]
        tsis_highs = self.tsis(nb_prd_slow, nb_prd_fast, use_nan, highs)
        # TSI Low
        lows = list(self.get_lows())
        lows.reverse()
        lows = [float(v) for v in lows]
        tsis_lows = self.tsis(nb_prd_slow, nb_prd_fast, use_nan, lows)
        super_tsis = self.super_trend(nb_prd, coef, tsis_closes, tsis_highs, tsis_lows)
        super_tsis.reverse()
        return tuple(super_tsis)
    '''
    '''
    def get_super_trend_ups(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG, coef: float = _COEF_SUPER_TREND) -> tuple:
        """
        To get Super Trend's up values\n
        :param nb_prd: number of period to use for ach average
        :param coef: coefficient  to adjust downs values
        :return: Super Trend's up values
        """
        k = self.COLLECTION_SUPER_TREND_UPS
        ups = self._get_collection(k)
        if ups is None:
            highs = self.get_highs()
            lows = self.get_lows()
            closes = list(self.get_closes())
            closes.reverse()
            nb = len(closes)
            if (len(highs) != nb) or (len(lows) != nb):
                raise Exception(f"The closes, highs, lows prices must have same number of period "
                                f"('{nb}', '{len(highs)}', '{len(lows)}')")
            ups = []
            atrs = self.get_true_range_avg(nb_prd)
            for i in range(nb):
                if atrs[i] is None:
                    ups.append(None)
                    continue
                # down = get_super_trend_down(i, highs, lows, atrs, coef)
                down = (highs[i] + lows[i]) / 2 + coef * atrs[i]
                if ups[i - 1] is None:
                    ups.append(down)
                    continue
                up_trend = down if (down < ups[i - 1]) or (closes[i - 1] > ups[i - 1]) else ups[i - 1]
                ups.append(up_trend)
            ups = tuple(ups)
            self._set_collection(k, ups)
        return ups

    def get_super_trend_downs(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG, coef: float = _COEF_SUPER_TREND) -> tuple:
        k = self.COLLECTION_SUPER_TREND_DOWNS
        downs = self._get_collection(k)
        if downs is None:
            highs = self.get_highs()
            lows = self.get_lows()
            closes = list(self.get_closes())
            closes.reverse()
            nb = len(closes)
            if (len(highs) != nb) or (len(lows) != nb):
                raise Exception(f"The closes, highs, lows prices must have same number of period "
                                f"('{nb}', '{len(highs)}', '{len(lows)}')")
            atrs = self.get_true_range_avg(nb_prd)
            downs = []
            for i in range(nb):
                if atrs[i] is None:
                    downs.append(None)
                    continue
                up = (highs[i] + lows[i]) / 2 - coef * atrs[i]
                if downs[i - 1] is None:
                    downs.append(up)
                    continue
                up_trend = up if (up > downs[i - 1]) or (closes[i - 1] < downs[i - 1]) else downs[i - 1]
                downs.append(up_trend)
            downs = tuple(downs)
            self._set_collection(k, downs)
        return downs

    def get_true_range_avg(self, nb_prd: int = _NB_PRD_TRUE_RANGE_AVG) -> tuple:
        """
        To get the Average True Range indicator\n
        :param nb_prd: number of period to use for ach average
        :return: the Average True Range indicator
        """
        avgs = self._get_collection(self.COLLECTION_TRUE_RANGE_AVG)
        if avgs is None:
            if nb_prd <= 1:
                raise ValueError(f"The number of period must be at less 2 instead '{nb_prd}'")
            trs = self.get_true_range()
            nb_none = len([v for v in trs if v is None])
            idx = nb_none
            idx += nb_prd - 1
            avgs = []
            nb = len(trs)
            for i in range(nb):
                if i < idx:
                    avgs.append(None)
                    continue
                seq = [trs[j] for j in range(nb) if (j > (idx - nb_prd)) and (j <= idx)]
                atr = sum(seq) / nb_prd
                avgs.append(atr)
                idx += 1
            avgs = tuple(avgs)
            self._set_collection(self.COLLECTION_TRUE_RANGE_AVG, avgs)
        return avgs

    def get_true_range(self) -> tuple:
        """
        To get the True Range indicator\n
        :return: True Range indicator
        """
        trs = self._get_collection(self.COLLECTION_TRUE_RANGE)
        if trs is None:
            closes = list(self.get_closes())
            closes.reverse()
            highs = self.get_highs()
            lows = self.get_lows()
            nb = len(closes)
            if (len(highs) != nb) or (len(lows) != nb):
                raise ValueError(f"The closes, highs and lows collections must have the same length "
                                 f"('{nb}', '{len(highs)}, '{len(lows)}')")
            trs = [None]
            for i in range(1, nb):
                hl = highs[i] - lows[i]
                hc = abs(highs[i] - closes[i - 1]) if (i > 0) else 0
                lc = abs(lows[i] - closes[i - 1]) if (i > 0) else 0
                tr = max([hl, hc, lc])
                trs.append(tr)
            trs = tuple(trs)
            self._set_collection(self.COLLECTION_TRUE_RANGE, trs)
        return trs
    '''
    # SuperTrend UP

    def _set_ms(self) -> None:
        """
        To generate the market's variation speed for its most recent period\n
        """
        """
        prd_time = self.get_period_time()
        delta = self.get_delta_price()
        return Decimal(delta/prd_time)
        """
        ms = self._get_speed(0, 1)
        self.__set_indicator(self.INDIC_MS, ms)

    def _set_ds_avg(self) -> None:
        """
        To set Drop Speed Average\n
        """
        exts = list(self._get_extremums())
        maxs = self.get_maximums()
        if exts[0] in maxs:
            del exts[0]
        spds = []
        for i in range(len(exts)):
            if exts[i] in maxs:
                nw_prd = exts[i - 1]
                old_prd = exts[i]
                spds.append(self._get_speed(nw_prd, old_prd))
        ds_avg = np.sum(np.array(spds)) / len(spds)
        self.__set_indicator(self.INDIC_DS_AVG, ds_avg)

    def _set_ps_avg(self) -> None:
        """
        To set Pop speed Average\n
        """
        exts = list(self._get_extremums())
        mins = self.get_minimums()
        if exts[0] in mins:
            del exts[0]
        spds = []
        for i in range(len(exts)):
            if exts[i] in mins:
                nw_prd = exts[i - 1]
                old_prd = exts[i]
                spds.append(self._get_speed(nw_prd, old_prd))
        ps_avg = np.sum(np.array(spds)) / len(spds)
        self.__set_indicator(self.INDIC_PS_AVG, ps_avg)

    def _set_dr(self) -> None:
        """
        To set the Drop Rate since the last maximum\n
        :exception Exception: if the last extremum is not a maximum
        """
        exts = self._get_extremums()
        maxs = self.get_maximums()
        if exts[0] not in maxs:
            raise Exception("Can't evaluate the Drop Rate cause the last extremum is not a maximum")
        dr = self._get_rate(0, exts[0])
        self.__set_indicator(self.INDIC_DR, dr)

    def _set_actual_slope(self) -> None:
        exts = self._get_extremums()
        old_prd = exts[0]
        slope = self.get_slope(0, old_prd)
        self.__set_indicator(self.INDIC_ACTUAL_SLOPE, slope)

    @staticmethod
    def super_trend(nb_prd: int, coef: float, closes: list, highs: list, lows: list) -> list:
        pd_closes = pd.Series(np.array(closes))
        pd_highs = pd.Series(np.array(highs))
        pd_lows = pd.Series(np.array(lows))
        supers_obj = _supertrend(pd_highs, pd_lows, pd_closes, nb_prd, coef)
        supers_serie = supers_obj[f'SUPERT_{nb_prd}_{float(coef)}']
        supers = supers_serie.to_list()
        return supers

    @staticmethod
    def get_super_trend_trend(closes: list, supers: list, prd: int) -> str:
        """
        To evaluate the trend of SuperTrend on a given period\n
        :param closes: values used to generate SuperTrend
        :param supers: SuperTrend values generated with closes param
        :param prd: the period where to check the trend
        :return: the trend at the given period
        NOTE: return None if trend can't be evaluated
        """
        nb_close = len(closes)
        nb_super = len(supers)
        if nb_close != nb_super:
            raise ValueError(f"The number of closes '{nb_close}' must match the number of SuperTrend '{nb_super}'.")
        if (prd >= nb_super) or (abs(prd) > nb_super):
            raise IndexError(f"The given period '{prd}' is out of bound '{nb_super}'.")
        close = closes[prd]
        if prd != 0:
            last_close = closes[prd-1]
            trend_up = (close > supers[prd]) or ((last_close < supers[prd-1]) and (close == supers[prd]))
            trend_dow = (close < supers[prd]) or ((last_close > supers[prd-1]) and (close == supers[prd]))
        else:
            trend_up = close > supers[prd]
            trend_dow = close < supers[prd]
        trend = MarketPrice.SUPERTREND_RISING if trend_up else None
        trend = MarketPrice.SUPERTREND_DROPING if (trend is None) and trend_dow else trend
        return trend

    @staticmethod
    def get_super_trend_switchers(closes: list, supers: list) -> Map:
        """
        To get indexes where trend switch\n
        :param closes: values used to generate SuperTrend
        :param supers: SuperTrend values generated with closes param
        :return: list of firsts index of each trend in SuperTrend
                 Map[index{int}]:   {string}    # MarketPrice.SUPERTREND_{RISING|DROPING}
        """
        switchers = Map()
        last_trend = None
        for i in range(len(closes)):
            new_trend = MarketPrice.get_super_trend_trend(closes, supers, i)
            # new_trend = new_trend if new_trend != last_trend else None
            switchers.put(new_trend, i) if new_trend != last_trend else None
            last_trend = new_trend
        return switchers

    @staticmethod
    def rsis(nb_prd: int, closes: list) -> list:
        pd_ser = pd.Series(np.array(closes))
        rsis_obj = RSIIndicator(pd_ser, nb_prd)
        rsis_series = rsis_obj.rsi()
        rsis = rsis_series.to_list()
        return rsis

    @staticmethod
    def tsis(nb_prd_slow: int, nb_prd_fast: int, use_nan: bool, closes: list) -> list:
        pd_series = pd.Series(np.array(closes))
        tsis_obj = TSIIndicator(pd_series, nb_prd_slow, nb_prd_fast, not use_nan)
        tsis_series = tsis_obj.tsi()
        tsis = tsis_series.to_list()
        return tsis

    @staticmethod
    def get_peak(vs: Union[list, tuple], min_idx: int, max_idx: int) -> [int, None]:
        nb_prd = len(vs)
        if max_idx >= nb_prd:
            peak_idx = _MF.get_maximum(vs, min_idx, nb_prd - 1)
        else:
            peak_idx = _MF.get_maximum(vs, min_idx, max_idx)
        return peak_idx

    @staticmethod
    def get_buy_period(odr: Order, mkt) -> int:
        """
        To get period index of when tha order was executed\n
        :param odr: the executed order
        :param mkt: MarketPrice
        :return: period index of when tha order was executed
        """
        if odr.get_status() != Order.STATUS_COMPLETED:
            raise Exception(f"The Order's status must be '{Order.STATUS_COMPLETED}' instead of '{odr.get_status()}'")
        buy_time = odr.get_execution_time()
        time = mkt.get_time()
        prd_time = mkt.get_period_time()
        buy_prd = int((time - buy_time) / prd_time)
        _stage = Config.get(Config.STAGE_MODE)
        buy_prd = buy_prd if _stage == Config.STAGE_1 else buy_prd + 1
        return buy_prd

    @staticmethod
    def get_peak_since_buy(last_odr: Order, vs: Union[list, tuple], mkt_prc) -> [int, None]:
        """
        To get the period of the maximum price in MarketPrice\n
        :param last_odr: last Order executed
        :param mkt_prc: MarketPrice
        :param vs: list/tuple where to look for the peak
        :return: period of the maximum price in MarketPrice
        """
        """
        last_odr = self._get_orders().get_last_execution()
        if last_odr is None:
            raise Exception("Last order completed can't be empty")
        """
        buy_prd = MarketPrice.get_buy_period(last_odr, mkt_prc)
        # closes = mkt_prc.get_closes()
        nb_prd = len(vs)
        peak_idx = MarketPrice.get_peak(vs, 0, nb_prd - 1) if (buy_prd >= nb_prd) \
            else MarketPrice.get_peak(vs, 0, buy_prd)
        return peak_idx

    @staticmethod
    def _save_market(mkt: tuple) -> None:
        p = Config.get(Config.DIR_SAVE_MARKET)
        mkt = [[str(v) for v in row] for row in mkt]
        # mkt = list(mkt)
        mkt.reverse()
        rows = [{
            Map.time: _MF.unix_to_date(_MF.get_timestamp()),
            Map.market: _MF.json_encode(mkt)
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
