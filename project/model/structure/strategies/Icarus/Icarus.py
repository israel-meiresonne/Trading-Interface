from typing import Tuple
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.TraderClass import TraderClass
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
    _PREDICTOR_PERIOD = 60 * 60
    _PREDICTOR_N_PERIOD = 1000
    _MIN_ROI_PREDICTED = 2/100
    _PREDICTION_OCCUPATION_RATE = 1
    _PREDICTION_OCCUPATION_SECURE_TRIGGER = 30/100
    _PREDICTION_OCCUPATION_REDUCE = 30/100
    _MIN_PERIOD = 60
    _PERIODS_REQUIRRED = [_MIN_PERIOD]
    _MAX_FLOAT_DEFAULT = -1

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
        pass
        '''
        # Get values
        pair = self.get_pair()
        buy_price = self._get_orders().get_last_execution().get_execution_price().get_value()
        if self._get_secure_order() is None:
            secure_price = TraderClass._secure_order_price(self, bkr, marketprice)
        else:
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
        return secure_price
        '''

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
    
    def _can_sell_roi(self) -> bool:
        roi_pos = self.get_roi_position()
        max_loss = self.get_max_loss()
        can_sell = roi_pos <= max_loss
        return can_sell
    
    def _can_sell_indicator(self, marketprice: MarketPrice) ->  bool:
        def is_supertrend_dropping() -> bool:
            supertrend = list(marketprice.get_super_trend())
            supertrend.reverse()
            supertrend_trend = MarketPrice.get_super_trend_trend(closes, supertrend, -2)
            return supertrend_trend == MarketPrice.SUPERTREND_DROPPING
        
        def is_psar_dropping() -> bool:
            psar = list(marketprice.get_psar())
            psar.reverse()
            psar_trend = MarketPrice.get_psar_trend(closes, psar, -2)
            return psar_trend == MarketPrice.PSAR_DROPPING
        
        def is_macd_dropping() -> bool:
            macd_ok = False
            period = self.get_period()
            buy_time = int(self.get_buy_order().get_execution_time() / 1000)
            buy_time_rounded = _MF.round_time(buy_time, period)
            next_open_time = buy_time_rounded + period
            open_time = marketprice.get_time()
            if open_time >= next_open_time:
                macd_map = marketprice.get_macd()
                macd = list(macd_map.get(Map.macd))
                macd.reverse()
                macd_ok = macd[-1] <= macd[-2]
            return macd_ok

        can_sell = False
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        # Check
        can_sell = is_macd_dropping() or is_psar_dropping() or is_supertrend_dropping()
        return can_sell

    def _can_sell_prediction(self, predictor_marketprice: MarketPrice, marketprice: MarketPrice) -> bool:
        def is_prediction_reached() -> bool:
            max_roi = self.max_roi(marketprice)
            max_roi_pred = self.max_roi_predicted()
            return max_roi >= max_roi_pred

        can_sell = is_prediction_reached()
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
        predictor_marketprice = self.get_marketprice(period=self.get_predictor_period())
        can_buy, _ = self.can_buy(predictor_marketprice, market_price)
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
        """
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
        """
        max_close_pred = self.get_max_close_predicted()
        old_max_price = self.get_max_prices()[-1]
        """
        # Evaluate Sell
        predictor_marketprice = self.get_marketprice(period=self.get_predictor_period())
        can_sell = self.can_sell(predictor_marketprice, market_price)
        if can_sell:
            self._sell(executions)
        """
        else:
            new_max_close_pred = self.get_max_close_predicted()
            new_prediction_higher = is_new_prediction_higher(max_close_pred, new_max_close_pred)
            occup_trigger_reached = is_occupation_trigger_reached()
            secure_is_max_loss = is_secure_is_max_loss()
            max_price_higher = is_max_price_higher(old_max_price, new_max_price=self.get_max_price(market_price))
            if new_prediction_higher and occup_trigger_reached:
                # Move up occupation secure if new prediction and occup trigger reached
                self._move_up_secure_order(executions)
            elif secure_is_max_loss and occup_trigger_reached:
                # Move up occupation secure
                self._move_up_secure_order(executions)
            elif occup_trigger_reached and max_price_higher:
                # Move up occupation secure
                self._move_up_secure_order(executions)
        """
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

    @staticmethod
    def stalker_can_add(market_price: MarketPrice) -> Tuple[bool, dict]:
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
        # Repport
        key_str = Icarus.stalker_can_add.__name__
        repport  = {
            f'{key_str}.psar_rising[-2]': psar_rising,
            f'{key_str}.closes[-1]': closes[-1],
            f'{key_str}.closes[-2]': closes[-2],
            f'{key_str}.psars[-1]': psars[-1],
            f'{key_str}.psars[-2]': psars[-2]
            }
        return can_add, repport

    @staticmethod
    def can_buy(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        pred_period = Icarus.get_predictor_period()
        if predictor_marketprice.get_period_time() != pred_period:
            predictor_period = Icarus.get_predictor_period()
            period = predictor_marketprice.get_period_time()
            raise ValueError(f"Predictor's MarketPrice must have period '{predictor_period}', instead '{period}'")
        # indicator
        indicator_ok, indicator_datas = Icarus._can_buy_indicator(child_marketprice)
        # Prediction
        pred_ok = False
        pred_repport = {}
        if indicator_ok:
            pred_ok, pred_repport = Icarus._can_buy_prediction(predictor_marketprice, child_marketprice)
        # Check
        can_buy = indicator_ok and pred_ok
        # Repport
        key = Icarus.can_buy.__name__
        repport = {
            f'{key}.indicator': indicator_ok,
            f'{key}.prediction': pred_ok,
            **indicator_datas,
            **pred_repport
        }
        return can_buy, repport

    @staticmethod
    def _can_buy_indicator(child_marketprice: MarketPrice) -> Tuple[bool, dict]:
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
        # Repport
        key = Icarus._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.supertrend_rising': supertrend_rising,
            f'{key}.supertrend_switch_up': supertrend_switch_up,
            f'{key}.psar_switch_up': psar_switch_up,
            f'{key}.closes[-1]': closes[-1],
            f'{key}.closes[-2]': closes[-2],
            f'{key}.supertrend[-1]': supertrend[-1],
            f'{key}.supertrend[-2]': supertrend[-2],
            f'{key}.supertrend[-3]': supertrend[-3],
            f'{key}.psar[-1]': psar[-1],
            f'{key}.psar[-2]': psar[-2],
            f'{key}.psar[-3]': psar[-3]
        }
        return can_buy_indicator, repport

    @staticmethod
    def _can_buy_prediction(predictor_marketprice: MarketPrice, child_marketprice: MarketPrice) -> Tuple[bool, dict]:
        close = child_marketprice.get_close()
        pair = child_marketprice.get_pair()
        pred_period = Icarus.get_predictor_period()
        predictor = Predictor(pair, pred_period)
        max_close_pred = Icarus._predict_max_high(predictor_marketprice, predictor)
        max_roi_pred = _MF.progress_rate(max_close_pred, close)
        pred_trigger = Icarus.get_min_roi_predicted()
        max_roi_ok = max_roi_pred >= pred_trigger
        # Repport
        key = Icarus._can_buy_prediction.__name__
        repport = {
            f'{key}.max_roi_ok': max_roi_ok,
            f'{key}.pred_period': pred_period,
            f'{key}.closes[-1]': close,
            f'{key}.max_close_pred': max_close_pred,
            f'{key}.max_roi_pred': max_roi_pred,
            f'{key}.pred_trigger': pred_trigger
        }
        return max_roi_ok, repport
    
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
            'max_price_id': max_price_id,
            'max_price': max_price,
            'max_close_predicted': max_close_predicted,
            'secure_odr_prc': secure_odr.get_limit_price() if secure_odr is not None else secure_odr,
            'max_loss': _MF.rate_to_str(max_loss),
            'prediction_strigger': _MF.rate_to_str(prediction_strigger),
            'occup_trigger': _MF.rate_to_str(occup_trigger),
            'occup_reduce_rate': _MF.rate_to_str(occup_reduce_rate),
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
            'max_occupation': _MF.rate_to_str(max_occupation) if has_position else None,
            'roi_position': _MF.rate_to_str(roi_position) if has_position else None,
            Map.roi: _MF.rate_to_str(roi),
            'max_roi': _MF.rate_to_str(max_roi) if has_position else max_roi,
            'max_roi_predicted': _MF.rate_to_str(max_roi_predicted) if max_roi_predicted is not None else max_roi_predicted,
            'max_roi_predicted_max': _MF.rate_to_str(max_roi_predicted_max) if max_roi_predicted_max is not None else max_roi_predicted_max,
            'max_roi_predicted_min': _MF.rate_to_str(max_roi_predicted_min) if max_roi_predicted_min is not None else max_roi_predicted_min,
            'n_prediction': n_prediction,
            'real_max_roi_predicted': _MF.rate_to_str(real_max_roi_predicted) if real_max_roi_predicted is not None else real_max_roi_predicted,
            'prediction_occupation_rate': _MF.rate_to_str(prediction_occupation_rate),
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
            'signals[-1]': signals[-1],
            'signals[-2]': signals[-2],
            'histograms[-1]': histograms[-1],
            'histograms[-2]': histograms[-2],
            "max_close_pred": args_map.get('max_close_pred'),
            "old_max_price": args_map.get('old_max_price'),
            "can_sell": args_map.get('can_sell'),
            "new_max_close_pred": args_map.get('new_max_close_pred'),
            "new_prediction_higher": args_map.get('new_prediction_higher'),
            "occup_trigger_reached": args_map.get('occup_trigger_reached'),
            "secure_is_max_loss": args_map.get('secure_is_max_loss'),
            "max_price_higher": args_map.get('max_price_higher')
        })
        self._print_move(params_map)

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
