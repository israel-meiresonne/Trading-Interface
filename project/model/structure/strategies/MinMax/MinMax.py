from typing import Union

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Price import Price


class MinMax(Strategy):
    _CONF_MAKET_PRICE = "config_market_price"
    _CONF_MAX_DR = "CONF_MAX_DR"

    def __init__(self, prms: Map):
        super().__init__(prms)
        self.__configs = None
        self.__secure_order = None
        self._last_dropping_super = None
        self._last_dropping_close = None

    def _init_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            # _stage = Config.get(Config.STAGE_MODE)
            # bkr_cls = bkr.__class__.__name__
            # bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
            # Set Configs
            self._init_constants(bkr)
            # Set Capital
            self._init_capital(bkr)

    def _init_capital(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        # bkr_cls = bkr.__class__.__name__
        # bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
        cap = None
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            cap = Price(1000, self.get_pair().get_right().get_symbol())
        elif _stage == Config.STAGE_3:
            """
            snap_rq_prms = Map({
                Map.account: BrokerRequest.ACCOUNT_MAIN,
                Map.begin_time: None,
                Map.end_time: self.get_timestamp(self.TIME_MILLISEC),
                Map.number: 5,
                Map.timeout: None,
            })
            exec(f"from model.API.brokers.{bkr_cls}.{bkr_rq_cls} import {bkr_rq_cls}")
            snap_rq = eval(bkr_rq_cls+f"('{BrokerRequest.RQ_ACCOUNT_SNAP}', snap_rq_prms)")
            bkr.get_account_snapshot(snap_rq)
            accounts = snap_rq.get_account_snapshot()
            right = self.get_pair().get_right()
            times = list(accounts.get(Map.account).keys())
            cap = accounts.get(Map.account, times[-1], right.get_symbol())
            """
            pass
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
            # Raise error if set capital is bellow Broker's minimum trade amount
        self._set_capital(cap) if cap is not None else None

    def _init_constants(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        bkr_cls = bkr.__class__.__name__
        bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
        # Prepare Set Configs
        mkt_rq_prms = Map({
            Map.pair: self.get_pair(),
            Map.period: 60,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 1
        })
        exec(f"from model.API.brokers.{bkr_cls}.{bkr_rq_cls} import {bkr_rq_cls}")
        bkr_rq = eval(bkr_rq_cls + f"('{BrokerRequest.RQ_MARKET_PRICE}', mkt_rq_prms)")
        bkr.get_market_price(bkr_rq)
        mkt_prc = bkr_rq.get_market_price()
        self.__configs = Map({
            self._CONF_MAKET_PRICE: Map({
                Map.pair: self.get_pair(),
                Map.period: 60,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 100
            }),
            self._CONF_MAX_DR: -0.05,
        })

    def __get_constants(self) -> Map:
        return self.__configs

    def _get_constant(self, k) -> [float, Map]:
        configs = self.__get_constants()
        if k not in configs.get_keys():
            raise IndexError(f"There's  not constant with this key '{k}'")
        return configs.get(k)

    def _set_secure_order(self, odr: Order) -> None:
        self.__secure_order = odr

    def _get_secure_order(self) -> Order:
        return self.__secure_order

    def _get_buy_capital(self) -> Price:
        """
        To get the capital available to make a buy Order\n
        :return: the capital available to make a buy Order
        :Note : the capital is in right asset of Strategy's pair
        """
        init_cap = self._get_capital()
        odrs = self._get_orders()
        b_cpt = init_cap.get_value()
        if odrs.get_size() > 0:
            odrs_sum = odrs.get_sum()
            b_cpt += odrs_sum.get(Map.right).get_value()
        r_sbl = self.get_pair().get_right().get_symbol()
        return Price(b_cpt, r_sbl)

    def _get_sell_quantity(self) -> Price:
        """
        To get the capital available to make a sell Order\n
        :return: the capital available to make a sell Order
        :Note : the capital is in left asset of Strategy's pair
        """
        odrs = self._get_orders()
        s_qty = 0
        if odrs.get_size() > 0:
            odr_sum = odrs.get_sum()
            s_qty += odr_sum.get(Map.left).get_value()
        l_sbl = self.get_pair().get_left().get_symbol()
        return Price(s_qty, l_sbl)

    def _has_position(self) -> bool:
        """
        Check if holding a left position\n
        :return: True if holding else False
        """
        odrs = self._get_orders()
        """
        ks = odrs.get_keys()
        ks.reverse()
        for k in ks:
            odr = odrs.get(k)
            if odr.get_status() == Order.STATUS_COMPLETED:
                has_pos = odr.get_move() == Order.MOVE_BUY
                break
        """
        return odrs.has_position()

    def _get_market_price(self, bkr: Broker) -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        bkr_cls = bkr.__class__.__name__
        rq_cls = BrokerRequest.get_request_class(bkr_cls)
        mkt_prms = self._get_constant(self._CONF_MAKET_PRICE)
        exec(f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}")
        rq_mkt = eval(rq_cls + "('" + BrokerRequest.RQ_MARKET_PRICE + "', mkt_prms)")
        bkr.get_market_price(rq_mkt)
        return rq_mkt.get_market_price()

    def _new_buy_order(self, bkr: Broker) -> Order:
        bkr_cls = bkr.__class__.__name__
        odr_cls = bkr_cls + Order.__name__
        pr = self.get_pair()
        pr_right = pr.get_right()
        b_cpt = self._get_buy_capital()
        odr_prms_map = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(b_cpt.get_value(), pr_right.get_symbol())
        })
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(odr_cls + "('" + Order.TYPE_MARKET + "', odr_prms_map)")
        self._add_order(odr)
        return odr

    def _new_sell_order(self, bkr: Broker) -> Order:
        bkr_cls = bkr.__class__.__name__
        odr_cls = bkr_cls + Order.__name__
        pr = self.get_pair()
        pr_left = pr.get_left()
        s_cpt = self._get_sell_quantity()
        odr_prms = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.quantity: Price(s_cpt.get_value(), pr_left.get_symbol())
        })
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls + "Order('" + Order.TYPE_MARKET + "', odr_prms)")
        self._add_order(odr)
        return odr

    def _new_secure_order(self, bkr: Broker, mkt_prc: MarketPrice) -> Order:
        bkr_cls = bkr.__class__.__name__
        odr_cls = bkr_cls + Order.__name__
        pr = self.get_pair()
        if self._has_position():
            sum_odr = self._get_orders().get_sum()
            qty = sum_odr.get(Map.left)
        else:
            close_val = mkt_prc.get_close()
            b_cap = self._get_buy_capital()
            qty_val = b_cap.get_value() / close_val
            qty = Price(qty_val, pr.get_left().get_symbol())
        # qty = sum_odr.get(Map.left)
        stop = mkt_prc.get_futur_price(self._get_constant(self._CONF_MAX_DR))
        odr_prms = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pr.get_right().get_symbol()),
            Map.quantity: qty
        })
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls + "Order('" + Order.TYPE_STOP + "', odr_prms)")
        self._add_order(odr)
        self._set_secure_order(odr)
        return odr

    def trade(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        self._init_strategy(bkr)
        mkt_prc = self._get_market_price(bkr)
        self._update_orders(bkr, mkt_prc)
        # Save
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        #
        if self._has_position():
            odrs_map = self._try_sell(bkr, mkt_prc)
        else:
            odrs_map = self._try_buy(bkr, mkt_prc)
        bkr.execute(odrs_map) if len(odrs_map.get_map()) > 0 else None

    # TREND(RSI)&TREND(CLOSE)V5.0: BUY
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        # Close Trend
        close = mkt_prc.get_close()
        closes_trends = mkt_prc.get_super_trend()
        close_trend_ok = (close > closes_trends[0]) or ((close < closes_trends[1]) and (close == closes_trends[0]))
        # RSI Trend
        rsi = mkt_prc.get_rsi()
        rsis_trends = mkt_prc.get_super_trend_rsis()
        rsis_trend = rsis_trends[0]
        last_rsis_trend = rsis_trends[1]
        rsi_trend_ok = (rsi > rsis_trend) or ((rsi < last_rsis_trend) and (rsi == rsis_trend))
        # Checking
        if close_trend_ok and rsi_trend_ok:
            self._buy(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_BUY)  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        """
        fields = [
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            # Buy
            'super_trend',
            'close_trend_ok',
            'rsi',
            'rsis_trend',
            'rsi_trend_ok',
            'rsis_trends',
            'closes_trends',
            # Lists
            'market_json',
            'rsis',
            'super_trends'
        ]
        """
        return odrs
    '''

    # TREND(RSI)&TREND(CLOSE)V5.1: BUY
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        closes = list(mkt_prc.get_closes())
        closes.reverse()
        closes_supers = list(mkt_prc.get_super_trend())
        closes_supers.reverse()
        # Close Trend
        close_trend = MarketPrice.get_super_trend_trend(closes, closes_supers, -1)
        close_trend_ok = close_trend == MarketPrice.SUPERTREND_RISING
        """
        # RSI Trend
        rsi = mkt_prc.get_rsi()
        rsis_trends = mkt_prc.get_super_trend_rsis()
        rsis_trend = rsis_trends[0]
        last_rsis_trend = rsis_trends[1]
        rsi_trend_ok = (rsi > rsis_trend) or ((rsi < last_rsis_trend) and (rsi == rsis_trend))
        """
        # Switch Point
        if (close_trend == MarketPrice.SUPERTREND_RISING) and (self._last_dropping_super is None):
            switchers = MarketPrice.get_super_trend_switchers(closes, closes_supers)
            trend_first_idx = switchers.get_keys()[-1] if close_trend_ok else None
            last_trend_idx = (trend_first_idx - 1) if trend_first_idx is not None else None
            self._last_dropping_super = closes_supers[last_trend_idx] if last_trend_idx is not None else None
            # self._last_dropping_super = closes[last_trend_idx] if last_trend_idx is not None else None
        if (close_trend == MarketPrice.SUPERTREND_DROPING) and (self._last_dropping_super is not None):
            self._last_dropping_super = None
        super_trend = closes_supers[-1]
        # super_trend = closes[-1]
        is_above_switch = super_trend >= self._last_dropping_super if self._last_dropping_super is not None else False
        # Peak
        maxs = mkt_prc.get_maximums()
        close_idx = 1
        last_is_peak = close_idx in maxs
        # Checking
        if close_trend_ok and is_above_switch and last_is_peak:
            self._buy(bkr, mkt_prc, odrs)
            self._last_dropping_super = None
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_BUY, _last_dropping_super=self._last_dropping_super)  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        """
        fields = [
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            # Buy
            'close_trend_ok',
            'is_above_switch',
            'last_is_peak',
            '_last_dropping_super',
            'super_trend',
            'trend_first_idx',
            'last_trend_idx',
            # Lists
            'switchers',
            'maxs',
            'market_json',
            'rsis',
            'super_trends'
        ]
        """
        return odrs
    '''

    # TREND(RSI)&TREND(CLOSE)V5.2: BUY
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        closes = list(mkt_prc.get_closes())
        closes.reverse()
        closes_supers = list(mkt_prc.get_super_trend())
        closes_supers.reverse()
        # Close Trend
        close_trend = MarketPrice.get_super_trend_trend(closes, closes_supers, -1)
        close_trend_ok = close_trend == MarketPrice.SUPERTREND_RISING
        # Switch Point
        if close_trend_ok and (self._last_dropping_close is None):
            switchers = MarketPrice.get_super_trend_switchers(closes, closes_supers)
            trend_first_idx = switchers.get_keys()[-1] if close_trend_ok else None
            last_trend_idx = (trend_first_idx - 1) if trend_first_idx is not None else None
            self._last_dropping_close = closes[last_trend_idx] if last_trend_idx is not None else None
        super_trend = closes_supers[-1]
        is_above_switch = super_trend >= self._last_dropping_close if self._last_dropping_close is not None else False
        # Peak
        maxs = mkt_prc.get_maximums()
        close_idx = 1
        last_is_peak = close_idx in maxs
        # Checking
        if close_trend_ok and is_above_switch and last_is_peak:
            self._buy(bkr, mkt_prc, odrs)
            self._last_dropping_close = None
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_BUY, _last_dropping_close=self._last_dropping_close) # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        """
        fields = [
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            # Buy
            'close_trend_ok',
            'is_above_switch',
            'last_is_peak',
            '_last_dropping_close',
            'super_trend',
            'trend_first_idx',
            'last_trend_idx',
            # Lists
            'switchers',
            'maxs',
            'market_json',
            'rsis',
            'super_trends'
        ]
        """
        return odrs
    '''

    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        odrs = Map()
        self._buy(bkr, mkt_prc, odrs)
        return odrs

    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        odrs = Map()
        self._move_up_secure_order(bkr, mkt_prc, odrs)
        self._sell(bkr, odrs)
        return odrs

    def _buy(self, bkr: Broker, mkt_prc: MarketPrice, odrs: Map) -> None:
        # buy order
        b_odr = self._new_buy_order(bkr)
        odrs.put(b_odr, len(odrs.get_map()))
        # secure order
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs.put(scr_odr, len(odrs.get_map()))

    # ——————————————————————— BUY UP ————————————————————————————————————————————
    # ——————————————————————— SELL DOWN —————————————————————————————————————————

    # TREND(RSI)&TREND(CLOSE)V5.0: SELL
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        _vars_before = dict(vars())
        odrs = Map()
        # Close Trend
        close = mkt_prc.get_close()
        closes_trends = mkt_prc.get_super_trend()
        close_trend_ok = (close < closes_trends[0]) or ((close > closes_trends[1]) and (close == closes_trends[0]))
        # RSI Trend
        rsi = mkt_prc.get_rsi()
        rsis_trends = mkt_prc.get_super_trend_rsis()
        rsis_trend = rsis_trends[0]
        last_rsis_trend = rsis_trends[1]
        rsi_trend_ok = (rsi < rsis_trend) or ((rsi > last_rsis_trend) and (rsi == rsis_trend))
        # Secure Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_constant(self._CONF_MAX_DR))          # ❌
        # CHECK
        if rsi_trend_ok or close_trend_ok:
            self._sell(bkr, odrs)
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL)  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # TREND(RSI)&TREND(CLOSE)V5.1,V5.2: SELL
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        odrs = Map()
        # Close Trend
        close = mkt_prc.get_close()
        closes_supers = mkt_prc.get_super_trend()
        close_trend_ok = (close < closes_supers[0]) or ((close > closes_supers[1]) and (close == closes_supers[0]))
        # Secure Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_constant(self._CONF_MAX_DR))
        # CHECK
        if close_trend_ok:
            self._sell(bkr, odrs)
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL)  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    def _sell(self, bkr: Broker, odrs: Map) -> None:
        old_scr_odr = self._get_secure_order()
        bkr.cancel(old_scr_odr) if old_scr_odr.get_status() != Order.STATUS_COMPLETED else None
        s_odr = self._new_sell_order(bkr)
        odrs.put(s_odr, len(odrs.get_map()))

    def _move_up_secure_order(self, bkr: Broker, mkt_prc: MarketPrice, odrs: Map) -> None:
        old_scr_odr = self._get_secure_order()
        bkr.cancel(old_scr_odr) if old_scr_odr.get_status() != Order.STATUS_COMPLETED else None
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs.put(scr_odr, len(odrs.get_map()))

    # ——————————————— SAVE DOWN ———————————————

    @staticmethod
    def _save_move(**params):
        p = Config.get(Config.DIR_SAVE_MOVES)
        params_map = Map(params)
        mkt_prc = params_map.get('mkt_prc')
        closes = mkt_prc.get_closes()
        closes_str = [str(v) for v in closes]
        market_json = ModelFeature.json_encode(closes_str)
        params_map.put(market_json, 'market_json')
        params_map.put(ModelFeature.unix_to_date(mkt_prc.get_time()), Map.time)
        params_map.put(mkt_prc.get_rsis(), 'rsis')
        params_map.put(mkt_prc.get_tsis(), 'tsis')
        params_map.put(mkt_prc.get_close(), Map.close)
        params_map.put(mkt_prc.get_super_trend(), 'super_trends')
        params_map.put(mkt_prc.get_super_trend()[0], 'super_trend')
        fields = [
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            # Buy
            'close_trend_ok',
            'is_above_switch',
            'last_is_peak',
            '_last_dropping_close',
            'super_trend',
            'trend_first_idx',
            'last_trend_idx',
            # Lists
            'switchers',
            'maxs',
            'market_json',
            'rsis',
            'super_trends'
        ]
        rows = [{k: (params_map.get(k) if params_map.get(k) is not None else '—') for k in fields}]
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    def _save_capital(self, close: float, time: int) -> None:
        p = Config.get(Config.DIR_SAVE_CAPITAL)
        cap = self._get_capital()
        s_qty = self._get_sell_quantity()
        b_amount = self._get_buy_capital()
        value = s_qty.get_value() * close if s_qty.get_value() > 0 else b_amount.get_value()
        perf = (value/cap.get_value() - 1) * 100
        rows = [{
            Map.time: ModelFeature.unix_to_date(time),
            'close': close,
            'initial': cap.__str__(),
            'left': s_qty.__str__(),
            'right': b_amount.__str__(),
            'value': value,
            'performance': f"{round(perf, 2)}%"
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
