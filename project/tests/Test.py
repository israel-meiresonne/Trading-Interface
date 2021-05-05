from datetime import datetime

import numpy as np
import pandas as pd
from pandas_ta import er as _er
from pandas_ta import aroon as _aroon

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.MinMax.MinMax import MinMax
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
            Map.time: int(int(mkt[0]) / 1000),
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


def get_historic(bnc: Broker, pr: Pair, period: int, nb_prd: int) -> BinanceMarketPrice:
    """
    bnc = Binance(Map({Map.api_pb: "pb_k",
                       Map.api_sk: "sk_k",
                       Map.test_mode: False
                       }))
    """
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
    """
    src_path = 'content/v0.01/2021-04-29 00.23.04_market.csv'
    depot_path = 'content/v0.01/DOGE_USDT-2021-04-29 00.23.04.csv'
    apimarket_to_market(src_path, depot_path)
    """
    """
    bnc_conf = Map({
        Map.api_pb: '',
        Map.api_sk: '',
        Map.test_mode: False
    })
    bnc = Binance(bnc_conf)
    fees1 = bnc.get_trade_fee(Pair("BNB/USDT"))
    print(id(fees1))
    print(fees1)
    fees2 = bnc.get_trade_fee(Pair("BNB/USDT"))
    print(id(fees2))
    print(fees2)
    """
    """
    path = 'content/v0.01/market-historic/active.csv'
    csv = FileManager.get_csv(path)
    market_list = [[row[Map.time], row[Map.open], row[Map.high], row[Map.low], row[Map.close]] for row in csv]
    bnc_market = BinanceMarketPrice(market_list, "1m")
    super_trends = list(bnc_market.get_super_trend())
    super_trends.reverse()
    closes = list(bnc_market.get_closes())
    closes.reverse()
    perfs = MinMax.get_performance(closes, super_trends, 0.001)
    print(perfs)
    """
    # """
    Config.update(Config.STAGE_MODE, Config.STAGE_3)
    minute = 60
    periods = [minute, minute * 3, minute * 5, minute * 15, minute * 30, minute * 60]
    pair = Pair("BNB/USDT")
    nb_period = 1000
    bnc = Binance(Map({Map.api_pb: "",
                       Map.api_sk: "",
                       Map.test_mode: False
                       }))
    fees = bnc.get_trade_fee(pair)
    fee = fees.get(Map.taker)
    rows = []
    for period in periods:
        print(f"Getting {pair}'s performance for the period '{period}'")
        bnc_market = get_historic(bnc, pair, period, nb_period)
        super_trends = list(bnc_market.get_super_trend())
        super_trends.reverse()
        closes = list(bnc_market.get_closes())
        closes.reverse()
        perf = MinMax.get_performance(closes, super_trends, fee)
        row = {
            f"{Map.time}(sec)": period,
            f"{Map.number}_{Map.period}": nb_period,
            Map.fee: fee,
            Map.roi: perf.get(Map.roi)
        }
        rows.append(row)
    # """
    # rows = [{"hello": "world"}]
    fields = list(rows[0].keys())
    path = f'content/v0.01/print/performance-{pair.get_merged_symbols().upper()}.csv'
    FileManager.write_csv(path, fields, rows, False)
    print("Print Success! ✅")
