import dill
import re as rgx
import threading
from abc import abstractmethod
from datetime import datetime
from json import dumps as json_encode
from json import loads as json_decode
from random import shuffle
from time import time as time_time
from typing import Union, Any

import numpy as np
from pytz import timezone
from scipy.signal import find_peaks
from scipy.stats import linregress

from model.structure.database.ModelAccess import ModelAccess


class ModelFeature(ModelAccess):
    TIME_SEC = "time_sec"
    TIME_MILLISEC = "time_millisec"
    FORMAT_D_H_M_S_MS = '%Y-%m-%d %H:%M:%S.%f'
    FORMAT_D_H_M_S = '%Y-%m-%d %H:%M:%S'
    FORMAT_D_H_M_S_FOR_FILE = '%Y-%m-%d_%H.%M.%S'
    TIME_ZONE_UTC = 'UTC'

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
    def unix_to_date(time: int, form: str = FORMAT_D_H_M_S, timezone_str: str = TIME_ZONE_UTC) -> str:
        # return datetime.fromtimestamp(time).strftime(form)
        return datetime.fromtimestamp(time, timezone(timezone_str)).strftime(form)

    # abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
    @staticmethod
    def new_code(size: int = 20, salt: str = 'abcdefghijklmnopqrstuvwxyz') -> str:
        """
        To generate code based on unix time in millisecond\n
        :param size: the  total size of the code
                    NOTE: the min size is 13
        :param salt: the string to use
        :return: a code based on unix time in millisecond
        """
        time = str(ModelFeature.get_timestamp(ModelFeature.TIME_MILLISEC))
        min_size = len(time)
        if size < min_size:
            raise ValueError(f"The code's size must be equal or over '{min_size}'.")
        salt = list(salt)
        shuffle(salt)
        code = time
        nb_salt = size - min_size
        subsalt = [salt[i] for i in range(len(salt)) if i < nb_salt]
        code += ''.join(subsalt)
        code_list = list(code)
        shuffle(code_list)
        code = ''.join(code_list)
        return code

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
    def clean(tab: Union[list, dict]) -> Union[list, dict]:
        """
        Clean collection by removing None or empty string element\n
        :param tab: the collection to clean
        :return: a brand new collection with new reference
        """
        t = type(tab)
        if t == list:
            # return [v for v in tab if (v != '') and (v is not None)]
            return [v for v in tab if (v is not None)]
        elif t == dict:
            # return {k: v for k, v in tab.items() if (v != '') and (v is not None)}
            return {k: v for k, v in tab.items() if (v is not None)}
        else:
            raise ValueError(f"Can't clean this type '{t}'")

    @staticmethod
    def json_encode(d) -> str:
        return json_encode(d)

    @staticmethod
    def json_decode(json: str) -> Any:
        return json_decode(json)

    @staticmethod
    def get_maximums(ds: list) -> list:
        """
        To get indexes of maximums in the given list\n
        :param ds: list of values
        :return: indexes of maximums in the given list
        """
        ys = np.array(ds)
        maxs, _ = find_peaks(ys)
        return list(maxs)

    @staticmethod
    def get_minimums(ds: list) -> list:
        """
        To get indexes of minimums in the given list\n
        :param ds: list of values
        :return: indexes of minimums in the given list
        """
        neg_ys = [-v for v in ds]
        mins, _ = find_peaks(neg_ys)
        return list(mins)

    @staticmethod
    def get_super_extremums(vs: list) -> list:
        maxs = ModelFeature.get_maximums(vs)
        max_vals = [vs[prd] for prd in maxs]
        mins = ModelFeature.get_minimums(vs)
        min_vals = [vs[prd] for prd in mins]
        fake_spr_maxs = ModelFeature.get_maximums(max_vals)
        spr_maxs = [maxs[prd] for prd in fake_spr_maxs]
        fake_spr_mins = ModelFeature.get_minimums(min_vals)
        spr_mins = [mins[prd] for prd in fake_spr_mins]
        spr_extrems = spr_maxs + spr_mins
        spr_extrems.sort()
        return spr_extrems

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
    def get_slope(y: list, x: list = None) -> 'Map':
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
        from model.tools.Map import Map
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
        from model.tools.Map import Map
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

    @staticmethod
    def slope_to_degree(slope: float) -> float:
        from math import atan as _arctg
        from math import pi as _pi
        rad = _arctg(slope)
        deg = rad*180/_pi
        return deg

    @staticmethod
    def get_nb_decimal(value: float) -> int:
        """
        To get the number of decimal in a number\n
        :param value:
        :return: number of decimal else None if given value is not float
        """
        if not isinstance(value, float):
            raise ValueError(f"The given value must be a float, instead '{value}'({type(value)})")
        return len(str(float(value)).split(".")[-1])  # if isinstance(value, float) else None

    @staticmethod
    def regex_match(regex: str, string: str) -> bool:
        """
        To check if a given string match the whole given regex\n
        :param regex: The regex to use
        :param string: To string to check
        :return: True if the string match the regex else False
        """
        return rgx.match(regex, string) is not None

    @staticmethod
    def regex_replace(regex: str, new_str: str, string: str) -> str:
        """
        To remplace the regex patern in the given string with a new one\n
        :param regex: The regex
        :param new_str: The replacement
        :param string: The string to search in
        :return: The given string with replacement if found
        """
        new_string = rgx.sub(regex, new_str, string)
        return new_string

    @staticmethod
    def float_to_str(val: float) -> str:
        return str(val).replace(".", ",") if val is not None else val

    @staticmethod
    def round_time(unix_time: float, interval: float) -> float:
        """
        To round the unix time to the last multiple of interval\n
        i.e: 2021-05-15 16:56:14 (interval=60*20) => 2021-05-15 16:40:00
        :param unix_time: Unix time
        :param interval: Interval in second
        :return: The last multiple of interval in second following the unix time given
        """
        last_unix = int(unix_time / interval) * interval
        return last_unix

    @staticmethod
    def prefix() -> str:
        date = ModelFeature.unix_to_date(ModelFeature.get_timestamp())
        thread_name = threading.current_thread().name
        return f"{date}| |{thread_name}| |"

    @staticmethod
    def thread_infos() -> str:
        import threading
        threads = threading.enumerate()
        thread_names = [thread.name for thread in threads]
        nb = threading.active_count()
        thread_infos = f"Threads ('{nb}'): '{thread_names}'"
        return thread_infos

    @staticmethod
    def generate_thread_name(thread_base_name: str, code_size: int = None) -> str:
        if (code_size is not None) and (code_size <= 0):
            raise ValueError(f"Code size must be > 0 or None")
        new_code = ModelFeature.new_code()
        if code_size is None:
            thread_code = new_code
        elif code_size > len(new_code):
            thread_code = ModelFeature.new_code(code_size)
        else:
            thread_code = new_code[0:code_size]
        return f'Thread_{thread_base_name}_{thread_code}'

    @staticmethod
    def remove_duplicates(values: list) -> list:
        """
        To remove duplicate values from list\n
        Parameters
        ----------
        values: list
            List of values

        Returns
        -------
        cleaned: list
            New list without any duplicate
        """
        return list(dict.fromkeys(values))

    @staticmethod
    def rate_to_str(rate: float) -> str:
        return f"{round(rate * 100, 2)}%"
    
    @staticmethod
    def binary_encode(obj: object) -> str:
        return dill.dumps(obj)

    @staticmethod
    def binary_decode(binary: str) -> object:
        return dill.loads(binary)
    
    @staticmethod
    def progress_rate(new_value: float, old_value: float) -> float:
        if (new_value < 0) or (old_value <= 0):
            raise ValueError(f"Don't respect contraint '(new_value'{new_value}' < 0) or (old_value'{old_value}' <= 0)'")
        return new_value / old_value - 1
