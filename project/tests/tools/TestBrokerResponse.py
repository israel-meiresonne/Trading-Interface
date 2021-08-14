import unittest

from requests import get as requests_get

from model.tools.BrokerResponse import BrokerResponse


class TestBrokerResponse(unittest.TestCase, BrokerResponse):
    def setUp(self) -> None:
        self.response = requests_get(url='http://ip-api.com/json/24.48.0.1')
        self.bkr_rsp = BrokerResponse(self.response)

    def test_json_encode_decode(self) -> None:
        original_obj = self.bkr_rsp
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)


if __name__ == '__main__':
    unittest.main()
