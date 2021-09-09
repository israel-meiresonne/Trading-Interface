from abc import ABC, abstractmethod

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class TraderClass(Strategy, MyJson, ABC):
    _CONF_MAKET_PRICE = "config_market_price"
    _CONF_MAX_DR = "CONF_MAX_DR"
    _EXEC_BUY = "EXEC_BUY"
    _EXEC_PLACE_SECURE = "EXEC_PLACE_SECURE"
    _EXEC_SELL = "EXEC_SELL"
    _EXEC_CANCEL_SECURE = "EXEC_CANCEL_SECURE"

    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:           {Strategy.__init__()}   # Same structure
               params[Map.period]:  {int}                   # Period interval in second
        """
        super().__init__(params)
        self.__configs = None
        self.__secure_order = None
        self._last_red_close = None
        self._last_dropping_close = None
        rtn = _MF.keys_exist([Map.period], params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required.")

    def _init_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            self._init_constants(bkr)

    def _init_capital(self, bkr: Broker) -> None:
        pass

    def _init_constants(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        period = self.get_period()
        self.__configs = Map({
            self._CONF_MAKET_PRICE: Map({
                Map.pair: self.get_pair(),
                Map.period: period,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 100 if _stage == Config.STAGE_1 else 250
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

    def _reset_secure_order(self) -> None:
        self.__secure_order = None

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

    def _get_market_price(self, bkr: Broker) -> MarketPrice:
        """
        To request MarketPrice to Broker\n
        :param bkr: an access to Broker's API
        :return: MarketPrice
        """
        _bkr_cls = bkr.__class__.__name__
        mkt_prms = self._get_constant(self._CONF_MAKET_PRICE)
        bkr_rq = bkr.generate_broker_request(_bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_prms)
        bkr.request(bkr_rq)
        return bkr_rq.get_market_price()

    def _new_buy_order(self, bkr: Broker) -> Order:
        _bkr_cls = bkr.__class__.__name__
        pair = self.get_pair()
        pr_right = pair.get_right()
        b_cpt = self._get_buy_capital()
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(b_cpt.get_value(), pr_right.get_symbol())
        })
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_MARKET, odr_params)
        self._add_order(odr)
        return odr

    def _new_sell_order(self, bkr: Broker) -> Order:
        _bkr_cls = bkr.__class__.__name__
        pair = self.get_pair()
        pr_left = pair.get_left()
        s_cpt = self._get_sell_quantity()
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: Price(s_cpt.get_value(), pr_left.get_symbol())
        })
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_MARKET, odr_params)
        self._add_order(odr)
        return odr

    def _new_secure_order(self, bkr: Broker, mkt_prc: MarketPrice) -> Order:
        _bkr_cls = bkr.__class__.__name__
        # odr_cls = bkr_cls + Order.__name__
        pr = self.get_pair()
        max_drop_rate = self._get_constant(self._CONF_MAX_DR)
        # max_rate = 1
        if self._has_position():
            sum_odr = self._get_orders().get_sum()
            qty = sum_odr.get(Map.left)
            qty = Price(qty.get_value(), qty.get_asset().get_symbol())
        else:
            close_val = mkt_prc.get_close()
            b_cap = self._get_buy_capital()
            qty_val = b_cap.get_value() / close_val
            qty = Price(qty_val, pr.get_left().get_symbol())
        super_trend = mkt_prc.get_super_trend()[0]
        stop = super_trend * (1 + max_drop_rate)
        # stop = super_trend
        odr_params = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pr.get_right().get_symbol()),
            Map.limit: Price(stop, pr.get_right().get_symbol()),
            Map.quantity: qty
        })
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_STOP_LIMIT, odr_params)
        self._add_order(odr)
        self._set_secure_order(odr)
        return odr

    def trade(self, bkr: Broker) -> int:
        _stage = Config.get(Config.STAGE_MODE)
        # Init Strategy in First turn
        self._init_strategy(bkr)
        # Get Market
        mkt_prc = self._get_market_price(bkr)
        # Update Orders
        self._update_orders(bkr, mkt_prc)
        # Get And Execute Orders
        if self._has_position():
            executions = self._try_sell(mkt_prc)
        else:
            self._reset_secure_order()
            executions = self._try_buy(mkt_prc)
        self.execute(bkr, executions, mkt_prc)
        # Backup Capital
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())
        return Strategy.get_bot_sleep_time()

    def stop_trading(self, bkr: Broker) -> None:
        if self._has_position():
            executions = Map()
            self._sell(executions)
            self.execute(bkr, executions)
        mkt_prc = self._get_market_price(bkr)
        self._update_orders(bkr, mkt_prc)
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())

    def execute(self, bkr: Broker, executions: Map, mkt_prc: MarketPrice = None) -> None:
        """
        To executions to submit to Broker's API\n
        :param bkr: Access to a Broker's API
        :param executions: Executions to execute
        :param mkt_prc: Market's prices
        """
        for idx, execution in executions.get_map().items():
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
                if secure_odr_status == Order.STATUS_SUBMITTED:
                    bkr.cancel(old_secure_order)
            else:
                raise Exception(f"Unknown execution '{execution}'.")

    @abstractmethod
    def _try_buy(self, market_price: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param market_price: market price
        :return: set of execution instruction
                 Map[index{int}]:   {str}
        """
        pass

    def _buy(self, executions: Map) -> None:
        """
        To add buy execution\n
        NOTE: its include Buy Order and a secure Order\n
        :param executions: where to place generated Order
        """
        # Buy Order
        executions.put(self._EXEC_BUY, len(executions.get_map()))
        # Place Secure order
        # executions.put(self._EXEC_PLACE_SECURE, len(executions.get_map()))

    def _secure_position(self, executions: Map) -> None:
        # Place Secure order
        executions.put(self._EXEC_PLACE_SECURE, len(executions.get_map()))

    @abstractmethod
    def _try_sell(self, market_price: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param market_price: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        pass

    def _sell(self, executions: Map) -> None:
        """
        To generate sell Order\n
        NOTE: its cancel secure Order and generate a sell Order\n
        :param executions: where to place generated Order
        """
        # Cancel Secure Order
        executions.put(self._EXEC_CANCEL_SECURE, len(executions.get_map())) \
            if self._get_secure_order() is not None else None
        # Sell
        executions.put(self._EXEC_SELL, len(executions.get_map()))

    def _move_up_secure_order(self, executions: Map) -> None:
        """
        To move up the secure Order\n
        :param executions: market price
        :param executions: where to place generated Order
        """
        # Cancel Secure Order
        executions.put(self._EXEC_CANCEL_SECURE, len(executions.get_map()))
        # Place Secure order
        executions.put(self._EXEC_PLACE_SECURE, len(executions.get_map()))

    # ——————————————— SAVE DOWN ———————————————

    @abstractmethod
    def save_move(self, market_price: MarketPrice):
        pass

    def _print_move(self, datas: Map) -> None:
        pair = self.get_pair()
        fields = datas.get_keys()
        rows = [{k: (datas.get(k) if datas.get(k) is not None else '—') for k in fields}]
        path = Config.get(Config.DIR_SAVE_MOVES)
        path = path.replace('$pair', pair.__str__().replace('/', '_').upper())
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    def _save_capital(self, close: float, time: int) -> None:
        p = Config.get(Config.DIR_SAVE_CAPITAL)
        p = p.replace('$pair', self.get_pair().__str__().replace('/', '_').upper())
        cap = self._get_capital()
        r_symbol = cap.get_asset().get_symbol()
        sell_qty = self._get_sell_quantity()
        buy_amount = self._get_buy_capital()
        odrs = self._get_orders()
        positions_value = sell_qty.get_value() * close
        current_capital_val = positions_value + buy_amount.get_value() if sell_qty.get_value() > 0 else buy_amount.get_value()
        roi = current_capital_val / cap.get_value() - 1
        sum_odr = odrs.get_sum() if odrs.get_size() > 0 else None
        fees = sum_odr.get(Map.fee) if sum_odr is not None else Price(0, r_symbol)
        fee_init_capital_rate = fees / cap
        current_capital_obj = Price(current_capital_val, r_symbol)
        rows = [{
            "class": self.__class__.__name__,
            Map.date: _MF.unix_to_date(_MF.get_timestamp(), _MF.FORMAT_D_H_M_S),
            Map.time: _MF.unix_to_date(time, _MF.FORMAT_D_H_M_S),
            Map.period: int(self.get_period()) / 60,
            'close': close,
            'initial': cap,
            'current_capital': current_capital_obj,
            'fees': fees,
            'fee_init_capital_rate': _MF.rate_to_str(fee_init_capital_rate),
            'left': sell_qty,
            'right': buy_amount,
            'positions_value': positions_value,
            Map.roi: _MF.rate_to_str(roi)
        }]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite, make_dir=True)

    @staticmethod
    def _save_period_ranking(ranking: Map) -> None:
        def float_to_str(number: float) -> str:
            return str(number).replace(".", ",")
        rows = []
        base = {
            Map.pair:  ranking.get(Map.pair),
            Map.fee:  float_to_str(ranking.get(Map.fee)),
            Map.number:  ranking.get(Map.number)
        }
        date = _MF.unix_to_date(_MF.get_timestamp())
        for rank, struc in ranking.get(Map.period).items():
            row = {
                Map.date: date,
                f"{Map.sum}_{Map.rank}": rank,
                Map.sum: struc[Map.rank][Map.sum],
                f"{Map.period}_{Map.rank}": struc[Map.rank][Map.period],
                f"{Map.roi}_{Map.rank}": struc[Map.rank][Map.roi],
                **base,
                f"{Map.period}_minutes": int(struc[Map.period] / 60),
                Map.roi: float_to_str(struc[Map.roi]),
                Map.day: float_to_str(struc[Map.day]),
                Map.transaction: _MF.json_encode(struc[Map.transaction]),
                Map.rate: _MF.json_encode(struc[Map.rate])
            }
            rows.append(row)
        path = Config.get(Config.DIR_SAVE_PERIOD_RANKING)
        fields = list(rows[0].keys())
        FileManager.write_csv(path, fields, rows, overwrite=False, make_dir=True)

    # ——————————————— STATIC METHOD DOWN ———————————————

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        pass

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        pass
