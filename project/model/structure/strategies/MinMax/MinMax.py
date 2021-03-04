from decimal import Decimal

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
    _CONF_PEAK_DROP_RATE = "_CONF_PEAK_DROP_RATE"

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

    def __set_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            bkr_cls = bkr.__class__.__name__
            rq_cls = BrokerRequest.get_request_class(bkr_cls)
            # Prepare Set Configs
            stage = Config.get(Config.STAGE_MODE)
            rq_prms = Map({
                Map.pair: self.get_pair(),
                Map.period: 60 * 60 * 24 if (stage == Config.STAGE_1) else 60,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 360
            })
            exec(f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}")
            bkr_rq = eval(rq_cls + f"('{BrokerRequest.RQ_MARKET_PRICE}', rq_prms)")
            bkr.get_market_price(bkr_rq)
            mkt_prc = bkr_rq.get_market_price()
            # Set Configs
            self._set_configs(Map({
                self._CONF_MAKET_PRICE: Map({
                    Map.pair: self.get_pair(),
                    Map.period: 60 * 60 * 24 if (stage == Config.STAGE_1) else 60,
                    Map.begin_time: None,
                    Map.end_time: None,
                    Map.number: 20
                }),
                self._CONF_PS_AVG: mkt_prc.get_indicator(MarketPrice.INDIC_PS_AVG),
                self._CONF_MAX_DR: Decimal('-0.005'),
                self._CONF_DS_AVG: mkt_prc.get_indicator(MarketPrice.INDIC_DS_AVG),
                self._CONF_PEAK_DROP_RATE: Decimal('-0.005')
            }))
            # Set Capital
            """
            rq_prms = Map({
                    Map.account: BrokerRequest.ACCOUNT_MAIN,
                    Map.begin_time: None,
                    Map.end_time: None,
                    Map.number: 1,
                    Map.timeout: None,
                })
            snap_rq = eval(rq_cls+f"('{BrokerRequest.RQ_ACCOUNT_SNAP}', rq_prms)")
            bkr.get_account_snapshot(snap_rq)
            accounts = snap_rq.get_account_snapshot()
            right = self.get_pair().get_right()
            cap = accounts.get(right.get_symbol())
            """
            cap = Price(1000, self.get_pair().get_right().get_symbol())
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
        self.__set_strategy(bkr)
        mkt_prc = self._get_market_price(bkr)
        self._update_orders(mkt_prc)
        _stage = Config.get(Config.STAGE_MODE)
        self._save_capital(close=mkt_prc.get_close()) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        if self._has_position():
            odrs_map = self._try_sell(bkr, mkt_prc)
        else:
            odrs_map = self._try_buy(bkr, mkt_prc)
        bkr.execute(odrs_map) if len(odrs_map.get_map()) > 0 else None
        # self._update_orders(mkt_prc)

    def _try_buy(self, bkr: Broker, mkt_prc: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs_map = Map()
        period = 1
        _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
        if (_slope > 0) and (period in mkt_prc.get_minimums()):
            _ps_avg = self._get_config(self._CONF_PS_AVG)
            _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
            if _ms >= _ps_avg:
                # buy order
                b_odr = self._new_buy_order(bkr)
                odrs_map.put(b_odr, len(odrs_map.get_map()))
                # secure order
                scr_odr = self._new_secure_order(bkr, mkt_prc)
                odrs_map.put(scr_odr, len(odrs_map.get_map()))
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), close=mkt_prc.get_close(), move=Order.MOVE_BUY) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs_map

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
            self._manage_secure_order(bkr, mkt_prc, odrs_map)
        elif _slope < 0:
            self._perform_sell(bkr, mkt_prc, odrs_map)
        # Save in files
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(**vars(), move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs_map
    '''

    def _get_peak_since_buy(self, mkt_prc: MarketPrice) -> [int, None]:
        """
        To get the period of the maximum price in MarketPrice\n
        :param mkt_prc: market prices
        :return: period of the maximum price in MarketPrice
        """
        last_odr = self._get_orders().get_last_execution()
        if last_odr is None:
            raise Exception("Last order completed can't be empty")
        buy_time = last_odr.get_execution_time()
        time = mkt_prc.get_time()
        prd_time = mkt_prc.get_period_time()
        buy_prd = (int((time - buy_time) / prd_time) + 1)
        closes = mkt_prc.get_closes()
        nb_prd = len(closes)
        if buy_prd >= nb_prd:
            peak_x = self.get_maximum(tuple(closes), 0, nb_prd - 1)
        else:
            peak_x = self.get_maximum(tuple(closes), 0, buy_prd)
        return peak_x

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
        close = mkt_prc.get_close()
        buy_odr_prc = buy_odr.get_execution_price().get_value()
        if (peak_max_drop is not None) \
                and (close > buy_odr_prc) \
                and (close <= peak_max_drop):
            self._sell(bkr, odrs)
        else:
            _slope = mkt_prc.get_indicator(MarketPrice.INDIC_ACTUAL_SLOPE)
            if (buy_odr_prc < close) and (_slope > 0):
                self._manage_secure_order(bkr, mkt_prc, odrs)
            elif _slope < 0:
                # self._check_sell(bkr, mkt_prc, odrs)
                vars_rtn = self._check_sell(bkr, mkt_prc, odrs)
        # Save in files
        _stage = Config.get(Config.STAGE_MODE)
        my_vars = {**vars(), **vars_rtn}
        self._save_move(**my_vars, move=Order.MOVE_SELL) \
            if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2) else None
        return odrs

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

    def _manage_secure_order(self, bkr: Broker, mkt_prc: MarketPrice, odrs_map: Map) -> None:
        old_scr_odr = self._get_secure_order()
        bkr.cancel(old_scr_odr) if old_scr_odr.get_status() != Order.STATUS_COMPLETED else None
        scr_odr = self._new_secure_order(bkr, mkt_prc)
        odrs_map.put(scr_odr, len(odrs_map.get_map()))

    @staticmethod
    def _save_move(**params):
        p = Config.get(Config.DIR_SAVE_MOVES)
        params_map = Map(params)
        closes = params_map.get('mkt_prc').get_closes()
        closes_str = [str(v) for v in closes]
        market_json = ModelFeature.json_encode(closes_str)
        params_map.put(market_json, 'market_json')
        fields = [
            'close',
            'move',
            "peak",
            "peak_max_drop",
            '_ms',
            '_dr',
            '_slope',
            'buy_odr_prc',
            '_max_dr',
            '_ps_avg',
            '_ds_avg',
            'market_json'
        ]
        rows = [{k: (params_map.get(k) if params_map.get(k) is not None else '—') for k in fields}]
        """
        row = {}
        for k, v in params_map.get_map().items():
            tp = type(v)
            if (tp == str) or (tp == int) or (tp == float) or (tp == bool):
                row[k] = v
        rows = [row]
        fields = list(row.keys())
        """
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    def _save_capital(self, close: Decimal):
        p = Config.get(Config.DIR_SAVE_CAPITAL)
        cap = self._get_capital()
        rows = [{
            'close': close,
            'initial': cap.__str__(),
            'left': self._get_sell_quantity().__str__(),
            'right': self._get_buy_capital().__str__()
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
