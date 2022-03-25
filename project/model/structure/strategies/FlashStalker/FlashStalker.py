from model.structure.strategies.IcarusStalker.IcarusStalker import IcarusStalker
from model.tools.Map import Map


class FlashStalker(IcarusStalker):
    def _format_stalk(self, repport: Map) -> dict:
        # Repport
        key = self.CHILD_STRATEGY._can_buy_indicator.__name__
        indicator_datas = {
            f'{key}.can_buy_indicator': None,
            f'{key}.close_above_big_ema': None,
            f'{key}.big_prev_high_bellow_ema': None,
            f'{key}.big_keltner_bellow_ema': None,
            f'{key}.big_prev_close_bellow_keltner': None,
            f'{key}.macd_historgram_positive': None,
            f'{key}.big_macd_historgram_positive': None,
            f'{key}.closes[-1]': None,
            f'{key}.high[-1]': None,
            f'{key}.ema[-1]': None,
            f'{key}.keltner_high[-1]': None
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
