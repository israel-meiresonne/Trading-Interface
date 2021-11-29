from typing import List, Union

from model.tools.Asset import Asset
from model.tools.MyJson import MyJson


class Price(MyJson):
    _N_DECIMAL = 8

    def __init__(self, value: Union[int, float], asset: Union[str, Asset], n_decimal: int = None, cut_exceed: bool = False) -> None:
        self.__value = None
        self.__asset = None
        self._set_asset(asset)
        self._set_value(value, cut_exceed=cut_exceed) if n_decimal is None else self._set_value(value, n_decimal=n_decimal, cut_exceed=cut_exceed)

    def _set_value(self, value: float, n_decimal: int = _N_DECIMAL, cut_exceed: bool = True) -> None:
        rounded_value = round(float(value), n_decimal) if not cut_exceed else int(float(value) * 10**(n_decimal))/10**(n_decimal)
        self.__value = rounded_value

    def get_value(self) -> float:
        return self.__value
    
    def _set_asset(self, asset: Union[str, Asset]) -> None:
        if isinstance(asset, str):
            self.__asset = Asset(asset)
        elif isinstance(asset, Asset):
            self.__asset = asset
        else:
            raise ValueError(f"The asset '{asset}' must type 'str' or 'Asset', instead '{type(asset)}'")

    def get_asset(self) -> Asset:
        return self.__asset

    @staticmethod
    def sum(prices: List['Price']) -> 'Price':
        """
        To sum list of prices\n
        :param prices: List of Price
        :return: Price sum or None if list of Price is empty
        """
        price_sum = None
        if len(prices) > 0:
            price_sum = prices[0]
            for i in range(1, len(prices)):
                price = prices[i]
                price_sum += price
        return price_sum

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Price(0, '@json')
        exec(MyJson.get_executable())
        return instance

    def __add__(self, other) -> 'Price':
        if not isinstance(other, Price):
            raise ValueError(f"Price can only be add with an other Price, instead: '{type(other)}'.")
        if self.get_asset() != other.get_asset():
            raise ValueError(f"Price must have the same symbol to be add, "
                             f"instead: '{self.get_asset()}' != '{other.get_asset()}'")
        new_val = self.get_value() + other.get_value()
        return Price(new_val, self.get_asset().get_symbol())

    def __sub__(self, other) -> 'Price':
        if not isinstance(other, Price):
            raise ValueError(f"Price can only be subtract with an other Price, instead: '{type(other)}'.")
        if self.get_asset() != other.get_asset():
            raise ValueError(f"Price must have the same symbol to be subtract, "
                             f"instead: '{self.get_asset()}' != '{other.get_asset()}'")
        new_val = self.get_value() - other.get_value()
        return Price(new_val, self.get_asset().get_symbol())

    def __mul__(self, other: Union['Price', int, float]) -> Union[int, float]:
        return self.get_value() * other.get_value() if isinstance(other, Price) else self.get_value() * other

    def __rmul__(self, other: Union[int, float]) -> Union[int, float]:
        return self * other

    def __truediv__(self, other: Union['Price', int, float]) -> Union[int, float]:
        return self.get_value() / other.get_value() if isinstance(other, Price) else self.get_value() / other

    def __rtruediv__(self, other: Union['Price', int, float]) -> Union[int, float]:
        return other.get_value() / self.get_value() if isinstance(other, Price) else other / self.get_value()

    def __neg__(self) -> 'Price':
        return Price(-self.get_value(), self.get_asset().get_symbol())

    def __eq__(self, other) -> bool:
        return self.get_value() == other.get_value() and \
               self.get_asset() == other.get_asset()

    def __str__(self) -> str:
        return f'{self.get_asset()} {self.get_value()}'.upper()

    def __repr__(self) -> str:
        return self.__str__()
