import time
<<<<<<< HEAD
from typing import Callable, List, Tuple

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
=======
from typing import List


from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.MyJson import MyJson
>>>>>>> Solomon-v5.4.4.2.2
from model.tools.Pair import Pair


class Noah(Strategy):
    PREFIX_ID =             'noah_'
<<<<<<< HEAD
    KELTNER_MULTIPLE_1 =    1
=======
>>>>>>> Solomon-v5.4.4.2.2
    KELTER_SUPPORT =        None

    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ••• STALK DOWN

    def _manage_stalk(self) -> None:
        while self.is_stalk_on():
            _MF.catch_exception(self._stalk_market, self.__class__.__name__) if not self.is_max_position_reached() else None
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _stalk_market(self) -> List[Pair]:
<<<<<<< HEAD
        def write(rows: List[dict], condition: Callable) -> None:
            file_path = self.get_path_file_stalk(condition)
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)
        stalk_pairs = self._get_stalk_pairs()
        marketprices = Map()
        repports = []
        stalk_start_date = _MF.unix_to_date(_MF.get_timestamp())
        period_1min = Broker.PERIOD_1MIN
        bought_pairs = []
        for stalk_pair in stalk_pairs:
            row_start_date = _MF.unix_to_date(_MF.get_timestamp())
            _, repport = self._can_buy(stalk_pair, marketprices)
            marketprice_1min = self._marketprice(stalk_pair, period_1min, marketprices)
            repport = {
                'stalk_start_date': stalk_start_date,
                'row_start_date': row_start_date,
                'market_date': _MF.unix_to_date(marketprice_1min.get_time()),
                Map.pair: stalk_pair,
                **repport
            }
            repports.append(repport)
        repports_df = pd.DataFrame(repports)
        can_buy_df = repports_df.loc[repports_df[Map.buy] == True]
        if can_buy_df.shape[0] > 0:
            can_buy_sorted = can_buy_df.sort_values(by=['keltner_roi'], ascending=False)
            for row_index in can_buy_sorted.index:
                buy_pair = repports_df.loc[row_index, Map.pair]
                buy_price = repports_df.loc[row_index, Map.price]
                self.buy(buy_pair, Order.TYPE_LIMIT, limit=buy_price)
                bought_pairs.append(buy_pair)
                if self.is_max_position_reached():
                    break
        write(repports, self._can_buy)
        return bought_pairs
=======
        pass
>>>>>>> Solomon-v5.4.4.2.2

    # ••• STALK UP
    # ••• TRADE DOWN

<<<<<<< HEAD
<<<<<<< HEAD
    def _trade_inner(self) -> None:
        pass
=======
    def trade(self) -> int:
        self._update_orders()
        self._try_buy_sell()
        return self.get_sleep_trade()

    def _try_buy_sell(self) -> None:
        positions = self.get_positions()
        self._move_closed_positions(positions)
        marketprices = Map()
        for pair_str, position in positions.items():
            if position.has_position():
                pair = Pair(pair_str)
                self._try_sell(pair, marketprices)
            elif not position.is_executed(Map.buy):
                pass
            else:
                raise Exception(f"Unkwown case: pair='{pair_str.upper()}', bought='{position.is_executed(Map.buy)}', sold='{position.is_executed(Map.sell)}'")

    def _can_buy(self, pair: Pair, marketprices: Map) -> Tuple[bool, dict]:
        TRIGGER_KELTNER_ROI = 2/100
        period_5min = Broker.PERIOD_5MIN
        def is_keltner_support_ok(vars_map: Map) -> bool:
            buy_price = None
            keltner_support = self.get_keltner_support()
            key_keltner_support = self.get_keltner_support_key(pair, marketprices)
            buy_instruction = keltner_support.loc[key_keltner_support, Map.buy]
            buy_price = self.keltner_support_to_price(pair, buy_instruction, marketprices)
            keltner_support_ok = isinstance(buy_price, [int, float])
            vars_map.put(keltner_support_ok, 'keltner_support_ok')
            vars_map.put(key_keltner_support, 'key_keltner_support')
            vars_map.put(buy_price, 'buy_price')
            vars_map.put(buy_instruction, 'buy_instruction')
            return keltner_support_ok
        vars_map = Map()
        marketprice_5min = self._marketprice(pair, period_5min, marketprices)
        # Check
        can_buy = self._stalk_is_keltner_roi_above_trigger(vars_map, marketprice_5min, TRIGGER_KELTNER_ROI) and\
            is_keltner_support_ok(vars_map)
        # Repport
        repport = {
            Map.buy: can_buy,
            'keltner_roi_above_trigger': vars_map.get('keltner_roi_above_trigger'),
            'keltner_support_ok': vars_map.get('keltner_support_ok'),

            'keltner_roi': vars_map.get('keltner_roi'),
            'keltner_roi_trigger': vars_map.get('keltner_roi_trigger'),
            
            'key_keltner_support': vars_map.get('key_keltner_support'),
            Map.price: vars_map.get('buy_price'),
            'buy_instruction': vars_map.get('buy_instruction')
        }
        # End
        return can_buy, repport

    def _try_sell(self, pair: Pair, marketprices: Map) -> None:
        def write(rows: List[dict], pair: Pair) -> None:
            file_path_pattern = Config.get(Config.DIR_SAVE_SELL_CONDITIONS)
            file_path = file_path_pattern.replace('_$pair', '')
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)
        position = self.get_position(pair)
        if position.get_sell_order() is None:
            keltner_support = self.get_keltner_support()
            key_keltner_support = self.get_keltner_support_key(pair, marketprices)
            sell_instruction = keltner_support.loc[key_keltner_support, Map.sell]
            sell_price = self.keltner_support_to_price(pair, sell_instruction, marketprices)
            self.sell(pair, Order.TYPE_LIMIT, limit=sell_price) if isinstance(sell_price, [int, float]) else self.sell(pair, Order.TYPE_MARKET)
            # Repport
            period_1min = Broker.PERIOD_1MIN
            marketprice_1min = self._marketprice(pair, period_1min, marketprices)
            repport = [{
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                'market_date': _MF.unix_to_date(marketprice_1min.get_time()),
                Map.pair: pair,
                'key_keltner_support': key_keltner_support,
                'sell_instruction': sell_instruction,
                'sell_price': sell_price
            }]
            write(repport, pair)

    def get_keltner_support_key(self, pair: Pair, marketprices: Map) -> str:
        def is_supertrend_rising(marketprice: MarketPrice) -> bool:
            closes = list(marketprice.get_closes())
            closes.reverse()
            supertrend = list(marketprice.get_super_trend())
            supertrend.reverse()
            return MarketPrice.get_super_trend_trend(closes, supertrend, -1) == MarketPrice.SUPERTREND_RISIN
        def is_psar_rising(marketprice: MarketPrice) -> bool:
            closes = list(marketprice.get_closes())
            closes.reverse()
            psar = list(marketprice.get_psar())
            psar.reverse()
            return MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_RISING
        periods = [
            Broker.PERIOD_1MIN,
            Broker.PERIOD_5MIN,
            Broker.PERIOD_15MIN
        ]
        periods.sort()
        teeths = []
        for period in periods:
            marketprice = self._marketprice(pair, period, marketprices)
            psar_rising = str(is_psar_rising(marketprice)).upper()
            supertrend_rising = str(is_supertrend_rising(marketprice)).upper()
            teeths.append(psar_rising)
            teeths.append(supertrend_rising)
        key = '_'.join(teeths)
        return key

    def keltner_support_to_price(self, pair: Pair, instruction: str, marketprices: Map) -> float:
        price = None
        infos = instruction.split("_")
        if len(infos) == 3:
            broker = self.get_broker()
            line = infos[1]
            period_str = infos[2]
            period = broker.str_to_period(period_str)
            marketprice = self._marketprice(pair, period, marketprices)
            keltner_map = marketprice.get_keltnerchannel(multiple=self.KELTNER_MULTIPLE_1)
            keltner = list(keltner_map.get_map()[line])
            keltner.reverse()
            price = keltner[-1]
        return price
>>>>>>> Noah-v1
=======
    def _trade_inner(self) -> None:
        pass
>>>>>>> Solomon-v5.4.4.2.2

    # ••• TRADE UP
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

<<<<<<< HEAD
    @classmethod
    def get_path_file_keltner_support(cls) -> str:
        return f'content/storage/Strategy/{cls.__name__}/indicators/keltner_supports.csv'

    @classmethod
    def get_keltner_support(cls) -> pd.DataFrame:
        df = cls.KELTER_SUPPORT
        if df is None:
            project_dir = FileManager.get_project_directory()
            file_path = cls.get_path_file_keltner_support()
            df = pd.read_csv(project_dir + file_path)
            cls.KELTER_SUPPORT = df = df.set_index(Map.id)
        return df

=======
>>>>>>> Solomon-v5.4.4.2.2
    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Noah.__new__(Noah)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
