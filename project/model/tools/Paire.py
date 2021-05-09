from model.tools.Asset import Asset


class Pair:
    _SEPARATOR = "/"

    def __init__(self, *agrs):
        nb = len(agrs)
        if nb == 1:
            self.__constructor1(agrs[0])
        elif nb == 2:
            self.__constructor2(agrs[0], agrs[1])

    def __constructor1(self, prsbl: str):
        """
        Constructor\n
        :param prsbl: couple of Asset symbol, i.e.: "BTC/USDT"
        """
        prs = prsbl.split(self._SEPARATOR)
        self.__left = Asset(prs[0])
        self.__right = Asset(prs[1])

    def __constructor2(self, lsbl: str, rsbl: str):
        """
        Constructor
        :param lsbl: symbol of the left Asset
        :param rsbl: symbol of the right Asset
        """
        self.__left = Asset(lsbl)
        self.__right = Asset(rsbl)

    @staticmethod
    def _get_separator() -> str:
        return Pair._SEPARATOR

    def get_left(self) -> Asset:
        return self.__left

    def get_right(self) -> Asset:
        return self.__right

    def get_merged_symbols(self) -> str:
        return self.get_left().get_symbol() + self.get_right().get_symbol()

    def __eq__(self, other):
        return self.get_left() == other.get_left() and \
               self.get_right() == other.get_right()

    def __str__(self) -> str:
        return self.get_left().get_symbol() + self._SEPARATOR + self.get_right().get_symbol()

    def __repr__(self) -> str:
        return self.__str__()
