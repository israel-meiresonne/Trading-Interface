import unittest
from time import sleep

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.RateLimit import RateLimit


class TestRateLimit(unittest.TestCase, RateLimit):
    def setUp(self) -> None:
        self.limit1 = 100
        self.interval1 = 2
        self.rate_limit1 = RateLimit(self.limit1, self.interval1)

    @staticmethod
    def wait_reset(rate_limit: RateLimit) -> None:
        next_reset = rate_limit.get_next_reset()
        sleep_time = next_reset - _MF.get_timestamp()
        if sleep_time > 0:
            print(f"Sleep time: {sleep_time}sec.")
            sleep(sleep_time + 1)

    def test_whole_usages(self) -> None:
        weight = 20
        rate_limit = self.rate_limit1
        # No Weight
        self.assertIsNone(rate_limit.get_weight())
        self.assertIsNone(rate_limit.get_next_reset())
        # Update Weight when before to set next_reset
        rate_limit.update_weight(weight * 2)
        self.assertIsNone(rate_limit.get_weight())
        self.assertIsNone(rate_limit.get_next_reset())
        # Add Weight
        rate_limit.add_weight(weight)
        rate_limit.add_weight(int(weight / 2))
        exp1 = int(weight * 3/2)
        result1 = rate_limit.get_weight()
        self.assertEqual(exp1, result1)
        self.assertIsInstance(rate_limit.get_next_reset(), int)
        # Update Weight
        rate_limit.update_weight(weight * 3)
        exp2 = weight * 3
        result2 = rate_limit.get_weight()
        self.assertEqual(exp2, result2)
        self.assertIsInstance(rate_limit.get_next_reset(), int)
        # Weight reset
        TestRateLimit.wait_reset(rate_limit)
        self.assertIsNone(rate_limit.get_weight())
        self.assertIsNone(rate_limit.get_next_reset())
        # Update Weight when next_reset is reached
        rate_limit.update_weight(weight * 4)
        self.assertIsNone(rate_limit.get_weight())
        self.assertIsNone(rate_limit.get_next_reset())

    def test_get_remaining_weight(self) -> None:
        weight = 15
        limit = self.limit1
        rate_limit = self.rate_limit1
        # Before to add
        exp1 = limit
        result1 = rate_limit.get_remaining_weight()
        self.assertEqual(exp1, result1)
        # When added
        rate_limit.add_weight(weight * 3)
        exp2 = limit - weight * 3
        result2 = rate_limit.get_remaining_weight()
        self.assertEqual(exp2, result2)
        # Limit exceeded
        rate_limit.add_weight(weight * 10)
        with self.assertRaises(Exception):
            rate_limit.get_remaining_weight()
        # When Weight reset
        TestRateLimit.wait_reset(rate_limit)
        exp2 = limit
        result2 = rate_limit.get_remaining_weight()
        self.assertEqual(exp2, result2)

    def test_get_remaining_time(self) -> None:
        rate_limit = self.rate_limit1
        weight = 10
        # Before Add
        self.assertIsNone(rate_limit.get_remaining_time())
        # After add
        rate_limit.add_weight(weight)
        exp1 = self.interval1
        result1 = rate_limit.get_remaining_time()
        self.assertEqual(exp1, result1)
        # After reset
        self.wait_reset(rate_limit)
        self.assertIsNone(rate_limit.get_remaining_time())


if __name__ == '__main__':
    unittest.main()
