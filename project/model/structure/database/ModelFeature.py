import datetime
import re
import subprocess
import threading
import time
from abc import abstractmethod
from json import dumps as json_encode
from json import loads as json_decode
from random import shuffle
from types import FunctionType, MethodType
from typing import Any, Tuple, Union

import dill
import numpy as np
import pandas as pd
import pytz
from scipy.signal import find_peaks
from scipy.stats import linregress

from model.structure.database.ModelAccess import ModelAccess


class ModelFeature(ModelAccess):
    OUTPUT = False
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
            ts = int(time.time() * 1000)
        elif unit == ModelFeature.TIME_SEC:
            ts = int(time.time())
        else:
            raise Exception(f"This time unit '{unit}' is not supported")
        return ts

    @staticmethod
    def date_to_unix(date: str, format: str = FORMAT_D_H_M_S, timezone_str: str = TIME_ZONE_UTC) -> float:
        local_time = pytz.timezone(timezone_str)
        naive_datetime = datetime.datetime.strptime(date, format)
        local_datetime = local_time.localize(naive_datetime, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        return utc_datetime.timestamp()

    @staticmethod
    def unix_to_date(time: int, form: str = FORMAT_D_H_M_S, timezone_str: str = TIME_ZONE_UTC) -> str:
        return datetime.datetime.fromtimestamp(time, pytz.timezone(timezone_str)).strftime(form)

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
        return re.match(regex, string) is not None

    @staticmethod
    def regex_replace(old_str: str, regex: str, new_str: str) -> str:
        """
        To remplace the regex patern in the given string with a new one\n
        :param string: The string to edit
        :param regex: The regex
        :param new_str: The replacement
        :return: The given string with replacement if found
        """
        new_string = re.sub(regex, new_str, old_str)
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
        thread_name = ModelFeature.thread_name()
        return f"{date}| |{thread_name}| |"

    @staticmethod
    def thread_infos() -> str:
        threads = threading.enumerate()
        thread_names = [thread.name for thread in threads]
        nb = threading.active_count()
        thread_infos = f"Threads ('{nb}'): '{thread_names}'"
        return thread_infos

    @staticmethod
    def thread_name() -> str:
        """
        To get name of the current Thread

        Returns:
        --------
        returrn: str
            Name of the current Thread
        """
        return threading.current_thread().name

    @staticmethod
    def generate_thread_name(thread_base_name: str, code_size: int = None) -> str:
        if (code_size is not None) and (code_size <= 0):
            raise ValueError(f"Code size must be > 0 or None")
        new_code = ModelFeature.new_code()
        if code_size is None:
            thread_code = ""
        elif code_size > len(new_code):
            thread_code = ModelFeature.new_code(code_size)
        else:
            thread_code = new_code[0:code_size]
        thread_code = '_' + thread_code if len(thread_code) > 0 else thread_code
        return f'Thread-{thread_base_name + thread_code}'

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
    
    @staticmethod
    def df_apply(df: pd.DataFrame, columns: list, func, params: list = None) -> pd.DataFrame:
        """
        To apply function on given columns of a DataFrame

        Parameters:
        -----------
        df: pd.DataFrame
            DataFrame to treat
        columns: list
            List of colomn name of given DataFrame
        func: function
            The function to apply on columns
        params: list = None
            Arguments to pass to function
        
        Returns:
        --------
        return: pd.DataFrame
            New DataFrame tranformed
        """
        df = df.copy()
        for col in columns:
            df[col] = df[col].apply(func, args=params) if params is not None else df[col].apply(func)
        return df

    def predict_endtime(starttime: int, turn: int, n_turn: int, now_time: int = None) -> int:
        """
        To predict when iteration will end

        Parameters:
        -----------
        starttime: int
            The unix time when loop started
        turn: int
            The number of tour done
        n_turn: int
            The number of tour to do
        now_time: int = None
            The actual unix time

        Returns:
        --------
        return: int
            The unix time of when iteration will end in second
        """
        if turn <= 0:
            raise ValueError(f"Number of turn done must be greater than Zero,instead '{turn}'")
        now_time = ModelFeature.get_timestamp() if now_time is None else now_time
        delta_time = now_time - starttime
        time_per_turn = delta_time / turn
        endtime = starttime + time_per_turn * n_turn
        return endtime
    
    def delta_time(starttime: int, endtime: int) -> datetime.timedelta:
        return datetime.timedelta(seconds=endtime-starttime)

    @staticmethod
    def loop_progression(starttime: int, turn: int, n_turn: int, message: str) -> str:
        _back_cyan = '\033[46m' + '\033[30m'
        _normal = '\033[0m'
        prefix_str = ModelFeature.prefix() + _back_cyan
        endtime = ModelFeature.predict_endtime(starttime, turn, n_turn) if turn > 1 else None
        endtime_str = ModelFeature.delta_time(starttime, endtime) if endtime is not None else '?'
        enddate = ModelFeature.unix_to_date(endtime) if endtime is not None else '?'
        status = prefix_str + f"[{turn}/{n_turn}] {message} == '{enddate}' == '{endtime_str}'" + _normal
        return status

    @staticmethod
    def catch_exception(callback: FunctionType, call_class: str, repport: bool = True, **kwargs) -> Any:
        """
        To wrap function in try-catch and execute it

        Parameters:
        -----------
        callback: FunctionType
            Function to wrap and execute
        call_class: str
            Name of the class raising the execption
        repport: bool = True
            Set True to repport exception else False
        **kwargs: dict[str, Any]
            Parameters for callback function to execute
        
        Return:
        -------
        return: Any
            The value returned by the callback if there's one else None
        """
        returned = None
        try:
            returned = callback(**kwargs)
        except Exception as e:
            if repport:
                from model.structure.Bot import Bot
                Bot.save_error(e, call_class)
        return returned

    @staticmethod
    def generate_thread(target: FunctionType, base_name: str, n_code: int = 5, **kwargs) -> Tuple[threading.Thread, str]:
        """
        To create a new thread

        Parameters:
        -----------
        target: FunctionType
            Function to execute i thread
        base_name: str
            Name of the new thread
        **kwargs: dict[str, Any]
            Parameters for callback function to execute

        Returns:
        --------
        return: Tuple[threading.Thread, str]
            New thread
            return[0]:  {Thread}
            return[1]:  {str}   # ouput message
        """
        _cls = ModelFeature
        thread_name = _cls.generate_thread_name(base_name, n_code)
        new_thread = threading.Thread(target=target, name=thread_name, kwargs=kwargs)
        output = f"New Thread '{thread_name}'!"
        return new_thread, output

    def wrap_thread(callback: FunctionType, call_class: str, base_name: str, repport: bool = True, **kwargs) -> Tuple[threading.Thread, str]:
        """
        To to generate a new thread wrapped in try-catch

        Parameters:
        -----------
        callback: FunctionType
            Function to wrap and execute
        base_name: str
            Name of the new thread
        call_class: str
            Name of the class raising the execption
        repport: bool = True
            Set True to repport exception else False
        **kwargs: dict[str, Any]
            Parameters for callback function to execute
        """
        _cls = ModelFeature
        wrap = _cls.catch_exception
        wrap_kwargs = {
            'callback': callback,
            'call_class': call_class,
            'repport': repport,
            **kwargs
            }
        thread, output = _cls.generate_thread(target=wrap, base_name=base_name, **wrap_kwargs)
        return thread, output

    @staticmethod
    def console(**kwargs) -> None:
        """
        To execute code in caller's context
        """
        _cls = ModelFeature
        pfx = _cls.prefix
        _normal = '\033[0m'
        _yellow = '\033[33m'
        locals().update(kwargs) if len(kwargs) > 0 else None
        end = False
        ex = f"{_yellow}>>>{_normal} "
        while not end:
            cmd = input(pfx() + _yellow + "Enter code:\n" + _normal)
            print(pfx() + ex + f"{cmd}")
            end = cmd == 'quit'
            try:
                rtn = eval(cmd) if not end else None
                print(pfx() + ex + f"{rtn}") if rtn is not None else None
            except Exception as e:
                print(e)

    @staticmethod
    def output(text: str) -> None:
        """
        To output messages

        Parameters:
        -----------
        text: str
            Message to output
        """
        if not ModelFeature.OUTPUT:
            from config.Config import Config
            from model.tools.FileManager import FileManager
            path = Config.get(Config.FILE_OUTPUT)
            FileManager.write(path, text, overwrite=False, make_dir=True, line_return=True)
        else:
            print(text)

    @staticmethod
    def wait_while(callback: FunctionType, value: Any, timeout: int, to_raise: Exception = None, **kwargs) -> None:
        """
        To wait until timeout for the callback to return the given value
        NOTE: Raise given exception if time is out

        Parameters:
        -----------
        callback: FunctionType
            Funtion to call
        value: Any
            Value to compare with calback's return
        timeout: int
            Time to wait for calback to match the given value
        to_raise: Exception = None
            Exception to raise if time is out
        **kwargs: dict[str, Any]
            Parameters for callback function
        """
        if (not isinstance(callback, FunctionType)) and (not isinstance(callback, MethodType)):
            raise TypeError(f"The callback must be of type '{FunctionType}' or '{MethodType}', instead '{type(callback)}'")
        if not isinstance(timeout, int):
            raise TypeError(f"The timeout must be of type '{int}', instead '{type(timeout)}'")
        if (to_raise is not None) and (not isinstance(to_raise, Exception)):
            raise TypeError(f"The exception to raise must be of type '{Exception}', instead '{type(to_raise)}'")
        i = 0
        while (callback(**kwargs) != value) and (i < timeout):
            i += 1
            time.sleep(1)
        if (to_raise is not None) and (i >= timeout):
            raise to_raise()

    @staticmethod
    def update_speed_test(speed_test: 'Map', test_name: str, starttime: int = None, endtime: int = None) -> None:
        from model.tools.Map import Map
        if starttime is not None:
            speed_test.put(starttime, test_name, Map.start)
        elif endtime is not None:
            speed_test.put(endtime, test_name, Map.end)
        else:
            raise ValueError("Start and end time can't both be None")

    @classmethod
    def print_speed_test(cls, speed_test: 'Map', class_name: str, function_name: str) -> None:
        from model.tools.Map import Map
        for test_name, row in speed_test.get_map().items():
            test_name = function_name.replace(",", ";")
            delta = f"speed_test,{class_name},{function_name},{test_name},{(row[Map.end] - row[Map.start])/1000}sec"
            cls.output(delta)

    @staticmethod
    def group_swings(values: list[float,int], zeros: list[float,int]) -> dict[int,list[int]]:
        """
        To group given values following if there are above, equal or bellow the corresponding zero value

        Parameters:
        -----------
        values: list[float,int]
            Values to group
        zeros: list[float,int]
            Values to use as reference (zero value) to compare with

        Raises:
        -------
        raise: ValueError
            If values and zeros don't have the same size

        Returns:
        --------
        return: dict[int,list[int]]
            Values grouped with their indexes sorted from lower to higher
            group[index{int}][0]:   {int}   # index from list of values that start the group
            group[index{int}][1]:   {int}   # index from list of values that end the group
        """
        def group(df: pd.DataFrame) -> None:
            group = []
            for i in range(df.index.shape[0]):
                index = df.index[i]
                groups[index] = group
                group.append(index) if len(group) == 0 else None
                if (i == df.index.shape[0]-1) or ((df.index[i+1] - df.index[i]) != 1):
                    group.append(index)
                    group = []

        from model.tools.Map import Map
        if len(values) != len(zeros):
            raise ValueError(f"Values and Zeros must have the same size")
        groups = {}
        all_df = pd.DataFrame({Map.x: values, Map.neutral: zeros})
        above_df = all_df[all_df[Map.x] > all_df[Map.neutral]]
        bellow_df = all_df[all_df[Map.x] < all_df[Map.neutral]]
        equal_df = all_df[all_df[Map.x] == all_df[Map.neutral]]
        group(above_df)
        group(bellow_df)
        group(equal_df)
        groups = dict(sorted(groups.items(), key=lambda row: row[0]))
        return groups

    @staticmethod
    def exec_console(command: str) -> str:
        """
        To execute console command

        Parameters:
        -----------
        command: str
            Command to execute

        Returns:
        --------
        command: str
            Executed command's output
        """
        command = "git branch | egrep '^\*'"
        output = subprocess.check_output(command, shell=True).decode("utf-8")
        return output
