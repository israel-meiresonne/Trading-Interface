from model.structure.Broker import Broker


class Binance(Broker):
    def __init__(self, cfs: dict):
        pass

    @staticmethod
    def list_paires() -> list:
        prs = [
            "BTC/USDT",
            "BTC/BNB",
            "ETH/USDT",
            "ETH/BNB",
            "EGLD/USDT"
        ]
        return prs



