from abc import ABC, abstractmethod

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class TraderClass(Strategy, MyJson, ABC):
    _MARKET_PRICE_N_PERIOD = 1000
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
        rtn = _MF.keys_exist([Map.period], params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required.")
        self.__marketprices = None
        self.__buy_order = None
        self.__secure_order = None
        self.__broker = None

    def _reset_marketprices(self) -> None:
        self.__marketprices = None

    def _get_marketprices(self) -> Map:
        """
        To get collection of MarketPrice

        NOTE: marketprices[period{int}] => {MarketPrice}

        Returns:
        --------
        return: Map
            Collection of MarketPrice
        """
        if self.__marketprices is None:
            self.__marketprices = Map()
        return self.__marketprices

    def get_marketprice(self, period: int, n_period: int = None, bkr: Broker = None) -> MarketPrice:
        marketprices = self._get_marketprices()
        if period not in marketprices.get_keys():
            bkr = bkr if bkr is not None else self.get_broker()
            pair = self.get_pair()
            n_period = n_period if n_period is not None else self.get_marketprice_n_period()
            marketprice = self._market_price(bkr, pair, period, n_period)
            marketprices.put(marketprice, period)
        return marketprices.get(period)

    def _reset_buy_order(self) -> None:
        self.__buy_order = None

    def _set_buy_order(self, buy_order: Order) -> None:
        self.__buy_order = buy_order

    def get_buy_order(self) -> Order:
        """
        To get executed Order of the last buy
        """
        return self.__buy_order

    def _reset_secure_order(self) -> None:
        self.__secure_order = None

    def _set_secure_order(self, odr: Order) -> None:
        self.__secure_order = odr

    def _get_secure_order(self) -> Order:
        return self.__secure_order
    
    def _reset_broker(self) -> None:
        self.__broker = None

    def _set_broker(self, bkr: Broker) -> None:
        self.__broker = bkr

    def get_broker(self) -> Broker:
        return self.__broker

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
    
    def _secure_order_price(self, bkr: Broker, marketprice: MarketPrice) -> Price:
        """
        To get Price at witch place secure Order

        NOTE: by default use get_max_loss() with buy Price as reference

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API
        marketprice: MarketPrice
            MarketPrice history

        Returns:
        --------
        return: Price
            Price (in right Strategy's right Asset) at witch place secure Order
        """
        pair = self.get_pair()
        # Get stop price
        buy_price = self._get_orders().get_last_execution().get_execution_price()
        max_loss = self.get_max_loss()
        stop = buy_price * (1 + max_loss)
        return Price(stop, pair.get_right().get_symbol())

    def _new_secure_order(self, bkr: Broker, marketprice: MarketPrice) -> Order:
        """
        To generate a STOP LIMIT order to sell at Price returned by function _secure_order_price()

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API
        marketprice: MarketPrice
            MarketPrice history
        
        Raises:
        -------
        raise: Exception
            If Strategy has not position to secure (must buy before)
            If stop price hasn't Strategy's right Asset
        
        Return:
        -------
        return: Order
            The secure Order to execute
        """
        if not self._has_position():
            raise Exception("Strategy must have position to generate secure Order")
        _bkr_cls = bkr.__class__.__name__
        pair = self.get_pair()
        # Get Quantity
        sum_odr = self._get_orders().get_sum()
        qty = sum_odr.get(Map.left)
        qty = Price(qty.get_value(), qty.get_asset().get_symbol())
        #  Generate Order
        stop = self._secure_order_price(bkr, marketprice)
        if stop.get_asset() != pair.get_right():
            raise Exception(f"Stop price '{stop}' must be in Strategy's right asset '{pair.__str__().upper()}'")
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.stop: stop,
            Map.limit: stop,
            Map.quantity: qty
        })
        odr = Order.generate_broker_order(_bkr_cls, Order.TYPE_STOP_LIMIT, odr_params)
        self._add_order(odr)
        self._set_secure_order(odr)
        return odr

    def trade(self, bkr: Broker) -> int:
        # Update nb trade done
        self._update_nb_trade()
        # Set Broker
        self._set_broker(bkr)
        # Get Market
        period = self.get_period()
        marketprice = self.get_marketprice(period)
        # Update Orders
        self._update_orders(bkr, marketprice)
        # Get And Execute Orders
        if self._has_position():
            executions = self._try_sell(marketprice, bkr)
        else:
            self._reset_secure_order()
            self._reset_buy_order()
            executions = self._try_buy(marketprice, bkr)
        self.execute(bkr, executions, marketprice)
        # Backup Capital
        self._save_capital(close=marketprice.get_close(), time=marketprice.get_time())
        # Reset
        self._reset_marketprices()
        self._reset_broker()
        return Strategy.get_bot_sleep_time()

    def stop_trading(self, bkr: Broker) -> None:
        if self._has_position():
            executions = Map()
            self._sell(executions)
            self.execute(bkr, executions)
        marketprice = self.get_marketprice(self.get_period(), bkr=bkr)
        self._update_orders(bkr, marketprice)
        self._save_capital(close=marketprice.get_close(), time=marketprice.get_time())

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
                self._set_buy_order(buy_order)
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
        if not self._has_position():
            self._reset_secure_order()
            self._reset_buy_order()

    @abstractmethod
    def _try_buy(self, market_price: MarketPrice, bkr: Broker) -> Map:
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
    def _try_sell(self, market_price: MarketPrice, bkr: Broker) -> Map:
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

    def _json_encode_prepare(self) -> None:
        self._reset_marketprices()

    # ——————————————— STATIC METHOD DOWN ———————————————

    @staticmethod
    @abstractmethod
    def get_max_loss() -> float:
        pass

    @staticmethod
    def get_marketprice_n_period() -> int:
        """
        To get number of period to retrieve from Broker's API

        Returns:
        --------
        return: int
            The number of period to retrieve from Broker's API
        """
        return TraderClass._MARKET_PRICE_N_PERIOD

    @staticmethod
    def get_period_ranking(bkr: Broker, pair: Pair) -> Map:
        pass

    @staticmethod
    def performance_get_rates(market_price: MarketPrice) -> list:
        pass

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        pass

   # ——————————————— SAVE DOWN ———————————————

    @abstractmethod
    def save_move(self, **agrs):
        pass

    def _print_move(self, datas: Map) -> None:
        pair = self.get_pair()
        datas = Map({
            Map.id: self.get_id(),
            'class': self.__class__.__name__,
            'nb_trade': self.get_nb_trade(),
            Map.pair: pair,
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            **datas.get_map()
        })
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
            'nb_trade': self.get_nb_trade(),
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
