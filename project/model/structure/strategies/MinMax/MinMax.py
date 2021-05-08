from typing import List

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class MinMax(Strategy):
    _CONF_MAKET_PRICE = "config_market_price"
    _CONF_MAX_DR = "CONF_MAX_DR"
    _EXEC_BUY = "EXEC_BUY"
    _EXEC_PLACE_SECURE = "EXEC_PLACE_SECURE"
    _EXEC_SELL = "EXEC_SELL"
    _EXEC_CANCEL_SECURE = "EXEC_CANCEL_SECURE"

    def __init__(self, prms: Map):
        super().__init__(prms)
        self.__configs = None
        self.__secure_order = None
        self._last_red_close = None
        self._last_dropping_close = None
        self.__best_period = None

    def _init_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            # Set Configs
            self._init_constants(bkr)
            # Set Capital
            self._init_capital(bkr)

    def _init_capital(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        cap = None
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            cap = Price(1000, self.get_pair().get_right().get_symbol())
        elif _stage == Config.STAGE_3:
            pass
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        self._set_capital(cap) if cap is not None else None

    def _init_constants(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        bkr_cls = bkr.__class__.__name__
        bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
        # Prepare Set Configs
        best_period = self._get_best_period()
        """
        mkt_rq_prms = Map({
            Map.pair: self.get_pair(),
            Map.period: best_period,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: 1
        })
        exec(f"from model.API.brokers.{bkr_cls}.{bkr_rq_cls} import {bkr_rq_cls}")
        bkr_rq = eval(bkr_rq_cls + f"('{BrokerRequest.RQ_MARKET_PRICE}', mkt_rq_prms)")
        bkr.get_market_price(bkr_rq)
        mkt_prc = bkr_rq.get_market_price()
        """
        self.__configs = Map({
            self._CONF_MAKET_PRICE: Map({
                Map.pair: self.get_pair(),
                Map.period: best_period,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 250
            }),
            self._CONF_MAX_DR: -0.05
        })

    def __get_constants(self) -> Map:
        return self.__configs

    def _get_constant(self, k) -> [float, Map]:
        configs = self.__get_constants()
        if k not in configs.get_keys():
            raise IndexError(f"There's  not constant with this key '{k}'")
        return configs.get(k)

    """
    def _set_best_period(self, bkr: Broker) -> None:
        pair = self.get_pair()
        period_ranking = MinMax.get_period_ranking(bkr, pair)
    """
    def set_best_period(self, best: int) -> None:
        self.__best_period = best

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        stg_name = MinMax.__name__
        minute = 60
        periods = [minute, minute * 3, minute * 5, minute * 15, minute * 30, minute * 60]
        nb_period = 1000
        period_ranking = Strategy.get_top_period(bkr, stg_name, pair, periods, nb_period)
        MinMax._save_period_ranking(period_ranking)
        return period_ranking

    def _get_best_period(self) -> int:
        _stage = Config.get(Config.STAGE_MODE)
        if _stage == Config.STAGE_1:
            self.set_best_period(60) if self.__best_period is None else None
            return self.__best_period
        elif (_stage == Config.STAGE_2) or (_stage == Config.STAGE_3):
            if self.__best_period is None:
                raise Exception(f"Strategy MinMax's best period must be set before.")
            return self.__best_period

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
        max_drop_rate = self._get_constant(self._CONF_MAX_DR)
        # max_rate = 1
        if self._has_position():
            sum_odr = self._get_orders().get_sum()
            qty = sum_odr.get(Map.left)
            # qty = Price(qty.get_value() * max_rate, qty.get_asset().get_symbol())
            qty = Price(qty.get_value(), qty.get_asset().get_symbol())
        else:
            close_val = mkt_prc.get_close()
            b_cap = self._get_buy_capital()
            qty_val = b_cap.get_value() / close_val
            qty = Price(qty_val, pr.get_left().get_symbol())
            # qty = Price(qty_val * max_rate, pr.get_left().get_symbol())
        # stop = mkt_prc.get_futur_price(self._get_constant(self._CONF_MAX_DR))
        super_trend = mkt_prc.get_super_trend()[0]
        # stop = super_trend * (1 + max_drop_rate)
        stop = super_trend
        odr_prms = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pr.get_right().get_symbol()),
            Map.limit: Price(stop, pr.get_right().get_symbol()),
            Map.quantity: qty
        })
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls + "Order('" + Order.TYPE_STOP_LIMIT + "', odr_prms)")
        self._add_order(odr)
        self._set_secure_order(odr)
        return odr

    def trade(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        # Init Strategy in First turn
        self._init_strategy(bkr)
        # Get Market
        mkt_prc = self._get_market_price(bkr)
        # Updatee Orders
        self._update_orders(bkr, mkt_prc)
        # Backup Capital
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())
        # Get And Execute Orders
        if self._has_position():
            executions = self._try_sell(mkt_prc)
        else:
            executions = self._try_buy(mkt_prc)
        # has_execution = len(executions.get_map()) > 0
        # bkr.execute(odrs_to_exec) if has_execution else None
        self.execute(bkr, mkt_prc, executions)
        # Check Order Execution
        # self._check_execution(bkr, mkt_prc, odrs_to_exec) if has_execution else None

    def execute(self, bkr: Broker, mkt_prc: MarketPrice, executions: Map) -> None:
        # from time import sleep                                          # ❌
        # sleep_time = 5                                                  # ❌
        for idx, execution in executions.get_map().items():
            # print(f"Execution: '{execution}'")                          # ❌
            if execution == self._EXEC_BUY:
                buy_order = self._new_buy_order(bkr)
                bkr.execute(buy_order)
            elif execution == self._EXEC_PLACE_SECURE:
                secure_order = self._new_secure_order(bkr, mkt_prc)
                bkr.execute(secure_order)
            elif execution == self._EXEC_SELL:
                sell_order = self._new_sell_order(bkr)
                bkr.execute(sell_order)
            elif execution == self._EXEC_CANCEL_SECURE:
                old_secure_order = self._get_secure_order()
                secure_odr_status = old_secure_order.get_status()
                if secure_odr_status == Order.STATUS_SUBMITTED:  # or (secure_odr_status == Order.STATUS_PROCESSING):
                    bkr.cancel(old_secure_order)
            else:
                raise Exception(f"Unknown execution '{execution}'.")
            # print(f"sleep for {sleep_time} seconds...")                 # ❌
            # sleep(sleep_time)                                           # ❌

    '''
    def _check_execution(self, bkr: Broker, mkt_prc: MarketPrice, odrs_to_exec: Map) -> None:
        """
        To check if all Order have been executed and retry execution of failed Order\n
        :param bkr: access to a Broker's API
        :param mkt_prc: market price
        :param odrs_to_exec: executed Order
        """
        odrs_failed = Map({idx: odr for idx, odr in odrs_to_exec.get_map().items()
                           if (odr.get_status() == Order.STATUS_FAILED) or (odr.get_status() == Order.STATUS_EXPIRED)})
        has_failed = len(odrs_failed.get_map()) > 0
        if has_failed:
            new_odrs_to_exec = Map()
            for idx, odr in odrs_failed.get_map().items():
                move = odr.get_move()
                odr_type = odr.get_type()
                if (move == Order.MOVE_BUY) and (odr_type == Order.TYPE_MARKET):
                    pass
                elif (move == Order.MOVE_SELL) and (odr_type == Order.TYPE_MARKET):
                    new_odrs_to_exec.put(self._new_sell_order(bkr), len(new_odrs_to_exec.get_map()))
                elif (move == Order.MOVE_SELL) and (odr_type == Order.TYPE_STOP_LIMIT):
                    new_odrs_to_exec.put(self._new_secure_order(bkr, mkt_prc), len(new_odrs_to_exec.get_map()))
                else:
                    odr_id = odr.get_id()
                    raise Exception(f"Unknown Order's state (move: '{move}', type: '{odr_type}', id: '{odr_id}').")
            bkr.execute(new_odrs_to_exec) if len(new_odrs_to_exec.get_map()) > 0 else None
    '''

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
    # '''
    def _try_buy(self, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: access to a Broker's API
        :param mkt_prc: market price
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        executions = Map()
        closes = list(mkt_prc.get_closes())
        closes.reverse()
        closes_supers = list(mkt_prc.get_super_trend())
        closes_supers.reverse()
        # Close Trend
        close_trend = MarketPrice.get_super_trend_trend(closes, closes_supers, -1)
        close_trend_ok = close_trend == MarketPrice.SUPERTREND_RISING
        # Switch Point
        if (close_trend == MarketPrice.SUPERTREND_RISING) and (self._last_red_close is None):
            switchers = MarketPrice.get_super_trend_switchers(closes, closes_supers)
            trend_first_idx = switchers.get_keys()[-1] if close_trend_ok else None
            last_trend_idx = (trend_first_idx - 1) if trend_first_idx is not None else None
            # self._last_red_trend = closes_supers[last_trend_idx] if last_trend_idx is not None else None
            self._last_red_close = closes[last_trend_idx] if last_trend_idx is not None else None
        if (close_trend == MarketPrice.SUPERTREND_DROPING) and (self._last_red_close is not None):
            self._last_red_close = None
        super_trend = closes_supers[-1]
        # super_trend = closes[-1]
        is_above_switch = super_trend >= self._last_red_close if self._last_red_close is not None else False
        # Checking
        last_red_close = self._last_red_close
        if close_trend_ok and is_above_switch:
            self._buy(executions)
            self._last_red_close = None
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_BUY, _last_red_close=last_red_close)  # \
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
            '_last_red_close',
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
        return executions
    # '''

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

    # TEST STAGE_3
    """
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        executions = Map()
        self._buy(bkr, mkt_prc, executions)
        self._move_up_secure_order(bkr, mkt_prc, executions)
        self._sell(bkr, executions)
        return executions

    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        raise Exception("❌ NO TRY SELL")
        return executions
    """

    def _buy(self, executions: Map) -> None:
        """
        To add buy execution\n
        NOTE: its include Buy Order and a secure Order\n
        :param executions: where to place generated Order
        """
        """
        # buy order
        b_odr = self._new_buy_order(bkr)
        odrs.put(b_odr, len(odrs.get_map()))
        # secure order
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs.put(scr_odr, len(odrs.get_map()))
        """
        # Buy Order
        executions.put(self._EXEC_BUY, len(executions.get_map()))
        # Place Secure order
        executions.put(self._EXEC_PLACE_SECURE, len(executions.get_map()))

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
    # '''
    def _try_sell(self, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        executions = Map()
        # Close Trend
        close = mkt_prc.get_close()
        closes_supers = mkt_prc.get_super_trend()
        close_trend_ok = (close < closes_supers[0]) or ((close > closes_supers[1]) and (close == closes_supers[0]))
        # Secure Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_constant(self._CONF_MAX_DR))
        # CHECK
        if close_trend_ok:
            self._sell(executions)
        # elif mkt_prc.get_close() > stop_base_prc:
        # elif closes_supers[0] > stop_base_prc:
        #     self._move_up_secure_order(executions)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL)  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return executions
    # '''

    def _sell(self, executions: Map) -> None:
        """
        To generate sell Order\n
        NOTE: its cancel secure Order and generate a sell Order\n
        :param bkr: access to a Broker's API
        :param executions: where to place generated Order
        """
        """
        old_scr_odr = self._get_secure_order()
        # bkr.cancel(old_scr_odr) if old_scr_odr.get_status() != Order.STATUS_COMPLETED else None
        secure_odr_status = old_scr_odr.get_status()
        bkr.cancel(old_scr_odr) \
            if (secure_odr_status == Order.STATUS_SUBMITTED) \
               or (secure_odr_status == Order.STATUS_PROCESSING) else None
        s_odr = self._new_sell_order(bkr)
        odrs.put(s_odr, len(odrs.get_map()))
        """
        # Cancel Secure Order
        executions.put(self._EXEC_CANCEL_SECURE, len(executions.get_map()))
        # Sell
        executions.put(self._EXEC_SELL, len(executions.get_map()))

    def _move_up_secure_order(self, executions: Map) -> None:
        """
        To move up the secure Order\n
        :param bkr: access to a Broker's API
        :param mkt_prc: market price
        :param executions: where to place generated Order
        """
        """
        old_scr_odr = self._get_secure_order()
        # bkr.cancel(old_scr_odr) if old_scr_odr.get_status() != Order.STATUS_COMPLETED else None
        secure_odr_status = old_scr_odr.get_status()
        bkr.cancel(old_scr_odr) \
            if (secure_odr_status == Order.STATUS_SUBMITTED) \
               or (secure_odr_status == Order.STATUS_PROCESSING) else None
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs.put(scr_odr, len(odrs.get_map()))
        """
        # Cancel Secure Order
        executions.put(self._EXEC_CANCEL_SECURE, len(executions.get_map()))
        # Place Secure order
        executions.put(self._EXEC_PLACE_SECURE, len(executions.get_map()))

    # ——————————————— SAVE DOWN ———————————————

    @staticmethod
    def _save_move(**params):
        p = Config.get(Config.DIR_SAVE_MOVES)
        params_map = Map(params)
        mkt_prc = params_map.get('mkt_prc')
        closes = mkt_prc.get_closes()
        closes_str = [str(v) for v in closes]
        market_json = _MF.json_encode(closes_str)
        params_map.put(market_json, 'market_json')
        params_map.put(_MF.unix_to_date(mkt_prc.get_time()), Map.time)
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
            '_last_red_close',
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
        r_symbol = cap.get_asset().get_symbol()
        sell_qty = self._get_sell_quantity()
        buy_amount = self._get_buy_capital()
        odrs = self._get_orders()
        positions_value = sell_qty.get_value() * close  # if sell_qty.get_value() > 0 else 0
        current_capital_val = positions_value + buy_amount.get_value() if sell_qty.get_value() > 0 else buy_amount.get_value()
        perf = (current_capital_val / cap.get_value() - 1) * 100
        sum_odr = odrs.get_sum() if odrs.get_size() > 0 else None
        fees = sum_odr.get(Map.fee) if sum_odr is not None else Price(0, r_symbol)
        # real_perf = ((current_capital_val - fees.get_value()) / cap - 1) * 100
        current_capital_obj = Price(current_capital_val, r_symbol)
        rows = [{
            Map.time: _MF.unix_to_date(time, _MF.FORMAT_D_H_M_S),
            'close': close,
            'initial': cap,
            'current_capital': current_capital_obj,
            # 'real_capital': current_capital_obj - fees,
            'fees': fees,
            'left': sell_qty,
            'right': buy_amount,
            'positions_value': positions_value,
            'capital_perf': f"{round(perf, 2)}%",
            # 'real_perf': f"{round(real_perf, 2)}%"
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    @staticmethod
    def _save_period_ranking(ranking: Map) -> None:
        rows = []
        base = {
            Map.pair:  ranking.get(Map.pair),
            Map.fee:  ranking.get(Map.fee),
            Map.number:  ranking.get(Map.number)
        }
        date = _MF.unix_to_date(_MF.get_timestamp())
        for rank, struc in ranking.get(Map.period).items():
            row = {
                Map.date: date,
                Map.rank: rank,
                f"{Map.period}_minutes": struc[Map.period] / 60,
                **base,
                Map.roi: struc[Map.roi],
                Map.day: struc[Map.day],
                Map.transaction: _MF.json_encode(struc[Map.transaction]),
                Map.rate: _MF.json_encode(struc[Map.rate])
            }
            rows.append(row)
        path = Config.get(Config.DIR_SAVE_PERIOD_RANKING)
        fields = list(rows[0].keys())
        FileManager.write_csv(path, fields, rows, overwrite=False)

    # ——————————————— STATIC METHOD DOWN ———————————————

    @staticmethod   # Strategy
    def get_performance(bkr: Broker, market_price: MarketPrice) -> Map:
        initial_capital = Strategy.get_performance_init_capital()
        pair = market_price.get_pair()
        fees = bkr.get_trade_fee(pair)
        fee_rate = fees.get(Map.taker)
        closes = list(market_price.get_closes())
        closes.reverse()
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        rates = MinMax._performance_get_rates(market_price)
        transactions = MinMax._performance_get_transactions(initial_capital, rates, fees)
        last_transac = transactions[-1]
        roi = last_transac.get(Map.capital) / initial_capital - 1
        perf = Map({
            Map.roi: roi,
            Map.fee: fee_rate,
            Map.rate: rates,
            Map.transaction: transactions,
        })
        return perf

    @staticmethod   # Strategy
    def _performance_get_transactions(initial_capital: float, rates: List[float], fees: Map) -> List[dict]:
        transactions = []
        fee_rate = fees.get(Map.taker)
        # Initialize First Capital
        transaction1 = Map()
        transaction1.put(initial_capital, Map.capital)
        transaction1.put(None, Map.buy)
        transaction1.put(None, Map.sell)
        transaction1.put(initial_capital * fee_rate, Map.fee)
        transactions.append(transaction1.get_map())
        for rate in rates:
            last_transac = transactions[-1]
            # Add Buy Transaction
            last_capital = last_transac.get(Map.capital)
            last_fee = last_transac.get(Map.fee)
            buy_transac = Map()
            buy = last_capital - last_fee
            sell_fee = buy * fee_rate
            buy_transac.put(buy, Map.capital)
            buy_transac.put(buy, Map.buy)
            buy_transac.put(sell_fee, Map.fee)
            transactions.append(buy_transac.get_map())
            # Add Sell Transaction
            sell_transact = Map()
            sell = buy * (1 + rate) - sell_fee
            buy_fee = sell * fee_rate
            sell_transact.put(sell, Map.capital)
            sell_transact.put(sell, Map.sell)
            sell_transact.put(buy_fee, Map.fee)
            transactions.append(sell_transact.get_map())
        return transactions

    @staticmethod   # Strategy
    def _performance_get_rates(market_price: MarketPrice) -> list:
        closes = list(market_price.get_closes())
        closes.reverse()
        super_trends = list(market_price.get_super_trend())
        super_trends.reverse()
        switchers = MarketPrice.get_super_trend_switchers(closes, super_trends)
        perf_rates = []
        nb_close = len(closes)
        periods = switchers.get_keys()
        nb_period = len(switchers.get_map())
        for i in range(nb_period):
            period = periods[i]
            trend = switchers.get(period)
            if (trend == MarketPrice.SUPERTREND_RISING) and (period > 0):
                start_period = period
                end_period = periods[i + 1] if i < nb_period - 1 else nb_close
                last_red_close = closes[start_period - 1]
                entry_period = None
                j = start_period
                while j < end_period:
                    super_trend = super_trends[j]
                    if super_trend >= last_red_close:
                        entry_period = j
                        break
                    j += 1
                perf_rate = (closes[end_period - 1] / closes[entry_period] - 1) if entry_period is not None else None
                perf_rates.append(perf_rate) if perf_rate is not None else None
        return perf_rates
