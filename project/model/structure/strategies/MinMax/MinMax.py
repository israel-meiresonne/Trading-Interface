from decimal import Decimal

from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.Asset import Asset
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Price import Price


class MinMax(Strategy):
    _CONF_MAKET_PRICE = "config_market_price"
    _CONF_PS_AVG = "CONF_PS_AVG"
    _CONF_MAX_DR = "CONF_MAX_DR"
    _CONF_DS_AVG = "CONF_DS_AVG"

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
        self.__orders = Map()
        self.__secure_order = None

    """
    def get_order(self, mkpc: MarketPrice) -> Order:
        prms = {
            Map.pair: Pair("BTC", "USDT"),
            Map.move: Order.MOVE_BUY,
            Map.market: Price(round(random() * 1000, 2), "USDT"),
        }
        odr = BinanceOrder(Order.TYPE_MARKET, prms)
        return odr
    """

    def _import_moduls(self, instucs: list) -> None:
        imports = self._get_imports()
        for instuc in instucs:
            if instuc not in imports:
                exec(instuc)
                self._add_import(instuc)

    def __set_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            bkr_cls = bkr.__class__.__name__
            rq_cls = BrokerRequest.get_request_class(bkr_cls)
            self._import_moduls([f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}"])
            rq_prms = Map({
                Map.pair: self.get_pair(),
                Map.period: 60,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 360
            })
            bkr_rq = eval(rq_cls+'(BrokerRequest.RQ_MARKET_PRICE, rq_prms)')
            bkr.get_market_price(bkr_rq)
            mkt_prc = bkr_rq.get_market_price()
            conf_mkt_prc = Map({
                Map.pair: self.get_pair(),
                Map.period: 60,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 20
            })
            configs = Map({
                self._CONF_MAKET_PRICE: conf_mkt_prc,
                self._CONF_PS_AVG: mkt_prc.get_indicator(MarketPrice.INDIC_PS_AVG),
                self._CONF_MAX_DR: Decimal('-0.005'),
                self._CONF_DS_AVG: mkt_prc.get_indicator(MarketPrice.INDIC_DS_AVG)
            })
            self._set_configs(configs)
            if self._get_capital() is None:
                rq_prms = Map({
                    Map.account: BrokerRequest.ACCOUNT_MAIN,
                    Map.begin_time: None,
                    Map.end_time: None,
                    Map.number: 1,
                    Map.timeout: None,
                })
                snap_rq = eval(rq_cls+'(BrokerRequest.RQ_ACCOUNT_SNAP, rq_prms)')
                bkr.get_account_snapshot(snap_rq)
                accounts = snap_rq.get_account_snapshot()
                right = self.get_pair().get_right()
                cap = accounts.get(right.get_symbol())
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

    def _get_orders(self) -> Map:
        return self.__orders

    def _add_order(self, odr: Order) -> None:
        odrs = self._get_orders()
        odrs.put(odr, len(odrs.get_map()))

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
        if len(odrs.get_map()) > 0:
            odr_sum = Order.sum_orders(odrs)
            b_cpt += odr_sum.get(Map.right).get_value()
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
        if len(odrs.get_map()) > 0:
            odr_sum = Order.sum_orders(odrs)
            s_qty += odr_sum.get(Map.left).get_value()
        l_sbl = self.get_pair().get_left().get_symbol()
        return Price(s_qty, l_sbl)

    def _has_position(self) -> bool:
        """
        Check if holding a left position\n
        :return: True if holding else False
        """
        has_pos = False
        odrs = self._get_orders()
        ks = odrs.get_keys()
        ks.reverse()
        for k in ks:
            odr = odrs.get(k)
            print(f"{k}: {odr.get_move()}")
            if odr.get_status() == Order.STATUS_COMPLETED:
                has_pos = odr.get_move() == Order.MOVE_BUY
                break
        return has_pos

    def _get_market_price(self, bkr: Broker) -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        bkr_cls = bkr.__class__.__name__
        rq_cls = BrokerRequest.get_request_class(bkr_cls)
        mkt_prms = self._get_config(self._CONF_MAKET_PRICE)
        # self._import_moduls([f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}"])
        exec(f"from model.API.brokers.{bkr_cls}.{rq_cls} import {rq_cls}")
        rq_mkt = eval(rq_cls+"('"+BrokerRequest.RQ_MARKET_PRICE+"', mkt_prms)")
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
        odr = eval(odr_cls+"('"+Order.TYPE_MARKET+"', odr_prms_map)")
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
        odr = eval(bkr_cls+"Order('"+Order.TYPE_MARKET+"', odr_prms)")
        self._add_order(odr)
        return odr

    def _new_secure_order(self, bkr: Broker, mkt_prc: MarketPrice) -> Order:
        bkr_cls = bkr.__class__.__name__
        odr_cls = bkr_cls + Order.__name__
        pr = self.get_pair()
        sum_odr = Order.sum_orders(self._get_orders())
        qty = sum_odr.get(Map.left)
        stop = mkt_prc.get_futur_price(self._get_config(self._CONF_MAX_DR))
        odr_prms = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pr.get_right().get_symbol()),
            Map.quantity: qty
        })
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls+"Order('"+Order.TYPE_STOP+"', odr_prms)")
        self._add_order(odr)
        return odr

    def trade(self, bkr: Broker) -> None:
        self.__set_strategy(bkr)
        if self._has_position():
            odrs_map = self._try_sell(bkr)
        else:
            odrs_map = self._try_buy(bkr)
        bkr.execute(odrs_map) if len(odrs_map.get_map()) > 0 else None

    def _try_buy(self, bkr: Broker) -> Map:
        """
        To try to buy position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        odrs_map = Map()
        mkt_prc = self._get_market_price(bkr)
        period = 1
        if(mkt_prc.get_delta_price() > 0) and (period in mkt_prc.get_minimums()):
            _ps_avg = self._get_config(self._CONF_PS_AVG)
            _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
            if _ms >= _ps_avg:
                # buy order
                b_odr = self._new_buy_order(bkr)
                odrs_map.put(b_odr, len(odrs_map.get_map()))
                # secure order
                scr_odr = self._new_secure_order(bkr, mkt_prc)
                odrs_map.put(scr_odr, len(odrs_map.get_map()))
        return odrs_map

    def _try_sell(self, bkr: Broker) -> Map:
        """
        To try to sell position\n
        :param bkr: an access to a Broker's API
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        odrs_map = Map()
        mkt_prc = self._get_market_price(bkr)
        delta_prc = mkt_prc.get_delta_price()
        if delta_prc > 0:
            old_scr_odr = self._get_secure_order()
            bkr.cancel(old_scr_odr)
            scr_odr = self._new_secure_order(bkr, mkt_prc)
            odrs_map.put(scr_odr, len(odrs_map.get_map()))
        elif delta_prc < 0:
            _dr = mkt_prc.get_indicator(MarketPrice.INDIC_DR)
            _max_dr = self._get_config(self._CONF_MAX_DR)
            _ms = mkt_prc.get_indicator(MarketPrice.INDIC_MS)
            _ds_avg = self._get_config(self._CONF_DS_AVG)
            if (_dr <= _max_dr) or (_ms >= _ds_avg):
                old_scr_odr = self._get_secure_order()
                bkr.cancel(old_scr_odr)
                s_odr = self._new_sell_order(bkr)
                odrs_map.put(s_odr, len(odrs_map.get_map()))
        return odrs_map
