import time
<<<<<<< HEAD
from typing import Callable, List

import numpy as np
import pandas as pd
=======
from typing import List

>>>>>>> Noah-v1

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
<<<<<<< HEAD
from model.tools.FileManager import FileManager
from model.tools.HandTrade import HandTrade
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
=======
>>>>>>> Noah-v1
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class Solomon(Strategy):
<<<<<<< HEAD
    PREFIX_ID =                 'solomon_'
    _SLEEP_TRADE =              30
    _MAX_POSITION =             10
    _MARKET_ANALYSE_N_PERIOD =  300
    MARKET_ANALYSE_WAIT_START = 60 * 10
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_5MIN,
<<<<<<< HEAD
        Broker.PERIOD_1H
=======
        Broker.PERIOD_1H,
>>>>>>> Solomon-v5.1.3
        ]
    PSAR_1 =                    dict(step=.6, max_step=.6)
    EMA_PARAMS_1 =              {'n_period': 5}
    EMA_PARAMS_2 =              {'n_period': 200}
    KELTNER_PARAMS_0 =          {'multiple': 1}
    KELTNER_PARAMS_1 =          {'multiple': 0.5}
    KELTNER_PARAMS_2 =          {'multiple': 0.25}
    K_BUY_SELL_CONDITION =      'K_BUY_SELL_CONDITION'
    K_EDITED_MARKET_TRENDS =    'K_EDITED_MARKET_TRENDS'
<<<<<<< HEAD
    COMPARATORS =               ['==', '>', '<', '<=', '>=']
    KELTNER_ZONE_H_INF =        'HIGH_INFINITY'
    KELTNER_ZONE_M_H =          'MIDDLE_HIGH'
    KELTNER_ZONE_L_M =          'LOW_MIDDLE'
    KELTNER_ZONE_INF_L =        'INFINITY_LOW'
    RISK_SAFE =                 'SAFE'
    RISK_MODERATE =             'MODERATE'
    RISK_RISKY =                'RISKY'
    BUY_CASE_WAVE =             'WAVE'
    BUY_CASE_LONG =             'LONG_RISE'
    SELECTED_PAIRS_FILE_PATH =  'content/storage/Strategy/Solomon/pairs/tradable.csv'
=======
    PREFIX_ID =             'solomon_'
    KELTER_SUPPORT =        None
>>>>>>> Noah-v1
=======
    MAX_LOSS_RATE =             -1/100
    MAX_PROFIT_RATE =           1/100
>>>>>>> Solomon-v2.0.2.2

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— SETTER/GETTER DOWN

    # def get_tradable_pairs(self) -> List[Pair]:
    #     tradable_pairs = self._tradable_pairs
    #     pair = self.get_pair()
    #     if (pair is None) and (tradable_pairs is None):
    #         r_asset = self.get_wallet().get_initial().get_asset()
    #         file_path = self.get_path(Map.left)
    #         left_asset_csv = FileManager.get_csv(file_path)
    #         tradable_pairs = [Pair(row[Map.left], r_asset) for row in left_asset_csv]
    #         self._set_tradable_pairs(tradable_pairs)
    #     else:
    #         tradable_pairs = super().get_tradable_pairs()
    #     return tradable_pairs

    # ——————————————————————————————————————————— SETTER/GETTER UP
    # ——————————————————————————————————————————— STALK DOWN

    def _manage_stalk(self) -> None:
        while self.is_stalk_on():
            _MF.catch_exception(self._stalk_market, self.__class__.__name__) if not self.is_max_position_reached() else None
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _stalk_market(self) -> List[Pair]:
<<<<<<< HEAD
        broker = self.get_broker()
        stalk_pairs = self._get_no_hold_pairs()
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

    def _trade_inner(self, marketprices: Map = Map()) -> None:
        def start_and_wait_market_analyse(analyse_periods: list[int]) -> None:
            C_Y = _MF.C_YELLOW
            S_N = _MF.S_NORMAL
            # Start analyse
            self.set_market_analyse_on(True)
            x = lambda : type(self.get_market_trend(analyse_periods[0]))
            wait_time = self.MARKET_ANALYSE_WAIT_START
            _MF.output(_MF.prefix() + f"{C_Y}Waiting the first analyse...{S_N}")
            _MF.wait_while(x, pd.DataFrame, wait_time, to_raise=Exception("The time to wait market's analyse is out"))
            _MF.output(_MF.prefix() + f"{C_Y}End wait the first analyse!{S_N}")
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
            broker_event = Broker.EVENT_NEW_PERIOD
            broker_callback = self._callback_trade
            broker_pairs = self.get_broker_pairs()
            tradable_pairs = self.get_tradable_pairs()
            required_periods = self._REQUIRED_PERIODS
            market_analyse_periods = self._MARKET_ANALYSE_TREND_PERIODS
            # Streams
            streams_1min = broker.generate_streams(broker_pairs, [Broker.PERIOD_1MIN])
            market_analyse_streams = broker.generate_streams(broker_pairs, market_analyse_periods)
            tradable_streams = broker.generate_streams(tradable_pairs, required_periods)
            all_streams = _MF.remove_duplicates([*tradable_streams, *streams_1min, *market_analyse_streams])
            tradable_streams_1min = [stream_1min for stream_1min in streams_1min if stream_1min in tradable_streams]
            # Open streams
            if (not broker.is_active()) or (not broker.exist_event_streams(broker_event, broker_callback, tradable_streams_1min)):
                broker.add_streams(all_streams)
                added_streams = broker.get_streams()
                added_pairs = list(added_streams.keys())
                self._set_broker_pairs(added_pairs)
                added_tradable_pairs = [tradable_pair for tradable_pair in tradable_pairs if tradable_pair in added_pairs]
                self._set_tradable_pairs(added_tradable_pairs)
                start_and_wait_market_analyse(market_analyse_periods)
                broker.add_event_streams(broker_event, broker_callback, tradable_streams_1min)
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
                can_buy, buy_report, _ = self.can_buy(broker, pair, marketprices, buy_datas)
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
                # sell_datas[Map.buy] =       buy_price.get_value()
                # sell_datas[Map.maximum] =   position.extrem_prices(broker).get(Map.maximum)
                sell_datas[Map.fee] =       buy_fee/buy_amount
                # Ask to sell
                can_sell, sell_report, _ = self.can_sell(broker, pair, marketprices, sell_datas)
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
=======
        pass

    # ••• STALK UP
    # ••• TRADE DOWN

    def trade(self) -> int:
        pass
>>>>>>> Noah-v1

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

<<<<<<< HEAD
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
<<<<<<< HEAD
<<<<<<< HEAD
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map, datas: dict) -> tuple[bool, dict, dict]:
        FEE_MULTIPLE =      1
        SMT_DEEP_TRIGGER =  10/100
        SMT_RISE_CEILING =  50/100
        SMT_RISE_INCREASE = 1/100
        FUNC_TO_PARAMS =    {}
        def get_callback_id(callback: Callable) -> str:
            return Map.key(callback.__name__, str(callback.__hash__()))
        def get_params(callback: Callable) -> list:
            return FUNC_TO_PARAMS[get_callback_id(callback)]
        def has_bought_since_negative_tangent_ema(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, last_buy_time: int, ema_params: dict = {}) -> bool:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            marketprice_df = marketprice.to_pd()
            # marketprice_df = marketprice_df.set_index(Map.time, drop=False)
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
        def buy_case(vars_map: Map) -> str:
            func_params = get_params(buy_case)
            case_value = None
            k_base = 'buy_case'
            vars_map.put(case_value, Map.value, k_base)
            # if cls.compare_trigger_and_market_trend(**func_params[0]):
            #     case_value = cls.BUY_CASE_WAVE
            # elif cls.is_market_trend_deep_and_rise(**func_params[1]):
            if cls.is_market_trend_deep_and_rise(**func_params[0]):
                case_value = cls.BUY_CASE_LONG
            vars_map.put(case_value, Map.value, k_base) if case_value is not None else None
            return case_value
        def are_profits_above_fees(vars_map: Map, fee_coef: float, buy_sell_fees: float) -> bool:
            func_params = get_params(are_profits_above_fees)
            # Check
            p_profit = potential_profit(**func_params[0])
            fee_trigger = fee_coef * buy_sell_fees
            profits_above_fees = (p_profit is not None) and (p_profit >= fee_trigger)
            # Put
            k_base = f'are_profits_above_fees'
            vars_map.put(profits_above_fees,    Map.condition,  k_base)
            vars_map.put(fee_coef,              Map.value,      f'{k_base}_fee_coef')
            vars_map.put(buy_sell_fees,         Map.value,      f'{k_base}_buy_sell_fees')
            vars_map.put(p_profit,              Map.value,      f'{k_base}_potential_profit')
            vars_map.put(fee_trigger,           Map.value,      f'{k_base}_fee_trigger')
            return profits_above_fees
        def potential_profit(period: int, price_line: str, index: int) -> float:
            func_params = get_params(potential_profit)
            period_str = period_strs[period]
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice_pd = marketprice.to_pd()
            r_level = risk_level(**func_params[0])
            buy_keltner_zone = cls.keltner_zone(**func_params[1])
            sell_price_v = cls.sell_price(**{**func_params[2], 'risk_level': r_level, 'keltner_zone': buy_keltner_zone})
            buy_price = marketprice_pd[price_line].iloc[index]
            futur_roi = _MF.progress_rate(sell_price_v, buy_price) if sell_price_v is not None else None
            # Put
            k_base = f'potential_profit_{period_str}[{index}]'
            vars_map.put(futur_roi,         Map.value,  f'{k_base}_futur_roi')
            vars_map.put(r_level,           Map.value,  f'{k_base}_risk_level')
            vars_map.put(buy_keltner_zone,  Map.value,  f'{k_base}_keltner_zone')
            vars_map.put(sell_price_v,      Map.value,  f'{k_base}_sell_price')
            vars_map.put(buy_price,         Map.value,  f'{k_base}_buy_price[{price_line}]')
            return futur_roi
        def risk_level(vars_map: Map) -> str:
            func_params = get_params(risk_level)
            A = ema_bellow_keltner =    cls.compare_ema_and_keltner(**func_params[0])
            B = supertrend_rising =     cls.is_supertrend_rising(**func_params[1])
            C = price_falling =         not cls.is_tangent_macd_line_positive(**func_params[2]) \
                                        and not cls.is_tangent_macd_line_positive(**func_params[3]) \
                                        and not cls.is_tangent_macd_line_positive(**func_params[4])
            if A and B and (not C):
                level = cls.RISK_SAFE
            elif A and (not B) and (not C):
                level = cls.RISK_MODERATE
            elif (not A) or C:
                level = cls.RISK_RISKY
            # Put
            k_base = 'risk_level'
            vars_map.put(level,                 Map.value,  f'{k_base}_risk_level')
            vars_map.put(ema_bellow_keltner,    Map.value,  f'{k_base}_ema_bellow_keltner')
            vars_map.put(supertrend_rising,     Map.value,  f'{k_base}_supertrend_rising')
            vars_map.put(price_falling,         Map.value,  f'{k_base}_price_falling')
            return level
=======
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float]:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        TRIGGE_KELTNER = 1/100
>>>>>>> Solomon-v1.1.2
=======
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict, float, dict]:
<<<<<<< HEAD
<<<<<<< HEAD
        TRIGGE_KELTNER = 0/100
>>>>>>> Solomon-v1.1.3.b
=======
        TRIGGE_KELTNER = 2.5/100
>>>>>>> Solomon-v1.1.4
=======
        TRIGGE_KELTNER = 3/100
>>>>>>> Solomon-v1.1.5
=======
        TRIGGE_KELTNER =        2/100
        KELTNER_RANGE_RATE =    1/4
<<<<<<< HEAD
>>>>>>> Solomon-v2.0.1.1
=======
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map, params: dict) -> tuple[bool, dict, float]:
        TRIGGE_KELTNER =            2/100
        KELTNER_RANGE_RATE =        1/8
        MEAN_MARKET_TREND_WINDOW =  5
        MEAN_MARKET_TREND_TRIGGER = 20/100
        def is_last_roi_positive(vars_map: Map, roi: float) -> bool:
            last_roi_positive = roi > 0
            vars_map.put(last_roi_positive, Map.condition,  f'is_last_roi_positive')
            return last_roi_positive
>>>>>>> Solomon-v2.0.2.2
=======
>>>>>>> Solomon-v2.1.3.1
=======
        TRIGGE_KELTNER =        0/100
        KELTNER_RANGE_RATE =    1/8
>>>>>>> Solomon-v2.1.3.b
=======
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
<<<<<<< HEAD
<<<<<<< HEAD
        TRIGGE_KELTNER = 0.4/100
>>>>>>> Solomon-v5.1.1.4
=======
        TRIGGE_KELTNER = 1/100
>>>>>>> Solomon-v5.1.1.4.1
=======
        TRIGGE_KELTNER = 2/100
>>>>>>> Solomon-v5.1.1.4.2
=======
        MARKETTREND_N_PERIOD = 5
>>>>>>> Solomon-v5.1.4.1.2
        vars_map = Map()
        period_1min =   Broker.PERIOD_1MIN
        period_5min =   Broker.PERIOD_5MIN
        period_1h =     Broker.PERIOD_1H
=======
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
        MARKET_TREND_TRIGGER = 20/100
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        period_1h = Broker.PERIOD_1H
>>>>>>> Solomon-v5.1.3
        periods = [
            period_1min,
            period_5min,
            period_1h
        ]
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
<<<<<<< HEAD
        period_strs = {period: broker.period_to_str(period) for period in periods}
        # Params
        last_buy_time = datas[Map.buy] if datas[Map.buy] is not None else 0 # in second
        fees = broker.get_trade_fee(pair)
        maker_fee = fees.get(Map.maker)
        taker_fee = fees.get(Map.taker)
        trade_fees = taker_fee + maker_fee
        keltner_trigger = FEE_MULTIPLE * trade_fees
        buy_price_line = Map.open if Config.get_stage() == Config.STAGE_1 else Map.close
        # Params
        now_index =     -1
        prev_index_2 =  -2
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        prev_index_3 =  -3
        prev_index_4 =  -4
=======
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
>>>>>>> Solomon-v2.0.2.2
=======
>>>>>>> Solomon-v5.1.1.2.1
=======
>>>>>>> Solomon-v5.1.3
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            # {Map.callback: cls.is_tangent_ema_positive,         Map.param: dict()},
            {Map.callback: cls.is_market_trend_deep_and_rise,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, fall_ceiling_rate=SMT_RISE_CEILING, increase_rate=SMT_RISE_INCREASE, last_buy_time=last_buy_time, is_int_round=False)},
            {Map.callback: cls.is_keltner_roi_above_trigger,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, trigger_keltner=keltner_trigger, keltner_params=cls.KELTNER_PARAMS_0)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=prev_index_2, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=prev_index_3, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_macd_from_negative,           Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.compare_emas,                    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, comparator='>=', ema_params_1=cls.EMA_PARAMS_1, ema_params_2=cls.EMA_PARAMS_2)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=prev_index_2)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index)}
=======
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
>>>>>>> Solomon-v2.0.2.2
=======
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, is_int_round=False)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_keltner_roi_above_trigger,        Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, trigge_keltner=TRIGGE_KELTNER, index=now_index)},
>>>>>>> Solomon-v4.1.b
=======
=======
            {Map.callback: cls.is_keltner_roi_above_trigger,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, trigge_keltner=TRIGGE_KELTNER, index=now_index)},
>>>>>>> Solomon-v5.1.1.4
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
<<<<<<< HEAD
            {Map.callback: cls.is_macd_line_positive,           Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=prev_index_2, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},
=======

            {Map.callback: cls.is_macd_line_positive,           Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},

>>>>>>> Solomon-v5.1.2.2.1
            {Map.callback: cls.is_tangent_macd_line_positive,   Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_psar_rising,                  Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)}
>>>>>>> Solomon-v5.1.1.2
=======
            {Map.callback: cls.is_market_trend_bellow,              Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, trigger=MARKET_TREND_TRIGGER, is_int_round=True)},
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, is_int_round=False)},
=======
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, is_int_round=False, window=MARKETTREND_N_PERIOD)},
>>>>>>> Solomon-v5.1.4.1.2
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_macd_line_positive,               Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_macd_line_positive,               Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, line_name=Map.histogram, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=now_index, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},
            {Map.callback: cls.is_tangent_macd_line_positive,       Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1h, marketprices=marketprices, index=prev_index_2, line_name=Map.macd, macd_params=MarketPrice.MACD_PARAMS_1)},
>>>>>>> Solomon-v5.1.3
        ]
        # FUNC_TO_PARAMS[get_callback_id(buy_case)] = [
        #     # compare_trigger_and_market_trend
        #     # is_market_trend_deep_and_rise
        #     func_and_params[1][Map.param]
        # ]
        # FUNC_TO_PARAMS[get_callback_id(are_profits_above_fees)] = [
        #     # potential_profit
        #     func_and_params[4][Map.param]
        # ]
        # FUNC_TO_PARAMS[get_callback_id(potential_profit)] = [
        #     # risk_level
        #     # keltner_zone
        #     # sell_price
        #     func_and_params[5][Map.param],
        #     func_and_params[6][Map.param],
        #     func_and_params[7][Map.param]
        # ]
        # FUNC_TO_PARAMS[get_callback_id(risk_level)] = [
        #     # compare_ema_and_keltner
        #     # is_supertrend_rising
        #     # is_tangent_macd_line_positive
        #     # is_tangent_macd_line_positive
        #     # is_tangent_macd_line_positive
        #     func_and_params[5][Map.param],
        #     func_and_params[6][Map.param],
        #     func_and_params[7][Map.param],
        #     func_and_params[8][Map.param],
        #     func_and_params[9][Map.param]
        # ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Keys
        # risk_period_str =   None    # period_strs[func_and_params[4][Map.param][Map.period]]
        # risk_index =        None    # func_and_params[4][Map.param][Map.index]
        # k_risk_level =      f'potential_profit_{risk_period_str}[{risk_index}]_risk_level'
        # k_keltner_zone =    f'potential_profit_{risk_period_str}[{risk_index}]_keltner_zone'
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        buy_case_value = cls.BUY_CASE_LONG
        can_buy = cls.is_market_trend_deep_and_rise(**func_and_params[0][Map.param]) \
            and cls.is_keltner_roi_above_trigger(**func_and_params[1][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[2][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[3][Map.param]) \
            and cls.is_macd_from_negative(**func_and_params[4][Map.param]) \
            and cls.compare_emas(**func_and_params[5][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[6][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[7][Map.param])
=======
        can_buy = cls.is_tangent_market_trend_positive(**func_and_params[0][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[1][Map.param]) \
<<<<<<< HEAD
            and cls.is_tangent_macd_line_positive(**func_and_params[2][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[3][Map.param])
        if can_buy:
            cls.is_keltner_roi_above_trigger(**func_and_params[4][Map.param])
>>>>>>> Solomon-v4.1.b
=======
            and (
                cls.is_macd_line_positive(**func_and_params[2][Map.param]) \
                or
                cls.is_tangent_macd_line_positive(**func_and_params[3][Map.param])\
                and
                cls.is_tangent_macd_line_positive(**func_and_params[4][Map.param])
            ) \
<<<<<<< HEAD
            and cls.is_tangent_macd_line_positive(**func_and_params[4][Map.param]) \
            and cls.is_psar_rising(**func_and_params[5][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[6][Map.param])
>>>>>>> Solomon-v5.1.1.2
=======
            and cls.is_tangent_macd_line_positive(**func_and_params[5][Map.param]) \
            and cls.is_psar_rising(**func_and_params[6][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[7][Map.param])
>>>>>>> Solomon-v5.1.1.2.1
=======
        can_buy = cls.is_keltner_roi_above_trigger(**func_and_params[0][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[1][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[2][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[3][Map.param]) \
            and cls.is_psar_rising(**func_and_params[4][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[5][Map.param])
>>>>>>> Solomon-v5.1.1.4
=======
        can_buy = cls.is_tangent_macd_line_positive(**func_and_params[0][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[1][Map.param]) \
=======
        can_buy = cls.is_market_trend_bellow(**func_and_params[0][Map.param]) \
            and cls.is_tangent_market_trend_positive(**func_and_params[1][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[2][Map.param]) \
            and cls.is_tangent_macd_line_positive(**func_and_params[3][Map.param]) \
>>>>>>> Solomon-v5.1.3
            and (
                cls.is_macd_line_positive(**func_and_params[4][Map.param])
                or
                cls.is_tangent_macd_line_positive(**func_and_params[5][Map.param])
            ) \
            and cls.is_tangent_macd_line_positive(**func_and_params[6][Map.param]) \
            and (
                cls.is_macd_line_positive(**func_and_params[7][Map.param]) \
                or
                cls.is_tangent_macd_line_positive(**func_and_params[8][Map.param]) \
                and
<<<<<<< HEAD
                cls.is_tangent_macd_line_positive(**func_and_params[7][Map.param])
            ) \
            and cls.is_psar_rising(**func_and_params[8][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[9][Map.param])
        if can_buy:
            cls.is_keltner_roi_above_trigger(**func_and_params[10][Map.param])
>>>>>>> Solomon-v5.1.2.2.1
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_buy, vars_map)
        cases = {
            Map.option:     buy_case_value,
            # Map.rank:       None,           # vars_map.get(Map.value, k_risk_level),
            # Map.keltner:    None            # vars_map.get(Map.value, k_keltner_zone)
=======
        indexes = marketprice_1min_pd.index
        period_strs = {period: broker.period_to_str(period) for period in [period_1min, period_5min, period_15min]}
        k_keltner_roi_1min = f'keltner_roi_{period_strs[period_1min]}'
        k_keltner_high_1min = f'keltner_high_{period_strs[period_1min]}[-1]'
        k_close_1min = f'close_{period_strs[period_1min]}[-1]'
        can_buy = cls.is_keltner_roi_above_trigger(vars_map, broker, pair, period_1min, marketprices, TRIGGE_KELTNER) \
            and cls.is_psar_rising(vars_map, broker, pair, period_1min, marketprices) \
            and cls.is_psar_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_psar_rising(vars_map, broker, pair, period_15min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_5min, marketprices) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_15min, marketprices) \
            and cls.is_price_bellow_keltner_line(vars_map, broker, pair, period_1min, marketprices, Map.close, Map.high)
        report = {
            f'can_buy':                                                             can_buy,
            f'keltner_roi_above_trigger_{period_strs[period_1min]}':                vars_map.get(f'keltner_roi_above_trigger_{period_strs[period_1min]}'),
            f'psar_rising_{period_strs[period_5min]}':                              vars_map.get(f'psar_rising_{period_strs[period_5min]}'),
            f'psar_rising_{period_strs[period_15min]}':                             vars_map.get(f'psar_rising_{period_strs[period_15min]}'),
            f'supertrend_rising_{period_strs[period_5min]}':                        vars_map.get(f'supertrend_rising_{period_strs[period_5min]}'),
            f'supertrend_rising_{period_strs[period_15min]}':                       vars_map.get(f'supertrend_rising_{period_strs[period_15min]}'),
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
            f'psar_{period_strs[period_1min]}[-1]':                                 vars_map.get(f'psar_{period_strs[period_1min]}[-1]'),
            f'psar_{period_strs[period_1min]}[-2]':                                 vars_map.get(f'psar_{period_strs[period_1min]}[-2]'),
            f'psar_{period_strs[period_5min]}[-1]':                                 vars_map.get(f'psar_{period_strs[period_5min]}[-1]'),
            f'psar_{period_strs[period_5min]}[-2]':                                 vars_map.get(f'psar_{period_strs[period_5min]}[-2]'),
            f'psar_{period_strs[period_15min]}[-1]':                                vars_map.get(f'psar_{period_strs[period_15min]}[-1]'),
            f'psar_{period_strs[period_15min]}[-2]':                                vars_map.get(f'psar_{period_strs[period_15min]}[-2]'),
            f'supertrend_{period_strs[period_1min]}[-1]':                           vars_map.get(f'supertrend_{period_strs[period_1min]}[-1]'),
            f'supertrend_{period_strs[period_1min]}[-2]':                           vars_map.get(f'supertrend_{period_strs[period_1min]}[-2]'),
            f'supertrend_{period_strs[period_5min]}[-1]':                           vars_map.get(f'supertrend_{period_strs[period_5min]}[-1]'),
            f'supertrend_{period_strs[period_5min]}[-2]':                           vars_map.get(f'supertrend_{period_strs[period_5min]}[-2]'),
            f'supertrend_{period_strs[period_15min]}[-1]':                          vars_map.get(f'supertrend_{period_strs[period_15min]}[-1]'),
            f'supertrend_{period_strs[period_15min]}[-2]':                          vars_map.get(f'supertrend_{period_strs[period_15min]}[-2]')
>>>>>>> Solomon-v3
        }
        return can_buy, report, cases

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map, datas: dict) -> tuple[bool, dict, float]:
<<<<<<< HEAD
        SMT_MAX_DROP =      10/100
        SELL_RATE_ABOVE =   30/100     
        SELL_RATE_BELLOW =  50/100
        FUNC_TO_PARAMS =    {}
        def get_callback_id(callback: Callable) -> str:
            return Map.key(callback.__name__, str(callback.__hash__()))
        def get_params(callback: Callable) -> list:
            return FUNC_TO_PARAMS[get_callback_id(callback)]
        def has_supertrend_switched_down(vars_map: Map, pair: Pair, period: int, buy_time: int, index: int) -> bool:
            """
            To check if supertrend has switched down since buy
=======
                cls.is_tangent_macd_line_positive(**func_and_params[9][Map.param])
            )
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_buy, vars_map)
        return can_buy, report

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map, datas: dict) -> tuple[bool, dict]:
        def has_switched_up_down(vars_map: Map, pair: Pair, period: int, buy_time: int, index: int) -> bool:
            """
            To check if supertrend has switched up then down since buy
>>>>>>> Solomon-v5.1.3
            """
            if index >= 0:
                raise ValueError(f"Index must be negative, instead '{index}'")
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
<<<<<<< HEAD
            marketprice.reset_collections()
            now_time = marketprice.get_time()
            # Price
            marketprice_df = marketprice.to_pd()
            # marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # Supertrends
            supertrends = list(marketprice.get_super_trend())
            supertrends.reverse()
            marketprice_df[Map.supertrend] = pd.Series(supertrends, index=marketprice_df.index)
            # Prepare
            buy_time_round = _MF.round_time(buy_time, period)
            index_time = marketprice_df[Map.time].iloc[index]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time_round) & (marketprice_df[Map.time] <= index_time)]
            rising_zone_df = sub_marketprice_df[sub_marketprice_df[Map.close] > sub_marketprice_df[Map.supertrend]]
=======
        KEEP_RATE =     30/100
        KEEP_TRIGGER =  1/100
        def can_stop_losses(vars_map: Map, keep_trigger: float, keep_rate: float, buy_price: float, max_roi: float, sell_fee_rate: float) -> bool:
            stop_price = None
>>>>>>> Solomon-v5.1.2.1.1
            # Check
            has_switched = bool((rising_zone_df.shape[0] > 0) and (sub_marketprice_df.loc[index_time, Map.close] < sub_marketprice_df.loc[index_time, Map.supertrend]))
=======
            # Price
            marketprice_df = marketprice.to_pd()
            marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # Supertrends
            supertrends = list(marketprice.get_super_trend())
            supertrends.reverse()
            supertrends_df = pd.DataFrame({Map.time: marketprice_df[Map.time], Map.supertrend: supertrends})
            supertrends_df.set_index(Map.time, drop=False, inplace=True)
            marketprice_df[Map.supertrend] = supertrends_df[Map.supertrend]
            # Prepare
            buy_time_round = _MF.round_time(buy_time, period)
            now_time = marketprice_df[Map.time].iloc[index]
            sub_marketprice_df = marketprice_df[(marketprice_df[Map.time] >= buy_time_round) & (marketprice_df[Map.time] <= now_time)]
            rising_zone_df = sub_marketprice_df[sub_marketprice_df[Map.close] > sub_marketprice_df[Map.supertrend]]
            # Check
            has_switched = (rising_zone_df.shape[0] > 0) and (sub_marketprice_df.loc[now_time, Map.close] < sub_marketprice_df.loc[now_time, Map.supertrend])
>>>>>>> Solomon-v5.1.3
            # Put
            trade_zone_start =  _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[0])
            trade_zone_end =    _MF.unix_to_date(sub_marketprice_df[Map.time].iloc[-1])
            rising_zone_start = _MF.unix_to_date(rising_zone_df[Map.time].iloc[0]) if rising_zone_df.shape[0] > 0 else None
            rising_zone_end =   _MF.unix_to_date(rising_zone_df[Map.time].iloc[-1]) if rising_zone_df.shape[0] > 0 else None
<<<<<<< HEAD
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
            marketprice_df = marketprice.to_pd()
            # marketprice_df = marketprice_df.set_index(Map.time, drop=False)
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
            marketprice_df = marketprice.to_pd()
            # marketprice_df = marketprice_df.set_index(Map.time, drop=False)
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
            k_keltner_low =     Map.key(Map.keltner, Map.low)
            k_keltner_roi =     Map.key(Map.keltner, Map.roi)
            # Price
            marketprice_df = marketprice.to_pd()
            # marketprice_df = marketprice_df.set_index(Map.time, drop=False)
            # Keltner
            keltner_map = marketprice.get_keltnerchannel(multiple=1)
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            marketprice_df[k_keltner_high] = pd.Series(keltner_high, index=marketprice_df.index)
            keltner_low = list(keltner_map.get(Map.low))
            keltner_low.reverse()
            marketprice_df[k_keltner_low] = pd.Series(keltner_low, index=marketprice_df.index)
            # Prepare
            max_roi = (max_price - buy_price) / buy_price
            marketprice_df[k_keltner_roi] = (marketprice_df[k_keltner_high] - marketprice_df[k_keltner_low]) / marketprice_df[k_keltner_low]
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
        def has_market_trend_rose(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, buy_time: int, is_int_round: bool = False, window: int = None) -> None:
            func_params = get_params(has_market_trend_rose)
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            now_date = _MF.unix_to_date(marketprice.get_time())
            buy_date = _MF.unix_to_date(buy_time)
            # Get trend
            market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
            k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
            # Get bracket
            open_times = list(marketprice.get_times())
            open_times.reverse()
            index_time = open_times[index]
            rounded_buy_time = _MF.round_time(buy_time, period)
            sub_market_trend_df = market_trend_df[(rounded_buy_time <= market_trend_df.index) & (market_trend_df.index <= index_time)]
            index_date = _MF.unix_to_date(index_time)
            rounded_buy_date = _MF.unix_to_date(rounded_buy_time)
            # Check
            max_rate = sub_market_trend_df[k_edited_rise_rate].max()
            rate_trigger = sell_rate(**func_params[0])
            index_max_rate = sub_market_trend_df[sub_market_trend_df[k_edited_rise_rate] == max_rate].index[-1]
            max_rate_date = _MF.unix_to_date(index_max_rate)
            has_reached = bool(max_rate >= rate_trigger)
            # Put
            k_base = f'has_market_trend_rose_{period_str}_{is_int_round}_{window}[{index}]'
            vars_map.put(has_reached,       Map.condition,  k_base)
            vars_map.put(now_date,          Map.value,      f'{k_base}_now_date')
            vars_map.put(index_date,        Map.value,      f'{k_base}_index_date')
            vars_map.put(buy_date,          Map.value,      f'{k_base}_buy_date')
            vars_map.put(rounded_buy_date,  Map.value,      f'{k_base}_rounded_buy_date')
            vars_map.put(max_rate_date,     Map.value,      f'{k_base}_max_rate_date')
            vars_map.put(max_rate,          Map.value,      f'{k_base}_max_rate')
            vars_map.put(rate_trigger,      Map.value,      f'{k_base}_rate_trigger')
            return has_reached
        def sell_rate(period: int, buy_time: int, buy_price: float, keltner_params: dict = {}) -> float:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice_pd = marketprice.to_pd()
            now_date = _MF.unix_to_date(marketprice.get_time())
            buy_date = _MF.unix_to_date(buy_time)
            # Keltner
            keltner_map = marketprice.get_keltnerchannel(**keltner_params)
            keltner = list(keltner_map.get_map()[Map.middle])
            keltner.reverse()
            marketprice_pd[Map.keltner] = pd.Series(keltner, index=marketprice_pd.index)
            # Index
            rounded_buy_time = _MF.round_time(buy_time, period)
            index_buy_time = marketprice_pd[marketprice_pd[Map.time] == rounded_buy_time].index[-1]
            round_buy_date = _MF.unix_to_date(rounded_buy_time)
            index_buy_date = _MF.unix_to_date(index_buy_time)
            # Check
            keltner_at_index = marketprice_pd[Map.keltner][index_buy_time]
            if buy_price >= keltner_at_index:
                rate = SELL_RATE_ABOVE
            else:
                rate = SELL_RATE_BELLOW
            # Put
            # prev_index = index - 1
            keltner_params_str = _MF.param_to_str(keltner_params)
            k_base = f'sell_rate_{period_str}_{keltner_params_str}'
            vars_map.put(rate,              Map.value,  k_base)
            vars_map.put(now_date,          Map.value,  f'{k_base}_now_date')
            vars_map.put(buy_date,          Map.value,  f'{k_base}_buy_date')
            vars_map.put(round_buy_date,    Map.value,  f'{k_base}_round_buy_date')
            vars_map.put(index_buy_date,    Map.value,  f'{k_base}_index_buy_date')
            vars_map.put(buy_price,         Map.value,  f'{k_base}_buy_price')
            vars_map.put(keltner_at_index,  Map.value,  f'{k_base}_keltner_at_index')
            return rate
        def has_market_trend_reach_max_drop(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, buy_time: int, is_int_round: bool = False, window: int = None) -> None:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            now_date = _MF.unix_to_date(marketprice.get_time())
            buy_date = _MF.unix_to_date(buy_time)
            # Get trend
            market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
            k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
            # Get bracket
            open_times = list(marketprice.get_times())
            open_times.reverse()
            time_at_index = open_times[index]
            rounded_buy_time = _MF.round_time(buy_time, period)
            trade_zone_df = market_trend_df[(market_trend_df.index >= rounded_buy_time) & (market_trend_df.index <= time_at_index)]
            max_rate =          float('nan')
            index_max_rate =    None
            fall_zone_df =      None
            min_rate =          float('nan')
            index_min_rate =    None
            if trade_zone_df.shape[0] > 0:
                max_rate = trade_zone_df[k_edited_rise_rate].max()
                index_max_rate = trade_zone_df[trade_zone_df[k_edited_rise_rate] == max_rate].index[-1]
                fall_zone_df = trade_zone_df[(trade_zone_df.index >= index_max_rate) & (trade_zone_df.index <= time_at_index)]
                min_rate = fall_zone_df[k_edited_rise_rate].min()
                index_min_rate = fall_zone_df[fall_zone_df[k_edited_rise_rate] == min_rate].index[-1]
            # Check
            drop_rate = max_rate - min_rate
            reached_max_drop = bool(drop_rate >= SMT_MAX_DROP)
            # Put
            date_at_index = _MF.unix_to_date(time_at_index)
            rounded_buy_date = _MF.unix_to_date(rounded_buy_time)
            max_rate_date = _MF.unix_to_date(index_max_rate) if index_max_rate is not None else None
            min_rate_date = _MF.unix_to_date(index_min_rate) if index_min_rate is not None else None
            k_base = f'has_market_trend_reach_max_drop_{period_str}_{is_int_round}_{window}[{index}]'
            vars_map.put(reached_max_drop,  Map.condition,  k_base)
            vars_map.put(now_date,          Map.value,      f'{k_base}_now_date')
            vars_map.put(date_at_index,     Map.value,      f'{k_base}_date_at_index')
            vars_map.put(buy_date,          Map.value,      f'{k_base}_buy_date')
            vars_map.put(rounded_buy_date,  Map.value,      f'{k_base}_rounded_buy_date')
            vars_map.put(max_rate_date,     Map.value,      f'{k_base}_max_rate_date')
            vars_map.put(max_rate,          Map.value,      f'{k_base}_max_rate')
            vars_map.put(min_rate_date,     Map.value,      f'{k_base}_min_rate_date')
            vars_map.put(min_rate,          Map.value,      f'{k_base}_min_rate')
            vars_map.put(drop_rate,         Map.value,      f'{k_base}_drop_rate')
            vars_map.put(SMT_MAX_DROP,      Map.value,      f'{k_base}_max_drop')
            return reached_max_drop
        def keltner_sell_price(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, keltner_line: str, keltner_params: dict = {}) -> float:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            keltner_map = marketprice.get_keltnerchannel(**keltner_params)
            keltner = list(keltner_map.get(keltner_line))
            keltner.reverse()
            sell_price = keltner[index]
            # Put
            params_str = _MF.param_to_str(keltner_params)
            prev_index = index - 1
            vars_map.put(keltner[index],        Map.value,  f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{index}]')
            vars_map.put(keltner[prev_index],   Map.value,  f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{prev_index}]')
            return sell_price
        def keltner_roi_sell_price(vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, keltner_line: str, buy_price: float, keltner_coef: float = 1, keltner_params: dict = {}) -> float:
            period_str = broker.period_to_str(period)
            marketprice = cls._marketprice(broker, pair, period, marketprices)
            marketprice.reset_collections()
            # Keltner
            keltner_map = marketprice.get_keltnerchannel(**keltner_params)
            keltner = list(keltner_map.get(keltner_line))
            keltner.reverse()
            keltner_low = list(keltner_map.get(Map.low))
            keltner_low.reverse()
            # Sell price
            keltner_roi = _MF.progress_rate(keltner[index], keltner_low[index])
            sell_price = buy_price * (1 + keltner_roi * keltner_coef)
            # Put
            k_base = f'keltner_roi_sell_price'
            params_str = _MF.param_to_str(keltner_params)
            prev_index = index - 1
            vars_map.put(buy_price,                 Map.value,  f'{k_base}_buy_price')
            vars_map.put(keltner_coef,              Map.value,  f'{k_base}_keltner_coef')
            vars_map.put(keltner_roi,               Map.value,  f'{k_base}_keltner_roi')
            vars_map.put(sell_price,                Map.value,  f'{k_base}_sell_price')
            vars_map.put(keltner_low[index],        Map.value,  f'{Map.key(Map.keltner, Map.low, period_str, params_str)}[{index}]')
            vars_map.put(keltner_low[prev_index],   Map.value,  f'{Map.key(Map.keltner, Map.low, period_str, params_str)}[{prev_index}]')
            vars_map.put(keltner[index],            Map.value,  f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{index}]')
            vars_map.put(keltner[prev_index],       Map.value,  f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{prev_index}]')
            return sell_price
        vars_map = Map()
        period_1min =   Broker.PERIOD_1MIN
        period_5min =   Broker.PERIOD_5MIN
        period_1h =     Broker.PERIOD_1H
        periods = [
            period_1min,
            period_5min,
            period_1h
=======
            vars_map.put(has_switched,                      Map.condition,  f'has_switched_up_down_{period_str}[{index}]')
            vars_map.put(_MF.unix_to_date(buy_time),        Map.value,      f'has_switched_up_down_{period_str}[{index}]_buy_time')
            vars_map.put(_MF.unix_to_date(buy_time_round),  Map.value,      f'has_switched_up_down_{period_str}[{index}]_buy_time_round')
            vars_map.put(_MF.unix_to_date(now_time),        Map.value,      f'has_switched_up_down_{period_str}[{index}]_now_time')
            vars_map.put(trade_zone_start,                  Map.value,      f'has_switched_up_down_{period_str}[{index}]_trade_zone_start')
            vars_map.put(trade_zone_end,                    Map.value,      f'has_switched_up_down_{period_str}[{index}]_trade_zone_end')
            vars_map.put(rising_zone_start,                 Map.value,      f'has_switched_up_down_{period_str}[{index}]_rising_zone_start')
            vars_map.put(rising_zone_end,                   Map.value,      f'has_switched_up_down_{period_str}[{index}]_rising_zone_end')
            return has_switched
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        periods = [
            period_1min
>>>>>>> Solomon-v5.1.3
        ]
=======
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
>>>>>>> Solomon-v2.0.2.2
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in periods}
        # Datas
<<<<<<< HEAD
        buy_time =              _MF.round_time(datas[Map.time], period_1min)  # in second
        # buy_price =             datas[Map.buy]
        buy_fee_rate =          datas[Map.fee]
        # buy_case =              datas[Map.option]
        # risk_level =            datas[Map.rank]
        # buy_keltner_zone =      datas[Map.keltner]
        fees = broker.get_trade_fee(pair)
        maker_fee = fees.get(Map.maker)
        trade_fees = buy_fee_rate + maker_fee
=======
        buy_time = datas[Map.time]  # in second
>>>>>>> Solomon-v5.1.3
        # Params
        now_index = -1
<<<<<<< HEAD
        k_base_can_stop = 'can_stop_losses'
        k_base_can_take = 'can_take_profit'
        k_stop_price = f'{k_base_can_stop}_stop_price'
        k_limit_price = f'{k_base_can_take}_limit_price'
        now_close = marketprice_1min_pd[Map.close].iloc[-1]
        # Add price
=======
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
>>>>>>> Solomon-v2.0.2.2
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-1],    Map.value, f'open_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.open].iloc[-2],    Map.value, f'open_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-1],     Map.value, f'low_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.low].iloc[-2],     Map.value, f'low_{period_strs[period_1min]}[-2]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-1],    Map.value, f'high_{period_strs[period_1min]}[-1]')
        vars_map.put(marketprice_1min_pd[Map.high].iloc[-2],    Map.value, f'high_{period_strs[period_1min]}[-2]')
<<<<<<< HEAD
        vars_map.put(now_close,                                 Map.value, f'close_{period_strs[period_1min]}[-1]')
=======
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-1],   Map.value, f'close_{period_strs[period_1min]}[-1]')
>>>>>>> Solomon-v2.0.2.2
        vars_map.put(marketprice_1min_pd[Map.close].iloc[-2],   Map.value, f'close_{period_strs[period_1min]}[-2]')
        # Set header
        this_func = cls.can_sell
        func_and_params = [
<<<<<<< HEAD
<<<<<<< HEAD
            {Map.callback: has_market_trend_reach_max_drop, Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index, buy_time=buy_time, is_int_round=False)}
=======
            {Map.callback: cls.is_roi_compare_trigger,          Map.param: dict(vars_map=vars_map, compare='>=', roi=position_roi, trigger=max_profit_rate)},
            {Map.callback: cls.is_psar_rising,                  Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,            Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_15min, marketprices=marketprices, index=now_index)},
            {Map.callback: is_roi_positive,                     Map.param: dict(vars_map=vars_map, roi=position_roi)},
            {Map.callback: cls.is_keltner_roi_above_trigger,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, trigge_keltner=0, index=now_index)}
>>>>>>> Solomon-v2.0.2.2
=======
            {Map.callback: has_switched_up_down, Map.param: dict(vars_map=vars_map, pair=pair, period=period_1min, buy_time=buy_time, index=now_index)},
>>>>>>> Solomon-v5.1.3
        ]
        # FUNC_TO_PARAMS[get_callback_id(has_market_trend_rose)] = [
        #     # sell_rate
        #     func_and_params[2][Map.param]
        # ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
        # vars_map.put(buy_case, Map.value, f'buy_case')
        can_sell = False
        sell_price = None
        can_sell = has_market_trend_reach_max_drop(**func_and_params[0][Map.param])
=======
        can_sell = has_switched_up_down(**func_and_params[0][Map.param])
>>>>>>> Solomon-v5.1.3
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_sell, vars_map)
        return can_sell, report, sell_price
=======
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
>>>>>>> Solomon-v2.0.2.2

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
    def is_keltner_roi_above_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, trigger_keltner: float, keltner_params: dict = {}) -> bool:
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
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        k_base = f'is_keltner_roi_above_trigger_{period_str}[{index}]'
        vars_map.put(keltner_roi_above_trigger,     Map.condition,  f'is_keltner_roi_above_trigger_{period_str}[{index}]')
        vars_map.put(trigger_keltner,               Map.value,      f'{k_base}_trigger_keltner')
        vars_map.put(keltner_roi,                   Map.value,      f'{k_base}_keltner_roi')
        vars_map.put(keltner_high[index],           Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{index}]')
        vars_map.put(keltner_high[prev_index],      Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{prev_index}]')
        vars_map.put(keltner_middle[index],         Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, params_str)}[{index}]')
        vars_map.put(keltner_middle[prev_index],    Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, params_str)}[{prev_index}]')
        vars_map.put(keltner_low[index],            Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{index}]')
        vars_map.put(keltner_low[prev_index],       Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{prev_index}]')
        return keltner_roi_above_trigger

    @classmethod
    def compare_price_and_keltner_line(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, comparator: str, price_line: str, keltner_line: str, \
        keltner_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Check
        market_price = marketprice_df[price_line].iloc[index]
        keltner_price = keltner[index]
        compare = bool(_MF.compare_first_and_second(comparator, market_price, keltner_price))
        # Put
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        k_base = f'compare_price[{price_line}]_{comparator}_keltner[{keltner_line}]_{period_str}_{params_str}[{index}]'
        vars_map.put(compare,               Map.condition,  k_base)
        vars_map.put(keltner[index],        Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, params_str)}[{index}]')
        vars_map.put(keltner[prev_index],   Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, params_str)}[{prev_index}]')
        return compare

    @classmethod
    def compare_keltner_profit_and_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, \
        comparator: str, price_line: str, keltner_line: str, trigger: float, keltner_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Prepare
        market_price = marketprice_df[price_line].iloc[index]
        keltner_price = keltner[index]
        keltner_profit = _MF.progress_rate(keltner_price, market_price)
        # Check
        compare = bool(_MF.compare_first_and_second(comparator, keltner_profit, trigger))
        # Put
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        k_base = f'compare_keltner_profit[{keltner_line},{price_line}]_{comparator}_trigger_keltner_{period_str}_{params_str}[{index}]'
        vars_map.put(compare,               Map.condition,  k_base)
        vars_map.put(keltner[index],        Map.value,      f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{index}]')
        vars_map.put(keltner[prev_index],   Map.value,      f'{Map.key(Map.keltner, keltner_line, period_str, params_str)}[{prev_index}]')
        vars_map.put(market_price,          Map.value,      f'{k_base}_market_price')
        vars_map.put(keltner_profit,        Map.value,      f'{k_base}_keltner_profit')
        vars_map.put(trigger,               Map.value,      f'{k_base}_trigger')
        return compare

    @classmethod
    def is_close_bellow_keltner_range(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, rate: float, keltner_params: dict = {}) -> bool:
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
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        vars_map.put(close_bellow_keltner_range,    Map.condition,  f'close_bellow_keltner_range_{period_str}[{index}]')
        vars_map.put(keltner_range,                 Map.value,      f'keltner_range_{period_str}[{index}]')
        vars_map.put(keltner_piece,                 Map.value,      f'keltner_piece_{period_str}[{index}]')
        vars_map.put(keltner_price,                 Map.value,      f'keltner_price_{period_str}[{index}]')
        vars_map.put(market_price,                  Map.value,      f'market_price_{period_str}[{index}]')
        vars_map.put(keltner_high[index],           Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{index}]')
        vars_map.put(keltner_high[prev_index],      Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{prev_index}]')
        vars_map.put(keltner_low[index],            Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{index}]')
        vars_map.put(keltner_low[prev_index],       Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{prev_index}]')
        return close_bellow_keltner_range

    @classmethod
    def compare_keltner_floor_and_rate(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, \
        comparator: str, keltner_line: str, buy_price: float, rate: float, keltner_params: dict = {}) -> bool:
        # comparators = cls.COMPARATORS
        # _MF.check_allowed_values(comparator, comparators)
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Prapare
        keltner_floor = (keltner[index] - buy_price) / buy_price
        # Check
        check = _MF.compare_first_and_second(comparator, keltner_floor, rate)
        # Put
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        k_base = f'compare_keltner_floor_{keltner_line}_{comparator}_{period_str}[{index}]'
        prev_index = index - 1
        vars_map.put(check,                         Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_date')
        vars_map.put(buy_price,                     Map.value,      f'{k_base}_buy_price')
        vars_map.put(keltner_floor,                 Map.value,      f'{k_base}_keltner_floor')
        vars_map.put(rate,                          Map.value,      f'{k_base}_rate')
        vars_map.put(keltner[index],                Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, params_str)}[{index}]')
        vars_map.put(keltner[prev_index],           Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, params_str)}[{prev_index}]')
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
    def compare_trigger_and_market_trend(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, comparator: str, trigger: float, is_int_round: bool, window: int = None) -> bool:
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
        index_trend_date = sub_market_trend_df[k_market_date].iloc[-1]
        # Check
        index_rise_rate = sub_market_trend_df[k_edited_rise_rate].iloc[-1]
        # is_bellow = bool(index_rise_rate*100 <= trigger*100)
        compare = bool(_MF.compare_first_and_second(comparator, trigger*100, index_rise_rate*100))
        # Report
        k_base = f'compare_{trigger}_{comparator}_market_trend({period_str},w={window},int={is_int_round})[{index}]'
        vars_map.put(compare,           Map.condition,  k_base)
        vars_map.put(index_date,        Map.value,      f'{k_base}_index_date')
        vars_map.put(index_trend_date,  Map.value,      f'{k_base}_trend_date')
        vars_map.put(index_rise_rate,   Map.value,      f'{k_base}_rise_rate')
        return compare

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
<<<<<<< HEAD
<<<<<<< HEAD
    def is_market_trend_deep_and_rise(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, fall_ceiling_rate: float, increase_rate: float, last_buy_time: int, is_int_round: bool = False, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        rounded_last_buy_time = _MF.round_time(last_buy_time, period)
        # Set trend
=======
    def is_tangent_market_trend_compare_zero(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, compare: str, index: int, is_int_round: bool, window: int = None) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        # Set mean
>>>>>>> Solomon-v2.0.2.2
        market_trend_df = cls.get_edited_market_trend(period, is_int_round, window)
        k_rise_rate, k_edited_rise_rate, edited_diff_rise_rate = cls.get_edited_market_trend_keys(is_int_round, window)
        k_market_date = 'market_date'
        # Get values
<<<<<<< HEAD
        open_times = list(marketprice.get_times())
        open_times.reverse()
        index_time = open_times[index]
        sub_market_trend_df = market_trend_df[market_trend_df.index <= index_time].iloc[-300:]
        index_date = _MF.unix_to_date(index_time)
        index_trend_date = sub_market_trend_df[k_market_date].iloc[-1]
        # Detect fall
        indexes = np.arange(stop=sub_market_trend_df.shape[0])
        sub_market_trend_df.insert(len(sub_market_trend_df.columns), Map.index, indexes)
        bellow_ceiling_df = sub_market_trend_df[(sub_market_trend_df[k_edited_rise_rate] <= fall_ceiling_rate)]
        above_ceiling_df = sub_market_trend_df[(sub_market_trend_df[k_edited_rise_rate] > fall_ceiling_rate) & (sub_market_trend_df[Map.time] < bellow_ceiling_df[Map.time].iloc[-1])] if bellow_ceiling_df.shape[0] > 0 else None
        start_fall_zones_df = bellow_ceiling_df[bellow_ceiling_df[Map.time] > above_ceiling_df[Map.time].iloc[-1]] if (above_ceiling_df is not None) and (above_ceiling_df.shape[0] > 0) else None
        index_fall_start = start_fall_zones_df.index[0] if (start_fall_zones_df is not None) and (start_fall_zones_df.shape[0] > 0) else None
        deep_fall = None
        rise_trigger = None
        fall_zone_start = None
        deep_fall_date = None
        is_above_trigger_continous = None
        is_rise_rate_still_rise = None
        has_bought = None
        time_reach_trigger = None
        date_reach_trigger = None
        if index_fall_start is not None:
            fall_zone_df = sub_market_trend_df[sub_market_trend_df.index >= index_fall_start]
            deep_fall = fall_zone_df[k_edited_rise_rate].min()
            rise_trigger = deep_fall + increase_rate
            fall_zone_start = _MF.unix_to_date(fall_zone_df.index[0])
            index_deep_fall = fall_zone_df[fall_zone_df[k_edited_rise_rate] == deep_fall].index[-1]
            deep_fall_date = _MF.unix_to_date(fall_zone_df[fall_zone_df[k_edited_rise_rate] == deep_fall].index[-1])
        if rise_trigger is not None:
            rise_zone_df = fall_zone_df[fall_zone_df.index >= index_deep_fall]
            above_trigger_df = rise_zone_df[rise_zone_df[k_edited_rise_rate] >= rise_trigger]
            mean_time_interval = above_trigger_df[Map.time].diff().mean()
            is_above_trigger_continous = (above_trigger_df.shape[0] == 1) or (mean_time_interval == period)
            is_rise_rate_still_rise = above_trigger_df[above_trigger_df[edited_diff_rise_rate] < 0].shape[0] == 0
            has_bought = rise_zone_df.index[0] <= rounded_last_buy_time <= rise_zone_df.index[-1]
            if above_trigger_df.shape[0] > 0:
                time_reach_trigger = above_trigger_df[Map.time].iloc[0] 
                date_reach_trigger = _MF.unix_to_date(time_reach_trigger)
        # Check
        rise_rate_at_index = sub_market_trend_df[k_edited_rise_rate].iloc[-1]
        rise_rate_at_prev_index = sub_market_trend_df[k_edited_rise_rate].iloc[-2]
        # deep_and_rise = bool((rise_trigger is not None) and (rise_rate_at_prev_index < rise_trigger) and (rise_rate_at_index >= rise_trigger))
        # deep_and_rise = bool((rise_trigger is not None) and (time_reach_trigger == index_time))
        deep_and_rise = bool((rise_trigger is not None) and (not has_bought) and (rise_rate_at_index >= rise_trigger) and is_above_trigger_continous and is_rise_rate_still_rise)
        # Report
        k_base = f'is_market_trend_deep_and_rise_{period_str}_{fall_ceiling_rate}_{increase_rate}[{index}]'
        vars_map.put(deep_and_rise,                 Map.condition,  k_base)
        vars_map.put(has_bought,                    Map.value,      f'{k_base}_has_bought')
        vars_map.put(is_above_trigger_continous,    Map.value,      f'{k_base}_is_above_trigger_continous')
        vars_map.put(is_rise_rate_still_rise,       Map.value,      f'{k_base}_is_rise_rate_still_rise')
        vars_map.put(index_date,                    Map.value,      f'{k_base}_index_date')
        vars_map.put(index_trend_date,              Map.value,      f'{k_base}_index_trend_date')
        vars_map.put(fall_zone_start,               Map.value,      f'{k_base}_fall_zone_start')
        vars_map.put(deep_fall_date,                Map.value,      f'{k_base}_deep_fall_date')
        vars_map.put(date_reach_trigger,            Map.value,      f'{k_base}_date_reach_trigger')
        vars_map.put(deep_fall,                     Map.value,      f'{k_base}_deep_fall')
        vars_map.put(rise_trigger,                  Map.value,      f'{k_base}_rise_trigger')
        vars_map.put(rise_rate_at_index,            Map.value,      f'{k_base}_rise_rate_at_index')
        vars_map.put(rise_rate_at_prev_index,       Map.value,      f'{k_base}_rise_rate_at_prev_index')
        return deep_and_rise

    @classmethod
=======
>>>>>>> Solomon-v5.1.1.2
    def is_macd_line_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, line_name: str, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
<<<<<<< HEAD
<<<<<<< HEAD
        now_time = marketprice.get_time()
=======
>>>>>>> Solomon-v5.1.1.2
=======
        now_time = marketprice.get_time()
>>>>>>> Solomon-v5.1.1.2.1
        macd_lines = marketprice.get_macd(**macd_params).get_map()
        macd_line = list(macd_lines[line_name])
        macd_line.reverse()
        # Check
        prev_index = index - 1
        macd_line_positive = macd_line[index] > 0
        # Put
        param_str = _MF.param_to_str(macd_params)
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Solomon-v5.1.1.2.1
        vars_map.put(macd_line_positive,            Map.condition,  f'is_{line_name}_positive_{period_str}[{index}]_{param_str}')
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_date')
        vars_map.put(macd_line[index],              Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_[{index}]')
        vars_map.put(macd_line[prev_index],         Map.value,      f'is_{line_name}_positive_{period_str}[{index}]_{param_str}_[{prev_index}]')
<<<<<<< HEAD
=======
        vars_map.put(macd_line_positive,    Map.condition,  f'is_{line_name}_positive_[{index}]_{param_str}_{period_str}')
        vars_map.put(macd_line[index],      Map.value,      f'is_{line_name}_positive_[{index}]_{param_str}_{period_str}[{index}]')
        vars_map.put(macd_line[prev_index], Map.value,      f'is_{line_name}_positive_[{index}]_{param_str}_{period_str}[{prev_index}]')
>>>>>>> Solomon-v5.1.1.2
=======
>>>>>>> Solomon-v5.1.1.2.1
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
    def compare_ema_and_keltner(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, comparator: str, keltner_line: str, \
        ema_params: dict = {}, keltner_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_date = _MF.unix_to_date(marketprice.get_time())
        marketprice_df = marketprice.to_pd()
        index_date = _MF.unix_to_date(marketprice_df[Map.time].iloc[index])
        # EMA
        ema = marketprice.get_ema(**ema_params)
        ema = list(ema)
        ema.reverse()
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        # Check
        ema_price = ema[index]
        keltner_price = keltner[index]
        compare = _MF.compare_first_and_second(comparator, ema_price, keltner_price)
        # Put
        prev_index = index - 1
        keltner_params_str = _MF.param_to_str(keltner_params)
        ema_param_str = _MF.param_to_str(ema_params)
        params_str = Map.key(keltner_params_str, ema_param_str)
        k_base = f'compare_ema_{comparator}_keltner[{keltner_line}]_{period_str}_{params_str}[{index}]'
        vars_map.put(compare,               Map.condition,  k_base)
        vars_map.put(now_date,              Map.value,      f'{k_base}_now_date')
        vars_map.put(index_date,            Map.value,      f'{k_base}_index_date')
        vars_map.put(keltner[index],        Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, keltner_params_str)}[{index}]')
        vars_map.put(keltner[prev_index],   Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, keltner_params_str)}[{prev_index}]')
        vars_map.put(ema[index],            Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str)}[{index}]')
        vars_map.put(ema[prev_index],       Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str)}[{prev_index}]')
        return compare

    @classmethod
    def compare_exetrem_ema_and_keltner(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, \
        comparator: str, ema_exetrem: str, keltner_line: str, ema_params: dict = {}, keltner_params: dict = {}) -> bool:
        _MF.check_allowed_values(ema_exetrem, [Map.minimum, Map.maximum])
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
        now_time = marketprice.get_time()
        # EMA
        k_ema_diff = Map.key(Map.ema, 'diff')
        ema = marketprice.get_ema(**ema_params)
        ema = list(ema)
        ema.reverse()
        marketprice_df[Map.ema] = pd.Series(ema, index=marketprice_df.index)
        marketprice_df[k_ema_diff] = marketprice_df[Map.ema].diff()
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner = list(keltner_map.get_map()[keltner_line])
        keltner.reverse()
        marketprice_df[Map.keltner] = pd.Series(keltner, index=marketprice_df.index)
        # Index
        index_time = marketprice_df[Map.time].iloc[index]
        sub_marketprice_df = marketprice_df[marketprice_df[Map.time] <= index_time]
        # Cook
        index_ema_extrem = sub_marketprice_df[sub_marketprice_df[k_ema_diff] < 0].index[-1] if ema_exetrem == Map.minimum else sub_marketprice_df[sub_marketprice_df[k_ema_diff] > 0].index[-1]
        extrem_time = sub_marketprice_df[Map.time][index_ema_extrem]
        # Check
        extrem_ema = sub_marketprice_df[Map.ema][index_ema_extrem]
        keltner_at_extrem_ema = sub_marketprice_df[Map.keltner][index_ema_extrem]
        compare = bool(_MF.compare_first_and_second(comparator, extrem_ema, keltner_at_extrem_ema))
        # Put
        prev_index = index - 1
        keltner_params_str = _MF.param_to_str(keltner_params)
        ema_param_str = _MF.param_to_str(ema_params)
        params_str = Map.key(keltner_params_str, ema_param_str)
        k_base = f'is_{ema_exetrem}_ema_{comparator}_keltner_{keltner_line}_{period_str}_{params_str}'
        vars_map.put(compare,                       Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_date')
        vars_map.put(_MF.unix_to_date(index_time),  Map.value,      f'{k_base}_index_date')
        vars_map.put(_MF.unix_to_date(extrem_time), Map.value,      f'{k_base}_extrem_date')
        vars_map.put(ema[index],                    Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str)}[{index}]')
        vars_map.put(ema[prev_index],               Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str)}[{prev_index}]')
        vars_map.put(extrem_ema,                    Map.value,      f'{k_base}_extrem_ema')
        vars_map.put(keltner[index],                Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, keltner_params_str)}[{index}]')
        vars_map.put(keltner[prev_index],           Map.value,      f'{Map.key(Map.keltner, keltner_line,    period_str, keltner_params_str)}[{prev_index}]')
        vars_map.put(keltner_at_extrem_ema,         Map.value,      f'{k_base}_keltner_at_extrem_ema')
        return compare

    @classmethod
    def compare_emas(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, comparator: str, ema_params_1: dict = {}, ema_params_2: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_date = _MF.unix_to_date(marketprice.get_time())
        marketprice_df = marketprice.to_pd()
        index_date = _MF.unix_to_date(marketprice_df[Map.time].iloc[index])
        # EMA 1
        ema_1 = marketprice.get_ema(**ema_params_1)
        ema_1 = list(ema_1)
        ema_1.reverse()
        # EMA 2
        ema_2 = marketprice.get_ema(**ema_params_2)
        ema_2 = list(ema_2)
        ema_2.reverse()
        # Check
        ema_price_1 = ema_1[index]
        ema_price_2 = ema_2[index]
        compare = _MF.compare_first_and_second(comparator, ema_price_1, ema_price_2)
        # Put
        prev_index = index - 1
        ema_param_str_1 = _MF.param_to_str(ema_params_1)
        ema_param_str_2 = _MF.param_to_str(ema_params_2)
        params_str = Map.key(ema_param_str_1, ema_param_str_2)
        k_base = f'compare_ema1_{comparator}_ema2_{period_str}_{params_str}[{index}]'
        vars_map.put(compare,           Map.condition,  k_base)
        vars_map.put(now_date,          Map.value,      f'{k_base}_now_date')
        vars_map.put(index_date,        Map.value,      f'{k_base}_index_date')
        vars_map.put(ema_1[index],      Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str_1)}[{index}]')
        vars_map.put(ema_1[prev_index], Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str_1)}[{prev_index}]')
        vars_map.put(ema_2[index],      Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str_2)}[{index}]')
        vars_map.put(ema_2[prev_index], Map.value,      f'{Map.key(Map.ema, period_str, ema_param_str_2)}[{prev_index}]')
        return compare

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
    def compare_rsi_and_trigger(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, comparator: str, trigger: float, rsi_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        rsi = list(marketprice.get_rsis(**rsi_params))
        rsi.reverse()
        # Check
        prev_index = index - 1
        compare = _MF.compare_first_and_second(comparator, rsi[index], trigger)
        # Put
        rsi_param_str = _MF.param_to_str(rsi_params)
        k_base = f'compare_rsi_{comparator}_{trigger}_{period_str}_{rsi_param_str}[{index}]'
        vars_map.put(compare,                       Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),    Map.value,      f'{k_base}_now_date')
        vars_map.put(rsi[index],                    Map.value,      f'{Map.key(Map.rsi, period_str, rsi_param_str)}[{index}]')
        vars_map.put(rsi[prev_index],               Map.value,      f'{Map.key(Map.rsi, period_str, rsi_param_str)}[{prev_index}]')
        return compare

    @classmethod
    def is_price_deep_enough(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, \
        keltner_line: str, macd_line: str, keltner_params: dict = {}, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        marketprice_df = marketprice.to_pd()
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
    def keltner_zone(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, price_line: str, keltner_params: dict = {}) -> str:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_date = _MF.unix_to_date(marketprice.get_time())
        marketprice_df = marketprice.to_pd()
        index_date = _MF.unix_to_date(marketprice_df[Map.time].iloc[index])
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner_high = list(keltner_map.get_map()[Map.high])
        keltner_high.reverse()
        keltner_middle = list(keltner_map.get_map()[Map.middle])
        keltner_middle.reverse()
        keltner_low = list(keltner_map.get_map()[Map.low])
        keltner_low.reverse()
        keltner = {
            Map.high:   keltner_high, 
            Map.middle: keltner_middle, 
            Map.low:    keltner_low
            }
        # Check
        market_price = marketprice_df[price_line].iloc[index]
        if market_price >= keltner[Map.high][index]:
            zone = cls.KELTNER_ZONE_H_INF   # 'HIGH_INFINITY'
        elif keltner[Map.middle][index] <= market_price < keltner[Map.high][index]:
            zone = cls.KELTNER_ZONE_M_H     # 'MIDDLE_HIGH'
        elif keltner[Map.low][index] <= market_price < keltner[Map.middle][index]:
            zone = cls.KELTNER_ZONE_L_M     # 'LOW_MIDDLE'
        elif market_price < keltner[Map.low][index]:
            zone = cls.KELTNER_ZONE_INF_L   # 'INFINITY_LOW'
        # Put
        prev_index = index - 1
        params_str = _MF.param_to_str(keltner_params)
        k_base = f'keltner_zone_price[{price_line}]_{period_str}_{params_str}[{index}]'
        k_keltner = Map.key(Map.keltner, params_str)
        vars_map.put(zone,                              Map.value,      k_base)
        vars_map.put(now_date,                          Map.value,      f'{k_base}_now_date')
        vars_map.put(index_date,                        Map.value,      f'{k_base}_index_date')
        vars_map.put(keltner[Map.high][index],          Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{index}]')
        vars_map.put(keltner[Map.high][prev_index],     Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, params_str)}[{prev_index}]')
        vars_map.put(keltner[Map.middle][index],        Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, params_str)}[{index}]')
        vars_map.put(keltner[Map.middle][prev_index],   Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, params_str)}[{prev_index}]')
        vars_map.put(keltner[Map.low][index],           Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{index}]')
        vars_map.put(keltner[Map.low][prev_index],      Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, params_str)}[{prev_index}]')
        return zone

    @classmethod
    def sell_price(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, risk_level: str, keltner_zone: str, keltner_params: dict = {}) -> float:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_date = _MF.unix_to_date(marketprice.get_time())
        marketprice_df = marketprice.to_pd()
        index_date = _MF.unix_to_date(marketprice_df[Map.time].iloc[index])
        # Keltner
        keltner_map = marketprice.get_keltnerchannel(**keltner_params)
        keltner_high = list(keltner_map.get_map()[Map.high])
        keltner_high.reverse()
        keltner_middle = list(keltner_map.get_map()[Map.middle])
        keltner_middle.reverse()
        keltner_low = list(keltner_map.get_map()[Map.low])
        keltner_low.reverse()
        keltner = {
            Map.high:   keltner_high, 
            Map.middle: keltner_middle, 
            Map.low:    keltner_low
            }
        # Check
        zone_L_INF = [cls.KELTNER_ZONE_H_INF, cls.KELTNER_ZONE_M_H, cls.KELTNER_ZONE_L_M]
        sellPrice = None
        if ( risk_level == cls.RISK_SAFE ) and (keltner_zone in zone_L_INF):
            sellPrice = keltner[Map.middle][index]
        elif ( risk_level == cls.RISK_SAFE ) and (keltner_zone == cls.KELTNER_ZONE_INF_L):
            sellPrice = keltner[Map.high][index]
        elif ( risk_level == cls.RISK_MODERATE ) and (keltner_zone in zone_L_INF):
            sellPrice = None
        elif ( risk_level == cls.RISK_MODERATE ) and (keltner_zone == cls.KELTNER_ZONE_INF_L):
            sellPrice = keltner[Map.middle][index]
        # Put
        prev_index = index - 1
        keltner_params_str = _MF.param_to_str(keltner_params)
        k_base = f'sell_price_{period_str}_{keltner_params_str}[{index}]'
        vars_map.put(sellPrice,                         Map.value,      f'{k_base}_sellPrice')
        vars_map.put(now_date,                          Map.value,      f'{k_base}_now_date')
        vars_map.put(index_date,                        Map.value,      f'{k_base}_index_date')
        vars_map.put(risk_level,                        Map.value,      f'{k_base}_risk_level')
        vars_map.put(keltner_zone,                      Map.value,      f'{k_base}_keltner_zone')
        vars_map.put(keltner[Map.high][index],          Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, keltner_params_str)}[{index}]')
        vars_map.put(keltner[Map.high][prev_index],     Map.value,      f'{Map.key(Map.keltner, Map.high,   period_str, keltner_params_str)}[{prev_index}]')
        vars_map.put(keltner[Map.middle][index],        Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, keltner_params_str)}[{index}]')
        vars_map.put(keltner[Map.middle][prev_index],   Map.value,      f'{Map.key(Map.keltner, Map.middle, period_str, keltner_params_str)}[{prev_index}]')
        vars_map.put(keltner[Map.low][index],           Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, keltner_params_str)}[{index}]')
        vars_map.put(keltner[Map.low][prev_index],      Map.value,      f'{Map.key(Map.keltner, Map.low,    period_str, keltner_params_str)}[{prev_index}]')
        return sellPrice

    @classmethod
    def is_macd_from_negative(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int, macd_params: dict = {}) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        marketprice.reset_collections()
        now_time = marketprice.get_time()
        market_times = list(marketprice.get_times())
        market_times.reverse()
        macd_lines = marketprice.get_macd(**macd_params).get_map()
        macd_macd, macd_signal, macd_histogram = list(macd_lines[Map.macd]), list(macd_lines[Map.signal]), list(macd_lines[Map.histogram])
        [macd_line.reverse() for macd_line in [macd_macd, macd_signal, macd_histogram]]
        # Prepare
        n_histogram = len(macd_histogram)
        index_positive = n_histogram + index if index < 0 else index
        zeros = np.zeros((n_histogram,)).tolist()
        histogram_zero_swings = _MF.group_swings(macd_histogram, zeros)
        # is_histogram_positive = macd_histogram[index] > 0
        switch_start_index = histogram_zero_swings[index_positive][0]
        switch_end_index = histogram_zero_swings[index_positive][1]
        macd_df = pd.DataFrame({Map.macd: macd_macd, Map.signal: macd_signal, Map.histogram: macd_histogram})
        swing_macd_df = macd_df.loc[switch_start_index:index_positive+1]
        negative_swing_macd_df = swing_macd_df[(swing_macd_df[Map.macd] < 0) & (swing_macd_df[Map.signal] < 0)]
        # Report
        date_switch_start_index = _MF.unix_to_date(market_times[switch_start_index])
        date_switch_end_index = _MF.unix_to_date(market_times[switch_end_index])
        date_start_negative_swing = None
        date_end_negative_swing = None
        if negative_swing_macd_df.shape[0] > 0:
            date_start_negative_swing = _MF.unix_to_date(market_times[negative_swing_macd_df[Map.macd].index[0]])
            date_end_negative_swing = _MF.unix_to_date(market_times[negative_swing_macd_df[Map.macd].index[-1]])
        # Check
        macd_from_negative = negative_swing_macd_df.shape[0] > 0
        # Put
        prev_index = index - 1
        param_str = _MF.param_to_str(macd_params)
        k_base = f'is_macd_from_negative_{period_str}[{index}]_{param_str}'
        vars_map.put(macd_from_negative,                    Map.condition,  k_base)
        vars_map.put(_MF.unix_to_date(now_time),            Map.value,      f'{k_base}_date')
        vars_map.put(_MF.unix_to_date(market_times[index]), Map.value,      f'{k_base}_index_date')
        vars_map.put(n_histogram,                           Map.value,      f'{k_base}_n_histogram')
        vars_map.put(index_positive,                        Map.value,      f'{k_base}_index_positive')
        vars_map.put(date_switch_start_index,               Map.value,      f'{k_base}_date_switch_start_index')
        vars_map.put(date_switch_end_index,                 Map.value,      f'{k_base}_date_switch_end_index')
        vars_map.put(date_start_negative_swing,             Map.value,      f'{k_base}_date_start_negative_swing')
        vars_map.put(date_end_negative_swing,               Map.value,      f'{k_base}_date_end_negative_swing')
        vars_map.put(macd_macd[index],                      Map.value,      f'{k_base}_macd_macd[{index}]')
        vars_map.put(macd_macd[prev_index],                 Map.value,      f'{k_base}_macd_macd[{prev_index}]')
        vars_map.put(macd_signal[index],                    Map.value,      f'{k_base}_macd_signal[{index}]')
        vars_map.put(macd_signal[prev_index],               Map.value,      f'{k_base}_macd_signal[{prev_index}]')
        vars_map.put(macd_histogram[index],                 Map.value,      f'{k_base}_macd_histogram[{index}]')
        vars_map.put(macd_histogram[prev_index],            Map.value,      f'{k_base}_macd_histogram[{prev_index}]')
        return macd_from_negative
=======
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
>>>>>>> Solomon-v2.0.2.2

    @classmethod
    def param_to_str(cls, params: dict) -> str:
        param_str = ''
        if len(params) > 0:
            for key, value in params.items():
                param_str += f'{key}={value}' if len(param_str) == 0 else f'_{key}={value}'
        return param_str

    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trades: list[dict], trade: dict, buy_conditions: list, sell_conditions: list) -> None:
<<<<<<< HEAD
        def is_order_set(side: str) -> bool:
            return trade[side] is not None
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
<<<<<<< HEAD
            buy_datas = {}
            buy_datas[Map.buy] = trades[-1][Map.buy][Map.time] if len(trades) > 0 else None
            can_buy, buy_condition, buy_case = cls.can_buy(broker, pair, marketprices, buy_datas)
=======
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            last_trade = trades[-1] if len(trades) > 0 else None
            buy_params = {}
            buy_params[Map.time] =  last_trade[Map.sell][Map.time] if last_trade is not None else 0
            buy_params[Map.roi] =   last_trade[Map.roi]() if last_trade is not None else 123
            can_buy, buy_condition, max_loss_price = cls.can_buy(broker, pair, marketprices, buy_params)
>>>>>>> Solomon-v2.0.2.2
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_MARKET, exec_type=Map.open)
<<<<<<< HEAD
                trade[Map.condition] = buy_case
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            sell_datas = trade[Map.condition]
            sell_datas[Map.time] =      trade[Map.buy][Map.time]
            sell_datas[Map.buy] =       trade[Map.buy][Map.execution]
            sell_datas[Map.fee] =       trade[Map.buy][Map.fee]
            can_sell, sell_condition, sell_price = cls.can_sell(broker, pair, marketprices, sell_datas)
=======
            can_buy, buy_condition = cls.can_buy(broker, pair, marketprices)
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_MARKET, exec_type=Map.close)
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            sell_datas = {}
            sell_datas[Map.time] = trade[Map.buy][Map.time]
            can_sell, sell_condition = cls.can_sell(broker, pair, marketprices, sell_datas)
>>>>>>> Solomon-v5.1.3
            sell_condition = cls._backtest_condition_add_prefix(sell_condition, pair, marketprice)
            sell_conditions.append(sell_condition)
            # Manage Order
            if can_sell:
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.close)
            elif sell_price is not None:
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_LIMIT, limit=sell_price)
=======
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
>>>>>>> Solomon-v2.0.2.2
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

    @classmethod
    def get_path(cls, option: str) -> str:
        if option == Map.left:
            class_name = cls.__name__
            storage_strategy_dir_path = Config.get(Config.DIR_STRATEGY_STORAGE)
            path = storage_strategy_dir_path + f'{class_name}/pairs/tradable.csv'
        return path

=======
>>>>>>> Noah-v1
    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Solomon.__new__(Solomon)
        exec(MyJson.get_executable())
        return instance

    # ––––––––––––––––––––––––––––––––––––––––––– STATIC UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
<<<<<<< HEAD
    
=======
>>>>>>> Noah-v1
