from model.tools.Currency import Currency


class Pair:
    SEPARATOR = "/"

    def __init__(self, prcd: str):
        """
        Constructor\n
        :param prcd: couple of Currency code, i.e.: "BTC/USDT"
        """
        prcd = prcd.lower()
        prs = prcd.split(self.SEPARATOR)
        self.to_buy = Currency(prs[0])
        self.to_sell = Currency(prs[1])

    def __int__(self, bcd: str, scd: str):
        """
        Constructor
        :param bcd: code of the Currency to buy
        :param scd: code of the Currency to sell
        :return: Pair
        """
        self.to_buy = Currency(bcd)
        self.to_sell = Currency(scd)
