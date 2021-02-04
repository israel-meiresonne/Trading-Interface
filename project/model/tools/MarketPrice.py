class MarketPrice:
    def __init__(self, mk: [dict, list]):
        """
        Constructor\n
        :param mk: market prices
        """
        self.__market = mk

    def get_market(self) -> dict:
        return self.__market
