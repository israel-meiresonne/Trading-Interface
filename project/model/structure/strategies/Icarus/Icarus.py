from typing import List, Tuple
import numpy as np

import pandas as pd

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class Icarus(TraderClass):
    _MAX_LOSS = -3/100
    _ROI_FLOOR_FIXE = 0.002
    MARKETPRICE_BUY_BIG_PERIOD = 60*60*6
    MARKETPRICE_BUY_LITTLE_PERIOD = 60*5
    _PREDICTOR_PERIOD = 60 * 60
    _PREDICTOR_N_PERIOD = 100
    _MIN_ROI_PREDICTED = 2/100
    _PREDICTION_OCCUPATION_RATE = 1
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 30/100
    _PREDICTION_OCCUPATION_REDUCE = 30/100
    _PREDICTION_OCCUPATION_REACHED_TRIGGER = 50/100
    _MIN_PERIOD = 60
    # _PERIODS_REQUIRRED = [_MIN_PERIOD, MARKETPRICE_BUY_BIG_PERIOD, MARKETPRICE_BUY_LITTLE_PERIOD]
    _PERIODS_REQUIRRED = [_MIN_PERIOD]
    _MAX_FLOAT_DEFAULT = -1
    EMA200_N_PERIOD = 200
    EMA50_N_PERIOD = 50
    ROC_WINDOW = 15
    MACD_PARAMS_1 = {'slow': 100, 'fast': 46, 'signal': 35}
    CANDLE_CHANGE_N_CANDLE = 60
    _PREDICTIONS = None
    _FILE_PATH_BACKTEST = f'$class/backtest/$path/$session_backtest.csv'

    def __init__(self, params: Map):
        super().__init__(params)
        self.__max_rsi = -1
        self.__floor_secure_order = None
        self.__predictor = None
        self.__max_price_id = None
        self.__max_prices = None
        self.__max_close_predicted = None
    
    # ——————————————————————————————————————————— FUNCTION GETTER DOWN —————————————————————————————————————————————————

    def get_predictor(self) -> Predictor:
        if self.__predictor is None:
            period = self.get_predictor_period()
            self.__predictor = Predictor(self.get_pair(), period)
        return self.__predictor

    # ——————————————————————————————————————————— FUNCTION GETTER UP ———————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION MAX ROI PREDICTED DOWN ——————————————————————————————————————

    def _reset_max_close_predicted(self) -> None:
        self.__max_close_predicted = None
    
    def _set_max_close_predicted(self, predictor_marketprice: MarketPrice = None, max_close_predicted: float = None) -> None:
        if predictor_marketprice is not None:
            predictor = self.get_predictor()
            max_close_predicted = self._predict_max_high(predictor_marketprice, predictor)
        self.__max_close_predicted = [max_close_predicted * 1]

    def _add_max_close_predicted(self, predictor_marketprice: MarketPrice = None, max_close_predicted: float = None) -> None:
        if self.__max_close_predicted is None:
            self.__max_close_predicted = []
        if predictor_marketprice is not None:
            predictor = self.get_predictor()
            max_close_predicted = self._predict_max_high(predictor_marketprice, predictor)
        max_preds = self.__max_close_predicted
        max_preds.append(max_close_predicted * 1) if max_close_predicted not in max_preds else None
    
    def get_max_close_predicted(self) -> float:
        mean = None
        max_close_predicted = self.__max_close_predicted
        if max_close_predicted is not None:
            mean = sum(max_close_predicted) / len(max_close_predicted)
        return mean
    
    def get_max_close_predicted_list(self) -> list:
        return self.__max_close_predicted
    
    def max_roi_predicted(self) -> float:
        """
        To get max roi predicted fixed with prediction's max fillable rate
        """
        max_roi_predicted = None
        if self._has_position():
            last_order = self._get_orders().get_last_execution()
            exec_price = last_order.get_execution_price()
            max_close_predicted = self.get_max_close_predicted()
            pred_fill_rate = self.get_prediction_occupation_rate()
            max_roi_predicted = _MF.progress_rate(max_close_predicted, exec_price.get_value())
            max_roi_predicted = max_roi_predicted * pred_fill_rate if max_roi_predicted > 0 else max_roi_predicted
        return max_roi_predicted
    
    def real_max_roi_predicted(self) -> float:
        """
        To get max roi predicted fixed without any rectification
        """
        max_roi_predicted = None
        if self._has_position():
            last_order = self._get_orders().get_last_execution()
            exec_price = last_order.get_execution_price()
            max_close_predicted = self.get_max_close_predicted()
            max_roi_predicted = _MF.progress_rate(max_close_predicted, exec_price.get_value())
        return max_roi_predicted

    def prediction_max_occupation(self, marketprice: MarketPrice) -> float:
        """
        To get max rate reached of max close predicted

        NOTE: formula: max_roi / max_roi_predicted

        Returns:
        --------
        return: float
            The max rate reached of max close predicted
        """
        max_roi_pred = self.max_roi_predicted()
        max_roi = self.max_roi(marketprice)
        return max_roi / max_roi_pred

    # ——————————————————————————————————————————— FUNCTION MAX ROI PREDICTED UP ————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION RSI DOWN ————————————————————————————————————————————————————
    
    def _reset_max_rsi(self) -> None:
        self.__max_rsi = -1

    def _set_max_rsi(self, new_max_rsi: float) -> None:
        if not isinstance(new_max_rsi, float):
            raise ValueError(f"max_rsi must be float, instead '{new_max_rsi}({type(new_max_rsi)})'")
        max_rsi = self.__max_rsi
        self.__max_rsi = new_max_rsi if new_max_rsi > max_rsi else max_rsi

    def get_max_rsi(self, market_price: MarketPrice) -> float:
        market_price.get_pair().are_same(self.get_pair())
        self._update_max_rsi(market_price) if self._has_position() else None
        return self.__max_rsi

    def _update_max_rsi(self, market_price: MarketPrice) -> None:
        buy_unix = self.get_buy_unix()
        times = list(market_price.get_times())
        times.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        if buy_unix in times:
            buy_time_idx = times.index(buy_unix)
            rsis_since_buy = rsis[buy_time_idx:]
            max_rsi = max(rsis_since_buy)
            self._set_max_rsi(max_rsi)

    def get_rsi_sell_floor(self, market_price: MarketPrice) -> float:
        max_rsi = self.get_max_rsi(market_price)
        rsi_step = self.get_rsi_step()
        return max_rsi - rsi_step

    # ——————————————————————————————————————————— FUNCTION RSI UP ——————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION MAX PRICE DOWN ——————————————————————————————————————————————

    def max_roi(self, marketprice: MarketPrice) -> float:
        """
        To get max roi for the current position taken

        Parameters:
        -----------
        marketprice: MarketPrice
            Market prices
        
        Returns:
        --------
        return: float
            The roi for the current position taken
        """
        max_price = max_roi = self.get_max_price(marketprice)
        if max_price >= 0:
            exec_price = self.get_buy_order().get_execution_price().get_value()
            max_roi = _MF.progress_rate(max_price, exec_price)
        return max_roi

    def _reset_max_price_id(self) -> None:
        self.__max_price_id = None

    def _set_max_price_id(self, max_price_id: str) -> None:
        self.__max_price_id = max_price_id

    def _get_max_price_id(self) -> str:
        return self.__max_price_id

    def _reset_max_prices(self) -> None:
        self.__max_prices = None
        self._reset_max_price_id()

    def get_max_prices(self) -> list:
        """
        To get list of different high prices reached since last buy

        Returns:
        return: list
            The list of different high prices reached since last buy
        """
        if self.__max_prices is None:
            self.__max_prices = [-1]
        return self.__max_prices
    
    def _set_max_price(self, new_max_price: float) -> None:
        max_prices = self.get_max_prices()
        max_prices.append(new_max_price) if (len(max_prices) == 0) or (new_max_price > max(max_prices)) else None
        
    def get_max_price(self, marketprice: MarketPrice) -> float:
        """
        To get max price reached since position taken

        NOTE: its max of high prices

        Parameters:
        -----------
        marketprice: MarketPrice
            Market prices

        Returns:
        --------
        return: float
            The max price reached since position taken
        """
        max_price_id = marketprice.get_id()
        if self._has_position() and (max_price_id != self._get_max_price_id()):
            marketprice.get_pair().are_same(self.get_pair())
            self._update_max_price(marketprice)
            self._set_max_price_id(max_price_id)
        max_prices = self.get_max_prices()
        return max_prices[-1]

    def _update_max_price(self, marketprice: MarketPrice) -> None:
        buy_order = self.get_buy_order()
        buy_time = int(buy_order.get_execution_time() / 1000)
        min_period = self.get_min_period()
        round_buy_time = _MF.round_time(buy_time, min_period)
        min_marketprice = self.get_marketprice(min_period)
        min_times = list(min_marketprice.get_times())
        min_times.reverse()
        if round_buy_time in min_times:
            buy_price = buy_order.get_execution_price()
            min_highs = list(min_marketprice.get_highs())
            min_highs.reverse()
            # Replace high with buy price
            buy_time_idx = min_times.index(round_buy_time)
            min_highs[buy_time_idx] = buy_price.get_value()
            # Get and Update max high since buy
            max_price = max(min_highs[buy_time_idx:])
        else:
            stg_period = self.get_period()
            round_buy_time = _MF.round_time(buy_time, stg_period)
            stg_times =  list(marketprice.get_times())
            stg_times.reverse()
            stg_highs = list(marketprice.get_highs())
            stg_highs.reverse()
            stg_highs = [stg_highs[i] for i in range(len(stg_times)) if stg_times[i] >= round_buy_time]
            max_price = None
            if round_buy_time in stg_times:
                buy_time_idx = stg_times.index(round_buy_time)
                stg_highs = stg_highs[buy_time_idx+1:]
                max_price = max(stg_highs) if len(stg_highs) > 0 else marketprice.get_close()
            else:
                max_price = marketprice.get_close()
        self._set_max_price(max_price)

    # ——————————————————————————————————————————— FUNCTION MAX PRICE UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR DOWN ——————————————————————————————————————————————

    def get_roi_floor(self, market_price: MarketPrice) -> float:
        max_roi = self.max_roi(market_price)
        roi_floor = self.get_max_loss()
        floors = {
            '1%': 0.01,
            '0.8%': 0.008,
            '1.8%': 0.018,
            '5%': 0.05,
            '6%': 0.06,
            '10%': 0.10,
            '12%': 0.12,
            '20%': 0.20
        }
        if floors['1%'] <= max_roi < floors['1.8%']:
            roi_floor = floors['0.8%']
        elif floors['1.8%'] <= max_roi < floors['6%']:
            roi_floor = max_roi - floors['0.8%']
        elif floors['6%'] <= max_roi < floors['12%']:
            roi_floor = max_roi - floors['1%']
        elif floors['12%'] <= max_roi:
            roi_floor = max_roi - max_roi * floors['20%']
        return roi_floor + self._ROI_FLOOR_FIXE

    def get_roi_position(self) -> float:
        """
        To get actual merged capital since last position taken\n
        Parameters
        ----------
        market_price

        Returns
        -------
        roi: float|None
            Actual merged capital if has position else None
        """
        roi = None
        if self._has_position():
            bkr = self.get_broker()
            last_order = self._get_orders().get_last_execution()
            buy_amount = last_order.get_executed_amount()
            r_asset = buy_amount.get_asset()
            buy_fee = last_order.get_fee(r_asset)
            pos = self.get_wallet().get_all_position_value(bkr)
            added_pos = self.get_wallet().get_all_position_value(bkr, Wallet.ATTR_ADDED_POSIIONS)
            removed_pos = self.get_wallet().get_all_position_value(bkr, Wallet.ATTR_REMOVED_POSIIONS)
            real_position = pos - added_pos + removed_pos
            roi = real_position / (buy_amount + buy_fee) - 1
        return roi

    def _reset_floor_secure_order(self) -> None:
        self.__floor_secure_order = None

    def _set_floor_secure_order(self, roi_floor: float) -> None:
        if not isinstance(roi_floor, float):
            raise ValueError(f"roi_floor must be float, instead '{roi_floor}({type(roi_floor)})'")
        self.__floor_secure_order = roi_floor

    def get_floor_secure_order(self) -> float:
        return self.__floor_secure_order

    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

    def _secure_order_price(self, bkr: Broker, marketprice: MarketPrice) -> Price:
        def index_last_rsi_below(rsi_trigger: float) -> int:
            # RSI
            rsi = list(marketprice.get_rsis())
            rsi.reverse()
            open_times = list(marketprice.get_times())
            open_times.reverse()
            period = self.get_period()
            buy_order = self.get_buy_order()
            buy_time = buy_order.get_execution_time()/1000
            buy_open_time = _MF.round_time(buy_time, period)
            last_index = None
            for i in range(len(open_times)):
                i = -i
                if (open_times[i] < buy_open_time) and (rsi[i] < rsi_trigger):
                    last_index = i
                    break
            return last_index

        # Get values
        pair = self.get_pair()
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        # EMA
        ema = list(marketprice.get_ema(self.EMA200_N_PERIOD))
        ema.reverse()
        ema_rising = closes[-1] > ema[-1]
        # Low
        lows = list(marketprice.get_lows())
        lows.reverse()
        rsi_trigger = 50 if ema_rising else 30
        i = index_last_rsi_below(rsi_trigger)
        secure_price_value = lows[i]
        secure_price = Price(secure_price_value, pair.get_right())
        return secure_price

    def get_buy_unix(self) -> int:
        if not self._has_position():
            raise Exception("Strategy must have position to get buy unix time")
        last_order = self._get_orders().get_last_execution()
        exec_time = int(last_order.get_execution_time() / 1000)
        period = self.get_period()
        buy_unix = int(_MF.round_time(exec_time, period))
        return buy_unix

    # ——————————————————————————————————————————— FUNCTION SECURE ORDER UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION CAN SELL DOWN ———————————————————————————————————————————————

    def can_sell(self, marketprice: MarketPrice) -> Tuple[bool, dict]:
        broker = self.get_broker()
        n_period = self.get_marketprice_n_period()
        min_period = self.get_min_period()
        datas = {
            Map.roi: self.get_wallet().get_roi(broker),
            Map.maximum: self.get_max_price(marketprice),
            # self.MARKETPRICE_BUY_BIG_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_BIG_PERIOD, n_period, broker),
            # self.MARKETPRICE_BUY_LITTLE_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_LITTLE_PERIOD, n_period, broker),
            min_period: self.get_marketprice(min_period, n_period, broker)
        }
        return self._can_sell_indicator(marketprice, datas)
    
    def _can_sell_roi(self) -> bool:
        roi_pos = self.get_roi_position()
        max_loss = self.get_max_loss()
        can_sell = roi_pos <= max_loss
        return can_sell

    @classmethod
    def _can_sell_indicator(cls, marketprice: MarketPrice, datas: dict = None) -> Tuple[bool, dict]:
        ROI_TRIGGER = 0.2/100
        def get_marketprice(period: int) -> MarketPrice:
            return datas[period]

        def is_1min_red_sequence_above_green_candle(vars_map: Map) -> bool:
            def get_last_green_candle_index(candles: np.ndarray, candle_swings: List[int]) -> int:
                green_index = None
                i = candles.shape[0] - 1
                while i > 0:
                    if candles[i] > 0:
                        green_index = i
                        break
                    i = candle_swings[i][0]
                    i -= 1
                return green_index

            def get_last_red_sequence_index(candles: np.ndarray, candle_swings: List[int]) -> int:
                red_sequence_index = None
                i = candles.shape[0] - 1
                while i > 0:
                    if candles[i] < 0:
                        red_sequence_index = candle_swings[i][0]
                        break
                    i = candle_swings[i][0]
                    i -= 1
                return red_sequence_index

            _1min_candles = np.array(_1min_closes) - np.array(_1min_opens)
            zeros = np.zeros(_1min_candles.shape[0], dtype=int)
            candle_swings = _MF.group_swings(_1min_candles, zeros)
            # Get index
            green_index = get_last_green_candle_index(_1min_candles, candle_swings)
            red_start_index = get_last_red_sequence_index(_1min_candles, candle_swings)
            red_end_index = candle_swings[red_start_index][1]
            # Get times
            buy_time = max(cls.get_buy_times(pair))
            buy_period = _MF.round_time(buy_time, marketprice_1min.get_period_time())
            green_time = _1min_open_times[green_index]
            red_time = _1min_open_times[red_start_index]
            now_period = _1min_open_times[-1]
            # Price
            red_sequence = _1min_candles[red_start_index:red_end_index+1]
            n_negative = sum([1 for v in red_sequence if v < 0])
            n_sequence = len(red_sequence)
            if n_negative != n_sequence:
                raise Exception(f"Red sequence must contain negative value only, instead neg='{n_negative}' & size='{n_sequence}'")
            sum_red_sequence = sum(red_sequence)
            # Check
            _1min_red_sequence_above_green_candle = (green_time >= buy_period) and (green_time != now_period) and (_1min_candles[-2] < 0)\
                and (green_time < red_time) and (_1min_candles[green_index] <= abs(sum_red_sequence))
            # Put
            vars_map.put(_1min_red_sequence_above_green_candle, 'red_sequence_above_green_candle')
            vars_map.put(_MF.unix_to_date(buy_period), 'red_sequence_above_green_buy_period')
            vars_map.put(_MF.unix_to_date(green_time), 'red_sequence_above_green_green_date')
            vars_map.put(_1min_candles[green_index], 'red_sequence_above_green_green_candle')
            vars_map.put(_MF.unix_to_date(red_time), 'red_sequence_above_green_start_red_date')
            vars_map.put(_MF.unix_to_date(_1min_open_times[red_end_index]), 'red_sequence_above_green_end_red_date')
            vars_map.put(sum_red_sequence, 'red_sequence_above_green_sum_red_sequence')
            vars_map.put(n_sequence, 'red_sequence_above_green_sequence_size')
            return _1min_red_sequence_above_green_candle

        def is_roi_above_trigger(vars_map: Map) -> bool:
            roi_above_trigger = roi >= ROI_TRIGGER
            # Put
            vars_map.put(roi_above_trigger, 'roi_above_trigger')
            return roi_above_trigger

        def is_supertrend_switch_down(vars_map: Map) -> bool:
            supertrend = list(marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            supertrend_rising_2 = MarketPrice.get_super_trend_trend(closes, supertrend, -2) == MarketPrice.SUPERTREND_RISING
            supertrend_dropping_1 = MarketPrice.get_super_trend_trend(closes, supertrend, -1) == MarketPrice.SUPERTREND_DROPPING
            supertrend_switch_down = supertrend_dropping_1 and supertrend_rising_2
            # Put
            vars_map.put(supertrend_switch_down, 'supertrend_switch_down')
            vars_map.put(supertrend_dropping_1, 'supertrend_dropping_1')
            vars_map.put(supertrend_rising_2, 'supertrend_rising_2')
            vars_map.put(supertrend, Map.supertrend)
            return supertrend_switch_down

        def is_psar_switch_down(vars_map: Map) -> bool:
            psar = list(marketprice.get_psar())
            psar.reverse()
            # Check
            psar_rising_2 = MarketPrice.get_psar_trend(closes, psar, -2) == MarketPrice.PSAR_RISING
            psar_dropping_1 = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_DROPPING
            psar_switch_down = psar_rising_2 and psar_dropping_1
            # Put
            vars_map.put(psar_switch_down, 'psar_switch_down')
            vars_map.put(psar_dropping_1, 'psar_dropping_1')
            vars_map.put(psar_rising_2, 'psar_rising_2')
            vars_map.put(psar, Map.psar)
            return psar_switch_down

        def is_min_tangent_rsi_negative(vars_map: Map) -> None:
            rsi = list(marketprice_1min.get_rsis())
            rsi.reverse()
            # Check
            min_tangent_rsi_negative = rsi[-1] < rsi[-2]
            # Put
            vars_map.put(min_tangent_rsi_negative, 'min_tangent_rsi_negative')
            vars_map.put(rsi, 'min_rsi')
            return min_tangent_rsi_negative

        vars_map = Map()
        can_sell = False
        # Vars
        roi = datas[Map.roi]
        max_roi = datas[Map.maximum]
        # MarketPrice
        pair = marketprice.get_pair()
        period = marketprice.get_period_time()
        closes = list(marketprice.get_closes())
        closes.reverse()
        opens = list(marketprice.get_opens())
        opens.reverse()
        # MarketPrice 1min
        marketprice_1min = get_marketprice(cls.get_min_period())
        _1min_closes = list(marketprice_1min.get_closes())
        _1min_closes.reverse()
        _1min_opens = list(marketprice_1min.get_opens())
        _1min_opens.reverse()
        _1min_open_times = list(marketprice_1min.get_times())
        _1min_open_times.reverse()
        # MarketPrice Xmin
        # marketprice_5min = get_marketprice(cls.MARKETPRICE_BUY_LITTLE_PERIOD)
        # marketprice_6h = get_marketprice(cls.MARKETPRICE_BUY_BIG_PERIOD)
        # Check
        can_sell = (is_roi_above_trigger(vars_map) and is_1min_red_sequence_above_green_candle(vars_map))\
            or (
                (is_supertrend_switch_down(vars_map) or is_psar_switch_down(vars_map))\
                    and is_min_tangent_rsi_negative(vars_map)
            )
        # Repport
        key = cls._can_buy_indicator.__name__
        supertrend = vars_map.get(Map.supertrend)
        psar = vars_map.get(Map.psar)
        min_rsi = vars_map.get('min_rsi')
        repport = {
            f'{key}._can_sell_indicator': can_sell,
            f'{key}.roi_above_trigger': vars_map.get('roi_above_trigger'),
            f'{key}.red_sequence_above_green_candle': vars_map.get('red_sequence_above_green_candle'),
            f'{key}.supertrend_switch_down': vars_map.get('supertrend_switch_down'),
            f'{key}.psar_switch_down': vars_map.get('psar_switch_down'),
            f'{key}.min_tangent_rsi_negative': vars_map.get('min_tangent_rsi_negative'),
            
            f'{key}.ROI_TRIGGER': ROI_TRIGGER,
            f'{key}.roi': roi,
            f'{key}.max_roi': max_roi,

            f'{key}.red_sequence_above_green_buy_period': vars_map.get('red_sequence_above_green_buy_period'),
            f'{key}.red_sequence_above_green_green_date': vars_map.get('red_sequence_above_green_green_date'),
            f'{key}.red_sequence_above_green_green_candle': vars_map.get('red_sequence_above_green_green_candle'),
            f'{key}.red_sequence_above_green_start_red_date': vars_map.get('red_sequence_above_green_start_red_date'),
            f'{key}.red_sequence_above_green_end_red_date': vars_map.get('red_sequence_above_green_end_red_date'),
            f'{key}.red_sequence_above_green_sum_red_sequence': vars_map.get('red_sequence_above_green_sum_red_sequence'),
            f'{key}.red_sequence_above_green_sequence_size': vars_map.get('red_sequence_above_green_sequence_size'),

            f'{key}.supertrend_dropping_1': vars_map.get('supertrend_dropping_1'),
            f'{key}.supertrend_rising_2': vars_map.get('supertrend_rising_2'),

            f'{key}.psar_dropping_1': vars_map.get('psar_dropping_1'),
            f'{key}.psar_rising_2': vars_map.get('psar_rising_2'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.supertrend[-2]': supertrend[-2] if supertrend is not None else None,
            f'{key}.psar[-1]': psar[-1] if psar is not None else None,
            f'{key}.psar[-2]': psar[-2] if psar is not None else None,
            f'{key}.min_rsi[-1]': min_rsi[-1] if min_rsi is not None else None,
            f'{key}.min_rsi[-2]': min_rsi[-2] if min_rsi is not None else None
        }
        return can_sell, repport

    def _can_sell_prediction(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        def is_prediction_reached() -> bool:
            max_roi = self.max_roi(marketprice)
            max_roi_pred = self.max_roi_predicted()
            return max_roi >= max_roi_pred

        def get_new_max_close_pred() -> float:
            predictor = self.get_predictor()
            return self._predict_max_high(predictor_marketprice, predictor)

        def is_new_prediction_better() -> bool:
            max_close_pred = get_new_max_close_pred()
            close = marketprice.get_close()
            max_roi_pred = _MF.progress_rate(max_close_pred, close)
            pred_trigger = self.get_min_roi_predicted()
            self._set_max_close_predicted(max_close_predicted=max_close_pred)
            return max_roi_pred >= pred_trigger

        can_sell = is_prediction_reached() and is_new_prediction_better()
        return can_sell

    # ——————————————————————————————————————————— FUNCTION CAN SELL UP —————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION TRY BUY/SELL DOWN ———————————————————————————————————————————

    def _try_buy(self, market_price: MarketPrice, bkr: Broker) -> Map:
        """
        To try to buy position\n
        :param market_price: market price
        :return: set of execution instruction
                 Map[index{int}]:   {str}
        """
        executions = Map()
        # Reset
        self._reset_max_rsi()
        self._reset_max_prices()
        self._reset_floor_secure_order()
        self._reset_max_close_predicted()
        # Big
        # big_period = Icarus.MARKETPRICE_BUY_BIG_PERIOD
        # big_marketprice = self.get_marketprice(big_period)
        # little
        # little_period = Icarus.MARKETPRICE_BUY_LITTLE_PERIOD
        # little_marketprice = self.get_marketprice(little_period)
        # min
        min_period = Icarus.get_min_period()
        min_marketprice = self.get_marketprice(min_period)
        # Check
        # can_buy, buy_repport = self.can_buy(market_price, big_marketprice, little_marketprice, min_marketprice)
        can_buy, buy_repport = self.can_buy(market_price, min_marketprice)
        if can_buy:
            self._buy(executions)
            # self._secure_position(executions)
        # Save
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
        return executions

    def _try_sell(self, market_price: MarketPrice, bkr: Broker) -> Map:
        """
        To try to sell position\n
        :param market_price: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        executions = Map()
        can_sell, repport = self.can_sell(market_price)
        if can_sell:
            self._sell(executions)
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
        self.save_sell_conditions(repport)
        return executions

    # ——————————————————————————————————————————— FUNCTION TRY BUY/SELL UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER DOWN ——————————————————————————————————————————

    @classmethod
    def get_max_loss(cls) -> float:
        return cls._MAX_LOSS
    
    @classmethod
    def get_predictor_period(cls) -> int:
        return cls._PREDICTOR_PERIOD

    @classmethod
    def get_predictor_n_period(cls) -> int:
        return cls._PREDICTOR_N_PERIOD

    @classmethod
    def get_min_roi_predicted(cls) -> float:
        return cls._MIN_ROI_PREDICTED
    
    @classmethod
    def get_prediction_occupation_rate(cls) -> float:
        return cls._PREDICTION_OCCUPATION_RATE
    
    @classmethod
    def get_prediction_occupation_secure_trigger(cls) -> float:
        return cls._PREDICTION_OCCUPATION_SECURE_TRIGGER
    
    @classmethod
    def get_prediction_occupation_reduce(cls) -> float:
        return cls._PREDICTION_OCCUPATION_REDUCE
    
    @classmethod
    def get_min_period(cls) -> int:
        """
        To get Broker's minimum period
        """
        return cls._MIN_PERIOD

    @classmethod
    def get_periods_required(cls) -> list:
        """
        To get list of period used to trade

        Returns:
        --------
        return: list
            List of period used to trade
        """
        return cls._PERIODS_REQUIRRED

    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY DOWN —————————————————————————————————————————

    @classmethod
    def stalker_can_add(cls, market_price: MarketPrice) -> Tuple[bool, dict]:
        pass

    @classmethod
    def can_buy(cls, child_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, min_marketprice)
        # Check
        can_buy = indicator_ok
        # Repport
        key = cls.can_buy.__name__
        repport = {
            f'{key}.indicator': indicator_ok,
            **indicator_datas
        }
        return can_buy, repport

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        N_CANDLE = 60
        TRIGGER_CANDLE_CHANGE = 0.5/100
        def price_change(i: int, open_prices: list[float], close_prices: list[float]) -> float:
            n_open = len(open_prices)
            n_close = len(close_prices)
            if n_open != n_close:
                raise ValueError(f"Price lists must have  the same size, instead '{n_open}'!='{n_close}' (open!=close)")
            return close_prices[i] - open_prices[i]

        def is_price_switch_up(vars_map: Map) -> bool:
            # Check
            price_change_1 = price_change(-1, opens, closes)
            price_change_2 = price_change(-2, opens, closes)
            price_switch_up = (price_change_1 > abs(price_change_2))
            # Put
            vars_map.put(price_switch_up, 'price_switch_up')
            vars_map.put(price_change_1, 'price_change_1')
            vars_map.put(price_change_2, 'price_change_2')
            return price_switch_up

        def is_min_macd_histogram_switch_up(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            macd_map = min_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            min_macd_histogram_switch_up = (histogram[-1] > 0) and (histogram[-2] < 0)
            # Put
            vars_map.put(min_macd_histogram_switch_up, 'min_macd_histogram_switch_up')
            vars_map.put(histogram, 'min_histogram')
            return min_macd_histogram_switch_up

        def is_mean_candle_change_60_above_trigger(vars_map: Map) -> bool:
            mean_candle_change = MarketPrice.mean_candle_variation(opens[-N_CANDLE:], closes[-N_CANDLE:])
            # Check
            mean_positive_candle = mean_candle_change.get(Map.positive, Map.mean)
            mean_candle_change_60_above_trigger = mean_positive_candle >= TRIGGER_CANDLE_CHANGE
            # Put
            vars_map.put(mean_candle_change_60_above_trigger, 'mean_candle_change_60_above_trigger')
            vars_map.put(mean_positive_candle, 'mean_candle_change_60_mean_positive_candle')
            return mean_candle_change_60_above_trigger

        def is_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(child_marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            supertrend_rising = MarketPrice.get_super_trend_trend(closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            # Put
            vars_map.put(supertrend_rising, 'supertrend_rising')
            vars_map.put(supertrend, Map.supertrend)
            return supertrend_rising

        def is_min_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(min_marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            min_supertrend_rising = MarketPrice.get_super_trend_trend(min_closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            # Put
            vars_map.put(min_supertrend_rising, 'min_supertrend_rising')
            vars_map.put(supertrend, 'min_supertrend')
            return min_supertrend_rising

        vars_map = Map()
        # Child
        period = child_marketprice.get_period_time()
        pair = child_marketprice.get_pair()
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        highs = list(child_marketprice.get_highs())
        highs.reverse()
        opens = list(child_marketprice.get_opens())
        opens.reverse()
        open_times = list(child_marketprice.get_times())
        open_times.reverse()
        # Min
        min_closes = list(min_marketprice.get_closes())
        min_closes.reverse()
        min_opens = list(min_marketprice.get_opens())
        min_opens.reverse()
        min_open_times = list(min_marketprice.get_times())
        min_open_times.reverse()
        # Little
        # Big
        # Check
        can_buy_indicator = is_price_switch_up(vars_map) and is_mean_candle_change_60_above_trigger(vars_map)\
            and is_supertrend_rising(vars_map) and is_min_macd_histogram_switch_up(vars_map) and is_min_supertrend_rising(vars_map)
        # Repport
        min_histogram = vars_map.get('min_histogram')
        supertrend = vars_map.get(Map.supertrend)
        min_supertrend = vars_map.get('min_supertrend')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.price_switch_up': vars_map.get('price_switch_up'),
            f'{key}.mean_candle_change_60_above_trigger': vars_map.get('mean_candle_change_60_above_trigger'),
            f'{key}.supertrend_rising': vars_map.get('supertrend_rising'),
            f'{key}.min_macd_histogram_switch_up': vars_map.get('min_macd_histogram_switch_up'),
            f'{key}.min_supertrend_rising': vars_map.get('min_supertrend_rising'),

            f'{key}.price_change_1': vars_map.get('price_change_1'),
            f'{key}.price_change_2': vars_map.get('price_change_2'),

            f'{key}.mean_candle_change_60_mean_positive_candle': vars_map.get('mean_candle_change_60_mean_positive_candle'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.min_closes[-1]': min_closes[-1],
            f'{key}.min_opens[-1]': min_opens[-1],
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.supertrend[-2]': supertrend[-2] if supertrend is not None else None,
            f'{key}.min_supertrend[-1]': min_supertrend[-1] if min_supertrend is not None else None,
            f'{key}.min_supertrend[-2]': min_supertrend[-2] if min_supertrend is not None else None,
            f'{key}.min_histogram[-1]': min_histogram[-1] if min_histogram is not None else None,
            f'{key}.min_histogram[-2]': min_histogram[-2] if min_histogram is not None else None
        }
        return can_buy_indicator, repport

    @classmethod
    def _can_buy_prediction(cls, predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        child_closes = child_marketprice.get_close()
        # Prediction
        pair = child_marketprice.get_pair()
        pred_period = cls.get_predictor_period()
        predictor = Predictor(pair, pred_period)
        max_close_pred = cls._predict_max_high(predictor_marketprice, predictor)
        max_roi_pred = _MF.progress_rate(max_close_pred, child_closes)
        pred_trigger = cls.get_min_roi_predicted()
        prediction_ok = max_roi_pred >= pred_trigger
        # Occupation
        predictor_highs = list(predictor_marketprice.get_highs())
        predictor_highs.reverse()
        occup_rate = None
        occup_trigger = cls._PREDICTION_OCCUPATION_REACHED_TRIGGER
        occup_rate_ok = False
        if prediction_ok:
            occup_rate = Predictor.occupation_rate(max_close_pred, predictor_highs[-1], child_closes)
            occup_rate_ok = occup_rate < occup_trigger
        # Check
        can_buy = prediction_ok and occup_rate_ok
        # Repport
        key = cls._can_buy_prediction.__name__
        repport = {
            f'{key}.prediction_ok': prediction_ok,
            f'{key}.occup_rate_ok': occup_rate_ok,
            f'{key}.pred_period': pred_period,
            f'{key}.max_close_pred': max_close_pred,
            f'{key}.max_roi_pred': max_roi_pred,
            f'{key}.pred_trigger': pred_trigger,
            f'{key}.child_closes[-1]': child_closes,
            f'{key}.occup_rate': occup_rate,
            f'{key}.occup_trigger': occup_trigger,
            f'{key}.predictor_highs[-1]': predictor_highs[-1]
        }
        return can_buy, repport
    
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY UP ———————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION PRREDICTOR DOWN ——————————————————————————————————————

    @classmethod
    def _get_file_path_prediction(cls) -> str:
        return f'content/storage/Strategy/{cls.__name__}/prediction/prediction.json'

    @classmethod
    def _get_predictions(cls) -> Map:
        """
        Map[pair{str}][predict_key{str}]:   {float}
        """
        if cls._PREDICTIONS is None:
            path = cls._get_file_path_prediction()
            json_str = _MF.catch_exception(FileManager.read, cls.__name__, repport=False, **{Map.path: path})
            cls._PREDICTIONS = Map() if json_str is None else MyJson.json_decode(json_str)
        return cls._PREDICTIONS

    @classmethod
    def _get_prediction(cls, pair: Pair, predict_key: str) -> float:
        predicts = cls._get_predictions()
        predict = predicts.get(pair.__str__(), predict_key)
        return predict

    @classmethod
    def _add_prediction(cls, pair: Pair, predict_key: str, max_close_pred: float) -> float:
        max_close_pred = float(max_close_pred)
        predicts = cls._get_predictions()
        predicts.put(max_close_pred, pair.__str__(), predict_key)
        path = cls._get_file_path_prediction()
        content = predicts.json_encode()
        FileManager.write(path, content, overwrite=True, make_dir=True)

    @classmethod
    def _predict_max_high(cls, predictor_marketprice: MarketPrice, predictor: Predictor) -> float:
        stage = Config.get_stage()
        model = predictor.get_model(Predictor.HIGH)
        n_feature = model.n_feature()
        highs = list(predictor_marketprice.get_highs())
        highs.reverse()
        xs, ys = Predictor.generate_dataset(highs, n_feature)
        highs_np = Predictor.market_price_to_np(predictor_marketprice, Predictor.HIGH, n_feature)
        if stage == Config.STAGE_1:
            pair = predictor_marketprice.get_pair()
            predict_key = '-'.join([str(e) for e in highs_np[-1,:]])
            max_close_pred = cls._get_prediction(pair, predict_key)
            if max_close_pred is None:
                max_close_pred = model.predict(highs_np, fixe_offset=True, xs_offset=xs, ys_offset=ys)[-1,-1]
                cls._add_prediction(pair, predict_key, max_close_pred)
        else:
            max_close_pred = model.predict(highs_np, fixe_offset=True, xs_offset=xs, ys_offset=ys)[-1,-1]
        return float(max_close_pred)
    
    @classmethod
    def predictor_market_price(cls, bkr: Broker, pair: Pair) -> MarketPrice:
        period = cls.get_predictor_period()
        n_period = cls.get_predictor_n_period()
        marketprice = cls._market_price(bkr, pair, period, n_period)
        return marketprice

    # ——————————————————————————————————————————— STATIC FUNCTION PRREDICTOR UP ————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @classmethod
    def file_path_backtest(cls, active_path: bool = None) -> str:
        """
        To get path to file where backtest are stored
        """
        dir_strategy_storage = Config.get(Config.DIR_STRATEGY_STORAGE)
        file_path = dir_strategy_storage + cls._FILE_PATH_BACKTEST.replace('$session', Config.get(Config.SESSION_ID))
        file_path = file_path.replace('$class', cls.__name__)
        if active_path is None:
            backtest_path = file_path
        elif active_path:
            backtest_path = file_path.replace('$path', 'active')
        elif not active_path:
            backtest_path = file_path.replace('$path', 'stock')
        return backtest_path

    @classmethod
    def file_path_backtest_test(cls) -> str:
        """
        To get path to file where backtest are stored
        """
        # '{class_name}/backtest/$path/$session/datas/$session_backtest.csv'
        # >>> '{class_name}/backtest/{test_path}/{session_id}/datas/{session_id}_backtest.csv'
        session_id = Config.get(Config.SESSION_ID)
        backtest_path = cls.file_path_backtest(active_path=None)
        file_path = backtest_path.replace('$path', 'tests')
        paths = file_path.split('/')
        paths.insert(-1, session_id)
        paths.insert(-1, 'datas')
        file_path = '/'.join(paths)
        return file_path

    @classmethod
    def file_path_backtest_repport(cls, buy_file: bool) -> str:
        """
        To get file path of where condition to buy/sell are printed
        """
        file_type = Map.buy if buy_file else Map.sell
        test_file_path = cls.file_path_backtest_test()
        repport_file_name = f'{Config.get(Config.SESSION_ID)}_{file_type}_repports.csv'
        repport_paths = test_file_path.split('/')
        repport_paths[-1] = repport_file_name
        repport_file_path = '/'.join(repport_paths)
        return repport_file_path

    @classmethod
    def best_pairs(cls) -> list[Pair]:
        """
        To get list of best Pair to tade

        Returns:
        --------
        return: list[Pair]
            List of best Pair to tade
        """
        pair_serie = cls.load_backtest(active_path=True)[Map.pair]
        best_pairs = [Pair(pair_str) for pair_str in pair_serie]
        return best_pairs

    @classmethod
    def load_backtest(cls, active_path: bool) -> pd.DataFrame:
        """
        To load most recent backtest

        Returns:
        --------
            The most recent backtest
        """
        file_path = cls.file_path_backtest(active_path)
        dir_path = FileManager.path_to_dir(file_path)
        files = FileManager.get_files(dir_path, make_dir=True)
        if len(files) == 0:
            raise Exception(f"There's no backtest file in this directory '{dir_path}'")
        real_file_path = FileManager.get_project_directory() + dir_path + files[-1]
        backtest_df = pd.read_csv(real_file_path)
        return backtest_df

    @classmethod
    def backtest(cls, broker: Broker, starttime: int, endtime: int, periods: list[int], pairs: list[Pair] = None, buy_type: str = Map.close, sell_type: str = Map.close) -> None:
        """
        To backtest Strategy

        Parameters:
        -----------
        broker: Broker
            Access to a Broker's API
        starttime: int
            Time of the older period to backtest
        endtime: int
            Time of the most recent period to backtest
        periods: list[int]
            Periods to backtest (in second)
        pairs: list[Pair] = None
            Pairs to backtest
        buy_type: str
            The price to use as buy price
        sell_type: str
            The price to use as sell price
        - close: to use close price
        - open: to use open price
        - mean: to use mean of open_price and close_price in period of 1min
        """
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI

        def wrap_trades(pair: Pair, period: int, turn: int) -> None:
            print(_MF.loop_progression(output_starttime, turn, n_turn,f"{pair.__str__().upper()}({BinanceAPI.convert_interval(period)})"))
            BinanceFakeAPI.reset()
            trades = cls.backtest_trade_history(pair, period, broker, buy_type, sell_type).to_dict(orient='records')
            fields = list(trades[0].keys())
            FileManager.write_csv(file_path, fields, trades, overwrite=False, make_dir=True)

        Config.update(Config.FAKE_API_START_END_TIME, {Map.start: starttime, Map.end: endtime})
        broker_name = broker.__class__.__name__
        active_path = True
        pairs = MarketPrice.history_pairs(broker_name, active_path=active_path) if pairs is None else pairs
        file_path = cls.file_path_backtest_test()
        output_starttime = _MF.get_timestamp()
        turn = 1
        n_turn = len(pairs) * len(periods)
        for pair in pairs:
            for period in periods:
                _MF.catch_exception(wrap_trades, cls.__name__, repport=True, **{Map.pair: pair, Map.period: period, 'turn': turn})
                turn += 1

    @classmethod
    def backtest_trade_history(cls, pair: Pair, period: int, broker: Broker, buy_type: str, sell_type: str)  -> pd.DataFrame:
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        from model.structure.Bot import Bot
        import sys

        def get_exec_price(marketprice: MarketPrice, exec_type: str) -> float:
            if marketprice.get_period_time() != cls.get_min_period():
                raise ValueError(f"The MarketPrice's period must be 1min, instead '{marketprice.get_period_time()}'sec.")
            close_prices = list(marketprice.get_closes())
            close_prices.reverse()
            open_prices = list(marketprice.get_opens())
            open_prices.reverse()
            if exec_type == Map.mean:
                exec_price = (close_prices[-1] + open_prices[-1])/2
            elif exec_type == Map.close:
                exec_price = close_prices[-1]
            elif exec_type == Map.open:
                exec_price = open_prices[-1]
            else:
                raise ValueError(f"This type of execution price '{exec_type}' is not supported")
            return exec_price

        buy_repports = []
        sell_repports = []
        n_period = 300
        fees = broker.get_trade_fee(pair)
        taker_fee_rate = fees.get(Map.taker)
        buy_sell_fee = ((1+taker_fee_rate)**2 - 1)
        pair_merged = pair.format(Pair.FORMAT_MERGED)
        str_period = BinanceAPI.convert_interval(period)
        big_period = cls.MARKETPRICE_BUY_BIG_PERIOD
        little_period = cls.MARKETPRICE_BUY_LITTLE_PERIOD
        min_period = cls.get_min_period()
        trades = None
        trade = {}
        market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: period,
            'n_period': n_period
            }
        #
        big_market_params = market_params.copy()
        big_market_params[Map.period] = big_period
        #
        little_market_params = market_params.copy()
        little_market_params[Map.period] = little_period
        #
        min_market_params = market_params.copy()
        min_market_params[Map.period] = min_period
        broker.add_streams([
            broker.generate_stream(Map({Map.pair: pair, Map.period: period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: big_period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: little_period}))
        ])
        i = 0
        Bot.update_trade_index(i)
        marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=True, **market_params)
        while isinstance(marketprice, MarketPrice):
            big_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **big_market_params)
            little_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **little_market_params)
            min_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **min_market_params)
            # Period
            open_times = list(marketprice.get_times())
            open_times.reverse()
            closes = list(marketprice.get_closes())
            closes.reverse()
            highs = list(marketprice.get_highs())
            highs.reverse()
            lows = list(marketprice.get_lows())
            lows.reverse()
            # Min Period
            min_highs = list(min_marketprice.get_highs())
            min_highs.reverse()
            min_lows = list(min_marketprice.get_lows())
            min_lows.reverse()
            # Update High/Low price
            if i == 0:
                higher_price = 0
                start_date = _MF.unix_to_date(open_times[-1])
                end_date = _MF.unix_to_date(open_times[-1])
                start_price = closes[-1]
            else:
                end_date = _MF.unix_to_date(open_times[-1])
                end_price = closes[-1]
                higher_price = highs[-1] if highs[-1] > higher_price else higher_price
            # Print time
            sys.stdout.write(f'\r{_MF.prefix()}{_MF.unix_to_date(open_times[-1])}')
            sys.stdout.flush()
            has_position = len(trade) != 0
            # Update Max/Min roi
            if has_position:
                high_roi = _MF.progress_rate(min_highs[-1], trade['buy_price'])
                low_roi = _MF.progress_rate(min_lows[-1], trade['buy_price'])
                min_roi_position = low_roi if (min_roi_position is None) or (low_roi < min_roi_position) else min_roi_position
                max_roi_position = high_roi if (max_roi_position is None) or high_roi > max_roi_position else max_roi_position
                # Can sell params
                can_sell_params = {
                    Map.roi: _MF.progress_rate(get_exec_price(min_marketprice, sell_type), trade['buy_price']),
                    Map.maximum: max_roi_position,
                    cls.MARKETPRICE_BUY_BIG_PERIOD: big_marketprice,
                    cls.MARKETPRICE_BUY_LITTLE_PERIOD: little_marketprice,
                    min_period: min_marketprice
                }
            # Try buy/sell
            if not has_position:
                trade_id = f'{pair_merged}_{str_period}_{i}'
                can_buy, buy_repport = cls.can_buy(marketprice, min_marketprice)
                buy_repport = {
                    Map.time: _MF.unix_to_date(min_marketprice.get_time()),
                   f'{Map.period}_{Map.time}': _MF.unix_to_date(open_times[-1]),
                    Map.id: trade_id,
                    **buy_repport
                }
                buy_repports.append(buy_repport)
                if can_buy:
                    buy_time = min_marketprice.get_time()
                    exec_price = get_exec_price(min_marketprice, buy_type)
                    min_roi_position = None
                    max_roi_position = None
                    cls._add_buy_time(pair, buy_time)
                    trade = {
                        Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                        Map.pair: pair,
                        Map.period: str_period,
                        Map.id: trade_id,
                        Map.start: start_date,
                        Map.end: end_date,
                        'buy_time': buy_time,
                        'buy_date': _MF.unix_to_date(buy_time),
                        'buy_price': exec_price,
                    }
            elif has_position:
                can_buy, sell_repport = cls._can_sell_indicator(marketprice, can_sell_params)
                sell_repport = {
                    Map.time: _MF.unix_to_date(min_marketprice.get_time()),
                    f'{Map.period}_{Map.time}': _MF.unix_to_date(open_times[-1]),
                    Map.id: trade_id,
                    **sell_repport
                }
                sell_repports.append(sell_repport)
                if can_buy:
                    # Prepare
                    sell_time = min_marketprice.get_time()
                    exec_price = get_exec_price(min_marketprice, sell_type)
                    # Put
                    trade['sell_time'] = sell_time
                    trade['sell_date'] = _MF.unix_to_date(sell_time)
                    trade['sell_price'] = exec_price
                    trade[Map.roi] = (trade['sell_price']/trade['buy_price'] - 1) - buy_sell_fee
                    trade['roi_losses'] = trade[Map.roi] if trade[Map.roi] < 0 else None
                    trade['roi_wins'] = trade[Map.roi] if trade[Map.roi] > 0 else None
                    trade['roi_neutrals'] = trade[Map.roi] if trade[Map.roi] == 0 else None
                    trade['min_roi_position'] = min_roi_position
                    trade['max_roi_position'] = max_roi_position
                    trade['min_roi'] = None
                    trade['mean_roi'] = None
                    trade['max_roi'] = None
                    trade['mean_win_roi'] = None
                    trade['mean_loss_roi'] = None
                    trade[Map.sum] = None
                    trade['min_sum_roi'] = None
                    trade['max_sum_roi'] = None
                    trade['final_roi'] = None
                    trade[Map.fee] = buy_sell_fee
                    trade['sum_fee'] = None
                    trade['sum_roi_no_fee'] = None
                    trade['start_price'] = None
                    trade['end_price'] = None
                    trade['higher_price'] = None
                    trade['market_performence'] = None
                    trade['max_profit'] = None
                    trade['n_win'] = None
                    trade['win_rate'] = None
                    trade['n_loss'] = None
                    trade['loss_rate'] = None
                    trades = pd.DataFrame([trade], columns=list(trade.keys())) if trades is None else trades.append(trade, ignore_index=True)
                    sum_roi = trades[Map.roi].sum()
                    sum_fee = trades[Map.fee].sum()
                    trades.loc[trades.index[-1], Map.sum] = sum_roi
                    trades.loc[trades.index[-1], f'sum_fee'] = sum_fee
                    trades.loc[trades.index[-1], f'sum_roi_no_fee'] = sum_roi + sum_fee
                    trade = {}
                    buy_time = None
            i += 1
            Bot.update_trade_index(i)
            marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **market_params)
        print()
        if trades is None:
            default = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.pair: pair,
                Map.period: str_period
                }
            trades = pd.DataFrame([default], columns=list(default.keys()))
        else:
            win_trades = trades[trades[Map.roi] > 0]
            loss_trades = trades[trades[Map.roi] < 0]
            n_trades = win_trades.shape[0] + loss_trades.shape[0]
            trades.loc[:,'higher_price'] = higher_price
            trades.loc[:,'start_price'] = start_price
            trades.loc[:,'end_price'] = end_price
            trades.loc[:,'higher_price'] = higher_price
            trades.loc[:,'market_performence'] = _MF.progress_rate(end_price, start_price)
            trades.loc[:,'max_profit'] = _MF.progress_rate(higher_price, start_price)
            trades.loc[:,'mean_roi'] = trades[Map.roi].mean()
            trades.loc[:,'min_roi'] = trades[Map.roi].min()
            trades.loc[:,'max_roi'] = trades[Map.roi].max()
            trades.loc[:,'mean_win_roi'] = win_trades[Map.roi].mean()
            trades.loc[:,'mean_loss_roi'] = loss_trades[Map.roi].mean()
            trades.loc[:,'min_sum_roi'] = trades[Map.sum].min()
            trades.loc[:,'max_sum_roi'] = trades[Map.sum].max()
            trades.loc[:,'final_roi'] = trades.loc[trades.index[-1], Map.sum]
            trades.loc[:,'n_win'] = win_trades.shape[0]
            trades.loc[:,'win_rate'] = win_trades.shape[0]/n_trades
            trades.loc[:,'n_loss'] = loss_trades.shape[0]
            trades.loc[:,'loss_rate'] = loss_trades.shape[0]/n_trades
        if len(buy_repports) > 0:
            repport_file_path = cls.file_path_backtest_repport(buy_file=True)
            fields = list(buy_repports[0].keys())
            rows = buy_repports
            FileManager.write_csv(repport_file_path, fields, rows, overwrite=False, make_dir=True)
        if len(sell_repports) > 0:
            repport_file_path = cls.file_path_backtest_repport(buy_file=False)
            fields = list(sell_repports[0].keys())
            rows = sell_repports
            FileManager.write_csv(repport_file_path, fields, rows, overwrite=False, make_dir=True)
        return trades

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Icarus(Map({
            Map.pair: Pair('@json/@json'),
            Map.maximum: None,
            Map.capital: Price(1, '@json'),
            Map.rate: 1,
            Map.period: 0
        }))
        exec(MyJson.get_executable())
        return instance

    def save_move(self, **agrs) -> None:
        args_map = Map(agrs)
        market_price = agrs['market_price']
        bkr = self.get_broker()
        roi = self.get_wallet().get_roi(bkr)
        has_position = self._has_position()
        closes = list(market_price.get_closes())
        closes.reverse()
        secure_odr = self._get_secure_order()
        roi_position = self.get_roi_position()
        max_roi = self.max_roi(market_price)
        max_price_id = self._get_max_price_id()
        max_price = self.get_max_price(market_price)
        max_loss = self.get_max_loss()
        """
        can buy
        """
        # Prediction
        buy_price = self.get_buy_order().get_execution_price() if has_position else None
        # Map to print
        params_map = Map({
            Map.time: _MF.unix_to_date(market_price.get_time()),
            Map.period: self.get_period(),
            Map.close: closes[-1],
            'closes[-2]': closes[-2],
            'closes[-3]': closes[-3],
            'buy_price': buy_price,
            'max_price_id': max_price_id,
            'max_price': max_price,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'max_loss': _MF.rate_to_str(max_loss),
            'has_position': has_position,
            'can_buy': args_map.get('can_buy'),
            'can_sell': args_map.get('can_sell'),
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(roi),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
        })
        self._print_move(params_map)

    def save_sell_conditions(self, sell_condition: dict) -> None:
        """
        To save sell conditions

        Parameters:
        -----------
        repport: dict
            Datas to print
        """
        pair = self.get_pair()
        to_print = {
           Map.id: self.get_id(),
           'class': self.__class__.__name__,
           'nb_trade': self.get_nb_trade(),
           Map.pair: pair,
           Map.date: _MF.unix_to_date(_MF.get_timestamp()),
           **sell_condition
        }
        path = Config.get(Config.DIR_SAVE_SELL_CONDITIONS).replace('$pair', pair.format(Pair.FORMAT_UNDERSCORE).upper())
        fields = list(to_print.keys())
        rows = [to_print]
        FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
