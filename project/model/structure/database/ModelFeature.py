from abc import abstractmethod
from datetime import datetime
from json import dumps as json_encode
from json import loads as json_decode
from time import time as time_time
from typing import Union, Any

import numpy as np
from scipy.signal import find_peaks
from scipy.stats import linregress

from model.structure.database.ModelAccess import ModelAccess
from model.tools.Map import Map


class ModelFeature(ModelAccess):
    TIME_SEC = "time_sec"
    TIME_MILLISEC = "time_millisec"

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get_timestamp(unit=TIME_SEC) -> int:
        """
        To get the timestamp in the given unit\n
        :param unit: a supported time unit
        :return: the timestamp in the given unit
        """
        if unit == ModelFeature.TIME_MILLISEC:
            ts = int(time_time() * 1000)
        elif unit == ModelFeature.TIME_SEC:
            ts = int(time_time())
        else:
            raise Exception(f"This time unit '{unit}' is not supported")
        return ts

    @staticmethod
    def date_to_unix(date: str) -> float:
        return datetime.fromisoformat(date).timestamp()

    @staticmethod
    def unix_to_date(time: int, form: str = '%Y-%m-%d %H:%M:%S.%f') -> str:
        return datetime.fromtimestamp(time).strftime(form)

    @staticmethod
    def keys_exist(ks: list, mp: dict) -> Union[None, str]:
        """
        Check all keys exist in map\n
        :param ks: list of keys
        :param mp: map where to check if keys exist in
        :return: None if all keys exist else the value of the missing key
        """
        for k in ks:
            if k not in mp:
                return k
        return None

    @staticmethod
    def clean(tab: Union[list, dict]) -> [list, dict]:
        """
        Clean collection by removing None or empty string element\n
        :param tab: the collection to clean
        :return: a brand new collection with new reference
        """
        t = type(tab)
        if t == list:
            return [v for v in tab if (v != '') and (v is not None)]
        elif t == dict:
            return {k: v for k, v in tab.items() if (v != '') and (v is not None)}
        else:
            raise ValueError(f"Can't clean this type '{t}'")

    @staticmethod
    def json_encode(d) -> str:
        return json_encode(d)

    @staticmethod
    def json_decode(json: str) -> Any:
        return json_decode(json)

    @staticmethod
    def get_maximums(ds: list) -> tuple:
        """
        To get indexes of maximums in the given list\n
        :param ds: list of values
        :return: indexes of maximums in the given list
        """
        ys = np.array(ds)
        maxs, _ = find_peaks(ys)
        return tuple(maxs)

    @staticmethod
    def get_minimums(ds: list) -> tuple:
        """
        To get indexes of minimums in the given list\n
        :param ds: list of values
        :return: indexes of minimums in the given list
        """
        neg_ys = [-v for v in ds]
        mins, _ = find_peaks(neg_ys)
        return tuple(mins)

    @staticmethod
    def get_maximum(ds: list, min_idx: int, max_idx: int) -> int:
        if max_idx >= len(ds):
            raise IndexError(f"The max limit '{max_idx}' is out of the list '{len(ds)}'")
        if min_idx >= max_idx:
            raise ValueError(f"The max limit '{max_idx}' must be greater than the min limit '{min_idx}'")
        maxs = ModelFeature.get_maximums(ds)
        peak_idx = -1.1
        for idx in maxs:
            d = ds[idx]
            peak_idx = idx if peak_idx < 0 else peak_idx
            peak_idx = idx if (idx >= min_idx) and (idx <= max_idx) and (d > ds[peak_idx]) else peak_idx
        return peak_idx if (min_idx <= peak_idx <= max_idx) else None

    @staticmethod
    def list_slice(xs, begin: int, end: int) -> list:
        """
        Extract a slice of the list\n
        :param xs: The input array.
        :param begin: index where to begin
        :param end: index where to end
        :return: a slice of the given list
        """
        nb = len(xs)
        if end <= begin:
            raise ValueError(f"The end index '{end}' must be greater than the begin index '{begin}")
        if begin < 0:
            raise IndexError(f"The begin index '{begin}' must be positive")
        if end >= nb:
            raise IndexError(f"The end '{end}' index is out of the bound '{nb-1}'")
        seq = [xs[j] for j in range(begin, end + 1)]
        return seq

    @staticmethod
    def get_slope(y: list, x: list = None) -> Map:
        """
        To get slope of the linear regression\n
        :param y: Y axis values
        :param x: X axis values
        :return: slope of the linear regression
                 Map[Map.slope]         {float}
                 Map[Map.yaxis]         {float}
                 Map[Map.correlation]
                 Map[Map.pvalue]
                 Map[Map.stderr]
        """
        if (x is not None) and (len(y) != len(x)):
            raise ValueError(f"The have as much Y values than X values ({len(y)} != {len(x)})")
        x = [v for v in range(len(y))] if x is None else x
        slope, intercept, rvalue, pvalue, stderr = linregress(x, y)
        result = Map({Map.slope: slope,
                      Map.yaxis: intercept,
                      Map.correlation: rvalue,
                      Map.pvalue: pvalue,
                      Map.stderr: stderr,
                      })
        return result

    @staticmethod
    def get_slopes(xs: list, nb_prd: int) -> list:
        """
        To get slopes of a given list\n
        :param xs: list of value
        :param nb_prd: number of period to use for each slope
        :return: slopes of a given list
        """
        if nb_prd <= 1:
            raise ValueError(f"The number of period must be at less 2 instead '{nb_prd}'")
        idx = nb_prd
        sps = []
        for i in range(len(xs)):
            if i < idx-1:
                sps.append(None)
                continue
            slc = ModelFeature.list_slice(xs, (idx - nb_prd), idx - 1)
            sp = ModelFeature.get_slope(slc)
            sps.append(sp.get(Map.slope))
            idx += 1
        return sps

    @staticmethod
    def get_averages(xs: list, nb_prd: int) -> list:
        """
        To get averages of the given list\n
        :param xs: list of value
        :param nb_prd: number of period to use for each average
        :return: averages of a given list
        """
        if nb_prd <= 1:
            raise ValueError(f"The number of period must be at less 2 instead '{nb_prd}'")
        idx = nb_prd
        avgs = []
        for i in range(len(xs)):
            if i < idx-1:
                avgs.append(None)
                continue
            slc = ModelFeature.list_slice(xs, (idx - nb_prd), idx - 1)
            avg = sum(slc) / nb_prd
            avgs.append(avg)
            idx += 1
        return avgs
