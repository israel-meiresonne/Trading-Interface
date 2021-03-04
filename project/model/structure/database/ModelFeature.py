from abc import abstractmethod
from datetime import datetime
from json import dumps as json_encode
from json import loads as json_decode
from time import time as time_time
from typing import Union, Any

import numpy as np
from scipy.signal import find_peaks

from model.structure.database.ModelAccess import ModelAccess


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
