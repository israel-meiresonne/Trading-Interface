from model.structure.strategies.Flash.Flash import Flash
from model.structure.strategies.IcarusStalker.IcarusStalker import IcarusStalker
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class FlashStalker(IcarusStalker):
    CHILD_STRATEGY = Flash
    _STALKER_BOT_EMPTY_SLEEP_TIME = 5      # in second
    _STALKER_BOT_SLEEP_TIME = 5            # in second

    def _format_stalk(self, repport: Map) -> dict:
        # Repport
        key = self.CHILD_STRATEGY._can_buy_indicator.__name__
        indicator_datas = {
            f'{key}.can_buy_indicator': None,
            f'{key}.zero_ratio_bellow_limit': None,
            f'{key}.close_above_big_keltner': None,
            f'{key}.big_macd_historgram_positive': None,
            f'{key}.macd_historgram_positive': None,
            f'{key}.edited_psar_rising': None,
            f'{key}.not_bought_edited_psar': None,
            f'{key}.big_supertrend_rising': None,
            f'{key}.supertrend_rising': None,
            f'{key}.big_psar_rising': None,
            f'{key}.zero_ratio': None,
            f'{key}.n_zero': None,
            f'{key}.zero_n_period': None,
            f'{key}.zero_ratio_limit': None,
            f'{key}.edited_psar_starttime': None,
            f'{key}.edited_psar_endtime': None,
            f'{key}.closes[-1]': None,
            f'{key}.big_closes[-1]': None,
            f'{key}.l_volumes[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.edited_psar[-1]': None,
            f'{key}.big_supertrend[-1]': None,
            f'{key}.supertrend[-1]': None,
            f'{key}.big_psar[-1]': None
        }
        # Repport
        key = self.CHILD_STRATEGY.can_buy.__name__
        child_datas = {
            f'{key}.indicator': None,
            **indicator_datas
        }
        # Repport
        key = self._eligible.__name__
        canvas = {
            f'{key}.child_time': None,
            f'{key}.pair': None,
            f'{key}.eligible': None,
            f'{key}.child_ok': None,
            f'{key}.child_period': None,
            **child_datas
        }
        content = {key: repport.get(key) for key in canvas}
        return content

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        pair = Pair('?/json')
        instance = FlashStalker(Map({
            Map.pair: pair,
            Map.maximum: None,
            Map.capital: Price(1, pair.get_right()),
            Map.rate: 1,
            Map.strategy: 'FlashStalker',
            Map.period: 0,
            Map.param: {
                Map.maximum: None,
                Map.capital: 0,
                Map.rate: 1,
                Map.period: 0
            }
        }))
        exec(MyJson.get_executable())
        return instance
