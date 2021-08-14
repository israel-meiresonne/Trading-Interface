from random import random
from typing import List

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair


class Binance(Broker, MyJson):
    def __init__(self, configs: Map):
        """
        Constructor\n
        :param configs: holds config params
                     cfgs[Map.public]       => {str}
                     cfgs[Map.secret]       => {str}
                     cfgs[Map.test_mode]    => {bool}
        """
        super().__init__()
        ks = [Map.public, Map.secret, Map.test_mode]
        rtn = _MF.keys_exist(ks, configs.get_map())
        if rtn is not None:
            raise IndexError(f"Property '{rtn}' is required")
        self.__api_public_key = configs.get(Map.public)
        self.__api_secret_key = configs.get(Map.secret)
        self.__test_mode = configs.get(Map.test_mode)

    def get_api_public_key(self) -> str:
        return self.__api_public_key

    def get_api_secret_key(self) -> str:
        return self.__api_secret_key

    def get_api_keys(self) -> Map:
        return BinanceAPI.format_api_keys(self.get_api_public_key(), self.get_api_secret_key())

    def test_mode(self) -> bool:
        """
        To check if environment is in test mode\n
        Returns
        -------
        test_mode: bool
            True if environment is in test mode else False for real mode
        """
        return self.__test_mode

    def get_base_params(self) -> list:
        test_mode = self.test_mode()
        public_key = self.get_api_public_key()
        secret_key = self.get_api_secret_key()
        return [test_mode, public_key, secret_key]

    def request(self, bnc_rq: BinanceRequest) -> None:
        bases_params = self.get_base_params()
        rq = bnc_rq.get_endpoint()
        params = bnc_rq.generate_request()
        rsp = BinanceAPI.request_api(*bases_params, rq, params)
        bnc_rq.handle_response(rsp)

    def get_trade_fee(self, pair: Pair) -> Map:
        fee = BinanceAPI.get_trade_fee(pair)
        return Map(fee)

    def execute(self, order: Order) -> None:
        bases_params = self.get_base_params()
        rq = order.get_api_request()
        rq_params = order.generate_order()
        rq_rsp = BinanceAPI.request_api(*bases_params, rq, rq_params)
        order.handle_response(rq_rsp)

    def cancel(self, order: Order) -> None:
        bases_params = self.get_base_params()
        params = order.generate_cancel_order()
        rq = BinanceAPI.RQ_CANCEL_ORDER
        rsp = BinanceAPI.request_api(*bases_params, rq, params)
        order.handle_response(rsp)

    def add_streams(self, new_streams: List[str]) -> None:
        BinanceAPI.add_streams(new_streams) if len(new_streams) > 0 else None

    @staticmethod
    def generate_stream(params: Map) -> str:
        """
        To generate a Broker stream\n
        Parameters
        ----------
        params: Map
            Param to adjust following Broker's needs
            params[Map.pair]:   {Pair}
            params[Map.period]: {int}   # in second

        Returns
        -------
        stream: str
            Broker stream
        """
        rq = BinanceAPI.RQ_KLINES
        symbol = params.get(Map.pair).get_merged_symbols()
        period = params.get(Map.period)
        period_str = BinanceAPI.convert_interval(period)
        stream = BinanceAPI.generate_stream(rq, symbol, period_str)
        return stream

    @staticmethod
    def close() -> None:
        # self._get_api().close_socket()
        BinanceAPI.close_socket()

    def get_next_trade_time(self) -> int:
        return int(random() * 10)

    @staticmethod
    def get_pairs(match: List[str] = None, no_match: List[str] = None) -> List[str]:
        return BinanceAPI.get_pairs(match=match, no_match=no_match)

    @staticmethod
    def list_paires() -> list:
        prs = [
            '?/USDT',
            'BTC/USDT',
            'BNB/USDT',
            'EGLD/USDT',
            'COS/USDT',
            'DOGE/USDT',
            'ETC/USDT',
            'RLC/USDT',
            'UNFI/USDT'
        ]
        return prs

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Binance(Map({
            Map.public: '@json',
            Map.secret: '@json',
            Map.test_mode: None
        }))
        exec(MyJson.get_executable())
        return instance
