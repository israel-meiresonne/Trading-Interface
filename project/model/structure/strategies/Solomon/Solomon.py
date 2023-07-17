import time
from typing import Callable, List

import numpy as np
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
    PREFIX_ID =                 'solomon_'
    _SLEEP_TRADE =              30
    _MAX_POSITION =             10
    KELTER_SUPPORT =            None
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_15MIN
        ]
    PSAR_1 =                    dict(step=.6, max_step=.6)
    EMA_PARAMS_1 =              {'n_period': 5}
    K_BUY_SELL_CONDITION =      'K_BUY_SELL_CONDITION'
    K_EDITED_MARKET_TRENDS =    'K_EDITED_MARKET_TRENDS'
    COMPARATORS =               ['==', '>', '<', '<=', '>=']

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
        stack = self.get_stack()
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
            broker_event = Broker.EVENT_NEW_PRICE
            broker_callback = self._callback_trade
            broker_pairs = self.get_broker_pairs()
            required_periods = self._REQUIRED_PERIODS
            strategy_streams = broker.generate_streams(broker_pairs, required_periods)
            stream_1min = broker.generate_streams(broker_pairs, [Broker.PERIOD_1MIN])
            all_streams = _MF.remove_duplicates([*strategy_streams, *stream_1min])
            if (not broker.is_active()) or (not broker.exist_event_streams(broker_event, broker_callback, all_streams)):
                broker.add_streams(all_streams)
                broker.add_event_streams(broker_event, broker_callback, stream_1min)
                added_streams = broker.get_streams()
                added_pairs = list(added_streams.keys())
                self._set_broker_pairs(added_pairs)
        stack_key = self.K_BUY_SELL_CONDITION
        if stack.get(stack_key) is not None:
            stack_copy = stack.get(stack_key).copy()
            del stack.get_map()[stack_key]
            for file, datas_dict in stack_copy.items():
                fields =    datas_dict[Map.column]
                rows =      datas_dict[Map.content]
                FileManager.write_csv(file, fields, rows, overwrite=False, make_dir=True)

    def _callback_trade(self, params: dict, marketprices: Map = None) -> None:
        def explode_params(params: dict) -> tuple[str, int, Pair, int, np.ndarray]:
            return tuple(params.values())
        def get_position(pair: Pair) -> HandTrade:
            return self.get_position(pair) if self.exist_position(pair) else None
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
        def is_pair_allowed(stream_pair: Pair) -> bool:
            stack = self.get_stack()
            k_broker_pair = Map.key(Map.broker, Map.pair)
            k_broker_pair_dict = Map.key(Map.broker, Map.pair, dict.__name__)
            k_broker_pair_size = Map.key(Map.broker, Map.pair, Map.size)
            k_broker_pair_id = Map.key(Map.broker, Map.pair, Map.id)
            broker_pair_size = stack.get(k_broker_pair, k_broker_pair_size)
            broker_pair_id = stack.get(k_broker_pair, k_broker_pair_id)
            broker_pairs = self.get_broker_pairs()
            if (broker_pair_size is None) \
                or (broker_pair_id is None) \
                or ((len(broker_pairs) != broker_pair_size) \
                or ((self.get_pair() is None) and (id(broker_pairs) != broker_pair_id))):
                broker_pair_dict = dict.fromkeys(broker_pairs)
                stack.put(broker_pair_dict,     k_broker_pair, k_broker_pair_dict)
                stack.put(len(broker_pairs),    k_broker_pair, k_broker_pair_size)
                stack.put(id(broker_pairs),     k_broker_pair, k_broker_pair_id)
            broker_pair_dict = stack.get(k_broker_pair, k_broker_pair_dict)
            return stream_pair in broker_pair_dict
        # # #
        period_1min = Broker.PERIOD_1MIN
        event, event_time, pair, event_period, market_row = explode_params(params)
        position = get_position(pair)
        if ((not self.is_max_position_reached()) or (position is not None)):
            broker = self.get_broker()
            marketprices = Map() if marketprices is None else marketprices
            buy_reports = []
            sell_reports = []
            loop_start_date = _MF.unix_to_date(event_time)
            unix_time = event_time if (Config.get(Config.STAGE_MODE) == Config.STAGE_1) else _MF.get_timestamp()
            turn_start_date = _MF.unix_to_date(unix_time)
            current_func = self._callback_trade.__name__
            if (position is None) or (not position.is_executed(Map.buy)):
                last_position = self.get_last_position(pair)
                buy_datas = {}
                buy_datas[Map.buy] = int(last_position.get_buy_order().get_execution_time()/1000) if last_position is not None else None
                can_buy, buy_report = self.can_buy(broker, pair, marketprices, buy_datas)
                report_buy_limit = -1
                # Report Buy
                buy_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                buy_report = self._new_row_condition(buy_report, current_func, loop_start_date, turn_start_date, buy_marketprice_1min, pair, can_buy, limit=report_buy_limit)
                buy_reports.append(buy_report)
                if can_buy:
                    self.buy(pair, Order.TYPE_MARKET, marketprices=marketprices)
            elif position.has_position():
                # Prepare datas
                sell_datas = {}
                buy_order = position.get_buy_order()
                buy_price = buy_order.get_execution_price()
                buy_fee = buy_order.get_fee(buy_price.get_asset())
                buy_amount = buy_order.get_executed_amount()
                sell_datas[Map.time] =      int(buy_order.get_execution_time()/1000)
                sell_datas[Map.buy] =       buy_price.get_value()
                sell_datas[Map.maximum] =   position.extrem_prices(broker).get(Map.maximum)
                sell_datas[Map.fee] =       buy_fee/buy_amount
                # Ask to sell
                can_sell, sell_report = self.can_sell(broker, pair, marketprices, sell_datas)
                # Report Sell
                sell_marketprice_1min = self._marketprice(broker, pair, period_1min, marketprices)
                sell_report = self._new_row_condition(sell_report, current_func, loop_start_date, turn_start_date, sell_marketprice_1min, pair, can_sell, -1)
                sell_reports.append(sell_report)
                # Check
                if can_sell:
                    self.sell(pair, Order.TYPE_MARKET, marketprices=marketprices)
                    self._add_last_position_id(position.get_id())
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
        streams = broker.get_event_streams()
        for event in Broker.EVENTS:
            broker.remove_event_streams(event, self._callback_trade, streams)
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
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map, datas: dict) -> tuple[bool, dict]:
        KELTNER_PARAMS_1 = {'multiple': 0.5}
        KELTNER_PARAMS_2 = {'multiple': 0.25}
        TRIGGER_KELTNER = 1/100
        def has_bought_since_negative_tangent_ema(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, last_buy_time: int, ema_params: dict = {}) -> bool:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            marketprice_df = marketprice.to_pd().copy()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            now_time = marketprice.get_time()
            index = -1
            prev_index = index - 1
            # EMA
            ema = marketprice.get_ema(**ema_params)
            ema = list(ema)
            ema.reverse()
            marketprice_df[Map.ema] = pd.Series(ema, index=marketprice_df.index)
            # Cook
            k_ema_diff = Map.key(Map.ema, 'diff')
            marketprice_df[k_ema_diff] = marketprice_df[Map.ema].diff()
            time_last_neg_ema = marketprice_df[marketprice_df[k_ema_diff] < 0][Map.time].iloc[-1]
            # Check
            has_bought = bool(time_last_neg_ema <= last_buy_time)
            # Put
            param_str = _MF.param_to_str(ema_params)
            k_base = f'has_bought_since_negative_tangent_ema_{period_str}_{param_str}'
            vars_map.put(has_bought,                                        Map.condition,  k_base)
            vars_map.put(_MF.unix_to_date(now_time),                        Map.value,      f'{k_base}_now_date')
            vars_map.put(_MF.unix_to_date(last_buy_time),                   Map.value,      f'{k_base}_last_buy_date')
            vars_map.put(_MF.unix_to_date(time_last_neg_ema),               Map.value,      f'{k_base}_last_ema_neg_date')
            vars_map.put(ema[index],                                        Map.value,      f'{k_base}_[{index}]')
            vars_map.put(ema[prev_index],                                   Map.value,      f'{k_base}_[{prev_index}]')
            vars_map.put(marketprice_df.loc[time_last_neg_ema, Map.ema],    Map.value,      f'{k_base}_ema_of_last_neg')
            vars_map.put(marketprice_df.loc[time_last_neg_ema, k_ema_diff], Map.value,      f'{k_base}_ema_diff_of_last_neg')
            return has_bought
        vars_map = Map()
        period_1min =   Broker.PERIOD_1MIN
        period_15min =  Broker.PERIOD_15MIN
        periods = [
            period_1min,
            period_15min
        ]
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in periods}
        # Params
        last_buy_time = datas[Map.buy] if datas[Map.buy] is not None else 0 # in second
        # Params
        now_index = -1
        prev_index_2 =  -2
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
            {Map.callback: has_bought_since_negative_tangent_ema,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, last_buy_time=last_buy_time, ema_params=cls.EMA_PARAMS_1)},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_macd_line_positive,               Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_ema_positive,             Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, ema_params=cls.EMA_PARAMS_1)},
            {Map.callback: cls.compare_exetrem_ema_and_keltner,     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, comapare='<=', ema_exetrem=Map.minimum, keltner_line=Map.low, ema_params=cls.EMA_PARAMS_1, keltner_params=KELTNER_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=prev_index_2, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_price_deep_enough,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, keltner_line=Map.high, macd_line=Map.histogram, keltner_params=KELTNER_PARAMS_2, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_ema_positive,             Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, ema_params=cls.EMA_PARAMS_1)},
            {Map.callback: cls.compare_exetrem_ema_and_keltner,     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, comapare='<=', ema_exetrem=Map.minimum, keltner_line=Map.low, ema_params=cls.EMA_PARAMS_1, keltner_params=KELTNER_PARAMS_1)},
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        can_buy = not has_bought_since_negative_tangent_ema(**func_and_params[0][Map.param])
        if can_buy:
            superMACD = cls.is_supertrend_rising(**func_and_params[1][Map.param]), cls.is_macd_line_positive(**func_and_params[2][Map.param])
            if superMACD[0] and superMACD[1]:
                can_buy = can_buy \
                    and cls.is_tangent_ema_positive(**func_and_params[3][Map.param]) \
                    and cls.compare_exetrem_ema_and_keltner(**func_and_params[4][Map.param])
            elif not superMACD[1]: # [TRUE, FALSE] OR [FALSE, FALSE] => [Any, FALSE] => not [Any, FALSE]][1]
                can_buy = can_buy \
                    and cls.is_tangent_macd_line_positive(**func_and_params[5][Map.param]) \
                    and cls.is_tangent_macd_line_positive(**func_and_params[6][Map.param]) \
                    and cls.is_tangent_macd_line_positive(**func_and_params[7][Map.param]) \
                    and cls.is_price_deep_enough(**func_and_params[8][Map.param]) \
                    and cls.is_tangent_ema_positive(**func_and_params[9][Map.param]) \
                    and cls.compare_exetrem_ema_and_keltner(**func_and_params[10][Map.param])
            else:
                can_buy = False
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_buy, vars_map)
        return can_buy, report

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map, datas: dict) -> tuple[bool, dict]:
        def has_supertrend_switched_down(vars_map: Map, pair: Pair, period: int, buy_time: int, index: int) -> bool:
            """
            To check if supertrend has switched down since buy
            """
            if index >= 0:
                raise ValueError(f"Index must be negative, instead '{index}'")
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            now_time = marketprice.get_time()
            # Price
            marketprice_df = marketprice.to_pd().copy()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # Supertrends
            supertrends = list(marketprice.get_super_trend())
            supertrends.reverse()
            marketprice_df[Map.supertrend] = pd.Series(supertrends, index=marketprice_df.index)
            # Prepare
            buy_time_round = _MF.round_time(buy_time, period)
            index_time = marketprice_df[Map.time].iloc[index]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time_round) & (marketprice_df[Map.time] <= index_time)]
            rising_zone_df = sub_marketprice_df[sub_marketprice_df[Map.close] > sub_marketprice_df[Map.supertrend]]
            # Check
            has_switched = bool((rising_zone_df.shape[0] > 0) and (sub_marketprice_df.loc[index_time, Map.close] < sub_marketprice_df.loc[index_time, Map.supertrend]))
            # Put
            trade_zone_start =  _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[0])
            trade_zone_end =    _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[-1])
            rising_zone_start = _MF.unix_to_date(rising_zone_df[Map.time].iloc[0]) if rising_zone_df.shape[0] > 0 else None
            rising_zone_end =   _MF.unix_to_date(rising_zone_df[Map.time].iloc[-1]) if rising_zone_df.shape[0] > 0 else None
            vars_map.put(has_switched,                      Map.condition,  f'has_supertrend_switched_down_{period_str}[{index}]')
            vars_map.put(_MF.unix_to_date(now_time),        Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_now_date')
            vars_map.put(_MF.unix_to_date(index_time),      Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_index_date')            
            vars_map.put(_MF.unix_to_date(buy_time),        Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_buy_date')
            vars_map.put(_MF.unix_to_date(buy_time_round),  Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_buy_date_round')
            vars_map.put(trade_zone_start,                  Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_trade_zone_start')
            vars_map.put(trade_zone_end,                    Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_trade_zone_end')
            vars_map.put(rising_zone_start,                 Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_rising_zone_start')
            vars_map.put(rising_zone_end,                   Map.value,      f'has_supertrend_switched_down_{period_str}[{index}]_rising_zone_end')
            return has_switched
        def has_macd_line_switched_positive(vars_map: Map, pair: Pair, period: int, buy_time: int, index: int, macd_line: str, macd_params: dict = {}) -> bool:
            """
            To check if MACD has switched up since buy
            """
            if index >= 0:
                raise ValueError(f"Index must be negative, instead '{index}'")
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            now_time = marketprice.get_time()
            # Price
            marketprice_df = marketprice.to_pd().copy()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # MACD
            macd = list(marketprice.get_macd(**macd_params).get_map()[macd_line])
            macd.reverse()
            marketprice_df[Map.macd] = pd.Series(macd, index=marketprice_df.index)
            # Prepare
            buy_time_round = _MF.round_time(buy_time, period)
            index_time = marketprice_df[Map.time].iloc[index]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time_round) & (marketprice_df[Map.time] <= index_time)]
            rising_zone_df = sub_marketprice_df[sub_marketprice_df[Map.macd] > 0]
            # Check
            has_switched = (rising_zone_df.shape[0] > 0)
            # Put
            trade_zone_start =  _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[0])
            trade_zone_end =    _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[-1])
            rising_zone_start = _MF.unix_to_date(rising_zone_df[Map.time].iloc[0]) if rising_zone_df.shape[0] > 0 else None
            rising_zone_end =   _MF.unix_to_date(rising_zone_df[Map.time].iloc[-1]) if rising_zone_df.shape[0] > 0 else None
            param_str = _MF.param_to_str(macd_params)
            prefix = f'has_{macd_line}_switched_positive_{period_str}_{param_str}_[{index}]'
            vars_map.put(has_switched,                      Map.condition,  prefix)
            vars_map.put(_MF.unix_to_date(now_time),        Map.value,      f'{prefix}_now_date')
            vars_map.put(_MF.unix_to_date(index_time),      Map.value,      f'{prefix}_index_date')            
            vars_map.put(_MF.unix_to_date(buy_time),        Map.value,      f'{prefix}_buy_date')
            vars_map.put(_MF.unix_to_date(buy_time_round),  Map.value,      f'{prefix}_buy_date_round')
            vars_map.put(trade_zone_start,                  Map.value,      f'{prefix}_trade_zone_start')
            vars_map.put(trade_zone_end,                    Map.value,      f'{prefix}_trade_zone_end')
            vars_map.put(rising_zone_start,                 Map.value,      f'{prefix}_rising_zone_start')
            vars_map.put(rising_zone_end,                   Map.value,      f'{prefix}_rising_zone_end')
            return has_switched
        def has_macd_line_switched_positive_then_negative(vars_map: Map, pair: Pair, period: int, buy_time: int, index: int, macd_line: str, macd_params: dict = {}) -> bool:
            """
            To check if MACD has switched down since buy
            """
            if index >= 0:
                raise ValueError(f"Index must be negative, instead '{index}'")
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            now_time = marketprice.get_time()
            # Price
            marketprice_df = marketprice.to_pd().copy()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # MACD
            macd = list(marketprice.get_macd(**macd_params).get_map()[macd_line])
            macd.reverse()
            marketprice_df[Map.macd] = pd.Series(macd, index=marketprice_df.index)
            # Prepare
            buy_time_round = _MF.round_time(buy_time, period)
            index_time = marketprice_df[Map.time].iloc[index]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time_round) & (marketprice_df[Map.time] <= index_time)]
            rising_zone_df = sub_marketprice_df[sub_marketprice_df[Map.macd] > 0]
            rising_zone_end_time =  None
            rising_zone_start =     None
            rising_zone_end =       None
            if rising_zone_df.shape[0] > 0:
                rising_zone_end_time = rising_zone_df[Map.time].iloc[-1]
                rising_zone_start = _MF.unix_to_date(rising_zone_df[Map.time].iloc[0])
                rising_zone_end =   _MF.unix_to_date(rising_zone_end_time)
            # Check
            has_switched_up_down = bool((rising_zone_df.shape[0] > 0) and (rising_zone_end_time < index_time))
            # Put
            trade_zone_start =  _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[0])
            trade_zone_end =    _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[-1])
            param_str = _MF.param_to_str(macd_params)
            prefix = f'has_{macd_line}_switched_positive_then_negative_{period_str}_{param_str}_[{index}]'
            vars_map.put(has_switched_up_down,              Map.condition,  prefix)
            vars_map.put(_MF.unix_to_date(now_time),        Map.value,      f'{prefix}_now_date')
            vars_map.put(_MF.unix_to_date(index_time),      Map.value,      f'{prefix}_index_date')
            vars_map.put(_MF.unix_to_date(buy_time),        Map.value,      f'{prefix}_buy_date')
            vars_map.put(_MF.unix_to_date(buy_time_round),  Map.value,      f'{prefix}_buy_date_round')
            vars_map.put(trade_zone_start,                  Map.value,      f'{prefix}_trade_zone_start')
            vars_map.put(trade_zone_end,                    Map.value,      f'{prefix}_trade_zone_end')
            vars_map.put(rising_zone_start,                 Map.value,      f'{prefix}_rising_zone_start')
            vars_map.put(rising_zone_end,                   Map.value,      f'{prefix}_rising_zone_end')
            return has_switched_up_down
        def can_stop_losses(vars_map: Map, stop_trigger: float, buy_price: float, max_price: float, min_profit: float, buy_fee_rate: float, sell_fee_rate: float) -> bool:
            stop_price = None
            # Prepare
            max_roi = (max_price - buy_price) / buy_price
            # Check
            can_stop = max_roi >= stop_trigger
            if can_stop:
                stop_price = buy_price * (1 + min_profit + buy_fee_rate + sell_fee_rate)
            # Put
            vars_map.put(can_stop,      Map.condition,  k_base_can_stop)
            vars_map.put(stop_trigger,  Map.value,      f'{k_base_can_stop}_stop_trigger')
            vars_map.put(buy_price,     Map.value,      f'{k_base_can_stop}_buy_price')
            vars_map.put(max_price,     Map.value,      f'{k_base_can_stop}_max_price')
            vars_map.put(min_profit,    Map.value,      f'{k_base_can_stop}_min_profit')
            vars_map.put(max_roi,       Map.value,      f'{k_base_can_stop}_max_roi')
            vars_map.put(buy_fee_rate,  Map.value,      f'{k_base_can_stop}_buy_fee_rate')
            vars_map.put(sell_fee_rate, Map.value,      f'{k_base_can_stop}_sell_fee_rate')
            vars_map.put(stop_price,    Map.value,      k_stop_price)
            return can_stop
        def can_take_profit(vars_map: Map, profit_trigger: float, buy_price: float, now_close: float, final_roi: float) -> tuple[bool, dict, float, float]:
            limit_price = None
            # Prepare
            now_roi = (now_close - buy_price) / buy_price
            # Check
            can_take = now_roi >= profit_trigger
            if can_take:
                limit_price = buy_price * (1 + final_roi)
            # Put
            vars_map.put(can_take,          Map.condition,  k_base_can_take)
            vars_map.put(profit_trigger,    Map.value,      f'{k_base_can_take}_profit_trigger')
            vars_map.put(buy_price,         Map.value,      f'{k_base_can_take}_buy_price')
            vars_map.put(now_close,         Map.value,      f'{k_base_can_take}_now_close')
            vars_map.put(final_roi,         Map.value,      f'{k_base_can_take}_final_roi')
            vars_map.put(now_roi,           Map.value,      f'{k_base_can_take}_now_roi')
            vars_map.put(limit_price,       Map.value,      k_limit_price)
            return can_take
        def is_max_roi_reached(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, buy_time: int, buy_price: float, max_price: float) -> bool:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            now_time = marketprice.get_time()
            # Keys
            k_keltner_high =    Map.key(Map.keltner, Map.high)
            k_keltner_roi =     Map.key(Map.keltner, Map.roi)
            # Price
            marketprice_df = marketprice.to_pd().copy()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # Keltner
            keltner_map = marketprice.get_keltnerchannel(multiple=1)
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            marketprice_df[k_keltner_high] = pd.Series(keltner_high, index=marketprice_df.index)
            # Prepare
            max_roi = (max_price - buy_price) / buy_price
            marketprice_df[k_keltner_roi] = (marketprice_df[k_keltner_high] - marketprice_df[Map.close]) / marketprice_df[Map.close]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time) & (marketprice_df[Map.time] <= now_time)]
            max_roi_trigger = min(sub_marketprice_df[k_keltner_roi])
            # Check
            max_roi_reached = max_roi >= max_roi_trigger
            # Put
            k_base = f'is_max_roi_reached_{period_str}'
            trade_zone_start =  _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[0])
            trade_zone_end =    _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[-1])
            vars_map.put(max_roi_reached,               Map.condition,  k_base)
            vars_map.put(_MF.unix_to_date(buy_time),    Map.value,      f'{k_base}_buy_date')
            vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_now_date')
            vars_map.put(max_roi_trigger,               Map.value,      f'{k_base}_max_roi_trigger')
            vars_map.put(buy_price,                     Map.value,      f'{k_base}_buy_price')
            vars_map.put(max_price,                     Map.value,      f'{k_base}_max_price')
            vars_map.put(max_roi,                       Map.value,      f'{k_base}_max_roi')
            vars_map.put(buy_fee_rate,                  Map.value,      f'{k_base}_buy_fee_rate')
            vars_map.put(trade_zone_start,              Map.value,      f'{k_base}_trade_zone_start')
            vars_map.put(trade_zone_end,                Map.value,      f'{k_base}_trade_zone_end')
            return max_roi_reached
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        periods = [
            period_1min
        ]
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in periods}
        # Datas
        buy_time = _MF.round_time(datas[Map.time], period_1min)  # in second
        buy_price = datas[Map.buy]
        position_max_price = datas[Map.maximum]
        buy_fee_rate = datas[Map.fee]
        fees = broker.get_trade_fee(pair)
        maker_fee = fees.get(Map.maker)
        trade_fees = buy_fee_rate + maker_fee
        # Params
        now_index = -1
        k_base_can_stop = 'can_stop_losses'
        k_base_can_take = 'can_take_profit'
        k_stop_price = f'{k_base_can_stop}_stop_price'
        k_limit_price = f'{k_base_can_take}_limit_price'
        now_close = marketprice_1min_pd[Map.close].iloc[-1]
        # Add price
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-1],    Map.value, f'open_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-2],    Map.value, f'open_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-1],     Map.value, f'low_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-2],     Map.value, f'low_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-1],    Map.value, f'high_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-2],    Map.value, f'high_{period_strs[period_1min]}[-2]')
        vars_map.put(now_close,                                 Map.value, f'close_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-2],   Map.value, f'close_{period_strs[period_1min]}[-2]')
        # Set header
        this_func = cls.can_sell
        func_and_params = [
            {Map.callback: is_max_roi_reached,                              Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, buy_time=buy_time, buy_price=buy_price, max_price=position_max_price)},
            {Map.callback: cls.is_tangent_rsi_positive,                     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)},
            {Map.callback: has_macd_line_switched_positive,                 Map.param: dict(vars_map=vars_map, pair=pair, period=period_1min, buy_time=buy_time, index=now_index, macd_line=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: has_supertrend_switched_down,                    Map.param: dict(vars_map=vars_map, pair=pair, period=period_1min, buy_time=buy_time, index=now_index)},
            {Map.callback: has_macd_line_switched_positive_then_negative,   Map.param: dict(vars_map=vars_map, pair=pair, period=period_1min, buy_time=buy_time, index=now_index, macd_line=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_supertrend_rising,                        Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_tangent_ema_positive,                     Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, ema_params=cls.EMA_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,               Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.macd)},
            {Map.callback: cls.compare_keltner_floor_and_rate,              Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, comparator='<', keltner_line=Map.low, buy_price=buy_price, rate=trade_fees)},
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        if is_max_roi_reached(**func_and_params[0][Map.param]):
            can_sell = not cls.is_tangent_rsi_positive(**func_and_params[1][Map.param])
        elif has_macd_line_switched_positive(**func_and_params[2][Map.param]):
            can_sell = has_supertrend_switched_down(**func_and_params[3][Map.param]) \
                or has_macd_line_switched_positive_then_negative(**func_and_params[4][Map.param]) \
                and not cls.is_supertrend_rising(**func_and_params[5][Map.param])
        else:
            can_sell = not cls.is_tangent_ema_positive(**func_and_params[6][Map.param]) \
                and not cls.is_tangent_macd_line_positive(**func_and_params[7][Map.param]) \
                and cls.compare_keltner_floor_and_rate(**func_and_params[8][Map.param])
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_sell, vars_map)
        return can_sell, report

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
    def is_keltner_roi_above_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, trigger_keltner: float, index: int) -> bool:
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
        keltner_roi = _MF.progress_rate(keltner_high[index], keltner_low[index])
        keltner_roi_above_trigger = keltner_roi >= trigger_keltner
        # Put
        vars_map.put(keltner_roi_above_trigger, Map.condition,  f'is_keltner_roi_above_trigger_{period_str}[{index}]')
        vars_map.put(trigger_keltner,           Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_trigger_keltner')
        vars_map.put(keltner_roi,               Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_keltner_roi')
        vars_map.put(keltner_low[-1],           Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_low[-1]')
        vars_map.put(keltner_low[-2],           Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_low[-2]')
        vars_map.put(keltner_low[index],        Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_low[{index}]')
        vars_map.put(keltner_middle[-1],        Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_middle[-1]')
        vars_map.put(keltner_middle[-2],        Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_middle[-2]')
        vars_map.put(keltner_middle[index],     Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_middle[{index}]')
        vars_map.put(keltner_high[-1],          Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_high[-1]')
        vars_map.put(keltner_high[-2],          Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_high[-2]')
        vars_map.put(keltner_high[index],       Map.value,      f'is_keltner_roi_above_trigger_{period_str}[{index}]_high[{index}]')
        return keltner_roi_above_trigger

    @classmethod
    def is_compare_price_and_keltner_line(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, compare: str, price_line: str, keltner_line: str, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
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
        marketprice.reset_collections()
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
    def compare_keltner_floor_and_rate(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, \
        comparator: str, keltner_line: str, buy_price: float, rate: float) -> bool:
        comparators = cls.COMPARATORS
        _MF.check_allowed_values(comparator, comparators)
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        keltner_map = marketprice.get_keltnerchannel(multiple=1)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Prapare
        keltner_floor = (keltner[index] - buy_price) / buy_price
        # Check
        if comparator == comparators[0]:
            check = keltner_floor == rate
        elif comparator == comparators[1]:
            check = keltner_floor > rate
        elif comparator == comparators[2]:
            check = keltner_floor < rate
        elif comparator == comparators[3]:
            check = keltner_floor <= rate
        elif comparator == comparators[4]:
            check = keltner_floor >= rate
        # Put
        k_base = f'compare_keltner_floor_{keltner_line}_{comparator}_{period_str}[{index}]'
        prev_index = index - 1
        vars_map.put(check,                         Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_date')
        vars_map.put(buy_price,                     Map.value,      f'{k_base}_buy_price')
        vars_map.put(keltner_floor,                 Map.value,      f'{k_base}_keltner_floor')
        vars_map.put(rate,                          Map.value,      f'{k_base}_rate')
        vars_map.put(keltner[index],                Map.value,      f'{k_base}_keltner_[{index}]')
        vars_map.put(keltner[prev_index],           Map.value,      f'{k_base}_keltner_[{prev_index}]')
        return check

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
        is_bellow = bool(last_min_rise_rate*100 <= trigger*100)
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
        is_bellow = bool(index_rise_rate*100 <= trigger*100)
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
        tangent_positive = bool(now_rise_rate*100 > prev_rise_rate*100)
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
    def is_macd_line_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, line_name: str, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        macd_lines = marketprice.get_macd(**macd_params).get_map()
        macd_line = list(macd_lines[line_name])
        macd_line.reverse()
        # Check
        prev_index = index - 1
        macd_line_positive = macd_line[index] > 0
        # Put
        param_str = _MF.param_to_str(macd_params)
        vars_map.put(macd_line_positive,            Map.condition,  f'is_{line_name}_positive_{period_str}[{index}]_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_date')
        vars_map.put(macd_line[index],              Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_[{index}]')
        vars_map.put(macd_line[prev_index],         Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_[{prev_index}]')
        return macd_line_positive

    @classmethod
    def is_tangent_macd_line_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, line_name: str, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        macd_lines = marketprice.get_macd(**macd_params).get_map()
        macd_line = list(macd_lines[line_name])
        macd_line.reverse()
        # Check
        prev_index = index - 1
        tangent_macd_line_positive = macd_line[index] > macd_line[prev_index]
        # Put
        param_str = _MF.param_to_str(macd_params)
        vars_map.put(tangent_macd_line_positive,    Map.condition,  f'is_tangent_{line_name}_positive_{period_str}[{index}]_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'is_tangent_{line_name}_positive_{period_str}[{index}]_{param_str}_date')
        vars_map.put(macd_line[index],              Map.value,      f'is_tangent_{line_name}_positive_{period_str}[{index}]_{param_str}_[{index}]')
        vars_map.put(macd_line[prev_index],         Map.value,      f'is_tangent_{line_name}_positive_{period_str}[{index}]_{param_str}_[{prev_index}]')
        return tangent_macd_line_positive

    @classmethod
    def is_tangent_ema_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, ema_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        ema = marketprice.get_ema(**ema_params)
        ema = list(ema)
        ema.reverse()
        # Check
        prev_index = index - 1
        tangent_ema_positive = ema[index] > ema[prev_index]
        # Put
        param_str = _MF.param_to_str(ema_params)
        vars_map.put(tangent_ema_positive,          Map.condition,  f'is_tangent_ema_positive_{period_str}[{index}]_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'is_tangent_ema_positive_{period_str}[{index}]_{param_str}_date')
        vars_map.put(ema[index],                    Map.value,      f'is_tangent_ema_positive_{period_str}[{index}]_{param_str}_[{index}]')
        vars_map.put(ema[prev_index],               Map.value,      f'is_tangent_ema_positive_{period_str}[{index}]_{param_str}_[{prev_index}]')
        return tangent_ema_positive

    @classmethod
    def is_tangent_rsi_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, rsi_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        rsi = marketprice.get_rsis(**rsi_params)
        rsi = list(rsi)
        rsi.reverse()
        # Check
        prev_index = index - 1
        tangent_rsi_positive = rsi[index] > rsi[prev_index]
        # Put
        param_str = _MF.param_to_str(rsi_params)
        k_base = f'is_tangent_rsi_positive_{period_str}[{index}]_{param_str}'
        vars_map.put(tangent_rsi_positive,          Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_date')
        vars_map.put(rsi[index],                    Map.value,      f'{k_base}_[{index}]')
        vars_map.put(rsi[prev_index],               Map.value,      f'{k_base}_[{prev_index}]')
        return tangent_rsi_positive

    @classmethod
    def compare_exetrem_ema_and_keltner(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, \
        comapare: str, ema_exetrem: str, keltner_line: str, ema_params: dict = {}, keltner_params: dict = {}) -> bool:
        compares = cls.COMPARATORS
        _MF.check_allowed_values(ema_exetrem, [Map.minimum, Map.maximum])
        _MF.check_allowed_values(comapare, compares)
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd().copy()
        now_time = marketprice.get_time()
        # EMA
        ema = marketprice.get_ema(**ema_params)
        ema = list(ema)
        ema.reverse()
        marketprice_df[Map.ema] = pd.Series(ema, index=marketprice_df.index)
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        marketprice_df[Map.keltner] = pd.Series(keltner, index=marketprice_df.index)
        # Cook
        k_ema_diff = Map.key(Map.ema, 'diff')
        marketprice_df[k_ema_diff] = marketprice_df[Map.ema].diff()
        index_ema_extrem = marketprice_df[marketprice_df[k_ema_diff] < 0].index[-1] if ema_exetrem == Map.minimum else marketprice_df[marketprice_df[k_ema_diff] > 0].index[-1]
        extrem_time = marketprice_df[Map.time].iloc[index_ema_extrem]
        # Check
        if comapare == compares[0]:
            check = bool(marketprice_df[Map.ema].iloc[index_ema_extrem] == marketprice_df[Map.keltner].iloc[index_ema_extrem])
        elif comapare == compares[1]:
            check = bool(marketprice_df[Map.ema].iloc[index_ema_extrem] > marketprice_df[Map.keltner].iloc[index_ema_extrem])
        elif comapare == compares[2]:
            check = bool(marketprice_df[Map.ema].iloc[index_ema_extrem] < marketprice_df[Map.keltner].iloc[index_ema_extrem])
        elif comapare == compares[3]:
            check = bool(marketprice_df[Map.ema].iloc[index_ema_extrem] <= marketprice_df[Map.keltner].iloc[index_ema_extrem])
        elif comapare == compares[4]:
            check = bool(marketprice_df[Map.ema].iloc[index_ema_extrem] >= marketprice_df[Map.keltner].iloc[index_ema_extrem])
        # Put
        param_str = _MF.param_to_str({**ema_params, **keltner_params})
        vars_map.put(check,                         Map.condition,  f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_date')
        vars_map.put(_MF.unix_to_date(extrem_time), Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_extrem_date')
        vars_map.put(ema[-1],                       Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_ema[-1]')
        vars_map.put(ema[-2],                       Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_ema[-2]')
        vars_map.put(ema[index_ema_extrem],         Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_ema_extrem')
        vars_map.put(keltner[-1],                   Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_keltner[-1]')
        vars_map.put(keltner[-2],                   Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_keltner[-2]')
        vars_map.put(keltner[index_ema_extrem],     Map.value,      f'is_{ema_exetrem}_ema_{comapare}_keltner_{keltner_line}_{period_str}_{param_str}_keltner_extrem')
        return check

    @classmethod
    def is_price_deep_enough(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, \
        keltner_line: str, macd_line: str, keltner_params: dict = {}, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd().copy()
        now_time = marketprice.get_time()
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        marketprice_df[Map.keltner] = pd.Series(keltner, index=marketprice_df.index)
        # MACD
        macd_map = marketprice.get_macd(**macd_params)
        macd = list(macd_map.get_map()[macd_line])
        macd.reverse()
        marketprice_df[Map.macd] = pd.Series(macd, index=marketprice_df.index)
        # Cook
        k_macd_diff = Map.key(Map.macd, 'diff')
        marketprice_df[k_macd_diff] = marketprice_df[Map.macd].diff()
        index_step = abs(marketprice_df.index[-1] - marketprice_df.index[-2])
        neg_marketprice_df = marketprice_df[marketprice_df[k_macd_diff] < 0]
        index_macd_switch = (neg_marketprice_df.index[-1] + index_step) if (neg_marketprice_df.shape[0] > 0) else None
        is_valid_index = index_macd_switch in marketprice_df.index
        switch_date = _MF.unix_to_date(marketprice_df[Map.time].iloc[index_macd_switch]) if is_valid_index else None
        # Check
        price_deep_enough = bool((is_valid_index) and (marketprice_df[Map.high].iloc[index_macd_switch] <= marketprice_df[Map.keltner].iloc[index_macd_switch]))
        # Put
        switch_high =       marketprice_df[Map.high].iloc[index_macd_switch] if is_valid_index else None
        switch_keltner =    keltner[index_macd_switch] if is_valid_index else None
        switch_macd =       macd[index_macd_switch] if is_valid_index else None
        param_str = _MF.param_to_str({**keltner_params, **macd_params})
        vars_map.put(price_deep_enough,                 Map.condition,  f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),        Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_date')
        vars_map.put(switch_date,                       Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_date_switch')
        vars_map.put(marketprice_df[Map.high].iloc[-1], Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_high[-1]')
        vars_map.put(marketprice_df[Map.high].iloc[-2], Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_high[-2]')
        vars_map.put(switch_high,                       Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_high_switch')
        vars_map.put(keltner[-1],                       Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_keltner[-1]')
        vars_map.put(keltner[-2],                       Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_keltner[-2]')
        vars_map.put(switch_keltner,                    Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_keltner_switch')
        vars_map.put(macd[-1],                          Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_macd[-1]')
        vars_map.put(macd[-2],                          Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_macd[-2]')
        vars_map.put(switch_macd,                       Map.value,      f'is_price_deep_enough_{keltner_line}_{macd_line}_{period_str}_{param_str}_macd_switch')
        return price_deep_enough

    @classmethod
    def param_to_str(cls, params: dict) -> str:
        param_str = ''
        if len(params) > 0:
            for key, value in params.items():
                param_str += f'{key}={value}' if len(param_str) == 0 else f'_{key}={value}'
        return param_str

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trades: list[dict], trade: dict, buy_conditions: list, sell_conditions: list) -> None:
        def is_order_set(side: str) -> bool:
            return trade[side] is not None
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            buy_datas = {}
            buy_datas[Map.buy] = trades[-1][Map.buy][Map.time] if len(trades) > 0 else None
            can_buy, buy_condition = cls.can_buy(broker, pair, marketprices, buy_datas)
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_MARKET, exec_type=Map.mean)
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            sell_datas = {}
            sell_datas[Map.time] =      trade[Map.buy][Map.time]
            sell_datas[Map.buy] =       trade[Map.buy][Map.execution]
            sell_datas[Map.fee] =       trade[Map.buy][Map.fee]
            sell_datas[Map.maximum] =   trade[Map.maximum]
            can_sell, sell_condition = cls.can_sell(broker, pair, marketprices, sell_datas)
            sell_condition = cls._backtest_condition_add_prefix(sell_condition, pair, marketprice)
            sell_conditions.append(sell_condition)
            # Manage Order
            if can_sell:
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.mean)
        return trade

    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST UP
    # ––––––––––––––––––––––––––––––––––––––––––– STATIC DOWN

    @classmethod
    def get_edited_market_trend_keys(cls, is_int_round: bool, window: int = None) -> tuple[str,str]:
        k_rise_rate = 'rise_rate'
        k_edited_rise_rate = f'{k_rise_rate}_{is_int_round}_{window}'
        edited_diff_rise_rate = f'diff_{k_edited_rise_rate}'
        return k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate

    @classmethod
    def get_edited_market_trend(cls, period: int, is_int_round: bool, window: int = None) -> pd.DataFrame:
        k_mean_market_trends = cls.K_EDITED_MARKET_TRENDS
        k_date = Map.date
        stack_keys = [k_mean_market_trends, period]
        stack = cls.get_stack()
        # Check if tab has changed
        edited_market_trend_df =    stack.get(*stack_keys)
        market_trend_df =           cls.get_market_trend(period)
        if (edited_market_trend_df is not None) and (edited_market_trend_df[k_date].iloc[-1] != market_trend_df[k_date].iloc[-1]):
            edited_market_trend_df = None
        # Try to Complet tab
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
    