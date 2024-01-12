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
    # _RSI_BUY_TRIGGER = 25
    # _RSI_SELL_TRIGGER = 30
    # _RSI_STEP = 10
    _MAX_LOSS = -0.01
    _ROI_FLOOR_FIXE = 0.002
<<<<<<< HEAD
    # _ROI_STEP = 0.005
=======
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
    _PERIODS_REQUIRRED = [_MIN_PERIOD, MARKETPRICE_BUY_BIG_PERIOD]
    _MAX_FLOAT_DEFAULT = -1
    EMA200_N_PERIOD = 200
    EMA50_N_PERIOD = 50
    ROC_WINDOW = 15
    MACD_PARAMS_1 = {'slow': 100, 'fast': 46, 'signal': 35}
    CANDLE_CHANGE_N_CANDLE = 60
    _PREDICTIONS = None
    _FILE_PATH_BACKTEST = f'$class/backtest/$path/$session_backtest.csv'
>>>>>>> Icarus-test

    def __init__(self, params: Map):
        super().__init__(params)
        self.__max_rsi = -1
        self.__max_roi = -1
        self.__floor_secure_order = None

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
        secure_price = Price(secure_price_value, pair.get_right())
        return secure_price
>>>>>>> Icarus-test

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
            Map.maximum: self.get_max_price(marketprice),
            self.MARKETPRICE_BUY_BIG_PERIOD: self.get_marketprice(self.MARKETPRICE_BUY_BIG_PERIOD, n_period, broker),
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
        def get_marketprice(period: int) -> MarketPrice:
            return datas[period]

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

        def is_tangent_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_dropping = macd[-1] <= macd[-2]
            return tangent_macd_dropping

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

        def is_tangent_5min_macd_historgram_negative(vars_map: Map) -> bool:
            macd_map = marketprice_5min.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_5min_macd_historgram_negative = histogram[-1] <= histogram[-2]
            # Put
            vars_map.put(tangent_5min_macd_historgram_negative, 'tangent_5min_macd_historgram_negative')
            vars_map.put(histogram, 'histogram_5min')
            return tangent_5min_macd_historgram_negative

        vars_map = Map()
        can_sell = False
        # Vars
<<<<<<< HEAD
        # MarketPrice
=======
>>>>>>> Icarus-v10.1
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
        _1min_open_times = list(marketprice_1min.get_times())
        _1min_open_times.reverse()
        # MarketPrice Xmin
        marketprice_6h = get_marketprice(cls.MARKETPRICE_BUY_BIG_PERIOD)
        # Check
        can_sell = is_histogram_negative(vars_map)
=======
        open_times = list(marketprice.get_times())
        open_times.reverse()
        # Other periods
        marketprice_5min = datas[cls.MARKETPRICE_BUY_LITTLE_PERIOD]
        marketprice_6h = datas[cls.MARKETPRICE_BUY_BIG_PERIOD]
        # Check
        if have_bought_macd_in_positive(vars_map):
            can_sell = is_tangent_5min_macd_historgram_negative(vars_map)
        else:
            can_sell = (not is_buy_period(vars_map))\
                and (
                    is_histogram_dropping(vars_map)
                    )
>>>>>>> Icarus-v10.1
        # Repport
        macd = vars_map.get(Map.macd)
        histogram = vars_map.get(Map.histogram)
        histogram_5min = vars_map.get('histogram_5min')
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}._can_sell_indicator': can_sell,
<<<<<<< HEAD
            f'{key}.histogram_negative': vars_map.get('histogram_negative'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None
=======
            f'{key}.bought_macd_in_positive': vars_map.get('bought_macd_in_positive'),
            f'{key}.tangent_5min_macd_historgram_negative': vars_map.get('tangent_5min_macd_historgram_negative'),
            f'{key}.its_buy_period': vars_map.get('its_buy_period'),
            f'{key}.histogram_dropping': vars_map.get('histogram_dropping'),

            f'{key}.open_time': vars_map.get('open_time'),
            f'{key}.buy_time': vars_map.get('buy_time'),
            f'{key}.buy_period': vars_map.get('buy_period'),

            f'{key}.bought_macd_buy_time': vars_map.get('bought_macd_buy_time'),
            f'{key}.bought_macd_buy_period': vars_map.get('bought_macd_buy_period'),
            f'{key}.bought_macd': vars_map.get('bought_macd'),

            f'{key}.closes[-1]': closes[-1],
            f'{key}.macd[-1]': macd[-1] if macd is not None else None,
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram_5min[-1]': histogram_5min[-1] if histogram_5min is not None else None
>>>>>>> Icarus-v10.1
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
        # Evaluate Buy
        can_buy = self.can_buy(market_price)
=======
        self._reset_max_close_predicted()
        # Big
        big_period = Icarus.MARKETPRICE_BUY_BIG_PERIOD
        big_marketprice = self.get_marketprice(big_period)
        # min
        min_period = Icarus.get_min_period()
        min_marketprice = self.get_marketprice(min_period)
        # Check
        can_buy, buy_repport = self.can_buy(market_price, big_marketprice, min_marketprice)
>>>>>>> Icarus-test
        if can_buy:
            self._buy(executions)
            self._secure_position(executions)
        self.save_move(market_price)
        return executions

    def _try_sell(self, market_price: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param market_price: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        executions = Map()
        # Evaluate Sell
        can_sell = self.can_sell(market_price)
        if can_sell:
            self._sell(executions)
        elif self.get_roi_floor(market_price) != self.get_floor_secure_order():
            self._move_up_secure_order(executions)
        self.save_move(market_price)
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
    def get_rsi_sell_trigger() -> float:
        return Icarus._RSI_SELL_TRIGGER
    """

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
        psar_ok = psar_trend == MarketPrice.PSAR_RISING
        # Keltner
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
    def can_buy(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        indicator_ok, indicator_datas = cls._can_buy_indicator(child_marketprice, big_marketprice, min_marketprice)
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
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice, min_marketprice: MarketPrice) -> Tuple[bool, dict]:
        def is_histogram_switch_positive(vars_map: Map) -> bool:
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            histogram_switch_positive = (histogram[-1] > 0) and (histogram[-2] < 0)
            # Put
            vars_map.put(histogram_switch_positive, 'histogram_switch_positive')
            vars_map.put(histogram, Map.histogram)
            return histogram_switch_positive

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
        big_closes = list(big_marketprice.get_closes())
        big_closes.reverse()
        # Check
        can_buy_indicator = is_histogram_switch_positive(vars_map)
        # Repport
        histogram = vars_map.get(Map.histogram)
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.histogram_switch_positive': vars_map.get('histogram_switch_positive'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.opens[-1]': opens[-1],
            f'{key}.min_closes[-1]': min_closes[-1],
            f'{key}.min_opens[-1]': min_opens[-1],
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.histogram[-1]': histogram[-1] if histogram is not None else None,
            f'{key}.histogram[-2]': histogram[-2] if histogram is not None else None
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
        active_path = True
        pairs = MarketPrice.history_pairs(broker_name, active_path=active_path) if pairs is None else pairs
        file_path = cls.file_path_backtest_test()
        broker_name = broker.__class__.__name__
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
                can_buy, buy_repport = cls.can_buy(marketprice, big_marketprice, min_marketprice)
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

    def save_move(self, market_price: MarketPrice) -> None:
        pair = self.get_pair()
        has_position = self._has_position()
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        secure_odr = self._get_secure_order()
        roi_position = self.get_roi_position(market_price)
        max_roi = self.get_max_roi(market_price)
        roi_floor = self.get_roi_floor(market_price)
        floor_secure_order = self.get_floor_secure_order()
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
            'has_position': has_position,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'can_buy': self.can_buy(market_price) if not has_position else None,
            'can_sell': self.can_sell(market_price) if has_position else None,
            Map.rsi: rsis[-1],
            'last_rsi': rsis[-2],
            'psar_rsis': psar_rsis[-1],
            'psar_rsis[-2]': psar_rsis[-2],
            'max_rsi': self.get_max_rsi(market_price),
            'max_loss': _MF.rate_to_str(self.get_max_loss()),
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(self.get_roi(market_price)),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
            'roi_floor': _MF.rate_to_str(roi_floor) if has_position else roi_floor,
            'floor_secure_order': _MF.rate_to_str(floor_secure_order) if has_position else floor_secure_order,
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
            'histograms[-2]': histograms[-2]
        })
        self._print_move(params_map)
