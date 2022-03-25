from typing import Tuple

from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice


class Flash(Icarus):
    pass

    @classmethod
    def _can_sell_indicator(cls, marketprice: MarketPrice) ->  bool:
        def is_tangent_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_dropping = macd[-1] <= macd[-2]
            return tangent_macd_dropping

        vars_map = Map()
        can_sell = is_tangent_macd_dropping(vars_map)
        return can_sell

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice) -> Tuple[bool, dict]:
        def is_big_keltner_bellow_ema(vars_map: Map) -> bool:
            ema = list(big_marketprice.get_ema(n_period=cls.EMA_N_PERIOD))
            ema.reverse()
            keltner = big_marketprice.get_keltnerchannel()
            keltner_high = list(keltner.get(Map.high))
            keltner_high.reverse()
            # Check
            big_keltner_bellow_ema = keltner_high[-1] < ema[-1]
            # Put
            vars_map.put(big_keltner_bellow_ema, 'big_keltner_bellow_ema')
            vars_map.put(ema, Map.ema)
            vars_map.put(keltner_high, 'keltner_high')
            return big_keltner_bellow_ema

        def is_big_prev_close_bellow_keltner(vars_map: Map) -> bool:
            closes = list(big_marketprice.get_closes())
            closes.reverse()
            keltner = big_marketprice.get_keltnerchannel()
            keltner_high = list(keltner.get(Map.high))
            keltner_high.reverse()
            # Check
            big_prev_close_bellow_keltner = closes[-2] < keltner_high[-2]
            # Put
            vars_map.put(big_prev_close_bellow_keltner, 'big_prev_close_bellow_keltner')
            vars_map.put(keltner_high, 'keltner_high')
            return big_prev_close_bellow_keltner

        def is_big_prev_high_bellow_ema(vars_map: Map) -> None:
            highs = list(big_marketprice.get_highs())
            highs.reverse()
            ema = list(big_marketprice.get_ema(n_period=cls.EMA_N_PERIOD))
            ema.reverse()
            # Check
            big_prev_high_bellow_ema = highs[-2] < ema[-2]
            # Put
            vars_map.put(big_prev_high_bellow_ema, 'big_prev_high_bellow_ema')
            vars_map.put(highs, Map.high)
            vars_map.put(ema, Map.ema)
            return big_prev_high_bellow_ema

        def is_close_above_big_ema(vars_map: Map) -> None:
            ema = list(big_marketprice.get_ema(n_period=cls.EMA_N_PERIOD))
            ema.reverse()
            # Check
            close_above_big_ema = closes[-1] > ema[-1]
            # Put
            vars_map.put(close_above_big_ema, 'close_above_big_ema')
            vars_map.put(ema, Map.ema)
            return close_above_big_ema

        def is_macd_historgram_positive(vars_map: Map, marketprice: MarketPrice, repport: bool) -> None:
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            period = marketprice.get_period_time()
            macd_historgram_positive = histogram[-1] > 0
            # Put
            vars_map.put(macd_historgram_positive, 'macd_historgram_positive') if repport else None
            return macd_historgram_positive

        def is_big_macd_historgram_positive(vars_map: Map) -> None:
            # Check
            big_macd_historgram_positive = is_macd_historgram_positive(vars_map, big_marketprice, repport=False)
            # Put
            vars_map.put(big_macd_historgram_positive, 'big_macd_historgram_positive')
            return big_macd_historgram_positive

        vars_map = Map()
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        # Check
        can_buy_indicator = is_close_above_big_ema(vars_map) and is_big_prev_high_bellow_ema(vars_map) \
            and is_big_keltner_bellow_ema(vars_map) and is_big_prev_close_bellow_keltner(vars_map) \
                and is_macd_historgram_positive(vars_map, child_marketprice, repport=True) \
                    and is_big_macd_historgram_positive(vars_map)
        # Repport
        ema = vars_map.get(Map.ema)
        highs = vars_map.get(Map.high)
        keltner_high = vars_map.get('keltner_high')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.close_above_big_ema': vars_map.get('close_above_big_ema'),
            f'{key}.big_prev_high_bellow_ema': vars_map.get('big_prev_high_bellow_ema'),
            f'{key}.big_keltner_bellow_ema': vars_map.get('big_keltner_bellow_ema'),
            f'{key}.big_prev_close_bellow_keltner': vars_map.get('big_prev_close_bellow_keltner'),
            f'{key}.macd_historgram_positive': vars_map.get('macd_historgram_positive'),
            f'{key}.big_macd_historgram_positive': vars_map.get('big_macd_historgram_positive'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.high[-1]': highs[-1] if highs is not None else None,
            f'{key}.ema[-1]': ema[-1] if ema is not None else None,
            f'{key}.keltner_high[-1]': keltner_high[-1] if keltner_high is not None else None
        }
        return can_buy_indicator, repport
