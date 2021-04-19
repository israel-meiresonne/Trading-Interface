import numpy as np
import pandas as pd
from pandas_ta import er as _er
from pandas_ta import aroon as _aroon

from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Paire import Pair


def extract_market():
    _fm_cls = FileManager
    # Extract
    fields = ['market_json']
    p = 'content/v0.01/analyse/2021-02-25 21.25.44_moves.csv'
    csv = _fm_cls.get_csv(p)
    rows = [_MF.json_decode(row[fields[0]]) for row in csv]
    # Convert
    mkt = list(rows[0])
    del mkt[0]
    mkt.reverse()
    for row in rows:
        mkt.append(row[0])
    # mkt.append(rows[len(rows)-1][0])
    # Write
    fields = ['market']
    rows = [{fields[0]: price.replace(".", ",")} for price in mkt]
    p = 'content/v0.01/analyse/2021-02-25 21.25.44_market.csv'
    _fm_cls.write_csv(p, fields, rows)


def extract_markets():
    _fm_cls = FileManager
    # Extract
    fields = ['market_json']
    p = 'content/v0.01/analyse/2021-02-25 21.25.44_moves.csv'
    csv = _fm_cls.get_csv(p)
    rows = [_MF.json_decode(row[fields[0]]) for row in csv]
    # Convert
    rows = [[price.replace(".", ",") for price in row] for row in rows]
    """
    mkts = list(rows[0])
    del mkt[0]
    mkt.reverse()
    for row in rows:
        mkt.append(row[0])
    # mkt.append(rows[len(rows)-1][0])
    """
    # Write
    # fields = ['market']
    rows = [{k: row[k] for k in range(len(row))} for row in rows]
    # print(rows)
    fields = list(rows[0].keys())
    p = 'content/v0.01/analyse/2021-02-25 21.25.44_markets.csv'
    _fm_cls.write_csv(p, fields, rows)


def capital_to_market(src_path: str, depot_path: str) -> None:
    _fm_cls = FileManager
    # Extract
    fields = ['market_json']
    csv = _fm_cls.get_csv(src_path)
    rows = [{Map.time: int(_MF.date_to_unix(row[Map.time])),
             Map.open: '0',
             Map.high: '0',
             Map.low: '0',
             Map.close: row[Map.close]}
            for row in csv]
    fields = list(rows[0].keys())
    _fm_cls.write_csv(depot_path, fields, rows)
    print("🖨 File printed ✅")


def apimarket_to_market(src_path: str, depot_path: str) -> None:
    _fm_cls = FileManager
    # Extract
    csv = _fm_cls.get_csv(src_path)
    """
    requests[
        request[
            market[
                0.  Open time
                1.  Open
                2.  High
                3.  Low
                4.  Close
                5.  Volume
                6.  Close time
                7.  Quote asset volume
                8.  Number of trades
                9.  Taker buy base asset volume
                10. Taker buy quote asset volume
                11. Ignore.
            ]
        ]  
    ]
    """
    rqs = [eval(row[Map.market]) for row in csv]
    rows = []
    mkts = {}
    for i in range(len(rqs)):
        rq = rqs[i]
        for j in range(len(rq)):
            if j == 0:
                continue
            mkt = rq[j]
            time = mkt[0]
            if time not in mkts:
                mkts[time] = mkt
    times = sorted(mkts)
    for time in times:
        mkt = mkts[time]
        row = {
            Map.time: int(mkt[0] / 1000),
            Map.open: mkt[1],
            Map.high: mkt[2],
            Map.low: mkt[3],
            Map.close: mkt[4],
            Map.volume: mkt[5]
        }
        rows.append(row)
    if rows[0][Map.time] >= rows[1][Map.time]:
        older_unix = rows[0][Map.time]
        recent_unix = rows[1][Map.time]
        older = _MF.unix_to_date(older_unix / 1000, _MF.FORMAT_D_H_M_S)
        recent = _MF.unix_to_date(recent_unix / 1000, _MF.FORMAT_D_H_M_S)
        raise Exception(f"Market must be ordered from older to recent "
                        f"instead '{older_unix}({older})', '{recent_unix}({recent})',...")
    fields = list(rows[0].keys())
    _fm_cls.write_csv(depot_path, fields, rows)
    print("🖨 File printed ✅")


def get_historic(pr: Pair, period: int, nb_prd: int) -> MarketPrice:
    bnc = Binance(Map({Map.api_pb: "pb_k",
                       Map.api_sk: "sk_k",
                       Map.test_mode: False
                       }))
    rq_prm = Map({Map.pair: pr,
                  Map.period: period,
                  Map.number: nb_prd
                  })
    rq = BinanceRequest(BrokerRequest.RQ_MARKET_PRICE, rq_prm)
    bnc.get_market_price(rq)
    mkt = rq.get_market_price()
    return mkt


def print_historic(pr_str: str, prd: int = 60, nb_prd: int = 1000) -> None:
    pr = Pair(pr_str)
    mkt = get_historic(pr, prd, nb_prd)
    print_market(mkt, pr)


def print_market(mkt: MarketPrice, pr: Pair) -> None:
    closes = mkt.get_closes()
    rows = []
    # times = [int(t / 1000) for t in mkt.get_times()]
    times = [t for t in mkt.get_times()]
    degs = mkt.get_slopes_degree(14)
    degs = [v for v in degs if v is not None]
    spr_extrems = _MF.get_super_extremums(list(degs))
    # print(spr_extrems)
    super_rsis = mkt.get_super_trend_rsis()
    super_tsis = mkt.get_super_trend_tsis()
    for i in range(len(closes)):
        row = {
            Map.time: times[i],
            Map.open: mkt.get_opens()[i],
            Map.high: mkt.get_highs()[i],
            Map.low: mkt.get_lows()[i],
            Map.close: closes[i],
            Map.rsi: mkt.get_rsis()[i],
            'super_rsis': super_rsis[i],
            Map.super_trend: mkt.get_super_trend()[i],
            Map.tsi: mkt.get_tsis(use_nan=True)[i],
            Map.tsi + "_ema": mkt.get_tsis_emas()[i],
            'super_tsis': super_tsis[i],
            'slopes': mkt.get_slopes(14)[i],
            'slope_deg': mkt.get_slopes_degree()[i],
            'extremuns': degs[i] if i in spr_extrems else None
        }
        rows.append(row)
    rows.reverse()
    date_format = _MF.FORMAT_D_H_M_S_MS.replace(':', '.')
    file = f"{pr.get_merged_symbols().upper()}-{_MF.unix_to_date(_MF.get_timestamp(), date_format)}"
    p = f"content/v0.01/market-historic/{file}.csv"
    fields = list(rows[0].keys())
    overwrite = True
    FileManager.write_csv(p, fields, rows, overwrite)
    print("🖨 File printed ✅")


def delta_sum(xs: list, nb_prd: int = 14) -> list:
    idx = nb_prd - 1
    rs = []
    nb_x = len(xs)
    for i in range(nb_x):
        if i < idx:
            rs.append('NAN')
            continue
        seq = [xs[j] for j in range(nb_x) if (j > (idx - nb_prd)) and (j <= idx)]
        dt_sum = 0
        for k in range(1, len(seq)):
            delta = (seq[k] / seq[k - 1]) - 1
            dt_sum += delta
        rs.append(dt_sum)
        idx += 1
    return rs


def get_true_range(closes: list, highs: list, lows: list) -> list:
    nb = len(closes)
    if (len(highs) != nb) or (len(lows) != nb):
        raise ValueError(f"The closes, highs and lows collections must have the same length "
                         f"('{nb}', '{len(highs)}, '{len(lows)}')")
    trs = [None]
    for i in range(1, nb):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1]) if (i > 0) else 0
        lc = abs(lows[i] - closes[i - 1]) if (i > 0) else 0
        tr = max([hl, hc, lc])
        trs.append(tr)
    return trs


def get_average_true_range(trs: list, nb_prd: int = 10) -> list:
    if nb_prd <= 1:
        raise ValueError(f"The number of period must be at less 2 instead '{nb_prd}'")
    idx = nb_prd - 1
    atrs = []
    nb = len(trs)
    for i in range(nb):
        if i < idx:
            atrs.append(None)
            continue
        seq = [trs[j] for j in range(nb) if (j > (idx - nb_prd)) and (j <= idx)]
        atr = sum(seq) / nb_prd
        atrs.append(atr)
        idx += 1
    return atrs


SUPER_TREND_COEF = 3


def get_super_trend_up(idx: int, highs: list, lows: list, atrs: list, coef: float = SUPER_TREND_COEF) -> float:
    return (highs[idx] + lows[idx]) / 2 - coef * atrs[idx]


def get_super_trend_down(idx: int, highs: list, lows: list, atrs: list, coef: float = SUPER_TREND_COEF) -> float:
    return (highs[idx] + lows[idx]) / 2 + coef * atrs[idx]


def get_super_trend_up_trend(closes: list, highs: list, lows: list, atrs: list, coef: float = SUPER_TREND_COEF):
    up_trends = []
    for i in range(len(closes)):
        if atrs[i] is None:
            up_trends.append(None)
            continue
        down = get_super_trend_down(i, highs, lows, atrs, coef)
        if up_trends[i - 1] is None:
            up_trends.append(down)
            continue
        up_trend = down if (down < up_trends[i - 1]) or (closes[i - 1] > up_trends[i - 1]) else up_trends[i - 1]
        up_trends.append(up_trend)
    return up_trends


def get_super_trend_down_trend(closes: list, highs: list, lows: list, atrs: list, coef: float = SUPER_TREND_COEF):
    down_trends = []
    for i in range(len(closes)):
        if atrs[i] is None:
            down_trends.append(None)
            continue
        up = get_super_trend_up(i, highs, lows, atrs, coef)
        if down_trends[i - 1] is None:
            down_trends.append(up)
            continue
        up_trend = up if (up > down_trends[i - 1]) or (closes[i - 1] < down_trends[i - 1]) else down_trends[i - 1]
        down_trends.append(up_trend)
    return down_trends


"""
1. ST=> BS(T), si : 
              1) ST(T-1) = BS(T-1)
               ET
              2) Close(T) < BS(T)
2. ST=>BS(T), si:
               4) ST(T-1) = BI(T-1)
               ET
              6)Close(T) < BI(T)
3. ST=> BI(T), si:
               1) ST(T-1) = BS(T-1) 
               ET
              3) Close(T) > BS(T)
4. ST=>BI(T), si :❌
               4) ST(T-1) = BI(T-1) => 57638.36600000001 == 57638.36600000001
               ET
              5) Close(T) > BI(T)   => 57993.79 > 57696.29
"""


def get_super_trend(closes: list, ups: list, downs: list) -> list:
    supers = []
    for i in range(len(closes)):
        if ups[i] is None:
            supers.append(None)
            continue
        spr = ups[i] if ((supers[i - 1] == ups[i - 1]) and (closes[i] < ups[i])) \
                        or ((supers[i - 1] == downs[i - 1]) and (closes[i] < downs[i])) else None
        if spr is None:
            spr = downs[i] if ((supers[i - 1] == ups[i - 1]) and (closes[i] > ups[i])) \
                              or ((supers[i - 1] == downs[i - 1]) and (closes[i] > downs[i])) else None
        supers.append(spr)
    return supers


if __name__ == '__main__':
    # extract_market()
    # extract_markets()
    # print_historic(Binance.list_paires()[0])
    # print_historic(Binance.list_paires()[2])
    """
    src_path='content/v0.01/backups/2021-03-20 12.31.44-3D/BNB/2021-03-20 12.32.26_capital.csv'
    depot_path='content/v0.01/market-historic/BNBUSDT-3D.csv'
    capital_to_market(src_path, depot_path)
    # nb_prd = 5
    p = "content/v0.01/market-historic/active.csv"
    csv = FileManager.get_csv(p)
    mkt_list = [[int(line[Map.time]), '0', line[Map.high], line[Map.low], line[Map.close]] for line in csv]
    mkt = BinanceMarketPrice(mkt_list, '1m')
    # mkt.get_super_trend()
    # print(mkt.get_super_trend())
    print_market(mkt, Pair("BNB/USDT"))
    """
    """
    closes = [float(row[4]) for row in mkt_list]
    highs = [float(row[2]) for row in mkt_list]
    lows = [float(row[3]) for row in mkt_list]
    trs = get_true_range(closes, highs, lows)
    trs_clean = [v for v in trs if (v is not None)]
    nb_none = len(trs) - len(trs_clean)
    atrs = get_average_true_range(trs_clean)
    atrs = [None for i in range(nb_none)] + atrs
    downs = get_super_trend_down_trend(closes, highs, lows, atrs)
    ups = get_super_trend_up_trend(closes, highs, lows, atrs)
    supers = get_super_trend(closes, ups, downs)
    print(supers)
    """
    """
    for i in range(len(ups)):
        print(i, ups[i])
    for i in range(len(downs)):
        print(i, downs[i])
    for i in range(len(supers)):
        print(i, supers[i])
    """
    """
    # closes = [row[Map.close] for row in csv]
    # closes = [i for i in range(1, len(closes)) if i < 10]
    # closes = [float(closes[i]) for i in range(len(closes)) if i < 30]
    # closes = [float(closes[i]) for i in range(len(closes))]
    # closes = [2*v for v in range(10)]
    mkt_list = [[int(line[Map.time]), line[Map.open], '0', '0', line[Map.close]] for line in csv]
    bnc_mkt = BinanceMarketPrice(mkt_list, '1m')
    rows = []
    times = [int(t/1000) for t in bnc_mkt.get_times()]
    for i in range(len(times)):
        row = {
            Map.time: times[i],
            Map.open: bnc_mkt.get_opens()[i],
            Map.rsi: bnc_mkt.get_rsis()[i],
            "slope_avg": bnc_mkt.get_slopes_avg()[i],
            Map.close: bnc_mkt.get_closes()[i]
        }
        rows.append(row)
    rows.reverse()
    """
    """
    p2 = f"content/v0.01/market-historic/BTC-RSI-SLOPE_AVG.csv"
    fields = list(rows[0].keys())
    overwrite = True
    FileManager.write_csv(p2, fields, rows, overwrite)
    print("🖨 File printed ✅")
    """
    """
    # src_path = 'content/v0.01/2021-04-04 23.02.14_market.csv'
    # depot_path = 'content/v0.01/BNB-USDT-2Days_market.csv'
    # apimarket_to_market(src_path, depot_path)
    api_pb = ''
    api_sk = ''
    test_mode = False
    '''
    api = BinanceAPI(api_pb, api_sk, test_mode)
    rq = BinanceAPI.RQ_ALL_ORDERS
    rq_params = Map({
        Map.symbol: "BNBUSDT",
        Map.startTime: 1612134000,
        Map.limit: 10
    })
    rsp = api.request_api(rq, rq_params)
    content = rsp.get_content()
    print(content)
    '''
    config = Map({
        Map.api_pb: api_pb,
        Map.api_sk: api_sk,
        Map.test_mode: test_mode
    })
    odr_rq_params = Map({
        Map.symbol: "BNBUSDT",
        Map.id: None,
        Map.begin_time: 1612134000,
        Map.end_time: None,
        Map.limit: 10,
        Map.timeout: None
    })
    snap_rq_params = Map({
        Map.account: BrokerRequest.ACCOUNT_MAIN,
        Map.begin_time: None,
        Map.end_time: _MF.get_timestamp(_MF.TIME_MILLISEC),
        Map.number: 5,
        Map.timeout: None,
    })
    bnc = Binance(config)
    # bnc_rq = BinanceRequest(BinanceRequest.RQ_ORDERS, odr_rq_params)
    bnc_rq = BinanceRequest(BinanceRequest.RQ_ACCOUNT_SNAP, snap_rq_params)
    bnc.request(bnc_rq)
    # api_rsp = bnc_rq.get_orders()
    api_rsp = bnc_rq.get_account_snapshot()
    # json = _MF.json_encode(api_rsp.get_map())
    # prt = {k: {k: v.__str__() for k, v in row.items()} for k, row in api_rsp.get(Map.account).items()}
    # prt = {**prt, **api_rsp.get(Map.response)}
    times = list(api_rsp.get(Map.account).keys())
    cap = api_rsp.get(Map.account, times[-1], "usdt")
    print(cap)
    """
    src = "content/v0.01/market-historic/COS/COS-USDT-2Days_market.csv"
    csv = FileManager.get_csv(src)
    mkt_list = [[int(line[Map.time]), float(line[Map.open]), float(line[Map.high]), float(line[Map.low]), float(line[Map.close])] for line in csv]
    bnc_mkt = BinanceMarketPrice(mkt_list, '1m')
    # Closes
    closes = list(bnc_mkt.get_closes())
    closes.reverse()
    closes_serie = pd.Series(np.array(closes))
    # Times
    times = list(bnc_mkt.get_times())
    times.reverse()
    # Highs
    highs = list(bnc_mkt.get_highs())
    highs.reverse()
    highs_serie = pd.Series(np.array(highs))
    # Lows
    lows = list(bnc_mkt.get_lows())
    lows.reverse()
    lows_serie = pd.Series(np.array(lows))
    nb_prd = 14
    # er_obj = _er(closes_serie, nb_prd)
    graph_obj = _aroon(highs_serie, lows_serie)
    # er_serie = er_obj[f'ER_{nb_prd}']
    aroon_up = graph_obj[f'AROONU_{nb_prd}'].to_list()
    aroon_down = graph_obj[f'AROOND_{nb_prd}'].to_list()
    aroon_osc = graph_obj[f'AROONOSC_{nb_prd}'].to_list()
    """
    aroon_up.reverse()
    aroon_down.reverse()
    aroon_osc.reverse()
    closes.reverse()
    """
    p = "content/v0.01/market-historic/COS/aroon.csv"
    # row = {Map.close: closes, "er": er_list}
    rows = [{Map.time: _MF.unix_to_date(times[i], _MF.FORMAT_D_H_M_S),
             Map.close: closes[i],
             "aroon_up": aroon_up[i],
             "aroon_down": aroon_down[i],
             "aroon_osc": aroon_osc[i]} for i in range(len(closes))]
    fields = list(rows[0].keys())
    FileManager.write_csv(p, fields, rows)


