from typing import Tuple

import pandas as pd

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class Icarus(TraderClass):
    _MAX_LOSS = -3/100
    _ROI_FLOOR_FIXE = 0.002
    _PREDICTOR_PERIOD = 60 * 60
    _PREDICTOR_N_PERIOD = 100
    _MIN_ROI_PREDICTED = 2/100
    _PREDICTION_OCCUPATION_RATE = 1
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 30/100
    _PREDICTION_OCCUPATION_REDUCE = 30/100
    _PREDICTION_OCCUPATION_REACHED_TRIGGER = 50/100
    _MIN_PERIOD = 60
    _PERIODS_REQUIRRED = [_MIN_PERIOD, _PREDICTOR_PERIOD]
    _MAX_FLOAT_DEFAULT = -1
    EMA_N_PERIOD = 200
    _PREDICTIONS = None
    _FILE_PATH_BACKTEST = f'Icarus/backtest/$path/$session_backtest.csv'

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
        ema = list(marketprice.get_ema(self.EMA_N_PERIOD))
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

    def can_sell(self, marketprice: MarketPrice) -> bool:
        # return self._can_sell_indicator(marketprice) or self._can_sell_prediction(predictor_marketprice, marketprice)
        return self._can_sell_indicator(marketprice)
    
    def _can_sell_roi(self) -> bool:
        roi_pos = self.get_roi_position()
        max_loss = self.get_max_loss()
        can_sell = roi_pos <= max_loss
        return can_sell
    
    def _can_sell_indicator(self, marketprice: MarketPrice) ->  bool:
        def is_buy_period() -> bool:
            period = self.get_period()
            buy_time = int(self.get_buy_order().get_execution_time() / 1000)
            buy_time_rounded = _MF.round_time(buy_time, period)
            first_open_time = buy_time_rounded + period
            open_time = marketprice.get_time()
            return open_time < first_open_time

        """
        def is_rsi_reached(rsi_trigger: float, vars_map: Map) -> bool:
            # RSI
            rsi = list(marketprice.get_rsis())
            rsi.reverse()
            rsi_reached = rsi[-1] > rsi_trigger
            return rsi_reached
        """

        def is_histogram_dropping(vars_map: Map) -> bool:
            # MACD
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_dropping = histogram[-1] < 0
            return histogram_dropping

        def are_macd_signal_negatives(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            macd_signal_negatives = (macd[-1] < 0) or (signal[-1] < 0)
            return macd_signal_negatives

        def is_tangent_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_dropping = macd[-1] <= macd[-2]
            return tangent_macd_dropping

        vars_map = Map()
        can_sell = False
        # Check
        can_sell = (not is_buy_period()) and (is_histogram_dropping(vars_map) or (are_macd_signal_negatives(vars_map) and is_tangent_macd_dropping(vars_map)))
        return can_sell

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
        # Evaluate Buy
        # predictor_marketprice = self.get_marketprice(period=self.get_predictor_period())
        can_buy, _ = self.can_buy(market_price)
        if can_buy:
            # self._set_max_close_predicted(predictor_marketprice=predictor_marketprice)
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
        def is_new_prediction_higher(old_close: float, new_close) -> bool:
            return new_close > old_close

        def is_occupation_trigger_reached() -> bool:
            occup_trigger = self.get_prediction_occupation_secure_trigger()
            occupation = self.prediction_max_occupation(market_price)
            return occupation >= occup_trigger

        def is_max_price_higher(old_max_price: float, new_max_price: float) -> bool:
            return new_max_price > old_max_price

        def is_secure_is_max_loss() -> bool:
            buy_odr = self.get_buy_order()
            secure_odr = self._get_secure_order()
            return secure_odr.get_limit_price().get_value() < buy_odr.get_execution_price().get_value()
        """

        executions = Map()
        # max_close_pred = self.get_max_close_predicted()
        # old_max_price = self.get_max_prices()[-1]
        # Evaluate Sell
        can_sell = self.can_sell(market_price)
        if can_sell:
            self._sell(executions)
        # else:
        #     new_max_close_pred = self.get_max_close_predicted()
        #     new_prediction_higher = is_new_prediction_higher(max_close_pred, new_max_close_pred)
        #     occup_trigger_reached = is_occupation_trigger_reached()
        #     # secure_is_max_loss = is_secure_is_max_loss()
        #     has_secure_odr = isinstance(self._get_secure_order(), Order)
        #     max_price_higher = is_max_price_higher(old_max_price, new_max_price=self.get_max_price(market_price))
        #     # elif secure_is_max_loss and occup_trigger_reached:
        #     if (not has_secure_odr) and occup_trigger_reached:
        #         # Move up occupation secure
        #         self._secure_position(executions)
        #     elif has_secure_odr and occup_trigger_reached and new_prediction_higher:
        #         # Move up occupation secure if new prediction and occup trigger reached
        #         self._move_up_secure_order(executions)
        #     elif has_secure_odr and occup_trigger_reached and max_price_higher:
        #         # Move up occupation secure
        #         self._move_up_secure_order(executions)
        # Save
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
        return executions

    # ——————————————————————————————————————————— FUNCTION TRY BUY/SELL UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER DOWN ——————————————————————————————————————————

    @staticmethod
    def get_max_loss() -> float:
        return Icarus._MAX_LOSS
    
    @staticmethod
    def get_predictor_period() -> int:
        return Icarus._PREDICTOR_PERIOD

    @staticmethod
    def get_predictor_n_period() -> int:
        return Icarus._PREDICTOR_N_PERIOD

    @staticmethod
    def get_min_roi_predicted() -> float:
        return Icarus._MIN_ROI_PREDICTED
    
    @staticmethod
    def get_prediction_occupation_rate() -> float:
        return Icarus._PREDICTION_OCCUPATION_RATE
    
    @staticmethod
    def get_prediction_occupation_secure_trigger() -> float:
        return Icarus._PREDICTION_OCCUPATION_SECURE_TRIGGER
    
    @staticmethod
    def get_prediction_occupation_reduce() -> float:
        return Icarus._PREDICTION_OCCUPATION_REDUCE
    
    @staticmethod
    def get_min_period() -> int:
        """
        To get Broker's minimum period
        """
        return Icarus._MIN_PERIOD

    @staticmethod
    def get_periods_required() -> list:
        """
        To get list of period used to trade

        Returns:
        --------
        return: list
            List of period used to trade
        """
        return Icarus._PERIODS_REQUIRRED

    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY DOWN —————————————————————————————————————————

    @classmethod
    def stalker_can_add(cls, market_price: MarketPrice) -> Tuple[bool, dict]:
        pass

    @classmethod
    def can_buy(cls, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        # if child_marketprice.get_period_time() != 60*15:
        #     child_period = child_marketprice.get_period()
        #     market_period = child_marketprice.get_period_time()
        #     raise ValueError(f"MarketPrice must have period '{child_period}', instead '{market_period}'")
        # indicator
        indicator_ok, indicator_datas = Icarus._can_buy_indicator(child_marketprice)
        # Check
        can_buy = indicator_ok
        # Repport
        key = Icarus.can_buy.__name__
        repport = {
            f'{key}.indicator': indicator_ok,
            **indicator_datas
        }
        return can_buy, repport

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        def is_ema_rising(vars_map: Map) -> bool:
            # EMA
            ema = list(child_marketprice.get_ema(cls.EMA_N_PERIOD))
            ema.reverse()
            ema_rising = closes[-1] > ema[-1]
            # Put
            vars_map.put(ema, 'ema')
            vars_map.put(ema_rising, 'ema_rising')
            return ema_rising

        def is_macd_negative(vars_map: Map) -> bool:
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            macd_negative = macd[-1] < 0
            # Put
            vars_map.put(macd, 'macd')
            vars_map.put(macd_negative, 'macd_negative')
            return macd_negative

        def is_macd_switch_up(vars_map: Map) -> bool:
            # MACD
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_rising = histogram[-1] > 0
            prev_histogram_dropping = histogram[-2] < 0
            macd_switch_up = histogram_rising and prev_histogram_dropping
            # Put
            vars_map.put(histogram, 'histogram')
            vars_map.put(histogram_rising, 'histogram_rising')
            vars_map.put(prev_histogram_dropping, 'prev_histogram_dropping')
            vars_map.put(macd_switch_up, 'macd_switch_up')
            return macd_switch_up

        def will_market_bounce(vars_map: Map) -> bool:
            open_times = list(child_marketprice.get_times())
            open_times.reverse()
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            macd_min_index = macd_last_minimum_index(macd, histogram)
            last_min_macd = macd[macd_min_index]
            macd_peak_index = macd_last_peak_index(macd, signal, histogram)
            last_peak_macd = macd[macd_peak_index]
            will_bounce = last_peak_macd > abs(last_min_macd)
            macd_min_date = _MF.unix_to_date(open_times[macd_min_index])
            macd_peak_date = _MF.unix_to_date(open_times[macd_peak_index])
            # Put
            vars_map.put(macd_min_index, 'macd_min_index')
            vars_map.put(last_min_macd, 'last_min_macd')
            vars_map.put(macd_peak_index, 'macd_peak_index')
            vars_map.put(last_peak_macd, 'last_peak_macd')
            vars_map.put(will_bounce, 'will_bounce')
            vars_map.put(macd_min_date, 'macd_min_date')
            vars_map.put(macd_peak_date, 'macd_peak_date')
            return will_bounce
        
        def macd_last_minimum_index(macd: list, histogram: list) -> int:
            neg_macd_indexes = []
            macd_df = pd.DataFrame({Map.macd: macd, Map.histogram: histogram})
            neg_macd_df = macd_df[macd_df[Map.macd] < 0]
            neg_idxs = neg_macd_df.index
            for i in range(2, neg_macd_df.shape[0]):
                i = -i
                neg_macd_indexes.append(neg_idxs[i+1]) if abs(i) == 2 else None
                if abs(neg_idxs[i] - neg_idxs[i+1]) == 1:
                    neg_macd_indexes.append(neg_idxs[i])
                else:
                    break
            last_lows_df = macd_df[macd_df.index.isin(neg_macd_indexes)]
            last_min_macd = last_lows_df[Map.macd].min()
            last_min_macd_index = last_lows_df[last_lows_df[Map.macd] == last_min_macd].index[-1]
            return last_min_macd_index

        def macd_last_peak_index(macd: list, signal: list, histogram: list) -> int:
            posi_macd_indexes = []
            macd_df = pd.DataFrame({Map.macd: macd, Map.signal: signal, Map.histogram: histogram})
            posi_macd_df = macd_df[(macd_df[Map.histogram] > 0) & (macd_df[Map.macd] > 0) & (macd_df[Map.signal] > 0)]
            posi_indexes = posi_macd_df.index
            for i in range(2, posi_macd_df.shape[0]):
                i = -i
                posi_macd_indexes.append(posi_indexes[i+1]) if abs(i) == 2 else None
                if abs(posi_indexes[i] - posi_indexes[i+1]) == 1:
                    posi_macd_indexes.append(posi_indexes[i])
                else:
                    break
            last_highs_df = macd_df[macd_df.index.isin(posi_macd_indexes)]
            last_macd_peak = last_highs_df[Map.macd].max()
            last_macd_peak_index = last_highs_df[last_highs_df[Map.macd] == last_macd_peak].index[-1]
            return last_macd_peak_index

        vars_map = Map()
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        can_buy_indicator = is_ema_rising(vars_map) and is_macd_negative(vars_map) and is_macd_switch_up(vars_map) and will_market_bounce(vars_map)
        # Repport
        ema = vars_map.get('ema')
        histogram = vars_map.get(Map.histogram)
        macd = vars_map.get(Map.macd)
        key = Icarus._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.ema_rising': vars_map.get('ema_rising'),
            f'{key}.macd_negative': vars_map.get('macd_negative'),
            f'{key}.histogram_rising': vars_map.get('histogram_rising'),
            f'{key}.prev_histogram_dropping': vars_map.get('prev_histogram_dropping'),
            f'{key}.macd_switch_up': vars_map.get('macd_switch_up'),
            f'{key}.will_bounce': vars_map.get('will_bounce'),
            f'{key}.macd_min_index': vars_map.get('macd_min_index'),
            f'{key}.macd_min_date': vars_map.get('macd_min_date'),
            f'{key}.last_min_macd': vars_map.get('last_min_macd'),
            f'{key}.macd_peak_index': vars_map.get('macd_peak_index'),
            f'{key}.macd_peak_date': vars_map.get('macd_peak_date'),
            f'{key}.last_peak_macd': vars_map.get('last_peak_macd'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.closes[-2]': closes[-2],
            f'{key}.closes[-3]': closes[-3],
            f'{key}.ema[-1]': ema[-1] if ema is not None else None,
            f'{key}.ema[-2]': ema[-2] if ema is not None else None,
            f'{key}.ema[-3]': ema[-3] if ema is not None else None,
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None,
            f'{key}.histogram[-3]': histogram[-3] if histogram is not None else None,
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
            f'{key}.macd[-2]': macd[-2] if macd is not None else None,
            f'{key}.macd[-3]': macd[-3] if macd is not None else None
        }
        return can_buy_indicator, repport

    @staticmethod
    def _can_buy_prediction(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        child_closes = child_marketprice.get_close()
        # Prediction
        pair = child_marketprice.get_pair()
        pred_period = Icarus.get_predictor_period()
        predictor = Predictor(pair, pred_period)
        max_close_pred = Icarus._predict_max_high(predictor_marketprice, predictor)
        max_roi_pred = _MF.progress_rate(max_close_pred, child_closes)
        pred_trigger = Icarus.get_min_roi_predicted()
        prediction_ok = max_roi_pred >= pred_trigger
        # Occupation
        predictor_highs = list(predictor_marketprice.get_highs())
        predictor_highs.reverse()
        occup_rate = None
        occup_trigger = Icarus._PREDICTION_OCCUPATION_REACHED_TRIGGER
        occup_rate_ok = False
        if prediction_ok:
            occup_rate = Predictor.occupation_rate(max_close_pred, predictor_highs[-1], child_closes)
            occup_rate_ok = occup_rate < occup_trigger
        # Check
        can_buy = prediction_ok and occup_rate_ok
        # Repport
        key = Icarus._can_buy_prediction.__name__
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
        return f'content/storage/Strategy/Icarus/prediction/prediction.json'

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
    
    @staticmethod
    def predictor_market_price(bkr: Broker, pair: Pair) -> MarketPrice:
        period = Icarus.get_predictor_period()
        n_period = Icarus.get_predictor_n_period()
        marketprice = Icarus._market_price(bkr, pair, period, n_period)
        return marketprice

    # ——————————————————————————————————————————— STATIC FUNCTION PRREDICTOR UP ————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @classmethod
    def file_path_backtest(cls, active_path: bool) -> str:
        """
        To get path to file where backtest are stored
        """
        dir_strategy_storage = Config.get(Config.DIR_STRATEGY_STORAGE)
        file_path = dir_strategy_storage + cls._FILE_PATH_BACKTEST.replace('$session', Config.get(Config.SESSION_ID))
        return file_path.replace('$path', 'active') if active_path else file_path.replace('$path', 'stock')

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
        files = FileManager.get_files(dir_path)
        if len(files) == 0:
            raise Exception(f"There's no backtest file in this directory '{dir_path}'")
        real_file_path = FileManager.get_project_directory() + dir_path + files[-1]
        backtest_df = pd.read_csv(real_file_path)
        return backtest_df

    @classmethod
    def backtest(cls, broker: Broker, starttime: int, endtime: int, periods: list[int], pairs: list[Pair] = None) -> None:
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
        """
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        from model.structure.Bot import Bot
        import sys
    
        def can_sell_indicator(marketprice: MarketPrice, buy_time: int) ->  bool:
            def is_buy_period() -> bool:
                period = marketprice.get_period_time()
                buy_time_rounded = _MF.round_time(buy_time, period)
                first_open_time = buy_time_rounded + period
                open_time = marketprice.get_time()
                return open_time < first_open_time

            def is_histogram_dropping(vars_map: Map) -> bool:
                macd_map = marketprice.get_macd()
                histogram = list(macd_map.get(Map.histogram))
                histogram.reverse()
                histogram_dropping = histogram[-1] < 0
                return histogram_dropping

            def are_macd_signal_negatives(vars_map: Map) -> bool:
                macd_map = marketprice.get_macd()
                macd = list(macd_map.get(Map.macd))
                macd.reverse()
                signal = list(macd_map.get(Map.signal))
                signal.reverse()
                macd_signal_negatives = (macd[-1] < 0) or (signal[-1] < 0)
                return macd_signal_negatives

            def is_tangent_macd_dropping(vars_map: Map) -> bool:
                macd_map = marketprice.get_macd()
                macd = list(macd_map.get(Map.macd))
                macd.reverse()
                tangent_macd_dropping = macd[-1] <= macd[-2]
                return tangent_macd_dropping

            vars_map = Map()
            can_sell = False
            # Check
            can_sell = (not is_buy_period()) and (is_histogram_dropping(vars_map) or (are_macd_signal_negatives(vars_map) and is_tangent_macd_dropping(vars_map)))
            return can_sell

        def trade_history(pair: Pair, period: int)  -> pd.DataFrame:
            buy_repports = []
            n_period = broker.get_max_n_period()
            fees = broker.get_trade_fee(pair)
            taker_fee_rate = fees.get(Map.taker)
            buy_sell_fee = ((1+taker_fee_rate)**2 - 1)
            pair_merged = pair.format(Pair.FORMAT_MERGED)
            str_period = BinanceAPI.convert_interval(period)
            trades = None
            trade = {}
            market_params = {
                Map.broker: broker,
                Map.pair: pair,
                Map.period: period,
                'n_period': n_period
                }
            i = 0
            Bot.update_trade_index(i)
            marketprice = _MF.catch_exception(MarketPrice.marketprice, Icarus.__name__, repport=False, **market_params)
            while isinstance(marketprice, MarketPrice):
                times = list(marketprice.get_times())
                times.reverse()
                closes = list(marketprice.get_closes())
                closes.reverse()
                highs = list(marketprice.get_highs())
                highs.reverse()
                if i == 0:
                    higher_price = 0
                    start_date = _MF.unix_to_date(times[-1])
                    end_date = _MF.unix_to_date(times[-1])
                    start_price = closes[-1]
                else:
                    end_date = _MF.unix_to_date(times[-1])
                    end_price = closes[-1]
                    higher_price = highs[-1] if highs[-1] > higher_price else higher_price
                sys.stdout.write(f'\r{_MF.prefix()}{_MF.unix_to_date(times[-1])}')
                sys.stdout.flush()
                has_position = len(trade) != 0
                if not has_position:
                    can_buy, buy_repport = cls.can_buy(marketprice)
                    buy_repport = {
                        Map.time: _MF.unix_to_date(times[-1]),
                        **buy_repport
                    }
                    buy_repports.append(buy_repport)
                    if can_buy:
                        buy_time = marketprice.get_time()
                        exec_price = marketprice.get_close()
                        trade = {
                            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                            Map.pair: pair,
                            Map.period: str_period,
                            Map.id: f'{pair_merged}_{str_period}_{i}',
                            Map.start: start_date,
                            Map.end: end_date,
                            'buy_time': buy_time,
                            'buy_date': _MF.unix_to_date(buy_time),
                            'buy_price': exec_price,
                        }
                elif has_position and can_sell_indicator(marketprice, buy_time):
                    sell_time = marketprice.get_time()
                    exec_price = marketprice.get_close()
                    trade['sell_time'] = sell_time
                    trade['sell_date'] = _MF.unix_to_date(sell_time)
                    trade['sell_price'] = exec_price
                    trade[Map.roi] = (trade['sell_price']/trade['buy_price'] - 1) - buy_sell_fee
                    trade['mean_roi'] = None
                    trade['min_roi'] = None
                    trade['max_roi'] = None
                    trade['mean_win_roi'] = None
                    trade['mean_loss_roi'] = None
                    trade[Map.sum] = None
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
                marketprice = _MF.catch_exception(MarketPrice.marketprice, Icarus.__name__, repport=False, **market_params)
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
                trades.loc[:,'final_roi'] = trades.loc[trades.index[-1], Map.sum]
                trades.loc[:,'n_win'] = win_trades.shape[0]
                trades.loc[:,'win_rate'] = win_trades.shape[0]/n_trades
                trades.loc[:,'n_loss'] = loss_trades.shape[0]
                trades.loc[:,'loss_rate'] = loss_trades.shape[0]/n_trades
            if len(buy_repports) > 0:
                repport_path = '/'.join(file_path.split('/')[:-2]) + f'/repports/{Config.get(Config.SESSION_ID)}_buy_repports.csv'
                fields = list(buy_repports[0].keys())
                rows = buy_repports
                FileManager.write_csv(repport_path, fields, rows, overwrite=False, make_dir=True)
            return trades

        Config.update(Config.FAKE_API_START_END_TIME, {Map.start: starttime, Map.end: endtime})
        active_path = True
        pairs = MarketPrice.history_pairs(broker_name, active_path=active_path) if pairs is None else pairs
        file_path = cls.file_path_backtest(active_path=False)
        broker_name = broker.__class__.__name__
        output_starttime = _MF.get_timestamp()
        turn = 1
        n_turn = len(pairs) * len(periods)
        def wrap_trades(pair: Pair, period: int, turn: int) -> None:
            print(_MF.loop_progression(output_starttime, turn, n_turn,f"{pair.__str__().upper()}({BinanceAPI.convert_interval(period)})"))
            trades = trade_history(pair, period).to_dict(orient='records')
            fields = list(trades[0].keys())
            FileManager.write_csv(file_path, fields, trades, overwrite=False, make_dir=True)

        for pair in pairs:
            for period in periods:
                _MF.catch_exception(wrap_trades, Icarus.__name__, repport=True, **{Map.pair: pair, Map.period: period, 'turn': turn})
                turn += 1

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
        # predictor_marketprice = agrs['predictor_marketprice']
        roi = self.get_wallet().get_roi(bkr)
        has_position = self._has_position()
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        secure_odr = self._get_secure_order()
        roi_position = self.get_roi_position()
        max_roi = self.max_roi(market_price)
        max_price_id = self._get_max_price_id()
        max_price = self.get_max_price(market_price)
        max_loss = self.get_max_loss()
        """
        can buy
        """
        # Psar Rsi
        psar_rsis = list(market_price.get_psar_rsis())
        psar_rsis.reverse()
        # Supertrend
        supertrends = list(market_price.get_super_trend())
        supertrends.reverse()
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        # Keltner Buy
        klc = market_price.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        # MACD
        macd_map = market_price.get_macd()
        macds = list(macd_map.get(Map.macd))
        macds.reverse()
        signals = list(macd_map.get(Map.signal))
        signals.reverse()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        # EMA
        ema = list(market_price.get_ema(self.EMA_N_PERIOD))
        ema.reverse()
        # # Prediction
        buy_price = self.get_buy_order().get_execution_price() if has_position else None
        # max_close_predicted = self.get_max_close_predicted()
        # max_close_predicted = self._predict_max_high(predictor_marketprice, self.get_predictor()) if max_close_predicted is None else max_close_predicted
        # max_roi_predicted = self.max_roi_predicted()
        # real_max_roi_predicted = self.real_max_roi_predicted()
        # prediction_occupation_rate = self.get_prediction_occupation_rate()
        # prediction_strigger = self.get_min_roi_predicted()
        # if max_roi_predicted is None:
        #     max_roi_predicted = _MF.progress_rate(max_close_predicted, closes[-1])
        # max_close_predicted_list = self.get_max_close_predicted_list()
        # max_roi_predicted_max = None
        # max_roi_predicted_min = None
        # n_prediction = len(max_close_predicted_list) if max_close_predicted_list is not None else -1
        # if has_position and (n_prediction > 0):
        #     max_roi_predicted_max = _MF.progress_rate(max(max_close_predicted_list), buy_price.get_value())
        #     max_roi_predicted_min = _MF.progress_rate(min(max_close_predicted_list), buy_price.get_value())
        # occup_trigger = self.get_prediction_occupation_secure_trigger()
        # max_occupation = self.prediction_max_occupation(market_price) if has_position else None
        # occup_reduce_rate = self.get_prediction_occupation_reduce()
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
            # 'max_close_predicted': max_close_predicted,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'max_loss': _MF.rate_to_str(max_loss),
            # 'prediction_strigger': _MF.rate_to_str(prediction_strigger),
            # 'occup_trigger': _MF.rate_to_str(occup_trigger),
            # 'occup_reduce_rate': _MF.rate_to_str(occup_reduce_rate),
            'has_position': has_position,
            'can_buy': args_map.get('can_buy'),
            'can_sell': args_map.get('can_sell'),
            'indicator_buy': self._can_buy_indicator(market_price)[0],
            'indicator_sell': self._can_sell_indicator(market_price) if has_position else None,
            Map.rsi: rsis[-1],
            'rsis[-2]': rsis[-2],
            'rsis[-3]': rsis[-3],
            'psar_rsis': psar_rsis[-1],
            'psar_rsis[-2]': psar_rsis[-2],
            'psar_rsis[-3]': psar_rsis[-3],
            'max_rsi': self.get_max_rsi(market_price),
            # 'max_occupation': _MF.rate_to_str(max_occupation) if has_position else None,
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(roi),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
            # 'max_roi_predicted': _MF.rate_to_str(max_roi_predicted) if max_roi_predicted is not None else max_roi_predicted,
            # 'max_roi_predicted_max': _MF.rate_to_str(max_roi_predicted_max) if max_roi_predicted_max is not None else max_roi_predicted_max,
            # 'max_roi_predicted_min': _MF.rate_to_str(max_roi_predicted_min) if max_roi_predicted_min is not None else max_roi_predicted_min,
            # 'n_prediction': n_prediction,
            # 'real_max_roi_predicted': _MF.rate_to_str(real_max_roi_predicted) if real_max_roi_predicted is not None else real_max_roi_predicted,
            # 'prediction_occupation_rate': _MF.rate_to_str(prediction_occupation_rate),
            'supertrends[-1]': supertrends[-1],
            'supertrends[-2]': supertrends[-2],
            'supertrends[-3]': supertrends[-3],
            'psars[-1]': psars[-1],
            'psars[-2]': psars[-2],
            'psars[-3]': psars[-3],
            'klc_highs[-1]': klc_highs[-1],
            'klc_highs[-2]': klc_highs[-2],
            'klc_highs[-3]': klc_highs[-3],
            'macds[-1]': macds[-1],
            'macds[-2]': macds[-2],
            'macds[-3]': macds[-3],
            'signals[-1]': signals[-1],
            'signals[-2]': signals[-2],
            'signals[-3]': signals[-3],
            'histograms[-1]': histograms[-1],
            'histograms[-2]': histograms[-2],
            'histograms[-3]': histograms[-3],
            'ema[-1]': ema[-1],
            'ema[-2]': ema[-2],
            'ema[-3]': ema[-3]
        })
        self._print_move(params_map)

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
