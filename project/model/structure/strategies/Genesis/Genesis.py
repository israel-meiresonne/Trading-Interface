import time
from typing import List

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

    def _trade_inner(self) -> None:
        pass

    # ••• TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————
    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST DOWN

    @classmethod
    def can_buy(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        func_name = cls.can_buy.__name__
        _stack = cls.get_stack()
        """
        _stack[func_name][Map.condition]:   {list}  # boolean column names
        _stack[func_name][Map.value]:       {list}  # values column names
        """
        var_map_keys = _stack.get(func_name)
        index_now = -1
        if var_map_keys is None:
            cls.is_tangent_market_trend_positive(vars_map, broker, pair, period_5min, marketprices, index_now)
            cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices, index_now)
            new_var_map_keys = vars_map.get_keys()
            for new_var_map_key in new_var_map_keys:
                columns = list(vars_map.get(new_var_map_key).keys())
                _stack.put(columns, func_name, new_var_map_key)
            var_map_keys = _stack.get(func_name)
        # Check
        can_buy = cls.is_tangent_market_trend_positive(vars_map, broker, pair, period_5min, marketprices, index_now) \
            and cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices, index_now)
        # Report
        boolean_keys = var_map_keys[Map.condition]
        values_keys = var_map_keys[Map.value]
        report = {
            func_name:      can_buy,
            **{boolean_key: vars_map.get(Map.condition, boolean_key) for boolean_key in boolean_keys},
            **{values_key:  vars_map.get(Map.value, values_key) for values_key in values_keys}
        }
        return can_buy, report

    @classmethod
    def can_sell(cls, broker: Broker, pair: Pair, marketprices: Map) -> tuple[bool, dict]:
        vars_map = Map()
        period_1min = Broker.PERIOD_1MIN
        period_5min = Broker.PERIOD_5MIN
        func_name = cls.can_sell.__name__
        _stack = cls.get_stack()
        """
        _stack[func_name][Map.condition]:   {list}  # boolean column names
        _stack[func_name][Map.value]:       {list}  # values column names
        """
        var_map_keys = _stack.get(func_name)
        index_now = -1
        if var_map_keys is None:
            cls.is_tangent_market_trend_positive(vars_map, broker, pair, period_5min, marketprices, index_now)
            cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices, index_now)
            new_var_map_keys = vars_map.get_keys()
            for new_var_map_key in new_var_map_keys:
                columns = list(vars_map.get(new_var_map_key).keys())
                _stack.put(columns, func_name, new_var_map_key)
            var_map_keys = _stack.get(func_name)
        # Check
        can_sell = not cls.is_tangent_market_trend_positive(vars_map, broker, pair, period_5min, marketprices, index_now) \
            or not cls.is_supertrend_rising(vars_map, broker, pair, period_1min, marketprices, index_now)
        # Report
        boolean_keys = var_map_keys[Map.condition]
        values_keys = var_map_keys[Map.value]
        report = {
            func_name:      can_sell,
            **{boolean_key: vars_map.get(Map.condition, boolean_key) for boolean_key in boolean_keys},
            **{values_key:  vars_map.get(Map.value, values_key) for values_key in values_keys}
        }
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

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Genesis.__new__(Genesis)
        exec(MyJson.get_executable())
        return instance

    # ––––––––––––––––––––––––––––––––––––––––––– STATIC UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
    