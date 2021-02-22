from random import random

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.Broker import Broker
from model.tools.Map import Map
from model.tools.Order import Order


class Binance(Broker):
    def __init__(self, configs: Map):
        """
        Constructor\n
        :param configs: holds config params
                     cfgs[Map.api_pb]       => {str}
                     cfgs[Map.api_sk]       => {str}
                     cfgs[Map.test_mode]    => {bool}
        """
        super().__init__()
        ks = [Map.api_pb, Map.api_sk, Map.test_mode]
        rtn = self.keys_exist(ks, configs.get_map())
        if rtn is not None:
            raise IndexError(f"Property '{rtn}' is required")
        api_pb = configs.get(Map.api_pb)
        api_sk = configs.get(Map.api_sk)
        test_mode = configs.get(Map.test_mode)
        self.__api = BinanceAPI(api_pb, api_sk, test_mode)

    def __get_api(self) -> BinanceAPI:
        return self.__api

    def get_account_snapshot(self, bkr_rq: BinanceRequest) -> None:
        api = self.__get_api()
        rq = BinanceAPI.RQ_ACCOUNT_SNAP
        prms = bkr_rq.generate_request()
        rsp = api.request_api(rq, prms)
        bkr_rq.handle_response(rsp)

    def get_market_price(self, bnc_rq: BinanceRequest) -> None:
        api = self.__get_api()
        rq = BinanceAPI.RQ_KLINES
        prms = bnc_rq.generate_request()
        rsp = api.request_api(rq, prms)
        bnc_rq.handle_response(rsp)

    def execute(self, odrs: Map) -> None:
        api = self.__get_api()
        for _, odr in odrs.get_map().items():
            rq = odr.get_api_request()
            rq_prms = odr.generate_order()
            rq_rsp = api.request_api(rq, rq_prms)
            odr.handle_response(rq_rsp)

    def cancel(self, odr: Order) -> None:
        params = odr.generate_cancel_order()
        rq = BinanceAPI.RQ_CANCEL_ORDER
        api = self.__get_api()
        rsp = api.request_api(rq, params)
        odr.handle_response(rsp)

    def get_next_trade_time(self) -> int:
        return int(random() * 10)

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
