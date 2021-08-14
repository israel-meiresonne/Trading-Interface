from datetime import datetime
from operator import itemgetter
from time import sleep
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
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Log import Log
from model.structure.Strategy import Strategy
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.MinMax.MinMax import MinMax
from model.structure.strategies.Floor.Floor import Floor
from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.structure.strategies.Stalker.Stalker import Stalker
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
_PRINT_SUCCESS = '🖨 File printed ✅'


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
    print(_PRINT_SUCCESS)


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
    print(_PRINT_SUCCESS)


def historic_to_market(path: str, pair: Pair, period: str) -> MarketPrice:
    _original_stage = Config.get(Config.STAGE_MODE)
    Config.update(Config.STAGE_MODE, Config.STAGE_1)
    # path = "content/v0.01/market-historic/DOGE/DOGEUSDT-5min-2021-05-13 13.44.54.csv"
    csv = FileManager.get_csv(path)
    mkt = [[row[Map.time], row[Map.open], row[Map.high], row[Map.low], row[Map.close]] for row in csv]
    # market_price = BinanceMarketPrice(mkt, "5m", Pair("DOGE/USDT"))
    market_price = BinanceMarketPrice(mkt, period, pair)
    Config.update(Config.STAGE_MODE, _original_stage)
    return market_price


def get_historic(bnc: Broker, pr: Pair, period: int, nb_prd: int, begin_time: int = None, end_time: int = None) -> MarketPrice:
    """
    bnc = Binance(Map({Map.api_pb: "pb_k",
                       Map.api_sk: "sk_k",
                       Map.test_mode: False
                       }))
    """
    rq_prm = Map({Map.pair: pr,
                  Map.period: period,
                  Map.begin_time: begin_time,
                  Map.end_time: end_time,
                  Map.number: nb_prd
                  })
    rq = BinanceRequest(BrokerRequest.RQ_MARKET_PRICE, rq_prm)
    bnc.request(rq)
    mkt = rq.get_market_price()
    return mkt


def print_historic(bkr, pair: Pair, prd: int = 60, nb_prd: int = 1000) -> None:
    # pr = Pair(pr_str)
    mkt = get_historic(bkr, pair, prd, nb_prd)
    print_market(mkt)


def print_market(mkt: MarketPrice) -> str:
    pair = mkt.get_pair()
    closes = mkt.get_closes()
    rows = []
    times = [t for t in mkt.get_times()]
    degs = mkt.get_slopes_degree(14)
    degs = [v for v in degs if v is not None]
    spr_extrems = _MF.get_super_extremums(list(degs))
    super_rsis = mkt.get_super_trend_rsis()
    macds = mkt.get_macd().get(Map.macd)
    signals = mkt.get_macd().get(Map.signal)
    histograms = mkt.get_macd().get(Map.histogram)
    panda_ta_supertrends = mkt.get_super_trend()
    manual_supertrends = wrap_supertrend(mkt)
    for i in range(len(closes)):
        row = {
            Map.time: times[i],
            Map.open: mkt.get_opens()[i],
            Map.high: mkt.get_highs()[i],
            Map.low: mkt.get_lows()[i],
            Map.close: closes[i],
            Map.macd: macds[i],
            Map.signal: signals[i],
            Map.histogram: histograms[i],
            'panda_ta_supertrends': panda_ta_supertrends[i],
            'manual_supertrends': manual_supertrends[i]
        }
        rows.append(row)
    rows.reverse()
    date_format = _MF.FORMAT_D_H_M_S.replace(':', '.')
    file = f"{pair.__str__().upper().replace('/','_')}-{_MF.unix_to_date(_MF.get_timestamp(), date_format)}"
    path = f"content/v0.01/print/{file}.csv"
    fields = list(rows[0].keys())
    overwrite = True
    FileManager.write_csv(path, fields, rows, overwrite)
    print(_PRINT_SUCCESS)
    return path


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
    bnc = Binance(Map({Map.public: "—",
                       Map.secret: "—",
                       Map.test_mode: False
                       }))
    return bnc


def get_top_asset(bnc: Broker, interval: int = 60 * 5, nb_period: int = 1000):
    # period = 60 * 5
    # nb_period = 1000
    # maximum = 3
    top_asset = Strategy.get_top_asset(bnc, MinMax.__name__, interval, nb_period)
    return top_asset


def resume_capital_files(prefix: str) -> None:
    folder_path = 'content/v0.01/tests/'
    file_names = FileManager.get_files(folder_path)
    regex = f'^{prefix}_g_capital_\w+.csv$'
    capiatl_file_names = [file_name for file_name in file_names if _MF.regex_match(regex, file_name)]
    # trade_sections = Map()
    trade_sections = []
    """
    Map[Pair.__str__()][index{int}][Map.capital]:   {Price}
    Map[Pair.__str__()][index{int}][Map.left]:      {Price}
    Map[Pair.__str__()][index{int}][Map.right]:     {Price}
    Map[Pair.__str__()][index{int}][Map.rate]:      {rate}
    """
    right_symbol = 'USDT'
    # print(file_names)
    for file_name in capiatl_file_names:
        # if file_name != '2021-05-23 12.24.51_g_capital_EGLD_USDT.csv':
        #     continue
        file_path = folder_path + file_name
        csv = FileManager.get_csv(file_path)
        left_symbol, _ = csv[0][Map.left].split(' ')
        nb_row = len(csv)
        pair = Pair(left_symbol, right_symbol)
        pair_str = pair.__str__()
        # trade_sections.put([], pair_str)
        for i in range(nb_row):
            row = csv[i]
            if (i == nb_row - 1) or row['initial'] != csv[i + 1]['initial']:
                #  left_value = row[Map.left]
                left_price = str_to_price(row[Map.left])     # Price(left_value, right_symbol)
                right_price = str_to_price(row[Map.right])    # Price(right_value, right_symbol)
                initial_capital_price = str_to_price(row['initial'])
                actual_capital_price = str_to_price(row['current_capital'])
                rate = actual_capital_price / initial_capital_price - 1
                trade_section = {
                    'unix_time': int(_MF.date_to_unix(row[Map.date])),
                    Map.pair: pair_str.upper(),
                    Map.date: row[Map.date],
                    Map.time: row[Map.time],
                    Map.close: row[Map.close],
                    Map.capital: initial_capital_price,
                    'actual_capital': actual_capital_price,
                    Map.fee: str_to_price(row['fees']),
                    Map.left: left_price,
                    Map.right: right_price,
                    Map.rate: rate*100
                }
                # trade_sections.get(pair_str).append(trade_section)
                trade_sections.append(trade_section)
    sections_sorted = sorted(trade_sections, key=lambda row: (row['unix_time'], row[Map.pair]))
    date = _MF.unix_to_date(_MF.get_timestamp())
    fields = list(sections_sorted[0].keys())
    sum_rate = sum([row[Map.rate] for row in sections_sorted])
    sum_fee = Price.sum([row[Map.fee] for row in sections_sorted])
    fee_row = {}
    for field in fields:
        if field == Map.fee:
            fee_row[Map.fee] = sum_fee
        else:
            fee_row[field] = '—'
    rows = [
        {field: f'⬇️ {date} ⬇️' for field in fields},
        *sections_sorted,
        {**{field: f'—' for field in fields if field != Map.rate}, Map.rate: f"{sum_rate}%"},
        fee_row
    ]
    print_path = folder_path + f'{prefix}_fb_global_capital_historic_👾.csv'
    FileManager.write_csv(print_path, fields, rows, overwrite=False)
    print(_PRINT_SUCCESS)


def str_to_price(price_str: str) -> Price:
    symbol, value = price_str.split(' ')
    return Price(value, symbol)


def print_global_capital(prefix: str) -> None:
    interval = 60 * 5
    end = False
    while not end:
        unix_time = _MF.get_timestamp()
        resume_capital_files(prefix)
        new_unix = _MF.get_timestamp()
        unix_rounded = int(new_unix / interval) * interval
        next_time = unix_rounded + interval
        sleep_time = next_time - new_unix
        date = _MF.unix_to_date(unix_time)
        next_date = _MF.unix_to_date(next_time)
        sleep_time_str = f"{int(sleep_time / 60)}min.{sleep_time % 60}sec."
        print(f"Next print of '{prefix}': '{sleep_time_str}': '{date}'->'{next_date}'")
        sleep(sleep_time)


def play_with_websocket() -> None:
    Config.update(Config.STAGE_MODE, Config.STAGE_2)
    bkr = get_broker()
    rq_params = Map({
        Map.pair: Pair('BTC/USDT'),
        Map.period: 60 * 15,
        Map.number: 5
    })
    bkr_rq = Broker.generate_broker_request(Binance.__name__, BrokerRequest.RQ_MARKET_PRICE, rq_params)
    bkr.request(bkr_rq)
    mkt_prc = bkr_rq.get_market_price()
    end = False
    while not end:
        entry = input("Enter your command:\n")
        if entry == 'end':
            end = True
            print('Programme ending...')
        elif entry == 'send':
            bkr_rq = Broker.generate_broker_request(Binance.__name__, BrokerRequest.RQ_MARKET_PRICE, rq_params)
            bkr.request(bkr_rq)
            mkt_prc = bkr_rq.get_market_price()
            print('Request sent and Market retrieved!')
        elif entry == 'show_market':
            bkr_rq = Broker.generate_broker_request(Binance.__name__, BrokerRequest.RQ_MARKET_PRICE, rq_params)
            bkr.request(bkr_rq)
            mkt_prc = bkr_rq.get_market_price()
            pair = mkt_prc.get_pair()
            print(f"Market ({pair}): close='{mkt_prc.get_close()}'")
            close_time = mkt_prc.get_time()
            print(f"Market ({pair}): time='{close_time}'->'{_MF.unix_to_date(close_time)}'")
        elif entry == 'exec':
            exec_end = False
            while not exec_end:
                execution = input('Enter your code:\n')
                print(execution)
                try:
                    exec(execution)
                except Exception as e:
                    print(f"Error: {e}")
                exec_end = execution == 'end'
    bkr.close()


def get_streams(pair_strs) -> List[str]:
    # pair_strs = ['BTC/USDT', 'DOGE/USDT', 'EGLD/USDT', 'ETH/USDT', 'BNB/USDT', 'SNX/USDT', 'BTC/USDT', 'DOGE/USDT']
    # ['btcusdt@kline_1m', 'dogeusdt@kline_3m', 'egldusdt@kline_3m', 'ethusdt@kline_5m', 'bnbusdt@kline_5m',
    # 'snxusdt@kline_15m', 'btcusdt@kline_15m', 'dogeusdt@kline_15m']
    streams = []
    i = 1
    for pair_str in pair_strs:
        stream = Binance.generate_stream(Map({
            Map.pair: Pair(pair_str),
            Map.period: 60 * i
        }))
        streams.append(stream)
        i += 1
    return streams


def analyse_final_roi(file_name: str) -> None:
    """
    group[Map.pair]:    {List[row{dict}]}
    """
    start_time = _MF.get_timestamp()
    def delta_date(newest: str, older: str) -> int:
        return int(_MF.date_to_unix(newest) - _MF.date_to_unix(older))

    def get_fees(exp: float) -> float:
        return (1+consts[2])**(exp) - 1

    def str_rate_to_float(str_rate: str) -> float:
        return eval(str_rate.replace('%', '/100'))
    path_base = f'content/v0.01/analyse/'
    src_path = f'{path_base}source/{file_name}'
    print(_MF.prefix(), 'Start getting csv')
    csv = FileManager.get_csv(src_path)
    groups = {}
    print(_MF.prefix(), 'Start Grouping')
    for row in csv:
        pair = row[Map.pair]
        groups[pair] = [] if pair not in groups else groups[pair]
        groups[pair].append(row)
    print(_MF.prefix(), 'Start sorting')
    for pair, rows in groups.items():
        groups[pair] = sorted(groups[pair], key=itemgetter('date'))
    print(_MF.prefix(), 'Start analyse')
    new_keys = [
        'New Pair?',
        'Last Pair?',
        'Entry'
    ]
    consts = [
        '—',        # 0
        '⬇️ ——— ⬇️',# 1
        0.0010,    # 2
        60 * 5     # 3
    ]
    print_rows = []
    for pair, rows in groups.items():
        if not _MF.regex_match('^.+/.+$', pair):
            continue
        i = 0
        first_row = rows[0]
        last_row = rows[-1]
        for row in rows:
            if row[Map.date] == '2021-08-05 14:54:50':
                print('ok')
            prev_row = rows[i-1] if i > 0 else None
            row['New Pair?'] = new_pair = row[Map.date] == first_row[Map.date]
            row['Last Pair?'] = last_pair = row[Map.date] == last_row[Map.date]
            key_out = 'Out'
            row['Entry'] = entry = 1 if new_pair or (row['last_roi'] == consts[0]) or (prev_row[key_out] == 1) else 0
            roi_bellow_floor = ((row['last_floor'] != consts[0])
                                and (str_rate_to_float(row[Map.roi]) <= str_rate_to_float(row['last_floor'])))
            row[key_out] = out = 1 if (not (row['supertrend_rising'] == 'True')) \
                                    or str_rate_to_float(row[Map.roi]) <= str_rate_to_float(row['max_loss']) \
                                    or roi_bellow_floor \
                                    or last_pair else 0
            row['Fee'] = get_fees(entry + out)
            row['Final roi'] = final_roi = str_rate_to_float(row[Map.roi]) if out == 1 else consts[0]
            prev_last_final_roi = prev_row['Last Final roi'] if prev_row is not None else consts[0]
            row['Last Final roi'] = last_final_roi = final_roi if final_roi != consts[0] else prev_last_final_roi
            key_new_last_entry = 'New Last Entry'
            prev_new_last_entry = prev_row[key_new_last_entry] if isinstance(prev_row, dict) else None
            time_ok = (delta_date(row[Map.date], prev_new_last_entry)) >= consts[3] if prev_new_last_entry is not None else False
            row[key_new_last_entry] = row[Map.date] if (prev_new_last_entry is None) or new_pair or ((entry == 1) and time_ok) else prev_new_last_entry
            row['New Holds time'] = new_holds_time = delta_date(row[Map.date], row[key_new_last_entry])
            row['New Final roi'] = new_final_roi = last_final_roi if ((new_holds_time >= consts[3]) and (out == 1)) \
                                                                     or last_pair \
                                                                     or roi_bellow_floor else consts[0]
            row['New Out'] = new_out = 1 if new_final_roi != consts[0] else 0
            row['New Fee'] = get_fees(2) if new_out == 1 else consts[0]
            print_rows.append(row)
            i += 1
    print(_MF.prefix(), 'Start printing')
    fields = list(print_rows[0].keys())
    depot_path = f"{path_base}depot/{file_name.replace('.csv', '_final-roi.csv')}"
    FileManager.write_csv(depot_path, fields, print_rows)
    exec_time = _MF.get_timestamp() - start_time
    exec_time_str = f"{int(exec_time / 60)}min.{exec_time % 60}sec."
    print(_MF.prefix(), f"End printing: exec_time='{exec_time_str}'")


def execute_orders() -> None:
    bkr = get_broker()
    pair = Pair('BTC/USDT')
    mkt = get_historic(bkr, pair, 60 * 5, 1000)
def filter_with_macd() -> None:
    bkr = get_broker()
    pair = Pair('DOGE/USDT')
    mkt = get_historic(bkr, pair, period=60 * 15, nb_prd=1000)
    bkr.close()
    times = list(mkt.get_times())
    times.reverse()
    closes = list(mkt.get_closes())
    closes.reverse()
    superstrends = list(mkt.get_super_trend())
    # MACD
    macd_map = mkt.get_macd(signal=5)
    macds = list(macd_map.get(Map.macd))
    macds.reverse()
    signals = list(macd_map.get(Map.signal))
    signals.reverse()
    histograms = list(macd_map.get(Map.histogram))
    histograms.reverse()
    # Switcher
    switchers = MarketPrice.get_super_trend_switchers(closes, superstrends)
    risings = []
    idxs = switchers.get_keys()
    i = 0
    rows = []
    macd_rows = []

    def roi(new: float, old: float) -> float:
        return round((new / old - 1) * 100, 2)

    def roi_str(new: float, old: float) -> str:
        return f"{roi(new, old)}%"

    def macd_ok(index: int, macds: list, signals: list, histograms: list) -> bool:
        macd = macds[index]
        signal = signals[index]
        histogram = histograms[index]
        positives = (macd > 0) and (signal > 0) and (histogram > 0)
        macds_ok = positives and (macd > signal) and (signal > histogram)
        return macds_ok

    for idx in idxs:
        if idx != idxs[-1]:
            trend = switchers.get(idx)
            if trend == MarketPrice.SUPERTREND_RISING:
                next_idx = idxs[i + 1]
                rising = closes[idx:next_idx]
                risings.append(rising)
                first = rising[0]
                rising_max = max(rising)
                rising_min = min(rising)
                rising_avg = sum(rising) / len(rising)
                row = {
                    'index': idx,
                    'UTC': _MF.unix_to_date(times[idx]),
                    'first': first,
                    'last': rising[-1],
                    'avg': rising_avg,
                    'avg_roi': roi_str(rising_avg, first),
                    'max': rising_max,
                    'max_roi': roi_str(rising_max, first),
                    'min': rising_min,
                    'min_roi': roi_str(rising_min, first)
                }
                rows.append(row)
                if macd_ok(idx, macds, signals, histograms):
                    macd_rows.append(row)
        i += 1
    print(_MF.json_encode(rows))
    print(_MF.json_encode(macd_rows))


def wrap_supertrend(mkt: MarketPrice) -> list:
    # Closes
    closes = list(mkt.get_closes())
    closes.reverse()
    pd_closes = pd.Series(np.array(closes))
    # Lows
    lows = list(mkt.get_lows())
    lows.reverse()
    pd_lows = pd.Series(np.array(lows))
    # Highs
    highs = list(mkt.get_highs())
    highs.reverse()
    pd_highs = pd.Series(np.array(highs))
    # supertrend_series, st_up, st_down = get_supertrend(pd_highs, pd_lows, pd_closes)
    supertrend_series = get_supertrend(pd_highs, pd_lows, pd_closes)
    supertrends = supertrend_series.iloc[:, 0].to_list()
    supertrends.insert(0, np.nan)
    supertrends.reverse()
    return supertrends


def get_supertrend(high, low, close, lookback=10, multiplier=3):
    # ATR

    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.ewm(lookback).mean()

    # H/L AVG AND BASIC UPPER & LOWER BAND

    hl_avg = (high + low) / 2
    upper_band = (hl_avg + multiplier * atr).dropna()
    lower_band = (hl_avg - multiplier * atr).dropna()

    # FINAL UPPER BAND
    final_bands = pd.DataFrame(columns=['upper', 'lower'])
    final_bands.iloc[:, 0] = [x for x in upper_band - upper_band]
    final_bands.iloc[:, 1] = final_bands.iloc[:, 0]
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 0] = 0
        else:
            if (upper_band[i] < final_bands.iloc[i - 1, 0]) | (close[i - 1] > final_bands.iloc[i - 1, 0]):
                final_bands.iloc[i, 0] = upper_band[i]
            else:
                final_bands.iloc[i, 0] = final_bands.iloc[i - 1, 0]

    # FINAL LOWER BAND

    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 1] = 0
        else:
            if (lower_band[i] > final_bands.iloc[i - 1, 1]) | (close[i - 1] < final_bands.iloc[i - 1, 1]):
                final_bands.iloc[i, 1] = lower_band[i]
            else:
                final_bands.iloc[i, 1] = final_bands.iloc[i - 1, 1]

    # SUPERTREND

    supertrend = pd.DataFrame(columns=[f'supertrend_{lookback}'])
    supertrend.iloc[:, 0] = [x for x in final_bands['upper'] - final_bands['upper']]

    for i in range(len(supertrend)):
        if i == 0:
            supertrend.iloc[i, 0] = 0
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and close[i] < final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and close[i] > final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and close[i] > final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and close[i] < final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]

    supertrend = supertrend.set_index(upper_band.index)
    supertrend = supertrend.dropna()[1:]

    # ST UPTREND/DOWNTREND

    upt = []
    dt = []
    close = close.iloc[len(close) - len(supertrend):]
    """
    for i in range(len(supertrend)):
        if close[i] > supertrend.iloc[i, 0]:
            upt.append(supertrend.iloc[i, 0])
            dt.append(np.nan)
        elif close[i] < supertrend.iloc[i, 0]:
            upt.append(np.nan)
            dt.append(supertrend.iloc[i, 0])
        else:
            upt.append(np.nan)
            dt.append(np.nan)

    st, upt, dt = pd.Series(supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
    upt.index, dt.index = supertrend.index, supertrend.index

    return st, upt, dt
    """
    return supertrend


if __name__ == '__main__':
    Config.update(Config.STAGE_MODE, Config.STAGE_2)
    bkr = get_broker()
    print_historic(bkr, Pair('BTC/USDT'), 60 * 15)
    bkr.close()
    close = mkt.get_close()
    bkr_odr1 = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, Map({
        Map.pair: pair,
        Map.move: Order.MOVE_BUY,
        Map.amount: Price(10, pair.get_right().get_symbol())
    }))
    bkr_odr2 = Order.generate_broker_order(Binance.__name__, Order.TYPE_MARKET, Map({
        Map.pair: pair,
        Map.move: Order.MOVE_SELL,
        Map.quantity: Price(100 / close, pair.get_left().get_symbol())
    }))
    bkr_odr3 = Order.generate_broker_order(Binance.__name__, Order.TYPE_STOP_LIMIT, Map({
        Map.pair: pair,
        Map.move: Order.MOVE_BUY,
        Map.stop: Price(close, pair.get_right().get_symbol()),
        Map.limit: Price(close, pair.get_right().get_symbol()),
        Map.quantity: Price(1000 / close, pair.get_left().get_symbol())
    }))
    bkr_odr4 = Order.generate_broker_order(Binance.__name__, Order.TYPE_STOP_LIMIT, Map({
        Map.pair: pair,
        Map.move: Order.MOVE_SELL,
        Map.stop: Price(close, pair.get_right().get_symbol()),
        Map.limit: Price(close, pair.get_right().get_symbol()),
        Map.quantity: Price(10000 / close, pair.get_left().get_symbol())
    }))
    bkr.execute(bkr_odr1)
    bkr.execute(bkr_odr2)
    bkr.execute(bkr_odr3)
    bkr.execute(bkr_odr4)
    bkr_rq_orders = BinanceRequest(BrokerRequest.RQ_ORDERS, Map({
        Map.pair: pair
    }))
    bkr_rq_trades = BinanceRequest(BrokerRequest.RQ_TRADES, Map({
        Map.pair: pair
    }))
    bkr.request(bkr_rq_orders)
    bkr.request(bkr_rq_trades)
    print('End')


if __name__ == '__main__':
    Config.update(Config.STAGE_MODE, Config.STAGE_2)
    execute_orders()
