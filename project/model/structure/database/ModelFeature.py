from abc import abstractmethod
from time import time as time_time

from model.structure.database.ModelAccess import ModelAccess


class ModelFeature(ModelAccess):
    TIME_SEC = "time_sec"
    TIME_MILLISEC = "time_millisec"

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get_time_stamps(unit=TIME_SEC) -> int:
        """
        To get the timestamp in the given unit\n
        :param unit: a supported time unit
        :return: the timestamp in the given unit
        """
        if unit == ModelFeature.TIME_MILLISEC:
            ts = int(time_time() * 1000)
        elif unit == ModelFeature.TIME_SEC:
            ts = time_time()
        else:
            raise Exception(f"This time unit '{unit}' is not supported")
        return ts

    @staticmethod
    def keys_exist(ks: list, mp: dict) -> [None, str]:
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
    def clean(tab: [list, dict]) -> [list, dict]:
        t = type(tab)
        if t == list:
            return [v for v in tab if (v != '') and (v is not None)]
        elif t == dict:
            return {k: v for k, v in tab.items() if (v != '') and (v is not None)}
        else:
            raise ValueError(f"Can't clean this type '{t}'")
