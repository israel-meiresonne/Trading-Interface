import unittest
from model.structure.Bot import Bot


class TestBot(unittest.TestCase, Bot):
    def setUp(self) -> None:
        self.bkr = "Binance"
        self.stg = "MinMax"
        self.prsbl = "BTC/USDT"

    """
    def test_id_format_is_correct(self):
        bt_id = self._generate_id(self.bkr, self.stg, self.prsbl)
        exp_id = self.bkr.lower() + Bot.SEPARATOR + self.stg.lower() + Bot.SEPARATOR + self.prsbl.lower()
        self.assertEqual(bt_id, exp_id)
    """

    """
    def test_bot_properties_has_correct_type(self):
        self.assertEqual(self.bt._get_broker().__class__.__name__, Broker.retrieve(self.bkr, {}).__class__.__name__)
        self.assertEqual(self.bt._get_strategy().__class__.__name__, Strategy.generate_strategy(self.stg).__class__.__name__)
        self.assertEqual(self.bt._get_pair().__class__.__name__, Pair.__name__)
    """


if __name__ == '__main__':
    unittest.main(verbosity=2)
