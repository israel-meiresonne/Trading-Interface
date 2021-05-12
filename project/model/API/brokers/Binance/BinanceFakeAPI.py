from json import dumps as json_encode
import re as rgx

from requests.models import Response

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerResponse import BrokerResponse
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair


class BinanceFakeAPI(BinanceAPI):
    _FILE_HISTORIC_MARKET_PRICES = Config.get(Config.DIR_HISTORIC_PRICES)
    _FILE_SAVE_ORDERS = Config.get(Config.DIR_SAVE_ORDER_RQ)
    _FILE_LOGS = Config.get(Config.DIR_SAVE_FAKE_API_RQ)
    _STAGE = Config.get(Config.STAGE_MODE)
    BACKUP = Map()
    """
    BACKUP[Map.id]      => {str}        # log's id
    BACKUP[Map.market]  => {list}       # List[List[{date, open, high, low, close, adj_close, volume}]]
    BACKUP[Map.index]   => {int|None}   # index of the most recent close returned
    """

    def __init__(self):
        pass

    @staticmethod
    def _get_stage() -> str:
        return BinanceFakeAPI._STAGE

    @staticmethod
    def set_backup(log_id: str, hist_mkt=None) -> None:
        _cls = BinanceFakeAPI
        stage = _cls._get_stage()
        if stage == Config.STAGE_1:
            p = _cls._FILE_HISTORIC_MARKET_PRICES
            csv = FileManager.get_csv(p)
            hist_mkt = [[row[k] for k in row] for row in csv]
            # """
            for row in hist_mkt:
                for i in range(len(row)):
                    if rgx.match('^[0-9]+$', row[i]):
                        row[i] = int(row[i]) if (i == 0) else row[i]
                    else:
                        row[i] = int(_MF.date_to_unix(row[i])) if (i == 0) else row[i]
            # """
            _cls._add_backup(log_id, Map.id, log_id)
            _cls._add_backup(log_id, Map.market, hist_mkt)
            _cls._add_backup(log_id, Map.index, 0)
        if stage == Config.STAGE_2:
            _cls._add_backup(log_id, Map.id, log_id)
            _cls._add_backup(log_id, Map.market, hist_mkt)
            _cls._add_backup(log_id, Map.index, None)

    @staticmethod
    def _get_backup() -> Map:
        return BinanceFakeAPI.BACKUP

    @staticmethod
    def _add_backup(log_id: str, k, v) -> None:
        backup = BinanceFakeAPI._get_backup()
        backup.put(v, log_id, k)

    @staticmethod
    def _get_backed(log_id: str, k) -> [str, int, float, list, dict]:
        _cls = BinanceFakeAPI
        backup = BinanceFakeAPI._get_backup()
        stage = _cls._get_stage()
        if (k == Map.index) and (stage != Config.STAGE_1):
            hist_mkt = _cls._get_backed(log_id, Map.market)
            v = len(hist_mkt) - 1
        else:
            v = backup.get(log_id, k)
        return v

    @staticmethod
    def _get_date(log_id) -> int:
        _cls = BinanceFakeAPI
        idx = _cls._get_backed(log_id, Map.index)
        hist_mkt = _cls._get_backed(log_id, Map.market)
        date = hist_mkt[idx][0]
        date = int(date/1000) if _cls._get_stage() != Config.STAGE_1 else date
        return date

    @staticmethod
    def _get_actual_close(log_id) -> str:
        _cls = BinanceFakeAPI
        idx = _cls._get_backed(log_id, Map.index)
        hist_mkt = _cls._get_backed(log_id, Map.market)
        actual_close = hist_mkt[idx][4]
        return actual_close

    @staticmethod
    def _save_log(log_id: str, rq: str, params: Map) -> None:
        _cls = BinanceFakeAPI
        p = _cls._FILE_LOGS
        unix_date = _cls._get_date(log_id)
        date = _MF.unix_to_date(unix_date, _MF.FORMAT_D_H_M_S)
        id_datas = {
            Map.date: date,
            Map.id: log_id,
            Map.request: rq,
            Map.market: _cls._get_actual_close(log_id)
        }
        row = {
            **id_datas,
            **params.get_map()
        }
        rows = [row]
        fields = list(rows[0].keys())
        overwrite = False
        FileManager.write_csv(p, fields, rows, overwrite)

    @staticmethod
    def steal_request(log_id: str, rq: str, params: Map) -> BrokerResponse:
        _cls = BinanceFakeAPI
        if _cls._get_backed(log_id, Map.id) is None:
            _cls.set_backup(log_id)
        if rq == _cls.RQ_KLINES:
            stage = _cls._get_stage()
            rsp_d = _cls._get_market_price(log_id, params) if stage == Config.STAGE_1 else None
            # _cls._save_log(log_id, rq, params) if stage == Config.STAGE_2 else None
        elif rgx.match('^RQ_ORDER.*$', rq) or (rq == _cls.RQ_CANCEL_ORDER):
            rsp_d = _cls._execute_order(log_id, rq, params)
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
        _cls._save_log(log_id, rq, params)
        return BrokerResponse(rsp)

    @staticmethod
    def _get_market_price(log_id: str, params: Map) -> list:
        _cls = BinanceFakeAPI
        nb_prd = params.get(Map.limit)
        idx = _cls._get_backed(log_id, Map.index)
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

    @staticmethod
    def _execute_order(log_id: str, rq: str, params: Map) -> dict:
        _cls = BinanceFakeAPI
        actual_close = float(_cls._get_actual_close(log_id))
        now_date = _cls._get_date(log_id)
        binance_symbol = params.get(Map.symbol)
        binance_move = params.get(Map.side)
        rows = [{
            Map.date: _MF.unix_to_date(now_date),
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
            exec_time = now_date
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
    _cls = BinanceFakeAPI
    """
    # '''
    from model.API.brokers.Binance.BinanceRequest import BinanceRequest
    from model.API.brokers.Binance.BinanceOrder import BinanceOrder
    from model.tools.Paire import Pair
    from model.tools.Price import Price

    log_id = 'id_123'
    bkr_rq_params = Map({
        Map.pair: Pair("BTC/USD"),
        Map.period: 60,
        Map.begin_time: None,
        Map.end_time: None,
        Map.number: 10
    })
    bnc_rq = BinanceRequest(BinanceRequest.RQ_MARKET_PRICE, bkr_rq_params)
    bnc_rq_params = bnc_rq.generate_request()
    rsp1 = _cls.steal_request(log_id, _cls.RQ_KLINES, bnc_rq_params)
    print(f"market price returned {len(rsp1.get_content())} lines")
    # '''
    # rsp2 = _cls.steal_request(log_id, _cls.RQ_KLINES, bnc_rq_params)
    i = 0
    ds1 = rsp1.get_content()
    # ds2 = rsp2.get_content()
    nb_ds1 = len(ds1)
    for i in range(nb_ds1):
        print(f'{i + 1}: {ds1[i]}')
    print('————————————————————')
    '''
    for i in range(len(ds2)):
        print(f'{nb_ds1 + i + 1}: {ds2[i]}')
    '''
    # '''
    odr_cls = BinanceOrder
    _cls = BinanceFakeAPI
    log_id = 'id_123'
    rq = _cls.RQ_ORDER_MARKET_qty
    rs_cancel = _cls.RQ_CANCEL_ORDER
    pr = Pair("BTC/USD")
    lsbl = pr.get_left().get_symbol()
    rsbl = pr.get_right().get_symbol()
    odr_params = Map({
        Map.pair: pr,
        Map.move: odr_cls.MOVE_BUY,
        Map.quantity: Price(55, lsbl),
        Map.amount: None
    })
    odr = BinanceOrder(odr_cls.TYPE_MARKET, odr_params)
    rsp = _cls.steal_request(log_id, rq, odr.generate_order())
    rsp_cancel = _cls.steal_request(log_id, rs_cancel, odr.generate_cancel_order())
    print(rsp.get_content())
    print(rsp_cancel.get_content())    
    """
    print(_cls._retreive_exchange_infos())
