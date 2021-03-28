from model.API.brokers.Binance.Binance import Binance
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
    closes = mkt.get_closes()
    rows = []
    # times = [int(t / 1000) for t in mkt.get_times()]
    times = [t for t in mkt.get_times()]
    for i in range(len(closes)):
        row = {
            Map.time: times[i],
            Map.open: mkt.get_opens()[i],
            Map.high: mkt.get_highs()[i],
            Map.low: mkt.get_lows()[i],
            Map.close: closes[i],
            Map.rsi: mkt.get_rsis()[i],
            Map.super_trend: mkt.get_super_trend()[i]
        }
        rows.append(row)
    rows.reverse()
    p = f"content/v0.01/market-historic/{pr.get_merged_symbols().upper()}-{_MF.unix_to_date(_MF.get_timestamp())}.csv"
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
    print_historic("COS/USDT")
    # nb_prd = 5
    p = "content/v0.01/market-historic/SuperTrend.csv"
    csv = FileManager.get_csv(p)
    mkt_list = [[int(line[Map.date]), '0', line[Map.high], line[Map.low], line[Map.close]] for line in csv]
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
