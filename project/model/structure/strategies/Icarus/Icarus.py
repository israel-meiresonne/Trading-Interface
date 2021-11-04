from typing import Tuple
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor
from model.tools.Price import Price


class Icarus(TraderClass):
    _MAX_LOSS = -3/100
    _ROI_FLOOR_FIXE = 0.002
    _PREDICTOR_PERIOD = 60 * 60
    _PREDICTOR_N_PERIOD = 1000
    _MIN_ROI_PREDICTED = 2/100
    _PREDICTION_OCCUPATION_RATE = 100/100
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 50/100
    _PREDICTION_OCCUPATION_REDUCE = 30/100

    def __init__(self, params: Map):
        super().__init__(params)
        self.__max_rsi = -1
        self.__max_roi = -1
        self.__floor_secure_order = None
        self.__predictor = None
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
        max_roi = self.get_max_roi(marketprice)
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
    # ——————————————————————————————————————————— FUNCTION MAX ROI DOWN ————————————————————————————————————————————————

    def _reset_max_roi(self) -> None:
        self.__max_roi = -1

    def _set_max_roi(self, new_max_roi: float) -> None:
        if not isinstance(new_max_roi, float):
            raise ValueError(f"max_roi must be float, instead '{new_max_roi}({type(new_max_roi)})'")
        max_roi = self.__max_roi
        self.__max_roi = new_max_roi if new_max_roi > max_roi else max_roi

    def get_max_roi(self, market_price: MarketPrice) -> float:
        """
        To get max roi for the current position taken
        """
        market_price.get_pair().are_same(self.get_pair())
        self._update_max_roi(market_price) if self._has_position() else None
        return self.__max_roi

    def _update_max_roi(self, market_price: MarketPrice) -> None:
        buy_unix = self.get_buy_unix()
        last_order = self._get_orders().get_last_execution()
        times = list(market_price.get_times())
        times.reverse()
        highs = list(market_price.get_highs())
        highs.reverse()
        if buy_unix in times:
            buy_time_idx = times.index(buy_unix)
            highs_since_buy = highs[buy_time_idx:]
            max_high = max(highs_since_buy)
            exec_price = last_order.get_execution_price()
            max_roi = max_high / exec_price - 1
            self._set_max_roi(max_roi)

    # ——————————————————————————————————————————— FUNCTION MAX ROI UP ——————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION ROI FLOOR DOWN ——————————————————————————————————————————————

    def get_roi_floor(self, market_price: MarketPrice) -> float:
        max_roi = self.get_max_roi(market_price)
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

    # ——————————————————————————————————————————— FUNCTION ROI FLOOR UP ————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SECURE ORDER DOWN ———————————————————————————————————————————

    def _secure_order_price(self, bkr: Broker, marketprice: MarketPrice) -> Price:
        pair = self.get_pair()
        # Get values
        buy_price = self._get_orders().get_last_execution().get_execution_price().get_value()
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
        return Price(secure_close, pair.get_right().get_symbol())

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

    def can_sell(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        # indicator
        indicator_ok = self._can_sell_indicator(marketprice)
        # Check
        can_sell = indicator_ok or self._can_sell_prediction(predictor_marketprice, marketprice)
        return can_sell
    
    def _can_sell_indicator(self, marketprice: MarketPrice) ->  bool:
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        # Psar
        supertrend = list(marketprice.get_super_trend())
        supertrend.reverse()
        supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -2)
        supertrend_dropping = supertrend_trend == MarketPrice.SUPERTREND_DROPPING
        return supertrend_dropping

    def _can_sell_prediction(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        def is_psar_dropping() -> bool:
            # Close
            closes = list(marketprice.get_closes())
            closes.reverse()
            # Psar
            psar = list(marketprice.get_psar())
            psar.reverse()
            psar_trend = MarketPrice.get_psar_trend(closes, psar, -2)
            var_psar_dropping = psar_trend == MarketPrice.PSAR_DROPPING
            return var_psar_dropping
        def is_prediction_reached() -> bool:
            max_roi = self.get_max_roi(marketprice)
            max_roi_pred = self.max_roi_predicted()
            return max_roi >= max_roi_pred
        def is_market_dropping() -> Tuple[bool, float]:
            close = marketprice.get_close()
            func_new_max_close_pred = get_new_max_close_pred()
            new_max_roi_pred = _MF.progress_rate(func_new_max_close_pred, close)
            func_market_dropping = new_max_roi_pred < self.get_min_roi_predicted()
            return func_market_dropping, func_new_max_close_pred
        def get_new_max_close_pred() -> float:
            predictor = self.get_predictor()
            return self._predict_max_high(predictor_marketprice, predictor)

        can_sell = False
        prediction_reached = is_prediction_reached()
        psar_dropping = is_psar_dropping()
        if prediction_reached or psar_dropping:
            market_dropping, new_max_close_pred = is_market_dropping()
            can_sell = (prediction_reached or psar_dropping) and market_dropping
            market_will_rise = prediction_reached and (not market_dropping)
            if can_sell or market_will_rise:
                 self._set_max_close_predicted(max_close_predicted=new_max_close_pred)
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
        self._reset_max_roi()
        self._reset_floor_secure_order()
        self._reset_max_close_predicted()
        # Evaluate Buy
        predictor_marketprice = self.predictor_market_price(bkr, self.get_pair())
        can_buy = self.can_buy(predictor_marketprice, market_price)
        if can_buy:
            self._set_max_close_predicted(predictor_marketprice=predictor_marketprice)
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
        def is_new_prediction(old_close: float, new_close) -> bool:
            return new_close > old_close
        def is_occupation_trigger_reached() -> bool:
            occup_trigger = self.get_prediction_occupation_secure_trigger()
            occupation = self.prediction_max_occupation(market_price)
            return occupation >= occup_trigger

        executions = Map()
        max_close_pred = self.get_max_close_predicted()
        # Evaluate Sell
        predictor_marketprice = self.predictor_market_price(bkr, self.get_pair())
        can_sell = self.can_sell(predictor_marketprice, market_price)
        if can_sell:
            self._sell(executions)
        else:
            new_max_close_pred = self.get_max_close_predicted()
            new_prediction = is_new_prediction(max_close_pred, new_max_close_pred)
            occup_trigger_reached = is_occupation_trigger_reached()
            if new_prediction and occup_trigger_reached:
                self._move_up_secure_order(executions)
            elif (self._get_secure_order() is None) and occup_trigger_reached:
                self._secure_position(executions)
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
    
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION CAN BUY DOWN —————————————————————————————————————————

    @staticmethod
    def stalker_can_add(market_price: MarketPrice) -> bool:
        # Close
        closes = list(market_price.get_closes())
        closes.reverse()
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        psar_trend = MarketPrice.get_psar_trend(closes, psars, -2)
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
        can_buy_indicator = False
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
        # Check
        supertrend_rising = now_supertrend_trend == MarketPrice.SUPERTREND_RISING
        supertrend_switch_up = supertrend_rising and (prev_supertrend_trend == MarketPrice.SUPERTREND_DROPPING)
        psar_switch_up = (now_psar_trend == MarketPrice.PSAR_RISING) and (prev_psar_trend == MarketPrice.PSAR_DROPPING)
        can_buy_indicator = (psar_switch_up and supertrend_rising) or supertrend_switch_up
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
            Map.capital: 1,
            Map.rate: 1,
            Map.period: 0
        }))
        exec(MyJson.get_executable())
        return instance

    def save_move(self, **agrs) -> None:
        market_price = agrs['market_price']
        predictor_marketprice = agrs['predictor_marketprice']
        # pair = self.get_pair()
        has_position = self._has_position()
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        secure_odr = self._get_secure_order()
        roi_position = self.get_roi_position(market_price)
        max_roi = self.get_max_roi(market_price)
        # roi_floor = self.get_roi_floor(market_price)
        # floor_secure_order = self.get_floor_secure_order()
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
        supertrends_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -2)
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
        # Prediction
        buy_price = self._get_orders().get_last_execution().get_execution_price() if has_position else None
        max_close_predicted = self.get_max_close_predicted()
        max_close_predicted = self._predict_max_high(predictor_marketprice, self.get_predictor()) if max_close_predicted is None else max_close_predicted
        max_roi_predicted = self.max_roi_predicted()
        real_max_roi_predicted = self.real_max_roi_predicted()
        prediction_occupation_rate = self.get_prediction_occupation_rate()
        prediction_strigger = self.get_min_roi_predicted()
        if max_roi_predicted is None:
            max_roi_predicted = _MF.progress_rate(max_close_predicted, closes[-1])
        max_close_predicted_list = self.get_max_close_predicted_list()
        max_roi_predicted_max = None
        max_roi_predicted_min = None
        n_prediction = len(max_close_predicted_list) if max_close_predicted_list is not None else -1
        if has_position and (n_prediction > 0):
            max_roi_predicted_max = _MF.progress_rate(max(max_close_predicted_list), buy_price.get_value())
            max_roi_predicted_min = _MF.progress_rate(min(max_close_predicted_list), buy_price.get_value())
        occup_trigger = self.get_prediction_occupation_secure_trigger()
        max_occupation = self.prediction_max_occupation(market_price) if has_position else None
        occup_reduce_rate = self.get_prediction_occupation_reduce()
        # Map to print
        params_map = Map({
            Map.time: _MF.unix_to_date(market_price.get_time()),
            Map.period: self.get_period(),
            Map.close: closes[-1],
            'closes[-2]': closes[-2],
            'closes[-3]': closes[-3],
            'buy_price': buy_price,
            'max_close_predicted': max_close_predicted,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'max_loss': _MF.rate_to_str(max_loss),
            'prediction_strigger': _MF.rate_to_str(prediction_strigger),
            'occup_trigger': _MF.rate_to_str(occup_trigger),
            'occup_reduce_rate': _MF.rate_to_str(occup_reduce_rate),
            'has_position': has_position,
            'indicator_buy': self._can_buy_indicator(market_price),
            'indicator_sell': self._can_sell_indicator(market_price),
            Map.rsi: rsis[-1],
            'rsis[-2]': rsis[-2],
            'rsis[-3]': rsis[-3],
            'psar_rsis': psar_rsis[-1],
            'psar_rsis[-2]': psar_rsis[-2],
            'psar_rsis[-3]': psar_rsis[-3],
            'max_rsi': self.get_max_rsi(market_price),
            # 'max_loss': _MF.rate_to_str(self.get_max_loss()),
            'max_occupation': _MF.rate_to_str(max_occupation) if has_position else None,
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(self.get_roi(market_price)),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
            'max_roi_predicted': _MF.rate_to_str(max_roi_predicted) if max_roi_predicted is not None else max_roi_predicted,
            'max_roi_predicted_max': _MF.rate_to_str(max_roi_predicted_max) if max_roi_predicted_max is not None else max_roi_predicted_max,
            'max_roi_predicted_min': _MF.rate_to_str(max_roi_predicted_min) if max_roi_predicted_min is not None else max_roi_predicted_min,
            'n_prediction': n_prediction,
            'real_max_roi_predicted': _MF.rate_to_str(real_max_roi_predicted) if real_max_roi_predicted is not None else real_max_roi_predicted,
            'prediction_occupation_rate': _MF.rate_to_str(prediction_occupation_rate),
            'supertrends[-1]': supertrends[-1],
            'supertrends[-2]': supertrends[-2],
            'supertrends[-2]': supertrends[-3],
            'psars[-1]': psars[-1],
            'psars[-2]': psars[-2],
            'psars[-2]': psars[-3],
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

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————