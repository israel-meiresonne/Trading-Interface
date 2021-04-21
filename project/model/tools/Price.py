from model.tools.Asset import Asset


class Price:
    def __init__(self, val: [int, float], sbl: str):
        self.__value = round(val, 8)
        self.__asset = Asset(sbl)

    def get_value(self) -> float:
        return self.__value

    def get_asset(self) -> Asset:
        return self.__asset

    def __eq__(self, other):
        return self.get_value() == other.get_value() and \
               self.get_asset() == other.get_asset()

    def __str__(self) -> str:
        return f'{self.get_asset()} {self.get_value()}'.upper()
