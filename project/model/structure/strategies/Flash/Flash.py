from typing import Tuple

from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.MarketPrice import MarketPrice


class Flash(Icarus):
    pass

    @classmethod
    def _can_sell_indicator(cls, marketprice: MarketPrice) ->  bool:
        pass

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice) -> Tuple[bool, dict]:
        pass
