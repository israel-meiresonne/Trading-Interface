from model.structure.database.ModelFeature import ModelFeature as _MF


class RateLimit:
    def __init__(self, limit: int, interval: float):
        self.__limit = limit
        self.__interval = interval
        self.__weight = None
        self.__next_reset = None

    def get_limit(self) -> int:
        return self.__limit

    def get_interval(self) -> float:
        return self.__interval

    def _set_weight(self, weight: int):
        if not isinstance(weight, int):
            raise ValueError(f"The weight must be type int, instead '{weight}({type(weight)})'")
        self.__weight = weight

    def get_weight(self) -> int:
        next_reset = self.get_next_reset()
        if next_reset is None:
            self.__weight = None
        return self.__weight

    def update_weight(self, weight: int) -> None:
        """
        To update weight with a new value\n
        NOTE: useful to sync RateLimit with other System like API, etc...
        Parameters
        ----------
        weight: int
            The new weight
        """
        self._set_weight(weight)

    def get_remaining_weight(self) -> int:
        """
        To get remaining weight before to reach weight limit\n
        Returns
        -------
        remaining: int
            Remaining weight
        """
        weight = self.get_weight()
        limit = self.get_limit()
        remaining = limit - weight if weight is not None else limit
        return remaining

    def _set_next_reset(self) -> None:
        self.__next_reset = _MF.get_timestamp() + self.get_interval()

    def get_next_reset(self) -> int:
        next_reset = self.__next_reset
        unix_time = _MF.get_timestamp()
        if (next_reset is not None) and (unix_time > next_reset):
            self.__next_reset = None
        return self.__next_reset

    def get_remaining_time(self) -> int:
        """
        To get the remaining time till the next reset\n
        Returns
        -------
        wait_time: int
            The remaining time till the next reset
        """
        next_reset = self.get_next_reset()
        wait_time = None
        if next_reset is not None:
            unix_time = _MF.get_timestamp()
            wait_time = next_reset - unix_time
        return wait_time

    def add_weight(self, weight: int) -> int:
        """
        To add weight on existing one\n
        Parameters
        ----------
        weight: int
            The weight to add

        Returns
        -------
        new_weight: int
            The new total weight
        """
        actual_weight = self.get_weight()
        if actual_weight is None:
            self._set_weight(weight)
            self._set_next_reset()
        else:
            new_weight = actual_weight + weight
            self._set_weight(new_weight)
        return weight if actual_weight is None else new_weight
