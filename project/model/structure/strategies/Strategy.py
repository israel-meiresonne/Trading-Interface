from abc import ABC, abstractmethod
from typing import Callable, List

import pandas as pd

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Hand import Hand
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Strategy(Hand, ABC):
    PREFIX_ID =     "strategy_"
    _SLEEP_TRADE =  10
    _MAX_POSITION = 5

    def __init__(self, capital: Price, broker_class: Callable, pair: Pair = None) -> None:
        self.__pair =           None
        self.__sleep_trade =    None
        super().__init__(capital, broker_class)
        if pair is not None:
            self._set_pair(pair)
            super().set_max_position(1)
        self.set_sleep_trade(self._SLEEP_TRADE)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN —————————————————————————————————————————

    def set_max_position(self, max_position: int) -> None:
        if self.get_pair() is not None:
            raise Exception(f"Can't update max position when attribut Strategy.pair is set")
        super().set_max_position(max_position)

    def get_broker_pairs(self) -> List[Pair]:
        pair = self.get_pair()
        if pair is not None:
            pairs = [pair]
        else:
            pairs = super().get_broker_pairs()
        return pairs

    def _set_pair(self, pair: Pair) -> None:
        capital = self.get_wallet().get_initial()
        if pair.get_right() != capital.get_asset():
            raise TypeError(f"The pair's right Asset '{pair.__str__().upper()}' must match capital's Asset '{capital}'")
        self.__pair = pair

    def get_pair(self) -> Pair:
        """
        To get the only pair allowed to trade

        Return:
        -------
        return: Pair
            Pair to trade
        """
        return self.__pair

    def set_sleep_trade(self, sleep_time: float) -> None:
        if not isinstance(sleep_time, (int, float)):
            raise TypeError(f"The trade's sleep time most be of types {' or '.join((int, float))}, intsead '{sleep_time}(type={type(sleep_time)})'")
        self.__sleep_trade = sleep_time

    def get_sleep_trade(self) -> float:
        """
        To get interval between two trade
        """
        return self.__sleep_trade

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ———————————————————————————————————————————
    # ——————————————————————————————————————————— SELF FUNCTION DOWN ——————————————————————————————————————————————————

    @abstractmethod
    def trade(self) -> int:
        """
        To automatically buy and/or sell positions

        Return:
        -------
        return: int
            The sleep time before the next call of this function
        """
        pass

    # ——————————————————————————————————————————— SELF FUNCTION UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN ————————————————————————————————————————————————
    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST DOWN

    @classmethod
    def backtest(cls, broker: Broker, pair: Pair, starttime: int, endtime: int) -> None:
        Config.update(Config.FAKE_API_START_END_TIME, {Map.start: starttime, Map.end: endtime})
        trades, buy_conditions, sell_conditions, stats = cls._backtest_loop(broker, pair, endtime)
        # Buy
        if len(buy_conditions) > 0:
            buy_file_path = cls.get_path_backtest_file(Map.condition, **{Map.side: Map.buy})
            buy_field = list(buy_conditions[0].keys())
            FileManager.write_csv(buy_file_path, buy_field, buy_conditions, overwrite=False, make_dir=True)
        # Sell
        if len(sell_conditions) > 0:
            sell_file_path = cls.get_path_backtest_file(Map.condition, **{Map.side: Map.sell})
            sell_field = list(sell_conditions[0].keys())
            FileManager.write_csv(sell_file_path, sell_field, sell_conditions, overwrite=False, make_dir=True)
        # Trades
        if len(trades) > 0:
            trade_file_path = cls.get_path_backtest_file(Map.test)
            rows = []
            for trade in trades:
                row = {}
                row[Map.date] =             _MF.unix_to_date(_MF.get_timestamp())
                row[Map.pair] =             trade[Map.buy][Map.pair]
                row[Map.start] =            _MF.unix_to_date(stats[Map.start])
                row[Map.end] =              _MF.unix_to_date(stats[Map.end])
                row['trade_id'] =           trade[Map.id]
                row['trade_settime'] =      trade[Map.settime]
                row['trade_date'] =         _MF.unix_to_date(trade[Map.settime])
                row['buy_order_id'] =       trade[Map.buy][Map.id]
                row['buy_order_settime'] =  trade[Map.buy][Map.settime]
                row['buy_order_date'] =     _MF.unix_to_date(trade[Map.buy][Map.settime])
                row['buy_time'] =           trade[Map.buy][Map.time]
                row['buy_date'] =           _MF.unix_to_date(trade[Map.buy][Map.time])
                row['buy_price'] =          trade[Map.buy][Map.execution]
                row['buy_fee'] =            trade[Map.buy][Map.fee]
                row['sell_order_id'] =      trade[Map.sell][Map.id]
                row['sell_order_settime'] = trade[Map.sell][Map.settime]
                row['sell_order_date'] =    _MF.unix_to_date(trade[Map.sell][Map.settime])
                row['sell_time'] =          trade[Map.sell][Map.time]
                row['sell_date'] =          _MF.unix_to_date(trade[Map.sell][Map.time])
                row['sell_price'] =         trade[Map.sell][Map.execution]
                row['sell_fee'] =           trade[Map.sell][Map.fee]
                row[Map.roi] =              trade[Map.roi]()
                row['roi_losses'] =         row[Map.roi] if row[Map.roi] < 0 else None
                row['roi_wins'] =           row[Map.roi] if row[Map.roi] > 0 else None
                row['roi_neutrals'] =       row[Map.roi] if row[Map.roi] == 0 else None
                row['min_roi_position'] =   _MF.progress_rate(trade[Map.minimum], trade[Map.buy][Map.execution]) - trade[Map.buy][Map.fee]
                row['max_roi_position'] =   _MF.progress_rate(trade[Map.maximum], trade[Map.buy][Map.execution]) - trade[Map.buy][Map.fee]
                rows.append(row)
            pd_rows = pd.DataFrame(rows)
            roi_wins = pd_rows['roi_wins']
            n_win = roi_wins.count()
            roi_losses = pd_rows['roi_losses']
            n_loss = roi_losses.count()
            pd_rows.loc[:,'min_roi'] =              pd_rows[Map.roi].min()
            pd_rows.loc[:,'mean_roi'] =             pd_rows[Map.roi].mean()
            pd_rows.loc[:,'max_roi'] =              pd_rows[Map.roi].max()
            pd_rows.loc[:,'min_win_roi'] =          roi_wins.min()
            pd_rows.loc[:,'mean_win_roi'] =         roi_wins.mean()
            pd_rows.loc[:,'max_win_roi'] =          roi_wins.max()
            pd_rows.loc[:,'min_loss_roi'] =         roi_losses.min()
            pd_rows.loc[:,'mean_loss_roi'] =        roi_losses.mean()
            pd_rows.loc[:,'max_loss_roi'] =         roi_losses.max()
            pd_rows.loc[:,'sum_roi'] =              pd_rows[Map.roi].sum()
            pd_rows.loc[:,'sum_fee'] =              pd_rows['buy_fee'].sum() + pd_rows['sell_fee'].sum()
            pd_rows.loc[:,'sum_roi_no_fee'] =       pd_rows.loc[:,'sum_roi'] + pd_rows.loc[:,'sum_fee']
            pd_rows.loc[:,'start_price'] =          stats[Map.open]
            pd_rows.loc[:,'end_price'] =            stats[Map.close]
            pd_rows.loc[:,'higher_price'] =         stats[Map.high]
            pd_rows.loc[:,'lower_price'] =          stats[Map.low]
            pd_rows.loc[:,'market_performence'] =   _MF.progress_rate(stats[Map.close], stats[Map.open])
            pd_rows.loc[:,'max_profit'] =           _MF.progress_rate(stats[Map.high], stats[Map.low])
            pd_rows.loc[:,'n_trade'] =              pd_rows.shape[0]
            pd_rows.loc[:,'n_win'] =                n_win
            pd_rows.loc[:,'win_rate'] =             n_win/pd_rows.shape[0]
            pd_rows.loc[:,'n_loss'] =               n_loss
            pd_rows.loc[:,'loss_rate'] =            n_loss/pd_rows.shape[0]
            FileManager.write_csv(trade_file_path, pd_rows.columns, pd_rows.replace({float('nan'): None}).to_dict('records'), overwrite=False, make_dir=True)

    @classmethod
    def _backtest_loop(cls, broker: Broker, pair: Pair, endtime: int) -> tuple[list[dict], list[dict], list[dict]]:
        def output(i: int, marketprice: MarketPrice, output_starttime: int, output_n_turn: int) -> tuple[int, int]:
            output_turn = i
            output_message = f"Backtest '{pair_str.upper()}' on '{_MF.unix_to_date(marketprice.get_time())}'"
            if i == 0:
                output_starttime = _MF.get_timestamp()
                output_n_turn = int((endtime - marketprice.get_time())/60)
            output = _MF.loop_progression(output_starttime, output_turn, output_n_turn, output_message)
            _MF.static_output(output)
            return output_starttime, output_n_turn
        def break_loop(i: int, market_params: dict) -> tuple[bool, MarketPrice]:
            _MF.update_bot_trade_index(i)
            marketprice = _MF.catch_exception(cls._marketprice, cls.__name__, repport=False, **market_params)
            return (not isinstance(marketprice, MarketPrice)), marketprice
        def update_stats(i: int, stats: dict, marketprice: MarketPrice) -> None:
            close = marketprice.get_close()
            open_time = marketprice.get_time()
            marketprice_np = marketprice.to_pd()
            high = float(marketprice_np.loc[marketprice_np.index[-1], Map.high])
            low = float(marketprice_np.loc[marketprice_np.index[-1], Map.low])
            open_price = float(marketprice_np.loc[marketprice_np.index[-1], Map.open])
            if i == 0:
                stats[Map.start] = open_time
                stats[Map.open] = open_price
            stats[Map.end] = open_time
            stats[Map.close] = close
            stats[Map.high] = high if ((stats[Map.high] is None) or (high > stats[Map.high])) else stats[Map.high]
            stats[Map.low] = low if ((stats[Map.low] is None) or (low < stats[Map.low])) else stats[Map.low]
        pair_str = pair.__str__()
        required_periods = cls._REQUIRED_PERIODS
        required_periods.sort()
        streams = broker.generate_streams([pair], required_periods)
        broker.add_streams(streams)
        market_params = {
            Map.broker: broker,
            Map.pair:   pair,
            Map.period: Broker.PERIOD_1MIN
        }
        trade = None
        trades = []
        buy_conditions = []
        sell_conditions = []
        stats = {
            Map.start:  None,
            Map.end:    None,
            Map.open:   None,
            Map.close:  None,
            Map.high:   None,
            Map.low:    None
        }
        #
        output_starttime = None
        output_n_turn = None
        #
        i = -1
        while True:
            # Manage Loop
            i += 1
            market_params['marketprices'] = marketprices = Map()
            can_break_loop, marketprice = break_loop(i, market_params)
            if can_break_loop:
                break
            # Print time
            output_starttime, output_n_turn = output(i, marketprice, output_starttime, output_n_turn)
            # Stats
            update_stats(i, stats, marketprice)
            # Trade
            cls._backtest_loop_inner(broker, marketprices, pair, trade, buy_conditions, sell_conditions)
            # Execution
            cls._backtest_execute_trade(broker, marketprices, trade) if trade is not None else None
            if (trade is not None) \
                and (trade[Map.buy][Map.status] == Order.STATUS_COMPLETED) \
                and (trade[Map.sell] is not None) \
                and (trade[Map.sell][Map.status] == Order.STATUS_COMPLETED):
                trades.append(trade)
                trade = None
        print() # To clean static print output()
        return trades, buy_conditions, sell_conditions, stats

    @classmethod
    @abstractmethod
    def _backtest_loop_inner(cls, broker: Broker, marketprices: Map, pair: Pair, buy_conditions: list, sell_conditions: list) -> None:
        pass

    @classmethod
    def _print_trade(cls, trade: dict, state_comment: str) -> None:
        def print_trade(file_path: str, trade: dict, state_comment: str) -> None:
            flattened_trade = flat_trade(trade)
            flattened_trade = {
                'print_time': _MF.unix_to_date(_MF.get_timestamp()),
                'state_comment': state_comment,
                **flattened_trade
            }
            fields = list(flattened_trade.keys())
            rows = [flattened_trade]
            FileManager.write_csv(file_path, fields, rows, overwrite=False, make_dir=True)
        def print_columns(file_path: str) -> None:
            empty_trade = cls._backtest_get_trade_skull()
            empty_trade[Map.buy] = cls._backtest_get_order_skull()
            empty_trade[Map.sell] = cls._backtest_get_order_skull()
            print_trade(file_path, empty_trade, '')
        def flat_trade(trade: dict) -> dict:
            flattened_trade = {}
            for attribut, value in trade.items():
                if isinstance(value, dict):
                    dict_value = {f'{attribut}_{k}': v for k, v in value.items()}
                    flattened_trade = {
                        **flattened_trade,
                        **dict_value
                    }
                else:
                    flattened_trade[attribut] = value if (not isinstance(value, Callable)) else None
            return flattened_trade
        file_path = cls.get_path_backtest_file(Map.trade)
        print_columns(file_path) if not FileManager.exist_file(file_path) else None
        print_trade(file_path, trade, state_comment)

    @classmethod
    def _backtest_get_trade_skull(cls) -> dict:
        trade = {
            Map.id:         None,
            Map.settime:    None,
            Map.maximum:    None,
            Map.minimum:    None,
            Map.roi:        None,
            Map.buy:        None,
            Map.sell:       None
        }
        return trade

    @classmethod
    def _backtest_new_trade(cls, broker: Broker, marketprices: Map, pair: Pair, order_type: str, limit: float = None, stop: float = None) -> dict:
        """
        | Keys              | Type          | Documentation                                                         |
        | ----------------- | ------------- | --------------------------------------------------------------------- |
        | dict[Map.id]      | {str}         | Trade's id                                                            |
        | dict[Map.settime] | {int}         | Trade's set time in second                                            |
        | dict[Map.maximum] | {float}       | The max price reached between the execution of the buy and sell order |
        | dict[Map.minimum] | {float}       | The min price reached between the execution of the buy and sell order |
        | dict[Map.roi]     | {Func}        | Function that return Trade's ROI                                      |
        | dict[Map.buy]     | {order{dict}} | The buy order                                                         |
        | dict[Map.sell]    | {order{dict}} | The sell order                                                        |
        """
        period_1min = Broker.PERIOD_1MIN
        cls._backtest_check_type(broker, Broker)
        cls._backtest_check_type(pair, Pair)
        cls._backtest_check_type(marketprices, Map)
        buy_order = cls.__backtest_new_order(broker, marketprices, pair, Map.buy, order_type, limit, stop)
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        open_time = marketprice.get_time()
        trade = cls._backtest_get_trade_skull()
        trade[Map.id] =         f'trade_{open_time}'
        trade[Map.settime] =    open_time
        trade[Map.maximum] =    None
        trade[Map.minimum] =    None
        trade[Map.buy] =        buy_order
        trade[Map.sell] =       None
        trade[Map.roi] =        lambda : _MF.progress_rate(trade[Map.sell][Map.execution], trade[Map.buy][Map.execution]) - (trade[Map.sell][Map.fee] + trade[Map.buy][Map.fee])
        cls._print_trade(trade, 'NEW_TRADE')
        return trade

    @classmethod
    def _backtest_trade_set_sell_order(cls, broker: Broker, marketprices: Map, trade: dict, order_type: str, limit: float = None, stop: float = None) -> None:
        side = Map.sell
        pair = trade[Map.buy][Map.pair]
        sell_order = cls.__backtest_new_order(broker, marketprices, pair, side, order_type, limit=limit, stop=stop)
        trade[side] = sell_order
        cls._print_trade(trade, 'TRADE_SET_SELL_ORDER')

    @classmethod
    def _backtest_update_trade(cls, trade: dict, side: str, new_status: str) -> None:
        cls.__backtest_update_order(trade[side], new_status)
        if (new_status == Order.STATUS_CANCELED) and (side == Map.sell):
            trade[side] = None
        cls._print_trade(trade, 'UPDATE_TRADE')

    @classmethod
    def _backtest_execute_trade(cls, broker: Broker, marketprices: Map, trade: dict) -> None:
        if trade[Map.buy][Map.status] is None:
            order = trade[Map.buy]
        elif (trade[Map.buy][Map.status] == Order.STATUS_COMPLETED) and (trade[Map.sell][Map.status] is None):
            order = trade[Map.sell]
        else:
            raise Exception(f"Unknown state buy_status='{trade[Map.buy][Map.status]}', sell_status='{trade[Map.sell][Map.status]}'")
        cls._backtest_execute_order(broker, marketprices, order) if order is not None else None
        cls.__backtest_trade_set_exetremums(broker, marketprices, trade)
        cls._print_trade(trade, 'EXECUTE_TRADE')

    @classmethod
    def __backtest_trade_set_exetremums(cls, broker: Broker, marketprices: Map, trade: dict) -> None:
        if trade[Map.buy][Map.status] == Order.STATUS_COMPLETED:
            period_1min = Broker.PERIOD_1MIN
            pair = trade[Map.buy][Map.pair]
            marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
            marketprice_np = marketprice.to_pd()
            buy_time = trade[Map.buy][Map.time]
            sell_time = trade[Map.sell][Map.time] if ((trade[Map.sell] is not None) and (trade[Map.sell][Map.status] == Order.STATUS_COMPLETED)) else marketprice.get_time()
            hold_interval = marketprice_np[(marketprice_np[Map.time] > buy_time) & (marketprice_np[Map.time] <= sell_time)]
            if hold_interval.shape[0] > 0:
                trade[Map.maximum] = float(hold_interval[Map.high].max())
                trade[Map.minimum] = float(hold_interval[Map.low].min())

    @classmethod
    def _backtest_get_order_skull(cls) -> dict:
        order = {
            Map.id:         None,
            Map.settime:    None,
            Map.pair:       None,
            Map.side:       None,
            Map.type:       None,
            Map.status:     None,
            Map.market:     None,
            Map.limit:      None,
            Map.stop:       None,
            Map.time:       None,
            Map.timestamp:  None,
            Map.execution:  None,
            Map.fee:        None
        }
        return order

    @classmethod
    def __backtest_new_order(cls, broker: Broker, marketprices: Map, pair: Pair, side: str, order_type: str, limit: float = None, stop: float = None) -> dict:
        """
        | key                 | type    | Documentation                                                 |
        | ------------------- | ------- | ------------------------------------------------------------- |
        | dict[Map.id]        | {str}   | Order's id                                                    |
        | dict[Map.settime]   | {int}   | Order's set time in second                                    |
        | dict[Map.pair]      | {Pair}  | Order's Pair                                                  |
        | dict[Map.side]      | {str}   | Order's side (buy, sell)                                      |
        | dict[Map.type]      | {str}   | Order's type (market, limit, stop_loss, stop_limit)           |
        | dict[Map.status]    | {str}   | Order's execution status                                      |
        | dict[Map.market]    | {float} | Market's close price at order's creation                      |
        | dict[Map.limit]     | {float} | The limit price                                               |
        | dict[Map.stop]      | {float} | The stop price                                                |
        | dict[Map.time]      | {int}   | The execution time in second                                  |
        | dict[Map.timestamp] | {int}   | Open Time (in second) of when the stop price has been reached |
        | dict[Map.execution] | {float} | The execution price                                           |
        | dict[Map.fee]       | {float} | The fee rate at execution                                     |
        """
        period_1min = Broker.PERIOD_1MIN
        cls._backtest_check_type(pair, Pair)
        cls._backtest_check_allowed_values(side, [Map.buy, Map.sell])
        cls._backtest_check_allowed_values(order_type, Order.TYPES)
        cls._backtest_check_type(limit, (int, float)) if limit is not None else None
        cls._backtest_check_type(stop, (int, float)) if stop is not None else None
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        open_time = marketprice.get_time()
        close = marketprice.get_close()
        price_stamp = close
        order = cls._backtest_get_order_skull()
        order[Map.id] =         f'order_{open_time}'
        order[Map.settime] =    open_time
        order[Map.pair] =       pair
        order[Map.side] =       side
        order[Map.type] =       order_type
        order[Map.status] =     None
        order[Map.market] =     price_stamp
        order[Map.limit] =      limit
        order[Map.stop] =       stop
        order[Map.time] =       None
        order[Map.timestamp] =  None
        order[Map.execution] =  None
        order[Map.fee] =        None
        return order

    @classmethod
    def __backtest_update_order(cls, order: dict, new_status: str, exec_time: int = None, exec_price: float = None, fee: float = None) -> None:
        if order[Map.status] in Order.FINAL_STATUS:
            raise ValueError(f"Can't update order's status '{order[Map.status]}' because it's final")
        if new_status == Order.STATUS_COMPLETED:
            cls._backtest_check_type(exec_time, (int, float))
            cls._backtest_check_type(exec_price, (int, float))
            cls._backtest_check_type(fee, (int, float))
            order[Map.status] = new_status
            order[Map.time] = exec_time
            order[Map.execution] = exec_price
            order[Map.fee] = fee
        elif new_status == Order.STATUS_SUBMITTED:
            order[Map.status] = new_status
        elif new_status == Order.STATUS_CANCELED:
            order[Map.status] = new_status
        else:
            raise ValueError(f"This order status '{new_status}' is not supported")

    @classmethod
    def _backtest_execute_order(cls, broker: Broker, marketprices: Map, order: dict) -> None:
        if order[Map.status] in Order.FINAL_STATUS:
            raise ValueError(f"Can't update order's status '{order[Map.status]}' because it's final")
        period_1min = Broker.PERIOD_1MIN
        pair = order[Map.pair]
        fee_rates = broker.get_trade_fee(pair)
        maker_fee_rate = fee_rates.get(Map.maker)
        taker_fee_rate = fee_rates.get(Map.taker)
        order_type = order[Map.type]
        marketprice = cls._marketprice(broker, pair, period_1min, marketprices)
        marketprice_pd = marketprice.to_pd()
        if order_type == Order.TYPE_MARKET:
            exec_time = int(marketprice_pd.loc[marketprice_pd.index[-1], Map.time])
            exec_price = float(marketprice_pd.loc[marketprice_pd.index[-1], Map.close])
            cls.__backtest_update_order(order, Order.STATUS_COMPLETED, exec_time=exec_time, exec_price=exec_price, fee=taker_fee_rate)
        elif (order_type == Order.TYPE_LIMIT) or ((order_type == Order.TYPE_STOP_LIMIT) and (order[Map.timestamp] is not None)):
            cls.__backtest_update_order(order, Order.STATUS_SUBMITTED)
            settime = order[Map.settime] if (order_type == Order.TYPE_LIMIT) else order[Map.timestamp]
            side = order[Map.side]
            limit = order[Map.limit]
            sub_marketprice = marketprice_pd[marketprice_pd[Map.time] >= settime]
            trigger_prices = sub_marketprice[sub_marketprice[Map.low] <= limit] \
                if side == Map.buy else sub_marketprice[sub_marketprice[Map.high] >= limit]
            if trigger_prices.shape[0] > 0:
                exec_time = int(trigger_prices.loc[trigger_prices.index[0], Map.time])
                cls.__backtest_update_order(order, Order.STATUS_COMPLETED, exec_time=exec_time, exec_price=limit, fee=maker_fee_rate)
        elif order_type == Order.TYPE_STOP:
            raise Exception(f"Must implement order type '{Order.TYPE_STOP}'")
        elif order_type == Order.TYPE_STOP_LIMIT:
            cls.__backtest_update_order(order, Order.STATUS_SUBMITTED)
            settime = order[Map.settime]
            side = order[Map.side]
            stop = order[Map.stop]
            price_stamp = order[Map.market]
            is_stamp_above = price_stamp > stop
            sub_marketprice = marketprice_pd[marketprice_pd[Map.time] >= settime]
            if is_stamp_above:
                trigger_prices = sub_marketprice[sub_marketprice[Map.low] <= stop]
            else:
                trigger_prices = sub_marketprice[sub_marketprice[Map.high] >= stop]
            if trigger_prices.shape[0] > 0:
                reach_time = trigger_prices.loc[trigger_prices.index[0], Map.time]
                order[Map.timestamp] = reach_time
                cls._backtest_execute_order(broker, marketprices, order)
        else:
            raise Exception(f"Unknown order type '{order_type}'")

    @classmethod
    def _backtest_check_type(cls, value, expected_type) -> None:
        if not isinstance(value, expected_type):
            raise TypeError(f"Expected type '{expected_type}', instead '{type(value)}'")

    @classmethod
    def _backtest_check_allowed_values(cls, value, alloweds: list) -> None:
        if value not in alloweds:
            raise ValueError(f"Value must be '{' or '.join(alloweds)}', instead '{value} (type={type(value)})'")

    @classmethod
    def _backtest_condition_add_prefix(cls, conditions: dict, pair, marketprice: MarketPrice) -> dict:
        if marketprice.get_period_time() != Broker.PERIOD_1MIN:
            raise ValueError(f"MarketPrice's period must be '{Broker.PERIOD_1MIN}', instead '{marketprice.get_period_time()}'")
        conditions = {
            Map.date:   _MF.unix_to_date(_MF.get_timestamp()),
            Map.market: _MF.unix_to_date(marketprice.get_time()),
            Map.time:   marketprice.get_time(),
            Map.pair:   pair,
            **conditions
        }
        return conditions

    @classmethod
    def get_path_backtest_file(cls, file: str, **kwargs) -> str:
        if file == Map.test:
            file_base = Config.get(Config.FILE_BACKTEST_TEST)
        elif file == Map.trade:
            file_base = Config.get(Config.FILE_BACKTEST_TRADE)
        elif file == Map.condition:
            file_base = Config.get(Config.FILE_BACKTEST_CONDITION)
            file_base = file_base.replace('$side', kwargs[Map.side])
        else:
            raise ValueError(f"Unkwon file '{file}'")
        file_path = file_base.replace('$class', cls.__name__)
        return file_path

    # ––––––––––––––––––––––––––––––––––––––––––– BACKTEST UP
    # ––––––––––––––––––––––––––––––––––––––––––– STATIC DOWN

    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        To get all available Strategy

        Returns:
        --------
        :return: List[str]
            List of available Strategy
        """
        path = Config.get(Config.DIR_STRATEGIES)
        return FileManager.get_dirs(path)

    # ––––––––––––––––––––––––––––––––––––––––––– STATIC UP
    # ——————————————————————————————————————————— STATIC FUNCTION UP ——————————————————————————————————————————————————
