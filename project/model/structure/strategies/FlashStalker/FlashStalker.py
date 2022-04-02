from model.structure.strategies.Flash.Flash import Flash
from model.structure.strategies.IcarusStalker.IcarusStalker import IcarusStalker
from model.tools.Map import Map


class FlashStalker(IcarusStalker):
    CHILD_STRATEGY = Flash

    def _format_stalk(self, repport: Map) -> dict:
        # Repport
        key = self.CHILD_STRATEGY._can_buy_indicator.__name__
        indicator_datas = {
            f'{key}.can_buy_indicator': None,
            f'{key}.zero_ratio_bellow_limit': None,
            f'{key}.close_above_big_keltner': None,
            f'{key}.macd_historgram_positive': None,
            f'{key}.big_macd_historgram_positive': None,
            f'{key}.big_supertrend_rising': None,
            f'{key}.edited_psar_rising': None,
            f'{key}.not_bought_edited_psar': None,
            f'{key}.zero_ratio': None,
            f'{key}.n_zero': None,
            f'{key}.zero_n_period': None,
            f'{key}.zero_ratio_limit': None,
            f'{key}.edited_psar_starttime': None,
            f'{key}.edited_psar_endtime': None,
            f'{key}.closes[-1]': None,
            f'{key}.l_volumes[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.edited_psar[-1]': None,
            f'{key}.big_supertrend[-1]': None
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
