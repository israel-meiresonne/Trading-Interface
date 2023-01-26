import time
from typing import Callable, List

import pandas as pd
from config.Config import Config

from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.Asset import Asset
from model.tools.FileManager import FileManager
from model.tools.HandTrade import HandTrade
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Solomon(Strategy):
    PREFIX_ID =         'solomon_'
    KELTER_SUPPORT =    None
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_5MIN,
        Broker.PERIOD_15MIN
        ]
    PSAR_1 = dict(step=.6, max_step=.6)

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ••• STALK DOWN

    def _manage_stalk(self) -> None:
        while self.is_stalk_on():
            _MF.catch_exception(self._stalk_market, self.__class__.__name__) if not self.is_max_position_reached() else None
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _stalk_market(self) -> List[Pair]:
        broker = self.get_broker()
        stalk_pairs = self._get_stalk_pairs()
        r_asset = self.get_wallet().get_initial().get_asset()
        period_1min = Broker.PERIOD_1MIN
        marketprices = Map()
        reports = []
        bought_pairs = []
        k_limit_price = Map.key(Map.limit, Map.price)
        loop_start_date = _MF.unix_to_date(_MF.get_timestamp())
        current_func = self._stalk_market.__name__
        # Stalk pairs
        for stalk_pair in stalk_pairs:
            turn_start_date = _MF.unix_to_date(_MF.get_timestamp())
            can_buy, report, limit_float, can_buy_keys = self.can_buy(broker, stalk_pair, marketprices)
            marketprice_1min = self._marketprice(broker, stalk_pair, period_1min, marketprices)
            report = self._new_row_condition(report, current_func, loop_start_date, turn_start_date, marketprice_1min, stalk_pair, can_buy, limit_float)
            reports.append(report)
        reports_df = pd.DataFrame(reports)
        if reports_df.shape[0] > 0:
            self._print_buy_sell_conditions(reports_df, self.can_buy)
            # Keys
            k_keltner_roi_1min = can_buy_keys[Map.key(Map.keltner, Map.roi)]
            # Buy positions
            can_buy_df = reports_df[reports_df[Map.condition] == True]
            if can_buy_df.shape[0] > 0:
                can_buy_sorted = can_buy_df.sort_values(by=[k_keltner_roi_1min], ascending=False)
                for i in can_buy_sorted.index:
                    buy_pair = reports_df.loc[i, Map.pair]
                    buy_limit_float = reports_df.loc[i, k_limit_price]
                    buy_limit = Price(buy_limit_float, r_asset)
                    self.buy(buy_pair, Order.TYPE_LIMIT, limit=buy_limit) if buy_pair.__str__() not in self.get_positions() else None
                    bought_pairs.append(buy_pair)
                    if self.is_max_position_reached():
                        break
        return bought_pairs

    @classmethod
    def _new_row_condition(cls, report: dict, current_func: str, loop_start_date: str, turn_start_date: str, marketprice_1min: MarketPrice, pair: Pair, can_buy_sell: bool, limit: float) -> dict:
        _MF.check_type(report, dict)
        _MF.check_type(current_func, str)
        _MF.check_type(loop_start_date, str)
        _MF.check_type(turn_start_date, str)
        _MF.check_type(marketprice_1min, MarketPrice)
        _MF.check_type(pair, Pair)
        _MF.check_type(can_buy_sell, bool)
        _MF.check_type(limit, float)
        k_limit_price = Map.key(Map.limit, Map.price)
        report = {
            Map.callback:   current_func,
            Map.loop:       loop_start_date,
            Map.turn:       turn_start_date,
            Map.market:     _MF.unix_to_date(marketprice_1min.get_time()),
            Map.pair:       pair,
            Map.condition:  can_buy_sell,
            k_limit_price:  limit,
            **report
        }
        return report

    @classmethod
    def _print_buy_sell_conditions(cls, rows_df: pd.DataFrame, condition: Callable) -> None:
        k_limit_price = Map.key(Map.limit, Map.price)
        keys = [Map.callback, Map.loop, Map.turn, Map.market, Map.pair, Map.condition, k_limit_price]
        k_missing = _MF.keys_exist(keys, list(rows_df.columns))
        if k_missing is not None:
            raise KeyError(f"Miss key '{k_missing}'")
        file_path = cls.get_path_file_stalk(condition)
        print_date = _MF.unix_to_date(_MF.get_timestamp())
        rows_df.insert(0, 'print_date', print_date)
        rows = rows_df.to_dict('records')
        fields = list(rows[0].keys())
        FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)

    # ••• STALK UP
    # ••• TRADE DOWN

    def _trade_inner(self, marketprices: Map = Map()) -> None:
        def get_unix_time(broker: Broker, period_1min: int, pair: Pair) -> int:
            if is_stage_one:
                marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                unix_time = marketprice_1min.get_time()
            else:
                unix_time = _MF.get_timestamp()
            return unix_time
        def manage_position(broker: Broker, position: HandTrade, period_1min: int, r_asset: Asset, class_name: str, current_func: str, loop_start_date: str, buy_reports: list, sell_reports: list) -> None:
            turn_start_date = _MF.unix_to_date(_MF.get_timestamp())
            pair = position.get_buy_order().get_pair()
            unix_time = get_unix_time(broker, period_1min, pair)
            if not position.is_executed(Map.buy):
                buy_settime = int(position.get_buy_order().get_settime()/1000)
                buy_next_update_time = _MF.round_time(buy_settime, period_1min) + period_1min
                can_buy, buy_report, buy_limit_float, _ = self.can_buy(broker, pair, marketprices)
                # Report Buy
                buy_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                buy_report = self._new_row_condition(buy_report, current_func, loop_start_date, turn_start_date, buy_marketprice_1min, pair, can_buy, buy_limit_float)
                buy_reports.append(buy_report)
                # Check
                if not can_buy:
                    self.cancel(pair, marketprices=marketprices)
                elif can_buy and (unix_time >= buy_next_update_time):
                    buy_limit = Price(buy_limit_float, r_asset)
                    self.cancel(pair, marketprices=marketprices)
                    self.buy(pair, Order.TYPE_LIMIT, limit=buy_limit, marketprices=marketprices)
            if position.has_position():
                is_sell_submitted = position.is_submitted(Map.sell)
                is_next_minute = False
                if is_sell_submitted:
                    sell_settime = int(position.get_sell_order().get_settime()/1000)
                    sell_next_update_time = _MF.round_time(sell_settime, period_1min) + period_1min
                    is_next_minute = unix_time >= sell_next_update_time
                can_sell, sell_report, sell_limit_float = self.can_sell(broker, pair, marketprices)
                sell_limit = Price(sell_limit_float, r_asset)
                # Report Buy
                sell_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                sell_report = self._new_row_condition(sell_report, current_func, loop_start_date, turn_start_date, sell_marketprice_1min, pair, can_sell, sell_limit_float)
                sell_reports.append(sell_report)
                # Check
                if can_sell:
                    self.cancel(pair, marketprices=marketprices) if is_sell_submitted else None
                    self.sell(pair, Order.TYPE_MARKET, marketprices=marketprices)
                elif (not can_sell) and (not is_sell_submitted):
                    self.sell(pair, Order.TYPE_LIMIT, limit=sell_limit, marketprices=marketprices)
                elif (not can_sell) and is_sell_submitted and is_next_minute:
                    self.cancel(pair, marketprices=marketprices)
                    self.sell(pair, Order.TYPE_LIMIT, limit=sell_limit, marketprices=marketprices)
            if position.is_closed():
                p = _MF.catch_exception(self.get_position, class_name, repport=False, **{Map.pair: pair})
                is_position_moved_to_closed = p is None
                if not is_position_moved_to_closed:
                    self._repport_positions(marketprices=marketprices)
                    self._move_closed_position(pair)
        # Stage 1
        is_stage_one = Config.get(Config.STAGE_MODE) == Config.STAGE_1
        if is_stage_one:
            self.set_stalk_on(on=False) if self.is_stalk_on() else None
            self._stalk_market()
        #
        broker = self.get_broker()
        positions = self.get_positions().copy()
        period_1min = Broker.PERIOD_1MIN
        r_asset = self.get_wallet().get_initial().get_asset()
        class_name = self.__class__.__name__
        buy_reports = []
        sell_reports = []
        loop_start_date = _MF.unix_to_date(_MF.get_timestamp())
        current_func = self._trade_inner.__name__
        for _, position in positions.items():
            loop_params = dict(
                broker=broker,
                position=position,
                period_1min=period_1min,
                r_asset=r_asset,
                class_name=class_name,
                current_func=current_func,
                loop_start_date=loop_start_date,
                buy_reports=buy_reports,
                sell_reports=sell_reports
            )
            _MF.catch_exception(manage_position, class_name, **loop_params)
        self._print_buy_sell_conditions(pd.DataFrame(buy_reports), self.can_buy) if len(buy_reports) > 0 else None
        self._print_buy_sell_conditions(pd.DataFrame(sell_reports), self.can_sell) if len(sell_reports) > 0 else None
    # ••• TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

    @classmethod
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float, dict]:
        TRIGGE_KELTNER = 2/100
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_15min = Broker.PERIOD_15MIN
        psar_params_1 = cls.PSAR_1
        psar_param_str_1 = cls.param_to_str(psar_params_1)
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        indexes = marketprice_1min_pd.index
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        k_keltner_roi_1min = f'keltner_roi_{period_strs[period_1min]}'
        k_keltner_high_1min = f'keltner_high_{period_strs[period_1min]}[-1]'
        k_close_1min = f'close_{period_strs[period_1min]}[-1]'
        # Check
        can_buy = cls.is_keltner_roi_above_trigger(vars_map, broker, pair, period_1min, marketprices, TRIGGE_KELTNER) \
            and cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_psar_rising(vars_map, broker, pair, period_15min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_15min, marketprices) \
            and ( 
                    (
                        cls.is_psar_rising(vars_map, broker, pair, period_1min, marketprices) \
                        and
                        cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices)
                    )
                    or cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices, psar_params=psar_params_1) \
                ) \
            and cls.is_price_bellow_keltner_line(vars_map, broker, pair, period_1min, marketprices, Map.close, Map.high)
        report = {
            f'can_buy':                                                             can_buy,
            f'keltner_roi_above_trigger_{period_strs[period_1min]}':                vars_map.get(f'keltner_roi_above_trigger_{period_strs[period_1min]}'),
            f'psar_rising_{period_strs[period_5min]}':                              vars_map.get(f'psar_rising_{period_strs[period_5min]}'),
            f'psar_rising_{period_strs[period_15min]}':                             vars_map.get(f'psar_rising_{period_strs[period_15min]}'),
            f'supertrend_rising_{period_strs[period_5min]}':                        vars_map.get(f'supertrend_rising_{period_strs[period_5min]}'),
            f'supertrend_rising_{period_strs[period_15min]}':                       vars_map.get(f'supertrend_rising_{period_strs[period_15min]}'),
            f'psar_rising_{period_strs[period_1min]}':                              vars_map.get(f'psar_rising_{period_strs[period_1min]}'),
            f'supertrend_rising_{period_strs[period_1min]}':                        vars_map.get(f'supertrend_rising_{period_strs[period_1min]}'),
            f'psar_rising_{period_strs[period_5min]}_{psar_param_str_1}':           vars_map.get(f'psar_rising_{period_strs[period_5min]}_{psar_param_str_1}'),
            f'{Map.close}_bellow_keltner_{Map.high}_{period_strs[period_1min]}':    vars_map.get(f'{Map.close}_bellow_keltner_{Map.high}_{period_strs[period_1min]}'),
            f'TRIGGE_KELTNER':                                                      TRIGGE_KELTNER,
            f'low_{period_strs[period_1min]}[-1]':                                  marketprice_1min_pd.loc[indexes[-1], Map.low],
            f'low_{period_strs[period_1min]}[-2]':                                  marketprice_1min_pd.loc[indexes[-2], Map.low],
            k_close_1min:                                                           marketprice_1min_pd.loc[indexes[-1], Map.close],
            f'close_{period_strs[period_1min]}[-2]':                                marketprice_1min_pd.loc[indexes[-2], Map.close],
            f'high_{period_strs[period_1min]}[-1]':                                 marketprice_1min_pd.loc[indexes[-1], Map.high],
            f'high_{period_strs[period_1min]}[-2]':                                 marketprice_1min_pd.loc[indexes[-2], Map.high],
            k_keltner_roi_1min:                                                     vars_map.get(k_keltner_roi_1min),
            f'keltner_low_{period_strs[period_1min]}[-1]':                          vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]'),
            f'keltner_low_{period_strs[period_1min]}[-2]':                          vars_map.get(f'keltner_low_{period_strs[period_1min]}[-2]'),
            f'keltner_middle_{period_strs[period_1min]}[-1]':                       vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]'),
            f'keltner_middle_{period_strs[period_1min]}[-2]':                       vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-2]'),
            k_keltner_high_1min:                                                    vars_map.get(k_keltner_high_1min),
            f'keltner_high_{period_strs[period_1min]}[-2]':                         vars_map.get(f'keltner_high_{period_strs[period_1min]}[-2]'),
            f'psar_{period_strs[period_5min]}[-1]':                                 vars_map.get(f'psar_{period_strs[period_5min]}[-1]'),
            f'psar_{period_strs[period_5min]}[-2]':                                 vars_map.get(f'psar_{period_strs[period_5min]}[-2]'),
            f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-1]':              vars_map.get(f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-1]'),
            f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-2]':              vars_map.get(f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-2]'),
            f'psar_{period_strs[period_15min]}[-1]':                                vars_map.get(f'psar_{period_strs[period_15min]}[-1]'),
            f'psar_{period_strs[period_15min]}[-2]':                                vars_map.get(f'psar_{period_strs[period_15min]}[-2]'),
            f'supertrend_{period_strs[period_5min]}[-1]':                           vars_map.get(f'supertrend_{period_strs[period_5min]}[-1]'),
            f'supertrend_{period_strs[period_5min]}[-2]':                           vars_map.get(f'supertrend_{period_strs[period_5min]}[-2]'),
            f'supertrend_{period_strs[period_15min]}[-1]':                          vars_map.get(f'supertrend_{period_strs[period_15min]}[-1]'),
            f'supertrend_{period_strs[period_15min]}[-2]':                          vars_map.get(f'supertrend_{period_strs[period_15min]}[-2]')
        }
        limit = vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]')
        keys = {
            Map.key(Map.keltner, Map.roi):  k_keltner_roi_1min,
            Map.key(Map.keltner, Map.high): k_keltner_high_1min,
            Map.close:                      k_close_1min
        }
        return can_buy, report, limit, keys

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float]:
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_15min = Broker.PERIOD_15MIN
        psar_params_1 = cls.PSAR_1
        psar_param_str_1 = cls.param_to_str(psar_params_1)
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        indexes = marketprice_1min_pd.index
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        # Check
        cls.is_keltner_roi_above_trigger(vars_map, broker, pair, period_1min, marketprices, 0)
        can_sell = (not cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices)) \
            or (not cls.is_psar_rising(vars_map, broker, pair, period_15min, marketprices)) \
            or (not cls.is_supertrend_rising(vars_map, broker, pair, period_5min, marketprices)) \
            or (not cls.is_supertrend_rising(vars_map, broker, pair, period_15min, marketprices)) \
            or (
                    (
                        not cls.is_psar_rising(vars_map, broker, pair, period_1min, marketprices) \
                        or
                        not cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices)
                    )
                    and
                    not cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices, psar_params=psar_params_1)
            )
        report = {
            'can_sell':                                                     can_sell,
            f'psar_rising_{period_strs[period_5min]}':                      vars_map.get(f'psar_rising_{period_strs[period_5min]}'),
            f'psar_rising_{period_strs[period_15min]}':                     vars_map.get(f'psar_rising_{period_strs[period_15min]}'),
            f'supertrend_rising_{period_strs[period_5min]}':                vars_map.get(f'supertrend_rising_{period_strs[period_5min]}'),
            f'supertrend_rising_{period_strs[period_15min]}':               vars_map.get(f'supertrend_rising_{period_strs[period_15min]}'),
            f'psar_rising_{period_strs[period_1min]}':                      vars_map.get(f'psar_rising_{period_strs[period_1min]}'),
            f'supertrend_rising_{period_strs[period_1min]}':                vars_map.get(f'supertrend_rising_{period_strs[period_1min]}'),
            f'psar_rising_{period_strs[period_5min]}_{psar_param_str_1}':   vars_map.get(f'psar_rising_{period_strs[period_5min]}_{psar_param_str_1}'),
            f'low_{period_strs[period_1min]}[-1]':                          marketprice_1min_pd.loc[indexes[-1], Map.low],
            f'low_{period_strs[period_1min]}[-2]':                          marketprice_1min_pd.loc[indexes[-2], Map.low],
            f'close_{period_strs[period_1min]}[-1]':                        marketprice_1min_pd.loc[indexes[-1], Map.close],
            f'close_{period_strs[period_1min]}[-2]':                        marketprice_1min_pd.loc[indexes[-2], Map.close],
            f'high_{period_strs[period_1min]}[-1]':                         marketprice_1min_pd.loc[indexes[-1], Map.high],
            f'high_{period_strs[period_1min]}[-2]':                         marketprice_1min_pd.loc[indexes[-2], Map.high],
            f'keltner_low_{period_strs[period_1min]}[-1]':                  vars_map.get(f'keltner_low_{period_strs[period_1min]}[-1]'),
            f'keltner_low_{period_strs[period_1min]}[-2]':                  vars_map.get(f'keltner_low_{period_strs[period_1min]}[-2]'),
            f'keltner_middle_{period_strs[period_1min]}[-1]':               vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]'),
            f'keltner_middle_{period_strs[period_1min]}[-2]':               vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-2]'),
            f'keltner_high_{period_strs[period_1min]}[-1]':                 vars_map.get(f'keltner_high_{period_strs[period_1min]}[-1]'),
            f'keltner_high_{period_strs[period_1min]}[-2]':                 vars_map.get(f'keltner_high_{period_strs[period_1min]}[-2]'),
            f'psar_{period_strs[period_5min]}[-1]':                         vars_map.get(f'psar_{period_strs[period_5min]}[-1]'),
            f'psar_{period_strs[period_5min]}[-2]':                         vars_map.get(f'psar_{period_strs[period_5min]}[-2]'),
            f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-1]':      vars_map.get(f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-1]'),
            f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-2]':      vars_map.get(f'psar_{period_strs[period_5min]}_{psar_param_str_1}[-2]'),
            f'psar_{period_strs[period_15min]}[-1]':                        vars_map.get(f'psar_{period_strs[period_15min]}[-1]'),
            f'psar_{period_strs[period_15min]}[-2]':                        vars_map.get(f'psar_{period_strs[period_15min]}[-2]'),
            f'supertrend_{period_strs[period_5min]}[-1]':                   vars_map.get(f'supertrend_{period_strs[period_5min]}[-1]'),
            f'supertrend_{period_strs[period_5min]}[-2]':                   vars_map.get(f'supertrend_{period_strs[period_5min]}[-2]'),
            f'supertrend_{period_strs[period_15min]}[-1]':                  vars_map.get(f'supertrend_{period_strs[period_15min]}[-1]'),
            f'supertrend_{period_strs[period_15min]}[-2]':                  vars_map.get(f'supertrend_{period_strs[period_15min]}[-2]')
        }
        limit = vars_map.get(f'keltner_middle_{period_strs[period_1min]}[-1]')
        return can_sell, report, limit

    @classmethod
    def is_psar_rising(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, psar_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        closes = list(marketprice.get_closes())
        closes.reverse()
        psars = list(marketprice.get_psar(**psar_params))
        psars.reverse()
        param_str = cls.param_to_str(psar_params)
        param_str = '_' + param_str if len(param_str) > 0 else ''
        # Check
        is_rising = MarketPrice.get_psar_trend(closes, psars, -1) == MarketPrice.PSAR_RISING
        vars_map.put(is_rising,     f'psar_rising_{period_str}{param_str}')
        vars_map.put(closes[-1],    f'close_{period_str}[-1]')
        vars_map.put(closes[-2],    f'close_{period_str}[-2]')
        vars_map.put(psars[-1],     f'psar_{period_str}{param_str}[-1]')
        vars_map.put(psars[-2],     f'psar_{period_str}{param_str}[-2]')
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
        # marketprice.reset_collections()
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
    def is_price_bellow_keltner_line(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, price_line: str, keltner_line: str) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        keltner_map = marketprice.get_keltnerchannel(multiple=1)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Check
        price_bellow_keltner_high = bool(marketprice_df[price_line].iloc[-1] < keltner[-1])
        # Put
        vars_map.put(price_bellow_keltner_high, f'{price_line}_bellow_keltner_{keltner_line}_{period_str}')
        vars_map.put(keltner[-1],               f'keltner_{keltner_line}_{period_str}[-1]')
        vars_map.put(keltner[-2],               f'keltner_{keltner_line}_{period_str}[-2]')
        return price_bellow_keltner_high

    @classmethod
    def param_to_str(cls, params: dict) -> str:
        param_str = ''
        if len(params) > 0:
            for key, value in params.items():
                param_str += f'{key}={value}' if len(param_str) == 0 else f'_{key}={value}'
        return param_str

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trade: dict, buy_conditions: list, sell_conditions: list) -> dict:
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            can_buy, buy_condition, buy_limit, _ = cls.can_buy(broker, pair, marketprices)
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
            cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.close) \
                if can_sell else cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_LIMIT, limit=sell_limit)
        return trade

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Solomon.__new__(Solomon)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
    