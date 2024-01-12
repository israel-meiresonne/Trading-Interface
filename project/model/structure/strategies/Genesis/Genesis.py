import time
from typing import Callable, List

import pandas as pd

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair


class Genesis(Strategy):
    PREFIX_ID =         'genesis_'
    KELTER_SUPPORT =    None

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STALK DOWN

    def _manage_stalk(self) -> None:
        while self.is_stalk_on():
            _MF.catch_exception(self._stalk_market, self.__class__.__name__) if not self.is_max_position_reached() else None
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _stalk_market(self) -> List[Pair]:
        pass

    # ——————————————————————————————————————————— STALK UP
    # ——————————————————————————————————————————— TRADE DOWN

    def _trade_inner(self) -> None:
        pass

    # ——————————————————————————————————————————— TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————
    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST DOWN

    @classmethod
<<<<<<< HEAD
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trades: list[dict], trade: dict, buy_conditions: list, sell_conditions: list) -> None:
        pass
=======
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
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
        TRIGGE_KELTNER = 2/100
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in [period_1min]}
        # Params
        now_index = -1
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
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_keltner_roi_above_trigger,        Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, trigge_keltner=TRIGGE_KELTNER, index=now_index)},
            {Map.callback: cls.is_tangent_rsi_positive,             Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)}
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        can_buy = cls.is_tangent_market_trend_positive(**func_and_params[0][Map.param]) \
            and cls.is_keltner_roi_above_trigger(**func_and_params[1][Map.param]) \
            and cls.is_tangent_rsi_positive(**func_and_params[2][Map.param]) \
            and cls.is_supertrend_rising(**func_and_params[3][Map.param])
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_buy, vars_map)
        return can_buy, report

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        marketprice_1min = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_1min_pd = marketprice_1min.to_pd()
        period_strs = {period: broker.period_to_str(period) for period in [period_1min]}
        # Params
        now_index = -1
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
        this_func = cls.can_sell
        func_and_params = [
            {Map.callback: cls.is_tangent_market_trend_positive,    Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_5min, marketprices=marketprices, index=now_index)},
            {Map.callback: cls.is_supertrend_rising,                Map.param: dict(vars_map=vars_map, broker=broker, pair=pair, period=period_1min, marketprices=marketprices, index=now_index)}
        ]
        header_dict = cls._can_buy_sell_set_headers(this_func, func_and_params)
        # Check
        can_sell = not cls.is_tangent_market_trend_positive(**func_and_params[0][Map.param]) \
            or not cls.is_supertrend_rising(**func_and_params[1][Map.param])
        # Report
        report = cls._can_buy_sell_new_report(this_func, header_dict, can_sell, vars_map)
        return can_sell, report

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
    def is_tangent_rsi_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        rsis = list(marketprice.get_rsis())
        rsis.reverse()
        # Check
        open_date = _MF.unix_to_date(marketprice.get_time())
        prev_index = index - 1
        tangent_rsi_positive = rsis[index] > rsis[prev_index]
        # Put
        vars_map.put(tangent_rsi_positive,  Map.condition,  f'tangent_rsi_positive_{period_str}[{index}]')
        vars_map.put(rsis[index],           Map.value,      f'tangent_rsi_positive_rsi_{period_str}[{index}]')
        vars_map.put(rsis[prev_index],      Map.value,      f'tangent_rsi_positive_rsi_{period_str}[{prev_index}]')
        vars_map.put(open_date,             Map.value,      f'tangent_rsi_positive_open_date_{period_str}[{index}]')
        return tangent_rsi_positive

    @classmethod
    def is_tangent_market_trend_positive(cls, vars_map: Map, broker: Broker, pair: Pair, period: int, marketprices: Map, index: int) -> bool:
        period_str = broker.period_to_str(period)
        marketprice = cls._marketprice(broker, pair, period, marketprices)
        market_trend_df = cls.get_market_trend(period)
        now_time = marketprice.get_time()
        now_date = _MF.unix_to_date(now_time)
        sub_market_trend_df = market_trend_df[market_trend_df.index <= now_time]
        prev_index = index - 1
        now_trend_date = sub_market_trend_df['market_date'].iloc[index]
        prev_trend_date = sub_market_trend_df['market_date'].iloc[prev_index]
        # Check
        now_rise_rate = sub_market_trend_df['rise_rate'].iloc[index]
        prev_rise_rate = sub_market_trend_df['rise_rate'].iloc[prev_index]
        tangent_positive = now_rise_rate > prev_rise_rate
        # Report
        vars_map.put(tangent_positive,  Map.condition,  f'tangent_market_trend_positive_{period_str}[{index}]')
        vars_map.put(now_date,          Map.value,      f'tangent_trend_now_date{period_str}[{index}]')
        vars_map.put(now_trend_date,    Map.value,      f'tangent_trend_now_trend_date{period_str}[{index}]')
        vars_map.put(prev_trend_date,   Map.value,      f'tangent_trend_prev_trend_date{period_str}[{prev_index}]')
        vars_map.put(now_rise_rate,     Map.value,      f'tangent_trend_now_rise_rate{period_str}[{index}]')
        vars_map.put(prev_rise_rate,    Map.value,      f'tangent_trend_prev_rise_rate{period_str}[{prev_index}]')
        return tangent_positive



    @classmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, trade: dict, buy_conditions: list, sell_conditions: list) -> dict:
        period_1min = Broker.PERIOD_1MIN
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        if (trade is None) or (trade[Map.buy][Map.status] != Order.STATUS_COMPLETED):
            can_buy, buy_condition = cls.can_buy(broker, pair, marketprices)
            buy_condition = cls._backtest_condition_add_prefix(buy_condition, pair, marketprice)
            buy_conditions.append(buy_condition)
            if can_buy:
                trade = cls._backtest_new_trade(broker, marketprices, pair, Order.TYPE_MARKET, exec_type=Map.close)
        elif trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            can_sell, sell_condition = cls.can_sell(broker, pair, marketprices)
            sell_condition = cls._backtest_condition_add_prefix(sell_condition, pair, marketprice)
            sell_conditions.append(sell_condition)
            if can_sell:
                cls._backtest_trade_set_sell_order(broker, marketprices, trade, Order.TYPE_MARKET, exec_type=Map.close)
        return trade
>>>>>>> Genesis-v1

    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST UP
    # ––––––––––––––––––––––––––––––––––––––––––– STATIC DOWN

    @classmethod
    def get_market_trend(cls, period: int) -> pd.DataFrame:
        _MF.check_type(period, int)
        MARKET_TRENDS = 'MARKET_TRENDS'
        stage = Config.get(Config.STAGE_MODE)
        if stage == Config.STAGE_1:
            _stack = cls.get_stack()
            market_trend_df = _stack.get(MARKET_TRENDS, period)
            if market_trend_df is None:
                strategy_storage_dir = Config.get(Config.DIR_STRATEGY_STORAGE)
                market_trend_file = f"{strategy_storage_dir}{cls.__name__}/market_trend/supertrend/{period}.csv"
                project_dir = FileManager.get_project_directory()
                market_trend_df = pd.read_csv(project_dir + market_trend_file, index_col=0)
                _stack.put(market_trend_df, MARKET_TRENDS, period)
        else:
            raise Exception(f"Behavior not implemeted for this stage '{stage}'")
        return market_trend_df

    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST UP
    # ––––––––––––––––––––––––––––––––––––––––––– STATIC DOWN

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Genesis.__new__(Genesis)
        exec(MyJson.get_executable())
        return instance

    # ––––––––––––––––––––––––––––––––––––––––––– STATIC UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
    