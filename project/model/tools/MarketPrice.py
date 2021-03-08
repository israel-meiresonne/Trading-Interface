from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Union

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from scipy.signal import find_peaks

from model.tools.Map import Map


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
    COLLECTION_TIMES = "COLLECTION_TIMES"
    COLLECTION_MINS = "COLLECTION_MINS"
    COLLECTION_MAXS = "COLLECTION_MAXS"
    COLLECTION_EXTREMS = "COLLECTION_EXTREMS"
    COLLECTION_RSIS = "COLLECTION_RSIS"

    @abstractmethod
    def __init__(self, mkt: list, prd_time: int):
        """
        Constructor\n
        :param mkt: market prices.
        NOTE: market prices must be ordered from the newest to the older
        """
        # self.__market = tuple((Decimal(v) for v in mkt))
        self.__market = mkt
        self.__period_time = prd_time
        self.__indicators = Map()
        self.__collections = Map({
            self.COLLECTION_OPENS: None,
            self.COLLECTION_CLOSES: None,
            self.COLLECTION_NEG_CLOSES: None,
            self.COLLECTION_TIMES: None,
            self.COLLECTION_MINS: None,
            self.COLLECTION_MAXS: None,
            self.COLLECTION_EXTREMS: None,
            self.COLLECTION_RSIS: None
        })

    def get_period_time(self) -> int:
        return self.__period_time

    def get_market(self) -> tuple:
        return tuple(self.__market)

    def __get_collections(self) -> Map:
        return self.__collections

    def _set_collection(self, k: str, e: Union[list, tuple]) -> None:
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
        self._get_indicators().put(Decimal(v), k)

    def _get_indicators(self) -> Map:
        return self.__indicators

    def get_indicator(self, ind: str) -> Decimal:
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

    def get_close(self, prd=0) -> Decimal:
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

    def get_rsis(self, nb_prd: int = 14) -> tuple:
        """
        To get collection of RSI\n
        :param nb_prd: number of period to use to generate each RSI point
        :return: RSI generated with the market's prices
        """
        rsis = self._get_collection(self.COLLECTION_RSIS)
        if rsis is None:
            closes = list(self.get_closes())
            closes.reverse()
            pd_ser = pd.Series(np.array(closes))
            rsis_obj = RSIIndicator(pd_ser, nb_prd)
            rsis_series = rsis_obj.rsi()
            rsis = rsis_series.to_list()
            rsis.reverse()
            self._set_collection(self.COLLECTION_RSIS, tuple(rsis))
        return rsis

    def get_delta_price(self, new_prd=0, old_prd=1) -> Decimal:
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

    def _get_speed(self, new_prd: int, old_prd: int) -> Decimal:
        prd_time = self.get_period_time()
        delta = self.get_delta_price(new_prd, old_prd)
        time = (old_prd - new_prd + 1) * prd_time
        return Decimal(delta / time)

    def _get_rate(self, new_prd: int, old_prd: int) -> Decimal:
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
        return Decimal(closes[new_prd] / closes[old_prd] - 1)

    def get_futur_price(self, rate: float) -> Decimal:
        """
        To apply a rate variation on the most recent price\n
        :param rate: the rate to apply ]-∞,+∞[
        :return: price*(1+rate)
        """
        closes = self.get_closes()
        return Decimal(closes[0]) * Decimal(str(1 + rate))

    def get_slope(self, new_prd: int, old_prd: int) -> Decimal:
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
        x = [v for v in range(len(y))]
        coefs, _ = np.polynomial.polynomial.Polynomial.fit(x, y, 1, full=True)
        return Decimal(str(round(coefs.coef[1], 2)))

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
