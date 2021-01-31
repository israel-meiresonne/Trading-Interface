from model.structure.Strategy import Strategy
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order


class MinMax(Strategy):
    def __init__(self):
        pass

    def get_order(self, mkpc: MarketPrice) -> Order:
        return Order()
