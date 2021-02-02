from model.tools.Asset import Asset


class Pair:
    _SEPARATOR = "/"

    def __init__(self, *agrs):
        nb = len(agrs)
        if nb == 1:
            self.__constructor1(agrs[0])
        elif nb == 2:
            self.__constructor2(agrs[0], agrs[1])

    def __constructor1(self, prcd: str):
        """
        Constructor\n
        :param prcd: couple of Asset code, i.e.: "BTC/USDT"
        """
        prs = prcd.split(self._SEPARATOR)
        self.__to_buy = Asset(prs[0])
        self.__to_sell = Asset(prs[1])

    def __constructor2(self, bcd: str, scd: str):
        """
        Constructor
        :param bcd: code of the Asset to buy
        :param scd: code of the Asset to sell
        """
        self.__to_buy = Asset(bcd)
        self.__to_sell = Asset(scd)

    def get_to_buy(self) -> Asset:
        return self.__to_buy

    def get_to_sell(self) -> Asset:
        return self.__to_sell
