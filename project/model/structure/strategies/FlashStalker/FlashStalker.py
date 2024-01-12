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
            f'{key}.close_above_keltner': None,
            f'{key}.close_above_big_keltner': None,
            f'{key}.prev_high_bellow_keltner': None,
            f'{key}.macd_historgram_positive': None,
            f'{key}.big_macd_historgram_positive': None,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.not_bought_in_macd': None,
            f'{key}.macd_starttime': None,
            f'{key}.macd_endtime': None,
            f'{key}.closes[-1]': None,
            f'{key}.big_highs[-1]': None,
            f'{key}.big_highs[-2]': None,
            f'{key}.keltner_high2_5[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.big_1_keltner_high[-1]': None,
            f'{key}.big_1_keltner_high[-2]': None
=======
            f'{key}.big_keltner_above_big_ema': None,
            f'{key}.closes[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.big_keltner_middle[-1]': None,
            f'{key}.big_ema[-1]': None
>>>>>>> Flash-v2.6.1
=======
            f'{key}.keltner_above_ema': None,
            f'{key}.closes[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.keltner_middle[-1]': None,
            f'{key}.ema[-1]': None
>>>>>>> Flash-v2.6.2
=======
            f'{key}.rsi_rising': None,
            f'{key}.closes[-1]': None,
            f'{key}.big_keltner_high2_5[-1]': None,
            f'{key}.rsi[-1]': None
>>>>>>> Flash-v2.6.6
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
