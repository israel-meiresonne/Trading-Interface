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


class Floor(Strategy):
    # Constants
    _CONF_MAKET_PRICE = "config_market_price"
    _CONF_MAX_DR = "CONF_MAX_DR"
    _CONST_RSI_ENTRY_TRIGGER = "RSI_ENTRY_TRIGGER"
    _CONST_MIN_OUT_FLOOR = "MIN_OUT_FLOOR"
    _CONST_RSI_FLOORS = "RSI_FLOORS"
    # Executions
    _EXEC_BUY = "EXEC_BUY"
    _EXEC_PLACE_SECURE = "EXEC_PLACE_SECURE"
    _EXEC_SELL = "EXEC_SELL"
    _EXEC_CANCEL_SECURE = "EXEC_CANCEL_SECURE"

    def __init__(self, params: Map):
        super().__init__(params)
        self.__configs = None
        self.__secure_order = None
        rtn = _MF.keys_exist([Map.period], params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required.")
        self.__best_period = params.get(Map.period)
        # Strategy
        self.up_min_floor_once = None

    def _init_strategy(self, bkr: Broker) -> None:
        if self.__configs is None:
            # Set Configs
            self._init_constants(bkr)
            # Set Capital
            # self._init_capital(bkr)

    def _init_capital(self, bkr: Broker) -> None:
        """
        _stage = Config.get(Config.STAGE_MODE)
        cap = None
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            cap = Price(1000, self.get_pair().get_right().get_symbol())
        elif _stage == Config.STAGE_3:
            pass
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        self._set_capital(cap) if cap is not None else None
        """
        pass

    def _init_constants(self, bkr: Broker) -> None:
        _stage = Config.get(Config.STAGE_MODE)
        best_period = self.get_best_period()
        self.__configs = Map({
            self._CONF_MAKET_PRICE: Map({
                Map.pair: self.get_pair(),
                Map.period: best_period,
                Map.begin_time: None,
                Map.end_time: None,
                Map.number: 100 if _stage == Config.STAGE_1 else 250
            }),
            self._CONF_MAX_DR: -0.1,
            self._CONST_RSI_ENTRY_TRIGGER: 25,
            self._CONST_MIN_OUT_FLOOR: 30,
            self._CONST_RSI_FLOORS: [i * 10 for i in range(11)]
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
    """
    def set_best_period(self, best: int) -> None:
        self.__best_period = best
    """

    def get_best_period(self) -> int:
        """
        _stage = Config.get(Config.STAGE_MODE)
        if _stage == Config.STAGE_1:
            # self.set_best_period(60) if self.__best_period is None else None
            return self.__best_period
        elif (_stage == Config.STAGE_2) or (_stage == Config.STAGE_3):
            if self.__best_period is None:
                raise Exception(f"Strategy MinMax's best period must be set before.")
            return self.__best_period
        """
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

    '''
    def _has_position(self) -> bool:
        """
        Check if holding a left position\n
        :return: True if holding else False
        """
        odrs = self._get_orders()
        return odrs.has_position()
    '''

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
        """
        odr_cls = bkr_cls + Order.__name__
        """
        pair = self.get_pair()
        pr_right = pair.get_right()
        b_cpt = self._get_buy_capital()
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: Price(b_cpt.get_value(), pr_right.get_symbol())
        })
        """
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(odr_cls + "('" + Order.TYPE_MARKET + "', odr_prms_map)")
        """
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_MARKET, odr_params)
        self._add_order(odr)
        return odr

    def _new_sell_order(self, bkr: Broker) -> Order:
        _bkr_cls = bkr.__class__.__name__
        # odr_cls = bkr_cls + Order.__name__
        pair = self.get_pair()
        pr_left = pair.get_left()
        s_cpt = self._get_sell_quantity()
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: Price(s_cpt.get_value(), pr_left.get_symbol())
        })
        """
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls + "Order('" + Order.TYPE_MARKET + "', odr_params)")
        """
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
        stop = super_trend * (1 + max_drop_rate)
        # stop = super_trend
        odr_params = Map({
            Map.pair: pr,
            Map.move: Order.MOVE_SELL,
            Map.stop: Price(stop, pr.get_right().get_symbol()),
            Map.limit: Price(stop, pr.get_right().get_symbol()),
            Map.quantity: qty
        })
        """
        exec(f"from model.API.brokers.{bkr_cls}.{odr_cls} import {odr_cls}")
        odr = eval(bkr_cls + "Order('" + Order.TYPE_STOP_LIMIT + "', odr_params)")
        """
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
        # Backup Capital
        self._save_capital(close=mkt_prc.get_close(), time=mkt_prc.get_time())
        # Get And Execute Orders
        if self._has_position():
            executions = self._try_sell(mkt_prc)
        else:
            executions = self._try_buy(mkt_prc)
        self.execute(bkr, executions, mkt_prc)
        return Strategy.get_bot_sleep_time()

    def stop_trading(self, bkr: Broker) -> None:
        if self._has_position():
            executions = Map()
            self._sell(executions)
            self.execute(bkr, executions)

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
                if secure_odr_status == Order.STATUS_SUBMITTED:  # or (secure_odr_status == Order.STATUS_PROCESSING):
                    bkr.cancel(old_secure_order)
            else:
                raise Exception(f"Unknown execution '{execution}'.")

    # V1.0: BUY
    # '''
    def _try_buy(self, market_price: MarketPrice) -> Map:
        """
        To try to buy position\n
        :param market_price: market price
        :return: set of order to execute
                 Map[index{int}] => {Order}
        """
        executions = Map()
        # Extract lists
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        # Get constants
        _rsi_entry_trigger = self._get_constant(Floor._CONST_RSI_ENTRY_TRIGGER)
        # RSI
        prev_rsi = rsis[-2]
        rsi = rsis[-1]
        rsi_ok = (prev_rsi <= _rsi_entry_trigger) and (rsi > prev_rsi)
        # Check buy
        if rsi_ok:
            self._buy(executions)
        # Backup
        """
        _stage = Config.get(Config.STAGE_MODE)
        fields = [
            "class",
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            # Buy
            'rsi_ok',
            'rsi_downstairs_ok',
            'up_min_floor_once',
            'last_floor',
            'rsi',
            'prev_rsi',
            'rsi_entry_trigger',
            '_min_out_floor',
            'super_trend',
            # Lists
            'rsis',
            'super_trends',
            '_floors'
        ]
        """
        self._save_move(pair=self.get_pair(), **vars(), move=Order.MOVE_BUY)
        return executions

    # TEST STAGE_3
    """
    def _try_buy(self, mkt_prc: MarketPrice) -> Map:
        executions = Map()
        self._buy(executions)
        # self._move_up_secure_order(bkr, mkt_prc, executions)
        # self._sell(bkr, executions)
        return executions

    def _try_sell(self, mkt_prc: MarketPrice) -> Map:
        executions = Map()
        return executions
    """

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

    # ——————————————————————— BUY UP ————————————————————————————————————————————
    # ——————————————————————— SELL DOWN —————————————————————————————————————————

    # V1.0: SELL
    # '''
    def _try_sell(self, market_price: MarketPrice) -> Map:
        """
        To try to sell position\n
        :param market_price: market prices
        :return: set of order to execute
                 Map[symbol{str}] => {Order}
        """
        executions = Map()
        # Extract lists
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        # Get constants
        _min_out_floor = self._get_constant(Floor._CONST_MIN_OUT_FLOOR)
        _floors = self._get_constant(Floor._CONST_RSI_FLOORS)
        # RSI downstairs
        rsi_downstairs_ok = False
        rsi = rsis[-1]
        prev_rsi = rsis[-2]
        self.up_min_floor_once = rsi > _min_out_floor \
            if (self.up_min_floor_once is None) or (not self.up_min_floor_once) else self.up_min_floor_once
        if self.up_min_floor_once:
            last_floor = _floors[Floor._get_floor_index(prev_rsi, _floors)]
            rsi_downstairs_ok = (last_floor >= _min_out_floor) and (rsi < last_floor)

        """
        # Secure Order
        secure_odr_prc = self._get_secure_order().get_stop_price().get_value()
        stop_base_prc = secure_odr_prc / (1 + self._get_constant(self._CONF_MAX_DR))
        """
        # CHECK
        if rsi_downstairs_ok:
            self._sell(executions)
            self.up_min_floor_once = None
        # elif mkt_prc.get_close() > stop_base_prc:
        # elif closes_supers[0] > stop_base_prc:
        #     self._move_up_secure_order(executions)
        # Backup
        _stage = Config.get(Config.STAGE_MODE)
        self._save_move(pair=self.get_pair(), **vars(), move=Order.MOVE_SELL, up_min_floor_once=self.up_min_floor_once)
        return executions

    # '''

    def _sell(self, executions: Map) -> None:
        """
        To generate sell Order\n
        NOTE: its cancel secure Order and generate a sell Order\n
        :param executions: where to place generated Order
        """
        # Cancel Secure Order
        # executions.put(self._EXEC_CANCEL_SECURE, len(executions.get_map()))
        # Sell
        executions.put(self._EXEC_SELL, len(executions.get_map()))

    def _move_up_secure_order(self, executions: Map) -> None:
        """
        To move up the secure Order\n
        :param executions: market price
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
    def _save_move(pair: Pair, **params):
        from model.structure.strategies.MinMax.MinMax import MinMax
        MinMax.save_move(pair, **params)
        '''
        p = Config.get(Config.DIR_SAVE_MOVES)
        # pair = self.get_pair()
        p = p.replace('$pair', pair.__str__().replace('/', '_').upper())
        params_map = Map(params)
        market_price = params_map.get('market_price')
        closes = market_price.get_closes()
        closes_str = [str(v) for v in closes]
        market_json = _MF.json_encode(closes_str)
        params_map.put(market_json, 'market_json')
        params_map.put(_MF.unix_to_date(market_price.get_time()), Map.time)
        params_map.put(market_price.get_rsis()[0], Map.rsi)
        params_map.put(market_price.get_rsis(), 'rsis')
        params_map.put(market_price.get_tsis(), 'tsis')
        params_map.put(market_price.get_close(), Map.close)
        params_map.put(market_price.get_super_trend(), 'super_trends')
        params_map.put(market_price.get_super_trend()[0], 'super_trend')
        params_map.put(Floor.__name__, "class")
        params_map.put(_MF.unix_to_date(_MF.get_timestamp()), Map.date)
        params_map.put(pair, Map.pair)
        # """
        fields = [
            "class",
            Map.pair,
            Map.date,
            Map.time,
            'close',
            'move',
            'secure_odr_prc',
            'stop_base_prc',
            'super_trend',
            # Buy
            'MinMax->',
            'close_trend_ok',
            'is_above_switch',
            '_last_red_close',
            '<-MinMax',
            'Floor->',
            'rsi_ok',
            'rsi_downstairs_ok',
            'up_min_floor_once',
            'last_floor',
            'rsi',
            'prev_rsi',
            'rsi_entry_trigger',
            '_min_out_floor',
            '<-Floor',
            # Lists
            'rsis',
            'super_trends',
            '_floors'
        ]
        # """
        for k, v in params_map.get_map().items():
            if isinstance(v, float):
                params_map.put(_MF.float_to_str(v), k)
        rows = [{k: (params_map.get(k) if params_map.get(k) is not None else '—') for k in fields}]
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
        '''

    def _save_capital(self, close: float, time: int) -> None:
        p = Config.get(Config.DIR_SAVE_CAPITAL)
        p = p.replace('$pair', self.get_pair().__str__().replace('/', '_').upper())
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
            "class": Floor.__name__,
            Map.date: _MF.unix_to_date(_MF.get_timestamp(), _MF.FORMAT_D_H_M_S),
            Map.time: _MF.unix_to_date(time, _MF.FORMAT_D_H_M_S),
            Map.period: int(self.get_best_period()) / 60,
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
        def float_to_str(number: float) -> str:
            return str(number).replace(".", ",")

        rows = []
        base = {
            Map.pair: ranking.get(Map.pair),
            Map.fee: float_to_str(ranking.get(Map.fee)),
            Map.number: ranking.get(Map.number)
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
        FileManager.write_csv(path, fields, rows, overwrite=False)

    # ——————————————— STATIC METHOD DOWN ———————————————

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        stg_name = Floor.__name__
        minute = 60
        periods = [minute, minute * 3, minute * 5, minute * 15, minute * 30, minute * 60]
        nb_period = 1000
        period_ranking = Strategy.get_top_period(bkr, stg_name, pair, periods, nb_period)
        Floor._save_period_ranking(period_ranking)
        return period_ranking

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        # Init
        perf_rates = []
        buy_price = None
        floors = [i * 10 for i in range(11)]
        rsi_entry_trigger = 25
        min_out_floor = 30
        up_min_floor_once = None
        # Extract lists
        times = list(market_price.get_times())
        times.reverse()
        closes = list(market_price.get_closes())
        closes.reverse()
        rsis = list(market_price.get_rsis())
        rsis.reverse()
        # Print
        for i in range(len(rsis)):
            rsi = rsis[i]
            last_rsi = rsis[i - 1] if i > 0 else None
            if (buy_price is None) \
                    and ((rsi is not None)
                         and (last_rsi is not None)) and ((last_rsi <= rsi_entry_trigger) and (rsi > last_rsi)):
                buy_price = closes[i]
            elif buy_price is not None:
                up_min_floor_once = rsi > min_out_floor if (up_min_floor_once is None) or (
                    not up_min_floor_once) else up_min_floor_once
                if up_min_floor_once:
                    last_floor = floors[Floor._get_floor_index(last_rsi, floors)]
                    if (last_floor >= min_out_floor) and (rsi < last_floor):
                        sell_price = closes[i]
                        perf_rate = sell_price / buy_price - 1
                        perf_rates.append(perf_rate)
                        buy_price = None
                        up_min_floor_once = None
                        last_floor = None
                        perf_rate = None
                        sell_price = None
        return perf_rates

    @staticmethod
    def _get_floor_index(val: float, levels: List[int]) -> int:
        idx = None
        for i in range(len(levels)):
            if val < levels[i]:
                idx = i - 1
                break
        return idx
