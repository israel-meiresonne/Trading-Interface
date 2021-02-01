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
