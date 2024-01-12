<<<<<<< HEAD
=======
from typing import List, Tuple
import numpy as np

import pandas as pd

from config.Config import Config
>>>>>>> Icarus-test
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Icarus(TraderClass):
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    # _RSI_BUY_TRIGGER = 25
    # _RSI_SELL_TRIGGER = 30
    # _RSI_STEP = 10
    _MAX_LOSS = -0.01
=======
    _MAX_LOSS = -0.4/100
=======
    _MIN_ROI_TRIGGER = -0.2/100
    _MAX_LOSS = -0.8/100
>>>>>>> Icarus-v13.3.1
    _MAX_ROI_DROP_TRIGGER = 1/100
    _MAX_ROI_DROP_RATE = 50/100
>>>>>>> Icarus-v13.3
=======
    _MAX_ROI_DROP_TRIGGER = 1/100
=======
    _MAX_ROI_DROP_TRIGGER = 1.5/100
>>>>>>> Icarus-v13.5.1.1.2
    _MAX_ROI_DROP_RATE = 50/100
    _MAX_LOSS = -3/100
>>>>>>> Icarus-v13.4.1
=======
    _MAX_LOSS = -0.5/100
>>>>>>> Icarus-v13.4.2.3
=======
    _MAX_LOSS = -1/100
>>>>>>> Icarus-v2.1.2.2
=======
    _MAX_LOSS = -1/100
>>>>>>> Icarus-v5.13
    _ROI_FLOOR_FIXE = 0.002
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    # _ROI_STEP = 0.005
=======
    MARKETPRICE_BUY_BIG_PERIOD = 60*60*6
    MARKETPRICE_BUY_LITTLE_PERIOD = 60*5
    _PREDICTOR_PERIOD = 60 * 60
<<<<<<< HEAD
    _PREDICTOR_N_PERIOD = 100
=======
    _PREDICTOR_PERIOD = 60 * 15
=======
    _PREDICTOR_PERIOD = 60 * 30
>>>>>>> Icarus-v4.3.c
    _PREDICTOR_N_PERIOD = 1000
>>>>>>> Icarus-v4.3.b
    _MIN_ROI_PREDICTED = 2/100
<<<<<<< HEAD
    _PREDICTION_OCCUPATION_RATE = 1
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 30/100
=======
    _PREDICTION_ROI_HIGH_TRIGGER = 2/100
    _PREDICTION_ROI_LOW_TRIGGER = 0
    _PREDICTION_OCCUPATION_RATE = 100/100
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 50/100
>>>>>>> Icarus-v4.3.2
    _PREDICTION_OCCUPATION_REDUCE = 30/100
    _PREDICTION_OCCUPATION_REACHED_TRIGGER = 50/100
    _MIN_PERIOD = 60
<<<<<<< HEAD
=======
    # _PERIODS_REQUIRRED = [_MIN_PERIOD, MARKETPRICE_BUY_BIG_PERIOD, MARKETPRICE_BUY_LITTLE_PERIOD]
>>>>>>> Icarus-v13.1.4
    _PERIODS_REQUIRRED = [_MIN_PERIOD]
    _MAX_FLOAT_DEFAULT = -1
<<<<<<< HEAD
<<<<<<< HEAD
    EMA200_N_PERIOD = 200
    EMA50_N_PERIOD = 50
    ROC_WINDOW = 15
    MACD_PARAMS_1 = {'slow': 100, 'fast': 46, 'signal': 35}
    CANDLE_CHANGE_N_CANDLE = 60
=======
    EMA_N_PERIOD = 200
    MACD_SIGNAL = 34
>>>>>>> Icarus-v6.7
    _PREDICTIONS = None
<<<<<<< HEAD
    _FILE_PATH_BACKTEST = f'$class/backtest/$path/$session_backtest.csv'
>>>>>>> Icarus-test
=======
    _PREDICTOR_N_PERIOD = 1000
    _MIN_ROI_PREDICTED = 1/100
<<<<<<< HEAD
    _PREDICTION_FILLING_RATE = 80/100
>>>>>>> Icarus-v2.1.2.2
=======
    _PREDICTION_FILLING_RATE = 55/100
>>>>>>> Icarus-v2.1.2.2.1
=======
    EMA_N_PERIOD = 200
    _RSI_BUY_TRIGGER = 60
    _RSI_SELL_TRIGGER = _RSI_BUY_TRIGGER
>>>>>>> Icarus-v5.12
=======
    _MACD_HISTOGRAM = None
>>>>>>> Icarus-v6.4.1

    def __init__(self, params: Map):
        super().__init__(params)
        self.__max_rsi = -1
        self.__max_roi = -1
        self.__floor_secure_order = None
<<<<<<< HEAD
=======
        self.__predictor = None
        self.__max_price_id = None
        self.__max_prices = None
        self.__max_close_predicted = None
        self.__min_price_predicted = None
        self.__min_price_predicted_id = None
    
    # ——————————————————————————————————————————— FUNCTION GETTER DOWN —————————————————————————————————————————————————
>>>>>>> Icarus-v4.3.2

<<<<<<< HEAD
=======
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
            pred_fill_rate = self.get_prediction_filling_rate()
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
            # pred_fill_rate = self.get_prediction_filling_rate()
            # max_close_predicted = max_close_predicted * pred_fill_rate if max_close_predicted > exec_price.get_value() else max_close_predicted
            max_roi_predicted = _MF.progress_rate(max_close_predicted, exec_price.get_value())
        return max_roi_predicted

    # ——————————————————————————————————————————— FUNCTION MAX ROI PREDICTED UP ————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION MIN PRICEPREDICTED DOWN —————————————————————————————————————

    def _set_min_price_predicted_id(self, min_price_predicted_id: int) -> int:
        self.__min_price_predicted_id = min_price_predicted_id

    def get_min_price_predicted_id(self) -> int:
        """
        To get the id of the MarquetPrice used to evaluate prediction

        Returns:
        --------
        return: int
            The id of the MarquetPrice used to evaluate prediction
        """
        return self.__min_price_predicted_id
    
    def _reset_min_price_predicted(self) -> None:
        self.__min_price_predicted = None

    def _set_min_price_predicted(self) -> None:
        old_min_pred_id = self.get_min_price_predicted_id()
        predictor_marketprice = self.get_marketprice(period=self.get_predictor_period())
        new_pred_id = id(predictor_marketprice)
        if new_pred_id != old_min_pred_id:
            predictor = self.get_predictor()
            self.__min_price_predicted = self._predict_min_low(predictor_marketprice, predictor)
            self._set_min_price_predicted_id(new_pred_id)
    
    def get_min_price_predicted(self) -> float:
        self._set_min_price_predicted()
        return self.__min_price_predicted

    # ——————————————————————————————————————————— FUNCTION MIN PRICEPREDICTED UP ———————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION RSI DOWN ————————————————————————————————————————————————————
    
>>>>>>> Icarus-v2.1.2.2
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
        rsi_step = self.get_period()
        return max_rsi - rsi_step

    def _reset_max_roi(self) -> None:
        self.__max_roi = -1

    def _set_max_roi(self, new_max_roi: float) -> None:
        if not isinstance(new_max_roi, float):
            raise ValueError(f"max_roi must be float, instead '{new_max_roi}({type(new_max_roi)})'")
        max_roi = self.__max_roi
        self.__max_roi = new_max_roi if new_max_roi > max_roi else max_roi

    def get_max_roi(self, market_price: MarketPrice) -> float:
        market_price.get_pair().are_same(self.get_pair())
        self._update_max_roi(market_price) if self._has_position() else None
        return self.__max_roi

    def _update_max_roi(self, market_price: MarketPrice) -> None:
        buy_unix = self.get_buy_unix()
        last_order = self._get_orders().get_last_execution()
        times = list(market_price.get_times())
        times.reverse()
        closes = list(market_price.get_closes())
        closes.reverse()
        if buy_unix in times:
            buy_time_idx = times.index(buy_unix)
            closes_since_buy = closes[buy_time_idx:]
            max_close = max(closes_since_buy)
            exec_price = last_order.get_execution_price()
            max_roi = max_close / exec_price - 1
            self._set_max_roi(max_roi)

    def get_roi_floor(self, market_price: MarketPrice) -> float:
        max_roi = self.get_max_roi(market_price)
        roi_floor = self.get_max_loss()
        floors = {
            '1%': 0.01,
            '0.8%': 0.008,
            '1.8%': 0.018,
            '5%': 0.05,
            '10%': 0.1
        }
        if floors['1%'] <= max_roi < floors['1.8%']:
            roi_floor = floors['0.8%']
        elif floors['1.8%'] <= max_roi < floors['10%']:
            roi_floor = max_roi - floors['0.8%']
        elif max_roi >= floors['10%']:
            roi_floor = max_roi - max_roi * floors['1%']
        return roi_floor + self._ROI_FLOOR_FIXE

    def get_roi_position(self, market_price: MarketPrice) -> float:
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
        market_price.get_pair().are_same(self.get_pair())
        roi = None
        if self._has_position():
            last_order = self._get_orders().get_last_execution()
            amount = last_order.get_amount()
            actual_capital = self.get_actual_capital_merged(market_price)
            roi = actual_capital / amount - 1
        return roi

    def _reset_floor_secure_order(self) -> None:
        self.__floor_secure_order = None

    def _set_floor_secure_order(self, roi_floor: float) -> None:
        if not isinstance(roi_floor, float):
            raise ValueError(f"roi_floor must be float, instead '{roi_floor}({type(roi_floor)})'")
        self.__floor_secure_order = roi_floor

    def get_floor_secure_order(self) -> float:
        return self.__floor_secure_order

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def _new_secure_order(self, bkr: Broker, mkt_prc: MarketPrice) -> Order:
        if not self._has_position():
            raise Exception("Strategy must have position to generate secure Order")
        _bkr_cls = bkr.__class__.__name__
        pair = self.get_pair()
<<<<<<< HEAD
        # Get Quantity
        sum_odr = self._get_orders().get_sum()
        qty = sum_odr.get(Map.left)
        qty = Price(qty.get_value(), qty.get_asset().get_symbol())
        # Get stop price
        buy_price = self._get_orders().get_last_execution().get_execution_price()
        roi_floor = self.get_roi_floor(mkt_prc)
        self._set_floor_secure_order(roi_floor)
        stop = buy_price * (1 + roi_floor)
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pair.get_right().get_symbol()),
            Map.limit: Price(stop, pair.get_right().get_symbol()),
            Map.quantity: qty
        })
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_STOP_LIMIT, odr_params)
        self._add_order(odr)
        self._set_secure_order(odr)
        return odr
=======
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
=======
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

    def _secure_order_price(self, bkr: Broker, marketprice: MarketPrice) -> Price:
        max_roi = self.get_max_price(marketprice)
        buy_price = self.get_buy_order().get_execution_price()
        pair = self.get_pair()
        # Secure Price
        secure_price_value = self._get_stop_limit_price(buy_price, max_roi)
>>>>>>> Icarus-v13.3
=======
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

    def _secure_order_price(self, bkr: Broker, marketprice: MarketPrice) -> Price:
        # Get values
        pair = self.get_pair()
<<<<<<< HEAD
        max_roi = self.max_roi(marketprice)
        buy_price = self.get_buy_order().get_execution_price()
        # Price
        secure_price_value = self._get_max_drop_sell_price(buy_price, max_roi)
>>>>>>> Icarus-v13.5.1.1.2
        secure_price = Price(secure_price_value, pair.get_right())
=======
        buy_price = self._get_orders().get_last_execution().get_execution_price().get_value()
        # '''
        if self._get_secure_order() is None:
            secure_price = TraderClass._secure_order_price(self, bkr, marketprice)
        else:
        # '''
            get_max_close_pred = self.get_max_close_predicted()
            max_occupation = self.prediction_max_occupation(marketprice)
            reduce_rate = self.get_prediction_occupation_reduce()
            # Delta between buy price and prediction price
            increase_range = get_max_close_pred - buy_price
            # Eval price corresponding to occupation rate
            occup_close = increase_range * max_occupation + buy_price
            # Eval price point to reduce
            reduce = increase_range * reduce_rate
            # Reduce price point to occupation to get secure price
            secure_close = occup_close - reduce
            secure_price = Price(secure_close, pair.get_right().get_symbol())
>>>>>>> Icarus-v5.13
        return secure_price
>>>>>>> Icarus-test

=======
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

>>>>>>> Icarus-v13.4.2.3
=======
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

>>>>>>> Icarus-v2.1.2.2
    def get_buy_unix(self) -> int:
        if not self._has_position():
            raise Exception("Strategy must have position to get buy unix time")
        last_order = self._get_orders().get_last_execution()
        exec_time = int(last_order.get_execution_time() / 1000)
        period = self.get_period()
        buy_unix = int(_MF.round_time(exec_time, period))
        return buy_unix

<<<<<<< HEAD
    def can_sell(self, market_price: MarketPrice) -> bool:
        """
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        rsi = rsis[-1]
        max_rsi = self.get_max_rsi(market_price)
        rsi_sell_trigger = self.get_rsi_sell_trigger()
        # Rsi floor
        rsi_sell_floor = self.get_rsi_sell_floor(market_price)
        rsi_ok = (max_rsi >= rsi_sell_trigger) and (rsi <= rsi_sell_floor)
        return rsi_ok
        """
        # Close
        closes = list(market_price.get_closes())
        closes.reverse()
        # Keltner
        klc = market_price.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        can_sell = closes[-1] <= klc_highs[-1]
        return can_sell

    def _try_buy(self, market_price: MarketPrice) -> Map:
=======
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION CAN SELL DOWN ———————————————————————————————————————————————

    def can_sell(self, marketprice: MarketPrice) -> Tuple[bool, dict]:
        broker = self.get_broker()
        n_period = self.get_marketprice_n_period()
        min_period = self.get_min_period()
        datas = {
            Map.roi: self.get_wallet().get_roi(broker),
<<<<<<< HEAD
            Map.maximum: self.get_max_price(marketprice),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            self.MARKETPRICE_BUY_BIG_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_BIG_PERIOD, n_period, broker),
<<<<<<< HEAD
=======
>>>>>>> Icarus-v13.1.3
=======
            # self.MARKETPRICE_BUY_BIG_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_BIG_PERIOD, n_period, broker),
            # self.MARKETPRICE_BUY_LITTLE_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_LITTLE_PERIOD, n_period, broker),
>>>>>>> Icarus-v13.1.4
=======
=======
            Map.maximum: self.max_roi(marketprice),
>>>>>>> Icarus-v13.5.1.1.2
            Map.buy: self.get_buy_order().get_execution_price(),
>>>>>>> Icarus-v13.3
=======
            Map.buy: self.get_buy_order().get_execution_price(),
>>>>>>> Icarus-v13.4.1
            min_period: self.get_marketprice(min_period, n_period, broker)
=======
            self.MARKETPRICE_BUY_LITTLE_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_LITTLE_PERIOD, n_period, broker),
            min_period: self.get_marketprice(self.MARKETPRICE_BUY_LITTLE_PERIOD, n_period, broker)
>>>>>>> Icarus-v10.1.1
        }
        return self._can_sell_indicator(marketprice, datas)
    
    def _can_sell_roi(self) -> bool:
        roi_pos = self.get_roi_position()
        max_loss = self.get_max_loss()
        can_sell = roi_pos <= max_loss
        return can_sell
<<<<<<< HEAD
=======
    
    def _can_sell_indicator(self, marketprice: MarketPrice) ->  bool:
<<<<<<< HEAD
<<<<<<< HEAD
=======
        """
>>>>>>> Icarus-v6.8
        def is_buy_period() -> bool:
            period = self.get_period()
            buy_time = int(self.get_buy_order().get_execution_time() / 1000)
            buy_time_rounded = _MF.round_time(buy_time, period)
            next_open_time = buy_time_rounded + period
            open_time = marketprice.get_time()
<<<<<<< HEAD
            return open_time < next_open_time
>>>>>>> Icarus-v5.12
=======
=======
            return open_time < first_open_time

<<<<<<< HEAD
        def is_supertrend_dropping() -> bool:
            supertrend = list(marketprice.get_super_trend())
            supertrend.reverse()
            supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -1)
            return supertrend_trend == MarketPrice.SUPERTREND_DROPPING
        
        def is_psar_dropping() -> bool:
            psar = list(marketprice.get_psar())
            psar.reverse()
            psar_trend = MarketPrice.get_psar_trend(closes, psar, -1)
            return psar_trend == MarketPrice.PSAR_DROPPING
        
        def is_macd_dropping() -> bool:
=======
        def is_rsi_reached(rsi_trigger: float, vars_map: Map) -> bool:
            # RSI
            rsi = list(marketprice.get_rsis())
            rsi.reverse()
            rsi_reached = rsi[-1] > rsi_trigger
            return rsi_reached

        def is_histogram_dropping(vars_map: Map) -> bool:
            # MACD
>>>>>>> Icarus-v6.8
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            macd_ok = macd[-1] <= macd[-2]
            return macd_ok

        def is_price_dropping() -> bool:
            opens = list(marketprice.get_opens())
            opens.reverse()
            price_dropping_2 = _MF.progress_rate(closes[-2], opens[-2])
            price_dropping_3 = _MF.progress_rate(closes[-3], opens[-3])
            return (price_dropping_2 < 0) and (price_dropping_3 < 0)

        can_sell = False
>>>>>>> Icarus-v5.9
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        # Psar
        supertrend = list(marketprice.get_super_trend())
        supertrend.reverse()
        supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -2)
        supertrend_dropping = supertrend_trend == MarketPrice.SUPERTREND_DROPPING
        # Keltner
        klc = marketprice.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_dropping = closes[-2] < klc_highs[-2]
        # Rsi
        rsi = list(marketprice.get_rsis())
        rsi.reverse()
        # Psar(Rsi)
        psar_rsi = list(marketprice.get_psar_rsis())
        psar_rsi.reverse()
        psar_rsi_trend = MarketPrice.get_psar_trend(rsi, psar_rsi, -2)
        psar_rsi_dropping = psar_rsi_trend == MarketPrice.PSAR_DROPPING
        # Check
<<<<<<< HEAD
        can_sell = supertrend_dropping or klc_dropping or psar_rsi_dropping
=======
        can_sell = (not is_buy_period()) and (is_price_dropping() or is_macd_dropping() or is_psar_dropping() or is_supertrend_dropping())
>>>>>>> Icarus-v5.9
        return can_sell
<<<<<<< HEAD
>>>>>>> Icarus-v5.2.1
=======
>>>>>>> Icarus-v5.3.1

    @classmethod
<<<<<<< HEAD
<<<<<<< HEAD
    def _get_stop_limit_price(cls, buy_price: float, max_roi: float) -> float:
        if max_roi >= cls._MAX_ROI_DROP_TRIGGER:
            stop_limit_price = buy_price * (1+(max_roi*(1-cls._MAX_ROI_DROP_RATE)))
        else:
            stop_limit_price = buy_price * (1+cls._MAX_LOSS)
        return stop_limit_price
=======
    def _get_max_drop_sell_price(cls, buy_price: float, max_roi: float) -> float:
=======
    def _get_max_drop_sell_price(cls, buy_price: Price, max_roi: float) -> float:
>>>>>>> Icarus-v13.5.1.1.2
        sell_price = None
        if max_roi >= cls._MAX_ROI_DROP_TRIGGER:
            sell_price = buy_price * (1+(max_roi*(1-cls._MAX_ROI_DROP_RATE)))
        return sell_price
>>>>>>> Icarus-v13.4.1

    @classmethod
    def _can_sell_indicator(cls, marketprice: MarketPrice, datas: dict = None) -> Tuple[bool, dict]:
<<<<<<< HEAD
<<<<<<< HEAD
        def get_marketprice(period: int) -> MarketPrice:
            return datas[period]

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        def is_histogram_negative(vars_map: Map) -> bool:
=======
        def are_macd_signal_negatives(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            macd_signal_negatives = (macd[-1] < 0) or (signal[-1] < 0)
            return macd_signal_negatives
=======
        def can_place_max_drop_limit(vars_map: Map) -> bool:
            place_max_drop_limit = max_roi >= cls._MAX_ROI_DROP_TRIGGER
            stop_limit_price = None
            # Get
            if place_max_drop_limit:
                stop_limit_price = cls._get_stop_limit_price(buy_price, max_roi)
=======
        ROI_TRIGGER = 0.2/100
        def get_marketprice(period: int) -> MarketPrice:
            return datas[period]

<<<<<<< HEAD
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
>>>>>>> Icarus-v13.4
            # Put
            vars_map.put(place_max_drop_limit, 'place_max_drop_limit')
            vars_map.put(stop_limit_price, 'stop_limit_price')
            return place_max_drop_limit
>>>>>>> Icarus-v13.3

        def is_tangent_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_dropping = macd[-1] <= macd[-2]
            return tangent_macd_dropping
        """

        def is_bollinger_reached(vars_map: Map) -> bool:
            bollinger = marketprice.get_bollingerbands()
            bollinger_high = list(bollinger.get(Map.high))
            bollinger_high.reverse()
            bollinger_low = list(bollinger.get(Map.low))
            bollinger_low.reverse()
            bollinger_reached = (closes[-1] >= bollinger_high[-1]) or (closes[-1] <= bollinger_low[-1])
            return bollinger_reached

        def is_roi_positive(vars_map: Map) -> bool:
            return roi > 0

        def is_ema_bellow_ema200(vars_map: Map) -> bool:
            ema = list(marketprice_6h.get_ema())
            ema.reverse()
            marketprice_6h.reset_collections()
            ema_200 = list(marketprice_6h.get_ema(cls.EMA_N_PERIOD))
            ema_200.reverse()
            # Check
            ema_bellow_ema200 = ema[-1] <= ema_200[-1]
            return ema_bellow_ema200

        def is_tangent_macd_5min_dropping(vars_map: Map) -> bool:
            macd_map = marketprice_5min.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_5min_dropping = macd[-1] <= macd[-2]
            return tangent_macd_5min_dropping
        
        def can_sell_with_macd_5min(vars_map: Map) -> bool:
            return is_roi_positive(vars_map) and is_ema_bellow_ema200(vars_map) and is_tangent_macd_5min_dropping(vars_map)
        """

        def is_buy_period(vars_map: Map) -> bool:
            buy_time = max(cls.get_buy_times(pair))
            buy_period = _MF.round_time(buy_time, period)
            open_time = marketprice.get_time()
            # Check
            its_buy_period = open_time == buy_period
            # Put
            vars_map.put(its_buy_period, 'its_buy_period')
            vars_map.put(_MF.unix_to_date(open_time), 'open_time')
            vars_map.put(_MF.unix_to_date(buy_time), 'buy_time')
            vars_map.put(_MF.unix_to_date(buy_period), 'buy_period')
            return its_buy_period

        def is_histogram_dropping(vars_map: Map) -> bool:
>>>>>>> Icarus-v10
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            histogram_negative = histogram[-1] < 0
            # Put
            vars_map.put(histogram_negative, 'histogram_negative')
            vars_map.put(histogram, Map.histogram)
            return histogram_negative

        def have_bought_macd_in_positive(vars_map: Map) -> bool:
            buy_time = max(cls.get_buy_times(pair))
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            # Get bought index
            buy_period = _MF.round_time(buy_time, period)
            buy_index = open_times.index(buy_period)
            # Check
            bought_macd_in_positive = macd[buy_index] >= 0
            # Put
            vars_map.put(bought_macd_in_positive, 'bought_macd_in_positive')
            vars_map.put(_MF.unix_to_date(buy_time), 'bought_macd_buy_time')
            vars_map.put(_MF.unix_to_date(buy_period), 'bought_macd_buy_period')
            vars_map.put(macd[buy_index], 'bought_macd')
            vars_map.put(macd, Map.macd)
            return bought_macd_in_positive

        def is_tangent_1min_macd_historgram_negative(vars_map: Map) -> bool:
            macd_map = marketprice_1min.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_1min_macd_historgram_negative = histogram[-1] <= histogram[-2]
            # Put
            vars_map.put(tangent_1min_macd_historgram_negative, 'tangent_1min_macd_historgram_negative')
            vars_map.put(histogram, 'macd_1min')
            return tangent_1min_macd_historgram_negative

        def is_buy_period(vars_map: Map) -> bool:
            buy_time = max(cls.get_buy_times(pair))
            buy_period = _MF.round_time(buy_time, period)
            open_time = marketprice.get_time()
            # Check
            its_buy_period = open_time == buy_period
            # Put
            vars_map.put(its_buy_period, 'its_buy_period')
            vars_map.put(_MF.unix_to_date(open_time), 'open_time')
            vars_map.put(_MF.unix_to_date(buy_time), 'buy_time')
            vars_map.put(_MF.unix_to_date(buy_period), 'buy_period')
            return its_buy_period

        def is_macd_histogram_negative(vars_map: Map) -> bool:
            marketprice.reset_collections()
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            macd_histogram_negative = histogram[-1] < 0
            # Put
            vars_map.put(macd_histogram_negative, 'macd_histogram_negative')
            vars_map.put(histogram, Map.histogram)
            return macd_histogram_negative

        def is_edited_macd_histogram_negative(vars_map: Map) -> bool:
            marketprice.reset_collections()
            macd_map = marketprice.get_macd(**cls.MACD_PARAMS_1)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            edited_macd_histogram_negative = histogram[-1] < 0
            # Put
            vars_map.put(edited_macd_histogram_negative, 'edited_macd_histogram_negative')
            vars_map.put(histogram, 'edited_histogram')
            return edited_macd_histogram_negative
=======
        """
        ROI_TRIGGER = 1/100
        def is_max_roi_above_trigger(vars_map: Map) -> bool:
            max_roi_above_trigger = max_roi >= ROI_TRIGGER
            vars_map.put(max_roi_above_trigger, 'max_roi_above_trigger')
            return max_roi_above_trigger
        """
        def is_macd_5min_historgram_positive(vars_map: Map) -> bool:
            macd_map = marketprice_5min.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            macd_5min_historgram_positive = histogram[-1] > 0
            # Put
            vars_map.put(macd_5min_historgram_positive, 'macd_5min_historgram_positive')
            vars_map.put(histogram, 'macd_5min_histogram')
            return macd_5min_historgram_positive

        def is_tangent_macd_5min_historgram_negative(vars_map: Map) -> bool:
            macd_map = marketprice_5min.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            macd_5min_historgram_negative = histogram[-1] <= histogram[-2]
            # Put
            vars_map.put(macd_5min_historgram_negative, 'macd_5min_historgram_negative')
            vars_map.put(histogram, 'macd_5min_histogram')
            return macd_5min_historgram_negative
>>>>>>> Icarus-v11.1.4
=======
        def is_min_tangent_rsi_negative(vars_map: Map) -> None:
            rsi = list(marketprice_1min.get_rsis())
            rsi.reverse()
            # Check
            min_tangent_rsi_negative = rsi[-1] < rsi[-2]
            # Put
            vars_map.put(min_tangent_rsi_negative, 'min_tangent_rsi_negative')
            vars_map.put(rsi, 'min_rsi')
            return min_tangent_rsi_negative
>>>>>>> Icarus-v11.4.5
=======
        def can_place_stop_limit_price(vars_map: Map) -> bool:
            place_stop_limit_price = True
            # Get Sell Price
            # Min(Opens(1min)[-2], Closes(1min)[-2])
            stop_limit_price = min([_1min_opens[-2], _1min_closes[-2]])
            # Put
            vars_map.put(place_stop_limit_price, 'place_stop_limit_price')
            vars_map.put(stop_limit_price, 'stop_limit_price')
            return place_stop_limit_price
        
        def get_buy_period(pair: Pair, period: int) -> int:
            buy_time = max(cls.get_buy_times(pair))
            buy_period = _MF.round_time(buy_time, period)
            return buy_period

        def is_1min_now_period_above_buy_period(vars_map: Map) -> bool:
            buy_period = get_buy_period(pair, marketprice_1min.get_period_time())
            now_period = _1min_open_times[-1]
            # Check
            _1min_now_period_above_buy_period = now_period > buy_period
            # Put
            vars_map.put(_1min_now_period_above_buy_period, '1min_now_period_above_buy_period')
            vars_map.put(_MF.unix_to_date(buy_period), 'buy_period')
            vars_map.put(_MF.unix_to_date(now_period), 'now_period')
            return _1min_now_period_above_buy_period
>>>>>>> Icarus-v13.2

        def is_min_roi_reached(vars_map: Map) -> bool:
            min_roi_reached = roi <= cls._MIN_ROI_TRIGGER
            # Put
            vars_map.put(min_roi_reached, 'min_roi_reached')
            return min_roi_reached

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

        def is_tangent_macd_negative(vars_map: Map) -> bool:
            marketprice.reset_collections()
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            # Check
            tangent_macd_negative = macd[-1] < macd[-2]
            # Put
            vars_map.put(tangent_macd_negative, 'tangent_macd_negative')
            vars_map.put(macd, Map.macd)
            return tangent_macd_negative

        def is_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            macd_dropping = macd[-1] <= macd[-2]
            vars_map.put(macd, 'macd')
            vars_map.put(macd_dropping, 'macd_dropping')
            return macd_dropping

        vars_map = Map()
=======
        def is_rsi_dropping() -> bool:
            rsi = list(marketprice.get_rsis())
            rsi.reverse()
            return rsi[-1] < self._RSI_SELL_TRIGGER

>>>>>>> Icarus-v5.12
        can_sell = False
<<<<<<< HEAD
        # Vars
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
        roi = datas[Map.roi]
        max_roi = datas[Map.maximum]
        buy_price = datas[Map.buy]
<<<<<<< HEAD
>>>>>>> Icarus-v13.3
=======
>>>>>>> Icarus-v13.4.1
        # MarketPrice
=======
>>>>>>> Icarus-v10.1
=======
        roi = datas[Map.roi]
        marketprice_1min = datas[cls.get_min_period()]
        marketprice_5min = datas[cls.MARKETPRICE_BUY_LITTLE_PERIOD]
        marketprice_6h = datas[cls.MARKETPRICE_BUY_BIG_PERIOD]
>>>>>>> Icarus-v10.1.1
        pair = marketprice.get_pair()
        period = marketprice.get_period_time()
        # Main Period
        closes = list(marketprice.get_closes())
        closes.reverse()
<<<<<<< HEAD
        opens = list(marketprice.get_opens())
        opens.reverse()
        # MarketPrice 1min
        marketprice_1min = get_marketprice(cls.get_min_period())
        _1min_closes = list(marketprice_1min.get_closes())
        _1min_closes.reverse()
        _1min_opens = list(marketprice_1min.get_opens())
        _1min_opens.reverse()
        _1min_lows = list(marketprice_1min.get_lows())
        _1min_lows.reverse()
        _1min_open_times = list(marketprice_1min.get_times())
        _1min_open_times.reverse()
        # MarketPrice Xmin
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        marketprice_6h = get_marketprice(cls.MARKETPRICE_BUY_BIG_PERIOD)
=======
>>>>>>> Icarus-v13.1.3
=======
        # marketprice_5min = get_marketprice(cls.MARKETPRICE_BUY_LITTLE_PERIOD)
        # marketprice_6h = get_marketprice(cls.MARKETPRICE_BUY_BIG_PERIOD)
>>>>>>> Icarus-v13.1.4
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        can_sell = is_histogram_negative(vars_map)
=======
        open_times = list(marketprice.get_times())
        open_times.reverse()
        # Other periods
        marketprice_5min = datas[cls.MARKETPRICE_BUY_LITTLE_PERIOD]
        marketprice_6h = datas[cls.MARKETPRICE_BUY_BIG_PERIOD]
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        if have_bought_macd_in_positive(vars_map):
            can_sell = is_tangent_1min_macd_historgram_negative(vars_map)
        else:
            can_sell = (not is_buy_period(vars_map))\
                and (
                    is_histogram_dropping(vars_map)
                    )
>>>>>>> Icarus-v10.1
=======
        can_sell = is_max_roi_above_trigger(vars_map) or ((not is_buy_period(vars_map)) and is_price_switch_down(vars_map))
>>>>>>> Icarus-v11.1.1
=======
        can_sell = is_1min_now_period_above_buy_period(vars_map) and can_place_stop_limit_price(vars_map)
>>>>>>> Icarus-v13.2
=======
        can_sell = is_1min_red_sequence_above_green_candle(vars_map)
=======
        can_sell = is_1min_red_sequence_above_green_candle(vars_map) or is_min_roi_reached(vars_map)
>>>>>>> Icarus-v13.3.1
        can_place_max_drop_limit(vars_map)
>>>>>>> Icarus-v13.3
=======
        can_sell = is_roi_above_trigger(vars_map) and is_1min_red_sequence_above_green_candle(vars_map)
<<<<<<< HEAD
>>>>>>> Icarus-v13.4
=======
        can_place_max_drop_limit(vars_map)
>>>>>>> Icarus-v13.4.1
=======
=======
>>>>>>> Icarus-v13.5.1.1.2
        can_sell = (is_roi_above_trigger(vars_map) and is_1min_red_sequence_above_green_candle(vars_map))\
            or (
                (is_supertrend_switch_down(vars_map) or is_psar_switch_down(vars_map)) or is_tangent_macd_negative(vars_map)\
                    and is_min_tangent_rsi_negative(vars_map)
            )
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> Icarus-v13.4.2
=======
        can_place_max_drop_limit(vars_map)
>>>>>>> Icarus-v13.5.1.1.2
=======
>>>>>>> Icarus-v13.5.1.1.2.1
        # Repport
        macd = vars_map.get(Map.macd)
        histogram = vars_map.get(Map.histogram)
        macd_1min = vars_map.get('macd_1min')
=======
        can_sell = is_max_roi_above_trigger(vars_map) or is_macd_histogram_negative(vars_map)
        # Repport
        histogram = vars_map.get(Map.histogram)
>>>>>>> Icarus-v11.1.10
        key = cls._can_buy_indicator.__name__
        supertrend = vars_map.get(Map.supertrend)
        psar = vars_map.get(Map.psar)
        min_rsi = vars_map.get('min_rsi')
        macd = vars_map.get(Map.macd)
        repport = {
            f'{key}._can_sell_indicator': can_sell,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.histogram_negative': vars_map.get('histogram_negative'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None
=======
            f'{key}.bought_macd_in_positive': vars_map.get('bought_macd_in_positive'),
            f'{key}.tangent_1min_macd_historgram_negative': vars_map.get('tangent_1min_macd_historgram_negative'),
            f'{key}.its_buy_period': vars_map.get('its_buy_period'),
            f'{key}.histogram_dropping': vars_map.get('histogram_dropping'),
=======
            f'{key}.max_roi_above_trigger': vars_map.get('max_roi_above_trigger'),
<<<<<<< HEAD
            f'{key}.its_buy_period': vars_map.get('its_buy_period'),
            f'{key}.price_switch_down': vars_map.get('price_switch_down'),
>>>>>>> Icarus-v11.1.1
=======
            f'{key}.macd_histogram_negative': vars_map.get('macd_histogram_negative'),
>>>>>>> Icarus-v11.1.10

            f'{key}.open_time': vars_map.get('open_time'),
            f'{key}.buy_time': vars_map.get('buy_time'),
            f'{key}.buy_period': vars_map.get('buy_period'),

            f'{key}.bought_macd_buy_time': vars_map.get('bought_macd_buy_time'),
            f'{key}.bought_macd_buy_period': vars_map.get('bought_macd_buy_period'),
            f'{key}.bought_macd': vars_map.get('bought_macd'),

            f'{key}.open_time': vars_map.get('open_time'),
            f'{key}.buy_time': vars_map.get('buy_time'),
            f'{key}.buy_period': vars_map.get('buy_period'),
=======
=======
            f'{key}.roi_above_trigger': vars_map.get('roi_above_trigger'),
>>>>>>> Icarus-v13.4
            f'{key}.red_sequence_above_green_candle': vars_map.get('red_sequence_above_green_candle'),
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.place_max_drop_limit': vars_map.get('place_max_drop_limit'),
=======
=======
>>>>>>> Icarus-v13.5.1.1.2
            f'{key}.supertrend_switch_down': vars_map.get('supertrend_switch_down'),
            f'{key}.psar_switch_down': vars_map.get('psar_switch_down'),
            f'{key}.tangent_macd_negative': vars_map.get('tangent_macd_negative'),
            f'{key}.min_tangent_rsi_negative': vars_map.get('min_tangent_rsi_negative'),
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> Icarus-v13.4.2
=======
            f'{key}.place_max_drop_limit': vars_map.get('place_max_drop_limit'),
>>>>>>> Icarus-v13.5.1.1.2
=======
>>>>>>> Icarus-v13.5.1.1.2.1
            
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
            f'{key}.min_roi_reached': vars_map.get('min_roi_reached'),
>>>>>>> Icarus-v13.3.1

<<<<<<< HEAD
            f'{key}.MIN_ROI_TRIGGER': cls._MIN_ROI_TRIGGER,
            f'{key}.MAX_ROI_DROP_TRIGGER': cls._MAX_ROI_DROP_TRIGGER,
            f'{key}.MAX_ROI_DROP_RATE': cls._MAX_ROI_DROP_RATE,
            f'{key}.buy_price': buy_price,
            f'{key}.roi': roi,
            f'{key}.max_roi': max_roi,
            f'{key}.place_max_drop_limit': vars_map.get('place_max_drop_limit'),
            f'{key}.stop_limit_price': vars_map.get('stop_limit_price'),
            Map.price: vars_map.get('stop_limit_price'),

            Map.price: vars_map.get('stop_limit_price'),

=======
>>>>>>> Icarus-v13.5.1.1.2
            f'{key}.supertrend_dropping_1': vars_map.get('supertrend_dropping_1'),
            f'{key}.supertrend_rising_2': vars_map.get('supertrend_rising_2'),

            f'{key}.psar_dropping_1': vars_map.get('psar_dropping_1'),
            f'{key}.psar_rising_2': vars_map.get('psar_rising_2'),
<<<<<<< HEAD
=======

<<<<<<< HEAD
            Map.price: vars_map.get('stop_limit_price'),
>>>>>>> Icarus-v13.5.1.1.2

=======
>>>>>>> Icarus-v13.5.1.1.2.1
            f'{key}.closes[-1]': closes[-1],
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
<<<<<<< HEAD
            f'{key}.histogram_5min[-1]': histogram_5min[-1] if histogram_5min is not None else None
>>>>>>> Icarus-v10.1
=======
            f'{key}.macd_1min[-1]': macd_1min[-1] if macd_1min is not None else None
>>>>>>> Icarus-v10.1.1
=======
            f'{key}.opens[-1]': opens[-1],
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None
>>>>>>> Icarus-v11.1.10
=======
        can_sell = is_max_roi_above_trigger(vars_map) or (is_edited_macd_histogram_negative(vars_map) and is_macd_histogram_negative(vars_map))
        # Repport
        histogram = vars_map.get(Map.histogram)
        edited_histogram = vars_map.get('edited_histogram')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}._can_sell_indicator': can_sell,
            f'{key}.max_roi_above_trigger': vars_map.get('max_roi_above_trigger'),
            f'{key}.macd_histogram_negative': vars_map.get('macd_histogram_negative'),
            f'{key}.edited_macd_histogram_negative': vars_map.get('edited_macd_histogram_negative'),
=======
        marketprice_1min = datas[cls.get_min_period()]
        marketprice_5min = datas[cls.MARKETPRICE_BUY_LITTLE_PERIOD]
        marketprice_6h = datas[cls.MARKETPRICE_BUY_BIG_PERIOD]
        # Check
        can_sell = is_roi_above_trigger(vars_map) and is_min_tangent_rsi_negative(vars_map)
        # Repport
        min_rsi = vars_map.get('min_rsi')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}._can_sell_indicator': can_sell,
            f'{key}.roi_above_trigger': vars_map.get('roi_above_trigger'),
            f'{key}.min_tangent_rsi_negative': vars_map.get('min_tangent_rsi_negative'),
>>>>>>> Icarus-v11.4.5

            f'{key}.roi_trigger': ROI_TRIGGER,
            f'{key}.max_roi': max_roi,
            f'{key}.roi': roi,

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
<<<<<<< HEAD
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.edited_histogram[-1]': edited_histogram[-1] if edited_histogram is not None else None
>>>>>>> Icarus-v11.1.13
=======
        can_sell = is_macd_5min_historgram_positive(vars_map) and is_tangent_macd_5min_historgram_negative(vars_map)
        # Repport
        macd_5min_histogram = vars_map.get('macd_5min_histogram')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}._can_sell_indicator': can_sell,
            f'{key}.macd_5min_historgram_positive': vars_map.get('macd_5min_historgram_positive'),
            f'{key}.macd_5min_historgram_negative': vars_map.get('macd_5min_historgram_negative'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.macd_5min_histogram[-1]': macd_5min_histogram[-1] if macd_5min_histogram is not None else None,
            f'{key}.macd_5min_histogram[-2]': macd_5min_histogram[-2] if macd_5min_histogram is not None else None
>>>>>>> Icarus-v11.1.4
=======
            f'{key}.min_rsi[-1]': min_rsi[-1] if min_rsi is not None else None,
            f'{key}.min_rsi[-2]': min_rsi[-2] if min_rsi is not None else None
>>>>>>> Icarus-v11.4.5
=======
            f'{key}.1min_now_period_above_buy_period': vars_map.get('1min_now_period_above_buy_period'),
            f'{key}.place_stop_limit_price': vars_map.get('place_stop_limit_price'),

            f'{key}.buy_period': vars_map.get('buy_period'),
            f'{key}.now_period': vars_map.get('now_period'),
            Map.stopPrice: vars_map.get('stop_limit_price'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.1min_closes[-1]': _1min_closes[-1],
            f'{key}.1min_closes[-2]': _1min_closes[-2],
            f'{key}.1min_opens[-1]': _1min_opens[-1],
            f'{key}.1min_opens[-2]': _1min_opens[-2],
            f'{key}.1min_lows[-1]': _1min_lows[-1],
            f'{key}.1min_lows[-2]': _1min_lows[-2]
>>>>>>> Icarus-v13.2
=======
            f'{key}.opens[-1]': opens[-1],
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.supertrend[-2]': supertrend[-2] if supertrend is not None else None,
            f'{key}.psar[-1]': psar[-1] if psar is not None else None,
            f'{key}.psar[-2]': psar[-2] if psar is not None else None,
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
            f'{key}.macd[-2]': macd[-2] if macd is not None else None,
            f'{key}.min_rsi[-1]': min_rsi[-1] if min_rsi is not None else None,
            f'{key}.min_rsi[-2]': min_rsi[-2] if min_rsi is not None else None
>>>>>>> Icarus-v13.4.2
        }
        return can_sell, repport
=======
        can_sell = is_rsi_dropping() if is_buy_period() else (is_macd_dropping() or is_psar_dropping() or is_supertrend_dropping())
        # can_sell = (not is_buy_period()) and (is_macd_dropping() or is_psar_dropping() or is_supertrend_dropping())
=======
        if not is_buy_period():
            if is_macd_dropping(vars_map):
                can_sell = True
            else:
                can_sell = is_rsi_ok(70, vars_map) if is_ema_rising(vars_map) else is_rsi_ok(50, vars_map)
>>>>>>> Icarus-v6.2
=======
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        # Check
        # can_sell = (not is_buy_period()) and (is_histogram_dropping(vars_map) or (are_macd_signal_negatives(vars_map) and is_tangent_macd_dropping(vars_map)))
        can_sell = is_bollinger_reached(vars_map)
>>>>>>> Icarus-v6.8
        return can_sell
>>>>>>> Icarus-v5.12

    def _can_sell_prediction(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        def is_prediction_reached() -> bool:
            max_roi = self.max_roi(marketprice)
            max_roi_pred = self.max_roi_predicted()
            return max_roi >= max_roi_pred
<<<<<<< HEAD

=======
        def is_market_dropping() -> Tuple[bool, float]:
            close = marketprice.get_close()
            func_new_max_close_pred = get_new_max_close_pred()
            new_max_roi_pred = _MF.progress_rate(func_new_max_close_pred, close)
            func_market_dropping = new_max_roi_pred < self.get_prediction_roi_high_trigger()
            return func_market_dropping, func_new_max_close_pred
>>>>>>> Icarus-v4.3.2
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

        can_sell = is_prediction_reached() and (not is_new_prediction_better())
        return can_sell

    # ——————————————————————————————————————————— FUNCTION CAN SELL UP —————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION TRY BUY/SELL DOWN ———————————————————————————————————————————

    def _try_buy(self, market_price: MarketPrice, bkr: Broker) -> Map:
>>>>>>> Icarus-test
        """
        To try to buy position\n
        :param market_price: market price
        :return: set of execution instruction
                 Map[index{int}]:   {str}
        """
        executions = Map()
        # Reset
        self._reset_max_rsi()
        self._reset_max_roi()
        self._reset_floor_secure_order()
<<<<<<< HEAD
<<<<<<< HEAD
=======
        self._reset_max_close_predicted()
        self._reset_min_price_predicted()
>>>>>>> Icarus-v4.3.2
        # Evaluate Buy
<<<<<<< HEAD
        can_buy = self.can_buy(market_price)
=======
        self._reset_max_close_predicted()
        # Big
<<<<<<< HEAD
=======
        # big_period = Icarus.MARKETPRICE_BUY_BIG_PERIOD
        # big_marketprice = self.get_marketprice(big_period)
        # little
        # little_period = Icarus.MARKETPRICE_BUY_LITTLE_PERIOD
        # little_marketprice = self.get_marketprice(little_period)
>>>>>>> Icarus-v13.1.4
        # min
        min_period = Icarus.get_min_period()
        min_marketprice = self.get_marketprice(min_period)
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
        can_buy, buy_repport = self.can_buy(market_price, big_marketprice, min_marketprice)
>>>>>>> Icarus-test
=======
        can_buy, buy_repport = self.can_buy(market_price, min_marketprice)
>>>>>>> Icarus-v13.1.3
=======
        # can_buy, buy_repport = self.can_buy(market_price, big_marketprice, little_marketprice, min_marketprice)
        can_buy, buy_repport = self.can_buy(market_price, min_marketprice)
>>>>>>> Icarus-v13.1.4
=======
        minute_marketprice = self.get_marketprice(period=60, n_period=10)
        if self.get_nb_trade() >= 9:
            a = 1
        can_buy, repport = self.can_buy(market_price, minute_marketprice)
>>>>>>> Icarus-v6.4.1
        if can_buy:
<<<<<<< HEAD
=======
            self._set_max_close_predicted(predictor_marketprice=predictor_marketprice)
            self._set_min_price_predicted()
>>>>>>> Icarus-v4.3.2
            self._buy(executions)
<<<<<<< HEAD
            self._secure_position(executions)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        self.save_move(market_price)
=======
=======
>>>>>>> Icarus-v13.4.2.3
=======
>>>>>>> Icarus-v2.1.2.2
=======
>>>>>>> Icarus-v5.13
=======
            # self._secure_position(executions)
            self._reset_histogram_list(self.get_pair())
>>>>>>> Icarus-v6.4.1
        # Save
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
>>>>>>> Icarus-v13.3
        return executions

    def _try_sell(self, market_price: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param market_price: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
<<<<<<< HEAD
        executions = Map()
=======
        '''
        def is_new_prediction_higher(old_close: float, new_close: float) -> bool:
            return new_close > old_close
        '''

        def is_occupation_trigger_reached() -> bool:
            occup_trigger = self.get_prediction_occupation_secure_trigger()
            occupation = self.prediction_max_occupation(market_price)
            return occupation >= occup_trigger

        def is_max_price_higher(old_max_price: float, new_max_price: float) -> bool:
            return new_max_price > old_max_price
        '''
        def is_secure_is_max_loss() -> bool:
            buy_order = self.get_buy_order()
            secure_order = self._get_secure_order()
            return secure_order.get_limit_price().get_value() < buy_order.get_execution_price().get_value()
        '''

        executions = Map()
        # max_close_pred = self.get_max_close_predicted()
        old_max_price = self.get_max_prices()[-1]
>>>>>>> Icarus-v5.13
        # Evaluate Sell
        can_sell = self.can_sell(market_price)
        if can_sell:
<<<<<<< HEAD
            self._sell(executions)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        elif self.get_roi_floor(market_price) != self.get_floor_secure_order():
            self._move_up_secure_order(executions)
        self.save_move(market_price)
=======
            # self._sell(executions)
            secure_order = self._get_secure_order()
            new_stop_price = repport[Map.stopPrice]
            if secure_order is None:
                self._secure_position(executions)
            elif new_stop_price > secure_order.get_stop_price():
                self._move_up_secure_order(executions)
=======
        elif (repport[Map.price] is not None) and (repport[Map.price] > self._get_secure_order().get_limit_price()):
            self._move_up_secure_order(executions)
>>>>>>> Icarus-v13.3
=======
        elif repport[Map.price] is not None:
            secure_order = self._get_secure_order()
            if secure_order is None:
                self._secure_position(executions)
            elif repport[Map.price] > secure_order.get_limit_price().get_value():
=======
        else:
            # new_max_close_pred = self.get_max_close_predicted()
            occup_trigger_reached = is_occupation_trigger_reached()
            max_price_higher = is_max_price_higher(old_max_price, new_max_price=self.get_max_price(market_price))
            if occup_trigger_reached and max_price_higher:
>>>>>>> Icarus-v5.13
                self._move_up_secure_order(executions)
>>>>>>> Icarus-v13.5.1.1.2
=======
>>>>>>> Icarus-v13.5.1.1.2.1
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
        self.save_sell_conditions(repport)
>>>>>>> Icarus-v13.2
        return executions

    """
    @staticmethod
    def get_rsi_step() -> float:
        return Icarus._RSI_STEP
    """

    @staticmethod
    def get_max_loss() -> float:
        return Icarus._MAX_LOSS

    """
    @staticmethod
    def get_roi_step() -> float:
        return Icarus._ROI_STEP
    """

    """
    @staticmethod
    def get_rsi_buy_trigger() -> float:
        return Icarus._RSI_BUY_TRIGGER

    @staticmethod
<<<<<<< HEAD
    def get_rsi_sell_trigger() -> float:
        return Icarus._RSI_SELL_TRIGGER
    """
=======
    def get_predictor_n_period() -> int:
        return Icarus._PREDICTOR_N_PERIOD

    @staticmethod
    def get_prediction_roi_high_trigger() -> float:
        return Icarus._PREDICTION_ROI_HIGH_TRIGGER

    @staticmethod
    def get_prediction_roi_low_trigger() -> float:
        return Icarus._PREDICTION_ROI_LOW_TRIGGER
    
    @staticmethod
    def get_prediction_filling_rate() -> float:
        return Icarus._PREDICTION_FILLING_RATE
    
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY DOWN —————————————————————————————————————————
>>>>>>> Icarus-v2.1.2.2

<<<<<<< HEAD
    @staticmethod
    def stalker_can_add(market_price: MarketPrice) -> bool:
        # Close
        closes = list(market_price.get_closes())
        closes.reverse()
        # Supertrend
        supertrends = list(market_price.get_super_trend())
        supertrends.reverse()
        supertrends_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -2)
        supertrend_ok = supertrends_trend == MarketPrice.SUPERTREND_RISING
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        psar_trend = MarketPrice.get_psar_trend(closes, psars, -2)
<<<<<<< HEAD
        psar_ok = psar_trend == MarketPrice.PSAR_RISING
        # Keltner
=======
        psar_rising = psar_trend == MarketPrice.PSAR_RISING
        # Check
        can_add = psar_rising
        return can_add

    @staticmethod
    def can_buy(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> bool:
        if predictor_marketprice.get_period_time() != Icarus.get_predictor_period():
            predictor_period = Icarus.get_predictor_period()
            period = predictor_marketprice.get_period_time()
            raise ValueError(f"Predictor's MarketPrice must have period '{predictor_period}', instead '{period}'")
        # indicator
        indicator_ok = Icarus._can_buy_indicator(child_marketprice)
        # Check
        can_buy = indicator_ok and Icarus._can_buy_prediction(predictor_marketprice, child_marketprice)
        return can_buy

    @staticmethod
    def _can_buy_indicator(child_marketprice: MarketPrice) -> bool:
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        # Supertrend
        supertrend = list(child_marketprice.get_super_trend())
        supertrend.reverse()
        now_supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -2)
        prev_supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -3)
        # Psar
        psar = list(child_marketprice.get_psar())
        psar.reverse()
        now_psar_trend = MarketPrice.get_psar_trend(closes, psar, -2)
        prev_psar_trend = MarketPrice.get_psar_trend(closes, psar, -3)
        # Keltner
        klc = child_marketprice.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_rising = closes[-2] > klc_highs[-2]
        # Rsi
        rsi = list(child_marketprice.get_rsis())
        rsi.reverse()
        # Psar(Rsi)
        psar_rsi = list(child_marketprice.get_psar_rsis())
        psar_rsi.reverse()
        psar_rsi_trend = MarketPrice.get_psar_trend(rsi, psar_rsi, -2)
        psar_rsi_rising = psar_rsi_trend == MarketPrice.PSAR_RISING
        # Check
        supertrend_rising = now_supertrend_trend == MarketPrice.SUPERTREND_RISING
        supertrend_switch_up = supertrend_rising and (prev_supertrend_trend == MarketPrice.SUPERTREND_DROPPING)
        psar_switch_up = (now_psar_trend == MarketPrice.PSAR_RISING) and (prev_psar_trend == MarketPrice.PSAR_DROPPING)
        can_buy_indicator = (psar_switch_up and supertrend_rising and klc_rising and psar_rsi_rising) or (supertrend_switch_up and klc_rising and psar_rsi_rising)
        return can_buy_indicator

    @staticmethod
    def _can_buy_prediction(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> bool:
        close = child_marketprice.get_close()
        pair = child_marketprice.get_pair()
        period = Icarus.get_predictor_period()
        predictor = Predictor(pair, period)
        max_close_pred = Icarus._predict_max_high(predictor_marketprice, predictor)
        max_roi_pred = _MF.progress_rate(max_close_pred, close)
        max_roi_ok = max_roi_pred >= Icarus.get_min_roi_predicted()
        return max_roi_ok
    
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY UP ———————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION PRREDICTOR DOWN ——————————————————————————————————————
    
    @staticmethod
    def _predict_max_high(predictor_marketprice: MarketPrice, predictor: Predictor) -> float:
        model = predictor.get_model(Predictor.HIGH)
        n_feature = model.n_feature()
        highs = list(predictor_marketprice.get_highs())
        highs.reverse()
        xs, ys = Predictor.generate_dataset(highs, n_feature)
        highs_np = Predictor.market_price_to_np(predictor_marketprice, Predictor.HIGH, n_feature)
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
        predictor_marketprice = agrs['predictor_marketprice']
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
>>>>>>> Icarus-v5.2.1
        klc = market_price.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_ok = (closes[-2] > klc_highs[-2]) and (closes[-1] > closes[-2])
        # MACD
        macd_map = market_price.get_macd()
        macds = list(macd_map.get(Map.macd))
        macds.reverse()
        signals = list(macd_map.get(Map.signal))
        signals.reverse()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        macd_ok = (macds[-2] > 0) and (signals[-2] > 0) and (histograms[-2] > 0)
        can_add = supertrend_ok and psar_ok and klc_ok and macd_ok
        return can_add

    @staticmethod
    def can_buy(market_price: MarketPrice) -> bool:
        # Close
        closes = list(market_price.get_closes())
        closes.reverse()
        # Supertrend
        supertrends = list(market_price.get_super_trend())
        supertrends.reverse()
        supertrends_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -2)
        supertrend_ok = supertrends_trend == MarketPrice.SUPERTREND_RISING
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        psar_trend = MarketPrice.get_psar_trend(closes, psars, -2)
        psar_ok = psar_trend == MarketPrice.PSAR_RISING
        # Keltner
        klc = market_price.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_ok = (closes[-3] < klc_highs[-3]) and (closes[-2] > klc_highs[-2]) and (closes[-1] > closes[-2])
        # MACD
        macd_map = market_price.get_macd()
        macds = list(macd_map.get(Map.macd))
        macds.reverse()
        signals = list(macd_map.get(Map.signal))
        signals.reverse()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        macd_ok = (macds[-2] > 0) and (signals[-2] > 0) and (histograms[-2] > 0)
        can_buy = supertrend_ok and psar_ok and klc_ok and macd_ok
        return can_buy
=======
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def can_buy(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, big_marketprice, min_marketprice)
=======
    def can_buy(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, little_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, big_marketprice, little_marketprice, min_marketprice)
>>>>>>> Icarus-v11.3.2
=======
    def can_buy(cls, child_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, min_marketprice)
>>>>>>> Icarus-v13.1.3
=======
    def can_buy(cls, child_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, min_marketprice)
>>>>>>> Icarus-v13.1.4
=======
    def can_buy(cls, child_marketprice: MarketPrice, minute_marketprice: MarketPrice) -> Tuple[bool, dict]:
        if child_marketprice.get_period_time() != 60*15:
            child_period = cls.get_period()
            market_period = child_marketprice.get_period_time()
            raise ValueError(f"MarketPrice must have period '{child_period}', instead '{market_period}'")
        # indicator
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, minute_marketprice)
>>>>>>> Icarus-v6.4.1
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        def is_histogram_switch_positive(vars_map: Map) -> bool:
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
=======
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice) -> Tuple[bool, dict]:
=======
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, little_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
>>>>>>> Icarus-v11.3.2
        def price_change(i: int) -> float:
            return closes[i] - opens[i]
=======
=======
>>>>>>> Icarus-v13.1.4
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        N_CANDLE = 60
        TRIGGER_CANDLE_CHANGE = 0.5/100
        TRIGGE_KELTNER = 0.1/100
        def price_change(i: int, open_prices: list[float], close_prices: list[float]) -> float:
            n_open = len(open_prices)
            n_close = len(close_prices)
            if n_open != n_close:
                raise ValueError(f"Price lists must have  the same size, instead '{n_open}'!='{n_close}' (open!=close)")
            return close_prices[i] - open_prices[i]
>>>>>>> Icarus-v13.1.3
=======
    def _can_buy_indicator(cls, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
<<<<<<< HEAD
=======
    def _get_histograms(cls) -> Map:
        """
        Map[Pair.__str__()][index{int}][Map.time]:      {int}      # Unix time of histogram (in second)
        Map[Pair.__str__()][index{int}][Map.histogram]: {float}    # Value of histogram
        """
        if cls._MACD_HISTOGRAM is None:
            cls._MACD_HISTOGRAM = Map()
        return cls._MACD_HISTOGRAM

    @classmethod
    def _reset_histogram_list(cls, pair: Pair) -> list:
        str_pair = pair.__str__()
        histograms = cls._get_histograms()
        if str_pair in histograms.get_keys():
            histograms.get_map()[str_pair] = None
            del histograms.get_map()[str_pair]

    @classmethod
    def _get_histogram_list(cls, pair: Pair) -> list:
        str_pair = pair.__str__()
        histograms = cls._get_histograms()
        if histograms.get(str_pair) is None:
            histograms.put([], str_pair)
        return histograms.get(str_pair)

    @classmethod
    def _update_histogram_list(cls, child_marketprice: MarketPrice, minute_marketprice: MarketPrice) -> None:
        pair = child_marketprice.get_pair()
        # Minute
        minute_open_time = minute_marketprice.get_time()
        # MACD
        macd_map = child_marketprice.get_macd()
        histogram = list(macd_map.get(Map.histogram))
        histogram.reverse()
        histogram_list = cls._get_histogram_list(pair)
        if (len(histogram_list) == 0) or (minute_open_time > histogram_list[-1][Map.time]):
            row = {
                Map.time: minute_open_time,
                Map.histogram: histogram[-1]
                }
            histogram_list.append(row)
        if len(histogram_list) > 2:
            del histogram_list[0]

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, minute_marketprice: MarketPrice) -> Tuple[bool, dict]:
>>>>>>> Icarus-v6.4.1
=======
>>>>>>> Icarus-v7.1
        def is_ema_rising(vars_map: Map) -> bool:
            # EMA
            ema = list(child_marketprice.get_ema(cls.EMA_N_PERIOD))
            ema.reverse()
            ema_rising = closes[-1] > ema[-1]
            # Put
            vars_map.put(ema, 'ema')
            vars_map.put(ema_rising, 'ema_rising')
            return ema_rising

<<<<<<< HEAD
<<<<<<< HEAD
        def is_macd_switch_up(vars_map: Map) -> bool:
            # MACD
=======
=======
        """
>>>>>>> Icarus-v7.1
        def is_macd_negative(vars_map: Map) -> bool:
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            macd_negative = macd[-1] < 0
            # Put
            vars_map.put(macd, 'macd')
            vars_map.put(macd_negative, 'macd_negative')
            return macd_negative

<<<<<<< HEAD
        def is_macd_histogram_rising(vars_map: Map) -> bool:
>>>>>>> Icarus-v6.7
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_rising = histogram[-1] > 0
            # Put
            vars_map.put(histogram, 'histogram')
            vars_map.put(histogram_rising, 'histogram_rising')
            return histogram_rising

        def is_rsi_reached(vars_map: Map) -> bool:
            rsi = list(child_marketprice.get_rsis())
            rsi.reverse()
            rsi_reached = rsi[-1] > 60
            # Put
            vars_map.put(rsi_reached, 'rsi_reached')
            vars_map.put(rsi, Map.rsi)
            return rsi_reached

        def is_edited_macd_switch_up(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            macd_map = child_marketprice.get_macd(signal=cls.MACD_SIGNAL)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_rising = histogram[-1] > 0
            prev_histogram_dropping = histogram[-2] < 0
            macd_switch_up = histogram_rising and prev_histogram_dropping
            # Put
            vars_map.put(histogram, 'edited_histogram')
            vars_map.put(histogram_rising, 'edited_histogram_rising')
            vars_map.put(prev_histogram_dropping, 'edited_prev_histogram_dropping')
            vars_map.put(macd_switch_up, 'edited_macd_switch_up')
            return macd_switch_up
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> Icarus-v6.1
=======

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Icarus-v7.2.10
        def is_closes_above_low_keltner(vars_map: Map) -> bool:
            open_times = list(child_marketprice.get_times())
            open_times.reverse()
            keltner_low = list(child_marketprice.get_keltnerchannel().get(Map.low))
            keltner_low.reverse()
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            last_min_index = MarketPrice.last_extremum_index(macd, signal, -1, excludes=[])
            macd_swing = _MF.group_swings(macd, signal)
            interval = macd_swing[last_min_index]
            sub_open_times = open_times[interval[0]:interval[1]+1]
            # Min Close
            sub_close = closes[interval[0]:interval[1]+1]
            min_close = min(sub_close)
            min_close_open_time = sub_open_times[sub_close.index(min_close)]
            # Min Keltner
            sub_keltner_low = keltner_low[interval[0]:interval[1]+1]
            min_keltner = min(sub_keltner_low)
            min_keltner_open_time = sub_open_times[sub_keltner_low.index(min_keltner)]
            # Check
            closes_above_low_keltner = min_close > min_keltner
            # Put
            vars_map.put(closes_above_low_keltner, 'closes_above_low_keltner')
            vars_map.put(_MF.unix_to_date(min_close_open_time), 'min_close_date')
            vars_map.put(min_close, 'min_close')
            vars_map.put(_MF.unix_to_date(min_keltner_open_time), 'min_keltner_date')
            vars_map.put(min_keltner, 'min_keltner')
            vars_map.put(keltner_low, 'keltner_low')
            vars_map.put(macd, Map.macd)
            vars_map.put(signal, Map.signal)
            vars_map.put(histogram, Map.histogram)
            return closes_above_low_keltner

<<<<<<< HEAD
        """
=======
>>>>>>> Icarus-v7.13
=======

>>>>>>> Icarus-v7.2
=======
        def is_bellow_keltner(vars_map: Map) -> bool:
            kc = child_marketprice.get_keltnerchannel()
            kc_high = list(kc.get(Map.high))
            kc_high.reverse()
            bellow_keltner = closes[-1] < kc_high[-1]
            return bellow_keltner

>>>>>>> Icarus-v7.2.1
=======
>>>>>>> Icarus-v7.2.10
        def will_market_bounce(vars_map: Map) -> bool:
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
>>>>>>> Icarus-v7.10

        def is_price_switch_up(vars_map: Map) -> bool:
>>>>>>> Icarus-v11.1.1
            # Check
<<<<<<< HEAD
            histogram_switch_positive = (histogram[-1] > 0) and (histogram[-2] < 0)
=======
            price_change_1 = price_change(-1, opens, closes)
            price_change_2 = price_change(-2, opens, closes)
<<<<<<< HEAD
            min_price_change_1 = price_change(-1, min_opens, min_closes)
            price_switch_up = (price_change_1 > abs(price_change_2)) and (min_price_change_1 > 0)
>>>>>>> Icarus-v13.4.2.2
=======
            price_switch_up = (price_change_1 > abs(price_change_2))
>>>>>>> Icarus-v13.5
            # Put
<<<<<<< HEAD
            vars_map.put(histogram_switch_positive, 'histogram_switch_positive')
            vars_map.put(histogram, Map.histogram)
            return histogram_switch_positive
=======
            vars_map.put(price_switch_up, 'price_switch_up')
            vars_map.put(price_change_2, 'switch_up_price_change_2')
            vars_map.put(price_change_3, 'switch_up_price_change_3')
            return price_switch_up
>>>>>>> Icarus-v11.1.1

<<<<<<< HEAD
        def is_price_above_prev_high(vars_map: Map) -> bool:
            # Check
            price_change_2 = price_change(-2)
<<<<<<< HEAD
            price_above_prev_high = (price_change_2 < 0) and (highs[-1] >= highs[-2])
=======
            price_change_3 = price_change(-3)
            price_change_1 = price_change(-1)
            price_switch_up = (price_change_3 < 0) and (price_change_2 > 0) and (price_change_1 >= abs(price_change_3))
>>>>>>> Icarus-v11.4.9
            # Put
<<<<<<< HEAD
            vars_map.put(price_above_prev_high, 'price_above_prev_high')
            vars_map.put(price_change_2, 'above_prev_high_price_change_2')
            return price_above_prev_high
=======
            vars_map.put(price_switch_up, 'price_switch_up')
            vars_map.put(price_change_1, 'price_change_1')
            vars_map.put(price_change_2, 'price_change_2')
<<<<<<< HEAD
            vars_map.put(price_change_3, 'price_change_3')
            return price_switch_up

<<<<<<< HEAD
        def is_macd_histogram_positive(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            macd_histogram_positive = histogram[-1] > 0
            # Put
            vars_map.put(macd_histogram_positive, 'macd_histogram_positive')
            vars_map.put(histogram, Map.histogram)
            return macd_histogram_positive

        def is_little_edited_macd_histogram_positive(vars_map: Map) -> bool:
            macd_map = little_marketprice.get_macd(**cls.MACD_PARAMS_1)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            little_edited_macd_histogram_positive = histogram[-1] > 0
            # Put
            vars_map.put(little_edited_macd_histogram_positive, 'little_edited_macd_histogram_positive')
            vars_map.put(histogram, 'little_edited_macd_histogram')
            return little_edited_macd_histogram_positive
>>>>>>> Icarus-v11.1.13

        def is_close_3_bellow_keltner_middle_3(vars_map: Map) -> bool:
            keltner = child_marketprice.get_keltnerchannel()
            keltner_middle = list(keltner.get(Map.middle))
            keltner_middle.reverse()
            close_3_bellow_keltner_middle_3 = closes[-3] < keltner_middle[-3]
            # Put
            vars_map.put(close_3_bellow_keltner_middle_3, f'close_3_bellow_keltner_middle_3')
            vars_map.put(keltner_middle, 'keltner_middle')
            return close_3_bellow_keltner_middle_3
=======
        def is_close_above_high_2(vars_map: Map) -> bool:
            # Check
            price_change_2 = price_change(-2)
            close_above_high_2 = (price_change_2 < 0) and (closes[-1] >= highs[-2])
            # Put
            vars_map.put(close_above_high_2, 'close_above_high_2')
            vars_map.put(price_change_2, 'close_above_high_2_price_change_2')
            return close_above_high_2
>>>>>>> Icarus-v11.1.5

        def is_min_macd_signal_peak_nearest_than_min(vars_map: Map) -> bool:
            macd_map = min_marketprice.get_macd()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            # Get extremums
            now_index = len(signal) - 1
            signal_swings = _MF.group_swings(macd, signal)
            start_index = signal_swings[now_index][0]
            sub_signal = signal[start_index:]
            # — Peak
            signal_peak = max(sub_signal)
            signal_peak_index = sub_signal.index(signal_peak)
            # — Min
            signal_min = min(sub_signal)
            signal_min_index = sub_signal.index(signal_min)
            # Dates
            sub_min_open_times = min_open_times[start_index:]
            # Check
            min_macd_signal_peak_nearest_than_min = signal_peak_index > signal_min_index
            # Put
            vars_map.put(min_macd_signal_peak_nearest_than_min, 'min_macd_signal_peak_nearest_than_min')
            vars_map.put(_MF.unix_to_date(sub_min_open_times[signal_peak_index]), 'min_macd_signal_peak_date')
            vars_map.put(_MF.unix_to_date(sub_min_open_times[signal_min_index]), 'min_macd_signal_min_date')
            vars_map.put(macd, 'min_macd')
            vars_map.put(signal, 'min_macd_signal')
            return min_macd_signal_peak_nearest_than_min

        def is_tangent_min_macd_positive(vars_map: Map) -> bool:
            macd_map = min_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            # Check
            tangent_min_macd_positive = macd[-1] > macd[-2]
            # Put
            vars_map.put(tangent_min_macd_positive, 'tangent_min_macd_positive')
            vars_map.put(macd, 'min_macd')
            return tangent_min_macd_positive

        def is_edited_min_macd_histogram_positive(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            macd_map = min_marketprice.get_macd(**cls.MACD_PARAMS_1)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            edited_min_macd_histogram_positive = histogram[-1] > 0
            # Put
            vars_map.put(edited_min_macd_histogram_positive, 'edited_min_macd_histogram_positive')
            vars_map.put(histogram, 'min_edited_histogram')
            return edited_min_macd_histogram_positive

        def is_rsi_above_peak_macd_posive_histogram(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            rsi = list(child_marketprice.get_rsis())
            rsi.reverse()
=======
            def macd_last_peak_index(macd: list, signal: list, histogram: list) -> int:
                posi_macd_indexes = []
                macd_df = pd.DataFrame({Map.macd: macd, Map.signal: signal, Map.histogram: histogram})
                posi_macd_df = macd_df[(macd_df[Map.histogram] > 0) & (macd_df[Map.macd] > 0) & (macd_df[Map.signal] > 0)]
                posi_indexes = posi_macd_df.index
                for i in range(1, posi_macd_df.shape[0]):
                    i = -i
                    posi_macd_indexes.append(posi_indexes[i])
                    next_is_in = abs(posi_indexes[i] - posi_indexes[i-1]) == 1
                    if next_is_in:
                        continue
                    ban_current_slice = (macd_df.loc[macd_df.index[-1], Map.macd] > 0) and (macd_df.index[-1] in posi_macd_indexes)
                    if (not next_is_in) and ban_current_slice:
                        posi_macd_indexes = []
                        continue
                    else:
                        break
                last_highs_df = macd_df[macd_df.index.isin(posi_macd_indexes)]
                last_macd_peak = last_highs_df[Map.macd].max()
                last_macd_peak_index = last_highs_df[last_highs_df[Map.macd] == last_macd_peak].index[-1]
                return last_macd_peak_index

            child_marketprice.reset_collections()
            open_times = list(child_marketprice.get_times())
            open_times.reverse()
>>>>>>> Icarus-v6.7
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            if histogram[-1] <= 0:
                raise ValueError(f"MACD's histogram must be positive, instead histogram='{histogram[-1]}'")
            # Get interval
            now_index = len(macd) - 1
            macd_swings = _MF.group_swings(macd, signal)
            start_index = macd_swings[now_index][0]
            sub_rsi = rsi[start_index:]
            rsi_peak = max(sub_rsi)
            # Dates
            sub_open_times = open_times[start_index:]
            peak_index = sub_rsi.index(rsi_peak)
            peak_time = sub_open_times[peak_index]
            # Check
            rsi_above_peak_macd_posive_histogram = rsi[-1] >= rsi_peak
            # Put
<<<<<<< HEAD
<<<<<<< HEAD
            vars_map.put(rsi_above_peak_macd_posive_histogram, 'rsi_above_peak_macd_posive_histogram')
            vars_map.put(_MF.unix_to_date(open_times[start_index]), 'rsi_above_peak_start_interval')
            vars_map.put(_MF.unix_to_date(peak_time), 'rsi_above_peak_peak_date')
            vars_map.put(rsi_peak, 'rsi_above_peak_rsi_peak')
            vars_map.put(rsi, Map.rsi)
            vars_map.put(signal, Map.signal)
            vars_map.put(macd, Map.macd)
            vars_map.put(histogram, Map.histogram)
            return rsi_above_peak_macd_posive_histogram
=======
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
>>>>>>> Icarus-v13.5

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

        def is_tangent_macd_histogram_positive(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_macd_histogram_positive = histogram[-1] > histogram[-2]
            # Put
            vars_map.put(tangent_macd_histogram_positive, 'tangent_macd_histogram_positive')
            vars_map.put(histogram, Map.histogram)
            return tangent_macd_histogram_positive

        def is_tangent_min_edited_macd_histogram_positive(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            macd_map = min_marketprice.get_macd(**cls.MACD_PARAMS_1)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_min_edited_macd_histogram_positive = histogram[-1] > histogram[-2]
            # Put
            vars_map.put(tangent_min_edited_macd_histogram_positive, 'tangent_min_edited_macd_histogram_positive')
            vars_map.put(histogram, 'min_edited_histogram')
            return tangent_min_edited_macd_histogram_positive

        def is_min_keltner_roi_above_trigger(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            keltner_map = min_marketprice.get_keltnerchannel(multiple=1)
            keltner_low = list(keltner_map.get(Map.low))
            keltner_low.reverse()
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            # Check
            keltner_roi = _MF.progress_rate(keltner_high[-1], keltner_low[-1])
            min_keltner_roi_above_trigger = keltner_roi >= TRIGGE_KELTNER
            # Put
            vars_map.put(min_keltner_roi_above_trigger, 'min_keltner_roi_above_trigger')
            vars_map.put(keltner_roi, 'keltner_roi')
            vars_map.put(keltner_map.get_map(), 'min_keltner')
            return min_keltner_roi_above_trigger

        def is_psar_rising(vars_map: Map) -> bool:
            psar = list(child_marketprice.get_psar())
            psar.reverse()
            psar_rising = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_RISING
            vars_map.put(psar_rising, 'psar_rising')
            vars_map.put(psar, Map.psar)
            return psar_rising

        def is_min_psar_rising(vars_map: Map) -> bool:
            psar = list(min_marketprice.get_psar())
            psar.reverse()
            min_psar_rising = MarketPrice.get_psar_trend(min_closes, psar, -1) == MarketPrice.PSAR_RISING
            vars_map.put(min_psar_rising, 'min_psar_rising')
            vars_map.put(psar, 'min_psar')
            return min_psar_rising

        def is_min_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(min_marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            min_supertrend_rising = MarketPrice.get_super_trend_trend(min_closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            # Put
            vars_map.put(min_supertrend_rising, 'min_supertrend_rising')
            vars_map.put(supertrend, 'min_supertrend')
            return min_supertrend_rising

        def is_delta_macd_rising(vars_map: Map) -> bool:
            histogram_rising = False
            minute_open_time = minute_marketprice.get_time()
            minute_period = minute_marketprice.get_period_time()
            child_period = child_marketprice.get_period_time()
            child_open_time = child_marketprice.get_time()
            histogram_list = cls._get_histogram_list(pair)
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            stored_histogram = None
            prev_histogram = histogram[-2]
            if (len(histogram_list) >= 2) and (minute_period  <= (minute_open_time - child_open_time) < child_period) and (prev_histogram < 0):
                stored_histogram = histogram_list[-2][Map.histogram]
                histogram_rising = ((stored_histogram + prev_histogram) > 0) and ((histogram[-1] + prev_histogram) > 0)
            vars_map.put(histogram_rising, 'histogram_rising')
            vars_map.put(_MF.unix_to_date(minute_open_time), 'minute_open_time')
            vars_map.put(stored_histogram, 'stored_histogram')
            vars_map.put(histogram_list, 'histogram_list')
            return histogram_rising
=======
            vars_map.put(macd_min_index, 'macd_min_index')
            vars_map.put(last_min_macd, 'last_min_macd')
            vars_map.put(macd_peak_index, 'macd_peak_index')
            vars_map.put(last_peak_macd, 'last_peak_macd')
            vars_map.put(will_bounce, 'will_bounce')
            vars_map.put(macd_min_date, 'macd_min_date')
            vars_map.put(macd_peak_date, 'macd_peak_date')
            return will_bounce
<<<<<<< HEAD

        def is_bellow_keltner(vars_map: Map) -> bool:
            keltner_map = child_marketprice.get_keltnerchannel()
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            bellow_keltner = closes[-1] < keltner_high[-1]
            vars_map.put(bellow_keltner, 'close_bellow_keltner')
            vars_map.put(keltner_high, 'keltner_high')
            return bellow_keltner
        """
>>>>>>> Icarus-v7.13.2

        def is_macd_switch_up(vars_map: Map) -> bool:
            # MACD
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_rising = (histogram[-2] > 0) and (histogram[-1] > 0)
            prev_histogram_dropping = histogram[-3] < 0
            macd_switch_up = histogram_rising and prev_histogram_dropping
            # Put
            vars_map.put(histogram, 'histogram')
            vars_map.put(histogram_rising, 'histogram_rising')
            vars_map.put(prev_histogram_dropping, 'prev_histogram_dropping')
            vars_map.put(macd_switch_up, 'macd_switch_up')
            return macd_switch_up

<<<<<<< HEAD
        def is_bellow_keltner(vars_map: Map) -> bool:
            keltner_map = child_marketprice.get_keltnerchannel()
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            bellow_keltner = closes[-1] < keltner_high[-1]
            vars_map.put(bellow_keltner, 'close_bellow_keltner')
            vars_map.put(keltner_high, 'keltner_high')
            return bellow_keltner
=======
            vars_map.put(macd_min_index, 'macd_min_index')
            vars_map.put(last_min_macd, 'last_min_macd')
            vars_map.put(macd_peak_index, 'macd_peak_index')
            vars_map.put(last_peak_macd, 'last_peak_macd')
            vars_map.put(will_bounce, 'will_bounce')
            vars_map.put(macd_min_date, 'macd_min_date')
            vars_map.put(macd_peak_date, 'macd_peak_date')
            return will_bounce
>>>>>>> Icarus-v7.13.1

=======
>>>>>>> Icarus-v7.13.2
        def is_lows_above_low_keltner(vars_map: Map) -> bool:
            open_times = list(child_marketprice.get_times())
            open_times.reverse()
            lows = list(child_marketprice.get_lows())
            lows.reverse()
            keltner_low = list(child_marketprice.get_keltnerchannel().get(Map.low))
            keltner_low.reverse()
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            last_min_index = MarketPrice.last_extremum_index(macd, signal, -1, excludes=[])
            macd_swing = _MF.group_swings(macd, signal)
            interval = macd_swing[last_min_index]
            sub_open_times = open_times[interval[0]:interval[1]+1]
            # Min Close
            sub_lows = lows[interval[0]:interval[1]+1]
            min_low = min(sub_lows)
            min_low_open_time = sub_open_times[sub_lows.index(min_low)]
            # Min Keltner
            sub_keltner_low = keltner_low[interval[0]:interval[1]+1]
            min_keltner = min(sub_keltner_low)
            min_keltner_open_time = sub_open_times[sub_keltner_low.index(min_keltner)]
            # Check
            lows_above_low_keltner = min_low > min_keltner
            # Put
            vars_map.put(lows_above_low_keltner, 'lows_above_low_keltner')
            vars_map.put(_MF.unix_to_date(min_low_open_time), 'min_low_date')
            vars_map.put(min_low, 'min_low')
            vars_map.put(_MF.unix_to_date(min_keltner_open_time), 'min_keltner_date')
            vars_map.put(min_keltner, 'min_keltner')
            vars_map.put(keltner_low, 'keltner_low')
            vars_map.put(macd, Map.macd)
            vars_map.put(signal, Map.signal)
            vars_map.put(histogram, Map.histogram)
            return lows_above_low_keltner

        """
=======
>>>>>>> Icarus-v7.2

        def is_macd_switch_up(vars_map: Map) -> bool:
            # MACD
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            histogram_rising = (histogram[-2] > 0) and (histogram[-1] > 0)
            prev_histogram_dropping = histogram[-3] < 0
            macd_switch_up = histogram_rising and prev_histogram_dropping
            # Put
            vars_map.put(histogram, 'histogram')
            vars_map.put(histogram_rising, 'histogram_rising')
            vars_map.put(prev_histogram_dropping, 'prev_histogram_dropping')
            vars_map.put(macd_switch_up, 'macd_switch_up')
            return macd_switch_up

        def is_bellow_keltner(vars_map: Map) -> bool:
            keltner_map = child_marketprice.get_keltnerchannel()
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            bellow_keltner = closes[-1] < keltner_high[-1]
            vars_map.put(bellow_keltner, 'close_bellow_keltner')
            vars_map.put(keltner_high, 'keltner_high')
            return bellow_keltner

        def is_macd_bellow_bull_peak(vars_map: Map) -> bool:
            def macd_bull_peak_index(closes: list, highs: list, lows: list, macd: list, signal: list, ema: list, supertrend: list) -> Tuple[int, dict]:
                all_df = pd.DataFrame({Map.close: closes, Map.high: highs, Map.low: lows, Map.macd: macd, Map.signal: signal, Map.ema: ema, Map.supertrend: supertrend})
                all_df['mean_h_l'] = (all_df[Map.high] + all_df[Map.low])/2
                now_index = all_df.shape[0] - 1
                # Swing
                supertrend_swings = _MF.group_swings(all_df['mean_h_l'].to_list(), supertrend)
                ema_swings = _MF.group_swings(highs, ema)
                interval_start_index = min([supertrend_swings[now_index][0], ema_swings[now_index][0]])
                interval_end_index = max([supertrend_swings[now_index][1], ema_swings[now_index][1]])
                # peak
                interval_df = all_df.loc[interval_start_index:interval_end_index+1]
                peak_macd = interval_df[Map.macd][interval_df[Map.macd] > interval_df[Map.signal]].max()
                peak_macd_index = interval_df[interval_df[Map.macd] == peak_macd].index[-1]
                # Repport
                repport = {
                    Map.start: interval_start_index,
                    Map.end: interval_end_index
                }
                return peak_macd_index, repport

            open_times = list(child_marketprice.get_times())
            open_times.reverse()
            closes = list(child_marketprice.get_closes())
            closes.reverse()
            highs = list(child_marketprice.get_highs())
            highs.reverse()
            lows = list(child_marketprice.get_lows())
            lows.reverse()
            macd_map = child_marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            signal = list(macd_map.get(Map.signal))
            signal.reverse()
            macd.reverse()
            ema = list(child_marketprice.get_ema(n_period=cls.EMA_N_PERIOD))
            ema.reverse()
            supertrend = list(child_marketprice.get_super_trend())
            supertrend.reverse()
            # Global Peak
            macd_peak_index, repport = macd_bull_peak_index(closes=closes, highs=highs, lows=lows, macd=macd, signal=signal, ema=ema, supertrend=supertrend)
            global_macd_peak = macd[macd_peak_index]
            # Local peak
            now_index = len(macd) - 1
            macd_swings = _MF.group_swings(macd, signal)
            sub_macd = macd[macd_swings[now_index][0]:macd_swings[now_index][1]+1]
            local_macd_peak = max(sub_macd)
            # Check
            macd_bellow_bull_peak = local_macd_peak < global_macd_peak
            # Put
            vars_map.put(macd_bellow_bull_peak, 'macd_bellow_bull_peak')
            vars_map.put(_MF.unix_to_date(open_times[repport[Map.start]]), 'macd_bull_peak_iterval_start')
            vars_map.put(_MF.unix_to_date(open_times[repport[Map.end]]), 'macd_bull_peak_iterval_end')
            vars_map.put(_MF.unix_to_date(open_times[macd_peak_index]), 'global_macd_bull_peak_date')
            vars_map.put(global_macd_peak, 'global_macd_bull_peak')
            vars_map.put(local_macd_peak, 'local_macd_bull_peak')
            vars_map.put(highs, Map.high)
            vars_map.put(lows, Map.low)
            vars_map.put(macd, Map.macd)
            vars_map.put(signal, Map.signal)
            vars_map.put(ema, Map.ema)
            vars_map.put(supertrend, Map.supertrend)
            return macd_bellow_bull_peak

        vars_map = Map()
<<<<<<< HEAD
        # Child
        period = child_marketprice.get_period_time()
        pair = child_marketprice.get_pair()
<<<<<<< HEAD
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        highs = list(child_marketprice.get_highs())
        highs.reverse()
        opens = list(child_marketprice.get_opens())
        opens.reverse()
<<<<<<< HEAD
<<<<<<< HEAD
        open_times = list(child_marketprice.get_times())
        open_times.reverse()
        # Min
<<<<<<< HEAD
        min_closes = list(min_marketprice.get_closes())
        min_closes.reverse()
        min_opens = list(min_marketprice.get_opens())
        min_opens.reverse()
=======
>>>>>>> Icarus-v11.3.2
        min_open_times = list(min_marketprice.get_times())
        min_open_times.reverse()
        # Little
=======
        highs = list(child_marketprice.get_highs())
        highs.reverse()
>>>>>>> Icarus-v11.1.1
=======
        highs = list(child_marketprice.get_highs())
        highs.reverse()
>>>>>>> Icarus-v11.1.5
        # Big
<<<<<<< HEAD
<<<<<<< HEAD
        # Check
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        can_buy_indicator = is_histogram_switch_positive(vars_map)
=======
        can_buy_indicator = is_price_switch_up(vars_map) or is_price_above_prev_high(vars_map)
>>>>>>> Icarus-v11.1.1
=======
        can_buy_indicator = is_price_switch_up(vars_map) or is_close_above_high_2(vars_map)
>>>>>>> Icarus-v11.1.5
=======
        can_buy_indicator = (is_price_switch_up(vars_map) or is_price_change_1_above_2(vars_map))\
            and is_edited_macd_histogram_positive(vars_map) and is_min_edited_macd_histogram_positive(vars_map)\
                and is_macd_histogram_positive(vars_map) and is_edited_macd_above_peak(vars_map)\
                    and is_rsi_above_peak_macd_posive_histogram(vars_map)
>>>>>>> Icarus-v11.4.4
=======
        # big_closes = list(big_marketprice.get_closes())
        # big_closes.reverse()
        # Check
        can_buy_indicator = is_price_switch_up(vars_map) and is_mean_candle_change_60_above_trigger(vars_map)\
<<<<<<< HEAD
            and is_min_close_bellow_min_keltner_middle(vars_map)
>>>>>>> Icarus-v13.1.4
        # Repport
        macd = vars_map.get(Map.macd)
        signal = vars_map.get(Map.signal)
        histogram = vars_map.get(Map.histogram)
<<<<<<< HEAD
=======
        can_buy_indicator = is_price_switch_up(vars_map)\
            and is_macd_histogram_positive(vars_map) and is_little_edited_macd_histogram_positive(vars_map)\
                and is_close_3_bellow_keltner_middle_3(vars_map)
        # Repport
        histogram = vars_map.get(Map.histogram)
        little_edited_macd_histogram = vars_map.get('little_edited_macd_histogram')
        keltner_middle = vars_map.get('keltner_middle')
>>>>>>> Icarus-v11.1.13
=======
        can_buy_indicator = (is_price_switch_up(vars_map) or is_price_change_1_above_2(vars_map))\
            and (is_min_macd_signal_peak_nearest_than_min(vars_map) or is_tangent_min_macd_positive(vars_map))
        # Repport
        min_macd_signal = vars_map.get('min_macd_signal')
        min_macd = vars_map.get('min_macd')
>>>>>>> Icarus-v11.3.2
=======
        can_buy_indicator = (is_price_switch_up(vars_map) or is_price_change_1_above_2(vars_map))\
            and is_edited_min_macd_histogram_positive(vars_map)
        # Repport
=======
        rsi = vars_map.get(Map.rsi)
        edited_histogram = vars_map.get('edited_histogram')
        edited_macd = vars_map.get('edited_macd')
        edited_signal = vars_map.get('edited_signal')
>>>>>>> Icarus-v11.4.4
        min_edited_histogram = vars_map.get('min_edited_histogram')
>>>>>>> Icarus-v11.3.3
=======
            and is_supertrend_rising(vars_map) and is_min_close_bellow_min_keltner_middle(vars_map)
=======
        # Check
        can_buy_indicator = is_price_switch_up(vars_map) and is_mean_candle_change_60_above_trigger(vars_map)\
<<<<<<< HEAD
            and is_supertrend_rising(vars_map) and is_min_macd_histogram_switch_up(vars_map)
>>>>>>> Icarus-v13.5
=======
            and is_supertrend_rising(vars_map) and is_min_macd_histogram_switch_up(vars_map)\
                and is_tangent_macd_histogram_positive(vars_map) and is_tangent_min_edited_macd_histogram_positive(vars_map)\
                    and is_min_keltner_roi_above_trigger(vars_map) and is_psar_rising(vars_map) and is_min_psar_rising(vars_map) and is_min_supertrend_rising(vars_map)
>>>>>>> Icarus-v13.5.1.1.2
        # Repport
        min_histogram = vars_map.get('min_histogram')
        keltner_low = vars_map.get('min_keltner', Map.low)
        keltner_middle = vars_map.get('min_keltner', Map.middle)
        keltner_high = vars_map.get('min_keltner', Map.high)
        min_edited_histogram = vars_map.get('min_edited_histogram')
        supertrend = vars_map.get(Map.supertrend)
<<<<<<< HEAD
>>>>>>> Icarus-v13.4.2
=======
        histogram = vars_map.get(Map.histogram)
        psar = vars_map.get(Map.psar)
        min_psar = vars_map.get('min_psar')
        min_supertrend = vars_map.get('min_supertrend')
>>>>>>> Icarus-v13.5.1.1.2
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.histogram_switch_positive': vars_map.get('histogram_switch_positive'),
=======
            f'{key}.price_switch_up': vars_map.get('price_switch_up'),
            f'{key}.mean_candle_change_60_above_trigger': vars_map.get('mean_candle_change_60_above_trigger'),
            f'{key}.supertrend_rising': vars_map.get('supertrend_rising'),
            f'{key}.min_macd_histogram_switch_up': vars_map.get('min_macd_histogram_switch_up'),
            f'{key}.tangent_macd_histogram_positive': vars_map.get('tangent_macd_histogram_positive'),
            f'{key}.tangent_min_edited_macd_histogram_positive': vars_map.get('tangent_min_edited_macd_histogram_positive'),
            f'{key}.min_keltner_roi_above_trigger': vars_map.get('min_keltner_roi_above_trigger'),
            f'{key}.psar_rising': vars_map.get('psar_rising'),
            f'{key}.min_psar_rising': vars_map.get('min_psar_rising'),
            f'{key}.min_supertrend_rising': vars_map.get('min_supertrend_rising'),

            f'{key}.price_change_1': vars_map.get('price_change_1'),
            f'{key}.price_change_2': vars_map.get('price_change_2'),

            f'{key}.mean_candle_change_60_mean_positive_candle': vars_map.get('mean_candle_change_60_mean_positive_candle'),
            
            f'{key}.TRIGGE_KELTNER': TRIGGE_KELTNER,
            f'{key}.keltner_roi': vars_map.get('keltner_roi'),

>>>>>>> Icarus-v13.1.4
            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.min_closes[-1]': min_closes[-1],
            f'{key}.min_opens[-1]': min_opens[-1],
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None
=======
            f'{key}.price_switch_up': vars_map.get('price_switch_up'),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.price_above_prev_high': vars_map.get('price_above_prev_high'),
=======
            f'{key}.macd_histogram_positive': vars_map.get('macd_histogram_positive'),
<<<<<<< HEAD
            f'{key}.little_edited_macd_histogram_positive': vars_map.get('little_edited_macd_histogram_positive'),
            f'{key}.close_3_bellow_keltner_middle_3': vars_map.get('close_3_bellow_keltner_middle_3'),
>>>>>>> Icarus-v11.1.13
=======
            f'{key}.close_above_high_2': vars_map.get('close_above_high_2'),
>>>>>>> Icarus-v11.1.5
=======
            f'{key}.price_change_1_above_2': vars_map.get('price_change_1_above_2'),
<<<<<<< HEAD
            f'{key}.min_macd_signal_peak_nearest_than_min': vars_map.get('min_macd_signal_peak_nearest_than_min'),
            f'{key}.tangent_min_macd_positive': vars_map.get('tangent_min_macd_positive'),
>>>>>>> Icarus-v11.3.2
=======
            f'{key}.edited_min_macd_histogram_positive': vars_map.get('edited_min_macd_histogram_positive'),
>>>>>>> Icarus-v11.3.3
=======
            f'{key}.edited_macd_above_peak': vars_map.get('edited_macd_above_peak'),
            f'{key}.rsi_above_peak_macd_posive_histogram': vars_map.get('rsi_above_peak_macd_posive_histogram'),
>>>>>>> Icarus-v11.4.4

            f'{key}.switch_up_price_change_2': vars_map.get('switch_up_price_change_2'),
            f'{key}.switch_up_price_change_3': vars_map.get('switch_up_price_change_3'),

            f'{key}.above_prev_high_price_change_2': vars_map.get('above_prev_high_price_change_2'),

            f'{key}.close_above_high_2_price_change_2': vars_map.get('close_above_high_2_price_change_2'),

            f'{key}.min_macd_signal_peak_date': vars_map.get('min_macd_signal_peak_date'),
            f'{key}.min_macd_signal_min_date': vars_map.get('min_macd_signal_min_date'),

            f'{key}.rsi_above_peak_start_interval': vars_map.get('rsi_above_peak_start_interval'),
            f'{key}.rsi_above_peak_peak_date': vars_map.get('rsi_above_peak_peak_date'),
            f'{key}.rsi_above_peak_rsi_peak': vars_map.get('rsi_above_peak_rsi_peak'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.highs[-1]': highs[-1],
=======
            f'{key}.highs[-1]': highs[-1],
            f'{key}.highs[-2]': highs[-2],
>>>>>>> Icarus-v11.1.5
            f'{key}.big_closes[-1]': big_closes[-1]
>>>>>>> Icarus-v11.1.1
=======
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
            f'{key}.signal[-1]': signal[-1] if signal is not None else None,
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
<<<<<<< HEAD
            f'{key}.little_edited_macd_histogram[-1]': little_edited_macd_histogram[-1] if little_edited_macd_histogram is not None else None,
=======
>>>>>>> Icarus-v13.1.3
            f'{key}.keltner_middle[-1]': keltner_middle[-1] if keltner_middle is not None else None,
            f'{key}.keltner_middle[-2]': keltner_middle[-2] if keltner_middle is not None else None,
            f'{key}.keltner_middle[-3]': keltner_middle[-3] if keltner_middle is not None else None
>>>>>>> Icarus-v11.1.13
=======
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.min_macd_signal[-1]': min_macd_signal[-1] if min_macd_signal is not None else None,
            f'{key}.min_macd[-1]': min_macd[-1] if min_macd is not None else None,
            f'{key}.min_macd[-2]': min_macd[-2] if min_macd is not None else None
>>>>>>> Icarus-v11.3.2
=======
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.min_edited_histogram[-1]': min_edited_histogram[-1] if min_edited_histogram is not None else None,
>>>>>>> Icarus-v11.3.3
=======
            f'{key}.edited_macd[-1]': edited_macd[-1] if edited_macd is not None else None,
            f'{key}.edited_signal[-1]': edited_signal[-1] if edited_signal is not None else None,
            f'{key}.edited_histogram[-1]': edited_histogram[-1] if edited_histogram is not None else None,
            f'{key}.min_edited_histogram[-1]': min_edited_histogram[-1] if min_edited_histogram is not None else None,
            f'{key}.rsi[-1]': rsi[-1] if rsi is not None else None
>>>>>>> Icarus-v11.4.4
=======
            # f'{key}.big_closes[-1]': big_closes[-1],
=======
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.supertrend[-2]': supertrend[-2] if supertrend is not None else None,
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> Icarus-v13.4.2
            f'{key}.min_keltner_middle[-1]': min_keltner_middle[-1] if min_keltner_middle is not None else None
>>>>>>> Icarus-v13.1.4
=======
            f'{key}.min_histogram[-1]': min_histogram[-1] if min_histogram is not None else None,
            f'{key}.min_histogram[-2]': min_histogram[-2] if min_histogram is not None else None
>>>>>>> Icarus-v13.5
=======
            f'{key}.min_supertrend[-1]': min_supertrend[-1] if min_supertrend is not None else None,
            f'{key}.min_supertrend[-2]': min_supertrend[-2] if min_supertrend is not None else None,
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None,
            f'{key}.min_edited_histogram[-1]': min_edited_histogram[-1] if min_edited_histogram is not None else None,
            f'{key}.min_edited_histogram[-2]': min_edited_histogram[-2] if min_edited_histogram is not None else None,
            f'{key}.psar[-1]': psar[-1] if psar is not None else None,
            f'{key}.psar[-2]': psar[-2] if psar is not None else None,
            f'{key}.min_psar[-1]': min_psar[-1] if min_psar is not None else None,
            f'{key}.min_psar[-2]': min_psar[-2] if min_psar is not None else None,
            f'{key}.min_histogram[-1]': min_histogram[-1] if min_histogram is not None else None,
            f'{key}.min_histogram[-2]': min_histogram[-2] if min_histogram is not None else None,
            f'{key}.keltner_low[-1]': keltner_low[-1] if keltner_low is not None else None,
            f'{key}.keltner_middle[-1]': keltner_middle[-1] if keltner_middle is not None else None,
            f'{key}.keltner_high[-1]': keltner_high[-1] if keltner_high is not None else None
>>>>>>> Icarus-v13.5.1.1.2
=======
    def _can_buy_indicator(cls, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        # Supertrend
        supertrend = list(child_marketprice.get_super_trend())
        supertrend.reverse()
        now_supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -1)
        prev_supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -2)
        # Psar
        psar = list(child_marketprice.get_psar())
        psar.reverse()
        now_psar_trend = MarketPrice.get_psar_trend(closes, psar, -1)
        prev_psar_trend = MarketPrice.get_psar_trend(closes, psar, -2)
        # MACD
        macd_map = child_marketprice.get_macd()
        macd = list(macd_map.get(Map.macd))
        histogram = list(macd_map.get(Map.histogram))
        histogram.reverse()
        macd.reverse()
        histogram_ok = histogram[-1] > 0
        macd_ok = macd[-1] > macd[-2]
        macd_rising = macd_ok and histogram_ok
        # EMA
        ema = list(child_marketprice.get_ema(cls.EMA_N_PERIOD))
        ema.reverse()
        ema_rising = closes[-1] > ema[-1]
        # RSI
        rsi = list(child_marketprice.get_rsis())
        rsi.reverse()
        rsi_rising = rsi[-1] > cls._RSI_BUY_TRIGGER
        # Check
<<<<<<< HEAD
        supertrend_rising = now_supertrend_trend == MarketPrice.SUPERTREND_RISING
        supertrend_switch_up = supertrend_rising and (prev_supertrend_trend == MarketPrice.SUPERTREND_DROPPING)
        psar_rising = now_psar_trend == MarketPrice.PSAR_RISING
        psar_switch_up = psar_rising and (prev_psar_trend == MarketPrice.PSAR_DROPPING)
        # can_buy_indicator = macd_rising and ((psar_switch_up and supertrend_rising) or (supertrend_switch_up and psar_rising))
        # can_buy_indicator = ema_rising and rsi_rising and macd_rising and (supertrend_rising and psar_rising)
        can_buy_indicator = ema_rising and macd_rising and (supertrend_rising and psar_rising)
=======
        if is_ema_rising(vars_map):
            rsi_trigger = 70
            can_buy_indicator = is_macd_switch_up(vars_map) and is_rsi_ok(rsi_trigger, vars_map)
        else:
            rsi_trigger = 50
            can_buy_indicator = is_macd_switch_up(vars_map) and is_rsi_ok(rsi_trigger, vars_map)
>>>>>>> Icarus-v6.1
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and ((is_lows_above_low_keltner(vars_map) or is_bellow_keltner(vars_map)) and is_macd_bellow_bull_peak(vars_map))
>>>>>>> Icarus-v7.13
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and (is_bellow_keltner(vars_map) and is_macd_bellow_bull_peak(vars_map))
>>>>>>> Icarus-v7.13.1
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and (is_lows_above_low_keltner(vars_map) and is_macd_bellow_bull_peak(vars_map))
>>>>>>> Icarus-v7.13.2
        # Repport
        key = cls._can_buy_indicator.__name__
=======
        pair = child_marketprice.get_pair()
        cls._update_histogram_list(child_marketprice, minute_marketprice)
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        delta_macd_rising = is_delta_macd_rising(vars_map)
        can_buy_indicator = is_ema_rising(vars_map) and is_macd_negative(vars_map) and is_macd_switch_up(vars_map) and delta_macd_rising
=======
        can_buy_indicator = is_ema_rising(vars_map) and is_macd_negative(vars_map) and is_macd_histogram_rising(vars_map) and is_edited_macd_switch_up(vars_map) and will_market_bounce(vars_map)
>>>>>>> Icarus-v6.7
=======
        can_buy_indicator = is_ema_rising(vars_map) and is_macd_negative(vars_map) \
            and is_macd_histogram_rising(vars_map) and is_edited_macd_switch_up(vars_map) \
                and is_rsi_reached(vars_map) and will_market_bounce(vars_map)
>>>>>>> Icarus-v6.7.1
=======
        # can_buy_indicator = is_ema_rising(vars_map) and is_macd_negative(vars_map) and is_macd_switch_up(vars_map) and will_market_bounce(vars_map)
<<<<<<< HEAD
<<<<<<< HEAD
        can_buy_indicator = is_ema_rising(vars_map) and is_macd_switch_up(vars_map)
>>>>>>> Icarus-v7.1
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and is_closes_above_low_keltner(vars_map)
>>>>>>> Icarus-v7.10
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and will_market_bounce(vars_map)
>>>>>>> Icarus-v7.2
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and will_market_bounce(vars_map) and is_bellow_keltner(vars_map)
>>>>>>> Icarus-v7.2.1
=======
        can_buy_indicator = is_macd_switch_up(vars_map) and will_market_bounce(vars_map) and is_closes_above_low_keltner(vars_map)
>>>>>>> Icarus-v7.2.10
        # Repport
        histogram = vars_map.get(Map.histogram)
        edited_histogram = vars_map.get('edited_histogram')
        rsi = vars_map.get(Map.rsi)
        macd = vars_map.get(Map.macd)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        histogram_list = vars_map.get('histogram_list')
=======
        signal = vars_map.get(Map.signal)
        keltner_low = vars_map.get('keltner_low')
>>>>>>> Icarus-v7.10
=======
        high = vars_map.get(Map.high)
        low = vars_map.get(Map.low)
        signal = vars_map.get(Map.signal)
        ema = vars_map.get(Map.ema)
        supertrend = vars_map.get(Map.supertrend)
        keltner_high = vars_map.get('keltner_high')
        keltner_low = vars_map.get('keltner_low')
>>>>>>> Icarus-v7.13
=======
        signal = vars_map.get(Map.signal)
        keltner_low = vars_map.get('keltner_low')
>>>>>>> Icarus-v7.2.10
        key = Icarus._can_buy_indicator.__name__
>>>>>>> Icarus-v6.4.1
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.ema_rising': ema_rising,
            f'{key}.rsi_rising': rsi_rising,
            f'{key}.supertrend_rising': supertrend_rising,
            f'{key}.supertrend_switch_up': supertrend_switch_up,
            f'{key}.psar_rising': psar_rising,
            f'{key}.psar_switch_up': psar_switch_up,
            f'{key}.macd_rising': macd_rising,
            f'{key}.macd_ok': macd_ok,
            f'{key}.histogram_ok': histogram_ok,
=======
            f'{key}.ema_rising': vars_map.get('ema_rising'),
            f'{key}.histogram_rising': vars_map.get('histogram_rising'),
<<<<<<< HEAD
            f'{key}.prev_histogram_dropping': vars_map.get('prev_histogram_dropping'),
=======
>>>>>>> Icarus-v7.2.10
            f'{key}.macd_switch_up': vars_map.get('macd_switch_up'),
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.rsi_ok': vars_map.get('rsi_ok'),
            f'{key}.rsi_trigger': vars_map.get('rsi_trigger'),
>>>>>>> Icarus-v6.1
            f'{key}.closes[-1]': closes[-1],
            f'{key}.closes[-2]': closes[-2],
            f'{key}.supertrend[-1]': supertrend[-1],
            f'{key}.supertrend[-2]': supertrend[-2],
            f'{key}.supertrend[-3]': supertrend[-3],
            f'{key}.psar[-1]': psar[-1],
            f'{key}.psar[-2]': psar[-2],
            f'{key}.psar[-3]': psar[-3],
            f'{key}.macd[-1]': macd[-1],
            f'{key}.macd[-2]': macd[-2],
            f'{key}.histogram[-1]': histogram[-1],
            f'{key}.histogram[-2]': histogram[-2],
            f'{key}.ema[-1]': ema[-1],
            f'{key}.ema[-2]': ema[-2],
            f'{key}._RSI_BUY_TRIGGER': cls._RSI_BUY_TRIGGER,
            f'{key}.rsi[-1]': rsi[-1],
            f'{key}.rsi[-2]': rsi[-2]
>>>>>>> Icarus-v5.12
=======
            f'{key}.histogram_rising': vars_map.get('histogram_rising'),
            f'{key}.delta_macd_rising': delta_macd_rising,
            f'{key}.minute_open_time': vars_map.get('minute_open_time'),
            f'{key}.stored_histogram': vars_map.get('stored_histogram'),
=======
            f'{key}.edited_histogram_rising': vars_map.get('edited_histogram_rising'),
            f'{key}.edited_prev_histogram_dropping': vars_map.get('edited_prev_histogram_dropping'),
            f'{key}.edited_macd_switch_up': vars_map.get('edited_macd_switch_up'),
            f'{key}.rsi_reached': vars_map.get('rsi_reached'),
            f'{key}.will_bounce': vars_map.get('will_bounce'),
            f'{key}.closes_above_low_keltner': vars_map.get('closes_above_low_keltner'),
            f'{key}.macd_peak_date': vars_map.get('macd_peak_date'),
            f'{key}.last_peak_macd': vars_map.get('last_peak_macd'),
<<<<<<< HEAD
>>>>>>> Icarus-v6.7
=======
            f'{key}.macd_switch_up': vars_map.get('macd_switch_up'),
            f'{key}.closes_above_low_keltner': vars_map.get('closes_above_low_keltner'),
=======
            f'{key}.macd_min_date': vars_map.get('macd_min_date'),
            f'{key}.last_min_macd': vars_map.get('last_min_macd'),
>>>>>>> Icarus-v7.2.10
            f'{key}.min_close_date': vars_map.get('min_close_date'),
            f'{key}.min_close': vars_map.get('min_close'),
            f'{key}.min_keltner_date': vars_map.get('min_keltner_date'),
            f'{key}.min_keltner': vars_map.get('min_keltner'),
<<<<<<< HEAD
>>>>>>> Icarus-v7.10
=======
            f'{key}.macd_bellow_bull_peak': vars_map.get('macd_bellow_bull_peak'),
            f'{key}.lows_above_low_keltner': vars_map.get('lows_above_low_keltner'),
            f'{key}.close_bellow_keltner': vars_map.get('close_bellow_keltner'),

            f'{key}.macd_bull_peak_iterval_start': vars_map.get('macd_bull_peak_iterval_start'),
            f'{key}.macd_bull_peak_iterval_end': vars_map.get('macd_bull_peak_iterval_end'),
            f'{key}.global_macd_bull_peak_date': vars_map.get('global_macd_bull_peak_date'),
            f'{key}.global_macd_bull_peak': vars_map.get('global_macd_bull_peak'),
            f'{key}.local_macd_bull_peak': vars_map.get('local_macd_bull_peak'),

            f'{key}.min_low_date': vars_map.get('min_low_date'),
            f'{key}.min_low': vars_map.get('min_low'),
            f'{key}.min_keltner_date': vars_map.get('min_keltner_date'),
            f'{key}.min_keltner': vars_map.get('min_keltner'),

>>>>>>> Icarus-v7.13
            f'{key}.closes[-1]': closes[-1],
            f'{key}.high[-1]': high[-1] if high is not None else None,
            f'{key}.low[-1]': low[-1] if low is not None else None,
=======
            f'{key}.closes[-1]': closes[-1],
            f'{key}.closes[-2]': closes[-2],
            f'{key}.closes[-3]': closes[-3],
>>>>>>> Icarus-v7.2.10
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
<<<<<<< HEAD
            f'{key}.macd[-2]': macd[-2] if macd is not None else None,
            f'{key}.macd[-3]': macd[-3] if macd is not None else None,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.histogram_list[-1]': histogram_list[-1] if len(histogram_list) >= 1 else None,
            f'{key}.histogram_list[-2]': histogram_list[-2] if len(histogram_list) >= 2 else None
>>>>>>> Icarus-v6.4.1
=======
            f'{key}.rsi[-1]': rsi[-1] if rsi is not None else None,
            f'{key}.rsi[-2]': rsi[-2] if rsi is not None else None,
            f'{key}.rsi[-3]': rsi[-3] if rsi is not None else None
>>>>>>> Icarus-v6.7.1
=======
=======
>>>>>>> Icarus-v7.2.10
            f'{key}.signal[-1]': signal[-1] if signal is not None else None,
            f'{key}.signal[-2]': signal[-2] if signal is not None else None,
            f'{key}.signal[-3]': signal[-3] if signal is not None else None,
            f'{key}.keltner_low[-1]': keltner_low[-1] if keltner_low is not None else None,
            f'{key}.keltner_low[-2]': keltner_low[-2] if keltner_low is not None else None,
            f'{key}.keltner_low[-3]': keltner_low[-3] if keltner_low is not None else None
<<<<<<< HEAD
>>>>>>> Icarus-v7.10
=======
            f'{key}.signal[-1]': signal[-1] if signal is not None else None,
            f'{key}.ema[-1]': ema[-1] if ema is not None else None,
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.keltner_high[-1]': keltner_high[-1] if keltner_high is not None else None,
            f'{key}.keltner_low[-1]': keltner_low[-1] if keltner_low is not None else None,
>>>>>>> Icarus-v7.13
=======
>>>>>>> Icarus-v7.2.10
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
=======
        period = Icarus.get_predictor_period()
        predictor = Predictor(pair, period)
        # High
        max_price_pred = Icarus._predict_max_high(predictor_marketprice, predictor)
        max_roi_pred = _MF.progress_rate(max_price_pred, close)
        max_roi_pred_ok = max_roi_pred >= Icarus.get_prediction_roi_high_trigger()
        # Low
        min_price_pred = Icarus._predict_min_low(predictor_marketprice, predictor)
        min_roi_pred = _MF.progress_rate(min_price_pred, close)
        min_roi_pred_ok = min_roi_pred >= Icarus.get_prediction_roi_low_trigger()
        # Check
        can_buy = max_roi_pred_ok and  min_roi_pred_ok
        return can_buy
>>>>>>> Icarus-v4.3.2
    
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
    
<<<<<<< HEAD
    @classmethod
    def predictor_market_price(cls, bkr: Broker, pair: Pair) -> MarketPrice:
        period = cls.get_predictor_period()
        n_period = cls.get_predictor_n_period()
        marketprice = cls._market_price(bkr, pair, period, n_period)
=======
    @staticmethod
    def _predict_min_low(predictor_marketprice: MarketPrice, predictor: Predictor) -> float:
        model = predictor.get_model(Predictor.LOW)
        n_feature = model.n_feature()
        lows = list(predictor_marketprice.get_lows())
        lows.reverse()
        xs, ys = Predictor.generate_dataset(lows, n_feature)
        lows_np = Predictor.market_price_to_np(predictor_marketprice, Predictor.LOW, n_feature)
        min_price_pred = model.predict(lows_np, fixe_offset=True, xs_offset=xs, ys_offset=ys)[-1,-1]
        return float(min_price_pred)
    
    @staticmethod
    def predictor_market_price(bkr: Broker, pair: Pair) -> MarketPrice:
        period = Icarus.get_predictor_period()
        n_period = Icarus.get_predictor_n_period()
        marketprice = Icarus._market_price(bkr, pair, period, n_period)
>>>>>>> Icarus-v4.3.2
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
<<<<<<< HEAD

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
        maker_fee_rate = fees.get(Map.maker)
        taker_fee_rate = fees.get(Map.taker)
        maker_fee_rate = fees.get(Map.maker)
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
<<<<<<< HEAD
        #
        big_market_params = market_params.copy()
        big_market_params[Map.period] = big_period
        #
        little_market_params = market_params.copy()
        little_market_params[Map.period] = little_period
        #
        min_market_params = market_params.copy()
        min_market_params[Map.period] = min_period
=======
        big_market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: big_period,
            'n_period': n_period
            }
        little_market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: little_period,
            'n_period': n_period
            }
        min_market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: min_period,
            'n_period': n_period
            }
<<<<<<< HEAD
>>>>>>> Icarus-v10.1.1
=======
>>>>>>> Icarus-v11.3.2
        broker.add_streams([
            broker.generate_stream(Map({Map.pair: pair, Map.period: period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: big_period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: little_period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: min_period})),
        ])
        i = 0
        Bot.update_trade_index(i)
        marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=True, **market_params)
        while isinstance(marketprice, MarketPrice):
            big_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **big_market_params)
            little_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **little_market_params)
            min_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **min_market_params)
<<<<<<< HEAD
<<<<<<< HEAD
            # Period
=======
>>>>>>> Icarus-v10.1.1
=======
>>>>>>> Icarus-v11.3.2
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
                    Map.roi: _MF.progress_rate(get_exec_price(min_marketprice, sell_type), trade['buy_price']) - taker_fee_rate,
                    Map.maximum: max_roi_position,
                    Map.buy: trade['buy_price'],
                    cls.MARKETPRICE_BUY_BIG_PERIOD: big_marketprice,
                    cls.MARKETPRICE_BUY_LITTLE_PERIOD: little_marketprice,
<<<<<<< HEAD
                    min_period: min_marketprice
=======
                    cls.get_min_period(): min_marketprice
>>>>>>> Icarus-v10.1.1
=======
    
        def can_sell_indicator(marketprice: MarketPrice, buy_time: int) ->  bool:
            def is_bollinger_reached(vars_map: Map) -> bool:
                bollinger = marketprice.get_bollingerbands()
                bollinger_high = list(bollinger.get(Map.high))
                bollinger_high.reverse()
                bollinger_low = list(bollinger.get(Map.low))
                bollinger_low.reverse()
                bollinger_reached = (closes[-1] >= bollinger_high[-1]) or (closes[-1] <= bollinger_low[-1])
                return bollinger_reached

            vars_map = Map()
            can_sell = False
            # Close
            closes = list(marketprice.get_closes())
            closes.reverse()
            # Check
            can_sell = is_bollinger_reached(vars_map)
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
>>>>>>> Icarus-v6.8
                }
            # Try buy/sell
            if not has_position:
<<<<<<< HEAD
                trade_id = f'{pair_merged}_{str_period}_{i}'
<<<<<<< HEAD
<<<<<<< HEAD
                can_buy, buy_repport = cls.can_buy(marketprice, big_marketprice, min_marketprice)
=======
                can_buy, buy_repport = cls.can_buy(marketprice, big_marketprice, little_marketprice, min_marketprice)
>>>>>>> Icarus-v11.3.2
=======
                can_buy, buy_repport = cls.can_buy(marketprice, min_marketprice)
>>>>>>> Icarus-v13.1.3
=======
                can_buy, buy_repport = cls.can_buy(marketprice, min_marketprice)
>>>>>>> Icarus-v13.1.4
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
                can_sell, sell_repport = cls._can_sell_indicator(marketprice, can_sell_params)
                sell_repport = {
                    Map.time: _MF.unix_to_date(min_marketprice.get_time()),
                    f'{Map.period}_{Map.time}': _MF.unix_to_date(open_times[-1]),
                    Map.id: trade_id,
                    **sell_repport
                }
                sell_repports.append(sell_repport)
<<<<<<< HEAD
                # Stop Limit Order
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                new_sell_stop_limit_price = sell_repport[Map.stopPrice]
                if new_sell_stop_limit_price is not None:
                    sell_stop_limit_price = None if 'sell_stop_limit_price' not in vars() else sell_stop_limit_price
                    sell_stop_limit_price = new_sell_stop_limit_price if (sell_stop_limit_price is None) or (new_sell_stop_limit_price > sell_stop_limit_price) else sell_stop_limit_price
                if can_sell and (min_lows[-1] <= sell_stop_limit_price):
                    # Prepare
                    sell_time = min_marketprice.get_time()
                    # exec_price = get_exec_price(min_marketprice, sell_type)
                    exec_price = sell_stop_limit_price
                    sell_stop_limit_price = None
=======
                def get_stop_limit_price(sell_repport: dict, old_sell_stop_limit_price: float, buy_price: float) -> float:
                    stop_limit_price = None
                    new_sell_stop_limit_price = sell_repport[Map.price]
                    if (old_sell_stop_limit_price is not None) and (new_sell_stop_limit_price is not None) and (new_sell_stop_limit_price > old_sell_stop_limit_price):
                        stop_limit_price = new_sell_stop_limit_price
                    elif old_sell_stop_limit_price is None:
                        stop_limit_price = buy_price * (1+cls._MAX_LOSS)
                    else:
                        stop_limit_price = old_sell_stop_limit_price
                    return stop_limit_price
                sell_stop_limit_price = None if 'sell_stop_limit_price' not in vars() else sell_stop_limit_price
                sell_stop_limit_price = get_stop_limit_price(sell_repport, sell_stop_limit_price, trade['buy_price'])
                stop_limit_reached = min_lows[-1] <= sell_stop_limit_price
                if can_sell or stop_limit_reached:
                    # Prepare
                    sell_time = min_marketprice.get_time()
=======
                def get_stop_limit_price(sell_repport: dict, old_sell_stop_limit_price: float) -> float:
                    stop_limit_price = None
                    new_sell_stop_limit_price = sell_repport[Map.price]
                    old_is_None = old_sell_stop_limit_price is None
                    new_is_None = new_sell_stop_limit_price is None
                    if (not old_is_None) and (not new_is_None) and (new_sell_stop_limit_price > old_sell_stop_limit_price):
                        stop_limit_price = new_sell_stop_limit_price
                    elif (old_is_None) and (not new_is_None):
                        stop_limit_price = new_sell_stop_limit_price
                    return stop_limit_price
                sell_stop_limit_price = None if 'sell_stop_limit_price' not in vars() else sell_stop_limit_price
                sell_stop_limit_price = get_stop_limit_price(sell_repport, sell_stop_limit_price)
                stop_limit_reached = (sell_stop_limit_price is not None) and (min_lows[-1] <= sell_stop_limit_price)
                if can_sell or stop_limit_reached:
                    # Prepare
                    sell_time = min_marketprice.get_time()
                    # exec_price = get_exec_price(min_marketprice, sell_type)
>>>>>>> Icarus-v13.4.1
=======
                sell_stop_limit_price = trade['buy_price'] * (1+cls._MAX_LOSS)
                stop_limit_reached = min_lows[-1] <= sell_stop_limit_price
                if can_sell or stop_limit_reached:
                    # Prepare
                    sell_time = min_marketprice.get_time()
                    # exec_price = get_exec_price(min_marketprice, sell_type)
>>>>>>> Icarus-v13.4.2.3
                    if can_sell and stop_limit_reached:
                        exec_price = max(sell_stop_limit_price, get_exec_price(min_marketprice, sell_type))
                    else:
                        exec_price = sell_stop_limit_price if stop_limit_reached else get_exec_price(min_marketprice, sell_type)
                    sell_stop_limit_price = None
<<<<<<< HEAD
<<<<<<< HEAD
                    stop_limit_fee = taker_fee_rate + maker_fee_rate
>>>>>>> Icarus-v13.3
=======
>>>>>>> Icarus-v13.4.1
=======
                    stop_limit_fees = taker_fee_rate + maker_fee_rate
>>>>>>> Icarus-v13.4.2.3
=======
                if can_sell:
                    # Prepare
                    sell_time = min_marketprice.get_time()
                    exec_price = get_exec_price(min_marketprice, sell_type)
>>>>>>> Icarus-v13.5.1.1.2.1
                    # Put
                    trade['sell_time'] = sell_time
                    trade['sell_date'] = _MF.unix_to_date(sell_time)
                    trade['sell_price'] = exec_price
                    sell_roi = (trade['sell_price']/trade['buy_price'] - 1)
                    trade[Map.roi] = (sell_roi - maker_fee_rate) if stop_limit_reached else (sell_roi - buy_sell_fee)
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
<<<<<<< HEAD
                    trade[Map.fee] = stop_limit_fee if stop_limit_reached else buy_sell_fee
=======
                    trade[Map.fee] = stop_limit_fees if stop_limit_reached else buy_sell_fee
>>>>>>> Icarus-v13.4.2.3
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
>>>>>>> Icarus-test

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Icarus(Map({
            Map.pair: Pair('@json/@json'),
            Map.maximum: None,
            Map.capital: 1,
            Map.rate: 1,
            Map.period: 0
        }))
        exec(MyJson.get_executable())
        return instance

<<<<<<< HEAD
    def save_move(self, market_price: MarketPrice) -> None:
        pair = self.get_pair()
=======
    def save_move(self, **agrs) -> None:
        args_map = Map(agrs)
        market_price = agrs['market_price']
        minute_marketprice = args_map.get('minute_marketprice')
        bkr = self.get_broker()
        # predictor_marketprice = agrs['predictor_marketprice']
        roi = self.get_wallet().get_roi(bkr)
>>>>>>> Icarus-v6.4.1
        has_position = self._has_position()
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        secure_odr = self._get_secure_order()
<<<<<<< HEAD
        roi_position = self.get_roi_position(market_price)
        max_roi = self.get_max_roi(market_price)
<<<<<<< HEAD
        roi_floor = self.get_roi_floor(market_price)
        floor_secure_order = self.get_floor_secure_order()
=======
        # roi_floor = self.get_roi_floor(market_price)
        # floor_secure_order = self.get_floor_secure_order()
        max_loss = self.get_max_loss()
        """
        can buy
        """
>>>>>>> Icarus-v2.1.2.2
        # Psar Rsi
        psar_rsis = list(market_price.get_psar_rsis())
        psar_rsis.reverse()
        # Supertrend
        supertrends = list(market_price.get_super_trend())
        supertrends.reverse()
        supertrends_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -2)
        supertrend_rising = supertrends_trend == MarketPrice.SUPERTREND_RISING
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        psar_trend = MarketPrice.get_psar_trend(closes, psars, -2)
        psar_rising = psar_trend == MarketPrice.PSAR_RISING
        # Keltner Buy
        klc = market_price.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_buy_ok = (closes[-3] < klc_highs[-3]) and (closes[-2] > klc_highs[-2]) and (closes[-1] > closes[-2])
        # Keltner Sell
        # klc = market_price.get_keltnerchannel()
        # klc_highs = list(klc.get(Map.high))
        # klc_highs.reverse()
        klc_sell_ok = closes[-1] <= klc_highs[-1]
        # MACD
        macd_map = market_price.get_macd()
        macds = list(macd_map.get(Map.macd))
        macds.reverse()
        signals = list(macd_map.get(Map.signal))
        signals.reverse()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        macd_ok = (macds[-2] > 0) and (signals[-2] > 0) and (histograms[-2] > 0)
=======
        roi_position = self.get_roi_position()
        max_roi = self.max_roi(market_price)
        max_price_id = self._get_max_price_id()
        max_price = self.get_max_price(market_price)
        max_loss = self.get_max_loss()
        """
        can buy
        """
        # Prediction
<<<<<<< HEAD
        buy_price = self.get_buy_order().get_execution_price() if has_position else None
>>>>>>> Icarus-v13.1.1
=======
        buy_price = self._get_orders().get_last_execution().get_execution_price() if has_position else None
        max_close_predicted = self.get_max_close_predicted()
        max_close_predicted = self._predict_max_high(predictor_marketprice, self.get_predictor()) if max_close_predicted is None else max_close_predicted
        max_roi_predicted = self.max_roi_predicted()
        real_max_roi_predicted = self.real_max_roi_predicted()
<<<<<<< HEAD
        prediction_filling_rate = self.get_prediction_filling_rate()
=======
        prediction_occupation_rate = self.get_prediction_occupation_rate()
        prediction_strigger = self.get_prediction_roi_high_trigger()
>>>>>>> Icarus-v4.3.2
        if max_roi_predicted is None:
            max_roi_predicted = _MF.progress_rate(max_close_predicted, closes[-1])
        max_close_predicted_list = self.get_max_close_predicted_list()
        max_roi_predicted_max = None
        max_roi_predicted_min = None
        n_prediction = len(max_close_predicted_list) if max_close_predicted_list is not None else -1
        if has_position and (n_prediction > 0):
            max_roi_predicted_max = _MF.progress_rate(max(max_close_predicted_list), buy_price.get_value())
            max_roi_predicted_min = _MF.progress_rate(min(max_close_predicted_list), buy_price.get_value())
<<<<<<< HEAD
>>>>>>> Icarus-v2.1.2.2
=======
        occup_trigger = self.get_prediction_occupation_secure_trigger()
        max_occupation = self.prediction_max_occupation(market_price) if has_position else None
        occup_reduce_rate = self.get_prediction_occupation_reduce()
        # Min prediction
        min_price_pred = self.get_min_price_predicted()
        min_price_predicted_id = self.get_min_price_predicted_id()
        min_roi_pred = None
        if has_position:
            min_roi_pred = _MF.rate_to_str(_MF.progress_rate(min_price_pred, buy_price.get_value()))
        elif min_price_pred is not None:
            min_roi_pred = _MF.rate_to_str(_MF.progress_rate(min_price_pred, closes[-1]))
>>>>>>> Icarus-v4.3.2
        # Map to print
        params_map = Map({
            'class': self.__class__.__name__,
            Map.pair: pair,
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            Map.time: _MF.unix_to_date(market_price.get_time()),
            Map.period: self.get_period(),
            Map.close: closes[-1],
            'closes[-2]': closes[-2],
            'closes[-3]': closes[-3],
<<<<<<< HEAD
=======
            'buy_price': buy_price,
            'max_close_predicted': max_close_predicted,
            'min_price_predicted_id': min_price_predicted_id,
            'min_price_predicted': min_price_pred,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'max_loss': _MF.rate_to_str(max_loss),
            # 'can_buy': self.can_buy(market_price) if not has_position else None,
            # 'can_sell': self.can_sell(market_price) if has_position else None,
>>>>>>> Icarus-v2.1.2.2
            'has_position': has_position,
<<<<<<< HEAD
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'can_buy': self.can_buy(market_price) if not has_position else None,
            'can_sell': self.can_sell(market_price) if has_position else None,
=======
            'can_buy': args_map.get('can_buy'),
            'can_sell': args_map.get('can_sell'),
            'indicator_buy': self._can_buy_indicator(market_price, minute_marketprice)[0] if not has_position else None,
            'indicator_sell': self._can_sell_indicator(market_price) if has_position else None,
>>>>>>> Icarus-v6.4.1
            Map.rsi: rsis[-1],
            'last_rsi': rsis[-2],
            'psar_rsis': psar_rsis[-1],
            'psar_rsis[-2]': psar_rsis[-2],
            'max_rsi': self.get_max_rsi(market_price),
            'max_loss': _MF.rate_to_str(self.get_max_loss()),
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(self.get_roi(market_price)),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
<<<<<<< HEAD
            'roi_floor': _MF.rate_to_str(roi_floor) if has_position else roi_floor,
            'floor_secure_order': _MF.rate_to_str(floor_secure_order) if has_position else floor_secure_order,
=======
            'max_roi_predicted': _MF.rate_to_str(max_roi_predicted) if max_roi_predicted is not None else max_roi_predicted,
            'min_roi_predicted': min_roi_pred,
            'max_roi_predicted_max': _MF.rate_to_str(max_roi_predicted_max) if max_roi_predicted_max is not None else max_roi_predicted_max,
            'max_roi_predicted_min': _MF.rate_to_str(max_roi_predicted_min) if max_roi_predicted_min is not None else max_roi_predicted_min,
            'n_prediction': n_prediction,
            'real_max_roi_predicted': _MF.rate_to_str(real_max_roi_predicted) if real_max_roi_predicted is not None else real_max_roi_predicted,
            'prediction_filling_rate': _MF.rate_to_str(prediction_filling_rate),
            # 'roi_floor': _MF.rate_to_str(roi_floor) if has_position else roi_floor,
            # 'floor_secure_order': _MF.rate_to_str(floor_secure_order) if has_position else floor_secure_order,
>>>>>>> Icarus-v2.1.2.2
            'CAN_BUY=>': '',
            'supertrend_rising': supertrend_rising,
            'psar_rising': psar_rising,
            'macd_ok': macd_ok,
            'klc_buy_ok': klc_buy_ok,
            'klc_sell_ok': klc_sell_ok,
            'supertrends[-1]': supertrends[-1],
            'supertrends[-2]': supertrends[-2],
            'psars[-1]': psars[-1],
            'psars[-2]': psars[-2],
            'klc_highs[-1]': klc_highs[-1],
            'klc_highs[-2]': klc_highs[-2],
            'klc_highs[-3]': klc_highs[-3],
            'macds[-1]': macds[-1],
            'macds[-2]': macds[-2],
            'signals[-1]': signals[-1],
            'signals[-2]': signals[-2],
            'histograms[-1]': histograms[-1],
<<<<<<< HEAD
            'histograms[-2]': histograms[-2]
=======
            'histograms[-2]': histograms[-2],
            'histograms[-3]': histograms[-3],
            'ema[-1]': ema[-1],
            'ema[-2]': ema[-2],
            'ema[-3]': ema[-3],
            **(args_map.get('repport') if args_map.get('repport') is not None else {})
>>>>>>> Icarus-v6.4.1
        })
        self._print_move(params_map)
