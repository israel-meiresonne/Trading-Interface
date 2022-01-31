from typing import Union
from model.tools.Asset import Asset
from model.tools.MyJson import MyJson


class Pair(MyJson):
    SEPARATOR = "/"
    UNDERSCORE = '_'
    LEFT = '$left'
    RIGHT = '$right'
    FORMAT_MERGED = LEFT + RIGHT
    FORMAT_UNDERSCORE = LEFT + UNDERSCORE + RIGHT
    FORMAT_SLASH = LEFT + SEPARATOR + RIGHT

    def __init__(self, *agrs):
        nb = len(agrs)
        if nb == 1:
            self.__constructor1(agrs[0])
        elif nb == 2:
            self.__constructor2(agrs[0], agrs[1])
        else:
            raise ValueError(f"This number of param '{nb}' is not supported")

    def __constructor1(self, prsbl: str):
        """
        Constructor\n
        :param prsbl: couple of Asset symbol, i.e.: "BTC/USDT"
        """
        prs = prsbl.split(self.SEPARATOR)
        self.__left = Asset(prs[0])
        self.__right = Asset(prs[1])

    def __constructor2(self, left: Union[str, Asset], right: Union[str, Asset]):
        """
        Constructor
        :param lsbl: symbol of the left Asset
        :param rsbl: symbol of the right Asset
        """
        self.__left = left if isinstance(left, Asset) else Asset(left)
        self.__right = right if isinstance(right, Asset) else Asset(right)

    def get_left(self) -> Asset:
        return self.__left

    def get_right(self) -> Asset:
        return self.__right

    def get_merged_symbols(self) -> str:
        return self.get_left().get_symbol() + self.get_right().get_symbol()
    
    def format(self, format: str = FORMAT_MERGED) -> str:
        """
        To format Pair into a string in the given format

        Parameters
        ----------
        format: str
            The format

        Returns
        -------
            Pair formatted into given format
        """
        return format.replace(Pair.LEFT, self.get_left().get_symbol()).replace(Pair.RIGHT, self.get_right().get_symbol())

    def are_same(self, second: 'Pair') -> None:
        if not isinstance(second, Pair):
            raise ValueError(f"Second pair must be instance of Pair(second='{second}')")
        if self != second:
            raise ValueError(f"Pair are not the same(self='{self}', second='{second}')")

    @staticmethod
    def _get_separator() -> str:
        return Pair.SEPARATOR

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Pair('@json/@json')
        exec(MyJson.get_executable())
        return instance

    def __eq__(self, other):
        return self.get_left() == other.get_left() and \
               self.get_right() == other.get_right()

    def __str__(self) -> str:
        return self.get_left().get_symbol() + self.SEPARATOR + self.get_right().get_symbol()

    def __repr__(self) -> str:
        return self.__str__()
