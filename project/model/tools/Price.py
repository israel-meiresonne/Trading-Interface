from decimal import Decimal, getcontext

from model.tools.Asset import Asset


class Price:
    def __init__(self, val: [int, float, Decimal], sbl: str):
        getcontext().prec = 8
        self.__value = Decimal(str(val)) * 1
        self.__asset = Asset(sbl)

    def get_value(self) -> Decimal:
        return self.__value

    def get_asset(self) -> Asset:
        return self.__asset

    def __eq__(self, other):
        return self.get_value() == other.get_value() and \
               self.get_asset() == other.get_asset()

    def __str__(self) -> str:
        return f'{self.get_asset()} {self.get_value()}'.upper()
