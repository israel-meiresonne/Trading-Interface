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
from model.tools.Price import Price


class Icarus(TraderClass):
    # _RSI_BUY_TRIGGER = 25
    # _RSI_SELL_TRIGGER = 30
    # _RSI_STEP = 10
    _MAX_LOSS = -0.01
    _ROI_FLOOR_FIXE = 0.002
    # _ROI_STEP = 0.005

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
        period = self.get_best_period()
        buy_unix = int(_MF.round_time(exec_time, period))
        return buy_unix

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
        # Evaluate Buy
        can_buy = self.can_buy(market_price)
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
            Map.period: self.get_best_period(),
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
        fields = params_map.get_keys()
        rows = [{k: (params_map.get(k) if params_map.get(k) is not None else '—') for k in fields}]
        overwrite = False
        path = Config.get(Config.DIR_SAVE_MOVES)
        path = path.replace('$pair', pair.__str__().replace('/', '_').upper())
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)
