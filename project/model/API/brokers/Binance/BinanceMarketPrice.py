from decimal import Decimal

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.MarketPrice import MarketPrice


class BinanceMarketPrice(MarketPrice):
    def __init__(self, mkt: list, prd_str: str):
        """
        Constructor\n
        :param mkt: the market prices.
        NOTE:   market prices are ordered from the older (i=0)
                to the newest (i=len()-1)
                So to facilitate the manipulation, market prices is reversed
                to have the newest prices in the top indexes and the older in
                the end
                    [
                      [
                        1499040000000,      // Open time
                        "0.01634790",       // Open
                        "0.80000000",       // High
                        "0.01575800",       // Low
                        "0.01577100",       // Close
                        "148976.11427815",  // Volume
                        1499644799999,      // Close time
                        "2434.19055334",    // Quote asset volume
                        308,                // Number of trades
                        "1756.87402397",    // Taker buy base asset volume
                        "28.46694368",      // Taker buy quote asset volume
                        "17928899.62484339" // Ignore.
                      ]
                    ]
        """
        prd = BinanceAPI.get_interval(prd_str)
        mkt.reverse()
        super().__init__(mkt, prd)

    def get_closes(self) -> tuple:
        k = self.COLLECTION_CLOSES
        closes = self._get_collection(k)
        if closes is None:
            idx = 4
            coll = self._extract_index(idx)
            closes = tuple(Decimal(v) for v in coll)
            self._set_collection(k, closes)
        return closes

    def get_close(self, prd=0) -> Decimal:
        closes = self.get_closes()
        if prd >= len(closes):
            raise ValueError(f"This period '{prd}' don't exist in market's closes")
        return closes[prd]

    def get_times(self) -> tuple:
        k = self.COLLECTION_TIMES
        times = self._get_collection(k)
        if times is None:
            idx = 0
            coll = self._extract_index(idx)
            times = tuple(int(v) for v in coll)
            self._set_collection(k, times)
        return times

    def get_time(self, prd=0) -> int:
        times = self.get_times()
        if prd >= len(times):
            raise IndexError(f"This period '{prd}' is out of time collection '{len(times)}'")
        return times[prd]

    '''
    def _extract_index(self, k: str, i: int) -> tuple:
        """
        To extract from each line of market price the given index\n
        :param k: access key to a supported collection
        :param i: the index to extract in each line
        :return: list of values extract of each line of market price
        """
        coll = self._get_collection(k)
        if coll is None:
            mkt = self.get_market()
            coll = tuple([Decimal(line[i]) for line in mkt])
            self._set_collection(k, coll)
        return coll
    '''

    def _extract_index(self, idx: int) -> list:
        """
        To extract from each line of market price the given index\n
        :param idx: the index to extract in each line
        :return: collection of values extracted from each line of market prices
        """
        mkt = self.get_market()
        coll = [line[idx] for line in mkt]
        return coll
