from config.Config import Config
from model.structure.Broker import Broker
from model.tools.BrokerRequest import BrokerRequest
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class Orders(Order):
    SAVE_ACTION_GENERATE = "GENERATE_REQUEST"
    SAVE_ACTION_HANDLE = "HANDLE_REQUEST"
    SAVE_ACTION_UPDATE = "UPDATE_COMPLETED"
    SAVE_ACTION_CANCEL = "GENERATE_CANCEL"

    def __init__(self):
        self.__orders = Map()
        self.__ids_to_indexes = Map()
        self.__sum = None
        self.__has_position = None

    def add_order(self, odr: Order) -> None:
        self._reset()
        odrs = self._get_orders()
        ids_to_indexes = self._get_ids_to_indexes()
        idx = len(odrs.get_map())
        odr_id = odr.get_id()
        odrs.put(odr, idx)
        ids_to_indexes.put(idx, odr_id)

    def _get_orders(self) -> Map:
        return self.__orders

    def get_order(self, idx=None, odr_id: str = None) -> Order:
        """
        To get an Order by its index or id\n
        :param idx: index position of an existing Order
        :param odr_id: Id of an existing Order
        :return: the Order at the given index or with the given id
        """
        if (idx is None) and (odr_id is None):
            raise ValueError(f"The Order's index and id can't both be null")
        if (idx is not None) and (odr_id is not None):
            raise ValueError(f"The Order's index and id can't both be set")
        odrs = self._get_orders()
        if idx is not None:
            idxs = odrs.get_keys()
            if idx not in idxs:
                raise ValueError(f"This index '{idx}' don't exist in Orders.")
            odr = odrs.get(idx)
        else:
            ids_to_indexes = self._get_ids_to_indexes()
            ids = ids_to_indexes.get_keys()
            if odr_id not in ids:
                raise ValueError(f"There's no Order with this id '{odr_id}'.")
            idx = ids_to_indexes.get(odr_id)
            odr = odrs.get(idx)
        return odr

    def _get_ids_to_indexes(self) -> Map:
        return self.__ids_to_indexes

    def get_last_execution(self) -> Order:
        """
        To get the last Order executed\n
        :return: the last Order executed
        """
        last = None
        odrs = self._get_orders()
        ks = odrs.get_keys()
        ks.reverse()
        for k in ks:
            odr = odrs.get(k)
            if odr.get_status() == Order.STATUS_COMPLETED:
                last = odr
                break
        return last

    def _set_sum(self) -> None:
        self.__sum = self._sum_orders(self._get_orders())

    def get_sum(self) -> Map:
        self._set_sum() if self.__sum is None else None
        return self.__sum

    def get_size(self) -> int:
        return len(self._get_orders().get_map())

    def _set_has_position(self, has_pos: bool) -> None:
        self.__has_position = has_pos

    def has_position(self) -> bool:
        """
        Check if holding a left position\n
        :return: True if holding else False
        """
        has_pos = self.__has_position
        if has_pos is None:
            has_pos = False
            odrs = self._get_orders()
            ks = odrs.get_keys()
            ks.reverse()
            for k in ks:
                odr = odrs.get(k)
                if odr.get_status() == Order.STATUS_COMPLETED:
                    has_pos = odr.get_move() == Order.MOVE_BUY
                    break
            self._set_has_position(has_pos)
        return has_pos

    def _reset(self) -> None:
        self.__sum = None
        self.__has_position = None

    def update(self, bkr: Broker, market: MarketPrice) -> None:
        """
        To update Orders\n
        :param bkr: access to a Broker's API  | Used in stage 3
        :param market: market's prices        | Used in stage 1 & 2
        """
        self._reset()
        _stage = Config.get(Config.STAGE_MODE)
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            self._update_stage_1_2(market)
        elif _stage == Config.STAGE_3:
            self._update_stage_3(bkr)

    def _update_stage_1_2(self, market: MarketPrice):
        close_val = market.get_close()
        odrs = self._get_orders()
        for _, odr in odrs.get_map().items():
            status = odr.get_status()
            if status is None:
                raise Exception(f"Order's status can't be null")
            if (status == Order.STATUS_SUBMITTED) or (status == Order.STATUS_PROCESSING):
                odr_type = odr.get_type()
                if odr_type == Order.TYPE_MARKET:
                    pass
                elif odr_type == Order.TYPE_STOP:
                    stop_price = odr.get_stop_price()
                    if (status != Order.STATUS_COMPLETED) and (stop_price.get_value() >= close_val):
                        self._update_algo_order_stage_1_2(odr, market)
                        # Backup
                        self.insert_order(self.SAVE_ACTION_UPDATE, odr)
                elif odr_type == Order.TYPE_LIMIT:
                    raise Exception("Must be implemented")
                elif odr_type == Order.TYPE_STOP_LIMIT:
                    stop_price = odr.get_stop_price()
                    limit_price = odr.get_limit_price()
                    if limit_price.get_value() != stop_price.get_value():
                        raise Exception("Must implement Order update when stop and limit price are different")
                    if (status != Order.STATUS_COMPLETED) and (stop_price.get_value() >= close_val):
                        """
                        odr._set_execution_price(stop_price)
                        odr._set_status(Order.STATUS_COMPLETED)
                        odr._set_execution_time(market.get_time())
                        """
                        self._update_algo_order_stage_1_2(odr, market)
                        # Backup
                        self.insert_order(self.SAVE_ACTION_UPDATE, odr)
                else:
                    raise Exception(f"Unknown Order's type '{odr_type}'")

    @staticmethod
    def _update_algo_order_stage_1_2(odr: Order, market: MarketPrice) -> None:
        stop_price = odr.get_stop_price()
        # close = market.get_close()
        qty_obj = odr.get_quantity()
        # qty_val = qty_obj.get_value()
        exec_qty_obj = qty_obj  # Price(qty_val, qty_obj.get_asset().get_symbol())
        exec_amount_obj = stop_price  # Price(stop_price.get_value(), odr.get_pair().get_right().get_symbol())
        odr._set_execution_price(stop_price)
        odr._set_status(Order.STATUS_COMPLETED)
        odr._set_execution_time(market.get_time())
        odr._set_executed_quantity(exec_qty_obj)  # if odr.get_quantity() is None else None
        odr._set_executed_amount(exec_amount_obj)  # if odr.get_amount() is None else None

    def _update_stage_3(self, bkr: Broker) -> None:
        odrs = self._get_orders()
        starttime = None
        for idx, odr in odrs.get_map().items():
            status = odr.get_status()
            if (status == Order.STATUS_SUBMITTED) or (status == Order.STATUS_PROCESSING):
                starttime = odr.get_settime()
                break
        if starttime is not None:
            first_odr = self.get_order(idx=0)
            bkr_cls = bkr.__class__.__name__
            bkr_rq_cls = BrokerRequest.get_request_class(bkr_cls)
            rq_prms = Map({
                Map.symbol: first_odr.get_pair().get_merged_symbols(),
                Map.id: None,
                Map.begin_time: starttime,
                Map.end_time: None,
                Map.limit: None,
                Map.timeout: None
            })
            exec(f"from model.API.brokers.{bkr_cls}.{bkr_rq_cls} import {bkr_rq_cls}")
            bkr_rq = eval(bkr_rq_cls + f"('{BrokerRequest.RQ_ORDERS}', rq_prms)")
            bkr.request(bkr_rq)
            odrs_datas = bkr_rq.get_orders()
            for idx, odr in odrs.get_map().items():
                odr_status = odr.get_status()
                if (odr_status == Order.STATUS_SUBMITTED) or (odr_status == Order.STATUS_PROCESSING):
                    """
                    # Get api Order
                    odr_bkr_id = odr.get_broker_id()
                    api_odr = odrs_datas.get(odr_bkr_id)
                    # Get api Order's properties
                    exec_price = api_odr.get(Map.price)
                    # exec_price_obj = Price(exec_price, odr.get_pair().__str__())  # ⚠️ instead odr.get_pair().get_symbol()
                    exec_price_obj = Price(exec_price, odr.get_pair().__str__())
                    api_odr_status = api_odr.get(Map.status)
                    api_exec_time = api_odr.get(Map.time)
                    exec_qty = float(odrs_datas.get(Map.qty))
                    exec_qty_obj = Price(exec_qty, l_symbol) if exec_qty > 0 else None
                    exec_amount = float(odrs_datas.get(Map.amount))
                    exec_amount_obj = Price(exec_amount, r_symbol) if exec_amount > 0 else None
                    # Update
                    odr._set_execution_price(exec_price_obj)
                    odr._set_status(api_odr_status)
                    odr._set_execution_time(api_exec_time)
                    odr._set_executed_quantity(exec_qty_obj)  # if odr.get_quantity() is None else None
                    odr._set_executed_amount(exec_amount_obj)  # if odr.get_amount() is None else None
                    """
                    odr_bkr_id = odr.get_broker_id()
                    odr_datas = Map(odrs_datas.get(odr_bkr_id))
                    self._update_algo_order_stage_3(odr, odr_datas)
                    # Backup
                    self.insert_order(self.SAVE_ACTION_UPDATE, odr)

    @staticmethod
    def _update_algo_order_stage_3(odr: Order, odr_datas: Map) -> None:
        r_symbol = odr.get_pair().get_right().get_symbol()
        l_symbol = odr.get_pair().get_left().get_symbol()
        # Get api Order
        # odr_bkr_id = odr.get_broker_id()
        # odr_datas = odrs_datas.get(odr_bkr_id)
        # Get api Order's properties
        new_status = odr_datas.get(Map.status)
        exec_time = odr_datas.get(Map.time) \
            if (new_status == Order.STATUS_PROCESSING) or (new_status == Order.STATUS_COMPLETED) else None
        # Exec Price
        exec_price = odr_datas.get(Map.price)
        exec_price_obj = Price(exec_price, r_symbol) if exec_price is not None else None
        # Exec Quantity
        exec_qty = odr_datas.get(Map.qty)
        exec_qty_obj = Price(exec_qty, l_symbol) if exec_qty is not None else None
        # Exec Amount
        exec_amount = odr_datas.get(Map.amount)
        exec_amount_obj = Price(exec_amount, r_symbol) if exec_amount is not None else None
        # Update
        odr._set_status(new_status)
        odr._set_execution_time(exec_time) if exec_time is not None else None
        odr._set_execution_price(exec_price_obj) if (odr.get_execution_price() is None) \
                                                    and (exec_price_obj is not None) else None
        odr._set_executed_quantity(exec_qty_obj) if (odr.get_executed_quantity() is None) \
                                                    and (exec_price_obj is not None) else None
        odr._set_executed_amount(exec_amount_obj) if (odr.get_executed_amount() is None) \
                                                     and (exec_amount_obj is not None) else None

    @staticmethod
    def _sum_orders(odrs: Map) -> Map:
        """
        To sum orders executed\n
        :param odrs: collection of Order
        :exception ValueError: if collection of order is empty
        :return: amount stilling in each asset
                 Map[Map.left]  => {Price}
                 Map[Map.right] => {Price}
        """
        if len(odrs.get_map()) <= 0:
            raise ValueError("The collection of Order can't be empty")
        ks = odrs.get_keys()
        pr = odrs.get(ks[0]).get_pair()
        pr_str = pr.__str__
        lspot = 0
        rspot = 0
        """
        for _, odr in odrs.get_map().items():
            if pr_str != odr.get_pair().__str__:
                raise Exception(f"All Order must have the same pair of asset: {pr_str}!={odr.get_pair().__str__}")
            if odr.get_status() == Order.STATUS_COMPLETED:
                move = odr.get_move()
                exct = odr.get_execution_price()
                if move == Order.MOVE_BUY:
                    if odr.get_quantity() is not None:
                        qty = odr.get_quantity()
                        lspot += qty.get_value()
                        rspot -= exct.get_value() * qty.get_value()
                    elif odr.get_amount() is not None:
                        amnt = odr.get_amount()
                        lspot += amnt.get_value() / exct.get_value()
                        rspot -= amnt.get_value()
                    else:
                        raise Exception("Unknown Order state")
                elif move == Order.MOVE_SELL:
                    if odr.get_quantity() is not None:
                        qty = odr.get_quantity()
                        lspot -= qty.get_value()
                        rspot += exct.get_value() * qty.get_value()
                    elif odr.get_amount():
                        amnt = odr.get_amount()
                        lspot -= amnt.get_value() / exct.get_value()
                        rspot += amnt.get_value()
                    else:
                        raise Exception("Unknown Order state")
                else:
                    raise Exception("Unknown Order move")
        """
        for _, odr in odrs.get_map().items():
            if pr_str != odr.get_pair().__str__:
                raise Exception(f"All Order must have the same pair of asset: {pr_str}!={odr.get_pair().__str__}")
            if odr.get_status() == Order.STATUS_COMPLETED:
                move = odr.get_move()
                exec_qty = odr.get_executed_quantity()
                exec_amount = odr.get_executed_amount()
                if move == Order.MOVE_BUY:
                    lspot += exec_qty.get_value()
                    rspot -= exec_amount.get_value()
                elif move == Order.MOVE_SELL:
                    lspot -= exec_qty.get_value()
                    rspot += exec_amount.get_value()
                else:
                    raise Exception("Unknown Order move")
        odrs_sum = Map({
            Map.left: Price(lspot, pr.get_left().get_symbol()),
            Map.right: Price(rspot, pr.get_right().get_symbol())
        })
        return odrs_sum

    @staticmethod
    def insert_order(action: str, odr: Order) -> None:
        from config.Config import Config
        from model.tools.FileManager import FileManager
        p = Config.get(Config.DIR_SAVE_ORDER_ACTIONS)
        d = {Map.action: action, **odr.__dict__}
        key1 = "_Order__order_params"
        for k, v in d[key1].get_map().items():
            if isinstance(v, Price) or isinstance(v, Pair):
                # d[key1][k] = v.__str__()
                d[key1].put(v.__str__(), k)
        rows = [d]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    # Don't use classes bellow
    def _set_market(self) -> None:
        pass

    def _set_limit(self) -> None:
        pass

    def _set_stop(self) -> None:
        pass

    def _set_stop_limit(self) -> None:
        pass

    def generate_order(self) -> Map:
        pass

    def generate_cancel_order(self) -> Map:
        pass