from abc import ABC, abstractmethod

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Price import Price
from model.tools.Request import Request
from model.tools.Transaction import Transaction


class Order(Request, Transaction, MyJson, ABC):
    PREFIX_ID = 'odr_'
    # Types
    TYPE_MARKET = "_set_market"
    TYPE_LIMIT = "_set_limit"
    TYPE_STOP = "_set_stop"
    TYPE_STOP_LIMIT = "_set_stop_limit"
    ODR_TYPES = [
        TYPE_MARKET,
        TYPE_LIMIT,
        TYPE_STOP,
        TYPE_STOP_LIMIT
    ]
    # Moves
    MOVE_BUY = "MOVE_BUY"
    MOVE_SELL = "MOVE_SELL"
    _MOVES = [MOVE_BUY, MOVE_SELL]
    # Status
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELED = "CANCELED"
    STATUS_FAILED = "FAILED"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_LIST = [
        STATUS_SUBMITTED,
        STATUS_PROCESSING,
        STATUS_COMPLETED,
        STATUS_CANCELED,
        STATUS_FAILED,
        STATUS_EXPIRED
    ]
    # Constants
    FAKE_FEE = 0.001

    @abstractmethod
    def __init__(self, odr_type: str, params: Map):
        """
        Constructor\n
        :param odr_type: type of Order
        :param params: Order's params
                        params[Map.pair]        => {Pair}
                        params[Map.move]        => {str}
                        params[Map.market]      => {Price}
                        params[Map.limit]       => {Price}
                        params[Map.stop]        => {Price}
                        params[Map.quantity]    => {Price}
                        params[Map.amount]      => {Price}
        """
        super().__init__()
        super()._set_attributs()
        self.__broker_id = None
        self.__type = None
        self.__status = None
        self.__move = None
        self.__market = None
        self._limit = None
        self._stop = None
        self._quantity = None
        self.__amount = None
        self.__order_params = params
        self.__request_params = None
        self.__cancel_request_params = None
        # After Execution Down
        self.__execution_time = None
        self.__execution_price = None
        self.__executed_quantity = None
        self.__executed_amount = None
        self.__fee = None
        self.__trades = None
        pair = params.get(Map.pair)
        self._set_id()
        self._set_settime()
        self._set_type(odr_type)
        self._set_pair(pair)
        self._set_order(params)

    def _set_order(self, params: Map) -> None:
        odr_type = self.get_type()
        qty = params.get(Map.quantity)
        if odr_type == self.TYPE_MARKET:
            self._check_market(params)
            self._set_move(params.get(Map.move))
            self._set_quantity(qty) if qty is not None else None
            self._set_amount(params.get(Map.amount))
        elif odr_type == self.TYPE_STOP:
            self._check_stop(params)
            self._set_move(params.get(Map.move))
            self._set_stop_price(params.get(Map.stop))
            self._set_quantity(qty)
        elif odr_type == self.TYPE_STOP_LIMIT:
            self._check_stop_limit(params)
            self._set_move(params.get(Map.move))
            self._set_stop_price(params.get(Map.stop))
            self._set_limit_price(params.get(Map.limit))
            self._set_quantity(qty)
        else:
            raise Exception(f"This Order type is not supported '{odr_type}'.")

    @staticmethod
    def _check_market(params: Map) -> None:
        # Check Keys
        ks = [Map.pair, Map.move]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a market Order")
        # Check Quantity and Amount
        qty = params.get(Map.quantity)
        amount = params.get(Map.amount)
        if (qty is None) and (amount is None):
            raise ValueError(f"The quantity or amount must be set to make a market Order")
        if (qty is not None) and (amount is not None):
            raise ValueError(f"The quantity and amount can both be set for a market Order")
        pr = params.get(Map.pair)
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        if (qty is not None) and (qty.get_asset().get_symbol() != pr_l_sbl):
            raise ValueError(f"The quantity's asset '{qty.get_asset().get_symbol()}' must"
                             f" be the same that the pair's left asset '{pr_l_sbl}'")
        if (amount is not None) and (amount.get_asset().get_symbol() != pr_r_sbl):
            raise ValueError(f"The amount's asset '{amount.get_asset().get_symbol()}' must"
                             f" be the same that the pair's right asset '{pr_l_sbl}'")

    @staticmethod
    def _check_stop(params: Map) -> None:
        # check params
        ks = [Map.pair, Map.move, Map.stop, Map.quantity]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a stop Order")
        # check logic
        Order._check_logic(params)

    @staticmethod
    def _check_stop_limit(params: Map) -> None:
        # Check params
        ks = [Map.pair, Map.move, Map.stop, Map.limit, Map.quantity]
        rtn = _MF.keys_exist(ks, params.get_map())
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a stop limit Order")
        # Check logic
        Order._check_logic(params)

    @staticmethod
    def _check_logic(params: Map) -> None:
        """
        To check logic of params\n
        """
        move = params.get(Map.move)
        if (move != Order.MOVE_BUY) and (move != Order.MOVE_SELL):
            raise ValueError(f"This Order move '{move}' is not supported.")
        pr = params.get(Map.pair)
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        stop = params.get(Map.stop)
        if stop is not None:
            stop_sbl = stop.get_asset().get_symbol()
            if stop_sbl != pr_r_sbl:
                raise ValueError(f"Stop price's asset '{stop_sbl}' must the same "
                                 f"that the right asset of the pair '{pr}'")
        limit = params.get(Map.limit)
        if limit is not None:
            limit_sbl = limit.get_asset().get_symbol()
            if limit_sbl != pr_r_sbl:
                raise ValueError(f"Limit price's asset '{limit_sbl}' must the same "
                                 f"that the right asset of the pair '{pr}'")
        qty = params.get(Map.quantity)
        if qty is not None:
            qty_sbl = qty.get_asset().get_symbol()
            if qty_sbl != pr_l_sbl:
                raise ValueError(f"Quantity's asset '{qty_sbl}' must the same "
                                 f"that the left asset of the pair '{pr}'")

    # ——————————————————————————————————————————— FUNCTION SELF SETTER/GETTER DOWN —————————————————————————————————————

    def _set_broker_id(self, odr_id) -> None:
        if self.__broker_id is not None:
            raise Exception(f"The Order's broker id is already set")
        self.__broker_id = str(odr_id)

    def get_broker_id(self) -> str:
        return self.__broker_id

    def _set_type(self, odr_type: str) -> None:
        if odr_type not in self.ODR_TYPES:
            raise ValueError(f"This Order type '{odr_type}' is not supported")
        self.__type = odr_type

    def get_type(self) -> str:
        return self.__type

    def _set_status(self, status: str) -> None:
        if status not in self.STATUS_LIST:
            raise ValueError(f"This Order status '{status}' is not supported")
        hold = self.get_status()
        if hold == self.STATUS_COMPLETED \
                or hold == self.STATUS_CANCELED \
                or hold == self.STATUS_FAILED \
                or hold == self.STATUS_EXPIRED:
            raise Exception(f"This Order status '{hold}' can't be updated to '{status}' cause it's final")
        self.__status = status

    def get_status(self) -> str:
        return self.__status

    def _set_move(self, move: str) -> None:
        if move not in self.get_moves():
            raise ValueError(f"This move '{move}' is not supported")
        self.__move = move
        self._set_transaction_type(Transaction.TYPE_BUY) if move == self.MOVE_BUY else self._set_transaction_type(Transaction.TYPE_SELL)

    def get_move(self) -> str:
        return self.__move

    def _set_limit_price(self, limit: Price) -> None:
        self._limit = limit

    def get_limit_price(self) -> Price:
        return self._limit

    def _set_stop_price(self, stop: Price) -> None:
        self._stop = stop

    def get_stop_price(self) -> Price:
        return self._stop

    def _set_quantity(self, qty: Price) -> None:
        self._quantity = qty

    def get_quantity(self) -> Price:
        return self._quantity

    def _set_amount(self, amount: Price) -> None:
        self.__amount = amount

    def get_amount(self) -> Price:
        return self.__amount

    def _set_execution_time(self, time: int) -> None:
        if self.__execution_time is not None:
            raise Exception(f"Order's execution time can't be updated.")
        self.__execution_time = int(time)

    def get_execution_time(self) -> int:
        """
        To get execution time in millisecond\n
        Returns
        -------
        exec_time: int
            execution time in millisecond
        """
        return self.__execution_time

    def _set_execution_price(self, price: Price) -> None:
        if self.__execution_price is not None:
            raise Exception(f"The execution price '{self.__execution_price}' is already set, (new price '{price}').")
        self.__execution_price = price

    def get_execution_price(self) -> Price:
        """
        To get market price at witch Order has been executed

        Returns:
        --------
        return: Price
            The market price at witch Order have been executed
        """
        return self.__execution_price

    def _set_executed_quantity(self, quantity: Price) -> None:
        if self.__executed_quantity is not None:
            raise Exception(f"The execution quantity "
                            f"'{self.__executed_quantity}' is already set, (new quantity '{quantity}').")
        self.__executed_quantity = quantity
        self._set_left(quantity)

    def get_executed_quantity(self) -> Price:
        """
        To get quantity of left Asset executed
        NOTE: executed_quantity = received_quantity + fee

        Returns:
        --------
        return: Price
            The quantity of left Asset executed
        """
        return self.__executed_quantity

    def _set_executed_amount(self, amount: Price) -> None:
        if self.__executed_amount is not None:
            raise Exception(f"The execution amount "
                            f"'{self.__executed_amount}' is already set, (new amount '{amount}').")
        self.__executed_amount = amount
        self._set_right(amount)

    def get_executed_amount(self) -> Price:
        """
        To get amount of right Asset executed
        NOTE: executed_amount = received_amount + fee

        Returns:
        --------
        return: Price
            The amount of right Asset executed
        """
        return self.__executed_amount

    def _set_fee(self, fee: Price) -> None:
        if self.__fee is not None:
            raise Exception(f"Order's fee can't be updated.")
        pair = self.get_pair()
        l_symbol = pair.get_left().get_symbol()
        r_symbol = pair.get_right().get_symbol()
        fee_symbol = fee.get_asset().get_symbol()
        exec_price = self.get_execution_price()
        if fee_symbol == l_symbol:
            l_fee = fee
            r_fee = Price(fee * exec_price, r_symbol)
        elif fee_symbol == r_symbol:
            l_fee = Price(fee / exec_price, l_symbol)
            r_fee = fee
        else:
            raise ValueError(f"The fee's symbol '{fee_symbol}' don't match Order's pair '{pair}'.")
        self.__fee = Map({
            l_symbol: l_fee,
            r_symbol: r_fee,
        })
        self._set_transaction_fee(r_fee)

    def get_fee(self, asset: Asset) -> Price:
        """
        To get fee charged to execute the Order

        Returns:
        --------
        return: Price
            The fee charged to execute the Order
        """
        pair = self.get_pair()
        if (asset != pair.get_left()) and (asset != pair.get_right()):
            raise ValueError(f"There is not fee with this symbol '{asset}' (Order's pair '{pair}').")
        return self.__fee.get(asset.get_symbol()) if isinstance(self.__fee, Map) else None

    def _set_trades(self, trades: Map) -> None:
        """
        To set trades executed\n
        Note: Usually an order is split by the Broker to sub-order (= trade) to be fill easier

        :param trades: executed trades
               Map[trade_id][*]:    {BrokerRequest.get_trades()}    # Same format
        """
        # Raise error if trades if empty
        if len(trades.get_map()) == 0:
            raise ValueError(f"The list of executed trade can't be empty.")
        trade_datas = self._exctract_trade_datas(trades)
        # Set exec time with the older trade time
        self._set_execution_time(trade_datas.get(Map.time))
        # Set exec price
        self._set_execution_price(trade_datas.get(Map.price))
        # Set fee
        self._set_fee(trade_datas.get(Map.fee))
        # Set exec amount
        self._set_executed_amount(trade_datas.get(Map.right))
        # Set exec quantity
        self._set_executed_quantity(trade_datas.get(Map.left))
        # Set trades
        self.__trades = trades

    def get_trades(self) -> Map:
        """
        To get executed trades\n
        :return: executed trades
                 Map[trade_id][*]:    {BrokerRequest.get_trades()}    # Same format
        """
        return self.__trades

    def _set_request_params(self, params: Map) -> None:
        self.__request_params = params

    def _get_request_params(self) -> Map:
        return self.__request_params

    def _set_cancel_request_params(self, params: Map) -> None:
        self.__cancel_request_params = params

    @abstractmethod
    def _set_market(self) -> None:
        """
        To prepare a market order request\n
        :param params: params to make a market Order
                        params[Map.pair]    => {Pair}
                        params[Map.move]    => {str}    # format: Order.MOVE_{BUY|SELL}
                        params[Map.quantity]=> {Price|None}
                        params[Map.amount]  => {Price|None}
        :Note : Map.quantity or Map.amount must be set
        """
        pass

    @abstractmethod
    def _set_limit(self) -> None:
        """
        To set a limit Order\n
        :param params: params to config a limit Order
        """
        pass

    @abstractmethod
    def _set_stop(self) -> None:
        """
        To prepare a stop order request\n
            params[Map.pair]    => {Pair}
            params[Map.move]    => {str}
            params[Map.stop]    => {Price}  # in right asset
            params[Map.quantity]=> {Price}  # in left asset
        """
        pass

    @abstractmethod
    def _set_stop_limit(self) -> None:
        """
        To prepare a stop order request\n
            params[Map.pair]    => {Pair}
            params[Map.move]    => {str}
            params[Map.stop]    => {Price}  # in right asset
            params[Map.limit]   => {Price}  # in right asset
            params[Map.quantity]=> {Price}  # in left asset
        """
        pass
    
    # ——————————————————————————————————————————— FUNCTION SELF SETTER/GETTER UP ———————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    @abstractmethod
    def generate_order(self) -> Map:
        """
        To generate params for a Order request\n
        :return: params for a Order request
        """
        pass

    @abstractmethod
    def generate_cancel_order(self) -> Map:
        """
        To generate params to cancel the Order\n
        :return: params to cancel the Order
        """
        pass

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION TRANSACTION DOWN ————————————————————————————————————————————

    # ——————————————————————————————————————————— FUNCTION TRANSACTION UP ——————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION STATIC SETTER/GETTER DOWN ———————————————————————————————————

    @staticmethod
    def get_moves() -> list:
        return Order._MOVES

    # ——————————————————————————————————————————— FUNCTION STATIC SETTER/GETTER UP —————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION STATIC DOWN —————————————————————————————————————————————————

    @staticmethod
    def generate_broker_order(broker_class: str, order_type: str, params: Map) -> 'Order':
        if order_type not in Order.ODR_TYPES:
            raise ValueError(f"This Order type '{order_type}' is not supported.")
        odr_class = broker_class + Order.__name__
        exec(f"from model.API.brokers.{broker_class}.{odr_class} import {odr_class}")
        odr = eval(f"{odr_class}('{order_type}', params)")
        return odr

    @staticmethod
    def _exctract_trade_datas(trades: Map) -> Map:
        """
        To extract datas from trades\n
        :param trades: executed trades
               Map[trade_id][*]:    {BrokerRequest.get_trades()}    # Same format
        :return: extracted datas\n
                 Map[Map.time]:     {int}   # Execution time of the older trade
                 Map[Map.price]:    {Price} # Average execution price
                 Map[Map.left]:     {Price} # Executed quantity in left asset
                 Map[Map.right]:    {Price} # Executed amount in right asset
                 Map[Map.fee]:      {Price} # Total fees charged
        """
        new_trades = []
        trade_ids = trades.get_keys()
        trade = Map(trades.get(trade_ids[0]))
        pair = trade.get(Map.pair)
        r_asset = pair.get_right()
        fee = trade.get(Map.fee)
        exec_time = trade.get(Map.time)
        total_quantity = Price(0, pair.get_left())
        fees = Price(0, fee.get_asset())
        price_min_decimal = 10**(5)
        for trade_id, trade in trades.get_map().items():
            trade_time = trade[Map.time]
            exec_time = trade_time if trade_time < exec_time else exec_time
            price = trade[Map.price]
            # Quantity
            quantity = trade[Map.quantity]
            total_quantity += quantity
            # Fee
            fee = trade[Map.fee]
            fees += fee
            # Decimal
            n_decimal = _MF.get_nb_decimal(price.get_value())
            price_min_decimal = n_decimal if n_decimal < price_min_decimal else price_min_decimal
            new_trade = {
                Map.price: price,
                Map.quantity: quantity,
                Map.commission: fee
            }
            new_trades.append(new_trade)
        price_rates = [(row[Map.quantity] / total_quantity) * row[Map.price] for row in new_trades]
        price_sum = sum(price_rates)
        exec_price_avg = Price(price_sum, r_asset, n_decimal=price_min_decimal, cut_exceed=True)
        datas = Map({
            Map.time: exec_time,
            Map.price: exec_price_avg,
            Map.left: total_quantity,
            Map.right: Price(exec_price_avg * total_quantity, r_asset, n_decimal=price_min_decimal, cut_exceed=True),
            Map.fee: fees
        })
        return datas

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        pass

    # ——————————————————————————————————————————— FUNCTION STATIC UP ———————————————————————————————————————————————————
