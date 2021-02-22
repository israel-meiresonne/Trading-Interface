
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Price import Price


class Orders(Order):
    SAVE_ACTION_GENERATE = "GENERATE"
    SAVE_ACTION_HANDLE = "HANDLE_REQUEST"
    SAVE_ACTION_UPDATE = "UPDATE_COMPLETED"

    def __init__(self):
        self.__orders = Map()
        self.__sum = None
        self.__has_position = None

    def add_order(self, odr: Order) -> None:
        odrs = self._get_orders()
        odrs.put(odr, len(odrs.get_map()))
        self._reset()

    def _get_orders(self) -> Map:
        return self.__orders

    def get_order(self, k) -> Order:
        odrs = self._get_orders()
        ks = odrs.get_keys()
        if k not in ks:
            raise ValueError(f"There's no Order at this key '{k}'")
        return odrs.get(k)

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

    def update(self, market: MarketPrice) -> None:
        self._reset()
        close_val = market.get_close(0)
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
                    odr_stop = odr.get_stop_price()
                    if (status != Order.STATUS_COMPLETED) and (odr_stop.get_value() >= close_val):
                        odr._set_execution_price(odr_stop)
                        odr._set_status(Order.STATUS_COMPLETED)
                        self.insert_order(self.SAVE_ACTION_UPDATE, odr)
                elif odr_type == Order.TYPE_LIMIT:
                    raise Exception("Must be implemented")
                else:
                    raise Exception(f"Unknown Order's type '{odr_type}'")

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

    def generate_order(self) -> Map:
        pass

    def generate_cancel_order(self) -> Map:
        pass