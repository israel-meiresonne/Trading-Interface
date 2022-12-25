from abc import ABC, abstractmethod
import statistics
from typing import Callable, Dict, Tuple, Union, List

import numpy as np
import pandas as pd
from pandas_ta import supertrend as _supertrend
from ta.volatility import KeltnerChannel, BollingerBands
from ta.momentum import RSIIndicator, TSIIndicator, ROCIndicator
from ta.trend import PSARIndicator, MACD
from ta.utils import _ema
from scipy.signal import find_peaks

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair


class MarketPrice(ABC):
    PREFIX_ID = 'mktprc_'
    _HISTORY_PATHS = {Map.active: 'active', Map.stock: 'stock'}
    _HISTORY_PERIODS = None
    _REGEX_HISTORY_FILE = r"\d+.csv"
    _PERIOD_MARKET_ANALYSE = 60 * 60
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
    COLLECTION_VOLUMES_LEFT = "COLLECTION_VOLUMES_LEFT"
    COLLECTION_VOLUMES_RIGHT = "COLLECTION_VOLUMES_RIGHT"
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
    COLLECTION_PSAR = "COLLECTION_PSAR"
    COLLECTION_PSAR_RSI = "COLLECTION_PSAR_RSI"
    COLLECTION_MACD = "COLLECTION_MACD"
    COLLECTION_MACD_SIGNAL = "COLLECTION_MACD_SIGNAL"
    COLLECTION_MACD_HISTOGRAM = "COLLECTION_MACD_HISTOGRAM"
    COLLECTION_KELTNERC_MIDDLE = "COLLECTION_KELTNERC_MIDDLE"
    COLLECTION_KELTNERC_HIGH = "COLLECTION_KELTNERC_HIGH"
    COLLECTION_KELTNERC_LOW = "COLLECTION_KELTNERC_LOW"
    COLLECTION_EMA = "COLLECTION_EMA"
    COLLECTION_BOLLINGER_HIGH = "COLLECTION_BOLLINGER_HIGH"
    COLLECTION_BOLLINGER_MIDDLE = "COLLECTION_BOLLINGER_MIDDLE"
    COLLECTION_BOLLINGER_LOW = "COLLECTION_BOLLINGER_LOW"
    COLLECTION_BOLLINGER_WIDTH = "COLLECTION_BOLLINGER_WIDTH"
    COLLECTION_BOLLINGER_RATE = "COLLECTION_BOLLINGER_RATE"
    COLLECTION_ROC = "COLLECTION_ROC"
    # Collection Config
    _NB_PRD_RSIS = 14
    _NB_PRD_SLOPES = 7
    _NB_PRD_SLOPES_AVG = 7
    _SUPERTREND_NB_PERIOD = 10  # 7
    _SUPERTREND_COEF = 3
    _NB_PRD_SLOW_TSI = 25
    _NB_PRD_FAST_TSI = 13
    SUPERTREND_RISING = "TREND_RISING"
    SUPERTREND_DROPPING = "TREND_DROPPING"
    _PSAR_STEP = 0.02
    _PSAR_MAX_STEP = 0.2
    PSAR_RISING = "PSAR_RISING"
    PSAR_DROPPING = "PSAR_DROPPING"
    MARKET_TREND_RISING = "MARKET_TREND_RISING"
    MARKET_TREND_NEUTRAL = "MARKET_TREND_NEUTRAL"
    MARKET_TREND_DROPPING = "MARKET_TREND_DROPPING"
    _MARKET_TREND_RATE = Map({
        MARKET_TREND_RISING: 0.55,
        MARKET_TREND_DROPPING: 0.45
    })
    _MACD_SLOW = 26
    _MACD_FAST = 12
    _MACD_SIGNAL = 9
    MACD_PARAMS_1 = {'slow': 100, 'fast': 46, 'signal': 35}
    _KELTNERC_WINDOW = 20
    _KELTNERC_MULTIPLE = 2
    _KELTNERC_MULTIPLE_LIBRARY = 2
    _EMA_N_PERIOD = 10
    _BOLLINGER_WINDOW = 20
    _BOLLINGER_WINDOW_DEV = 2
    _ROC_WINDOW = 12

    @abstractmethod
    def __init__(self, mkt: list, prd_time: int, pair: Pair):
        """
        Constructor\n
        :param mkt: market prices.
        NOTE: market prices must be ordered from the newest to the older
        """
        if not isinstance(mkt, list):
            raise ValueError(f"Market param must be type 'list', instead '{type(mkt)}'")
        self.__id = self.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        mkt = [row.copy() for row in mkt]
        self.__id = self.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        mkt.reverse()
        self.__market = tuple(mkt)
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
            self.COLLECTION_VOLUMES_LEFT: None,
            self.COLLECTION_VOLUMES_RIGHT: None,
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
            self.COLLECTION_TRUE_RANGE: None,
            self.COLLECTION_PSAR: None,
            self.COLLECTION_PSAR_RSI: None,
            self.COLLECTION_MACD: None,
            self.COLLECTION_MACD_SIGNAL: None,
            self.COLLECTION_MACD_HISTOGRAM: None,
            self.COLLECTION_KELTNERC_MIDDLE: None,
            self.COLLECTION_KELTNERC_HIGH: None,
            self.COLLECTION_KELTNERC_LOW: None,
            self.COLLECTION_EMA: None,
            self.COLLECTION_BOLLINGER_HIGH: None,
            self.COLLECTION_BOLLINGER_MIDDLE: None,
            self.COLLECTION_BOLLINGER_LOW: None,
            self.COLLECTION_BOLLINGER_WIDTH: None,
            self.COLLECTION_BOLLINGER_RATE: None,
            self.COLLECTION_ROC: None
        })
        self.__pd = None
        # Backup
        # stage = Config.get(Config.STAGE_MODE)
        # self._save_market(self) if stage != Config.STAGE_1 else None

    def get_id(self) -> str:
        return self.__id

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def get_market(self) -> tuple:
        return self.__market

    def get_period_time(self) -> int:
        return self.__period_time

    def get_pair(self) -> Pair:
        return self.__pair

    def reset_collections(self) -> None:
        """
        To reset all collection
        """
        collections = self._get_collections()
        for key, _ in collections.get_map().items():
            collections.put(None, key)

    def _get_collections(self) -> Map:
        return self.__collections

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
        self._get_collections().put(tuple(e), k)

    def _get_collection(self, k) -> tuple:
        """
        To get the collection at the given key\n
        :param k: key where to get the collection
        :exception IndexError: if the given key is not supported
        :return: the collection at the given key
        """
        colls = self._get_collections()
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

    @abstractmethod
    def get_volumes(self, side: str) -> tuple:
        """
        To get trading volumes

        Parameters:
        -----------
        side: str
            Map.left: to get trading volume in left asset
            Map.right: to get trading volume in right asset

        Raises:
        -------
        raise: ValueError
            If side is not supported

        Returns:
        --------
        return: tuple
            Trading volumes in given asset
        """
        pass

    def to_pd(self) -> pd.DataFrame:
        """
        To group all list in one dict of Numpy
        NOTE: list qre order from older (index=0) to newest (index=-1)

        Return:
        -------
        pd[Map.time]    # Open times    \n
        pd[Map.open]    # Open prices   \n
        pd[Map.close]   # Close price   \n
        pd[Map.high]    # High prices   \n
        pd[Map.low]     # Low prices    \n
        """
        prices_pd = self.__pd
        if prices_pd is None:
            open_times = list(self.get_times())
            open_times.reverse()
            opens = list(self.get_opens())
            opens.reverse()
            closes = list(self.get_closes())
            closes.reverse()
            highs = list(self.get_highs())
            highs.reverse()
            lows = list(self.get_lows())
            lows.reverse()
            prices = {
                Map.time:   open_times,
                Map.open:   opens,
                Map.close:  closes,
                Map.high:   highs,
                Map.low:    lows
                }
            
            self.__pd = prices_pd = pd.DataFrame(prices)
        return prices_pd

    @staticmethod
    def check_volume_side(side: str) -> bool:
        if side not in [Map.left, Map.right]:
            raise ValueError(f"This volume side '{side}' is not supported")
        return True

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

    def get_psar_rsis(self, nb_period: int = _NB_PRD_RSIS, step: float = _PSAR_STEP, max_step: float = _PSAR_MAX_STEP) -> tuple:
        k = self.COLLECTION_PSAR_RSI
        psar_rsis = self._get_collection(k)
        if psar_rsis is None:
            # Rsis
            rsis = list(self.get_rsis())
            rsis.reverse()
            rsis = rsis[nb_period-1:]
            # High
            highs = list(self.get_highs())
            highs.reverse()
            rsi_highs = MarketPrice.rsis(nb_period, highs)[nb_period-1:]
            # Low
            lows = list(self.get_lows())
            lows.reverse()
            rsi_lows = MarketPrice.rsis(nb_period, lows)[nb_period-1:]
            # Psar
            psar_rsis = MarketPrice.psar(rsi_highs, rsi_lows, rsis, step=step, max_step=max_step)
            psar_rsis = [
                *[float('nan') for i in range(nb_period - 1)],
                *psar_rsis
            ]
            psar_rsis.reverse()
            psar_rsis = tuple(psar_rsis)
            self._set_collection(k, psar_rsis)
        return psar_rsis

    def get_supertrend_rsis(self, nb_prd: int = _SUPERTREND_NB_PERIOD, coef: float = _SUPERTREND_COEF) -> tuple:
        k = self.COLLECTION_SUPER_TREND_RSIS
        super_rsis = self._get_collection(k)
        if super_rsis is None:
            # RSI Close
            rsis = list(self.get_rsis(nb_prd))
            rsis.reverse()
            # RSI High
            highs = list(self.get_highs())
            highs.reverse()
            rsis_highs = self.rsis(nb_prd, highs)
            # RSI Low
            lows = list(self.get_lows())
            lows.reverse()
            rsis_lows = self.rsis(nb_prd, lows)
            super_rsis = self.super_trend(nb_prd, coef, rsis, rsis_highs, rsis_lows)
            super_rsis.reverse()
            super_rsis = tuple(super_rsis)
            self._set_collection(k, super_rsis)
        return super_rsis

    # TSI DOWN
    def get_tsis(self, nb_prd_slow: int = _NB_PRD_SLOW_TSI, nb_prd_fast: int = _NB_PRD_FAST_TSI,
                 use_nan: bool = False) -> tuple:
        k = self.COLLECTION_TSIS
        tsis = self._get_collection(k)
        if tsis is None:
            closes = list(self.get_closes())
            closes.reverse()
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

    def get_super_trend(self, nb_prd: int = _SUPERTREND_NB_PERIOD, coef: float = _SUPERTREND_COEF) -> tuple:
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

    def get_psar(self, step: float = _PSAR_STEP, max_step: float = _PSAR_MAX_STEP) -> tuple:
        k = self.COLLECTION_PSAR
        psars = self._get_collection(k)
        if psars is None:
            closes = list(self.get_closes())
            closes.reverse()
            highs = list(self.get_highs())
            highs.reverse()
            lows = list(self.get_lows())
            lows.reverse()
            psars = MarketPrice.psar(highs, lows, closes, step=step, max_step=max_step)
            psars.reverse()
            psars = tuple(psars)
            self._set_collection(k, psars)
        return psars

    def get_macd(self, slow: int = _MACD_SLOW, fast: int = _MACD_FAST, signal: int = _MACD_SIGNAL) -> Map:
        k = self.COLLECTION_MACD
        macds = self._get_collection(k)
        if macds is None:
            closes = list(self.get_closes())
            closes.reverse()
            macd_map = MarketPrice.macd(closes, slow, fast, signal)
            # Treat MACDs
            macds = macd_map.get(Map.macd)
            macds.reverse()
            macds = tuple(macds)
            # Treat Signals
            signals = macd_map.get(Map.signal)
            signals.reverse()
            signals = tuple(signals)
            # Treat Histograms
            histograms = macd_map.get(Map.histogram)
            histograms.reverse()
            histograms = tuple(histograms)
            # Set  collections
            self._set_collection(k, macds)
            self._set_collection(MarketPrice.COLLECTION_MACD_SIGNAL, signals)
            self._set_collection(MarketPrice.COLLECTION_MACD_HISTOGRAM, histograms)
        macd_map = Map({
            Map.macd: macds,
            Map.signal: self._get_collection(MarketPrice.COLLECTION_MACD_SIGNAL),
            Map.histogram: self._get_collection(MarketPrice.COLLECTION_MACD_HISTOGRAM)
        })
        return macd_map

    def get_keltnerchannel(self, window: int = _KELTNERC_WINDOW, multiple: float = _KELTNERC_MULTIPLE, original_version: bool = False) -> Map:
        k = self.COLLECTION_KELTNERC_MIDDLE
        kelc_middles = self._get_collection(k)
        if kelc_middles is None:
            closes = list(self.get_closes())
            closes.reverse()
            highs = list(self.get_highs())
            highs.reverse()
            lows = list(self.get_lows())
            lows.reverse()
            kelc = MarketPrice.keltnerchannel(highs, lows, closes, window, multiple, original_version)
            # Middle
            kelc_middles = kelc.get(Map.middle)
            kelc_middles.reverse()
            # High
            kelc_highs = kelc.get(Map.high)
            kelc_highs.reverse()
            # Low
            kelc_lows = kelc.get(Map.low)
            kelc_lows.reverse()
            # Set  collections
            self._set_collection(k, kelc_middles)
            self._set_collection(MarketPrice.COLLECTION_KELTNERC_HIGH, kelc_highs)
            self._set_collection(MarketPrice.COLLECTION_KELTNERC_LOW, kelc_lows)
        kelc_map = Map({
            Map.middle: kelc_middles,
            Map.high: self._get_collection(MarketPrice.COLLECTION_KELTNERC_HIGH),
            Map.low: self._get_collection(MarketPrice.COLLECTION_KELTNERC_LOW)
        })
        return kelc_map

    def get_ema(self, n_period: int = _EMA_N_PERIOD) -> tuple:
        """
        To get the EMA of closes

        Parameters:
        -----------
        n_period: int
            Number of period to use

        Returns:
        --------
        return: tuple
            The EMA of closes
        """
        k = self.COLLECTION_EMA
        ema = self._get_collection(k)
        if ema is None:
            closes = list(self.get_closes())
            closes.reverse()
            fillna = False
            ema = self.ema(closes, n_period, fillna)
            ema.reverse()
            ema = tuple(ema)
            self._set_collection(k, ema)
        return ema

    def get_bollingerbands(self, window: int = _BOLLINGER_WINDOW, window_dev: int = _BOLLINGER_WINDOW_DEV) -> Map:
        """
        To get Bollinger Bands

        Parameters:
        -----------
        closes: list
            Market's closes prices
        window: int
            The number of period to use
        window_dev: int
            n factor standard deviation

        Returns:
        --------
        return: Map
            Bollinger Bands
            indicator[Map.high]:    {list}  # Bollinger Bands's High Band
            indicator[Map.middle]:  {list}  # Bollinger Bands's middle Band
            indicator[Map.low]:     {list}  # Bollinger Bands's low Band
            indicator[Map.width]:   {list}  # Bollinger Bands's Width
            indicator[Map.rate]:    {list}  # Bollinger Bands's Percentage Band
        """
        k = self.COLLECTION_BOLLINGER_MIDDLE
        bollinger_middle = self._get_collection(k)
        if bollinger_middle is None:
            closes = list(self.get_closes())
            closes.reverse()
            bollinger = self.bollingerbands(closes, window, window_dev)
            bollinger_high = bollinger.get(Map.high)
            bollinger_high.reverse()
            bollinger_middle = bollinger.get(Map.middle)
            bollinger_middle.reverse()
            bollinger_low = bollinger.get(Map.low)
            bollinger_low.reverse()
            bollinger_width = bollinger.get(Map.width)
            bollinger_width.reverse()
            bollinger_rate = bollinger.get(Map.rate)
            bollinger_rate.reverse()
            self._set_collection(self.COLLECTION_BOLLINGER_HIGH, bollinger_high)
            self._set_collection(self.COLLECTION_BOLLINGER_MIDDLE, bollinger_middle)
            self._set_collection(self.COLLECTION_BOLLINGER_LOW, bollinger_low)
            self._set_collection(self.COLLECTION_BOLLINGER_WIDTH, bollinger_width)
            self._set_collection(self.COLLECTION_BOLLINGER_RATE, bollinger_rate)
        bollinger = Map({
            Map.high: self._get_collection(self.COLLECTION_BOLLINGER_HIGH),
            Map.middle: bollinger_middle,
            Map.low: self._get_collection(self.COLLECTION_BOLLINGER_LOW),
            Map.width: self._get_collection(self.COLLECTION_BOLLINGER_WIDTH),
            Map.rate: self._get_collection(self.COLLECTION_BOLLINGER_RATE)
        })
        return bollinger

    def get_roc(self, window: int = _ROC_WINDOW) -> tuple:
        """
        To get Rate-of-Change (ROC)
        """
        key = self.COLLECTION_ROC
        roc = self._get_collection(key)
        if roc is None:
            closes = list(self.get_closes())
            closes.reverse()
            roc = self.roc(closes, window)
            roc.reverse()
            self._set_collection(key, roc)
        return roc

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
    def get_period_market_analyse() -> int:
        return MarketPrice._PERIOD_MARKET_ANALYSE

    @staticmethod
    def super_trend(nb_prd: int, coef: float, closes: list, highs: list, lows: list) -> list:
        pd_closes = pd.Series(np.array(closes))
        pd_highs = pd.Series(np.array(highs))
        pd_lows = pd.Series(np.array(lows))
        supers_obj = _supertrend(pd_highs, pd_lows, pd_closes, nb_prd, coef)
        supers_serie = supers_obj[f'SUPERT_{nb_prd}_{float(coef)}']
        super_trends = supers_serie.to_list()
        super_trends[0] = float('nan')
        return super_trends

    @staticmethod
    def get_super_trend_trend(closes: list, supers: list, prd: int) -> str:
        """
        To evaluate the trend of SuperTrend at the given period\n
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
        trend = MarketPrice.SUPERTREND_DROPPING if (trend is None) and trend_dow else trend
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
    def psar(highs: list, lows: list, closes: list, step: float, max_step: float) -> list:
        """
        To generate the Parabolic Stop and Reverse (PSAR) indicator.\n
        :param highs: Market's high prices.
        :param lows: Market's low prices.
        :param closes: Market's close prices.
        :param step: The acceleration coefficient used to compute PSAR.
        :param max_step: The maximum value allowed for the Acceleration Factor.
        :return: The Parabolic Stop and Reverse (PSAR) indicator.
        """
        pd_closes = pd.Series(np.array(closes))
        pd_highs = pd.Series(np.array(highs))
        pd_lows = pd.Series(np.array(lows))
        psar_obj = PSARIndicator(pd_highs, pd_lows, pd_closes, step, max_step)
        psar_series = psar_obj.psar()
        psar = psar_series.to_list()
        return psar

    @staticmethod
    def get_psar_trend(closes: list, psars: list, index: int) -> str:
        """
        To evaluate the trend of Psar at the given period\n
        :param closes: values used to generate SuperTrend
        :param psars: Psar values generated with the given closes param
        :param index: Index of the period to check the trend
        :return: the trend at the given period else None if trend can't be evaluate
        """
        nb_close = len(closes)
        nb_psar = len(psars)
        if nb_close != nb_psar:
            raise ValueError(f"The number of closes '{nb_close}' must match the number of Psar '{nb_psar}'.")
        if (index >= nb_psar) or (abs(index) > nb_psar):
            raise IndexError(f"The given index '{index}' is out of bound '{nb_psar}'.")
        close = closes[index]
        psar = psars[index]
        trend = MarketPrice.PSAR_RISING if psar < close else None
        trend = MarketPrice.PSAR_DROPPING if (trend is None) and (psar > close) else trend
        return trend

    @staticmethod
    def ema(values: list, n_period: int, fillna: bool) -> list:
        """
        To evaluate EMA

        Paremeters:
        -----------
        values: list
            Value to treat
        n_period: int
            Number of period to use
        fillna: bool
            Set True to fill Nan value with '-1' else False

        Returns:
        --------
        return: list
            The EMA
        """
        pd_series = pd.Series(values)
        return _ema(pd_series, n_period, fillna).to_list()

    @staticmethod
    def get_peak(vs: Union[list, tuple], min_idx: int, max_idx: int) -> Union[int, None]:
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
    def get_peak_since_buy(last_odr: Order, vs: Union[list, tuple], mkt_prc) -> Union[int, None]:
        """
        To get the period of the maximum price in MarketPrice\n
        :param last_odr: last Order executed
        :param mkt_prc: MarketPrice
        :param vs: list/tuple where to look for the peak
        :return: period of the maximum price in MarketPrice
        """
        buy_prd = MarketPrice.get_buy_period(last_odr, mkt_prc)
        # closes = mkt_prc.get_closes()
        nb_prd = len(vs)
        peak_idx = MarketPrice.get_peak(vs, 0, nb_prd - 1) if (buy_prd >= nb_prd) \
            else MarketPrice.get_peak(vs, 0, buy_prd)
        return peak_idx

    @staticmethod
    def analyse_market_trend(bkr: 'Broker', end_time: int = None, nb_period: int = None) -> Map:
        """
        To analyse market's trend\n
        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        end_time: int
            Most recent unix time for an interval
        nb_period: int
            Number of older periods to take from end_time

        Returns
        -------
        analyse: Map
            Rate of number of Pair in each market trend
            Map[MarketPrice.MARKET_TREND_*]:    {float} # Rate [0,1]
        """
        from model.tools.BrokerRequest import BrokerRequest
        if (end_time is not None) and ((not isinstance(end_time, int)) or (end_time < 1)):
            raise ValueError(f"End Time must be type int and >= 1, instead '{end_time}({type(end_time)})'")
        if (nb_period is not None) and ((not isinstance(nb_period, int)) or (nb_period < 1)):
            raise ValueError(f"Number of period to use must be type int and >= 1, "
                             f"instead '{nb_period}({type(nb_period)})'")
        stablecoins = Config.get(Config.CONST_STABLECOINS)
        concat_stable = '|'.join(stablecoins)
        stablecoin_rgx = f'({concat_stable})/\w+$'
        # Fiat regex
        fiats = Config.get(Config.CONST_FIATS)
        concat_fiat = '|'.join(fiats)
        fiat_rgx = rf'({concat_fiat})/\w+$'
        # Get pairs
        no_match = [
            r'^\w+(up|down|bear|bull)\/\w+$',
            r'^(bear|bull)/\w+$',
            r'^\w*inch\w*/\w+$',
            fiat_rgx,
            stablecoin_rgx,
            r'BCHSV/\w+$'
        ]
        match = [r'^.+\/usdt']
        # Add streams
        pair_strs = bkr.get_pairs(match=match, no_match=no_match)
        # pair_strs = [pair_strs[i] for i in range(len(pair_strs)) if i < 10]
        pairs = [Pair(pair_str) for pair_str in pair_strs]
        period = MarketPrice.get_period_market_analyse()
        streams = [bkr.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
        bkr.add_streams(streams)
        # Get market prices
        _bkr_cls = bkr.__class__.__name__
        market_params = Map({
            Map.pair: None,
            Map.period: period,
            Map.begin_time: None,
            Map.end_time: end_time,
            Map.number: nb_period if nb_period is not None else 50
        })
        analyse = Map({
            Map.drop: 0,
            Map.neutral: 0,
            Map.rise: 0
        })
        for pair in pairs:
            market_params.put(pair, Map.pair)
            market_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, market_params)
            bkr.request(market_rq)
            market_price = market_rq.get_market_price()
            closes = list(market_price.get_closes())
            closes.reverse()
            super_trends = list(market_price.get_super_trend())
            super_trends.reverse()
            trend = MarketPrice.get_super_trend_trend(closes, super_trends, -1)
            if trend == MarketPrice.SUPERTREND_RISING:
                cpt = analyse.get(Map.rise) + 1
                analyse.put(cpt, Map.rise)
            elif trend == MarketPrice.SUPERTREND_DROPPING:
                cpt = analyse.get(Map.drop) + 1
                analyse.put(cpt, Map.drop)
            else:
                raise Exception(f"Unsupported trend '{trend}' for super_trend")
        drop = analyse.get(Map.drop)
        neutral = analyse.get(Map.neutral)
        rise = analyse.get(Map.rise)
        total = rise + drop + neutral
        analyse.put(drop / total, MarketPrice.MARKET_TREND_DROPPING)
        analyse.put(neutral / total, MarketPrice.MARKET_TREND_NEUTRAL)
        analyse.put(rise / total, MarketPrice.MARKET_TREND_RISING)
        return analyse

    @staticmethod
    def get_market_trend(bkr: 'Broker', end_time: int = None, nb_period: int = 50, analyse: Map = None) -> str:
        """
        To get market's trend\n
        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        end_time: int
            Most recent unix time for an interval
        nb_period: int
            Number of older periods to take from end_time
        analyse: Map
            Analyse from MarketPrice.analyse_market_trend()
        Returns
        -------
        trend: str
            market's trend, format: MarketPrice.MARKET_TREND_*
        """
        market_rates = MarketPrice._MARKET_TREND_RATE
        analyse = MarketPrice.analyse_market_trend(bkr, end_time, nb_period) if analyse is None else analyse
        rising_rate = analyse.get(MarketPrice.MARKET_TREND_RISING)
        if rising_rate >= market_rates.get(MarketPrice.MARKET_TREND_RISING):
            trend = MarketPrice.MARKET_TREND_RISING
        elif rising_rate >= market_rates.get(MarketPrice.MARKET_TREND_DROPPING):
            trend = MarketPrice.MARKET_TREND_NEUTRAL
        else:
            trend = MarketPrice.MARKET_TREND_DROPPING
        return trend

    @classmethod
    def analyse_market(cls, broker: 'Broker', pairs: List[Pair], periods: List[int], endtime: int = None, starttime: int = None, n_period: int = None, marketprices: Map = None) -> Dict[int, pd.DataFrame]:
        """
        To get analyse of market's trend

        Parameters:
        -----------
        broker: 'Broker'
            Access to a Broker API
        pairs: List[Pair]
            Pairs analyse
        periods: List[int]
            Periods to analyse
        endtime: int = None
            Most recent time (in second) that edge the interval to analyse
        starttime: int = None
            Older time that (in second) edge the interval to analyse
        n_period: int = None
            Number of period to analyse (to set only if starttime is not set)
        marketprices: Map = None
            MarketPrice to reuse instead of request new price
            marketprices[Pair.hash()][period{int}] -> {MarketPrice}

        Returns:
        --------
        return: Dict[int, pd.DataFrame]
            Analyse of market's trend
        """
        def join_df(pair: Pair, base_df: pd.DataFrame, to_join: pd.DateOffset) -> pd.DataFrame:
            if base_df.shape[0] == 0:
                base_df = pd.DataFrame({pair: to_join[pair]}, index=to_join.index)
            else:
                base_df = base_df.join(to_join)
            return base_df
        
        def ge_marketprice(marketprices: Map, pair: Pair, period: int, endtime: int = None, starttime: int = None, n_period: int = None) -> MarketPrice:
            marketprice = marketprices.get(pair, period)
            if marketprice is None:
                if endtime is None:
                    endtime = _MF.round_time(unix_time, period)
                if (starttime is None) and (n_period is None):
                    n_period = broker.get_max_n_period()
                marketprice_df = cls.marketprices(broker, pair, period, endtime=endtime, starttime=starttime, n_period=n_period)
                marketprice_list = marketprice_df.to_numpy().tolist()
                marketprice = cls.new_marketprice(broker.__class__, marketprice_list, pair, period)
                marketprices.put(marketprice, pair, period)
            return marketprice
        
        def catch_error() -> MarketPrice:
            return _MF.catch_exception(ge_marketprice, MarketPrice.__name__, **{'marketprices': marketprices, 'pair': pair, 'period': period, 'endtime': endtime, 'starttime': starttime, 'n_period': n_period})

        marketprices = marketprices if marketprices is not None else Map()
        unix_time = _MF.get_timestamp()
        analyses = {}
        for period in periods:
            supertrends_df = pd.DataFrame()
            closes_df = pd.DataFrame()
            for pair in pairs:
                marketprice = catch_error()
                if (marketprice is None) or (len(marketprice.get_times()) == 0):
                    continue
                open_times = list(marketprice.get_times())
                open_times.reverse()
                closes = list(marketprice.get_closes())
                closes.reverse()
                supertrends = list(marketprice.get_super_trend())
                supertrends.reverse()
                # Close
                new_closes_df = pd.DataFrame({pair: closes}, index=open_times)
                closes_df = join_df(pair, closes_df, new_closes_df)
                # Supertrend
                new_supertrends_df = pd.DataFrame({pair: supertrends}, index=open_times)
                supertrends_df = join_df(pair, supertrends_df, new_supertrends_df)
            # Supertrend str
            supertrends_str_df = pd.DataFrame(columns=closes_df.columns, index=closes_df.index)
            supertrends_str_df[closes_df.columns] = ''
            supertrends_str_df[(closes_df > supertrends_df)] = MarketPrice.SUPERTREND_RISING
            supertrends_str_df[(closes_df < supertrends_df)] = MarketPrice.SUPERTREND_DROPPING
            # Record analyse
            # ••• prepare
            period_str = broker.period_to_str(period)
            analyse_df = pd.DataFrame([], index=supertrends_str_df.index)
            # ••• build market dates
            market_dates = [_MF.unix_to_date(open_time) for open_time in list(analyse_df.index)]
            market_dates_df = pd.DataFrame({Map.date: market_dates}, index=analyse_df.index)
            # ••• build rows to print
            analyse_df[Map.date] = _MF.unix_to_date(_MF.get_timestamp())
            analyse_df['market_date'] = market_dates_df[Map.date]
            analyse_df[Map.period] = period_str
            analyse_df['n_pair'] = supertrends_str_df.shape[1]
            analyse_df['n_rise'] = supertrends_str_df[supertrends_str_df == MarketPrice.SUPERTREND_RISING].count(axis=1)
            analyse_df['rise_rate'] = analyse_df['n_rise']/analyse_df['n_pair']
            analyse_df['n_drop'] = supertrends_str_df[supertrends_str_df == MarketPrice.SUPERTREND_DROPPING].count(axis=1)
            analyse_df['drop_rate'] = analyse_df['n_drop']/analyse_df['n_pair']
            # ••• put
            analyses[period] = analyse_df
        return analyses

    @staticmethod
    def macd(closes: list, slow: int, fast: int, signal: int) -> Map:
        """
        To generate the Moving Average Convergence Divergence (MACD)\n
        Parameters:
        -----------
        closes: list
            Market's close prices.
        slow: int
            Number period long term
        fast: int
            Number period short term
        signal
            Number period to signal

        Returns:
        --------
        return:  Map
            MACD's macd, signal line and Histogram
            macd[Map.macd]:         {List}
            macd[Map.signal]:       {List}
            macd[Map.histogram]:    {List}
        """
        pd_closes = pd.Series(np.array(closes))
        macd_obj = MACD(pd_closes, slow, fast, signal)
        macd_map = Map({
            Map.macd: macd_obj.macd().to_list(),
            Map.signal: macd_obj.macd_signal().to_list(),
            Map.histogram: macd_obj.macd_diff().to_list()
        })
        return macd_map

    @classmethod
    def keltnerchannel(cls, highs: list, lows: list, closes: list, window: int, multiplier: float, original_version: bool) -> Map:
        """
        To generate Keltner Channels\n
        Parameters
        ----------
        highs: list
            Market's hight prices
        lows: list
            Market's low prices
        closes: list
            Market's close prices
        window: int
            The number of period to use
        multiplier: float
            Multiple of middle Keltner
        original_version: bool
            True to use original version as the centerline (SMA of typical price) else False to use EMA of close
        Returns
        -------
        indicator: Map
            Keltner Channels
            indicator[Map.high]:    {list}  # Keltner Channel's High Band
            indicator[Map.middle]:  {list}  # Keltner Channel's middle Band
            indicator[Map.low]:     {list}  # Keltner Channel's low Band
        """
        pd_closes = pd.Series(np.array(closes))
        pd_highs = pd.Series(np.array(highs))
        pd_lows = pd.Series(np.array(lows))
        kel_obj = KeltnerChannel(pd_highs, pd_lows, pd_closes, window, multiplier=multiplier, original_version=original_version)
        hband = kel_obj.keltner_channel_hband()
        mband = kel_obj.keltner_channel_mband()
        lband = kel_obj.keltner_channel_lband()
        hband_list = hband.to_list()
        mband_list = mband.to_list()
        lband_list = lband.to_list()
        kel_map = Map({
            Map.high: hband_list,
            Map.low: lband_list,
            Map.middle: mband_list
        })
        return kel_map

    @staticmethod
    def bollingerbands(closes: list, window: int, window_dev: int) -> Map:
        """
        To generate Bollinger Bands

        Parameters:
        -----------
        closes: list
            Market's closes prices
        window: int
            The number of period to use
        window_dev: int
            n factor standard deviation

        Returns:
        --------
        return: Map
            Bollinger Bands
            indicator[Map.high]:    {list}  # Bollinger Bands's High Band
            indicator[Map.middle]:  {list}  # Bollinger Bands's middle Band
            indicator[Map.low]:     {list}  # Bollinger Bands's low Band
            indicator[Map.width]:   {list}  # Bollinger Bands's Width
            indicator[Map.rate]:    {list}  # Bollinger Bands's Percentage Band
        """
        pd_closes = pd.Series(np.array(closes))
        bollinger = BollingerBands(pd_closes, window, window_dev)
        bollinger_high = bollinger.bollinger_hband().to_list()
        bollinger_middle = bollinger.bollinger_mavg().to_list()
        bollinger_low = bollinger.bollinger_lband().to_list()
        bollinger_width = bollinger.bollinger_wband().to_list()
        bollinger_rate = bollinger.bollinger_pband().to_list()
        bollinger_rate_map = Map({
            Map.high: bollinger_high,
            Map.middle: bollinger_middle,
            Map.low: bollinger_low,
            Map.width: bollinger_width,
            Map.rate: bollinger_rate
        })
        return bollinger_rate_map

    @staticmethod
    def roc(closes: list, window: int) -> list:
        closes_series = pd.Series(closes)
        roc_obj = ROCIndicator(closes_series, window)
        roc = roc_obj.roc().to_list()
        return roc

    @staticmethod
    def get_spot_pairs(broker_class: str, fiat_asset: Asset) -> List[Pair]:
        """
        To get pairs available for spot trading\n
        Parameters
        ----------
        broker_class: str
            Class name of a Broker
        fiat_asset: Asset
            Asset to use as right asset
        Returns
        -------
        pairs: List[Pair]
            Pairs available for spot trading
        """
        exec(f'from model.API.brokers.{broker_class}.{broker_class} import {broker_class}')
        _bkr_cls = eval(broker_class)
        stablecoins = Config.get(Config.CONST_STABLECOINS)
        concat_stable = '|'.join(stablecoins)
        stablecoin_rgx = f'({concat_stable})/\w+$'
        # Fiat regex
        fiats = Config.get(Config.CONST_FIATS)
        concat_fiat = '|'.join(fiats)
        fiat_rgx = rf'({concat_fiat})/\w+$'
        # Get pairs
        no_match = [
            r'^\w+(up|down|bear|bull)\/\w+$',
            r'^(bear|bull)/\w+$',
            r'^\w*inch\w*/\w+$',
            fiat_rgx,
            stablecoin_rgx
        ]
        match = [rf'^.+\/{fiat_asset.__str__()}']
        # Add streams
        pair_strs = _bkr_cls.get_pairs(match=match, no_match=no_match)
        pairs = [Pair(pair_str) for pair_str in pair_strs]
        return pairs

    @staticmethod
    def marketprice(broker: 'Broker', pair: Pair, period: int, n_period: int, starttime: int = None, endtime: int = None) -> 'MarketPrice':
        """
        To request MarketPrice to Broker

        Parameters
        ----------
        broker: Broker
            Access to a Broker's API
        pair: Pair
            Pair to get market prices for
        period: int
            The period interval to request
        n_period: int
            The number of period to retrieve
        starttime: int
            The older time
        endtime: int
            The most recent time

        Returns
        -------
        return: MarketPrice
            MarketPrice from Broker's API
        """
        from model.tools.BrokerRequest import BrokerRequest

        _bkr_cls = broker.__class__.__name__
        mkt_params = Map({
            Map.pair: pair,
            Map.period: period,
            Map.begin_time: starttime,
            Map.end_time: endtime,
            Map.number: n_period
        })
        bkr_rq = broker.generate_broker_request(
            _bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_params)
        broker.request(bkr_rq)
        return bkr_rq.get_market_price()

    @staticmethod
    def marketprices(broker: 'Broker', pair: Pair, period: int, endtime: int, starttime: int = None, n_period: int = None) -> pd.DataFrame:
        """
        To request recurisively market history from starttime (older) to endtime (recent)
        NOTE: if there's not enough period between starttime and endtime, market history already downloaded is returned

        Parameters
        ----------
        broker: Broker
            Access to a Broker's API
        pair: Pair
            Pair to get market prices for
        period: int
            The period interval to request
        n_period: int
            The number of period to retrieve
        endtime: int
            The most recent open time (in second)
        starttime: int
            The older open time (in second)
        n_period: int
            The number of period to retrieve

        Raise
        ------
        raise: Exception
            endtime is before actual time
        raise: Exception
            starttime is after or equal endtime
        raise: Exception
            if starttime and n_period are both None
        raise: Exception
            if starttime and n_period are both set

        Returns
        -------
            The market history from starttime (older) to endtime (recent)
        """
        unix_time = _MF.get_timestamp()
        if starttime == n_period == None:
            raise ValueError(f"starttime and n_period can't both be None")
        if (starttime != None) and (n_period != None):
            raise ValueError(f"starttime '{starttime}' and n_period '{n_period}' can't both be set")
        if (starttime is not None) and (not isinstance(starttime, int)):
            raise ValueError(f"Param 'starttime' must be type int, instead '{type(starttime)}'")
        if not isinstance(endtime, int):
            raise ValueError(f"Param 'endtime' must be type int, instead '{type(endtime)}'")
        if endtime > unix_time:
            raise Exception(f"The endtime must be before than actual time, instead endtime'{endtime}' > actual'{unix_time}'")
        if (starttime is not None) and (starttime >= endtime):
            raise Exception(f"The starttime must be before than endtime, instead starttime'{starttime}' >= endtime'{endtime}'")
        if starttime is None:
            starttime = endtime - (n_period * period)
        starttime = _MF.round_time(starttime, period) - period
        max_n_period = broker.get_max_n_period()
        endtime = _MF.round_time(endtime, period)
        endtime_copy = endtime
        marketprices = None
        end = False
        while not end:
            marketprice = MarketPrice.marketprice(broker, pair, period, n_period=max_n_period, endtime=endtime_copy)
            market = list(marketprice.get_market())
            market.reverse()
            martket_np = np.array(market, dtype=np.float64)
            marketprices = martket_np if marketprices is None else np.vstack((martket_np, marketprices))
            endtime_copy -= period * max_n_period
            end = (martket_np.shape[0] < max_n_period) \
                or (endtime_copy <= starttime)
        # Convert to DataFrame
        marketprices_pd = pd.DataFrame(marketprices, columns=[str(i) for i in range(marketprices.shape[1])])
        # Drop duplicates
        marketprices_pd = marketprices_pd.drop_duplicates(subset='0', keep='last', ignore_index=True)
        # Sort following the open time
        marketprices_pd = marketprices_pd.sort_values(by='0', axis=0, ascending=True)
        # Remove exceeding periods
        marketprices_pd = marketprices_pd[(marketprices_pd.iloc[:,0] >= ((starttime+period)*1000)) & (marketprices_pd.iloc[:,0] <= (endtime*1000))]
        return marketprices_pd

    @classmethod
    def download_marketprices(cls, broker: 'Broker', pairs: List[Pair], periods: List[int], endtime: int, starttime: int) -> None:
        """
        To download and save markt prices

        Parameters:
        -----------
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            List of Pair to download
        periods: List[int]
            List of period to download (in second)
        endtime: int
            The most recent time to download (in second)
        starttime: int
            The older time to download (in second)
        """
        def get_marketprices(broker: 'Broker', pair: Pair, period: int, endtime: int, starttime: int) -> pd.DataFrame:
            marketprice_pd = _MF.catch_exception(cls.marketprices, cls.__name__, repport=True, **{
                'broker': broker, 
                'pair': pair, 
                'period': period, 
                'endtime': endtime, 
                'starttime': starttime
                })
            return marketprice_pd

        def print_history(path: str, marketprice: pd.DataFrame) -> None:
            csv = marketprice.to_csv(index=False)
            FileManager.write(path, csv, overwrite=True, make_dir=True)
        
        def print_config(path: str, marketprice: pd.DataFrame) -> None:
            first_time = int(marketprice.iloc[0,0]/1000)
            last_time = int(marketprice.iloc[-1,0]/1000)
            max_high = marketprice.iloc[:,2].max()
            min_low = marketprice.iloc[:,3].min()
            roi = _MF.progress_rate(max_high, min_low)
            rows = [{
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.broker: broker_name,
                Map.pair: pair,
                Map.period: period,
                Map.interval: _MF.delta_time(0, period),
                Map.shape: marketprice.shape,
                Map.start_time: _MF.unix_to_date(first_time),
                Map.end_time: _MF.unix_to_date(last_time),
                Map.time: _MF.delta_time(first_time, last_time),
                Map.roi: roi,
                f"{Map.roi}_str": _MF.rate_to_str(roi)
            }]
            fields = list(rows[0].keys())
            file_path = path + 'config.csv'
            FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)

        _back_cyan = '\033[46m' + '\033[30m'
        _normal = '\033[0m'
        broker_name = broker.__class__.__name__
        # Ouput
        n_turn = len(pairs) * len(periods)
        turn = 1
        out_starttime = _MF.get_timestamp()
        _MF.output(f"{_MF.prefix() + _back_cyan}Start extracting prices of '{len(pairs)}' pairs from '{_MF.unix_to_date(starttime)}' to '{_MF.unix_to_date(endtime)}'{_normal}")
        for pair in pairs:
            for period in periods:
                _MF.output(_MF.loop_progression(out_starttime, turn, n_turn, message=f"{pair.__str__().upper()} {int(period/60)}min."))
                turn += 1
                if cls.exist_history(broker_name, pair, period):
                    marketprice_pd = cls.load_marketprice(broker_name, pair, period, active_path=False)
                    old_starttime = int(marketprice_pd.iloc[0,0]/1000)
                    old_endtime = int(marketprice_pd.iloc[-1,0]/1000)
                    if (old_starttime - starttime) > 0:
                        # Download before existing history
                        before_marketprice_pd = get_marketprices(broker, pair, period, old_starttime, starttime)
                        marketprice_pd = pd.concat([before_marketprice_pd[:-1], marketprice_pd], ignore_index=True)
                    if (endtime - old_endtime) > 0:
                        # Download after existing history
                        after_marketprice_pd = get_marketprices(broker, pair, period, endtime, old_endtime)
                        marketprice_pd = pd.concat([marketprice_pd, after_marketprice_pd.iloc[1:]], ignore_index=True)
                else:
                    marketprice_pd = get_marketprices(broker, pair, period, endtime, starttime)
                    if marketprice_pd is None:
                        continue
                file_path = cls.file_path_market_history(broker_name, pair, period, active_path=False)
                dir_path = cls.dir_path_market_history(broker_name, pair, active_path=False)
                print_history(file_path, marketprice_pd)
                print_config(dir_path, marketprice_pd)

    @staticmethod
    def load_marketprice(broker_name: str, pair: Pair, period: int, active_path: bool) -> pd.DataFrame:
        """
        To load market history

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        pair: Pair
            Pair to get file path of
        period: int
            Period to get file path of (in second)
        active_path: bool
            Set True to access histories for the running session 
            else False to access stored histories

        Return:
        -------
        return: pd.DataFrame
            Loaded market history
        """
        if active_path:
            pair_dir_path = MarketPrice.dir_path_pair(broker_name, active_path=True)
            str_pairs = FileManager.get_dirs(pair_dir_path, make_dir=True)
            if pair.format(Pair.FORMAT_UNDERSCORE).upper() not in str_pairs:
                raise ValueError(f"This Pair '{pair}' don't has its Active history")
        else:
            pair_dir_path = MarketPrice.dir_path_pair(broker_name, active_path=False)
            str_pairs = FileManager.get_dirs(pair_dir_path, make_dir=True)
            if pair.format(Pair.FORMAT_UNDERSCORE).upper() not in str_pairs:
                raise ValueError(f"This Pair '{pair}' don't has its Stock history")
        stock_file_path = MarketPrice.file_path_market_history(broker_name, pair, period, active_path=False)
        project_dir = FileManager.get_project_directory()
        history = pd.read_csv(project_dir + stock_file_path)
        return history

    @classmethod
    def exist_history(cls, broker_name: str, pair: Pair, period: int) -> bool:
        """
        To check if a market history exist

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        pair: Pair
            Pair of the history to check
        period: int
            Period of the history to check (in second)

        Returns:
        --------
        return: bool
            True if exist a history else False
        """
        active_path = False
        file_path = cls.file_path_market_history(broker_name, pair, period, active_path)
        file_name = file_path.split('/')[-1]
        dir_path_history = cls.dir_path_market_history(broker_name, pair, active_path)
        history_files = _MF.catch_exception(FileManager.get_files, cls.__name__, repport=True, **{'path': dir_path_history, 'make_dir': False})
        exist_history = (file_name in history_files) if isinstance(history_files, list) else False
        return exist_history

    @staticmethod
    def file_path_market_history(broker_name: str, pair: Pair, period: int, active_path: bool = True) -> str:
        """
        To get the file path to a market price history

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        pair: Pair
            Pair to get file path of
        period: int
            Period to get file path of (in second)
        active_path: bool = True
            Set True to get file path to history for the running session 
            else False to get path to where histories are stored

        Return:
        -------
        return: str
            The file path to the market price history with the give pair and period
        """
        canvas = Config.get(Config.FILE_PATH_MARKET_HISTORY)
        hist_path = MarketPrice._HISTORY_PATHS
        underscored_pair = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        stock_path = hist_path[Map.active] if active_path else hist_path[Map.stock]
        file_path = canvas.replace('$stock_path', stock_path).replace('$broker', broker_name).replace('$pair', underscored_pair).replace('$period', str(period))
        return file_path

    @staticmethod
    def dir_path_market_history(broker_name: str, pair: Pair, active_path: bool) -> str:
        """
        To get the directory path to where all market histories are stored

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        pair: Pair
            Pair to get file path of
        active_path: bool
            Set True to get file path to history for the running session 
            else False to get path to where histories are stored

        Return:
        -------
        return: str
            The directory path to where all market histories are stored
        """
        period = -1
        file_path = MarketPrice.file_path_market_history(broker_name, pair, period, active_path)
        dir_path = FileManager.path_to_dir(file_path)
        return dir_path

    @staticmethod
    def dir_path_pair(broker_name: str, active_path: bool) -> str:
        """
        To get directory path to where all pairs are stored

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        active_path: bool
            Set True to access histories for the running session 
            else False to access stored histories

        Returns:
        -------
        return: str
            Directory path to where all pairs are stored
        """
        pair = Pair('none/none')
        dir_path = MarketPrice.dir_path_market_history(broker_name, pair, active_path)
        pairs_dir_path = '/'.join(dir_path.split('/')[:-2]) + '/'
        return pairs_dir_path

    @staticmethod
    def history_pairs(broker_name: str, active_path: bool) -> List[Pair]:
        """
        To get list of Pair with a history

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker
        active_path: bool
            Set True to access histories for the running session 
            else False to access stored histories

        Return:
        -------
        return: List[Pair]
            List of Pair with a history
        """
        pair_dir_path = MarketPrice.dir_path_pair(broker_name, active_path)
        str_pairs = FileManager.get_dirs(pair_dir_path, make_dir=True)
        pairs = [Pair(*str_pair.split(Pair.UNDERSCORE)) for str_pair in str_pairs]
        return pairs

    @staticmethod
    def history_periods(broker_name: str) -> List[int]:
        """
        To get list of period available for market histories

        Parameters:
        -----------
        broker_name: str
            Class name of a supported Broker

        Return:
        -------
        return: List[int]
            List of period available for market histories
        """
        _cls = MarketPrice
        if _cls._HISTORY_PERIODS is None:
            dir_path_pair = _cls.dir_path_pair(broker_name, active_path=False)
            underscored_pairs = FileManager.get_dirs(dir_path_pair, make_dir=True)
            pair = Pair(*underscored_pairs[0].split(Pair.UNDERSCORE))
            history_dir_path = _cls.dir_path_market_history(broker_name, pair, active_path=False)
            history_files = FileManager.get_files(history_dir_path)
            regex = _cls.regex_history_file()
            periods = [int(file.split('.')[0]) for file in history_files if _MF.regex_match(regex, file)]
            periods.sort()
            _cls._HISTORY_PERIODS = periods
        return _cls._HISTORY_PERIODS

    @staticmethod
    def regex_history_file() -> str:
        return MarketPrice._REGEX_HISTORY_FILE

    @staticmethod
    def last_extremum_index(values: list, zeros: list, extremum: int, excludes: list = []) -> int:
        """
        To get index of the last extremum
        * 1: to get index of the last peak
        * 0: to get index of the last zero
        * -1: to get index of the last minimum

        Parameters:
        -----------
        values: list
            Values to search peak in
        zeros: list
            Values to use as comparaison base
        extremum: int
            The extremum to get
        exclude: list = []
            List of index to exclude (can be positive of negative)

        Returns:
        --------
        Index of the last peak
        """
        def excludes_are_in(swings: list, excludes: list) -> bool:
            index_range = range(swings[i][0], (swings[i][1] + 1))
            excludes_in = sum([1 for exclude in excludes if exclude in index_range]) > 0
            return excludes_in
        
        if extremum not in [1, 0, -1]:
            raise ValueError(f"Extremum must be '1', '0', or '-1', instead '{extremum}'")
        last_peak_index = None
        n_row = len(values)
        excludes = [(n_row + i) if (isinstance(float(values[i]), float)) and (i < 0) else i for i in excludes]
        zero_np = np.array(zeros)
        values_pd = pd.DataFrame({Map.x: values, Map.zero: zero_np})
        swings = _MF.group_swings(values, zero_np.tolist())
        i = n_row - 1
        while i >= 0:
            if extremum == 1:
                in_group = values[i] > zeros[i]
            elif extremum == 0:
                in_group = values[i] == zeros[i]
            elif extremum == -1:
                in_group = values[i] < zeros[i]
            if in_group and (not excludes_are_in(swings, excludes)):
                sub_values = values_pd.loc[swings[i][0]:(swings[i][1]), Map.x]
                if extremum in [1, -1]:
                    target_value = sub_values.max() if extremum == 1 else sub_values.min()
                    last_peak_index = sub_values[sub_values == target_value].index[-1]
                else:
                    last_peak_index = sub_values.index[-1]
                break
            else:
                i = swings[i][0]
            del in_group
            i -= 1
        return last_peak_index

    @classmethod
    def mean_candle_variation(cls, open_prices: List[float], close_prices: List[float]) -> Map:
        """
        To get mean variation rate of positive and negative candles and their standard deviation

        Parameters:
        -----------
        open_prices: List[float]
            List of open price
        close_prices: List[float]
            List of close price

        Raises:
        -------
        raise: ValueError
            If list of open and close pricse have not the same size

        Returns:
        --------
        return: Map
            Map[Map.all | positive | negative][Map.mean]:   {float} # mean variation rate of all | positive | negative candle
            Map[Map.all | positive | negative][Map.stdev]:  {float} # standard deviation of all | positive | negative candle
            Map[Map.all | positive | negative][Map.number]: {int}   # number of candle used
        """
        def mean_candle(candles: np.ndarray, mean_type: int) -> Tuple[float, float]:
            result = None
            std_dev = None
            n_candle = None
            if mean_type == 0:
                sub_candles = candles
                result = candles.mean()
            elif mean_type == 1:
                sub_candles = candles[candles > 0]
                result = sub_candles.mean()
            elif mean_type == -1:
                sub_candles = candles[candles < 0]
                result = sub_candles.mean()
            else:
                raise ValueError(f"This mean type '{mean_type}' is not supported")
            if sub_candles.shape[0] > 2:
                result = float(sub_candles.mean())
                std_dev = float(statistics.stdev(sub_candles))
                n_candle = sub_candles.shape[0]
            return result, std_dev, n_candle

        n_open = len(open_prices)
        n_close = len(close_prices)
        if n_open != n_close:
            raise ValueError(f"The list of open and close prices must have the same size, instead '{n_open}'!='{n_close}'")
        # Make candle
        open_prices = np.array(open_prices)
        close_prices = np.array(close_prices)
        candles = (close_prices - open_prices)/open_prices
        # Calcul
        all_var, all_stddev, n_all_candle = mean_candle(candles, 0)
        pos_var, pos_stddev, n_pos_candle = mean_candle(candles, 1)
        neg_var, neg_stddev, n_neg_candle = mean_candle(candles, -1)
        results = Map({
            Map.all: {Map.mean: all_var, Map.stdev: all_stddev, Map.number: n_all_candle},
            Map.positive: {Map.mean: pos_var, Map.stdev: pos_stddev, Map.number: n_pos_candle},
            Map.negative: {Map.mean: neg_var, Map.stdev: neg_stddev, Map.number: n_neg_candle}
        })
        return results

    @classmethod
    def mean_candle_sequence(cls, open_prices: List[float], close_prices: List[float]) -> Map:
        """
        To calculate mean number of consecutive positive and negative candles

        Parameters:
        -----------
        open_prices: List[float]
            List of open price
        close_prices: List[float]
            List of close price

        Raises:
        -------
        raise: ValueError
            If list of open and close pricse have not the same size

        Returns:
        --------
        return: Map
            Map[Map.positive]: {float}  # Mean number of of consecutive positive candles
            Map[Map.negative]: {float}  # Mean number of of consecutive positive candles
        """
        n_open = len(open_prices)
        n_close = len(close_prices)
        if n_open != n_close:
            raise ValueError(f"The list of open and close prices must have the same size, instead '{n_open}'!='{n_close}'")
        open_prices = np.array(open_prices)
        close_prices = np.array(close_prices)
        candles = (close_prices - open_prices)/open_prices
        zeros = np.zeros(n_open, dtype=int)
        candle_swings = _MF.group_swings(candles, zeros)
        pos_sequence = []
        neg_sequence = []
        i = 0
        while i < n_open:
            start_index = candle_swings[i][0]
            end_index = candle_swings[i][1]
            n_candle = (end_index - start_index + 1)
            if candles[i] > 0:
                pos_sequence.append(n_candle)
            elif candles[i] < 0:
                neg_sequence.append(n_candle)
            i = end_index
            i += 1
        n_pos_sequence = len(pos_sequence)
        n_neg_sequence = len(neg_sequence)
        result = Map({
            Map.positive: sum(pos_sequence)/n_pos_sequence if n_pos_sequence > 0 else 0,
            Map.negative: sum(pos_sequence)/n_neg_sequence if n_neg_sequence > 0 else 0
        })
        return result

    @classmethod
    def new_marketprice(cls, broker: Callable, marketprice_list: List[List[float]], pair: Pair, period: int) -> 'MarketPrice':
        """
        To instantiate a MarketPrice object for the given Broker

        Parameters:
        -----------
        broker: Callable
            Class of Broker used to get prices
        marketprice_list: List[list]
            List of prices
        pair: Pair
            Pair used to get prices
        period: int
            Period used to get prices

        Returns:
        --------
        return: MarketPrice
            MarketPrice object for the given Broker
        """
        class_name = f"{broker.__name__}{MarketPrice.__name__}"
        import_exec = _MF.get_import(class_name)
        exec(import_exec)
        period_str = broker.period_to_str(period)
        market_class = eval(class_name)
        marketprice = market_class(marketprice_list, period_str, pair)
        return marketprice

    @staticmethod
    def _save_market(market_price: 'MarketPrice') -> None:
        p = Config.get(Config.DIR_SAVE_MARKET)
        mkt = market_price.get_market()
        mkt = [[str(v) for v in row] for row in mkt]
        mkt.reverse()
        rows = [{
            Map.time: _MF.unix_to_date(_MF.get_timestamp()),
            Map.pair: market_price.get_pair(),
            Map.interval: int(market_price.get_period_time() / 60),
            Map.number: len(mkt),
            Map.market: _MF.json_encode(mkt)
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite, make_dir=True)
