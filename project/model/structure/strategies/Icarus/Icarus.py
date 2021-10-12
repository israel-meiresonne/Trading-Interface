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
    _MAX_LOSS = -0.03
    _ROI_FLOOR_FIXE = 0.002
    _PREDICTOR_PERIOD = 60 * 60
    _PREDICTOR_N_PERIOD = 100
    _MIN_ROI_PREDICTED = 1/100

    def __init__(self, params: Map):
        super().__init__(params)
        self.__max_rsi = -1
        self.__max_roi = -1
        self.__floor_secure_order = None
        self.__predictor = None
        self.__max_close_predicted = None
    
    def get_predictor(self) -> Predictor:
        if self.__predictor is None:
            period = self.get_predictor_period()
            self.__predictor = Predictor(self.get_pair(), period)
        return self.__predictor

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

    def _new_secure_order(self, bkr: Broker, mkt_prc: MarketPrice) -> Order:
        if not self._has_position():
            raise Exception("Strategy must have position to generate secure Order")
        _bkr_cls = bkr.__class__.__name__
        pair = self.get_pair()
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

    def get_buy_unix(self) -> int:
        if not self._has_position():
            raise Exception("Strategy must have position to get buy unix time")
        last_order = self._get_orders().get_last_execution()
        exec_time = int(last_order.get_execution_time() / 1000)
        period = self.get_period()
        buy_unix = int(_MF.round_time(exec_time, period))
        return buy_unix

    def can_sell(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        # indicator
        indicator_ok = self._can_sell_indicator(marketprice)
        # Predictor
        max_roi_ok = self._can_sell_prediction(predictor_marketprice, marketprice)
        # Check
        can_sell = indicator_ok or max_roi_ok
        return can_sell
    
    def _can_sell_indicator(self, market_price: MarketPrice) ->  bool:
        # Close
        closes = list(market_price.get_closes())
        closes.reverse()
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        # Check
        prev_psar_trend_1 = MarketPrice.get_psar_trend(closes, psars, -2)
        can_sell = prev_psar_trend_1 == MarketPrice.PSAR_DROPPING
        return can_sell
    
    def _can_sell_prediction(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        market_dropping = False
        max_roi = self.get_max_roi(marketprice)
        max_roi_pred = self.max_roi_predicted()
        if max_roi >= max_roi_pred:
            predictor = self.get_predictor()
            close = marketprice.get_close()
            new_max_close_pred = self._predict_max_high(predictor_marketprice, predictor)
            new_max_roi_pred = _MF.progress_rate(new_max_close_pred, close)
            market_dropping = new_max_roi_pred < self.get_min_roi_predicted()
            self._update_max_close_predicted(new_max_close_pred) if not market_dropping else None
        return market_dropping
    
    def _reset_max_close_predicted(self) -> None:
        self.__max_close_predicted = None
    
    def _set_max_close_predicted(self, predictor_marketprice: MarketPrice = None) -> None:
        predictor = self.get_predictor()
        self.__max_close_predicted = self._predict_max_high(predictor_marketprice, predictor)
    
    def _update_max_close_predicted(self, max_close_predicted: float) -> None:
        self.__max_close_predicted = max_close_predicted
    
    def get_max_close_predicted(self) -> float:
        return self.__max_close_predicted
    
    def max_roi_predicted(self) -> float:
        max_roi_predicted = None
        if self._has_position():
            last_order = self._get_orders().get_last_execution()
            exec_price = last_order.get_execution_price()
            max_close_predicted = self.get_max_close_predicted()
            _MF.progress_rate(max_close_predicted, exec_price)
        return max_roi_predicted

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
            self._set_max_close_predicted(predictor_marketprice)
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
        # Evaluate Sell
        predictor_marketprice = self.predictor_market_price(bkr, self.get_pair())
        can_sell = self.can_sell(predictor_marketprice, market_price)
        if can_sell:
            self._sell(executions)
        # Save
        var_param = vars().copy()
        del var_param['self']
        self.save_move(**var_param)
        return executions

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
        klc_ok = (closes[-2] > klc_highs[-2])   # and (closes[-1] > closes[-2])
        # MACD
        macd_map = market_price.get_macd()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        macd_ok = histograms[-2] > 0
        # Check
        can_add = supertrend_ok and psar_ok and klc_ok and macd_ok
        return can_add

    @staticmethod
    def can_buy(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> bool:
        if predictor_marketprice.get_period_time() != Icarus.get_predictor_period():
            predictor_period = Icarus.get_predictor_period()
            period = predictor_marketprice.get_period_time()
            raise ValueError(f"Predictor's MarketPrice must have period '{predictor_period}', instead '{period}'")
        # indicator
        indicator_ok = Icarus._can_buy_indicator(child_marketprice)
        # Predictor
        max_roi_ok = Icarus._can_buy_prediction(predictor_marketprice, child_marketprice)
        # Check
        can_buy = indicator_ok and max_roi_ok
        return can_buy

    @staticmethod
    def _can_buy_indicator(child_marketprice: MarketPrice) -> bool:
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        # Supertrend
        supertrends = list(child_marketprice.get_super_trend())
        supertrends.reverse()
        supertrends_trend = MarketPrice.get_super_trend_trend(closes, supertrends, -2)
        supertrend_ok = supertrends_trend == MarketPrice.SUPERTREND_RISING
        # Psar
        psars = list(child_marketprice.get_psar())
        psars.reverse()
        prev_psar_trend_1 = MarketPrice.get_psar_trend(closes, psars, -2)
        prev_psar_trend_2 = MarketPrice.get_psar_trend(closes, psars, -3)
        psar_ok = (prev_psar_trend_1 == MarketPrice.PSAR_RISING) and (prev_psar_trend_2 == MarketPrice.PSAR_DROPPING)
        # Keltner
        klc = child_marketprice.get_keltnerchannel()
        klc_highs = list(klc.get(Map.high))
        klc_highs.reverse()
        klc_ok = (closes[-2] > klc_highs[-2])   # and (closes[-1] > closes[-2])
        # MACD
        macd_map = child_marketprice.get_macd()
        histograms = list(macd_map.get(Map.histogram))
        histograms.reverse()
        macd_ok = histograms[-2] > 0
        # Check
        can_buy = supertrend_ok and psar_ok and klc_ok and macd_ok
        return can_buy

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
    
    @staticmethod
    def _predict_max_high(predictor_marketprice: MarketPrice, predictor: Predictor) -> float:
        # pair = predictor.get_pair()
        # period = predictor.get_period()
        # n_period = Icarus.get_predictor_n_period()
        # marketprice = Icarus._market_price(bkr, pair, period, n_period)
        n_feature = predictor.get_model(Predictor.HIGH).n_feature()
        highs_np = Predictor.market_price_to_np(predictor_marketprice, Predictor.HIGH, n_feature)
        max_close_pred = predictor.predict(highs_np, Predictor.HIGH)[-1,-1]
        return float(max_close_pred)
    
    @staticmethod
    def predictor_market_price(bkr: Broker, pair: Pair) -> MarketPrice:
        period = Icarus.get_predictor_period()
        n_period = Icarus.get_predictor_n_period()
        marketprice = Icarus._market_price(bkr, pair, period, n_period)
        return marketprice

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
        roi_floor = self.get_roi_floor(market_price)
        floor_secure_order = self.get_floor_secure_order()
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
        supertrend_rising = supertrends_trend == MarketPrice.SUPERTREND_RISING
        # Psar
        psars = list(market_price.get_psar())
        psars.reverse()
        prev_psar_trend_1 = MarketPrice.get_psar_trend(closes, psars, -2)
        prev_psar_trend_2 = MarketPrice.get_psar_trend(closes, psars, -3)
        psar_buy_ok = (prev_psar_trend_1 == MarketPrice.PSAR_RISING) and (prev_psar_trend_2 == MarketPrice.PSAR_DROPPING)
        psar_sell_ok = prev_psar_trend_1 == MarketPrice.PSAR_DROPPING
        # Keltner Buy
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
        macd_histogram_positive = histograms[-2] > 0
        # Prediction
        buy_price = self._get_orders().get_last_execution().get_execution_price() if has_position else None
        max_close_predicted = self.get_max_close_predicted()
        max_close_predicted = self._predict_max_high(predictor_marketprice, self.get_predictor()) if max_close_predicted is None else max_close_predicted
        max_roi_predicted = self.max_roi_predicted()
        if max_roi_predicted is None:
            max_roi_predicted = _MF.progress_rate(max_close_predicted, closes[-1])
        # Map to print
        params_map = Map({
            Map.time: _MF.unix_to_date(market_price.get_time()),
            Map.period: self.get_period(),
            Map.close: closes[-1],
            'closes[-2]': closes[-2],
            'closes[-3]': closes[-3],
            'has_position': has_position,
            'buy_price': buy_price,
            'max_close_predicted': max_close_predicted,
            # 'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            # 'can_buy': self.can_buy(market_price) if not has_position else None,
            # 'can_sell': self.can_sell(market_price) if has_position else None,
            Map.rsi: rsis[-1],
            'last_rsi': rsis[-2],
            'psar_rsis': psar_rsis[-1],
            'psar_rsis[-2]': psar_rsis[-2],
            'max_rsi': self.get_max_rsi(market_price),
            # 'max_loss': _MF.rate_to_str(self.get_max_loss()),
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(self.get_roi(market_price)),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
            'max_roi_predicted': _MF.rate_to_str(max_roi_predicted) if max_roi_predicted is not None else max_roi_predicted,
            # 'roi_floor': _MF.rate_to_str(roi_floor) if has_position else roi_floor,
            # 'floor_secure_order': _MF.rate_to_str(floor_secure_order) if has_position else floor_secure_order,
            'CAN_BUY=>': '',
            'supertrend_rising': supertrend_rising,
            'psar_buy_ok': psar_buy_ok,
            'psar_sell_ok': psar_sell_ok,
            'macd_histogram_positive': macd_histogram_positive,
            'klc_ok': klc_ok,
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