import time
from threading import Thread
from typing import Callable, Dict, List, Tuple, Union

import pandas as pd
from config.Config import Config

from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.HandTrade import HandTrade
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Orders import Orders
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class Hand(MyJson):
    PREFIX_ID =                 'hand_'
    _MAX_POSITION =             1
    _THREAD_STALK =             'stalk'
    _THREAD_POSITION =          'position'
    _THREAD_MARKET_ANALYSE =    'market_analyse'
    _TIMEOUT_THREAD_STOP =      60*2
    _SLEEP_POSITION =           10
    _SLEEP_POSITION_VIEW =      5
    _SLEEP_STALK =              30
    _SLEEP_MARKET_ANALYSE =     60
    _N_PERIOD =                 300
    _STALK_FUNCTIONS =          None
    _REQUIRED_PERIODS = [
        Broker.PERIOD_1MIN,
        Broker.PERIOD_5MIN,
        Broker.PERIOD_15MIN,
        Broker.PERIOD_1H,
        ]

    def __init__(self, capital: Price, broker_class: Callable) -> None:
        self.__id =                     None
        self.__settime =                None
        self.__broker_class =           None
        self.__broker =                 None
        self.__wallet =                 None
        self.__max_position =           None
        self.__positions =              None
        self.__failed_orders =          None
        self.__new_positions =          None
        self.__closed_positions =       None
        self.__orders =                 None
        self.__orders_ref_id =          None
        self.__is_stalk_on =            False
        self.__thread_stalk =           None
        self.__is_position_on =         False
        self.__thread_position =        None
        self.__market_analyse_on =      False
        self.__thread_market_analyse =  None
        self.__backup =                 None
        self._set_id()
        self._set_settime()
        self._set_wallet(capital)
        self._set_broker_class(broker_class)
        self.set_max_position(self._MAX_POSITION)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN —————————————————————————————————————————

    def _set_id(self) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()

    def get_id(self) -> str:
        return self.__id

    def _set_settime(self) -> None:
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def _set_broker_class(self, broker_class: Callable) -> None:
        if not callable(broker_class):
            raise ValueError(f"The broker class must be callable, instead '{broker_class}(type={type(broker_class)})'")
        self.__broker_class = broker_class.__name__

    def get_broker_class(self) -> str:
        """
        To get broker class name

        Returns:
        --------
        return: Broker
            Broker class name
        """
        return self.__broker_class

    def set_broker(self, broker: Broker) -> None:
        broker_class = self.get_broker_class()
        if broker.__class__.__name__ != broker_class:
            raise TypeError(f"The broker's type must be '{broker_class}', instead 'name={broker.__class__.__name__}(type={type(broker)})'")
        self.__broker = broker

    def reset_broker(self) -> None:
        self.__broker = None

    def is_broker_set(self) -> bool:
        """
        To check if Broker is set

        Returns:
        --------
        return: bool
            True if Broker is set else False
        """
        broker = _MF.catch_exception(self.get_broker, self.__class__.__name__, repport=False)
        return isinstance(broker, Broker)

    def get_broker(self) -> Broker:
        """
        To get access to a broker's API

        Returns:
        --------
        return: Broker
            Access to a broker's API
        """
        broker = self.__broker
        if broker is None:
            raise Exception("The broker attribut must be set before access")
        return broker

    def _set_wallet(self, initial: Price) -> None:
        self.__wallet = Wallet(initial)

    def get_wallet(self) -> Wallet:
        """
        To get wallet that manage capital

        Returns:
        --------
        return: Wallet
            Wallet that manage capital
        """
        return self.__wallet

    def set_max_position(self, max_position: int) -> None:
        if not isinstance(max_position, int):
            raise TypeError(f"The max number of position must be of type '{int}', instead '{max_position}(type={type(max_position)})'")
        n_position = len(self.get_positions())
        old_max = self.get_max_position()
        if old_max is not None:
            remaining = old_max - n_position
            if remaining <= 0:
                raise Exception(f"Can't update max position when there's no free position remaining (remaining='{remaining}', max_position='{old_max}')")
        min_max_position = max([1, n_position])
        if max_position < min_max_position:
            raise ValueError(f"The max number of position must respect 'max_position >= '{min_max_position}', instead max_position='{max_position}'")
        self.__max_position = max_position

    def get_max_position(self) -> int:
        """
        To get max number of position allowed to hold

        Returns:
        --------
        return: int
            Max number of position allowed to hold
        """
        return self.__max_position

    def is_max_position_reached(self) -> bool:
        """
        To check if the max number of position allowed is reached

        Returns:
        --------
        return: bool
            True if the max number of position allowed is reached else False
        """
        max_position = self.get_max_position()
        n_position = len(self.get_positions())
        return n_position >= max_position

    def get_positions(self) -> Dict[str, HandTrade]:
        """
        To get collection of pairs being trade

        Returns:
        --------
        return: Dict[str,HandTrade]
            collection of pairs being trade
            positions[Pair.__str__(){str}]: {HandTrade}
        """
        if self.__positions is None:
            self.__positions = {}
        return self.__positions

    def get_position(self, pair: Pair) -> HandTrade:
        """
        To get position of the given pair

        Parameters:
        -----------
        pair: Pair
            Pair to get position of

        Returns:
        --------
        return: Dict[str,HandTrade]
            Position of the given pair
        """
        positions = self.get_positions()
        pair_str = pair.__str__()
        if pair_str not in positions:
            raise ValueError(f"A position for this pair '{pair_str.upper()}' don't exist")
        return positions[pair_str]

    def _add_position(self, position: HandTrade) -> None:
        """
        To add new position in collection of positions

        Parameters:
        -----------
        trade: HandTrade
            Position to add
        """
        positions = self.get_positions()
        pair_str = position.get_buy_order().get_pair().__str__()
        if pair_str in positions:
            raise ValueError(f"A position for this pair '{pair_str.upper()}' alrady exist")
        positions[pair_str] = position

    def _remove_position(self, pair: Pair) -> None:
        """
        To remove position from collection of positions

        Parameters:
        -----------
        pair: Pair
            Pair of the position to remove
        """
        self.get_position(pair)
        self.get_positions().pop(pair.__str__())

    def _get_failed_orders(self) -> Dict[str, Order]:
        """
        To get collection of Order that failed to be submitted or executed

        Returns:
        --------
        return: Dict[str, Order]
            Collection of Order that failed to be submitted or executed\n
            dict[Order.get_id(){str}]   -> {Order}
        """
        failed_orders = self.__failed_orders
        if failed_orders is None:
            self.__failed_orders = failed_orders = {}
        return failed_orders

    def get_failed_order(self, order_id: str) -> Order:
        """
        To get a failed Order

        Parameters:
        -----------
        order_id: str
            Id of the failed Order to get

        Returns:
        --------
        return: Order
            The failed Order with the given id
        """
        failed_orders = self._get_failed_orders()
        if order_id not in failed_orders:
            raise ValueError(f"Don't exist a failed Order with this id '{order_id}'")
        return failed_orders[order_id]

    def _add_failed_order(self, order: Order) -> None:
        """
        To add a new failed Order

        Parameters:
        -----------
        order: Order
            Failed Order to add
        """
        if not isinstance(order, Order):
            raise TypeError(f"Failed Order must be of type '{Order}', instead type='{type(order)}'")
        order_id = order.get_id()
        failed_orders = self._get_failed_orders()
        order_ids = list(failed_orders.keys())
        if order_id in order_ids:
            raise ValueError(f"Failed Order with this id '{order_id}' already exist")
        if order.get_status() not in HandTrade.FAIL_STATUS:
            raise Exception(f"Order's status '{order.get_status()}' is not a failed one")
        failed_orders[order_id] = order

    def _reset_new_positions(self) -> None:
        self.__new_positions = None

    def get_propositions(self) -> pd.DataFrame:
        """
        To get list of new pair proposd to trade

        Returns:
        --------
        return: pd.DataFrame
            List of new positions
        | date | pair | buy | metricX |
        | ---- | ---- | --- | ------- |
        | 1997-03-23 03:15:21 | btc/usdt | True | Y
        | 1997-06-30 03:06:07 | doge/usdt | False | X
        """
        new_positions = self.__new_positions
        if (new_positions is None) or (new_positions.shape[0] == 0):
            self.__new_positions = new_positions = pd.DataFrame(columns=[Map.date, Map.pair, Map.link, Map.buy])
        return new_positions

    def _add_proposition(self, pair: Pair) -> None:
        """
        To add a new pair in list of pairs proposed to trade
        NOTE: add new row only if all row with the given pair have all their columns completed

        Parameters:
        -----------
        pair: Pair
            Pair to add
        """
        pair_str = pair.__str__()
        new_positions = self.get_propositions()
        n_no_treadted = new_positions[new_positions[Map.buy].isna() & (new_positions[Map.pair] == pair_str)].shape[0]
        if n_no_treadted == 0:
            new_row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.pair: pair_str,
                Map.link: None,
                Map.buy: None
            }
            self.__new_positions = new_positions.append(new_row, ignore_index=True)

    def _mark_proposition(self, pair: Pair, have_bought: bool) -> None:
        """
        To mark if a proposed position has been bought
        NOTE: only mark the most recent row

        Parameters:
        -----------
        pair: Pair
            Pair to mark
        have_bought: bool
            Set True to mark pair as bought else False
        """
        new_positions = self.get_propositions()
        pair_index = list(new_positions.loc[new_positions[Map.buy].isna() & (new_positions[Map.pair] == pair.__str__())].index)
        if len(pair_index) > 0:
            new_positions.loc[pair_index[-1], Map.buy] = have_bought

    def get_closed_positions(self) -> List[HandTrade]:
        """
        To get list of closed positions

        Returns:
        --------
        return: List[HandTrade]
            List of closed positions
        """
        if self.__closed_positions is None:
            self.__closed_positions = []
        return self.__closed_positions

    def _add_closed_position(self, position: HandTrade) -> None:
        """
        To add a new position in list of closed position

        Parameters:
        -----------
        trade: HandTrade
            Position to add
        """
        if not position.is_closed():
            raise ValueError(f"The position '{position.get_buy_order().get_pair().__str__().upper()}' must be closed")
        self.get_closed_positions().append(position)

    def _move_closed_position(self, pair: Pair) -> None:
        """
        To move a closed position from list of positions to list of closed positions

        Parameters:
        -----------
        pair: Pair
            Pair to move
        """
        position = self.get_position(pair)
        self._remove_position(pair)
        self._add_closed_position(position)

    def _move_closed_positions(self, positions: Dict[str, HandTrade] = None) -> None:
        """
        To loop move of closed positions
        """
        positions = self.get_positions().copy() if positions is None else positions
        [self._move_closed_position(Pair(pair_str)) for pair_str, position in positions.items() if position.is_closed()]

    def _reset_orders_map(self) -> None:
        self.__orders = None

    def _get_orders_map(self) -> Map:
        """
        To get collection of submited order

        Returns:
        --------
        return: Orders
            Collection of submited order
            map[Pair.__str__()]:    Orders
        """
        ref_id = self._get_orders_ref_id()
        new_ref_id, position_orders = self.concat_order_ref_id(self.get_positions())
        orders_map = self.__orders
        if (orders_map is None) or (new_ref_id != ref_id):
            self._set_orders_ref_id(new_ref_id)
            orders_map = Map()
            for position_order in position_orders:
                pair_str = position_order.get_pair().__str__()
                orders = orders_map.get(pair_str)
                if orders is None:
                    orders = Orders()
                    orders_map.put(orders, pair_str)
                orders.add_order(position_order)
            self.__orders = orders_map
        return orders_map

    def _set_orders_ref_id(self, ref_id: str) -> str:
        self.__orders_ref_id = ref_id

    def _get_orders_ref_id(self) -> str:
        return self.__orders_ref_id

    def _reset_thread_stalk(self) -> None:
        self.__thread_stalk = None

    def set_stalk_on(self, on: bool) -> None:
        """
        To start or stop thread that stalk market

        Parameters:
        -----------
        on: bool
            Set True to start thread else False to stop
        """
        if not isinstance(on, bool):
            raise TypeError(f"The stalk status must be of type '{bool}', instead '{on}({type(on)})'")
        self.__is_stalk_on = on
        self._get_thread_stalk().start() if on and (not self._get_thread_stalk().is_alive()) else None
        if not on:
            _MF.wait_while(self._get_thread_stalk().is_alive, False, self._TIMEOUT_THREAD_STOP, Exception(f"Time to stop stalk is out"))
            self._reset_thread_stalk()

    def is_stalk_on(self) -> bool:
        """
        To check if class is allowed to stalk market opportunity to buy

        Returns:
        --------
        return: bool
            True if class is allowed to stalk market else False
        """
        return self.__is_stalk_on

    def _get_thread_stalk(self) -> Thread:
        """
        To get thread that stalk market

        Returns:
        --------
        return: Thread
            Thread that stalk market
            NOTE: create a new thread if there is no thread running
        """
        thread = self.__thread_stalk
        if thread is None:
            self.__thread_stalk, output = _MF.generate_thread(self._manage_stalk, base_name=self._THREAD_STALK)
            _MF.output(output)
        return self.__thread_stalk

    def _reset_thread_position(self) -> None:
        self.__thread_position = None

    def set_position_on(self, on: bool) -> None:
        """
        To start or stop thread that manage positions

        Parameters:
        -----------
        on: bool
            Set True to start thread else False to stop
        """
        if not isinstance(on, bool):
            raise TypeError(f"The running status of thread that manage positions must be of type '{bool}', instead '{on}({type(on)})'")
        self.__is_position_on = on
        self._get_thread_position().start() if on and (not self._get_thread_position().is_alive()) else None
        if not on:
            _MF.wait_while(self._get_thread_position().is_alive, False, self._TIMEOUT_THREAD_STOP, Exception(f"Time to stop management of positions is out"))
            self._reset_thread_position()

    def is_position_on(self) -> bool:
        """
        To check if thread that manage positions is allowed to run

        Returns:
        --------
        return: bool
            True if thread that manage positions is allowed to run else False
        """
        return self.__is_position_on

    def _get_thread_position(self) -> Thread:
        """
        To get thread that manage positions

        Returns:
        --------
        return: Thread
            Thread that manage positions
            NOTE: create a new thread if there is no thread running
        """
        thread = self.__thread_position
        if thread is None:
            self.__thread_position, output = _MF.generate_thread(self._manage_positions, base_name=self._THREAD_POSITION)
            _MF.output(output)
        return self.__thread_position

    def _reset_thread_market_analyse(self) -> None:
        self.__thread_market_analyse = None

    def set_market_analyse_on(self, on: bool) -> None:
        """
        To start or stop thread that manage analyse of market

        Parameters:
        -----------
        on: bool
            Set True to start thread else False to stop
        """
        if not isinstance(on, bool):
            raise TypeError(f"The running status of thread that analyse market must be of type '{bool}', instead '{on}({type(on)})'")
        self.__market_analyse_on = on
        self._get_thread_market_analyse().start() if on and (not self._get_thread_market_analyse().is_alive()) else None
        if not on:
            _MF.wait_while(self._get_thread_market_analyse().is_alive, False, self._TIMEOUT_THREAD_STOP, Exception(f"Time to stop market's analyse is out"))
            self._reset_thread_market_analyse()

    def is_market_analyse_on(self) -> bool:
        """
        To check if thread that manage positions is allowed to run

        Returns:
        --------
        return: bool
            True if thread that manage positions is allowed to run else False
        """
        return self.__market_analyse_on

    def _get_thread_market_analyse(self) -> Thread:
        """
        To get thread that manage analyse of market

        Returns:
        --------
        return: Thread
            Thread that manage analyse of market
            NOTE: create a new thread if there is no thread running
        """
        thread = self.__thread_market_analyse
        if thread is None:
            self.__thread_market_analyse, output = _MF.generate_thread(self._manage_market_analyse, base_name=self._THREAD_MARKET_ANALYSE)
            _MF.output(output)
        return self.__thread_market_analyse

    def _set_backup(self, backup: str) -> None:
        self.__backup = backup

    def _reset_backup(self) -> None:
        self.__backup = None

    def _get_backup(self) -> str:
        return self.__backup

    def _get_stalk_functions(self) -> List[Callable]:
        if Hand._STALK_FUNCTIONS is None:
            Hand._STALK_FUNCTIONS = [
                self._stalk_condition_icarus_v13_5_1,
                self._stalk_condition_1
                ]
        return Hand._STALK_FUNCTIONS

    def get_broker_pairs(self) -> List[Pair]:
        """
        To get list of pair available from Broker's API

        Returns:
        --------
        return: List[Pair]
            List of pair available from Broker's API
        """
        broker_class = self.get_broker_class()
        fiat_asset = self.get_wallet().get_initial().get_asset()
        spot_pairs = MarketPrice.get_spot_pairs(broker_class, fiat_asset)
        # return spot_pairs
        return [Pair('BTC', fiat_asset), Pair('DOGE', fiat_asset), Pair('ETH', fiat_asset), Pair('BNB', fiat_asset)]

    def _get_stalk_pairs(self) -> List[Pair]:
        """
        To get list of pair to stalk

        Returns:
        --------
        return: List[Pair]
            List of pair to stalk
        """
        spot_pairs = self.get_broker_pairs()
        pair_positions = list(self.get_positions().keys())
        return [spot_pair for spot_pair in spot_pairs if spot_pair.__str__() not in pair_positions]

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ———————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ——————————————————————————————————————————————————
    # ••• FUNCTION SELF MANAGE ATTRIBUTS DOWN

    def _position_capital(self) -> Price:
        """
        To get capital available to buy one position

        Returns:
        --------
        return: Price
            Capital available to buy one position
        """
        buy_capital = self.get_wallet().buy_capital()
        r_asset = buy_capital.get_asset()
        max_position = self.get_max_position()
        positions = self.get_positions().copy()
        active_positions = [1 for _, position in positions.items() if position.has_position()]
        remaining = max_position - len(active_positions)
        capital_value = buy_capital/remaining if remaining > 0 else 0
        position_capital = Price(capital_value, r_asset)
        return position_capital

    def _update_orders(self) -> None:
        """
        To sychronize with Broker's API states of Order from Trade in list of position
        """
        def get_orders(orders_map: Map, pair_str: str) -> Orders:
            return orders_map.get(pair_str)

        broker = self.get_broker()
        orders_map = self._get_orders_map()
        wallet = self.get_wallet()
        for pair_str, orders in orders_map.get_map().items():
            orders = get_orders(orders_map, pair_str)
            orders.update(broker, wallet)

    # ••• FUNCTION SELF MANAGE ATTRIBUTS UP
    # ••• FUNCTION SELF THREAD POSITIONS DOWN

    def _manage_positions(self) -> None:
        """
        To manage positions
        """
        while self.is_position_on():
            _MF.catch_exception(self.update_positions, Hand.__name__)
            sleep_interval = self._SLEEP_POSITION_VIEW if len(self.get_positions()) > 0 else self._SLEEP_POSITION
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), sleep_interval)
            time.sleep(sleep_time)

    def update_positions(self) -> None:
        """
        To update positions states with thier states in Broker's API
        ### Update steps:
        - Update states of submitted Order
        - Submit new Order to Broker's API
        - Record positions states
        - Move closed position to list of closed position
        - Backup Hand if there's any change
        """
        self._update_orders()
        positions = self.get_positions().copy()
        [self._try_submit(position) for _, position in positions.items() if not position.is_submitted()]
        self._repport_positions()
        # [self._move_closed_position(Pair(pair_str)) for pair_str, position in positions.items() if position.is_closed()]
        self._move_closed_positions(positions)
        self.backup()

    def _repport_positions(self) -> None:
        def print_row(file_path: str, rows: List[dict], overwrite: bool, make_dir: bool) -> None:
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows, overwrite=overwrite, make_dir=make_dir)

        def get_residue(broker: Broker, wallet: Wallet, positions: Dict[str, HandTrade]) -> Price:
            r_asset = wallet.get_initial().get_asset()
            assets = wallet.assets()
            residues = [wallet.get_position_value(broker, l_asset) for l_asset in assets if Pair(l_asset, r_asset).__str__() not in positions.keys()]
            residues.append(Price(0, r_asset))
            return Price.sum(residues)

        def get_global_rows(positions: Dict[str, HandTrade]) -> List[dict]:
            n_position = len(positions)
            #
            n_trade = len(self.get_closed_positions()) + n_position
            # Total
            initial_capital = wallet.get_initial()
            now_capital = wallet.get_total(broker)
            spot = wallet.get_spot()
            position_value = wallet.get_all_position_value(broker)
            capital_futur_position = self._position_capital()
            # Residue
            residue = get_residue(broker, wallet, positions)
            residue_initial_rate = residue/initial_capital
            residue_now_rate = residue/now_capital
            # Fee
            fee = wallet.trade_fee()
            fee_initial_rate = fee/initial_capital
            fee_now_rate = fee/now_capital
            # Roi
            roi = wallet.get_roi(broker)
            settime = int(self.get_settime()/1000)
            unix_time = _MF.get_timestamp()
            run_time = _MF.delta_time(settime, unix_time)
            set_to_now_time = unix_time - settime
            roi_day = ((roi/(set_to_now_time)) * 60 * 60 * 24) if set_to_now_time > 0 else 0
            row = [{
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.id: self.get_id(),
                'initial_capital': initial_capital,
                'now_capital': now_capital,
                Map.spot: spot,
                Map.position: position_value,
                'capital_futur_position': capital_futur_position,
                Map.residue: residue,
                'residue_initial_rate': _MF.rate_to_str(residue_initial_rate),
                'residue_now_rate': _MF.rate_to_str(residue_now_rate),
                Map.fee: fee,
                'fee_initial_rate': _MF.rate_to_str(fee_initial_rate),
                'fee_now_rate': _MF.rate_to_str(fee_now_rate),
                Map.roi: _MF.rate_to_str(roi),
                'roi_day': _MF.rate_to_str(roi_day),
                'run_time': run_time,
                'n_position': n_position,
                'max_position': self.get_max_position(),
                Map.trade: n_trade
            }]
            return row

        def get_position_rows(positions: Dict[str, HandTrade]) -> pd.DataFrame:
            columns = [
                'unix_date',
                'market_date',
                Map.id,
                Map.pair,
                'buy_order_status',
                'buy_order_stop',
                'buy_order_limit',
                Map.amount,
                'buy_date',
                'buy_price',
                'buy_amount',
                'buy_quantity',
                Map.quantity,
                'position_value',
                'sell_order_status',
                'sell_order_stop',
                'sell_order_limit',
                'sell_date',
                'sell_price',
                'sell_amount',
                'sell_quantity',
                'hold_time',
                Map.fee,
                'fee_rate',
                Map.roi,
                'min_roi',
                'max_roi',
                'min_price',
                'max_price',
                Map.low,
                Map.high,
                Map.close
            ]
            rows = pd.DataFrame(columns=columns)
            for pair_str, position in positions.items():
                position_closed = position.is_closed()
                has_position = position.has_position()
                pair = Pair(pair_str)
                l_asset = pair.get_left()
                r_asset = pair.get_right()
                marketprice = wallet.get_marketprice(broker, l_asset)
                # Open_time
                open_times = list(marketprice.get_times())
                open_times.reverse()
                # Closes
                closes = list(marketprice.get_closes())
                closes.reverse()
                # Lows
                lows = list(marketprice.get_lows())
                lows.reverse()
                # highs
                highs = list(marketprice.get_highs())
                highs.reverse()
                # Buy
                buy_order = position.get_buy_order()
                amount = buy_order.get_amount()
                buy_order_status = buy_order.get_status()
                buy_order_stop = buy_order.get_stop_price()
                buy_order_limit = buy_order.get_limit_price()
                buy_date = None
                buy_price = None
                buy_amount = None
                buy_quantity = None
                if position.is_executed(Map.buy):
                    buy_time = int(buy_order.get_execution_time()/1000)
                    buy_date = _MF.unix_to_date(buy_time)
                    buy_price = buy_order.get_execution_price()
                    buy_amount = buy_order.get_executed_amount()
                    buy_quantity = buy_order.get_executed_quantity()
                # Sell
                sell_order = position.get_sell_order()
                sell_order_is_None = sell_order is None
                quantity = sell_order.get_quantity() if not sell_order_is_None else None
                sell_order_status = sell_order.get_status() if not sell_order_is_None else None
                sell_order_stop = sell_order.get_stop_price() if not sell_order_is_None else None
                sell_order_limit = sell_order.get_limit_price() if not sell_order_is_None else None
                position_value = None
                sell_date = None
                sell_price = None
                sell_amount = None
                sell_quantity = None
                if position_closed:
                    sell_time = int(sell_order.get_execution_time()/1000)
                    sell_date = _MF.unix_to_date(sell_time)
                    sell_price = sell_order.get_execution_price()
                    sell_amount = sell_order.get_executed_amount()
                    sell_quantity = sell_order.get_executed_quantity()
                    position_value = Price(sell_quantity*sell_price, r_asset)
                else:
                    position_value = Price(buy_quantity*closes[-1], r_asset) if buy_quantity is not None else None
                # Position
                hold_time = None
                roi = None
                max_roi = None
                min_roi = None
                max_price = None
                min_price = None
                fee = None
                fee_rate = None
                if has_position:
                    hold_time = _MF.delta_time(buy_time, _MF.get_timestamp())
                    extrem_prices = position.extrem_prices(broker)
                    max_price = extrem_prices.get(Map.maximum)
                    min_price = extrem_prices.get(Map.minimum)
                    fee = buy_order.get_fee(r_asset)
                    fee_rate = fee/buy_amount
                    roi = _MF.progress_rate(closes[-1], buy_price.get_value()) - fee_rate
                elif position_closed:
                    hold_time = _MF.delta_time(buy_time, sell_time)
                    extrem_prices = position.extrem_prices(broker)
                    max_price = position.get_max_price()
                    min_price = position.get_min_price()
                    fee = buy_order.get_fee(r_asset) + sell_order.get_fee(r_asset)
                    fee_rate = fee/(sell_amount)
                    roi = _MF.progress_rate(sell_price, buy_price) - fee_rate
                if (has_position or position_closed):
                    max_roi = _MF.progress_rate(max_price, buy_price.get_value())
                    min_roi = _MF.progress_rate(min_price, buy_price.get_value())
                row = {
                    'unix_date': _MF.unix_to_date(_MF.get_timestamp()),
                    'market_date': _MF.unix_to_date(open_times[-1]),
                    Map.id: position.get_id(),
                    Map.pair: pair_str.upper(),
                    'buy_order_status': buy_order_status,
                    'buy_order_stop': buy_order_stop,
                    'buy_order_limit': buy_order_limit,
                    Map.amount: amount,
                    'buy_date': buy_date,
                    'buy_price': buy_price,
                    'buy_amount': buy_amount,
                    'buy_quantity': buy_quantity,
                    Map.quantity: quantity,
                    'position_value': position_value,
                    'sell_order_status': sell_order_status,
                    'sell_order_stop': sell_order_stop,
                    'sell_order_limit': sell_order_limit,
                    'sell_date': sell_date,
                    'sell_price': sell_price,
                    'sell_amount': sell_amount,
                    'sell_quantity': sell_quantity,
                    'hold_time': hold_time,
                    Map.fee: fee,
                    'fee_rate': _MF.rate_to_str(fee_rate) if fee_rate is not None else fee_rate,
                    Map.roi: _MF.rate_to_str(roi) if roi is not None else roi,
                    'min_roi': _MF.rate_to_str(min_roi) if (min_roi is not None) and (not _MF.is_nan(min_roi)) else min_roi,
                    'max_roi': _MF.rate_to_str(max_roi) if (max_roi is not None) and (not _MF.is_nan(max_roi)) else max_roi,
                    'min_price': min_price,
                    'max_price': max_price,
                    Map.low: lows[-1],
                    Map.high: highs[-1],
                    Map.close: closes[-1]
                }
                rows = rows.append(row, ignore_index=True)
            return rows

        broker = self.get_broker()
        wallet = self.get_wallet()
        wallet.reset_marketprices()
        positions = self.get_positions().copy()
        # save global states
        file_path_global = Config.get(Config.DIR_SAVE_GLOBAL_STATE)
        global_rows = get_global_rows(positions)
        print_row(file_path_global, global_rows, overwrite=False, make_dir=True)
        # save position states
        file_path_position = Config.get(Config.DIR_SAVE_GLOBAL_MOVES).replace('$class', self.__class__.__name__)
        position_rows = get_position_rows(positions)
        position_rows_dict = position_rows.to_dict('records')
        print_row(file_path_position, position_rows_dict, overwrite=False, make_dir=True) if position_rows.shape[0] > 0 else None
        # repport view position
        project_dir = FileManager.get_project_directory()
        file_path_position_view = Config.get(Config.FILE_VIEW_HAND_POSITION)
        dir_path_position_view = FileManager.path_to_dir(file_path_position_view)
        FileManager.get_files(dir_path_position_view, make_dir=True)
        position_rows.to_csv(project_dir + file_path_position_view, index=False)

    # ••• FUNCTION SELF THREAD POSITIONS UP
    # ••• FUNCTION SELF THREAD STALK DOWN

    def _manage_stalk(self) -> None:
        """
        To manage stalk
        """
        def stalk() -> None:
            new_pairs = self._stalk_market()
            [self._add_proposition(pair) for pair in new_pairs] if len(new_pairs) > 0 else None
            self._update_stalk_file()

        while self.is_stalk_on():
            _MF.catch_exception(stalk, Hand.__name__)
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_STALK)
            time.sleep(sleep_time)

    def _update_stalk_file(self) -> None:
        file_path = Config.get(Config.FILE_VIEW_HAND_STALK)
        dir_path = FileManager.path_to_dir(file_path)
        project_dir = FileManager.get_project_directory()
        FileManager.get_files(dir_path, make_dir=True)
        load_file = _MF.catch_exception(pd.read_csv, Hand.__name__, repport=False, **{'filepath_or_buffer': project_dir+file_path})
        # FileManager
        if load_file is not None:
            # load input
            input_pd = load_file[~load_file[Map.buy].isna()]
            if input_pd.shape[0] > 0:
                input_indexes = list(input_pd.index)
                [self._mark_proposition(Pair(input_pd.loc[input_index,Map.pair]), bool(input_pd.loc[input_index,Map.buy])) for input_index in input_indexes]
        # Print untreadted
        new_positions = self.get_propositions()
        no_treated = new_positions[new_positions[Map.buy].isna()]
        no_treated.to_csv(project_dir + file_path, index=False)

    def _stalk_market(self) -> List[Pair]:
        """
        To stalk market for opportunities to buy

        Returns:
        --------
        return: List[Pair]
            List of new opportunities to buy
        """
        def write(rows: List[dict], condition: Callable) -> None:
            file_path = self.get_path_file_stalk(condition)
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)

        stalk_pairs = self._get_stalk_pairs()
        marketprices = Map()
        conditions = self._get_stalk_functions()
        selected_pairs = []
        stalk_start_date = _MF.unix_to_date(_MF.get_timestamp())
        period_1min = Broker.PERIOD_1MIN
        for condition in conditions:
            condition_repports = []
            for stalk_pair in stalk_pairs:
                row_start_date = _MF.unix_to_date(_MF.get_timestamp())
                can_select, pair_repport = condition(stalk_pair, marketprices)
                selected_pairs.append(stalk_pair) if can_select else None
                marketprice_1min = self._marketprice(stalk_pair, period_1min, marketprices)
                pair_repport = {
                    'stalk_start_date': stalk_start_date,
                    'row_start_date': row_start_date,
                    'market_date': _MF.unix_to_date(marketprice_1min.get_time()),
                    Map.pair: stalk_pair.__str__().upper(),
                    **pair_repport
                }
                condition_repports.append(pair_repport)
            write(condition_repports, condition) if len(condition_repports) > 0 else None
        return selected_pairs

    def _stalk_condition_icarus_v13_5_1(self, pair: Pair, marketprices: Map) -> Tuple[bool, dict]:
        period_1min = Broker.PERIOD_1MIN
        period_15min = Broker.PERIOD_15MIN
        N_CANDLE = 60
        TRIGGER_CANDLE_CHANGE = 0.5/100
        TRIGGE_KELTNER = 0.1/100
        def price_change(i: int, open_prices: list[float], close_prices: list[float]) -> float:
            n_open = len(open_prices)
            n_close = len(close_prices)
            if n_open != n_close:
                raise ValueError(f"Price lists must have  the same size, instead '{n_open}'!='{n_close}' (open!=close)")
            return close_prices[i] - open_prices[i]

        def is_price_switch_up(vars_map: Map) -> bool:
            # Check
            price_change_1 = price_change(-1, opens, closes)
            price_change_2 = price_change(-2, opens, closes)
            price_switch_up = (price_change_1 > abs(price_change_2))
            # Put
            vars_map.put(price_switch_up, 'price_switch_up')
            vars_map.put(price_change_1, 'price_change_1')
            vars_map.put(price_change_2, 'price_change_2')
            return price_switch_up

        def is_min_macd_histogram_switch_up(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            macd_map = min_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            min_macd_histogram_switch_up = (histogram[-1] > 0) and (histogram[-2] < 0)
            # Put
            vars_map.put(min_macd_histogram_switch_up, 'min_macd_histogram_switch_up')
            vars_map.put(histogram, 'min_histogram')
            return min_macd_histogram_switch_up

        def is_mean_candle_change_60_above_trigger(vars_map: Map) -> bool:
            mean_candle_change = MarketPrice.mean_candle_variation(opens[-N_CANDLE:], closes[-N_CANDLE:])
            # Check
            mean_positive_candle = mean_candle_change.get(Map.positive, Map.mean)
            mean_candle_change_60_above_trigger = mean_positive_candle >= TRIGGER_CANDLE_CHANGE
            # Put
            vars_map.put(mean_candle_change_60_above_trigger, 'mean_candle_change_60_above_trigger')
            vars_map.put(mean_positive_candle, 'mean_candle_change_60_mean_positive_candle')
            return mean_candle_change_60_above_trigger

        def is_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(child_marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            supertrend_rising = MarketPrice.get_super_trend_trend(closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            # Put
            vars_map.put(supertrend_rising, 'supertrend_rising')
            vars_map.put(supertrend, Map.supertrend)
            return supertrend_rising

        """
        def is_tangent_macd_histogram_positive(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            macd_map = child_marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_macd_histogram_positive = histogram[-1] > histogram[-2]
            # Put
            vars_map.put(tangent_macd_histogram_positive, 'tangent_macd_histogram_positive')
            vars_map.put(histogram, Map.histogram)
            return tangent_macd_histogram_positive

        def is_tangent_min_edited_macd_histogram_positive(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            macd_map = min_marketprice.get_macd(**MarketPrice.MACD_PARAMS_1)
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            tangent_min_edited_macd_histogram_positive = histogram[-1] > histogram[-2]
            # Put
            vars_map.put(tangent_min_edited_macd_histogram_positive, 'tangent_min_edited_macd_histogram_positive')
            vars_map.put(histogram, 'min_edited_histogram')
            return tangent_min_edited_macd_histogram_positive

        def is_min_keltner_roi_above_trigger(vars_map: Map) -> bool:
            min_marketprice.reset_collections()
            keltner_map = min_marketprice.get_keltnerchannel(multiple=1)
            keltner_low = list(keltner_map.get(Map.low))
            keltner_low.reverse()
            keltner_high = list(keltner_map.get(Map.high))
            keltner_high.reverse()
            # Check
            keltner_roi = _MF.progress_rate(keltner_high[-1], keltner_low[-1])
            min_keltner_roi_above_trigger = keltner_roi >= TRIGGE_KELTNER
            # Put
            vars_map.put(min_keltner_roi_above_trigger, 'min_keltner_roi_above_trigger')
            vars_map.put(keltner_roi, 'keltner_roi')
            vars_map.put(keltner_map.get_map(), 'min_keltner')
            return min_keltner_roi_above_trigger

        def is_psar_rising(vars_map: Map) -> bool:
            psar = list(child_marketprice.get_psar())
            psar.reverse()
            psar_rising = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_RISING
            vars_map.put(psar_rising, 'psar_rising')
            vars_map.put(psar, Map.psar)
            return psar_rising

        def is_min_psar_rising(vars_map: Map) -> bool:
            psar = list(min_marketprice.get_psar())
            psar.reverse()
            min_psar_rising = MarketPrice.get_psar_trend(min_closes, psar, -1) == MarketPrice.PSAR_RISING
            vars_map.put(min_psar_rising, 'min_psar_rising')
            vars_map.put(psar, 'min_psar')
            return min_psar_rising

        def is_min_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(min_marketprice.get_super_trend())
            supertrend.reverse()
            # Check
            min_supertrend_rising = MarketPrice.get_super_trend_trend(min_closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            # Put
            vars_map.put(min_supertrend_rising, 'min_supertrend_rising')
            vars_map.put(supertrend, 'min_supertrend')
            return min_supertrend_rising
        """

        vars_map = Map()
        child_marketprice = self._marketprice(pair, period_15min, marketprices)
        min_marketprice = self._marketprice(pair, period_1min, marketprices)
        # Child
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        highs = list(child_marketprice.get_highs())
        highs.reverse()
        opens = list(child_marketprice.get_opens())
        opens.reverse()
        open_times = list(child_marketprice.get_times())
        open_times.reverse()
        # Min
        min_closes = list(min_marketprice.get_closes())
        min_closes.reverse()
        min_opens = list(min_marketprice.get_opens())
        min_opens.reverse()
        min_open_times = list(min_marketprice.get_times())
        min_open_times.reverse()
        # Check
        # can_buy_indicator = is_price_switch_up(vars_map) and is_mean_candle_change_60_above_trigger(vars_map)\
        #     and is_supertrend_rising(vars_map) and is_min_macd_histogram_switch_up(vars_map)\
        #         and is_tangent_macd_histogram_positive(vars_map) and is_tangent_min_edited_macd_histogram_positive(vars_map)\
        #             and is_min_keltner_roi_above_trigger(vars_map) and is_psar_rising(vars_map) and is_min_psar_rising(vars_map) and is_min_supertrend_rising(vars_map)
        can_buy_indicator = is_price_switch_up(vars_map) and is_mean_candle_change_60_above_trigger(vars_map)\
            and is_supertrend_rising(vars_map) and is_min_macd_histogram_switch_up(vars_map)
        # Repport
        min_histogram = vars_map.get('min_histogram')
        keltner_low = vars_map.get('min_keltner', Map.low)
        keltner_middle = vars_map.get('min_keltner', Map.middle)
        keltner_high = vars_map.get('min_keltner', Map.high)
        min_edited_histogram = vars_map.get('min_edited_histogram')
        supertrend = vars_map.get(Map.supertrend)
        histogram = vars_map.get(Map.histogram)
        psar = vars_map.get(Map.psar)
        min_psar = vars_map.get('min_psar')
        min_supertrend = vars_map.get('min_supertrend')
        repport = {
            'can_buy_indicator': can_buy_indicator,
            'price_switch_up': vars_map.get('price_switch_up'),
            'mean_candle_change_60_above_trigger': vars_map.get('mean_candle_change_60_above_trigger'),
            'supertrend_rising': vars_map.get('supertrend_rising'),
            'min_macd_histogram_switch_up': vars_map.get('min_macd_histogram_switch_up'),
            'tangent_macd_histogram_positive': vars_map.get('tangent_macd_histogram_positive'),
            'tangent_min_edited_macd_histogram_positive': vars_map.get('tangent_min_edited_macd_histogram_positive'),
            'min_keltner_roi_above_trigger': vars_map.get('min_keltner_roi_above_trigger'),
            'psar_rising': vars_map.get('psar_rising'),
            'min_psar_rising': vars_map.get('min_psar_rising'),
            'min_supertrend_rising': vars_map.get('min_supertrend_rising'),

            'price_change_1': vars_map.get('price_change_1'),
            'price_change_2': vars_map.get('price_change_2'),

            'mean_candle_change_60_mean_positive_candle': vars_map.get('mean_candle_change_60_mean_positive_candle'),
            
            'TRIGGE_KELTNER': TRIGGE_KELTNER,
            'keltner_roi': vars_map.get('keltner_roi'),

            'closes[-1]': closes[-1],
            'opens[-1]': opens[-1],
            'min_closes[-1]': min_closes[-1],
            'min_opens[-1]': min_opens[-1],
            'supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            'supertrend[-2]': supertrend[-2] if supertrend is not None else None,
            'min_supertrend[-1]': min_supertrend[-1] if min_supertrend is not None else None,
            'min_supertrend[-2]': min_supertrend[-2] if min_supertrend is not None else None,
            'histogram[-1]': histogram[-1] if histogram is not None else None,
            'histogram[-2]': histogram[-2] if histogram is not None else None,
            'min_edited_histogram[-1]': min_edited_histogram[-1] if min_edited_histogram is not None else None,
            'min_edited_histogram[-2]': min_edited_histogram[-2] if min_edited_histogram is not None else None,
            'psar[-1]': psar[-1] if psar is not None else None,
            'psar[-2]': psar[-2] if psar is not None else None,
            'min_psar[-1]': min_psar[-1] if min_psar is not None else None,
            'min_psar[-2]': min_psar[-2] if min_psar is not None else None,
            'min_histogram[-1]': min_histogram[-1] if min_histogram is not None else None,
            'min_histogram[-2]': min_histogram[-2] if min_histogram is not None else None,
            'keltner_low[-1]': keltner_low[-1] if keltner_low is not None else None,
            'keltner_middle[-1]': keltner_middle[-1] if keltner_middle is not None else None,
            'keltner_high[-1]': keltner_high[-1] if keltner_high is not None else None
        }
        return can_buy_indicator, repport

    def _stalk_condition_1(self, pair: Pair, marketprices: Map) -> Tuple[bool, dict]:
        period_5min = Broker.PERIOD_5MIN
        TRIGGER_KELTNER_ROI = 0.5/100
        vars_map = Map()
        marketprice_5min = self._marketprice(pair, period_5min, marketprices)
        keltner_roi = self._stalk_is_keltner_roi_above_trigger(vars_map, marketprice_5min, TRIGGER_KELTNER_ROI)
        price_switch_up = self._stalk_is_price_switch_up(vars_map, marketprice_5min)
        stalk_condition_1 = price_switch_up and keltner_roi
        repport = {
            'stalk_condition_1': stalk_condition_1,
            'price_switch_up': vars_map.get('price_switch_up'),
            'keltner_roi_above_trigger': vars_map.get('keltner_roi_above_trigger'),

            'price_change_1': vars_map.get('price_change_1'),
            'price_change_2': vars_map.get('price_change_2'),
            
            'keltner_roi': vars_map.get('keltner_roi'),
            'keltner_roi_trigger': vars_map.get('keltner_roi_trigger'),

            'keltner_high[-1]': vars_map.get('keltner_high[-1]'),
            'keltner_low[-1]': vars_map.get('keltner_low[-1]')
        }
        return False, repport

    # ••• FUNCTION SELF THREAD STALK UP
    # ••• FUNCTION SELF THREAD MARKET ANALYSE DOWN

    def _manage_market_analyse(self) -> None:
        """
        To manage analyse of market
        """
        while self.is_market_analyse_on():
            _MF.catch_exception(self._analyse_market, Hand.__name__, **{'marketprices': Map()})
            sleep_time = _MF.sleep_time(_MF.get_timestamp(), self._SLEEP_MARKET_ANALYSE)
            time.sleep(sleep_time)

    def _analyse_market(self, marketprices: Map) -> None:
        """
        To print analyse of market's trend
        """
        def join_df(pair: Pair, base_df: pd.DataFrame, to_join: pd.DateOffset) -> pd.DataFrame:
            if base_df.shape[0] == 0:
                base_df = pd.DataFrame({pair: to_join[pair]}, index=to_join.index)
            else:
                base_df = base_df.join(to_join)
            return base_df

        def write(period_str: str, analyse: pd.DataFrame) -> None:
            file_path = self.get_path_file_market_trend(period_str)
            rows = analyse.to_dict('records')
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows, overwrite=True, make_dir=True)

        broker = self.get_broker()
        pairs = self.get_broker_pairs()
        periods = self._REQUIRED_PERIODS
        for period in periods:
            if not self.is_market_analyse_on():
                break
            supertrends_df = pd.DataFrame()
            closes_df = pd.DataFrame()
            for pair in pairs:
                if not self.is_market_analyse_on():
                    break
                marketprice = self._marketprice(pair, period, marketprices)
                open_times = list(marketprice.get_times())
                open_times.reverse()
                closes = list(marketprice.get_closes())
                closes.reverse()
                supertrends = list(marketprice.get_super_trend())
                supertrends.reverse()
                # Close
                new_closes_df = pd.DataFrame({pair: closes}, index=open_times)
                closes_df = join_df(pair, closes_df, new_closes_df)
                # Supertrend
                new_supertrends_df = pd.DataFrame({pair: supertrends}, index=open_times)
                supertrends_df = join_df(pair, supertrends_df, new_supertrends_df)
            # Supertrend str
            supertrends_str_df = pd.DataFrame(columns=closes_df.columns, index=closes_df.index)
            supertrends_str_df[closes_df.columns] = ''
            supertrends_str_df[(closes_df > supertrends_df)] = MarketPrice.SUPERTREND_RISING
            supertrends_str_df[(closes_df < supertrends_df)] = MarketPrice.SUPERTREND_DROPPING
            # Print
            # ••• prepare
            period_str = broker.period_to_str(period)
            analyse_df = pd.DataFrame([], index=supertrends_str_df.index)
            # ••• build market dates
            market_dates = [_MF.unix_to_date(open_time) for open_time in list(analyse_df.index)]
            market_dates_df = pd.DataFrame({Map.date: market_dates}, index=analyse_df.index)
            # ••• build rows to print
            analyse_df[Map.date] = _MF.unix_to_date(_MF.get_timestamp())
            analyse_df['market_date'] = market_dates_df[Map.date]
            analyse_df[Map.period] = period_str
            analyse_df['n_pair'] = supertrends_str_df.shape[1]
            analyse_df['n_rise'] = supertrends_str_df[supertrends_str_df == MarketPrice.SUPERTREND_RISING].count(axis=1)
            analyse_df['rise_rate'] = analyse_df['n_rise']/analyse_df['n_pair']
            analyse_df['n_drop'] = supertrends_str_df[supertrends_str_df == MarketPrice.SUPERTREND_DROPPING].count(axis=1)
            analyse_df['drop_rate'] = analyse_df['n_drop']/analyse_df['n_pair']
            write(period_str, analyse_df)

    # ••• FUNCTION SELF THREAD MARKET ANALYSE UP
    # ••• FUNCTION SELF BUY/SELL DOWN

    def buy(self, pair: Pair, order_type: str, stop: Price = None, limit: Price = None, buy_function: Callable = None) -> Union[str, None]:
        """
        To buy a new position

        Parameters:
        -----------
        pair: Pair
            The pair to buy
        order_type: str
            The type of order to use to buy
        stop: Price=None
            Price for order requiring a stop price
        limit: Price=None
            Price for order requiring a limit price
        buy_function: Callable=None
            function from Hand than define how to execute order

        Returns:
        --------
        return: str
            The buy Order's id if the Order fail to be submitted else None
        """
        if pair.get_right() != self.get_wallet().get_initial().get_asset():
            r_asset_exp = self.get_wallet().get_initial().get_asset()
            raise ValueError(f"The pair to buy's right Asset must be '{r_asset_exp.__str__().upper()}', instead '{pair.__str__().upper()}'")
        if self.is_max_position_reached():
            raise Exception(f"The max number of position allowed '{self.get_max_position()}' is already reached")
        # Order
        broker_class_str = self.get_broker_class()
        amount = self._position_capital()
        prices = self._prepare_algo_price(pair, order_type, amount, stop, limit)
        order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: amount,
            Map.quantity: prices.get(Map.quantity),
            Map.stop: stop,
            Map.limit: limit
        })
        order = Order.generate_broker_order(broker_class_str, order_type, order_params)
        # Trade
        buy_function = buy_function if buy_function is not None else self.condition_true
        trade = HandTrade(order, buy_function=buy_function)
        # Execution
        order_id = None
        self._try_submit(trade)
        if not trade.has_failed(Map.buy):
            # Mark as bought
            self._add_position(trade)
            self._mark_proposition(pair, True)
        else:
            self._add_failed_order(order)
            order_id = order.get_id()
        self._repport_positions()
        self.backup()
        return order_id

    def sell(self, pair: Pair, order_type: str, stop: Price = None, limit: Price = None, sell_function: Callable = None) -> Union[str, None]:
        """
        To sell a new position

        Parameters:
        -----------
        pair: Pair
            The pair to sell
        order_type: str
            The type of order to use to sell
        stop: Price=None
            Price for order requiring a stop price
        limit: Price=None
            Price for order requiring a limit price
        sell_function: Callable = None
            function from Hand than define how to execute order

        Returns:
        --------
        return: str
            The sell Order's id if the Order fail to be submitted else None
        """
        position = self.get_position(pair)
        if not position.has_position():
            raise Exception(f"Must hold '{pair.__str__().upper()}' position before to place sell Order")
        if position.get_sell_order() is not None:
            raise Exception(f"This position '{pair.__str__().upper()}' already has a sell Order")
        # Order
        broker_class_str = self.get_broker_class()
        l_asset = pair.get_left()
        quantity = self.get_wallet().get_position(l_asset)
        order_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: quantity,
            Map.stop: stop,
            Map.limit: limit
        })
        order = Order.generate_broker_order(broker_class_str, order_type, order_params)
        # Trade
        sell_function = sell_function if sell_function is not None else self.condition_true
        position.set_sell_order(order)
        position.set_sell_function(sell_function)
        # Execution
        order_id = None
        self._try_submit(position)
        if position.has_failed(Map.sell):
            self._add_failed_order(order)
            order_id = order.get_id()
        self._repport_positions()
        self.backup()
        return order_id

    def cancel(self, pair: Pair) -> None:
        """
        To cancel Trade if not executed yet\n
        NOTE: Delete Trade from list of position If buy Order is not executed

        Parameters:
        -----------
        pair: Pair
            Pair of the position to cancel
        """
        self._update_orders()
        position = self.get_position(pair)
        broker = self.get_broker()
        failed_order_id = None
        if position.has_failed(Map.buy):
            buy_order = position.get_buy_order()
            failed_order_id = buy_order.get_id()
            self._add_failed_order(buy_order)
            self._remove_position(pair)
        elif position.has_failed(Map.sell):
            sell_order = position.get_sell_order()
            failed_order_id = sell_order.get_id()
            self._add_failed_order(sell_order)
            position.reset_sell_order()
        elif not position.is_executed(Map.buy):
            buy_order = position.get_buy_order()
            broker.cancel(buy_order)
            self._remove_position(pair)
        elif position.has_position():
            sell_order = position.get_sell_order()
            if sell_order is not None:
                broker.cancel(sell_order)
                position.reset_sell_order()
        self._repport_positions()
        self.backup()
        return failed_order_id

    def _try_submit(self, trade: HandTrade) -> None:
        """
        To submit given position to Broker for execution

        Parameters:
        -----------
        trade: HandTrade
            Position to execute
        """
        buy_order = trade.get_buy_order()
        sell_order = trade.get_sell_order()
        if buy_order.get_status() is None:
            if trade.get_buy_function(self)():
                broker = self.get_broker()
                broker.execute(buy_order)
                self.get_wallet().buy(buy_order) if trade.is_executed(Map.buy) else None
        if (trade.is_executed(Map.buy)) and (sell_order is not None) and (sell_order.get_status() is None):
            if trade.get_sell_function(self)():
                broker = self.get_broker()
                broker.execute(sell_order)
                self.get_wallet().sell(sell_order) if trade.is_executed(Map.sell) else None

    # ••• FUNCTION SELF BUY/SELL UP
    # ••• FUNCTION SELF BUY/SELL CONDITION DOWN

    def condition_true(self) -> bool:
        """
        The default condition to buy/sell position
        """
        return True

    # ••• FUNCTION SELF BUY/SELL CONDITION UP
    # ••• FUNCTION SELF OTHERS DOWN

    def add_streams(self) -> None:
        """
        To add streams to Broker's socket
        """
        def get_streams(broker: Broker, pairs: List[Pair], periods: List[int]) -> List[str]:
            periods = _MF.remove_duplicates(periods)
            streams = []
            for period in periods:
                streams = [
                    *streams,
                    *[broker.generate_stream(Map({Map.pair: pair, Map.period: period})) for pair in pairs]
                ]
            streams = _MF.remove_duplicates(streams)
            return streams
        broker_pairs = self.get_broker_pairs()
        required_periods = self._REQUIRED_PERIODS
        broker = self.get_broker()
        streams = get_streams(broker, broker_pairs, required_periods)
        broker.add_streams(streams)

    def _marketprice(self, pair: Pair, period: int, marketprices: Map) -> MarketPrice:
        pair_str = pair.__str__()
        marketprice = marketprices.get(pair_str, period)
        if marketprice is None:
            broker = self.get_broker()
            n_period = self._N_PERIOD
            marketprice = MarketPrice.marketprice(broker, pair, period, n_period)
            marketprices.put(marketprice, pair_str, period)
        return marketprice

    def _json_encode_to_dict(self) -> dict:
        attributes = self.__dict__.copy()
        for attribute, value in attributes.items():
            if isinstance(value, Broker):
                attributes[attribute] = None
            if isinstance(value, Map) and (len(value.get_map()) > 0) and isinstance(value.get(value.get_keys()[-1]), Orders):
                attributes[attribute] = None
            if Map.backup in attribute:
                attributes[attribute] = None
        return attributes

    def backup(self, force: bool = False) -> None:
        backup = self._get_backup()
        json_str = self.json_encode()
        if force or (backup != json_str):
            hand_id = self.get_id()
            hand_file_path = self.get_path_file_backup(hand_id)
            FileManager.write(hand_file_path, json_str, overwrite=True, make_dir=True)
            self._set_backup(json_str)

    # ••• FUNCTION SELF OTHERS UP
    # ——————————————————————————————————————————— FUNCTION SELF UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————

    @classmethod
    def get_path_file_backup(cls, hand_id: str) -> str:
        """
        To get the file path to where to store Hand instance

        Parameters:
        -----------
        hand_id: str
            ID of a Hand object

        Returns:
        --------
        return: str
            The file path to where to store Hand instance
        """
        stage = Config.get(Config.STAGE_MODE)
        file_pattern = Config.get(Config.FILE_SAVE_HAND)
        hand_file_path = file_pattern.replace('$stage', stage).replace('$class', cls.__name__).replace('$id', hand_id)
        return hand_file_path

    @classmethod
    def get_path_dir_hands(cls) -> str:
        """
        To get path directory to where all Hand are stored
        """
        hand_id = "fake_id"
        hand_file_path = cls.get_path_file_backup(hand_id)
        splitted = hand_file_path.split('/')
        path_dir_hands = '/'.join(splitted[:-2]) + '/'
        return path_dir_hands

    @classmethod
    def load(cls, hand_id: str) -> 'Hand':
        """
        To load the most recent backup

        Parameters:
        -----------
        hand_id: str
            ID of a Hand to load

        Returns:
        --------
        return: Hand
            Hand instance
        """
        hand_file_path = cls.get_path_file_backup(hand_id)
        hand_dir_path = FileManager.path_to_dir(hand_file_path)
        backup_files = _MF.catch_exception(FileManager.get_files, cls.__name__, **{Map.path: hand_dir_path})
        if (backup_files is None) or len(backup_files) == 0:
            raise Exception(f"There's not Hand backup with this id '{hand_id}'")
        most_recent_file_path = hand_dir_path + backup_files[-1]
        json_str = FileManager.read(most_recent_file_path)
        hand = MyJson.json_decode(json_str)
        return hand

    @classmethod
    def list_hand_ids(cls) -> List[str]:
        """
        To list id of Hand stored Hand available for load
        """
        path_dir_hands = cls.get_path_dir_hands()
        hand_ids = FileManager.get_dirs(path_dir_hands, make_dir=True)
        return hand_ids

    @classmethod
    def concat_order_ref_id(cls, positions: Dict[str, HandTrade]) -> Tuple[str, List[Order]]:
        ref_ids = []
        position_orders = []
        for _, position in positions.items():
            buy_order = position.get_buy_order()
            sell_order = position.get_sell_order()
            ref_ids.append(position.get_id())
            ref_ids.append(str(id(buy_order)))
            ref_ids.append(str(id(sell_order)))
            position_orders.append(buy_order)
            position_orders.append(sell_order) if sell_order is not None else None
        new_ref_id = '-'.join(ref_ids)
        return new_ref_id, position_orders

    @classmethod
    def _prepare_algo_price(cls, pair: Pair, order_type: str, amount: Price, stop: Price, limit: Price) -> Map:
        """
        To convert amount price to prices require foor algo Order
        """
        l_asset = pair.get_left()
        prices = {}
        prices[Map.amount] = amount
        prices[Map.stop] = stop
        prices[Map.limit] = limit
        if order_type == Order.TYPE_STOP:
            prices[Map.quantity] = Price(amount/stop, l_asset)
        elif order_type in [Order.TYPE_LIMIT, Order.TYPE_STOP_LIMIT]:
            prices[Map.quantity] = Price(amount/limit, l_asset)
        return Map(prices)

    @classmethod
    def get_path_file_stalk(cls, condition: Callable) -> str:
        """
        To get path to file where to store stalk of market

        Parameters:
        -----------
        condition: Callable
            Function executed to avaluate if a pair is interesting to buy when stalking market

        Returns:
        --------
        return: str
            Path to file where to store stalk of market
        """
        base_path = Config.get(Config.DIR_SAVE_MARKET_STALK)
        func_name = condition.__name__
        extension = ".csv"
        file_path = base_path.replace(extension, f'-{func_name}') + extension
        return file_path

    @classmethod
    def get_path_file_market_trend(cls, period_str: str) -> str:
        """
        To get path to file where to store analyse of market's trend
        """
        file_path_pattern = Config.get(Config.FILE_VIEW_HAND_MARKET_TREND)
        file_path = file_path_pattern.replace('$period', period_str)
        return file_path

    @classmethod
    def _stalk_price_change(cls, i: int, open_prices: list[float], close_prices: list[float]) -> float:
        n_open = len(open_prices)
        n_close = len(close_prices)
        if n_open != n_close:
            raise ValueError(f"Price lists must have  the same size, instead '{n_open}'!='{n_close}' (open!=close)")
        return close_prices[i] - open_prices[i]

    @classmethod
    def _stalk_is_price_switch_up(cls, vars_map: Map, marketprice: MarketPrice) -> bool:
        open_prices = list(marketprice.get_opens())
        open_prices.reverse()
        close_prices = list(marketprice.get_closes())
        close_prices.reverse()
        # Check
        price_change_1 = cls._stalk_price_change(-1, open_prices, close_prices)
        price_change_2 = cls._stalk_price_change(-2, open_prices, close_prices)
        price_switch_up = (price_change_1 >= abs(price_change_2) > 0)
        # Put
        vars_map.put(price_switch_up, 'price_switch_up')
        vars_map.put(price_change_1, 'price_change_1')
        vars_map.put(price_change_2, 'price_change_2')
        return price_switch_up

    @classmethod
    def _stalk_is_keltner_roi_above_trigger(cls, vars_map: Map, marketprice: MarketPrice, roi_trigger: float) -> bool:
        marketprice.reset_collections()
        keltner_map = marketprice.get_keltnerchannel(multiple=1)
        keltner_low = list(keltner_map.get(Map.low))
        keltner_low.reverse()
        keltner_high = list(keltner_map.get(Map.high))
        keltner_high.reverse()
        # Check
        keltner_roi = _MF.progress_rate(keltner_high[-1], keltner_low[-1])
        keltner_roi_above_trigger = keltner_roi >= roi_trigger
        # Put
        vars_map.put(keltner_roi_above_trigger, 'keltner_roi_above_trigger')
        vars_map.put(keltner_roi, 'keltner_roi')
        vars_map.put(roi_trigger, 'keltner_roi_trigger')
        vars_map.put(keltner_high[-1], 'keltner_high[-1]')
        vars_map.put(keltner_low[-1], 'keltner_low[-1]')
        return keltner_roi_above_trigger

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Hand(Price(0, '@json'), Broker)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
