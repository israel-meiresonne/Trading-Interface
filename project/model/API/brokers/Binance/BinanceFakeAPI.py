from json import dumps as json_encode
import re as rgx
from typing import Any

from requests.models import Response

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.Bot import Bot
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerResponse import BrokerResponse
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair


class BinanceFakeAPI(BinanceAPI):
    _FILE_SAVE_ORDERS = Config.get(Config.DIR_SAVE_ORDER_RQ)
    _FILE_LOGS = Config.get(Config.DIR_SAVE_FAKE_API_RQ)
    _DIR_MARKET_HISTORICS = Config.get(Config.DIR_MARKET_HISTORICS)
    _CONST_INITIAL_INDEX = 60 * BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD     # 60 000, to initialize index's position
    _CONST_MIN_PERIOD_MILLI = 60 * 1000 # Period interval of the min period available all in millisecond
    _VARS = None
    """
    _VARS[Map.market][pair_merged{str}][period{int}]:   {List[list]}    # pair_merged format: 'DOGEUSDT', period in second
    _VARS[Map.index]:                                   {int|None}      # Trade index of a Bot
    """

    def __init__(self):
        pass

    @staticmethod
    def _get_stage() -> str:
        return Config.get(Config.STAGE_MODE)

    @staticmethod
    def _get_dir_market_historics() -> str:
        return BinanceFakeAPI._DIR_MARKET_HISTORICS

    @staticmethod
    def _load_market_historics() -> None:
        _cls = BinanceFakeAPI
        _bkr_cls = BinanceAPI.__name__.replace('API', '')
        original_path = _cls._get_dir_market_historics()
        path_brokered = original_path.replace('$broker', _bkr_cls)
        path_pair_folder = path_brokered.replace('$pair/', '')
        pair_folders = FileManager.get_dirs(path_pair_folder)
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

    @staticmethod
    def _get_market_historic(pair_merged: str, period_milli: int) -> list:
        return BinanceFakeAPI._get_var(Map.market, pair_merged.upper(), period_milli)

    @staticmethod
    def _get_lower_market_historic(pair_merged: str) -> list:
        market_historics = Map(BinanceFakeAPI._get_var(Map.market, pair_merged.upper()))
        period_millis = market_historics.get_keys()
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
            # market_historic = _cls._get_vars().get(pair_merged, period_milli)
            # market_historic = _cls._get_market_historic(pair_merged, period_milli)
            # index = -len(market_historic)
            index = -1
        else:
            raise Exception(f"This stage '{_stage}' is not supported")
        return index

    @staticmethod
    def _get_time(pair_merged: str, period_milli: int) -> int:
        """
        To get current time following the index\n
        :param pair_merged: Merged pair's symbol, i.e.: 'DOGEUSDT'
        :param period_milli: Period interval in millisecond, i.e.: 5min => 60 * 5 * 1000 = 300 000
        """
        _cls = BinanceFakeAPI
        """
        date = None
        if _cls._get_stage() == Config.STAGE_1:
            idx = _cls._get_backed(log_id, Map.index)
            hist_mkt = _cls._get_backed(log_id, Map.market)
            date = hist_mkt[idx][0]
            date = int(date/1000) if _cls._get_stage() != Config.STAGE_1 else date
        else:
            date = _MF.get_timestamp()
        return date
        """
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
        """
        idx = _cls._get_backed(log_id, Map.index)
        hist_mkt = _cls._get_backed(log_id, Map.market)
        actual_close = hist_mkt[idx][4]
        """
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
        FileManager.write_csv(path, fields, rows, overwrite)

    @staticmethod
    def steal_request(rq: str, params: Map) -> BrokerResponse:
        _cls = BinanceFakeAPI
        _stage = _cls._get_stage()
        if (_stage == Config.STAGE_1) and (_cls._VARS is None):
            _cls._load_market_historics()
        if rq == _cls.RQ_KLINES:
            rsp_d = _cls._get_market_price(params) if _stage == Config.STAGE_1 else None
        elif rgx.match('^RQ_ORDER.*$', rq) or (rq == _cls.RQ_CANCEL_ORDER):
            rsp_d = _cls._execute_order(rq, params)
        elif rq == _cls.RQ_EXCHANGE_INFOS:
            rsp_d = _cls._retreive_exchange_infos()
        elif rq == _cls.RQ_TRADE_FEE:
            rsp_d = _cls._retreive_trade_fees()
        else:
            raise Exception(f"Unknown request '{rq}'")
        rsp = Response()
        rsp.status_code = 200
        rsp._content = json_encode(rsp_d).encode()
        rsp.request = params
        _cls._save_log(rq, params)
        return BrokerResponse(rsp)

    @staticmethod
    def _get_market_price(params: Map) -> list:
        """
        _cls = BinanceFakeAPI
        nb_prd = params.get(Map.limit)
        idx = _cls.get_index()  # _cls._get_backed(log_id, Map.index)
        if (idx is None) or (idx < nb_prd):
            idx = nb_prd
        else:
            idx += 1
        # idx = nb_prd if idx is None else idx + 1
        min_idx = idx - nb_prd
        hist_mkt = _cls._get_backed(log_id, Map.market)
        d = [hist_mkt[i] for i in range(len(hist_mkt)) if (i <= idx) and (i > min_idx)]
        _cls._add_backup(log_id, Map.index, idx)
        return d
        """
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
        return market

    @staticmethod
    def _execute_order(rq: str, params: Map) -> dict:
        _cls = BinanceFakeAPI
        pair_merged = params.get(Map.symbol)
        period_milli = _cls._extract_period_milli(params)
        # period = int(period_milli/1000)
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
        p = _cls._FILE_SAVE_ORDERS
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)
        exec_time = None
        exec_qty = 0
        exec_amount = 0
        fills = []
        if (rq == _cls.RQ_ORDER_MARKET_qty) or (rq == _cls.RQ_ORDER_MARKET_amount):
            status = _cls.STATUS_ORDER_FILLED
            exec_time = actual_time
            quantity = params.get(Map.quantity)
            amount = params.get(Map.quoteOrderQty)
            pair_str = BinanceAPI.symbol_to_pair(binance_symbol)
            pair = Pair(pair_str)
            if quantity is not None:
                exec_qty = float(quantity)
                exec_amount = actual_close * exec_qty
            elif amount is not None:
                exec_amount = amount
                exec_qty = exec_amount / actual_close
            else:
                raise Exception("The quantity or the amount must be set for market Order.")
            fee_symbol = pair.get_right().get_symbol().upper() \
                if binance_move == BinanceAPI.SIDE_BUY else pair.get_left().get_symbol().upper()
            fills = [
                {
                    Map.price: actual_close,
                    Map.qty: exec_qty,
                    Map.commission: "0.000",
                    Map.commissionAsset: fee_symbol
                }
            ]
        elif (rq == _cls.RQ_ORDER_STOP_LOSS) \
                or (rq == _cls.RQ_ORDER_STOP_LOSS_LIMIT):
            status = _cls.STATUS_ORDER_NEW
            actual_close = None
        elif rq == _cls.RQ_CANCEL_ORDER:
            status = _cls.STATUS_ORDER_CANCELED
        else:
            raise Exception(f"Unknown request '{rq}'")
        rsp_d = {
            Map.orderId: int(f"{123}_{_MF.new_code(salt=str(_MF.get_timestamp(_MF.TIME_MILLISEC)))}"),
            Map.status: status,
            Map.price: actual_close,
            Map.transactTime: exec_time,
            Map.executedQty: exec_qty,
            Map.cummulativeQuoteQty: exec_amount,
            Map.fills: fills
        }
        return rsp_d

    @staticmethod
    def _retreive_exchange_infos() -> dict:
        path = Config.get(Config.DIR_BINANCE_EXCHANGE_INFOS)
        content = FileManager.read(path)
        ex_infos = _MF.json_decode(content)
        return ex_infos

    @staticmethod
    def _retreive_trade_fees() -> list:
        path = Config.get(Config.DIR_BINANCE_TRADE_FEE)
        content = FileManager.read(path)
        trade_fees = _MF.json_decode(content)
        return trade_fees


if __name__ == '__main__':
    Config.update(Config.STAGE_MODE, Config.STAGE_1)
    _cls = BinanceFakeAPI
    _cls._load_market_historics()
    market = _cls._get_market_price(params=Map({
        Map.symbol: Pair('DOGE/USDT').get_merged_symbols().upper(),
        Map.interval: 60 * 5 * 1000,
        Map.limit: 5
    }))
    print(_MF.json_encode(market))
