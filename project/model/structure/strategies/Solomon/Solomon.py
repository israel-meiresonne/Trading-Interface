import time
from typing import Callable, List

import numpy as np
import pandas as pd

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.HandTrade import HandTrade
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Solomon(Strategy):
    PREFIX_ID =             'solomon_'
    _SLEEP_TRADE =          30
    KELTER_SUPPORT =        None
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_5MIN,
        Broker.PERIOD_15MIN
        ]
    PSAR_1 =                    dict(step=.6, max_step=.6)
    K_BUY_SELL_CONDITION =      'K_BUY_SELL_CONDITION'
    K_MARKET_TRENDS =           'K_MARKET_TRENDS'
    K_EDITED_MARKET_TRENDS =    'K_EDITED_MARKET_TRENDS'
    MAX_LOSS_RATE =             -1/100
    MAX_PROFIT_RATE =           1/100

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STALK DOWN

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
        _MF.check_type(limit, (int, float))
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
        # Save header
        to_print = cls.get_stack()
        stack_base_key = [cls.K_BUY_SELL_CONDITION, file_path]
        stack_column_key = [*stack_base_key, Map.column]
        stack_content_key = [*stack_base_key, Map.content]
        content = to_print.get(*stack_content_key)
        if content is None:
            content = rows
            to_print.put(fields, *stack_column_key)
        else:
            content = [*content, *rows]
        to_print.put(content,   *stack_content_key)

    # ——————————————————————————————————————————— STALK UP
    # ——————————————————————————————————————————— TRADE DOWN

    """
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
    """

    def _trade_inner(self, marketprices: Map = Map()) -> None:
        broker = self.get_broker()
        if Config.get(Config.STAGE_MODE) == Config.STAGE_1:
            pair = self.get_pair()
            period_1min = Broker.PERIOD_1MIN
            marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
            event_time = marketprice_1min.get_time()
            params = {
                Map.time:   event_time,
                Map.pair:   pair,
                Map.period: period_1min,
                Map.price:  None
            }
            self._callback_trade(params, marketprices)
        else:
            broker.add_event_callback(Broker.EVENT_NEW_PERIOD, self._callback_trade) if (not broker.exist_event_callback(Broker.EVENT_NEW_PERIOD, self._callback_trade)) else None
        stack = self.get_stack()
        stack_key = self.K_BUY_SELL_CONDITION
        if stack.get(stack_key) is not None:
            stack_copy = stack.get(stack_key).copy()
            del stack.get_map()[stack_key]
            for file, datas_dict in stack_copy.items():
                fields =    datas_dict[Map.column]
                rows =      datas_dict[Map.content]
                FileManager.write_csv(file, fields, rows, overwrite=False, make_dir=True)

    def _callback_trade(self, params: dict, marketprices: Map = None) -> None:
        def explode_params(params: dict) -> tuple[int, Pair, int, np.ndarray]:
            return tuple(params.values())
        def get_position(pair: Pair) -> HandTrade:
            return _MF.catch_exception(self.get_position, self.__class__.__name__, repport=False, **{Map.pair: pair})
        def can_stalk(unix_time: int, pair: Pair, period: int, stalk_interval: int) -> bool:
            can = False
            stack = self.get_stack()
            keys = [Map.stalk, pair, period, Map.time]
            last_stalk = stack.get(*keys)
            if last_stalk is None:
                can = True
            else:
                next_stalk = last_stalk + stalk_interval
                can = unix_time >= next_stalk
            if can:
                event_time_rounded = _MF.round_time(unix_time, stalk_interval)
                stack.put(event_time_rounded, *keys)
            return can
        # # #
        period_1min = Broker.PERIOD_1MIN
        event_time, pair, event_period, market_row = explode_params(params)
        if (params[Map.period] != period_1min) or (not can_stalk(unix_time=event_time, pair=pair, period=event_period, stalk_interval=period_1min)):
            return None
        position = get_position(pair)
        if ((not self.is_max_position_reached()) or (position is not None)):
            broker = self.get_broker()
            r_asset = self.get_wallet().get_initial().get_asset()
            marketprices = Map() if marketprices is None else marketprices
            buy_reports = []
            sell_reports = []
            loop_start_date = _MF.unix_to_date(event_time)
            unix_time = event_time if (Config.get(Config.STAGE_MODE) == Config.STAGE_1) else _MF.get_timestamp()
            turn_start_date = _MF.unix_to_date(unix_time)
            current_func = self._callback_trade.__name__
            if (position is None) or (not position.is_executed(Map.buy)):
                can_buy, buy_report = self.can_buy(broker, pair, marketprices)
                # Report Buy
                buy_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                buy_report = self._new_row_condition(buy_report, current_func, loop_start_date, turn_start_date, buy_marketprice_1min, pair, can_buy, -1)
                buy_reports.append(buy_report)
                if can_buy:
                    self.buy(pair, Order.TYPE_MARKET, marketprices=marketprices)
            elif position.has_position():
                can_sell, sell_report, sell_limit_float = self.can_sell(broker, pair, marketprices)
                sell_limit = Price(sell_limit_float, r_asset)
                # Report Buy
                sell_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                sell_report = self._new_row_condition(sell_report, current_func, loop_start_date, turn_start_date, sell_marketprice_1min, pair, can_sell, sell_limit_float)
                sell_reports.append(sell_report)
                # Check
                is_sell_submitted = position.is_submitted(Map.sell)
                if can_sell:
                    self.cancel(pair, marketprices=marketprices) if is_sell_submitted else None
                    self.sell(pair, Order.TYPE_MARKET, marketprices=marketprices) if position.has_position() else None
                elif (not can_sell) and (not is_sell_submitted):
                    self.sell(pair, Order.TYPE_LIMIT, limit=sell_limit, marketprices=marketprices)
                elif (not can_sell) and is_sell_submitted:
                    self.cancel(pair, marketprices=marketprices)
                    self.sell(pair, Order.TYPE_LIMIT, limit=sell_limit, marketprices=marketprices) if position.has_position() else None
            position = get_position(pair)
            if (position is not None) and position.is_closed():
                self._repport_positions(marketprices=marketprices)
                self._move_closed_position(pair)
            self._print_buy_sell_conditions(pd.DataFrame(buy_reports), self.can_buy) if len(buy_reports) > 0 else None
            self._print_buy_sell_conditions(pd.DataFrame(sell_reports), self.can_sell) if len(sell_reports) > 0 else None

    # ——————————————————————————————————————————— TRADE UP
    # ——————————————————————————————————————————— OTHERS SELF DOWN

    def stop(self) -> None:
        broker = self.get_broker()
        broker.delete_event_callback(Broker.EVENT_NEW_PERIOD, self._callback_trade)
        super().stop()

    # ——————————————————————————————————————————— OTHERS SELF UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————
    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST DOWN

    @classmethod
    def _can_buy_sell_set_headers(cls, caller_callback: Callable, func_and_params: list[dict]) -> dict:
        """
        Parameters:
        -----------
        caller_func: Callable
            The callback calling this function
        func_and_params: list[dict]
            List of function to check and their params
            | Keys                                 |     | Type     |     | Doc                     |
            | ------------------------------------ | --- | -------- | --- | ----------------------- |
            | list[index{int}][dict[Map.callback]] | ->  | Callable | ->  | Function to execute     |
            | list[index{int}][dict[Map.param]]    | ->  | dict     | ->  | Params for the callback |
        """
        def get_vars_map() -> Map:
            return func_and_params[0][Map.param]['vars_map']
        caller_callback_name = caller_callback.__name__
        _stack = cls.get_stack()
        vars_map = get_vars_map()
        """
        _stack[caller_callback_name][Map.condition]:   {list}  # boolean column names
        _stack[caller_callback_name][Map.value]:       {list}  # values column names
        """
        header_dict = _stack.get(caller_callback_name)
        if header_dict is None:
            [row[Map.callback](**row[Map.param]) if isinstance(row[Map.param], dict) else row[Map.callback](*row[Map.param]) for row in func_and_params]
            new_header_dict = vars_map.get_keys()
            for new_var_map_key in new_header_dict:
                columns = list(vars_map.get(new_var_map_key).keys())
                _stack.put(columns, caller_callback_name, new_var_map_key)
            header_dict = _stack.get(caller_callback_name)
        return header_dict

    @classmethod
    def _can_buy_sell_new_report(cls, caller_callback: Callable, header_dict: dict, can_result: bool, vars_map: Map) -> dict:
        caller_callback_name = caller_callback.__name__
        boolean_keys = header_dict[Map.condition]
        values_keys = header_dict[Map.value]
        report = {
            caller_callback_name:   can_result,
            **{boolean_key:         vars_map.get(Map.condition, boolean_key) for boolean_key in boolean_keys},
            **{values_key:          vars_map.get(Map.value, values_key) for values_key in values_keys}
        }
        return report

    @classmethod
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map, params: dict) -> tuple[bool, dict, float]:
        TRIGGE_KELTNER =            2/100
        KELTNER_RANGE_RATE =        1/8
        MEAN_MARKET_TREND_WINDOW =  5
        MEAN_MARKET_TREND_TRIGGER = 20/100
        def is_last_roi_positive(vars_map: Map, roi: float) -> bool:
            last_roi_positive = roi > 0
            vars_map.put(last_roi_positive, Map.condition,  f'is_last_roi_positive')
            return last_roi_positive
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_15min = Broker.PERIOD_15MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        # Params
        now_index =     -1
        prev_index_2 =  -2
        compare_1 =     '<='
        now_time =      marketprice_1min_pd[Map.time].iloc[-1]
        # Params
        last_sell_time =    params[Map.time]
        last_sell_date =    _MF.unix_to_date(last_sell_time)
        last_sell_roi =     params[Map.roi]
        buy_price =         marketprice_1min_pd[Map.close].iloc[-1]
        fees =              broker.get_trade_fee(pair)
        maker_fee =         fees.get(Map.maker)
        taker_fee =         fees.get(Map.taker)
        max_loss_price, max_loss_rate = cls._max_sell_price(buy_price, cls.MAX_LOSS_RATE, taker_fee, maker_fee)
        # Add value
        vars_map.put(taker_fee,         Map.value, 'taker_fee')
        vars_map.put(maker_fee,         Map.value, 'maker_fee')
        vars_map.put(buy_price,         Map.value, 'buy_price')
        vars_map.put(max_loss_price,    Map.value, 'max_loss_price')
        vars_map.put(max_loss_rate,     Map.value, 'max_loss_rate')
        vars_map.put(last_sell_date,    Map.value, 'last_sell_date')
        vars_map.put(last_sell_roi,     Map.value, 'last_sell_roi')
        # Add price
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-1],   Map.value, f'open_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-2],   Map.value, f'open_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-1],    Map.value, f'low_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-2],    Map.value, f'low_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-1],   Map.value, f'high_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-2],   Map.value, f'high_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-1],  Map.value, f'close_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-2],  Map.value, f'close_{period_strs[period_1min]}[-2]')
        # Set header
        this_func = cls.can_buy
        func_and_params = [
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, is_int_round=True, window=MEAN_MARKET_TREND_WINDOW)},
            {Map.callback: cls.is_last_min_market_trend_bellow,     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, trigger=MEAN_MARKET_TREND_TRIGGER, is_int_round=True, window=MEAN_MARKET_TREND_WINDOW)},
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index, is_int_round=False)},
            {Map.callback: cls.is_last_min_market_trend_bellow,     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index, trigger=MEAN_MARKET_TREND_TRIGGER, is_int_round=True)},
            {Map.callback: cls.is_keltner_roi_above_trigger,        Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, trigge_keltner=TRIGGE_KELTNER, index=prev_index_2)},
            {Map.callback: cls.is_compare_price_and_keltner_line,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, compare=compare_1, price_line=Map.low, keltner_line=Map.low, index=prev_index_2)},
            {Map.callback: cls.is_close_bellow_keltner_range,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, rate=KELTNER_RANGE_RATE, index=now_index)},
            {Map.callback: is_last_roi_positive,                    Map.param: dict(vars_map=vars_map, roi=last_sell_roi)},
            {Map.callback: cls.are_times_in_same_psar,              Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, old_time=last_sell_time, new_time=now_time, psar_params={})},
            {Map.callback: cls.is_psar_rising,                      Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, psar_params={})},
            {Map.callback: cls.is_psar_rising,                      Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index, psar_params={})},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)}
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        can_buy = cls.is_tangent_market_trend_positive(**func_and_params[0][Map.param]) \
            and cls.is_last_min_market_trend_bellow(**func_and_params[1][Map.param]) \
            and cls.is_tangent_market_trend_positive(**func_and_params[2][Map.param]) \
            and cls.is_last_min_market_trend_bellow(**func_and_params[3][Map.param]) \
            and cls.is_keltner_roi_above_trigger(**func_and_params[4][Map.param]) \
            and cls.is_compare_price_and_keltner_line(**func_and_params[5][Map.param]) \
            and cls.is_close_bellow_keltner_range(**func_and_params[6][Map.param]) \
            and ((is_last_roi_positive(**func_and_params[7][Map.param])) or (not cls.are_times_in_same_psar(**func_and_params[8][Map.param]))) \
            and cls.is_psar_rising(**func_and_params[9][Map.param]) \
            and cls.is_psar_rising(**func_and_params[10][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[11][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[12][Map.param])
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_buy, vars_map)
        return can_buy, report, max_loss_price

    @classmethod
    def _max_sell_price(cls, buy_price: float, max_rate: float, buy_fee_rate: float, sell_fee_rate: float) -> tuple[float, float]:
        sell_price = buy_price * (1 + (max_rate + buy_fee_rate + sell_fee_rate))
        roi = _MF.progress_rate(sell_price, buy_price)
        return sell_price, roi

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map, params: dict) -> tuple[bool, dict, str, dict]:
        def is_roi_positive(vars_map: Map, roi: float) -> bool:
            # Check
            roi_positive = roi >= 0
            # Put
            vars_map.put(roi_positive, Map.condition, f'is_roi_positive')
            return roi_positive
        vars_map = Map()
        period_1min =   Broker.PERIOD_1MIN
        period_5min =   Broker.PERIOD_5MIN
        period_15min =  Broker.PERIOD_15MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        # Params
        now_index = -1
        # Max Prices
        limit_price =   None
        stop_price =    None
        sell_key =      None
        position_roi =  params[Map.roi]
        buy_price =     params[Map.buy]
        buy_fee_rate =  params[Map.fee]
        fees =          broker.get_trade_fee(pair)
        maker_fee =     fees.get(Map.maker)
        taker_fee =     fees.get(Map.taker)
        max_loss_price, max_loss_rate =     cls._max_sell_price(buy_price, cls.MAX_LOSS_RATE, buy_fee_rate, maker_fee)
        max_profit_price, max_profit_rate = cls._max_sell_price(buy_price, cls.MAX_PROFIT_RATE, buy_fee_rate, taker_fee)
        # Add value
        vars_map.put(position_roi,      Map.value, 'position_roi')
        vars_map.put(taker_fee,         Map.value, 'taker_fee')
        vars_map.put(maker_fee,         Map.value, 'maker_fee')
        vars_map.put(buy_price,         Map.value, 'buy_price')
        vars_map.put(max_loss_price,    Map.value, 'max_loss_price')
        vars_map.put(max_loss_rate,     Map.value, 'max_loss_rate')
        vars_map.put(max_profit_price,  Map.value, 'max_profit_price')
        vars_map.put(max_profit_rate,   Map.value, 'max_profit_rate')
        #
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-1],    Map.value, f'open_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-2],    Map.value, f'open_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-1],     Map.value, f'low_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-2],     Map.value, f'low_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-1],    Map.value, f'high_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-2],    Map.value, f'high_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-1],   Map.value, f'close_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-2],   Map.value, f'close_{period_strs[period_1min]}[-2]')
        # Set header
        this_func = cls.can_sell
        func_and_params = [
            {Map.callback: cls.is_roi_compare_trigger,          Map.param: dict(vars_map=vars_map, compare='>=', roi=position_roi, trigger=max_profit_rate)},
            {Map.callback: cls.is_psar_rising,                  Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)},
            {Map.callback: is_roi_positive,                     Map.param: dict(vars_map=vars_map, roi=position_roi)},
            {Map.callback: cls.is_keltner_roi_above_trigger,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, trigge_keltner=0, index=now_index)}
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        can_sell = cls.is_roi_compare_trigger(**func_and_params[0][Map.param]) \
            or (not cls.is_psar_rising(**func_and_params[1][Map.param])) \
            or (not cls.is_supertrend_rising(**func_and_params[2][Map.param])) \
            or (not cls.is_supertrend_rising(**func_and_params[3][Map.param]))
        if (not can_sell):
            if is_roi_positive(**func_and_params[4][Map.param]):
                sell_key = Map.limit
                cls.is_keltner_roi_above_trigger(**func_and_params[5][Map.param])
                limit_price = vars_map.get(Map.value, f'keltner_middle_{period_strs[period_1min]}[-1]')
            else:
                sell_key = Map.stop
                stop_price = max_loss_price
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_sell, vars_map)
        sell_prices = {Map.limit: limit_price, Map.stop: stop_price}
        return can_sell, report, sell_key, sell_prices

    @classmethod
    def is_psar_rising(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, psar_params: dict = {}) -> bool:
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
        is_rising = MarketPrice.get_psar_trend(closes, psars, index) == MarketPrice.PSAR_RISING
        vars_map.put(is_rising,     Map.condition,  f'psar_rising_{period_str}{param_str}[{index}]')
        vars_map.put(closes[-1],    Map.value,      f'close_{period_str}[-1]')
        vars_map.put(closes[-2],    Map.value,      f'close_{period_str}[-2]')
        vars_map.put(closes[index], Map.value,      f'close_{period_str}[{index}]')
        vars_map.put(psars[-1],     Map.value,      f'psar_{period_str}{param_str}[-1]')
        vars_map.put(psars[-2],     Map.value,      f'psar_{period_str}{param_str}[-2]')
        vars_map.put(psars[index],  Map.value,      f'psar_{period_str}{param_str}[{index}]')
        return is_rising

    @classmethod
    def are_times_in_same_psar(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, old_time: int, new_time: int, psar_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_pd = marketprice.to_pd()
        closes = marketprice_pd[Map.close]
        open_times = marketprice_pd[Map.time]
        psars = list(marketprice.get_psar(**psar_params))
        psars.reverse()
        # Init
        psar_start_time =   None
        psar_end_time =     None
        old_date =          None
        new_date =          None
        psar_start_date =   None
        psar_end_date =     None
        # Dates
        groups = _MF.group_swings(psars, closes)
        old_sub_times = open_times[open_times <= old_time]
        if old_sub_times.shape[0] > 0:
            old_index =         old_sub_times.index[-1]
            psar_start_index =  groups[old_index][0]
            psar_end_index =    groups[old_index][1]
            psar_start_time =   open_times[psar_start_index]
            psar_end_time =     open_times[psar_end_index]
            old_date =          _MF.unix_to_date(old_time)
            new_date =          _MF.unix_to_date(new_time)
            psar_start_date =   _MF.unix_to_date(psar_start_time)
            psar_end_date =     _MF.unix_to_date(psar_end_time)
            # Check
            time_in_same_psar = psar_start_time <= new_time <= psar_end_time
        else:
            time_in_same_psar = False
        # Put
        param_str = cls.param_to_str(psar_params)
        param_str = '_' + param_str if len(param_str) > 0 else ''
        vars_map.put(time_in_same_psar, Map.condition,  f'are_times_in_same_psar_{period_str}{param_str}')
        vars_map.put(psars[-1],         Map.value,      f'are_time_in_same_psar_psar_{period_str}{param_str}[-1]')
        vars_map.put(psars[-2],         Map.value,      f'are_time_in_same_psar_psar_{period_str}{param_str}[-2]')
        vars_map.put(old_date,          Map.value,      f'are_time_in_same_psar_old_date_{period_str}{param_str}')
        vars_map.put(new_date,          Map.value,      f'are_time_in_same_psar_new_date_{period_str}{param_str}')
        vars_map.put(psar_start_date,   Map.value,      f'are_time_in_same_psar_start_date_{period_str}{param_str}')
        vars_map.put(psar_end_date,     Map.value,      f'are_time_in_same_psar_end_date_{period_str}{param_str}')
        return time_in_same_psar

    @classmethod
    def is_supertrend_rising(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        closes = list(marketprice.get_closes())
        closes.reverse()
        supertrends = list(marketprice.get_super_trend())
        supertrends.reverse()
        is_rising = MarketPrice.get_super_trend_trend(closes, supertrends, index) == MarketPrice.SUPERTREND_RISING
        vars_map.put(is_rising,             Map.condition,  f'supertrend_rising_{period_str}[{index}]')
        vars_map.put(closes[-1],            Map.value,      f'close_{period_str}[-1]')
        vars_map.put(closes[-2],            Map.value,      f'close_{period_str}[-2]')
        vars_map.put(closes[index],         Map.value,      f'close_{period_str}[{index}]')
        vars_map.put(supertrends[-1],       Map.value,      f'supertrend_{period_str}[-1]')
        vars_map.put(supertrends[-2],       Map.value,      f'supertrend_{period_str}[-2]')
        vars_map.put(supertrends[index],    Map.value,      f'supertrend_{period_str}[{index}]')
        return is_rising

    @classmethod
    def is_keltner_roi_above_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, trigge_keltner: float, index: int) -> bool:
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
        keltner_roi = _MF.progress_rate(keltner_high[index], keltner_low[index])
        keltner_roi_above_trigger = keltner_roi >= trigge_keltner
        # Put
        vars_map.put(keltner_roi_above_trigger, Map.condition,  f'keltner_roi_above_trigger_{period_str}[{index}]')
        vars_map.put(keltner_roi,               Map.value,      f'keltner_roi_{period_str}')
        vars_map.put(keltner_low[-1],           Map.value,      f'keltner_low_{period_str}[-1]')
        vars_map.put(keltner_low[-2],           Map.value,      f'keltner_low_{period_str}[-2]')
        vars_map.put(keltner_low[index],        Map.value,      f'keltner_low_{period_str}[{index}]')
        vars_map.put(keltner_middle[-1],        Map.value,      f'keltner_middle_{period_str}[-1]')
        vars_map.put(keltner_middle[-2],        Map.value,      f'keltner_middle_{period_str}[-2]')
        vars_map.put(keltner_middle[index],     Map.value,      f'keltner_middle_{period_str}[{index}]')
        vars_map.put(keltner_high[-1],          Map.value,      f'keltner_high_{period_str}[-1]')
        vars_map.put(keltner_high[-2],          Map.value,      f'keltner_high_{period_str}[-2]')
        vars_map.put(keltner_high[index],       Map.value,      f'keltner_high_{period_str}[{index}]')
        return keltner_roi_above_trigger

    @classmethod
    def is_compare_price_and_keltner_line(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, compare: str, price_line: str, keltner_line: str, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        keltner_map = marketprice.get_keltnerchannel(multiple=1)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Check
        market_price = marketprice_df[price_line].iloc[index]
        keltner_price = keltner[index]
        price_compare_keltner_high = bool(eval(f'{market_price} {compare} {keltner_price}'))
        # Put
        vars_map.put(price_compare_keltner_high,    Map.condition,  f'{price_line}[{index}]_{compare}_keltner_{keltner_line}_{period_str}[{index}]')
        vars_map.put(keltner[-1],                   Map.value,      f'keltner_{keltner_line}_{period_str}[-1]')
        vars_map.put(keltner[-2],                   Map.value,      f'keltner_{keltner_line}_{period_str}[-2]')
        vars_map.put(keltner[index],                Map.value,      f'keltner_{keltner_line}_{period_str}[{index}]')
        return price_compare_keltner_high

    @classmethod
    def is_close_bellow_keltner_range(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, rate: float, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        keltner_lines = marketprice.get_keltnerchannel(multiple=1).get_map()
        keltner_high = list(keltner_lines[Map.high])
        keltner_high.reverse()
        keltner_low = list(keltner_lines[Map.low])
        keltner_low.reverse()
        #
        price_line = Map.open if Config.get(Config.STAGE_MODE) == Config.STAGE_1 else Map.close
        # Check
        keltner_range = keltner_high[index] - keltner_low[index]
        keltner_piece = keltner_range * rate
        keltner_price = keltner_piece + keltner_low[index]
        market_price = marketprice_df[price_line].iloc[index]
        close_bellow_keltner_range = bool(market_price <= keltner_price)
        # Put
        vars_map.put(close_bellow_keltner_range,    Map.condition,  f'close_bellow_keltner_range_{period_str}[{index}]')
        vars_map.put(keltner_range,                 Map.value,      f'keltner_range_{period_str}[{index}]')
        vars_map.put(keltner_piece,                 Map.value,      f'keltner_piece_{period_str}[{index}]')
        vars_map.put(keltner_price,                 Map.value,      f'keltner_price_{period_str}[{index}]')
        vars_map.put(market_price,                  Map.value,      f'market_price_{period_str}[{index}]')
        vars_map.put(keltner_high[-1],              Map.value,      f'keltner_high_{period_str}[-1]')
        vars_map.put(keltner_high[-2],              Map.value,      f'keltner_high_{period_str}[-2]')
        vars_map.put(keltner_high[index],           Map.value,      f'keltner_high_{period_str}[{index}]')
        vars_map.put(keltner_low[-1],               Map.value,      f'keltner_low_{period_str}[-1]')
        vars_map.put(keltner_low[-2],               Map.value,      f'keltner_low_{period_str}[-2]')
        vars_map.put(keltner_low[index],            Map.value,      f'keltner_low_{period_str}[{index}]')
        return close_bellow_keltner_range

    @classmethod
    def is_last_min_market_trend_bellow(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, trigger: float, is_int_round: bool, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # Set mean
        market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        k_market_date = 'market_date'
        # Get Dates
        open_times = list(marketprice.get_times())
        open_times.reverse()
        index_time = open_times[index]
        index_date = _MF.unix_to_date(index_time)
        sub_market_trend_df = market_trend_df[market_trend_df.index <= index_time]
        index_trend_date = sub_market_trend_df[k_market_date].iloc[index]
        index_rise_rate = sub_market_trend_df[k_edited_rise_rate].iloc[index]
        # Get Min
        neg_sub_df = sub_market_trend_df[sub_market_trend_df[edited_diff_rise_rate] < 0]
        last_min_index = neg_sub_df.index[-1]
        last_min_rise_rate = sub_market_trend_df.loc[last_min_index, k_edited_rise_rate]
        last_min_date = sub_market_trend_df.loc[last_min_index, k_market_date]
        # Check
        is_bellow = last_min_rise_rate*100 <= trigger*100
        # Report
        vars_map.put(is_bellow,             Map.condition,  f'last_min_market_trend_bellow_{period_str}_{window}[{index}]')
        vars_map.put(is_int_round,          Map.value,      f'last_min_market_trend_bellow_is_int_round_{period_str}_{window}[{index}]')
        vars_map.put(trigger,               Map.value,      f'last_min_market_trend_bellow_trigger_{period_str}_{window}[{index}]')
        vars_map.put(last_min_rise_rate,    Map.value,      f'last_min_market_trend_bellow_last_min_rise_rate_{period_str}_{window}[{index}]')
        vars_map.put(index_date,            Map.value,      f'last_min_market_trend_bellow_index_date_{period_str}_{window}[{index}]')
        vars_map.put(index_trend_date,      Map.value,      f'last_min_market_trend_bellow_index_trend_date_{period_str}_{window}[{index}]')
        vars_map.put(last_min_date,         Map.value,      f'last_min_market_trend_bellow_last_min_date_{period_str}_{window}[{index}]')
        vars_map.put(index_rise_rate,       Map.value,      f'last_min_market_trend_bellow_index_rise_rate_{period_str}_{window}[{index}]')
        return is_bellow

    @classmethod
    def is_market_trend_bellow(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, trigger: float, is_int_round: bool, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # Set trend
        market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        k_market_date = 'market_date'
        # Get values
        open_times = list(marketprice.get_times())
        open_times.reverse()
        index_time = open_times[index]
        index_date = _MF.unix_to_date(index_time)
        sub_market_trend_df = market_trend_df[market_trend_df.index <= index_time]
        index_trend_date = sub_market_trend_df[k_market_date].iloc[index]
        # Check
        index_rise_rate = sub_market_trend_df[k_edited_rise_rate].iloc[index]
        is_bellow = index_rise_rate*100 <= trigger*100
        # Report
        vars_map.put(is_bellow,         Map.condition,  f'market_trend_bellow_{period_str}_{window}[{index}]')
        vars_map.put(is_int_round,      Map.value,      f'market_trend_bellow_is_int_round_{period_str}_{window}[{index}]')
        vars_map.put(trigger,           Map.value,      f'market_trend_bellow_trigger_{period_str}_{window}[{index}]')
        vars_map.put(index_date,        Map.value,      f'market_trend_bellow_index_date_{period_str}_{window}[{index}]')
        vars_map.put(index_trend_date,  Map.value,      f'market_trend_bellow_index_trend_date_{period_str}_{window}[{index}]')
        vars_map.put(index_rise_rate,   Map.value,      f'market_trend_bellow_index_rise_rate_{period_str}_{window}[{index}]')
        return is_bellow

    @classmethod
    def is_tangent_market_trend_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, is_int_round: bool, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # Set mean
        market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        k_market_date = 'market_date'
        # Get values
        now_time = marketprice.get_time()
        now_date = _MF.unix_to_date(now_time)
        sub_mean_market_trend_df = market_trend_df[market_trend_df.index <= now_time]
        prev_index = index - 1
        now_trend_date = sub_mean_market_trend_df[k_market_date].iloc[index]
        prev_trend_date = sub_mean_market_trend_df[k_market_date].iloc[prev_index]
        # Check
        now_rise_rate = sub_mean_market_trend_df[k_edited_rise_rate].iloc[index]
        prev_rise_rate = sub_mean_market_trend_df[k_edited_rise_rate].iloc[prev_index]
        tangent_positive = now_rise_rate*100 > prev_rise_rate*100
        # Report
        vars_map.put(tangent_positive,  Map.condition,  f'tangent_market_trend_positive_{period_str}_{window}[{index}]')
        vars_map.put(is_int_round,      Map.value,      f'tangent_market_trend_positive_is_int_round_{period_str}_{window}[{index}]')
        vars_map.put(now_date,          Map.value,      f'tangent_market_trend_positive_now_date_{period_str}_{window}[{index}]')
        vars_map.put(now_trend_date,    Map.value,      f'tangent_market_trend_positive_now_trend_date_{period_str}_{window}[{index}]')
        vars_map.put(prev_trend_date,   Map.value,      f'tangent_market_trend_positive_prev_trend_date_{period_str}_{window}[{prev_index}]')
        vars_map.put(now_rise_rate,     Map.value,      f'tangent_market_trend_positive_now_rise_rate_{period_str}_{window}[{index}]')
        vars_map.put(prev_rise_rate,    Map.value,      f'tangent_market_trend_positive_prev_rise_rate_{period_str}_{window}[{prev_index}]')
        return tangent_positive

    @classmethod
    def is_tangent_market_trend_compare_zero(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, compare: str, index: int, is_int_round: bool, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # Set mean
        market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        k_market_date = 'market_date'
        # Get values
        now_time = marketprice.get_time()
        now_date = _MF.unix_to_date(now_time)
        sub_mean_market_trend_df = market_trend_df[market_trend_df.index <= now_time]
        prev_index = index - 1
        now_trend_date = sub_mean_market_trend_df[k_market_date].iloc[index]
        prev_trend_date = sub_mean_market_trend_df[k_market_date].iloc[prev_index]
        # Check
        now_rise_rate = sub_mean_market_trend_df[k_edited_rise_rate].iloc[index]
        prev_rise_rate = sub_mean_market_trend_df[k_edited_rise_rate].iloc[prev_index]
        tangent_positive = eval(f'{now_rise_rate*100} {compare} {prev_rise_rate*100}')
        # Report
        vars_map.put(tangent_positive,  Map.condition,  f'tangent_market_trend_{compare}_0_{period_str}_{window}[{index}]')
        vars_map.put(is_int_round,      Map.value,      f'tangent_market_trend_{compare}_0_is_int_round_{period_str}_{window}[{index}]')
        vars_map.put(now_date,          Map.value,      f'tangent_market_trend_{compare}_0_now_date_{period_str}_{window}[{index}]')
        vars_map.put(now_trend_date,    Map.value,      f'tangent_market_trend_{compare}_0_now_trend_date_{period_str}_{window}[{index}]')
        vars_map.put(prev_trend_date,   Map.value,      f'tangent_market_trend_{compare}_0_prev_trend_date_{period_str}_{window}[{prev_index}]')
        vars_map.put(now_rise_rate,     Map.value,      f'tangent_market_trend_{compare}_0_now_rise_rate_{period_str}_{window}[{index}]')
        vars_map.put(prev_rise_rate,    Map.value,      f'tangent_market_trend_{compare}_0_prev_rise_rate_{period_str}_{window}[{prev_index}]')
        return tangent_positive

    @classmethod
    def is_roi_compare_trigger(cls, vars_map: Map, compare: str, roi: float, trigger: float) -> bool:
        # Check
        roi_compare_trigger = eval(f'{roi} {compare} {trigger}')
        # Report
        vars_map.put(roi_compare_trigger,   Map.condition, f'is_roi_compare_trigger_{compare}')
        vars_map.put(roi,                   Map.value,     f'is_roi_compare_trigger_{compare}_roi')
        vars_map.put(trigger,               Map.value,     f'is_roi_compare_trigger_{compare}_trigger')
        vars_map.put(compare,               Map.value,     f'is_roi_compare_trigger_{compare}_compare')
        return roi_compare_trigger

    @classmethod
    def param_to_str(cls, params: dict) -> str:
        param_str = ''
        if len(params) > 0:
            for key, value in params.items():
                param_str += f'{key}={value}' if len(param_str) == 0 else f'_{key}={value}'
        return param_str

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trades: list[dict], trade: dict, buy_conditions: list, sell_conditions: list) -> None:
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            last_trade = trades[-1] if len(trades) > 0 else None
            buy_params = {}
            buy_params[Map.time] =  last_trade[Map.sell][Map.time] if last_trade is not None else 0
            buy_params[Map.roi] =   last_trade[Map.roi]() if last_trade is not None else 123
            can_buy, buy_condition, max_loss_price = cls.can_buy(broker, pair, marketprices, buy_params)
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_MARKET, exec_type=Map.open)
                cls._backtest_execute_trade(broker, marketprices, trade)
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_STOP_LIMIT, limit=max_loss_price, stop=max_loss_price)
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            close_price = marketprice.get_close()
            sell_params = {}
            sell_params[Map.fee] = buy_fee =    trade[Map.buy][Map.fee]
            sell_params[Map.buy] = buy_price =  trade[Map.buy][Map.execution]
            sell_params[Map.roi] =              _MF.progress_rate(close_price, buy_price) - buy_fee
            can_sell, sell_condition, sell_key, sell_prices = cls.can_sell(broker, pair, marketprices, sell_params)
            sell_condition = cls._backtest_condition_add_prefix(sell_condition, pair, marketprice)
            sell_conditions.append(sell_condition)
            cls._backtest_update_trade(trade, Map.sell, Order.STATUS_CANCELED) if trade[Map.sell] is not None else None
            if (sell_key == Map.limit):
                sell_limit = sell_prices[sell_key]
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_LIMIT, limit=sell_limit)
            elif (sell_key == Map.stop):
                sell_stop = sell_prices[sell_key]
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_STOP_LIMIT, limit=sell_stop, stop=sell_stop)
            cls._backtest_execute_trade(broker, marketprices, trade) if trade[Map.sell] is not None else None
            if can_sell and ((trade[Map.sell] is None) or (trade[Map.sell][Map.status] != Order.STATUS_COMPLETED)):
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.close)
        return trade

    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST UP
    # ––––––––––––––––––––––––––––––––––––––––––– STATIC DOWN

    @classmethod
    def get_market_trend(cls, period: int) -> pd.DataFrame:
        _MF.check_type(period, int)
        k_market_trends = cls.K_MARKET_TRENDS
        stage = Config.get(Config.STAGE_MODE)
        if stage == Config.STAGE_1:
            _stack = cls.get_stack()
            market_trend_df = _stack.get(k_market_trends, period)
            if market_trend_df is None:
                market_trend_file = f"content/storage/MarketPrice/histories/stock/market_trend/supertrend/{period}.csv"
                project_dir = FileManager.get_project_directory()
                market_trend_df = pd.read_csv(project_dir + market_trend_file, index_col=0)
                _stack.put(market_trend_df, k_market_trends, period)
        else:
            raise Exception(f"Behavior not implemeted for this stage '{stage}'")
        return market_trend_df

    @classmethod
    def get_edited_market_trend_keys(cls, is_int_round: bool, window: int = None) -> tuple[str,str]:
        k_rise_rate = 'rise_rate'
        k_edited_rise_rate = f'{k_rise_rate}_{is_int_round}_{window}'
        edited_diff_rise_rate = f'diff_{k_edited_rise_rate}'
        return k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate

    @classmethod
    def get_edited_market_trend(cls, period: int, is_int_round: bool, window: int = None) -> pd.DataFrame:
        k_mean_market_trends = cls.K_EDITED_MARKET_TRENDS
        stack_keys = [k_mean_market_trends, period]
        stack = cls.get_stack()
        edited_market_trend_df = stack.get(*stack_keys)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        if (edited_market_trend_df is None) or (k_edited_rise_rate not in edited_market_trend_df.columns):
            if edited_market_trend_df is None:
                edited_market_trend_df = cls.get_market_trend(period).copy(deep=True)
                stack.put(edited_market_trend_df, *stack_keys)
            is_window_set = window is not None
            float_to_int = lambda x : int(x*100)/100 if not _MF.is_nan(x) else x
            k_edited_keys = Map()
            k_edited_diff_keys = Map()
            gened_keys = [
                [*cls.get_edited_market_trend_keys(True,    window)],
                [*cls.get_edited_market_trend_keys(True,    None)],
                [*cls.get_edited_market_trend_keys(False,   window)],
                [*cls.get_edited_market_trend_keys(False,   None)],
            ]
            k_edited_keys.put(gened_keys[0][1],   True,   window)
            k_edited_keys.put(gened_keys[1][1],   True,   None)
            k_edited_keys.put(gened_keys[2][1],   False,  window)
            k_edited_keys.put(gened_keys[3][1],   False,  None)
            #
            k_edited_diff_keys.put(gened_keys[0][2],   True,   window)
            k_edited_diff_keys.put(gened_keys[1][2],   True,   None)
            k_edited_diff_keys.put(gened_keys[2][2],   False,  window)
            k_edited_diff_keys.put(gened_keys[3][2],   False,  None)
            '''
            is_int_round=False AND is_window_set=True
            '''
            if is_window_set:
                combin_keys =       [False, window]
                k_edited_key =      k_edited_keys.get(*combin_keys)
                k_diff_edited_key = k_edited_diff_keys.get(*combin_keys)
                edited_market_trend_df[k_edited_key] =       edited_market_trend_df[k_rise_rate].rolling(window=window).mean()
                edited_market_trend_df[k_diff_edited_key] =  edited_market_trend_df[k_edited_key].diff()
            '''
            is_int_round=True AND is_window_set=False
            '''
            combin_keys = [True, None]
            k_edited_key =       k_edited_keys.get(*combin_keys)
            k_diff_edited_key =  k_edited_diff_keys.get(*combin_keys)
            edited_market_trend_df[k_edited_key] =       _MF.df_apply(edited_market_trend_df, [k_rise_rate], float_to_int)[k_rise_rate]
            edited_market_trend_df[k_diff_edited_key] =  edited_market_trend_df[k_edited_key].diff()
            '''
            is_int_round=True AND is_window_set=True
            '''
            if is_window_set:
                combin_keys = [True, window]
                k_edited_key =       k_edited_keys.get(*combin_keys)
                k_diff_edited_key =  k_edited_diff_keys.get(*combin_keys)
                k_mean_rise_rate = k_edited_keys.get(False, window)
                edited_market_trend_df[k_edited_key] =      _MF.df_apply(edited_market_trend_df, [k_mean_rise_rate], float_to_int)[k_mean_rise_rate]
                edited_market_trend_df[k_diff_edited_key] = edited_market_trend_df[k_edited_key].diff()
            '''
            is_int_round=False AND is_window_set=False
            '''
            combin_keys = [False, None]
            k_edited_key =       k_edited_keys.get(*combin_keys)
            k_diff_edited_key =  k_edited_diff_keys.get(*combin_keys)
            edited_market_trend_df[k_edited_key] =      edited_market_trend_df[k_rise_rate]
            edited_market_trend_df[k_diff_edited_key] = edited_market_trend_df[k_edited_key].diff()
        return edited_market_trend_df

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Solomon.__new__(Solomon)
        exec(MyJson.get_executable())
        return instance

    # ––––––––––––––––––––––––––––––––––––––––––– STATIC UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
    