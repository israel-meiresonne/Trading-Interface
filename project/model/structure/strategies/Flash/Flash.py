from typing import Tuple

from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice


class Flash(Icarus):
    KELTNER_LARGE_MULTIPLE_BUY = 2.5
    KELTNER_SMALL_MULTIPLE_BUY = 1

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
        def is_close_above_keltner(vars_map: Map) -> bool:
            big_marketprice.reset_collections()
            mult = cls.KELTNER_LARGE_MULTIPLE_BUY
            keltner = big_marketprice.get_keltnerchannel(multiple=mult)
            keltner_high = list(keltner.get(Map.high))
            keltner_high.reverse()
            # Check
            close_above_keltner = closes[-1] > keltner_high[-1]
            # Put
            vars_map.put(close_above_keltner, 'close_above_keltner')
            vars_map.put(keltner_high, f'big_2.5_keltner_high')
            return close_above_keltner

        def is_prev_high_bellow_keltner(vars_map: Map) -> bool:
            mult = cls.KELTNER_SMALL_MULTIPLE_BUY
            highs = list(big_marketprice.get_highs())
            highs.reverse()
            keltner = big_marketprice.get_keltnerchannel(multiple=mult)
            keltner = big_marketprice.get_keltnerchannel()
            keltner_high = list(keltner.get(Map.high))
            keltner_high.reverse()
            # Check
            prev_high_bellow_keltner = highs[-2] > keltner_high[-2]
            # Put
            vars_map.put(prev_high_bellow_keltner, 'prev_high_bellow_keltner')
            vars_map.put(keltner_high, f'big_1_keltner_high')
            return prev_high_bellow_keltner

        def is_macd_historgram_positive(vars_map: Map, marketprice: MarketPrice, repport: bool) -> None:
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
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
        can_buy_indicator = is_close_above_keltner(vars_map) and is_prev_high_bellow_keltner(vars_map) \
            and is_big_macd_historgram_positive(vars_map) and is_macd_historgram_positive(vars_map,  child_marketprice, repport=True)
        # Repport
        ema = vars_map.get(Map.ema)
        highs = vars_map.get(Map.high)
        keltner_high2_5 = vars_map.get('big_2.5_keltner_high')
        keltner_high1_0 = vars_map.get('big_2.big_1_keltner_high')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.close_above_keltner': vars_map.get('close_above_keltner'),
            f'{key}.prev_high_bellow_keltner': vars_map.get('prev_high_bellow_keltner'),
            f'{key}.macd_historgram_positive': vars_map.get('macd_historgram_positive'),
            f'{key}.big_macd_historgram_positive': vars_map.get('big_macd_historgram_positive'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.big_2.5_keltner_high[-1]': keltner_high2_5[-1] if keltner_high2_5 is not None else None,
            f'{key}.big_1_keltner_high[-1]': keltner_high1_0[-1] if keltner_high1_0 is not None else None,
        }
        return can_buy_indicator, repport
