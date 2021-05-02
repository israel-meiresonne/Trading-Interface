from model.tools.Asset import Asset


class Price:
    def __init__(self, value: [int, float], symbol: str):
        self.__value = round(float(value), 8)
        self.__asset = Asset(symbol)

    def _set_value(self, value: float) -> None:
        self.__value = value

    def get_value(self) -> float:
        return self.__value

    def get_asset(self) -> Asset:
        return self.__asset

    def __add__(self, other):
        if not isinstance(other, Price):
            raise ValueError(f"Price can only be add with an other Price, instead: '{type(other)}'.")
        if self.get_asset() != other.get_asset():
            raise ValueError(f"Price must have the same symbol to be add, "
                             f"instead: '{self.get_asset()}' != '{other.get_asset()}'")
        new_val = self.get_value() + other.get_value()
        return Price(new_val, self.get_asset().get_symbol())

    def __sub__(self, other):
        if not isinstance(other, Price):
            raise ValueError(f"Price can only be subtract with an other Price, instead: '{type(other)}'.")
        if self.get_asset() != other.get_asset():
            raise ValueError(f"Price must have the same symbol to be subtract, "
                             f"instead: '{self.get_asset()}' != '{other.get_asset()}'")
        new_val = self.get_value() - other.get_value()
        return Price(new_val, self.get_asset().get_symbol())

    def __mul__(self, other: [int, float]) -> [int, float]:
        return self.get_value() * other.get_value() if isinstance(other, Price) else self.get_value() * other

    def __rmul__(self, other: [int, float]) -> [int, float]:
        return self * other

    def __truediv__(self, other: [int, float]) -> [int, float]:
        return self.get_value() / other.get_value() if isinstance(other, Price) else self.get_value() / other

    def __rtruediv__(self, other: [int, float]) -> [int, float]:
        return other.get_value() / self.get_value() if isinstance(other, Price) else other / self.get_value()

    def __neg__(self):
        return Price(-self.get_value(), self.get_asset().get_symbol())

    def __eq__(self, other):
        return self.get_value() == other.get_value() and \
               self.get_asset() == other.get_asset()

    def __str__(self) -> str:
        return f'{self.get_asset()} {self.get_value()}'.upper()
