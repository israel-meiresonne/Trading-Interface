from decimal import Decimal
# from math import isnan
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
    _CONF_PS_AVG = "CONF_PS_AVG"
    _CONF_MAX_DR = "CONF_MAX_DR"
    _CONF_DS_AVG = "CONF_DS_AVG"
    _CONF_PEAK_DROP_RATE = "CONF_PEAK_DROP_RATE"
    _CONF_TSI_PEAK_DROP_RATE = "CONF_TSI_PEAK_DROP_RATE"
    _CONF_RSI_BS = "_CONF_RSI_BS"                   # RSI Buy Signal
    _CONF_RSI_SS = "_CONF_RSI_SS"                   # RSI Sell Signal
    _CONF_SLP_BS = "_CONF_SLP_BS"                   # Slope Buy Signal
    _CONF_RSI_PEAK_DROP_POINT = "_CONF_RSI_PEAK_DROP_POINT"
    _TREND_RISING = "TREND_RISING"
    _TREND_DROPING = "TREND_DROPING"

    def __init__(self, prms: Map):
        """
        Constructor\n
        :param prms: params
                     prms[Map.pair]     => {Pair}
                     prms[Map.capital]  => {Price|None}
                     prms[Map.rate]     => {float|None}  # ]0,1]
        """
        super().__init__(prms)
        self.__configs = None
        self.__secure_order = None
        self._trends = None
        self._permits = Map()

    def _set_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            bkr_cls = bkr.__class__.__name__
            rq_cls = BrokerRequest.get_request_class(bkr_cls)
            # Prepare Set Configs
            _stage = Config.get(Config.STAGE_MODE)
            mkt_rq_prms = Map({
                Map.pair: self.get_pair(),
                # Map.period: 60 * 60 * 24 if (stage == Config.STAGE_1) else 60,            # ✅
                Map.period: 60,                                                         # ❌
                Map.begin_time: None,
                Map.end_time: None,
                # Map.number: 360                                                           # ✅
                Map.number: 1                                                           # ❌
            })
            exec(f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}")
            bkr_rq = eval(rq_cls + f"('{BrokerRequest.RQ_MARKET_PRICE}', mkt_rq_prms)")
            bkr.get_market_price(bkr_rq)
            mkt_prc = bkr_rq.get_market_price()
            # Set Configs
            self._set_configs(Map({
                self._CONF_MAKET_PRICE: Map({
                    Map.pair: self.get_pair(),
                    Map.period: 60,
                    Map.begin_time: None,
                    Map.end_time: None,
                    Map.number: 100
                }),
                self._CONF_MAX_DR: Decimal('-0.05'),
                # self._CONF_DS_AVG: mkt_prc.get_indicator(MarketPrice.INDIC_DS_AVG),       # ✅
                # self._CONF_DS_AVG: Decimal('-0.001608511499838030450275348233'),        # ❌
                self._CONF_PEAK_DROP_RATE: Decimal('-0.005'),
                # self._CONF_RSI_BS: Decimal('40'),               # BTC
                # self._CONF_RSI_SS: Decimal('57.5'),             # BTC
                # self._CONF_SLP_BS: Decimal('20'),               # BTC
                # self._CONF_RSI_PEAK_DROP_POINT: Decimal('3'),   # BTC
                self._CONF_RSI_BS: Decimal('40'),               # BNB
                self._CONF_RSI_SS: Decimal('50'),               # BNB
                self._CONF_SLP_BS: Decimal('0.2'),              # BNB
                self._CONF_RSI_PEAK_DROP_POINT: Decimal('3'),   # BNB
                self._CONF_TSI_PEAK_DROP_RATE: Decimal('-0.005')
            }))
            # Set Capital
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
                cap = Price(1000, self.get_pair().get_right().get_symbol())
            elif _stage == Config.STAGE_3:
                # """
                snap_rq_prms = Map({
                        Map.account: BrokerRequest.ACCOUNT_MAIN,
                        Map.begin_time: None,
                        Map.end_time: self.get_timestamp(self.TIME_MILLISEC),
                        Map.number: 5,
                        Map.timeout: None,
                    })
                snap_rq = eval(rq_cls+f"('{BrokerRequest.RQ_ACCOUNT_SNAP}', snap_rq_prms)")
                bkr.get_account_snapshot(snap_rq)
                accounts = snap_rq.get_account_snapshot()
                right = self.get_pair().get_right()
                times = list(accounts.get(Map.account).keys())
                cap = accounts.get(Map.account, times[-1], right.get_symbol())
                # """
            else:
                raise Exception(f"Unknown stage '{_stage}'.")
            # Raise error if set capital is bellow Broker's minimum trade amount
            self._set_capital(cap)

    def _set_configs(self, configs: Map) -> None:
        self.__configs = configs

    def __get_configs(self) -> Map:
        return self.__configs

    def _get_config(self, k) -> [float, Decimal, Map]:
        configs = self.__get_configs()
        if k not in configs.get_keys():
            raise IndexError(f"There's  not config for this key '{k}'")
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
        mkt_prms = self._get_config(self._CONF_MAKET_PRICE)
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
        stop = mkt_prc.get_futur_price(self._get_config(self._CONF_MAX_DR))
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
        self._set_strategy(bkr)
        mkt_prc = self._get_market_price(bkr)
        self._update_orders(bkr, mkt_prc)
        # Save
        _stage = Config.get(Config.STAGE_MODE)
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())  # \
        # if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        #
        if self._has_position():
            odrs_map = self._try_sell(bkr, mkt_prc)
        else:
            odrs_map = self._try_buy(bkr, mkt_prc)
        bkr.execute(odrs_map) if len(odrs_map.get_map()) > 0 else None

    # ——————————————— BUY DOWN ———————————————

    # ORIGINAL WITH RSI
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        period = 1
        _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
        if (_slope > 0) and (period in mkt_prc.get_minimums()):
            _ps_avg = self._get_config(self._CONF_PS_AVG)
            _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
            # """
            _rsi_bs = self._get_config(self._CONF_RSI_BS)
            rsi = mkt_prc.get_rsi()
            if (rsi <= _rsi_bs) and (_ms >= _ps_avg):
            # """
            # if _ms >= _ps_avg:
                """
                # buy order
                b_odr = self._new_buy_order(bkr)
                odrs.put(b_odr, len(odrs.get_map()))
                # secure order
                scr_odr = self._new_secure_order(bkr, mkt_prc)
                odrs.put(scr_odr, len(odrs.get_map()))
                """
                self._buy(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # WITH RSI & SLOPE AVG
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        rsi = mkt_prc.get_rsi()
        _rsi_bs = self._get_config(self._CONF_RSI_BS)
        slope_avg = mkt_prc.get_slopes_avg()[0]
        _slope_bs = self._get_config(self._CONF_SLP_BS)
        if (rsi <= _rsi_bs) and (slope_avg < _slope_bs):
            self._buy(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # TSI > EMA(TSI) & RSI
    '''
    def _update_permits(self, mkt_prc: MarketPrice) -> None:
        permits = self._permits
        rsi_permit = permits.get(Map.rsi)
        if (rsi_permit is None) or (not rsi_permit):
            _rsi_bs = self._get_config(self._CONF_RSI_BS)
            rsi_permit = mkt_prc.get_rsi() <= _rsi_bs
            permits.put(rsi_permit, Map.rsi)

    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        self._update_permits(mkt_prc)
        rsi_permit = self._permits.get(Map.rsi)
        tsi = mkt_prc.get_tsis()[0]
        ema_tsi = mkt_prc.get_tsis_emas()[0]
        if rsi_permit and (tsi >= ema_tsi):
            self._buy(bkr, mkt_prc, odrs)
            self._permits.put(None, Map.rsi)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY, rsi=mkt_prc.get_rsi()) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    def _get_trends(self) -> list:
        self._trends = [] if self._trends is None else self._trends
        return self._trends

    def _update_trends(self, mkt_prc: MarketPrice) -> None:
        close = mkt_prc.get_close()
        sptrend = mkt_prc.get_super_trend()[0]
        trend = self._TREND_RISING if close > sptrend else None
        trend = self._TREND_DROPING if ((trend is None) and (close < sptrend)) else trend
        trends = self._get_trends()
        trends.append(trend) if (len(trends) <= 0) or (trends[-1] != trend) else None

    # SuperTrend Switch: V1
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        self._update_trends(mkt_prc)
        trends = self._get_trends()
        up_end = (len(trends) >= 2) and (trends[-1] == self._TREND_RISING) and (trends[-2] == self._TREND_DROPING)
        if up_end:
            self._buy(bkr, mkt_prc, odrs)
            a = trends
            self._trends = None
            trends = a
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY, rsi=mkt_prc.get_rsi(),
                        tsi=mkt_prc.get_tsis()[0], ema_tsi=mkt_prc.get_tsis_emas()[0]) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # SuperTrend Switch: V2
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        self._update_trends(mkt_prc)
        trends = self._get_trends()
        ema_tsi = mkt_prc.get_tsis_emas()[0]
        rsi = mkt_prc.get_rsi()
        rsi_ok = (rsi < 60)
        # Switch
        tsi = mkt_prc.get_tsis()[0]
        tsi_ok = tsi > ema_tsi
        trend_switch = (len(trends) >= 2) and (trends[-1] == self._TREND_RISING) and (trends[-2] == self._TREND_DROPING)
        drop_to_rise_ok = rsi_ok and tsi_ok and trend_switch
        # Is Rising
        trend_ok = trends[-1] == self._TREND_RISING
        rising_ok = trend_ok and tsi_ok and rsi_ok
        # Checking
        if drop_to_rise_ok or rising_ok:
            self._buy(bkr, mkt_prc, odrs)
            a = trends
            self._trends = None
            trends = a
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # SuperTrend Switch: V3
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs = Map()
        self._update_trends(mkt_prc)
        trends = self._get_trends()
        ema_tsi = mkt_prc.get_tsis_emas()[0]
        rsis = mkt_prc.get_rsis()
        xs = [v for v in range(3)]
        ys = [float(rsis[i]) for i in range(2, -1, -1)]
        # ys = [rsis[2], rsis[1], rsis[0]]
        rsi_slope = self.get_slope(ys, xs).get(Map.slope)
        rsi_ok = (rsi_slope > 0)
        # Switch
        tsi = mkt_prc.get_tsis()[0]
        tsi_ok = tsi > ema_tsi
        trend_switch = (len(trends) >= 2) and (trends[-1] == self._TREND_RISING) and (trends[-2] == self._TREND_DROPING)
        drop_to_rise_ok = rsi_ok and tsi_ok and trend_switch
        # Is Rising
        trend_ok = trends[-1] == self._TREND_RISING
        rising_ok = trend_ok and tsi_ok and rsi_ok
        # Checking
        if drop_to_rise_ok or rising_ok:
            self._buy(bkr, mkt_prc, odrs)
            a = trends
            self._trends = None
            trends = a
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY, rsi=mkt_prc.get_rsi()) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        """
        fields = [
            Map.time,
            'close',
            'move',
            'buy_odr_prc',
            'secure_odr_prc',
            'stop_base_prc',
            '_slope',
            '_slope_bs',
            'slope_avg',
            'peak',
            'peak_max_drop',
            'rsi',
            '_rsi_bs',
            '_rsi_ss',
            'rsi_up',
            'rsi_permit',
            'rsi_peak_idx',
            'rsi_peak_prd',
            'rsi_peak',
            'rsi_ok',
            '_rsi_pk_dp',
            'rsi_peak_max_drop',
            'tsi',
            'peak_tsis_prd',
            'peak_tsi',
            'tsi_max_drop_rate',
            'tsi_max_drop',
            'tsi_ok',
            'ema_tsi',
            'super_trend',
            'last_sptrend',
            'up_end',
            'trends',
            '_ms',
            '_ps_avg',
            '_ds_avg',
            '_dr',
            '_max_dr',
            'market_json',
            'rsis',
            'tsis',
            'super_trends'
        ]
        """
        return odrs
    '''

    # TREND(RSI)&TREND(CLOSE): BUY
    # '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        _vars_before = dict(vars())
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
        self._save_move(**vars(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
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
    # '''

    # JULIA'S BUY
    '''
    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        odrs = Map()
        close = mkt_prc.get_close()
        last_sptrend = mkt_prc.get_super_trend()[1]
        rsi = mkt_prc.get_rsi()                 # ❌
        _rsi_bs = self._get_config(self._CONF_RSI_BS)
        if (close < last_sptrend) and (rsi <= _rsi_bs):
            self._buy(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    def _buy(self, bkr: Broker, mkt_prc: MarketPrice, odrs: Map) -> None:
        # buy order
        b_odr = self._new_buy_order(bkr)
        odrs.put(b_odr, len(odrs.get_map()))
        # secure order
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs.put(scr_odr, len(odrs.get_map()))

    # ——————————————— BUY UP ——————————————————
    # ——————————————— SELL DOWN ———————————————

    # No PEAK
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        odrs_map = Map()
        last_odr = self._get_orders().get_last_execution()
        if last_odr is None:
            raise Exception("Last order completed can't be empty")
        exec_prc_val = last_odr.get_execution_price().get_value()
        close = mkt_prc.get_close()
        _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
        if (exec_prc_val < close) and (_slope > 0):
            self._move_up_secure_order(bkr, mkt_prc, odrs_map)
        elif _slope < 0:
            self._check_sell(bkr, mkt_prc, odrs_map)
        # Save in files
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs_map
    '''

    # WITH PEAK & RSI
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        buy_odr = self._get_orders().get_last_execution()
        if buy_odr is None:
            raise Exception("Last order completed can't be empty")
        # Extract Peak
        peak_idx = self._get_peak_since_buy(mkt_prc)
        peak = mkt_prc.get_close(peak_idx) if peak_idx is not None else None
        _pk_dr = self._get_config(self._CONF_PEAK_DROP_RATE)
        peak_max_drop = peak * (1 + _pk_dr) if peak is not None else None
        #
        _rsi_ss = self._get_config(self._CONF_RSI_SS)
        rsi = mkt_prc.get_rsi()
        if rsi > _rsi_ss:
            close = mkt_prc.get_close()
            buy_odr_prc = buy_odr.get_execution_price().get_value()
            if (peak_max_drop is not None) \
                    and (close > buy_odr_prc) \
                    and (close <= peak_max_drop):
                self._sell(bkr, odrs)
            else:
                _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
                if (buy_odr_prc < close) and (_slope > 0):
                    self._move_up_secure_order(bkr, mkt_prc, odrs)
                elif _slope < 0:
                    # self._check_sell(bkr, mkt_prc, odrs)
                    vars_rtn = self._check_sell(bkr, mkt_prc, odrs)
        # Save in files
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # WITH PEAK & OPTIMIZED RSI
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        buy_odr = self._get_orders().get_last_execution()
        if buy_odr is None:
            raise Exception("Last order completed can't be empty")
        # Extract Peak
        peak_idx = self._get_peak_since_buy(mkt_prc)
        peak = mkt_prc.get_close(peak_idx) if peak_idx is not None else None
        _pk_dr = self._get_config(self._CONF_PEAK_DROP_RATE)
        peak_max_drop = peak * (1 + _pk_dr) if peak is not None else None
        #
        _rsi_ss = self._get_config(self._CONF_RSI_SS)
        rsi = mkt_prc.get_rsi()
        close = mkt_prc.get_close()
        buy_odr_prc = buy_odr.get_execution_price().get_value()
        if close > buy_odr_prc:
            rsi_up = rsi > _rsi_ss
            if rsi_up and (peak is not None) and (close <= peak_max_drop):
                self._sell(bkr, odrs)
            elif rsi_up:
                _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
                _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
                _ds_avg = self._get_config(self._CONF_DS_AVG)
                self._sell(bkr, odrs) if (_slope < 0) and (_ms <= _ds_avg) else None
            elif close > self._get_secure_order().get_stop_price().get_value():
                self._move_up_secure_order(bkr, mkt_prc, odrs)
        elif close < buy_odr_prc:
            self._sell(bkr, odrs)
        # Save in files
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # WITH RSI PEAK
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        buy_odr = self._get_orders().get_last_execution()
        if buy_odr is None:
            raise Exception("Last order completed can't be empty")
        # Extract Peak
        # rsi_peak_idx = self._get_buy_period(buy_odr, mkt_prc)
        buy_odr_idx = self._get_buy_period(buy_odr, mkt_prc)
        # rsi_peak = mkt_prc.get_rsi(rsi_peak_idx) if rsi_peak_idx is not None else None
        rsi_peak_idx = self._get_peak(mkt_prc.get_rsis(), 0, buy_odr_idx) if buy_odr_idx is not None else None
        rsi_peak = mkt_prc.get_rsi(rsi_peak_idx) if rsi_peak_idx is not None else None
        _rsi_pk_dp = self._get_config(self._CONF_RSI_PEAK_DROP_POINT)
        rsi_peak_max_drop = (rsi_peak - _rsi_pk_dp) if (rsi_peak is not None) and (not isnan(rsi_peak)) else None
        #
        _rsi_ss = self._get_config(self._CONF_RSI_SS)
        rsi = mkt_prc.get_rsi()
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_config(self._CONF_MAX_DR))          # ❌
        if (rsi > _rsi_ss) and (rsi_peak_max_drop is not None) and (rsi < rsi_peak_max_drop):
            self._sell(bkr, odrs)
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # RSI PEAK & TSI PEAK: V1
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        last_odr = self._get_orders().get_last_execution()
        if last_odr is None:
            raise Exception("Last order completed can't be empty")
        _rsi_ss = self._get_config(self._CONF_RSI_SS)
        # RSI
        rsis = mkt_prc.get_rsis()
        rsi_peak_prd = MarketPrice.get_peak_since_buy(last_odr, rsis, mkt_prc)
        rsi_peak = rsis[rsi_peak_prd] if rsi_peak_prd is not None else None
        rsi_ok = (rsi_peak is not None) and (rsi_peak >= _rsi_ss)
        # TSI
        tsis = mkt_prc.get_tsis()
        tsi = tsis[0]
        peak_tsis_prd = MarketPrice.get_peak_since_buy(last_odr, tsis, mkt_prc)
        peak_tsi = tsis[peak_tsis_prd] if peak_tsis_prd is not None else None
        _tsi_max_drop_rate = self._get_config(self._CONF_TSI_PEAK_DROP_RATE)
        # tsi_max_drop = (peak_tsi * (1+_tsi_max_drop_rate)) if peak_tsi is not None else None
        tsi_max_drop = (peak_tsi - abs(peak_tsi * _tsi_max_drop_rate)) if peak_tsi is not None else None
        tsi_ok = (tsi_max_drop is not None) and (tsi <= tsi_max_drop)
        # SECURE Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_config(self._CONF_MAX_DR))          # ❌
        # CHECK
        if rsi_ok and tsi_ok:
            self._sell(bkr, odrs)
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL, rsi=mkt_prc.get_rsi(), ema_tsi=mkt_prc.get_tsis_emas()[0]) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # TSI < EMA(TSI) OR DROPPING
    '''
    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        self._update_trends(mkt_prc)
        # TSI
        tsi = mkt_prc.get_tsis()[0]
        ema_tsi = mkt_prc.get_tsis_emas()[0]
        tsi_ok = tsi < ema_tsi
        # Trend
        trends = self._get_trends()
        trend_ok = trends[-1] == self._TREND_DROPING
        # SECURE Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_config(self._CONF_MAX_DR))          # ❌
        # CHECK
        if tsi_ok or trend_ok:
            self._sell(bkr, odrs)
            a = trends
            trends = None
            trends = a
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL, rsi=mkt_prc.get_rsi()) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # TREND(RSI)&TREND(CLOSE): SELL
    # '''
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
        stop_base_prc = secure_odr_prc / (1 + self._get_config(self._CONF_MAX_DR))          # ❌
        # CHECK
        if rsi_trend_ok or close_trend_ok:
            self._sell(bkr, odrs)
        elif mkt_prc.get_close() > stop_base_prc:
            self._move_up_secure_order(bkr, mkt_prc, odrs)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    # '''

    # JULIA'S SELL
    '''
    def _update_trend(self, mkt_prc: MarketPrice) -> None:
        close = mkt_prc.get_close()
        sptrend = mkt_prc.get_super_trend()[0]
        trend = self._TREND_UP if close > sptrend else None
        trend = self._TREND_DOWN if ((trend is None) and (close < sptrend)) else trend
        trends = self._get_trends()
        trends.append(trend) if (len(trends) <= 0) or (trends[-1] != trend) else None

    def _try_sell(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :param mkt_prc: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        vars_rtn = {}
        odrs = Map()
        self._update_trend(mkt_prc)
        trends = self._get_trends()
        up_end = (len(trends) >= 2) and (trends[-1] == self._TREND_DOWN) and (trends[-2] == self._TREND_UP)
        if up_end:
            self._sell(bkr, odrs)
            a = list(trends)                # ❌
            trends = None
            trends = a                      # ❌
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL, rsi=mkt_prc.get_rsi()) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs
    '''

    # ——————————————— SELL UP ———————————————

    @staticmethod
    def _get_buy_period(odr: Order, mkt_prc: MarketPrice) -> int:
        """
        To get period index of when tha order was executed\n
        :param odr: the executed order
        :param mkt_prc: market prices
        :return: period index of when tha order was executed
        """
        if odr.get_status() != Order.STATUS_COMPLETED:
            raise Exception(f"The Order's status must be '{Order.STATUS_COMPLETED}' instead of '{odr.get_status()}'")
        buy_time = odr.get_execution_time()
        time = mkt_prc.get_time()
        prd_time = mkt_prc.get_period_time()
        # buy_prd = (int((time - buy_time) / prd_time) + 1)
        buy_prd = int((time - buy_time) / prd_time)
        _stage = Config.get(Config.STAGE_MODE)
        buy_prd = buy_prd if _stage == Config.STAGE_1 else buy_prd + 1
        return buy_prd

    def _get_peak(self, vs: Union[list, tuple], min_idx: int, max_idx: int) -> [int, None]:
        nb_prd = len(vs)
        if max_idx >= nb_prd:
            peak_idx = self.get_maximum(vs, min_idx, nb_prd - 1)
        else:
            peak_idx = self.get_maximum(vs, min_idx, max_idx)
        return peak_idx

    def _get_peak_since_buy(self, mkt_prc: MarketPrice) -> [int, None]:
        """
        To get the period of the maximum price in MarketPrice\n
        :param mkt_prc: market prices
        :return: period of the maximum price in MarketPrice
        """
        last_odr = self._get_orders().get_last_execution()
        if last_odr is None:
            raise Exception("Last order completed can't be empty")
        """
        buy_time = last_odr.get_execution_time()
        time = mkt_prc.get_time()
        prd_time = mkt_prc.get_period_time()
        buy_prd = (int((time - buy_time) / prd_time) + 1)
        """
        buy_prd = self._get_buy_period(last_odr, mkt_prc)
        closes = mkt_prc.get_closes()
        nb_prd = len(closes)
        """
        if buy_prd >= nb_prd:
            peak_idx = self.get_maximum(tuple(closes), 0, nb_prd - 1)
        else:
            peak_idx = self.get_maximum(tuple(closes), 0, buy_prd)
        """
        peak_idx = self._get_peak(closes, 0, nb_prd - 1) if (buy_prd >= nb_prd) else self._get_peak(closes, 0, buy_prd)
        return peak_idx

    def _check_sell(self, bkr: Broker, mkt_prc: MarketPrice, odrs: Map):  # -> None:
        _dr = mkt_prc.get_indicator(MarketPrice.INDIC_DR)
        _max_dr = self._get_config(self._CONF_MAX_DR)
        _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
        _ds_avg = self._get_config(self._CONF_DS_AVG)
        if (_dr <= _max_dr) or (_ms <= _ds_avg):
            self._sell(bkr, odrs)
        return vars()

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

    # ——————————————— SAVE ———————————————

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
            'tsis',
            'super_trends'
        ]
        rows = [{k: (params_map.get(k) if params_map.get(k) is not None else '—') for k in fields}]
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    '''
    SAVE_KEYS = None
    @staticmethod
    def _save_move(_vars_before: dict, _vars_after: dict, sell_attr: list = []) -> None:
        _new_vars = {k: _vars_after[k] for k in _vars_after if (k not in _vars_before) and k not in vars()}
        keys = list(_new_vars.keys()) + sell_attr if MinMax.SAVE_KEYS is None else MinMax.SAVE_KEYS
        MinMax.SAVE_KEYS = keys
        keys.sort()
        firsts = [
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc'
        ]
        row = {}
        for k in firsts:
            row[k] = _new_vars[k] if k in _new_vars else '—'
        for k, v in _new_vars.items():
            if (k not in row) and ((type(v) == bool) or(type(v) == str) or (type(v) == int) or (type(v) == float) or (type(v) == Decimal)):
                row[k] = v
        for k, v in _new_vars.items():
            if k not in row:
                row[k] = v
        for k in MinMax.SAVE_KEYS:
            if k not in row:
                row[k] = '—'
        rows = [row]
        fields = list(row.keys())
        overwrite = False
        p = Config.get(Config.DIR_SAVE_MOVES)
        FileManager.write_csv(p, fields, rows, overwrite)
    '''

    def _save_capital(self, close: Decimal, time: int) -> None:
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
