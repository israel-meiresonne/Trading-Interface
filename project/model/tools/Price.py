from model.tools.Asset import Asset


class Price:
    def __init__(self, val: float, sbl: str):
        self.__value = val
        self.__asset = Asset(sbl)

    def get_value(self) -> float:
        return self.__value

    def get_asset(self) -> Asset:
        return self.__asset