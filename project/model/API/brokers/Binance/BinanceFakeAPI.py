from json import dumps as json_encode
import re as rgx
from typing import Any

from requests.models import Response

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.Bot import Bot
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.BrokerResponse import BrokerResponse
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair


class BinanceFakeAPI(BinanceAPI):
    _FILE_SAVE_ORDER_REQUESTS = Config.get(Config.DIR_SAVE_ORDER_RQ)
    _FILE_LOGS = Config.get(Config.DIR_SAVE_FAKE_API_RQ)
    _FILE_LOAD_ORDERS = Config.get(Config.FILE_BINANCE_FAKE_API_ORDERS)
    _DIR_MARKET_HISTORICS = Config.get(Config.DIR_MARKET_HISTORICS)
    _CONST_INITIAL_INDEX = 60 * BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD     # 60 000, to initialize index's position
    _CONST_MIN_PERIOD_MILLI = 60 * 1000     # Period interval of the min period available all in millisecond
    _VARS = None
    """
    _VARS[Map.market][pair_merged{str}][period{int}]:   {List[list]}    # pair_merged format: 'DOGEUSDT', period in second
    _VARS[Map.index]:                                   {int|None}      # Trade index of a Bot
    """
    _ORDERS = None

    @staticmethod
    def _get_stage() -> str:
        return Config.get(Config.STAGE_MODE)

    @staticmethod
    def _get_dir_market_historics() -> str:
        return BinanceFakeAPI._DIR_MARKET_HISTORICS

    @staticmethod
    def _get_file_load_orders() -> str:
        return BinanceFakeAPI._FILE_LOAD_ORDERS.replace('$stage', BinanceFakeAPI._get_stage())

    @staticmethod
    def _load_market_historics() -> None:
        _cls = BinanceFakeAPI
        _bkr_cls = BinanceAPI.__name__.replace('API', '')
        original_path = _cls._get_dir_market_historics()
        path_brokered = original_path.replace('$broker', _bkr_cls)
        path_pair_folder = path_brokered.replace('$pair/', '')
        pair_folders = FileManager.get_dirs(path_pair_folder, make_dir=True)
        print("Start loading market historic...♻️")
        for pair_folder in pair_folders:
            pair_merged = _MF.regex_replace('%.+$', '', pair_folder)
            path_files_folder = path_brokered.replace('$pair', pair_folder)
            market_files = FileManager.get_files(path_files_folder)
            market_files = [file for file in market_files if _MF.regex_match('^[0-9]+.csv', file)]
            for market_file in market_files:
                path_market_file = path_files_folder + market_file
                csv = FileManager.get_csv(path_market_file)
                market_historic = [[row[k] for k in row] for row in csv]
                for row in market_historic:
                    for i in range(len(row)):
                        if _MF.regex_match('^[0-9]+$', row[i]):
                            row[i] = int(row[i]) if (i == 0) or (i == 6) else row[i]
                period = int(market_file.replace('.csv', ''))
                _cls.add_market_historic(pair_merged, period, market_historic)
                print(f"📲 File historic of '{pair_merged}' for period '{int(period/(60*1000))}min.' is loaded️ ✅")

    @staticmethod
    def _get_vars() -> Map:
        if BinanceFakeAPI._VARS is None:
            BinanceFakeAPI._VARS = Map()
        return BinanceFakeAPI._VARS

    @staticmethod
    def _get_var(*keys) -> Any:
        return BinanceFakeAPI._get_vars().get(*keys)

    @staticmethod
    def add_market_historic(pair_merged: str, period_milli: int, market: list) -> None:
        """
        To add new market historic\n
        :param pair_merged: Merged pair's symbol, i.e.: 'DOGEUSDT'
        :param period_milli: Period interval in millisecond, i.e.: 5min => 60 * 5 * 1000 = 300 000
        :param market: Market historic
        """
        cls_vars = BinanceFakeAPI._get_vars()
        cls_vars.put(market, Map.market, pair_merged.upper(), int(period_milli))
        BinanceFakeAPI._update_orders()

    @staticmethod
    def _get_market_historic(pair_merged: str, period_milli: int) -> list:
        return BinanceFakeAPI._get_var(Map.market, pair_merged.upper(), period_milli)

    @staticmethod
    def _get_lower_market_historic(pair_merged: str) -> list:
        _cls = BinanceFakeAPI
        market_historics = Map(_cls._get_var(Map.market, pair_merged.upper()))
        period_millis = market_historics.get_keys()
        if len(period_millis) == 0:
            period_str = _cls.INTERVAL_1MIN
            rsp = BinanceAPI._send_market_historics_request(False, _cls.RQ_KLINES, Map({
                Map.symbol: pair_merged.upper(),
                Map.interval: period_str,
                Map.limit: _cls.CONSTRAINT_KLINES_MAX_PERIOD
            }))
            period_milli = int(BinanceAPI.get_interval(period_str) * 1000)
            _cls.add_market_historic(pair_merged, period_milli, rsp.get_content())
        period_millis.sort()
        market_historic = market_historics.get_map()[period_millis[0]]
        return market_historic

    @staticmethod
    def get_index(pair_merged: str = None, period_milli: int = None) -> int:
        """
        To get market index\n
        If Stage1 index is evaluated\n
        If Stage2 index is the last index of market historic\n
        :param pair_merged: Need in Stage2
        :param period_milli: Need in Stage2
        :return: market index
        """
        _cls = BinanceFakeAPI
        _stage = _cls._get_stage()
        if _stage == Config.STAGE_1:
            trade_index = Bot.get_trade_index()
            initial_index = BinanceFakeAPI._CONST_INITIAL_INDEX
            index = (initial_index + trade_index)   # * nb_minute
        elif _stage == Config.STAGE_2:
            index = -1
        else:
            raise Exception(f"This stage '{_stage}' is not supported")
        return index

    @staticmethod
    def _get_time(pair_merged: str = None, period_milli: int = None) -> int:
        """
        To get current time following the index\n
        :param pair_merged: Merged pair's symbol, i.e.: 'DOGEUSDT'
        :param period_milli: Period interval in millisecond, i.e.: 5min => 60 * 5 * 1000 = 300 000
        """
        _cls = BinanceFakeAPI
        if _cls._get_stage() == Config.STAGE_1:
            index = _cls.get_index(pair_merged, period_milli)
            merged_pairs = list(_cls._get_var(Map.market).keys())
            market_hist = _cls._get_market_historic(merged_pairs[0], _cls._CONST_MIN_PERIOD_MILLI)
            time = market_hist[index][0]
        else:
            time = _MF.get_timestamp(_MF.TIME_MILLISEC)
        return time

    @staticmethod
    def _get_actual_close(pair_merged: str, period_milli: int = None) -> str:
        """
        To get current time following the index\n
        :param pair_merged: Merged pair's symbol, i.e.: 'DOGEUSDT'
        :param period_milli: Period interval in millisecond, i.e.: 5min => 60 * 5 * 1000 = 300 000
        """
        _cls = BinanceFakeAPI
        _stage = _cls._get_stage()
        index = _cls.get_index(pair_merged, period_milli)
        market_hist = _cls._get_market_historic(pair_merged, _cls._CONST_MIN_PERIOD_MILLI) \
            if _stage == Config.STAGE_1 else _cls._get_lower_market_historic(pair_merged)
        actual_close = market_hist[index][4]
        return actual_close

    @staticmethod
    def _extract_period_milli(params: Map) -> int:
        period_str = params.get(Map.interval)
        period = BinanceFakeAPI.get_interval(period_str) if period_str is not None else None
        return period * 1000 if period is not None else None

    @staticmethod
    def _get_orders() -> Map:
        """
        To get orders submitted\n
        Returns
        -------
        orders: Map
            All orders submitted
            orders[Pair.__str__()]: {List[dict]}
        """
        _cls = BinanceFakeAPI
        if _cls._ORDERS is None:
            orders = Map()
            file_path = _cls._get_file_load_orders()    # BinanceFakeAPI._FILE_LOAD_ORDERS
            folder_path = _MF.regex_replace(r'[0-9\-]+_.+\.json$', '', file_path)
            files = FileManager.get_files(folder_path, make_dir=True)
            file_name = files[-1] if len(files) > 0 else None
            if file_name is not None:
                backup_file_path = folder_path + file_name
                backup = FileManager.read(backup_file_path)
                orders = MyJson.json_decode(backup)
            _cls._ORDERS = orders
        return _cls._ORDERS

    @staticmethod
    def _save_orders() -> None:
        file_path = BinanceFakeAPI._get_file_load_orders()
        content = BinanceFakeAPI._get_orders().json_encode()
        FileManager.write(file_path, content, make_dir=True)

    @staticmethod
    def _get_order(pair: Pair, order_id: int = None, client_order_id: str = None) -> dict:
        if (order_id is None) and (client_order_id is None):
            raise ValueError("Either order_id or client_order_id must be sent")
        orders = BinanceFakeAPI._get_orders()
        pair_str = pair.__str__()
        order_list = orders.get(pair_str)
        order = [order for order in order_list if (order[Map.orderId] == order_id) or (order[Map.clientOrderId] == client_order_id)]
        if len(order) != 1:
            raise Exception(f"There's not order with these ids order_id='{order_id}' client_order_id='{client_order_id}'")
        return order[0]

    @staticmethod
    def _push_order(pair: Pair, order: dict) -> None:
        orders = BinanceFakeAPI._get_orders()
        pair_str = pair.__str__()
        order_list = orders.get(pair_str)
        order_list.append(order) if isinstance(order_list, list) else orders.put([order], pair_str)

    @staticmethod
    def _execute_order(order: dict) -> None:
        _cls = BinanceFakeAPI
        if order[Map.status] != _cls.STATUS_ORDER_NEW:
            raise ValueError(f"Order's status must be '{_cls.STATUS_ORDER_NEW}', instead '{order[Map.status]}'")
        # Extract from order
        order_type = order[Map.type]
        pair_merged = order[Map.symbol]
        pair = _cls.merged_to_pair(pair_merged)
        # Extract from class
        actual_close = float(_cls._get_actual_close(pair_merged))
        actual_time_milli = _cls._get_time()
        # Prepare Fees
        asset_right = pair.get_right()
        asset_left = pair.get_left()
        is_buyer = order[Map.side] == BinanceAPI.SIDE_BUY
        fee_asset = Asset(asset_right.get_symbol() if is_buyer else asset_left.get_symbol())
        fees_rates = _cls.get_trade_fee(pair)
        # Treat order type
        if order_type == _cls.TYPE_MARKET:
            trade_rate = fees_rates.get(Map.taker)
            is_maker = False
            # Get exec prices
            exec_price = actual_close
            exec_qty = order[Map.origQty]
            exec_amount = actual_close * exec_qty
        elif order_type == _cls.TYPE_STOP_LOSS_LIMIT:
            stop_price = order[Map.stopPrice]
            if (order[Map.side] == _cls.SIDE_BUY) and (actual_close < stop_price):
                raise Exception(f"For move side '{_cls.SIDE_BUY}' and order type '{order_type}'"
                                f" the actual close must be above or equal to the the stop price,"
                                f" instead actual_close='{actual_close}' stop_price='{stop_price}'")
            if (order[Map.side] == _cls.SIDE_SELL) and (actual_close > stop_price):
                raise Exception(f"For move side '{_cls.SIDE_SELL}' and order type '{order_type}'"
                                f" the actual close must be bellow or equal to the the stop price,"
                                f" instead actual_close='{actual_close}' stop_price='{stop_price}'")
            trade_rate = fees_rates.get(Map.maker)
            is_maker = True
            # Get exec prices
            exec_price = limit_price = order[Map.price]
            quantity = exec_qty = order[Map.origQty]
            exec_amount = limit_price * quantity
        else:
            raise Exception(f"This order type '{order_type}' is not supported")
        # Update order
        order[Map.status] = _cls.STATUS_ORDER_FILLED
        order[Map.executedQty] = exec_qty
        order[Map.cummulativeQuoteQty] = exec_amount
        order[Map.updateTime] = actual_time_milli
        # Generate fees
        if fee_asset == asset_right:
            fees = exec_amount * trade_rate
        elif fee_asset == asset_left:
            fees = exec_qty * trade_rate
        else:
            raise Exception(f"Unknown fee symbol '{fee_asset}'")
        # Add trade
        trade_id = _MF.new_code(salt=str(_MF.get_timestamp(_MF.TIME_MILLISEC)))
        order[Map.fills] = [{
            Map.price: exec_price,
            Map.qty: exec_qty,
            Map.commission: fees,
            Map.commissionAsset: fee_asset.__str__().upper(),
            Map.symbol: pair_merged,
            Map.tradeId: trade_id,
            Map.id: trade_id,
            Map.orderId: order[Map.orderId],
            Map.orderListId: -1,
            Map.quoteQty: exec_amount,
            Map.time: actual_time_milli,
            Map.isBuyer: is_buyer,
            Map.isMaker: is_maker,
            Map.isBestMatch: None
        }]

    @staticmethod
    def _add_order(rq: str, params: Map) -> dict:
        _cls = BinanceFakeAPI
        pair_merged = params.get(Map.symbol)
        pair = _cls.merged_to_pair(pair_merged)

        def new_id() -> str:
            return _MF.new_code(salt=str(_MF.get_timestamp(_MF.TIME_MILLISEC)))

        def new_order_canvas(params: Map) -> dict:
            # Extract from params
            client_order_id = params.get(Map.newClientOrderId)
            odr_type = params.get(Map.type)
            side_move = params.get(Map.side)
            # Get from class
            period_milli = _cls._extract_period_milli(params)
            actual_time_milli = _cls._get_time(pair_merged, period_milli)
            return {
                Map.symbol: pair_merged,
                Map.orderId: new_id(),
                Map.orderListId: -1,
                Map.clientOrderId: client_order_id if client_order_id is not None else new_id(),
                Map.transactTime: actual_time_milli,
                Map.price: None,
                Map.origQty: None,
                Map.executedQty: None,
                Map.cummulativeQuoteQty: None,
                Map.status: _cls.STATUS_ORDER_NEW,
                Map.timeInForce: params.get(Map.timeInForce),
                Map.type: odr_type,
                Map.side: side_move,
                Map.time: actual_time_milli,
                Map.updateTime: actual_time_milli
            }

        def generate_order(rq: str, params: Map) -> dict:
            # Extract from params
            side_move = params.get(Map.side)
            quantity = params.get(Map.quantity)
            amount = params.get(Map.quoteOrderQty)
            # Get from class
            period_milli = _cls._extract_period_milli(params)
            actual_close = float(_cls._get_actual_close(pair_merged, period_milli))
            if (rq == _cls.RQ_ORDER_MARKET_qty) or (rq == _cls.RQ_ORDER_MARKET_amount):
                # Prepare prices
                quantity = amount / actual_close if side_move == _cls.SIDE_BUY else quantity
                # Generate Order
                order = new_order_canvas(params)
                order[Map.price] = 0
                order[Map.origQty] = quantity
                # Execute order
                _cls._execute_order(order)
            elif rq == _cls.RQ_ORDER_STOP_LOSS_LIMIT:
                # Prepare prices
                limit_price = params.get(Map.price)
                stop_price = params.get(Map.stopPrice)
                if stop_price != limit_price:
                    raise Exception(f"Case stop_price != limit_price not implemented yet,"
                                    f" stop_price='{stop_price}', limit_price='{limit_price}'")
                # Generate Order
                order = new_order_canvas(params)
                order[Map.price] = limit_price
                order[Map.origQty] = quantity
                order[Map.executedQty] = 0
                order[Map.cummulativeQuoteQty] = 0
                order[Map.stopPrice] = stop_price
                order[Map.fills] = []
            else:
                raise Exception(f"This request '{rq}' is not supported")
            return order

        order = generate_order(rq, params)
        _cls._push_order(pair, order)
        _cls._update_orders()
        return order

    @staticmethod
    def _update_orders() -> None:
        _cls = BinanceFakeAPI
        orders = _cls._get_orders()
        pendings = Map()
        for pair_str, order_list in orders.get_map().items():
            pending_list = [order for order in order_list if order[Map.status] == _cls.STATUS_ORDER_NEW]
            if len(pending_list) > 0:
                pendings.put(pending_list, pair_str)
        for pair_str, order_list in pendings.get_map().items():
            actual_close = float(_cls._get_actual_close(Pair(pair_str).get_merged_symbols()))
            for order in order_list:
                order_type = order[Map.type]
                if order_type == _cls.TYPE_STOP_LOSS_LIMIT:
                    stop_price = order[Map.stopPrice]
                    if ((order[Map.side] == _cls.SIDE_BUY) and (actual_close >= stop_price)) \
                            or ((order[Map.side] == _cls.SIDE_SELL) and (actual_close <= stop_price)):
                        _cls._execute_order(order)
                else:
                    raise Exception(f"This order type '{order_type}' is not supported")
        _cls._save_orders()

    @staticmethod
    def _save_log(rq: str, params: Map) -> None:
        _cls = BinanceFakeAPI
        path = _cls._FILE_LOGS
        pair_merged = params.get(Map.symbol)
        period_milli = _cls._extract_period_milli(params)
        time_milli = _cls._get_time(pair_merged, period_milli)
        date = _MF.unix_to_date(int(time_milli/1000), _MF.FORMAT_D_H_M_S)
        try:
            actual_close = _cls._get_actual_close(pair_merged, period_milli)
        except Exception as e:
            actual_close = None
        id_datas = {
            Map.date: date,
            'trade_index': Bot.get_trade_index(),
            Map.request: rq,
            Map.market: actual_close
        }
        row = {
            **id_datas,
            **params.get_map()
        }
        rows = [row]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(path, fields, rows, overwrite, make_dir=True)

    @staticmethod
    def steal_request(rq: str, params: Map) -> BrokerResponse:
        _cls = BinanceFakeAPI
        _stage = _cls._get_stage()
        if (_stage == Config.STAGE_1) and (_cls._VARS is None):
            _cls._load_market_historics()
        if rq == _cls.RQ_EXCHANGE_INFOS:
            rsp_d = _cls._retrieve_exchange_infos()
        elif rq == _cls.RQ_TRADE_FEE:
            rsp_d = _cls._retrieve_trade_fees()
        elif rq == _cls.RQ_KLINES:
            rsp_d = _cls._get_market_price(params) if _stage == Config.STAGE_1 else None
            _cls._update_orders()
        elif rgx.match(BinanceAPI._ORDER_RQ_REGEX, rq):
            rsp_d = _cls._submit_order(rq, params)
        elif rq == _cls.RQ_CANCEL_ORDER:
            rsp_d = _cls._cancel_order(params)
        elif rq == _cls.RQ_ALL_ORDERS:
            rsp_d = _cls._retrieve_all_orders(params)
        elif rq == _cls.RQ_ALL_TRADES:
            rsp_d = _cls._retrieve_all_trades(params)
        else:
            raise Exception(f"Unknown request '{rq}'")
        rsp = Response()
        rsp.status_code = 200
        rsp._content = json_encode(rsp_d).encode()
        rsp.request = params
        _cls._save_log(rq, params)
        return BrokerResponse(rsp)

    @staticmethod
    def _retrieve_exchange_infos() -> dict:
        path = Config.get(Config.DIR_BINANCE_EXCHANGE_INFOS)
        content = FileManager.read(path)
        ex_infos = _MF.json_decode(content)
        return ex_infos

    @staticmethod
    def _retrieve_trade_fees() -> list:
        path = Config.get(Config.DIR_BINANCE_TRADE_FEE)
        content = FileManager.read(path)
        trade_fees = _MF.json_decode(content)
        return trade_fees

    @staticmethod
    def _get_market_price(params: Map) -> list:
        _cls = BinanceFakeAPI
        pair_merged = params.get(Map.symbol)
        period_milli = _cls._extract_period_milli(params)
        nb_period = params.get(Map.limit)
        index = _cls.get_index()
        historic = _cls._get_market_historic(pair_merged, period_milli)
        nb_minute = int(period_milli / (60 * 1000))
        new_nb_period = nb_period * nb_minute
        min_index = index - new_nb_period
        market_duplic = historic[min_index:index]
        market = [market_duplic[i] for i in range(len(market_duplic)) if (i == 0) or (market_duplic[i][0] != market_duplic[i-1][0])]
        nb_row = len(market)
        if nb_row > nb_period:
            nb_to_delete = nb_row - nb_period
            market = market[nb_to_delete:nb_row]
        market[-1][4] = _cls._get_actual_close(pair_merged)
        return market

    @staticmethod
    def _submit_order(rq: str, params: Map) -> dict:
        _cls = BinanceFakeAPI
        pair_merged = params.get(Map.symbol)
        period_milli = _cls._extract_period_milli(params)
        actual_close = float(_cls._get_actual_close(pair_merged, period_milli))
        actual_time_milli = _cls._get_time(pair_merged, period_milli)
        actual_time = int(actual_time_milli/1000)
        binance_symbol = params.get(Map.symbol)
        binance_move = params.get(Map.side)
        rows = [{
            Map.date: _MF.unix_to_date(actual_time),
            Map.orderId: params.get(Map.orderId),
            Map.request: rq,
            Map.symbol: binance_symbol,
            Map.market: actual_close,
            Map.side: binance_move,
            Map.type: params.get(Map.type),
            Map.quantity: params.get(Map.quantity),
            Map.quoteOrderQty: params.get(Map.quoteOrderQty),
            Map.stopPrice: params.get(Map.stopPrice),
            Map.timeInForce: params.get(Map.timeInForce),
            Map.newOrderRespType: params.get(Map.newOrderRespType)
        }]
        fields = list(rows[0].keys())
        p = _cls._FILE_SAVE_ORDER_REQUESTS
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite, make_dir=True)
        rsp_d = _cls._add_order(rq, params)
        return rsp_d

    @staticmethod
    def _cancel_order(params: Map) -> dict:
        _cls = BinanceFakeAPI
        order_id = params.get(Map.orderId)
        client_order_id = params.get(Map.origClientOrderId)
        pair_merged = params.get(Map.symbol)
        pair = _cls.merged_to_pair(pair_merged)
        order = _cls._get_order(pair, order_id) \
            if order_id is not None else _cls._get_order(pair, client_order_id=client_order_id)
        if order[Map.status] != _cls.STATUS_ORDER_NEW:
            raise Exception(f"Can't cancel an order with this status '{order[Map.status]}'")
        cancel_rsp = {
            Map.symbol: pair_merged,
            Map.origClientOrderId: order[Map.clientOrderId],
            Map.orderId: order[Map.orderId],
            Map.orderListId: -1,
            Map.clientOrderId: _MF.new_code(),
            Map.price: order[Map.price],
            Map.origQty: order[Map.price],
            Map.executedQty: order[Map.executedQty],
            Map.cummulativeQuoteQty: order[Map.cummulativeQuoteQty],
            Map.status: _cls.STATUS_ORDER_CANCELED,
            Map.timeInForce: order[Map.timeInForce],
            Map.type: order[Map.type],
            Map.side: order[Map.side]
          }
        if Map.stopPrice in order:
            cancel_rsp[Map.stopPrice] = order[Map.stopPrice]
        order[Map.status] = _cls.STATUS_ORDER_CANCELED
        return cancel_rsp

    @staticmethod
    def _retrieve_all_orders(params: Map) -> list:
        _cls = BinanceFakeAPI
        pair = _cls.merged_to_pair(params.get(Map.symbol))
        order_list = _cls._get_orders().get(pair.__str__())
        return order_list

    @staticmethod
    def _retrieve_all_trades(params: Map) -> list:
        _cls = BinanceFakeAPI
        order_list = _cls._retrieve_all_orders(params)
        trade_list = [order[Map.fills][0] for order in order_list if order[Map.status] == _cls.STATUS_ORDER_FILLED]
        return trade_list

    @staticmethod
    def merged_to_pair(pair_merged: str) -> Pair:
        pair_str = BinanceAPI.symbol_to_pair(pair_merged)
        return Pair(pair_str)


if __name__ == '__main__':
    pass
