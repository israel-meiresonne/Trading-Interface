from datetime import datetime
from typing import List

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
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.MinMax.MinMax import MinMax
from model.structure.strategies.Floor.Floor import Floor
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Paire import Pair
from model.tools.Price import Price


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


def historic_to_market(path: str) -> MarketPrice:
    _original_stage = Config.get(Config.STAGE_MODE)
    Config.update(Config.STAGE_MODE, Config.STAGE_1)
    # path = "content/v0.01/market-historic/DOGE/DOGEUSDT-5min-2021-05-13 13.44.54.csv"
    csv = FileManager.get_csv(path)
    mkt = [[row[Map.time], row[Map.open], row[Map.high], row[Map.low], row[Map.close]] for row in csv]
    market_price = BinanceMarketPrice(mkt, "5m", Pair("DOGE/USDT"))
    Config.update(Config.STAGE_MODE, _original_stage)
    return market_price

def get_historic(bnc: Broker, pr: Pair, period: int, nb_prd: int) -> MarketPrice:
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


def print_historic(bkr, pair: Pair, prd: int = 60, nb_prd: int = 1000) -> None:
    # pr = Pair(pr_str)
    mkt = get_historic(bkr, pair, prd, nb_prd)
    print_market(mkt, pair)


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
    # super_tsis = mkt.get_super_trend_tsis()
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
            # 'super_tsis': super_tsis[i],
            'slopes': mkt.get_slopes(14)[i],
            'slope_deg': mkt.get_slopes_degree()[i],
            'extremuns': degs[i] if i in spr_extrems else None
        }
        rows.append(row)
    rows.reverse()
    date_format = _MF.FORMAT_D_H_M_S.replace(':', '.')
    file = f"{pr.get_merged_symbols().upper()}-{_MF.unix_to_date(_MF.get_timestamp(), date_format)}"
    p = f"content/v0.01/print/{file}.csv"
    fields = list(rows[0].keys())
    overwrite = True
    FileManager.write_csv(p, fields, rows, overwrite)
    print("🖨 File printed ✅")


def performance_get_rates(market_price: MarketPrice) -> list:
    # Init
    perf_rates = []
    buy_price = None
    sell_price = None       # ❌
    last_floor = None       # ❌
    perf_rate = None        # ❌
    floors = [i * 10 for i in range(11)]
    rsi_entry_trigger = 25
    min_out_floor = 30
    up_min_floor_once = None
    # max_loss_rate = -0.03
    # max_loss_close = None
    # Extract lists
    times = list(market_price.get_times())
    times.reverse()
    closes = list(market_price.get_closes())
    closes.reverse()
    rsis = list(market_price.get_rsis())
    rsis.reverse()
    # Print
    rows = []
    for i in range(len(rsis)):
        rsi = rsis[i]
        last_rsi = rsis[i - 1] if i > 0 else None
        close = closes[i]
        if (buy_price is None) \
                and ((rsi is not None)
                and (last_rsi is not None)) and ((last_rsi <= rsi_entry_trigger) and (rsi > last_rsi)):
            buy_price = closes[i]
            # max_loss_close = buy_price * (1 + max_loss_rate)
            """
            elif (buy_price is not None) and (close <= max_loss_close):
                # sell_price = close
                perf_rate = max_loss_close / buy_price - 1
                perf_rates.append(perf_rate)
                buy_price = None
                up_min_floor_once = None
                last_floor = None
                max_loss_close = None
            """
        elif buy_price is not None:
            up_min_floor_once = rsi > min_out_floor if (up_min_floor_once is None) or (not up_min_floor_once) else up_min_floor_once
            if up_min_floor_once:
                last_floor = floors[get_floor_index(last_rsi, floors)]
                if (last_floor >= min_out_floor) and (rsi < last_floor):
                    sell_price = close
                    perf_rate = sell_price / buy_price - 1
                    perf_rates.append(perf_rate)
                    buy_price = None
                    up_min_floor_once = None
                    last_floor = None
                    # max_loss_close = None
        row = {
            Map.time: _MF.unix_to_date(times[i]),
            Map.close: _MF.float_to_str(close),
            Map.rsi: _MF.float_to_str(rsi),
            "last_rsi": _MF.float_to_str(last_rsi),
            "rsi_entry": _MF.float_to_str(rsi_entry_trigger),
            "min_out_floor": _MF.float_to_str(min_out_floor),
            "up_min_floor_once": up_min_floor_once,
            "last_floor": _MF.float_to_str(last_floor),
            # "max_loss_rate": max_loss_rate,
            # "max_loss_close": max_loss_close,
            "perf_rate": _MF.float_to_str(perf_rate),
            Map.buy: _MF.float_to_str(buy_price),
            Map.sell: _MF.float_to_str(sell_price),
            "floors": floors
        }
        rows.append(row)
        perf_rate = None
        sell_price = None
    date = _MF.unix_to_date(_MF.get_timestamp(), _MF.FORMAT_D_H_M_S).replace(":", ".")
    path = f'content/v0.01/print/Floor_perf-{date}.csv'
    fields = list(rows[0].keys())
    FileManager.write_csv(path, fields, rows)
    return perf_rates


def get_floor_index(val: float, levels: List[int]) -> int:
    idx = None
    for i in range(len(levels)):
        if val < levels[i]:
            idx = i - 1
            break
    return idx


def print_performance(rows: list, path: str) -> None:
    fields = list(rows[0].keys())
    FileManager.write_csv(path, fields, rows, False)
    print("Print Success! ✅")


def get_broker() -> Broker:
    bnc = Binance(Map({Map.api_pb: "mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5",
                       Map.api_sk: "xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr",
                       Map.test_mode: False
                       }))
    return bnc


def get_top_asset(bnc: Broker, interval: int = 60 * 5, nb_period: int = 1000):
    # period = 60 * 5
    # nb_period = 1000
    # maximum = 3
    top_asset = Strategy.get_top_asset(bnc, MinMax.__name__, interval, nb_period)
    return top_asset


if __name__ == '__main__':
    """
    for i in range(0, 2):
        src_path = f'content/v0.01/2021-05-08 22.19.36_market-1-{i}.csv'
        depot_path = f'content/v0.01/DOGE_USDT-2021-05-08 22.19.36-{i}.csv'
        apimarket_to_market(src_path, depot_path)
    """
    # bnc = get_broker()
    # print_historic(bnc, Pair("DOGE/USDT"), 60*5)
    Config.update(Config.STAGE_MODE, Config.STAGE_1)
    path = "content/v0.01/market-historic/DOGE/DOGEUSDT-5min-2021-05-13 13.44.54.csv"
    """
    csv = FileManager.get_csv(path)
    mkt = [[row[Map.time], row[Map.open], row[Map.high], row[Map.low], row[Map.close]] for row in csv]
    market_price = BinanceMarketPrice(mkt, "5m", Pair("DOGE/USDT"))
    market_price = historic_to_market(path)
    """
    """
    rates = performance_get_rates(market_price)
    print(rates)
    print(sum(rates)*100)
    """
    """
    bnc = get_broker()
    perf = Floor.get_performance(bnc, Floor.__name__, market_price)
    print(_MF.json_encode(perf.get_map()))
    """
