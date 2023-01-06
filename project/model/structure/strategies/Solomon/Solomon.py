import time
from typing import List

from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair


class Solomon(Strategy):
    PREFIX_ID =         'solomon_'
    KELTER_SUPPORT =    None
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_5MIN,
        Broker.PERIOD_15MIN
        ]

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

    def trade(self) -> int:
        pass

    # ••• TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

    @classmethod
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float]:
        TRIGGE_KELTNER = 2.5/100
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_15min = Broker.PERIOD_15MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        indexes = marketprice_1min_pd.index
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        can_buy = cls.is_keltner_roi_above_trigger(vars_map, broker, pair, period_1min, marketprices, TRIGGE_KELTNER) \
            and cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_psar_rising(vars_map, broker, pair, period_15min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_15min, marketprices)
        report = {
            f'can_buy':                                                 can_buy,
            f'keltner_roi_above_trigger_{period_strs[period_1min]}':    vars_map.get(f'keltner_roi_above_trigger_{period_strs[period_1min]}'),
            f'psar_rising_{period_strs[period_5min]}':                  vars_map.get(f'psar_rising_{period_strs[period_5min]}'),
            f'psar_rising_{period_strs[period_15min]}':                 vars_map.get(f'psar_rising_{period_strs[period_15min]}'),
            f'supertrend_rising_{period_strs[period_5min]}':            vars_map.get(f'supertrend_rising_{period_strs[period_5min]}'),
            f'supertrend_rising_{period_strs[period_15min]}':           vars_map.get(f'supertrend_rising_{period_strs[period_15min]}'),
            f'TRIGGE_KELTNER':                                          TRIGGE_KELTNER,
            f'low_{period_strs[period_1min]}[-1]':                      marketprice_1min_pd.loc[indexes[-1], Map.low],
            f'low_{period_strs[period_1min]}[-2]':                      marketprice_1min_pd.loc[indexes[-2], Map.low],
            f'close_{period_strs[period_1min]}[-1]':                    marketprice_1min_pd.loc[indexes[-1], Map.close],
            f'close_{period_strs[period_1min]}[-2]':                    marketprice_1min_pd.loc[indexes[-2], Map.close],
            f'high_{period_strs[period_1min]}[-1]':                     marketprice_1min_pd.loc[indexes[-1], Map.high],
            f'high_{period_strs[period_1min]}[-2]':                     marketprice_1min_pd.loc[indexes[-2], Map.high],
            f'keltner_roi_{period_strs[period_1min]}':                  vars_map.get(f'keltner_roi_{period_strs[period_1min]}'),
            f'keltner_low_{period_strs[period_1min]}[-1]':              vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]'),
            f'keltner_low_{period_strs[period_1min]}[-2]':              vars_map.get(f'keltner_low_{period_strs[period_1min]}[-2]'),
            f'keltner_middle_{period_strs[period_1min]}[-1]':           vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]'),
            f'keltner_middle_{period_strs[period_1min]}[-2]':           vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-2]'),
            f'keltner_high_{period_strs[period_1min]}[-1]':             vars_map.get(f'keltner_high_{period_strs[period_1min]}[-1]'),
            f'keltner_high_{period_strs[period_1min]}[-2]':             vars_map.get(f'keltner_high_{period_strs[period_1min]}[-2]'),
            f'psar_{period_strs[period_5min]}[-1]':                     vars_map.get(f'psar_{period_strs[period_5min]}[-1]'),
            f'psar_{period_strs[period_5min]}[-2]':                     vars_map.get(f'psar_{period_strs[period_5min]}[-2]'),
            f'psar_{period_strs[period_15min]}[-1]':                    vars_map.get(f'psar_{period_strs[period_15min]}[-1]'),
            f'psar_{period_strs[period_15min]}[-2]':                    vars_map.get(f'psar_{period_strs[period_15min]}[-2]'),
            f'supertrend_{period_strs[period_5min]}[-1]':               vars_map.get(f'supertrend_{period_strs[period_5min]}[-1]'),
            f'supertrend_{period_strs[period_5min]}[-2]':               vars_map.get(f'supertrend_{period_strs[period_5min]}[-2]'),
            f'supertrend_{period_strs[period_15min]}[-1]':              vars_map.get(f'supertrend_{period_strs[period_15min]}[-1]'),
            f'supertrend_{period_strs[period_15min]}[-2]':              vars_map.get(f'supertrend_{period_strs[period_15min]}[-2]')
        }
        limit = vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]')
        return can_buy, report, limit

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float]:
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_15min = Broker.PERIOD_15MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        indexes = marketprice_1min_pd.index
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        cls.is_keltner_roi_above_trigger(vars_map, broker, pair, period_1min, marketprices, 0)
        can_sell = (not cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices)) \
            or (not cls.is_psar_rising(vars_map, broker, pair, period_15min, marketprices)) \
            or (not cls.is_supertrend_rising(vars_map, broker, pair, period_5min, marketprices)) \
            or (not cls.is_supertrend_rising(vars_map, broker, pair, period_15min, marketprices))
        report = {
            'can_sell':                                         can_sell,
            f'psar_rising_{period_strs[period_5min]}':          vars_map.get(f'psar_rising_{period_strs[period_5min]}'),
            f'psar_rising_{period_strs[period_15min]}':         vars_map.get(f'psar_rising_{period_strs[period_15min]}'),
            f'supertrend_rising_{period_strs[period_5min]}':    vars_map.get(f'supertrend_rising_{period_strs[period_5min]}'),
            f'supertrend_rising_{period_strs[period_15min]}':   vars_map.get(f'supertrend_rising_{period_strs[period_15min]}'),
            f'low_{period_strs[period_1min]}[-1]':              marketprice_1min_pd.loc[indexes[-1], Map.low],
            f'low_{period_strs[period_1min]}[-2]':              marketprice_1min_pd.loc[indexes[-2], Map.low],
            f'close_{period_strs[period_1min]}[-1]':            marketprice_1min_pd.loc[indexes[-1], Map.close],
            f'close_{period_strs[period_1min]}[-2]':            marketprice_1min_pd.loc[indexes[-2], Map.close],
            f'high_{period_strs[period_1min]}[-1]':             marketprice_1min_pd.loc[indexes[-1], Map.high],
            f'high_{period_strs[period_1min]}[-2]':             marketprice_1min_pd.loc[indexes[-2], Map.high],
            f'keltner_low_{period_strs[period_1min]}[-1]':      vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]'),
            f'keltner_low_{period_strs[period_1min]}[-2]':      vars_map.get(f'keltner_low_{period_strs[period_1min]}[-2]'),
            f'keltner_middle_{period_strs[period_1min]}[-1]':   vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]'),
            f'keltner_middle_{period_strs[period_1min]}[-2]':   vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-2]'),
            f'keltner_high_{period_strs[period_1min]}[-1]':     vars_map.get(f'keltner_high_{period_strs[period_1min]}[-1]'),
            f'keltner_high_{period_strs[period_1min]}[-2]':     vars_map.get(f'keltner_high_{period_strs[period_1min]}[-2]'),
            f'psar_{period_strs[period_5min]}[-1]':             vars_map.get(f'psar_{period_strs[period_5min]}[-1]'),
            f'psar_{period_strs[period_5min]}[-2]':             vars_map.get(f'psar_{period_strs[period_5min]}[-2]'),
            f'psar_{period_strs[period_15min]}[-1]':            vars_map.get(f'psar_{period_strs[period_15min]}[-1]'),
            f'psar_{period_strs[period_15min]}[-2]':            vars_map.get(f'psar_{period_strs[period_15min]}[-2]'),
            f'supertrend_{period_strs[period_5min]}[-1]':       vars_map.get(f'supertrend_{period_strs[period_5min]}[-1]'),
            f'supertrend_{period_strs[period_5min]}[-2]':       vars_map.get(f'supertrend_{period_strs[period_5min]}[-2]'),
            f'supertrend_{period_strs[period_15min]}[-1]':      vars_map.get(f'supertrend_{period_strs[period_15min]}[-1]'),
            f'supertrend_{period_strs[period_15min]}[-2]':      vars_map.get(f'supertrend_{period_strs[period_15min]}[-2]')
        }
        limit = vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]')
        return can_sell, report, limit

    @classmethod
    def is_psar_rising(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        closes = list(marketprice.get_closes())
        closes.reverse()
        psars = list(marketprice.get_psar())
        psars.reverse()
        is_rising = MarketPrice.get_psar_trend(closes, psars, -1) == MarketPrice.PSAR_RISING
        vars_map.put(is_rising,     f'psar_rising_{period_str}')
        vars_map.put(closes[-1],    f'close_{period_str}[-1]')
        vars_map.put(closes[-2],    f'close_{period_str}[-2]')
        vars_map.put(psars[-1],     f'psar_{period_str}[-1]')
        vars_map.put(psars[-2],     f'psar_{period_str}[-2]')
        return is_rising

    @classmethod
    def is_supertrend_rising(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        closes = list(marketprice.get_closes())
        closes.reverse()
        supertrends = list(marketprice.get_super_trend())
        supertrends.reverse()
        is_rising = MarketPrice.get_super_trend_trend(closes, supertrends, -1) == MarketPrice.SUPERTREND_RISING
        vars_map.put(is_rising,         f'supertrend_rising_{period_str}')
        vars_map.put(closes[-1],        f'close_{period_str}[-1]')
        vars_map.put(closes[-2],        f'close_{period_str}[-2]')
        vars_map.put(supertrends[-1],   f'supertrend_{period_str}[-1]')
        vars_map.put(supertrends[-2],   f'supertrend_{period_str}[-2]')
        return is_rising

    @classmethod
    def is_keltner_roi_above_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, trigge_keltner: float) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        keltner_map = marketprice.get_keltnerchannel(multiple=1)
        keltner_low = list(keltner_map.get(Map.low))
        keltner_low.reverse()
        keltner_middle = list(keltner_map.get(Map.middle))
        keltner_middle.reverse()
        keltner_high = list(keltner_map.get(Map.high))
        keltner_high.reverse()
        # Check
        keltner_roi = _MF.progress_rate(keltner_high[-1], keltner_low[-1])
        keltner_roi_above_trigger = keltner_roi >= trigge_keltner
        # Put
        vars_map.put(keltner_roi_above_trigger, f'keltner_roi_above_trigger_{period_str}')
        vars_map.put(keltner_roi,               f'keltner_roi_{period_str}')
        vars_map.put(keltner_low[-1],           f'keltner_low_{period_str}[-1]')
        vars_map.put(keltner_low[-2],           f'keltner_low_{period_str}[-2]')
        vars_map.put(keltner_middle[-1],        f'keltner_middle_{period_str}[-1]')
        vars_map.put(keltner_middle[-2],        f'keltner_middle_{period_str}[-2]')
        vars_map.put(keltner_high[-1],          f'keltner_high_{period_str}[-1]')
        vars_map.put(keltner_high[-2],          f'keltner_high_{period_str}[-2]')
        return keltner_roi_above_trigger

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trade: dict, buy_conditions: list, sell_conditions: list) -> dict:
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            can_buy, buy_condition, buy_limit = cls.can_buy(broker, pair, marketprices)
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_LIMIT, limit=buy_limit)
            elif (trade is not None) and (not can_buy):
                cls._backtest_update_trade(trade, Map.buy, Order.STATUS_CANCELED)
                trade = None
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            can_sell, sell_condition, sell_limit = cls.can_sell(broker, pair, marketprices)
            sell_condition = cls._backtest_condition_add_prefix(sell_condition, pair, marketprice)
            sell_conditions.append(sell_condition)
            cls._backtest_update_trade(trade, Map.sell, Order.STATUS_CANCELED) if trade[Map.sell] is not None else None
            cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.mean) \
                if can_sell else cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_LIMIT, limit=sell_limit)
        return trade

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Solomon.__new__(Solomon)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————

