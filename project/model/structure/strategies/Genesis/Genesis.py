import time
from typing import List
from model.structure.Broker import Broker


from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair


class Genesis(Strategy):
    PREFIX_ID =             'genesis_'
    KELTER_SUPPORT =        None

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ••• STALK DOWN

    def _manage_stalk(self) -> None:
        while self.is_stalk_on():
            _MF.catch_exception(self._stalk_market, self.__class__.__name__) if not self.is_max_position_reached() else None
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _stalk_market(self) -> List[Pair]:
        pass

    # ••• STALK UP
    # ••• TRADE DOWN

    def _trade_inner(self) -> None:
        pass

    # ••• TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, buy_conditions: list, sell_conditions: list) -> dict:
        pass

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Genesis.__new__(Genesis)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
    