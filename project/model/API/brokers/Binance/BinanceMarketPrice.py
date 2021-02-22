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

    def _get_closes(self) -> tuple:
        return self._extract_index(self.COLLECTION_CLOSES, 4)

    def get_close(self, prd: int) -> Decimal:
        closes = self._get_closes()
        if prd >= len(closes):
            raise ValueError(f"This period '{prd}' don't exist in market's closes")
        return closes[prd]

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
