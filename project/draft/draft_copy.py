import os
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd


def push_path() -> None:
    file_path = os.path.abspath(__file__)
    project_dir = '/'.join(file_path.split('/')[:-2]) + '/'
    sys.path.append(project_dir) if project_dir not in sys.path else None
push_path()

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.API.brokers.Binance.BinanceSocket import BinanceSocket
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Hand import Hand
from model.structure.strategies.Strategy import Strategy
from model.tools.Asset import Asset
from model.tools.FileManager import FileManager
from model.tools.HandTrade import HandTrade
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from view.Console.View import View


class Analyse:
    @staticmethod
    def get_period_str(marketprice: MarketPrice) -> str:
        period_str = BinanceAPI.convert_interval(marketprice.get_period_time())
        return period_str

    @staticmethod
    def get_prices(marketprice: MarketPrice, price_name: str) -> list:
        prices = list(eval(f'marketprice.get_{price_name}s()'))
        prices.reverse()
        return prices

    @staticmethod
    def key_keltner(period_str: str, keltner_line: str, index: int) -> str:
        return f'keltner({period_str},{keltner_line})[{index}]'

    @staticmethod
    def key_ema(period_str: str, ema_n_period: int, index: int) -> str:
        return f'ema({period_str},{ema_n_period})[{index}]'

    @staticmethod
    def key_price(period_str: str, price_name: str, index: int) -> str:
        return f'price_{price_name}({period_str})[{index}]'

    @staticmethod
    def key_macd(period_str: str, macd_line: str, macd_params: dict, index: int) -> str:
        params_str = Analyse.join_params(macd_params)
        return f"macd({period_str},{macd_line},{params_str})[{index}]"

    @staticmethod
    def join_params(params: dict) -> str:
        return ','.join([f'{k}={v}' for k, v in params.items()])

    @staticmethod
    def is_ema_above_keltner(func_vars_map: Map, marketprice: MarketPrice, ema_n_period: int, keltner_line: str) -> bool:
        period_str = Analyse.get_period_str(marketprice)
        marketprice.reset_collections()
        keltner_map = marketprice.get_keltnerchannel()
        keltner = list(keltner_map.get(keltner_line))
        keltner.reverse()
        ema = list(marketprice.get_ema(n_period=ema_n_period))
        ema.reverse()
        # Check
        ema_above_keltner = ema[-1] > keltner[-1]
        # Put
        func_vars_map.put(
            keltner[-1], Analyse.key_keltner(period_str, keltner_line, -1))
        func_vars_map.put(
            ema[-1], Analyse.key_ema(period_str, ema_n_period, -1))
        return {f'ema({period_str},{ema_n_period})_above_keltner({period_str},{keltner_line})': ema_above_keltner}

    @staticmethod
    def is_price_above_keltner(func_vars_map: Map, marketprice: MarketPrice, price_name: str, keltner_line: str) -> bool:
        period_str = Analyse.get_period_str(marketprice)
        marketprice.reset_collections()
        keltner_map = marketprice.get_keltnerchannel()
        keltner = list(keltner_map.get(keltner_line))
        keltner.reverse()
        prices = Analyse.get_prices(marketprice, price_name)
        # Check
        price_above_keltner = prices[-1] > keltner[-1]
        # Put
        func_vars_map.put(
            keltner[-1], Analyse.key_keltner(period_str, keltner_line, -1))
        func_vars_map.put(
            prices[-1], Analyse.key_price(period_str, price_name, -1))
        return {f'{price_name}({period_str})_above_keltner({period_str},{keltner_line})': price_above_keltner}

    @staticmethod
    def is_price_above_ema(func_vars_map: Map, marketprice: MarketPrice, price_name: str, ema_n_period: int) -> bool:
        period_str = Analyse.get_period_str(marketprice)
        marketprice.reset_collections()
        ema = list(marketprice.get_ema(n_period=ema_n_period))
        ema.reverse()
        prices = Analyse.get_prices(marketprice, price_name)
        # Check
        price_above_ema = prices[-1] > ema[-1]
        # Put
        func_vars_map.put(
            ema[-1], Analyse.key_ema(period_str, ema_n_period, -1))
        func_vars_map.put(
            prices[-1], Analyse.key_price(period_str, price_name, -1))
        return {f'{price_name}({period_str})_above_ema({period_str},{ema_n_period})': price_above_ema}

    @staticmethod
    def is_macd_positive(func_vars_map: Map, marketprice: MarketPrice, macd_line: str, macd_params: dict = {}) -> bool:
        marketprice.reset_collections()
        period_str = Analyse.get_period_str(marketprice)
        macd_map = marketprice.get_macd() if len(
            macd_params) == 0 else marketprice.get_macd(**macd_params)
        macd_list = list(macd_map.get(macd_line))
        macd_list.reverse()
        # Check
        macd_positive = macd_list[-1] > 0
        # Put
        func_vars_map.put(
            macd_list[-1], Analyse.key_macd(period_str, macd_line, macd_params, -1))
        func_vars_map.put(
            macd_list[-2], Analyse.key_macd(period_str, macd_line, macd_params, -2))
        func_vars_map.put(
            macd_list[-3], Analyse.key_macd(period_str, macd_line, macd_params, -3))
        return {f'macd({period_str},{macd_line},{Analyse.join_params(macd_params)})_positive': macd_positive}

    @staticmethod
    def is_supertrend_rising(func_vars_map: Map, marketprice: MarketPrice) -> bool:
        marketprice.reset_collections()
        period_str = Analyse.get_period_str(marketprice)
        price_name = Map.close
        supertrend = list(marketprice.get_super_trend())
        supertrend.reverse()
        closes = Analyse.get_prices(marketprice, price_name)
        # Check
        supertrend_rising = MarketPrice.get_super_trend_trend(
            closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
        # Put
        func_vars_map.put(supertrend[-1], f'supertrend({period_str})[-1]')
        func_vars_map.put(
            closes[-1], Analyse.key_price(period_str, price_name, -1))
        return {f'supertrend({period_str})_rising': supertrend_rising}

    @staticmethod
    def is_psar_rising(func_vars_map: Map, marketprice: MarketPrice) -> bool:
        marketprice.reset_collections()
        period_str = Analyse.get_period_str(marketprice)
        price_name = Map.close
        psar = list(marketprice.get_psar())
        psar.reverse()
        closes = Analyse.get_prices(marketprice, price_name)
        # Check
        psar_rising = MarketPrice.get_psar_trend(
            closes, psar, -1) == MarketPrice.PSAR_RISING
        # Put
        func_vars_map.put(psar[-1], f'psar({period_str})[-1]')
        func_vars_map.put(
            closes[-1], Analyse.key_price(period_str, price_name, -1))
        return {f'psar({period_str})_rising': psar_rising}

    @staticmethod
    def is_candle_change_above_trigger(func_vars_map: Map, marketprice: MarketPrice, trigger: float, n_candle: int) -> bool:
        marketprice.reset_collections()
        period_str = Analyse.get_period_str(marketprice)
        opens = list(marketprice.get_opens())
        opens.reverse()
        closes = list(marketprice.get_closes())
        closes.reverse()
        # Get mean change
        mean_candle_change = MarketPrice.mean_candle_variation(
            opens[-n_candle:], closes[-n_candle:])
        mean_sequence = MarketPrice.mean_candle_sequence(
            opens[-n_candle:], closes[-n_candle:])
        # Check
        candle_change_above_trigger = mean_candle_change.get(
            Map.positive, Map.mean) >= trigger
        # Put
        func_vars_map.put(
            trigger, f'mean_candle_change_trigger_{trigger}({period_str})')
        func_vars_map.put(mean_candle_change.get(Map.positive, Map.mean),
                          f'mean_candle_change_positive_mean_{n_candle}({period_str})')
        func_vars_map.put(mean_candle_change.get(Map.positive, Map.stdev),
                          f'mean_candle_change_positive_stdev_{n_candle}({period_str})')
        func_vars_map.put(mean_candle_change.get(Map.negative, Map.mean),
                          f'mean_candle_change_negative_mean_{n_candle}({period_str})')
        func_vars_map.put(mean_candle_change.get(Map.negative, Map.stdev),
                          f'mean_candle_change_negative_stdev_{n_candle}({period_str})')
        func_vars_map.put(mean_sequence.get(
            Map.positive), f'mean_candle_change_positive_sequence_{n_candle}({period_str})')
        func_vars_map.put(mean_sequence.get(
            Map.negative), f'mean_candle_change_negative_sequence_{n_candle}({period_str})')
        return {f'candle_change_above_trigger_{n_candle}({period_str})': candle_change_above_trigger}

    @staticmethod
    def is_keltner_roi_above_trigger(func_vars_map: Map, marketprice: MarketPrice, trigger: float, multiple: int) -> dict:
        marketprice.reset_collections()
        period_str = Analyse.get_period_str(marketprice)
        keltner = marketprice.get_keltnerchannel(multiple=multiple)
        keltner_low = list(keltner.get(Map.low))
        keltner_low.reverse()
        keltner_high = list(keltner.get(Map.high))
        keltner_high.reverse()
        # Check
        keltner_roi = _MF.progress_rate(keltner_high[-1], keltner_low[-1])
        keltner_roi_above_trigger = keltner_roi >= trigger
        # Put
        func_vars_map.put(
            trigger, f'keltner_roi_above_trigger({period_str},multiple={multiple})_trigger')
        func_vars_map.put(
            keltner_roi, f'keltner_roi_above_trigger{trigger}({period_str},multiple={multiple})_keltner_roi')
        return {f'keltner_roi(multiple={multiple})_above_trigger({period_str})': keltner_roi_above_trigger}

    @staticmethod
    def test_metrics(func_vars_map: Map, marketprice: MarketPrice) -> dict:
        ema200_n_period = 200
        ema50_n_period = 50
        macd_params_100 = Icarus.MACD_PARAMS_1
        return {
            # EMA200 > Keltner
            # —— Local
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema200_n_period, Map.high),
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema200_n_period, Map.middle),
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema200_n_period, Map.low),
            # EMA50 > Keltner
            # —— Local
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema50_n_period, Map.high),
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema50_n_period, Map.middle),
            **Analyse.is_ema_above_keltner(func_vars_map, marketprice, ema50_n_period, Map.low),
            # Price > Keltner
            # —— Local|Close
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.close, Map.high),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.close, Map.middle),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.close, Map.low),
            # —— Local|High
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.high, Map.high),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.high, Map.middle),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.high, Map.low),
            # —— Local|Low
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.low, Map.high),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.low, Map.middle),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.low, Map.low),
            # —— Local|Open
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.open, Map.high),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.open, Map.middle),
            **Analyse.is_price_above_keltner(func_vars_map, marketprice, Map.open, Map.low),
            # Price > EMA200
            # —— Local
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.open, ema200_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.high, ema200_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.low, ema200_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.close, ema200_n_period),
            # Price > EMA50
            # —— Local
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.open, ema50_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.high, ema50_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.low, ema50_n_period),
            **Analyse.is_price_above_ema(func_vars_map, marketprice, Map.close, ema50_n_period),
            # MACD > 0
            # —— Local
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.macd),
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.signal),
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.histogram),
            # Edited MACD > 0
            # —— Local
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.macd, macd_params_100),
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.signal, macd_params_100),
            **Analyse.is_macd_positive(func_vars_map, marketprice, Map.histogram, macd_params_100),
            # Supertrend
            **Analyse.is_supertrend_rising(func_vars_map, marketprice),
            # Psar
            **Analyse.is_psar_rising(func_vars_map, marketprice),
            # Candle
            **Analyse.is_candle_change_above_trigger(func_vars_map, marketprice, trigger=1/100, n_candle=15),
            **Analyse.is_candle_change_above_trigger(func_vars_map, marketprice, trigger=1/100, n_candle=30),
            **Analyse.is_candle_change_above_trigger(func_vars_map, marketprice, trigger=1/100, n_candle=60),
            # Keltner_roi
            **Analyse.is_keltner_roi_above_trigger(func_vars_map, marketprice, trigger=1/100, multiple=1),
            **Analyse.is_keltner_roi_above_trigger(func_vars_map, marketprice, trigger=1/100, multiple=MarketPrice._KELTNERC_MULTIPLE)
        }


class Draft(Order, Hand):
    _PRINT_SUCCESS = '🖨 File printed ✅'
    _BROKER = Binance(
        Map({Map.public: "-", Map.secret: "-", Map.test_mode: False}))
    _VIEW = View()
    RECORD_OPTIONS = ['Record', 'Print']
    CONSTRAINT_KLINES_MAX_PERIOD = 300

    @staticmethod
    def get_broker() -> Broker:
        return Draft._BROKER

    @staticmethod
    def get_view() -> View:
        return Draft._VIEW

    @staticmethod
    def tag_session_id() -> str:
        command = "git branch | egrep '^\*'"
        output = subprocess.check_output(command, shell=True)
        output = output.decode("utf-8").replace("* ", "").replace("\n", "")
        session_id = Config.get(Config.SESSION_ID)
        new_session_id = f"{session_id}_{output}"
        return Draft.update_session_id(new_session_id)

    @staticmethod
    def update_session_id(new_id: str) -> str:
        Config.update(Config.SESSION_ID, '@xxx@')
        Config.update(Config.SESSION_ID, new_id)
        return Config.get(Config.SESSION_ID)

    @classmethod
    def set_model_output(cls, record_option: str = None) -> None:
        _MF.check_type(record_option, str) if record_option is not None else None
        if record_option is None:
            view = Draft.get_view()
            record_options = cls.RECORD_OPTIONS
            record_option = record_options[view.menu("Do you want to record or print Standard Ouput:", record_options)]
        _MF.OUTPUT = record_option == record_options[1]

    @staticmethod
    def download_market_histories() -> None:
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        Config.print_session_config()
        broker = Draft.get_broker()
        broker_name = broker.__class__.__name__
        starttime = int(_MF.date_to_unix('2020-01-01 0:00:00'))
        endtime =   int(_MF.date_to_unix('2023-07-15 00:00:00'))
        fiat_asset = Asset('USDT')
        pairs = all_pairs = MarketPrice.get_spot_pairs(broker_name, fiat_asset)
        # pairs = existing_pairs = MarketPrice.history_pairs(broker_name, active_path=False)
        # pairs = miss_pairs = [pair for pair in all_pairs if pair not in existing_pairs]
        download_pairs = pairs
        periods = [60, 60*3, 60*5, 60*15, 60*30, 60*60, 60*60*6]
        MarketPrice.download_marketprices(
            broker, download_pairs, periods, endtime, starttime)
        Config.update(Config.STAGE_MODE, old_stage)

    @staticmethod
    def listen_market() -> None:
        def print_market() -> None:
            while END != "end":
                marketprice = MarketPrice.marketprice(
                    broker, pair, period, n_period)
                close = marketprice.get_close()
                open_time = marketprice.get_time()
                unix_time = _MF.get_timestamp()
                print(
                    f"{_MF.unix_to_date(unix_time)}: open_time='{_MF.unix_to_date(open_time)}', close='{close}'")
                time.sleep(1)

        BinanceSocket._DEBUG = False
        broker = Draft.get_broker()
        view = Draft.get_view()
        pair = Pair(view.input("Enter the Pair to listen:"))
        period = 60
        n_period = 10
        END = None
        th, output = _MF.generate_thread(print_market, 'print_market')
        print(output)
        th.start()
        while END != "end":
            END = input("Tape 'end' to end console: ")

    @staticmethod
    def analyse_market_trend() -> None:
        def is_end() -> bool:
            return END == 'end'

        def analyse() -> None:
            sleep_interval = 60
            while not is_end():
                trends = MarketPrice.analyse_market_trend(broker)
                rising_rate = trends.get(MarketPrice.MARKET_TREND_RISING)
                unix_time = _MF.get_timestamp()
                wake_time = _MF.round_time(
                    unix_time, sleep_interval) + sleep_interval
                sleep_time = wake_time - unix_time
                print(_MF.prefix(
                ) + f"Rising rate: '{_MF.rate_to_str(rising_rate)}' — Sleep for '{_MF.delta_time(0,sleep_time)}'")
                time.sleep(sleep_time)

        _MF.OUTPUT = False
        BinanceSocket._DEBUG = True
        END = None
        broker = Draft.get_broker()
        period = MarketPrice.get_period_market_analyse()
        pairs = MarketPrice.get_spot_pairs(
            broker.__class__.__name__, Asset('USDT'))
        streams = [broker.generate_stream(
            Map({Map.pair: pair, Map.period: period})) for pair in pairs]
        streams = [
            *[broker.generate_stream(Map({Map.pair: pair, Map.period: 60}))
              for pair in pairs],
            *streams
        ]
        broker.add_streams(streams)
        analyse_thread, output = _MF.generate_thread(analyse, 'market_analyse')
        print(_MF.prefix() + output)
        analyse_thread.start()
        while not is_end():
            END = input("Enter 'end' to close console:\n")

    @staticmethod
    def check_stage1_histories_available() -> None:
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        BinanceSocket._DEBUG = False
        interval = {
            Map.starttime: 1634515200,  # October 18, 2021 0:00:00
            Map.endtime: 1651363200	    # May 1, 2022 0:00:00
        }
        Config.update(Config.FAKE_API_START_END_TIME, interval)
        broker = Draft.get_broker()
        broker_name = broker.__class__.__name__
        pairs = MarketPrice.history_pairs(broker_name, active_path=False)
        period = max(MarketPrice.history_periods(broker_name))
        n_period = broker.get_max_n_period()
        params = {
            Map.broker: broker,
            Map.pair: None,
            Map.period: period,
            'n_period': n_period
        }
        i = 1
        n_pair = len(pairs)
        for pair in pairs:
            print(_MF.prefix() + f"[{i}/{n_pair}] {pair.__str__().upper()}")
            i += 1
            params[Map.pair] = pair
            _MF.catch_exception(MarketPrice.marketprice,
                                'draft', repport=True, **params)
            BinanceFakeAPI.reset()
        Config.update(Config.STAGE_MODE, old_stage)

    @staticmethod
    def get_stage1_history_dates() -> dict:
        dates = {
            '13_14_February_2021': {
                Map.start:1613227500,
                Map.end:1613313900
                },
            '21_May_2021': {
                Map.start:1621555200,
                Map.end:1621641600
                },
            'May_2021': {
                Map.start:  1619827200,
                Map.end:    1622505600
                },
            'February_2021': {
                Map.start:1612137600,
                Map.end:1614556800
                },
            'June_2021': {
                Map.start:1622505600,
                Map.end:1625097600
                },
            'January_2021_January_2022': {
                Map.start:1609459200,
                Map.end:1640995200
                },
            'January_2022_January_2023': {
                Map.start:  1640995200,
                Map.end:    1672531200
                },
            'May_to_July_2022': {
                Map.start:1651363200,
                Map.end:1656633600
                },
            'January_2021_January_2023': {
                Map.start:1609459200,
                Map.end:1672531200
                },
            '11_July_2022': {
                Map.start:1657497600,
                Map.end:1657584000
                },
            '15_July_2022': {
                Map.start:1657843200,
                Map.end:1657929600
                },
            '17_July_2022': {
                Map.start:1658016000,
                Map.end:1658102400
                },
            '30_June_2021': {
                Map.start:  1625011200,
                Map.end:    1625097600
                },
            '01_23_January_2023': {
                Map.start:  1672531200,
                Map.end:    1674432000
                },
            '12_20_February_2023': {
                Map.start:  1676160000,
                Map.end:    1676851200
                },
            'January_2021_March_2023': {
                Map.start:  1609459200,
                Map.end:    1677628800
                },
            'January_2023_March_2023': {
                Map.start:  1672531200,
                Map.end:    1677628800
                },
            'January_2023_April_2023': {
                Map.start:  1672531200,
                Map.end:    1680307200
                },
            '19_February_2023': {
                Map.start:  1676764800,
                Map.end:    1676851200
                },
            '01_March_2021_12_May_2021': {
                Map.start:  1614556800,
                Map.end:    1620777600
                },
            '2023-04-02_12.03.31_Solomon-v4.1': {
                Map.start:  1680437011,
                Map.end:    1680825600
                },
            'January_2021_10_April_2023': {
                Map.start:  1609459200,
                Map.end:    1681084800
                },
            'January_2021_july_2023': {
                Map.start:  1609459200,
                Map.end:    1688169600
                },
            'January_2023_10_April_2023': {
                Map.start:  1672531200,
                Map.end:    1681084800
                },
            'January_2023_may_2023': {
                Map.start:  1672531200,
                Map.end:    1682899200
                },
            'January_2023_june_2023': {
                Map.start:  1672531200,
                Map.end:    1685577600
                },
            '20_October_2022_20_November_2022': {
                Map.start:  1666224000,
                Map.end:    1668902400
                },
            'May_2022': {Map.start: 1651363200,Map.end: 1654041600},
            'January_2021_July_2021': {Map.start: 1609459200,Map.end: 1625097600},
            'January_2022_July_2022': {Map.start: 1640995200,Map.end: 1656633600},
            '2023-07-11_17.03.36_Solomon-v5.3.1.11.1': {Map.start: 1689095520,Map.end: 1689260760}
        }
        return dates

    @staticmethod
    def backtest() -> None:
        def buffer_backtest(backtest_params: dict) -> None:
            def get_pair_index(d: pd.DataFrame, pair: Pair) -> int:
                return d.loc[d.loc[:, Map.pair] == pair.__str__()].index[0]

            def read_tested_content() -> pd.DataFrame:
                d = pd.read_csv(project_dir + tested_pairs_file)
                return d

            def no_tested_pairs(tested_content: pd.DataFrame) -> pd.Series:
                return to_test_content.loc[~to_test_content.loc[:, Map.pair].isin(tested_content.loc[:, Map.pair])]

            def wait_end_writting() -> None:
                while FileManager.is_writting():
                    time.sleep(0.001)

            project_dir = FileManager.get_project_directory()
            buffer_path = 'content/storage/Strategy/Icarus/backtest/stock/buffer/'
            to_test_pairs_file = buffer_path + 'pairs.csv'
            tested_pairs_file = buffer_path + 'tested_pairs.csv'
            to_test_content = pd.read_csv(project_dir + to_test_pairs_file)
            # Tested file exist?
            tested_fields = [Map.pair, Map.start, Map.end]
            if tested_pairs_file.split('/')[-1] not in FileManager.get_files(buffer_path):
                FileManager.write_csv(tested_pairs_file, tested_fields, [
                ], overwrite=True, make_dir=True)
                wait_end_writting()
            # Test
            tested_content = read_tested_content()
            loop_starttime = _MF.date_to_unix(
                tested_content.loc[tested_content.index[0], Map.start]) if tested_content.shape[0] > 0 else _MF.get_timestamp()
            while no_tested_pairs(tested_content).shape[0] > 0:
                test_start_time = _MF.get_timestamp()
                # Test
                no_test_pairs_str = no_tested_pairs(tested_content)
                next_pair_str = no_test_pairs_str.iloc[0, 0]
                next_pair = Pair(next_pair_str)
                print(_MF.loop_progression(
                    loop_starttime, tested_content.shape[0]+1, to_test_content.shape[0], next_pair.__str__().upper()))
                # -- Mark pair as selected
                pair_index = tested_content.shape[0]
                tested_content.loc[pair_index, Map.pair] = next_pair_str
                tested_content.loc[pair_index, Map.start] = _MF.unix_to_date(
                    test_start_time)
                tested_content.to_csv(
                    project_dir + tested_pairs_file, index=False)
                # -- Test selected pair
                backtest_params['pairs'] = [next_pair]
                class_ref.backtest(**backtest_params)
                # Repport results
                tested_content = read_tested_content()
                pair_index = get_pair_index(tested_content, next_pair)
                tested_content.loc[pair_index, Map.end] = _MF.unix_to_date(
                    _MF.get_timestamp())
                tested_content.to_csv(
                    project_dir + tested_pairs_file, index=False)
                tested_content = read_tested_content()
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        broker = Draft.get_broker()
        view = Draft.get_view()
        # Strategy
        stgs = Strategy.list_strategies()
        class_ref = eval(stgs[view.menu("Chose the Strategy to use:", stgs)])
        # Dates
        dates = Draft.get_stage1_history_dates()
        date_keys = list(dates.keys())
        date = dates[date_keys[view.menu("Choose your date:", date_keys)]]
        starttime = date[Map.start]
        endtime = date[Map.end]
        periods = [60*15]
        # periods = [60*5]
        # Run mode
        run_modes = ['One pair', 'Buffer pairs']
        run_mode = run_modes[view.menu("Choose your run mode:", run_modes)]
        # Pair
        price_types = [Map.open, Map.mean, Map.close]
        backtest_params = {
            Map.broker: broker,
            Map.starttime: starttime,
            Map.endtime: endtime,
            'periods': periods,
            'pairs': None,
            'buy_type': price_types[view.menu("Choose the price type when buying:", price_types)],
            'sell_type': price_types[view.menu("Choose the price type when selling:", price_types)]
        }
        if run_mode == run_modes[0]:
            pairs_str = ['BCH/USDT', 'COCOS/USDT', 'ROSE/USDT', 'TROY/USDT',
                         'TOMO/USDT', 'BAT/USDT', 'BNB/USDT', 'BTC/USDT', 'ATM/USDT']
            pairs = [Pair(pairs_str[view.menu("Enter Pair:", pairs_str)])]
            backtest_params['pairs'] = pairs
            class_ref.backtest(**backtest_params)
        elif run_mode == run_modes[1]:
            buffer_backtest(backtest_params)
        else:
            raise ValueError(f"Unknown run mode '{run_mode}'")
        Config.update(Config.STAGE_MODE, old_stage)

    @classmethod
    def backtest2(cls, strategy_class: Strategy = None, pair: Pair = None, starttime: int = None, endtime: int = None) -> bool:
        # Config
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        BinanceFakeAPI.reset()
        BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        Config.print_session_config()
        broker = Draft.get_broker()
        view = Draft.get_view()
        # Strategy
        strategy_class = cls.input_strategy_class() if strategy_class is None else strategy_class
        # Date
        starttime, endtime = cls.input_backtest_dates() if (starttime is None) or (endtime is None) else (starttime, endtime)
        # pair = Pair('BCH/USDT')
        pair = Pair(view.input('Enter the Pair to backtest:')) if pair is None else pair
        cls.print_backtest_config(broker, strategy_class, pair, starttime, endtime)
        strategy_class.backtest(broker, pair, starttime, endtime)
        # sleep_time = 10
        # _MF.output(f"Backtesting '{pair.__str__().upper()}' for '{sleep_time}'sec.")
        # _MF.sleep(sleep_time)
        # End
        Config.update(Config.STAGE_MODE, old_stage)
        return True

    @classmethod
    def loop_backtest2(cls) -> None:
        def load_df(absolut_file_path: str) -> pd.DataFrame:
            df = pd.read_csv(absolut_file_path)
            df.set_index(Map.pair, drop=False, inplace=True)
            return df
        def print_df(absolut_file_path: str, df: pd.DataFrame) -> None:
            df.to_csv(absolut_file_path, index=False)
        def update_session_id(pair: Pair) -> None:
            session_id = Config.get(Config.SESSION_ID)
            right_asset_str = pair.get_right().__str__().upper()
            new_str = f'-{pair.format(Pair.FORMAT_UNDERSCORE).upper()}'
            regex_match = f'.+-\w+_{right_asset_str}'
            if _MF.regex_match(regex_match, session_id):
                regex_replace = fr'-\w+_{right_asset_str}$'
                new_session_id = _MF.regex_replace(session_id, regex_replace, new_str)
            else:
                new_session_id = session_id + new_str
            Config.update_session_id(new_session_id)
        # Vars
        dir_actual_session = Config.get(Config.DIR_ACTUAL_SESSION)
        file_path = dir_actual_session + 'pairs_backtest_loop.csv'
        absolut_file_path = FileManager.get_project_directory() + file_path
        # Input
        strategy_class = cls.input_strategy_class()
        starttime, endtime = cls.input_backtest_dates()
        #
        pair_df = load_df(absolut_file_path)
        pair_str = pair_df[pd.isna(pair_df[Map.start])][Map.pair].iloc[0]
        pair_df.loc[pair_str, Map.start] = _MF.unix_to_date(_MF.get_timestamp())
        print_df(absolut_file_path, pair_df)
        # Loop
        wait_write_time = 60*5
        while True:
            update_session_id(Pair(pair_str))
            # Loop message
            output_starttime = _MF.date_to_unix(pair_df.loc[pair_df.index[0], Map.start])
            n_turn = pair_df.shape[0]
            turn = pair_df[Map.pair].to_list().index(pair_str) + 1
            output = _MF.loop_progression(output_starttime, turn, n_turn, f"DRAFT LOOP on '{pair_str.upper()}'")
            _MF.output(output)
            # Backtest
            # cls.backtest2(strategy_class=strategy_class, pair=Pair(pair_str), starttime=starttime, endtime=endtime)
            is_success = _MF.catch_exception(cls.backtest2, cls.__name__, **dict(strategy_class=strategy_class, pair=Pair(pair_str), starttime=starttime, endtime=endtime))
            # Report backtest
            pair_df = load_df(absolut_file_path)
            if is_success == True:
                pair_df.loc[pair_str, Map.end] = _MF.unix_to_date(_MF.get_timestamp())
                print_df(absolut_file_path, pair_df)
            untreated = pair_df[pd.isna(pair_df[Map.start])]
            #
            if untreated.shape[0] == 0:
                break
            else:
                view.output(f"Waiting '{wait_write_time/60}'min. for writting thread to end...", richs=[view.C_YELLOW])
                _MF.wait_while(FileManager.is_writting, False, wait_write_time, Exception(f"Time to wait end of writting is out"))
                view.output(f"Writting thread is clear!", is_success=True)
                # Reload
                pair_df = load_df(absolut_file_path)
                pair_str = untreated[Map.pair].iloc[0]
                pair_df.loc[pair_str, Map.start] = _MF.unix_to_date(_MF.get_timestamp())
                print_df(absolut_file_path, pair_df)

    @classmethod
    def input_strategy_class(cls) -> Strategy:
        def get_strategy_class(strategy_str: str) -> Strategy:
            exec(_MF.get_import(strategy_str))
            return eval(strategy_str)
        view = Draft.get_view()
        strategies = Strategy.list_strategies()
        strategy_str = strategies[view.menu('Select the Strategy to backtest:', strategies)]
        strategy_class = get_strategy_class(strategy_str)
        return strategy_class

    @classmethod
    def input_backtest_dates(cls) -> tuple:
        view = Draft.get_view()
        dates = Draft.get_stage1_history_dates()
        date_keys = list(dates.keys())
        date_key = date_keys[view.menu("Choose your date:", date_keys)]
        date = dates[date_key]
        starttime = date[Map.start]
        endtime = date[Map.end]
        return starttime, endtime

    @classmethod
    def print_backtest_config(cls, broker: Broker, strategy_class: Strategy, pair: Pair, starttime: int, endtime: int) -> None:
        conf_file_path = Config.get(Config.DIR_SESSION_CONFIG) + f'backtest_conf.json'
        backtest_conf = {
            Map.id:         Config.get(Config.SESSION_ID),
            Map.broker:     broker.__class__.__name__,
            Map.strategy:   strategy_class.__name__,
            Map.pair:       pair.__str__(),
            Map.start:      starttime,
            Map.end:        endtime,
            Map.date:       f'{_MF.unix_to_date(starttime)} => {_MF.unix_to_date(endtime)}'
            }
        backtest_conf_json = _MF.json_encode(backtest_conf)
        FileManager.write(conf_file_path, backtest_conf_json, overwrite=False)

    @staticmethod
    def analyse_backtest() -> None:
        def print_row(rows: List[dict]) -> None:
            fields = list(rows[0].keys())
            FileManager.write_csv(print_path, fields, rows,
                                  overwrite=False, make_dir=True)

        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        BinanceSocket._DEBUG = False
        view = Draft.get_view()
        dates = Draft.get_stage1_history_dates()
        date_keys = list(dates.keys())
        selected_date = date_keys[view.menu("Choose your date:", date_keys)]
        Config.update(Config.FAKE_API_START_END_TIME, dates[selected_date])
        # Files
        test_id = input('Enter the backtest ID:\n')
        read_file = f'{test_id}_backtest.csv'
        read_file_name = read_file.replace('.csv', '')
        file_path = f'/Users/israelmeiresonne/MY-MAC/ROQUETS/companies/apollo21/dev/apollo21/dev/apollo21/project/content/storage/Strategy/Icarus/backtest/tests/{test_id}/datas/'
        file_date = _MF.unix_to_date(
            _MF.get_timestamp(), _MF.FORMAT_D_H_M_S_FOR_FILE)
        print_path = f"content/storage/Strategy/Icarus/backtest/tests/{test_id}/datas/analyses/{file_date}_{read_file_name}_indicator_metrics.csv"
        df = pd.read_csv(file_path + read_file)
        df = df.set_index(Map.id)
        # Variables
        vars_map = Map()
        broker = Draft.get_broker()
        pair = Pair(df.iloc[1, 1])
        n_period = TraderClass.get_marketprice_n_period()
        min_period = 60
        period = 60*15
        big_period = Icarus.MARKETPRICE_BUY_BIG_PERIOD
        little_period = Icarus.MARKETPRICE_BUY_LITTLE_PERIOD
        trade_ids = list(df.index)
        min_period_str = BinanceAPI.convert_interval(min_period)
        local_period_str = BinanceAPI.convert_interval(period)
        # MarketPrice
        market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: period,
            'n_period': n_period
        }
        big_market_params = market_params.copy()
        big_market_params[Map.period] = big_period
        little_market_params = market_params.copy()
        little_market_params[Map.period] = little_period
        min_market_params = market_params.copy()
        min_market_params[Map.period] = min_period
        broker.add_streams([
            broker.generate_stream(
                Map({Map.pair: pair, Map.period: min_period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: period})),
            broker.generate_stream(
                Map({Map.pair: pair, Map.period: big_period})),
            broker.generate_stream(
                Map({Map.pair: pair, Map.period: little_period}))
        ])
        #
        starttime = _MF.get_timestamp()
        turn = 0
        n_turn = len(trade_ids)
        for trade_id in trade_ids:
            # Loop
            turn += 1
            print(_MF.loop_progression(starttime, turn, n_turn, trade_id))
            # Trade
            trade_index = int(trade_id.split('_')[2])
            Bot.update_trade_index(trade_index)
            # MarketPrice
            min_marketprice = _MF.catch_exception(
                MarketPrice.marketprice, 'draft', repport=True, **min_market_params)
            local_marketprice = _MF.catch_exception(
                MarketPrice.marketprice, 'draft', repport=True, **market_params)
            big_marketprice = _MF.catch_exception(
                MarketPrice.marketprice, 'draft', repport=True, **big_market_params)
            little_marketprice = _MF.catch_exception(
                MarketPrice.marketprice, 'draft', repport=True, **little_market_params)
            row = {
                **Analyse.test_metrics(vars_map, min_marketprice),
                **Analyse.test_metrics(vars_map, little_marketprice),
                **Analyse.test_metrics(vars_map, local_marketprice),
                **Analyse.test_metrics(vars_map, big_marketprice)
            }
            vars_map.sort()
            row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                f'{min_period_str}_time': _MF.unix_to_date(min_marketprice.get_time()),
                f'{local_period_str}_time': _MF.unix_to_date(local_marketprice.get_time()),
                Map.id: trade_id,
                **row,
                **vars_map.get_map()
            }
            print_row([row])
        # End
        Config.update(Config.STAGE_MODE, old_stage)

    @staticmethod
    def download_marketprice(broker: Broker, pair: Pair, periods: List[int], endtime: int, starttime: int) -> Dict[int, pd.DataFrame]:
        marketprices_dict = {}
        n_prev_period = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        for period in periods:
            new_starttime = starttime - period * n_prev_period
            marketprices_df = MarketPrice.marketprices(
                broker, pair, period, endtime, new_starttime)
            marketprices_dict[period] = marketprices_df
        return marketprices_dict

    @staticmethod
    def ask_session_id() -> Tuple[str, str]:
        view = Draft.get_view()
        path_session_dir = view.input(
            "Enter the path to the Session to load (since project directory):")
        path_session_dir = path_session_dir if path_session_dir[-1] == '/' else (
            path_session_dir + '/')
        FileManager.get_files(path_session_dir)
        load_session_id = path_session_dir.split('/')[-2]
        print(_MF.prefix(), f"session's ID: {load_session_id}")
        return path_session_dir, load_session_id

    @staticmethod
    def stage2_analyse_file_paths(path_session_dir: str) -> Dict[str, str]:
        load_session_id = path_session_dir.split('/')[-2]
        path_dir_completed_order = path_session_dir + "analyse/orders/"
        path_completed_order_file = path_dir_completed_order + \
            f"{load_session_id}_completed_orders.csv"
        path_completed_trade_file = path_dir_completed_order + \
            f"{load_session_id}_completed_trades.csv"
        path_trades_metrics_file = path_dir_completed_order + \
            f"{load_session_id}_trades_metrics.csv"
        path_rated_metrics_file = path_dir_completed_order + \
            f"{load_session_id}_rated_metrics.csv"
        return {
            Map.order: path_completed_order_file,
            Map.trade: path_completed_trade_file,
            Map.metric: path_trades_metrics_file,
            Map.rate: path_rated_metrics_file
        }

    @staticmethod
    def load_orders() -> pd.DataFrame:
        order_file_path = Config.get(Config.DIR_SAVE_ORDER_ACTIONS)
        order_dir = FileManager.path_to_dir(order_file_path)
        GM_str_pairs = GM['pair'].drop_duplicates()
        pairs = [Pair(GM_str_pair) for GM_str_pair in GM_str_pairs]
        order_file_paths = [order_file_path.replace('$pair', pair.format(
            Pair.FORMAT_UNDERSCORE).upper()) for pair in pairs]
        existing_files = FileManager.get_files(order_dir)
        existing_order_file_paths = [
            order_file_path for order_file_path in order_file_paths if order_file_path.split('/')[-1] in existing_files]
        ORDERS = _MF.concat_files(existing_order_file_paths)

    @staticmethod
    def format_orders() -> None:
        def new_trade(pair: Pair, trade_id: str, trade_order: int, row: pd.DataFrame) -> pd.DataFrame:
            row_index = row.index[0]
            fees_dict_str = row.loc[row_index, '_Order__fee']
            left_str_fees = fees_dict_str.split(
                ',')[0].split(': ')[1].split(' ')
            fee_left = Price(left_str_fees[1], left_str_fees[0])
            trade = pd.DataFrame([{
                'save_time':            row.loc[row_index, 'time'],
                'pair':                 row.loc[row_index, '_Transaction__pair'],
                'trade_id':             trade_id,
                'trade_order':          trade_order,
                'order_id':             row.loc[row_index, '_Transaction__id'],
                'broker_id':            row.loc[row_index, '_Order__broker_id'],
                'set_time':             row.loc[row_index, '_Transaction__settime'],
                'set_date':             _MF.unix_to_date(row.loc[row_index, '_Transaction__settime']/1000, form=_MF.FORMAT_D_H_M_S_MS),
                'execution_time':       row.loc[row_index, '_Order__execution_time'],
                'execution_date':       _MF.unix_to_date(row.loc[row_index, '_Order__execution_time']/1000, form=_MF.FORMAT_D_H_M_S_MS),
                'Move':                 row.loc[row_index, '_Order__move'],
                'order_type':           row.loc[row_index, '_Order__type'],
                'status':               row.loc[row_index, '_Order__status'],
                'asked_quantity':       row.loc[row_index, '_quantity'],
                'asked_amount':         row.loc[row_index, '_Order__amount'],
                'limit_price':          row.loc[row_index, '_limit'],
                'stop_price':           row.loc[row_index, '_stop'],
                'execution_price':      row.loc[row_index, '_Order__execution_price'],
                'executed_quantity':    row.loc[row_index, '_Order__executed_quantity'],
                'executed_amount':      row.loc[row_index, '_Order__executed_amount'],
                'fee_left':             fee_left,
                'fee_right':            row.loc[row_index, '_Transaction__transaction_fee']
            }])
            return trade

        COMPLETED_ORDERS = ORDERS[ORDERS['_Order__status']
                                  == Order.STATUS_COMPLETED]
        order_str_pairs = COMPLETED_ORDERS['_Transaction__pair'].drop_duplicates(
        )
        order_pairs = [Pair(order_str_pair)
                       for order_str_pair in order_str_pairs]
        CLEAN_COMPLETED_ORDERS = pd.DataFrame()
        for order_pair in order_pairs:
            pair_COMPLETED_ORDERS = COMPLETED_ORDERS[COMPLETED_ORDERS['_Transaction__pair'] == order_pair.__str__(
            )]
            pair_COMPLETED_ORDERS.sort_values(
                by=['_Order__execution_time'], inplace=True)
            order_ids = pair_COMPLETED_ORDERS['_Transaction__id']
            i = 0
            n_order = pair_COMPLETED_ORDERS.shape[0]
            target_trade_id = '$#trade'
            while i < n_order:
                order_id = order_ids.iloc[i]
                order_row = pair_COMPLETED_ORDERS[pair_COMPLETED_ORDERS['_Transaction__id'] == order_id]
                if (i+1) % 2 == 1:
                    trade_id = order_id
                    trade_order = 0
                elif (i+1) % 2 == 0:
                    trade_order += 1
                else:
                    raise Exception(
                        f"Unkwon case: i='{i}', modulo='{(i+1)%2}'")
                trade = new_trade(order_pair, trade_id, trade_order, order_row)
                CLEAN_COMPLETED_ORDERS = CLEAN_COMPLETED_ORDERS.append(
                    trade, ignore_index=True)
                i += 1

        order_path_from_project = DIR_SESSION_ANALYSE + f'orders/'
        FileManager.make_directory(order_path_from_project)
        order_file_path = PROJECT_DIR + order_path_from_project + \
            f'{SESSION_ID}_completed_orders.csv'
        CLEAN_COMPLETED_ORDERS.to_csv(order_file_path, index=False)

    @staticmethod
    def format_orders_to_trades() -> None:
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)

        def print_row(file_path: str, rows: List[dict], overwrite) -> None:
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows,
                                  overwrite=overwrite, make_dir=False)

        def str_to_price(str_price: str) -> Price:
            str_asset, value = str_price.split(' ')
            return Price(float(value), str_asset)

        def extract_times(orders: pd.DataFrame, trade_ids: pd.Series) -> Tuple[int, int]:
            first_execution_time = orders.loc[trade_ids[0], 'execution_time']
            starttime = int(_MF.round_time(
                first_execution_time, _1min_period)/1000)
            last_trade = orders[orders['trade_id'] == trade_ids[-1]]
            last_execution_time = last_trade.loc[last_trade.index[-1],
                                                 'execution_time']
            endtime = int(_MF.round_time(
                last_execution_time, _1min_period)/1000)
            return starttime, endtime

        def new_backtest_row(pair_backtests: pd.DataFrame, buy_order: pd.Series, sell_order: pd.Series, datas: dict) -> pd.DataFrame:
            backtest_row = {}
            backtest_row['date'] = _MF.unix_to_date(_MF.get_timestamp())
            backtest_row['pair'] = buy_order['pair']
            backtest_row['trade_id'] = buy_order['trade_id']
            backtest_row['start'] = datas[Map.start]
            backtest_row['end'] = datas[Map.end]
            backtest_row['buy_order_id'] = buy_order.name
            backtest_row['buy_time'] = buy_order['execution_time']
            backtest_row['buy_date'] = _MF.unix_to_date(
                int(buy_order['execution_time']/1000))
            backtest_row['buy_price'] = float(
                buy_order['execution_price'].split(' ')[-1])
            backtest_row['sell_order_id'] = sell_order.name
            backtest_row['sell_time'] = sell_order['execution_time']
            backtest_row['sell_date'] = _MF.unix_to_date(
                int(sell_order['execution_time']/1000))
            backtest_row['sell_price'] = float(
                sell_order['execution_price'].split(' ')[-1])
            backtest_row['roi'] = _MF.progress_rate(
                backtest_row['sell_price'], backtest_row['buy_price']) - datas[Map.fee]
            backtest_row['roi_losses'] = backtest_row['roi'] if backtest_row['roi'] < 0 else None
            backtest_row['roi_wins'] = backtest_row['roi'] if backtest_row['roi'] > 0 else None
            backtest_row['roi_neutrals'] = backtest_row['roi'] if backtest_row['roi'] == 0 else None
            backtest_row['min_roi_position'] = _MF.progress_rate(
                datas[Map.minimum], backtest_row['buy_price'])
            backtest_row['max_roi_position'] = _MF.progress_rate(
                datas[Map.maximum], backtest_row['buy_price'])
            backtest_row['min_roi'] = None
            backtest_row['mean_roi'] = None
            backtest_row['max_roi'] = None
            backtest_row['mean_win_roi'] = None
            backtest_row['mean_loss_roi'] = None
            backtest_row['sum'] = (pair_backtests['roi'].sum(
            ) + backtest_row['roi']) if pair_backtests is not None else backtest_row['roi']
            backtest_row['min_sum_roi'] = None
            backtest_row['max_sum_roi'] = None
            backtest_row['final_roi'] = None
            backtest_row['fee'] = datas[Map.fee]
            backtest_row['sum_fee'] = (pair_backtests['fee'].sum(
            ) + backtest_row['fee']) if pair_backtests is not None else backtest_row['fee']
            backtest_row['sum_roi_no_fee'] = ((pair_backtests['roi'] + pair_backtests['fee']).sum() + (
                backtest_row['roi'] + backtest_row['fee']))if pair_backtests is not None else (backtest_row['roi'] + backtest_row['fee'])
            backtest_row['start_price'] = datas['start_price']
            backtest_row['end_price'] = datas['end_price']
            backtest_row['higher_price'] = datas['higher_price']
            backtest_row['market_performence'] = datas['market_performence']
            backtest_row['max_profit'] = datas['max_profit']
            backtest_row['n_win'] = None
            backtest_row['win_rate'] = None
            backtest_row['n_loss'] = None
            backtest_row['loss_rate'] = None
            return pd.DataFrame([backtest_row])

        def extract_backtest_datas(_1min_marketprices: pd.DataFrame, buy_order: pd.Series, sell_order: pd.Series) -> dict:
            datas = {}
            # Trade
            buy_time = buy_order['execution_time']
            sell_time = sell_order['execution_time']
            position_1min_marketprices = _1min_marketprices[(
                _1min_marketprices.iloc[:, 0] > buy_time) & (_1min_marketprices.iloc[:, 0] < sell_time)]
            # Fee
            buy_fee = str_to_price(
                buy_order['fee_right'])/str_to_price(buy_order['executed_amount'])
            sell_fee = str_to_price(
                sell_order['fee_left'])/str_to_price(sell_order['executed_quantity'])
            # Global
            global_1min_marketprices = _1min_marketprices[(_1min_marketprices.iloc[:, 0] > first_all_order_starttime) & (
                _1min_marketprices.iloc[:, 0] < last_all_order_endtime)]
            # Datas
            datas[Map.start] = _MF.unix_to_date(first_all_order_starttime/1000)
            datas[Map.end] = _MF.unix_to_date(last_all_order_endtime/1000)
            datas[Map.fee] = sell_fee + buy_fee
            datas[Map.minimum] = position_1min_marketprices.iloc[:, 3].min()
            datas[Map.maximum] = position_1min_marketprices.iloc[:, 2].max()
            datas['start_price'] = global_1min_marketprices.iloc[0, 4]
            datas['end_price'] = global_1min_marketprices.iloc[-1, 4]
            datas['higher_price'] = global_1min_marketprices.iloc[:, 2].max()
            datas['market_performence'] = _MF.progress_rate(
                datas['end_price'], datas['start_price'])
            datas['max_profit'] = _MF.progress_rate(
                datas['higher_price'], datas['start_price'])
            return datas

        def complete_backtest(backtests: pd.DataFrame) -> None:
            backtests.loc[:, 'min_roi'] = backtests.loc[:, 'roi'].min()
            backtests.loc[:, 'mean_roi'] = backtests.loc[:, 'roi'].mean()
            backtests.loc[:, 'max_roi'] = backtests.loc[:, 'roi'].max()
            backtests.loc[:, 'mean_win_roi'] = backtests.loc[:,
                                                             'roi_wins'].mean()
            backtests.loc[:, 'mean_loss_roi'] = backtests.loc[:,
                                                              'roi_losses'].mean()
            backtests.loc[:, 'min_sum_roi'] = backtests.loc[:, 'sum'].min()
            backtests.loc[:, 'max_sum_roi'] = backtests.loc[:, 'sum'].max()
            backtests.loc[:, 'final_roi'] = backtests.loc[:, 'roi'].sum()
            backtests.loc[:, 'n_win'] = backtests.loc[:,
                                                      'roi_wins'].dropna().shape[0]
            backtests.loc[:, 'win_rate'] = backtests.loc[backtests.index[0],
                                                         'n_win']/backtests.shape[0]
            backtests.loc[:, 'n_loss'] = backtests.loc[:,
                                                       'roi_losses'].dropna().shape[0]
            backtests.loc[:, 'loss_rate'] = backtests.loc[backtests.index[0],
                                                          'n_loss']/backtests.shape[0]

        # Default Variables
        broker = Draft.get_broker()
        # periods = [60, 5*60, 15*60, 60*60, 6*60*60]
        _1min_period = 60
        # Paths
        path_session_dir, load_session_id = Draft.ask_session_id()
        project_dir = FileManager.get_project_directory()
        analyse_paths = Draft.stage2_analyse_file_paths(path_session_dir)
        path_completed_order_file = analyse_paths[Map.order]
        path_completed_trade_file = analyse_paths[Map.trade]
        # Load Completed Orders
        completed_orders = pd.read_csv(
            project_dir + path_completed_order_file, index_col='order_id').sort_values(['execution_time'])
        str_pairs = completed_orders['pair'].drop_duplicates()
        pairs = [Pair(str_pair) for str_pair in str_pairs]
        starttime, endtime = extract_times(
            completed_orders, completed_orders['trade_id'].drop_duplicates())
        first_all_order_starttime = _MF.round_time(
            completed_orders['execution_time'].iloc[0]/1000, _1min_period)*1000
        last_all_order_endtime = _MF.round_time(
            completed_orders['execution_time'].iloc[-1]/1000, _1min_period)*1000
        # Load Completed Trades
        loaded_completed_trades = _MF.catch_exception(
            pd.read_csv, 'Draft', **{'filepath_or_buffer': project_dir + path_completed_trade_file})
        treated_trade_ids = loaded_completed_trades['trade_id'] if loaded_completed_trades is not None else [
        ]
        # Loop Trades
        backtests = None
        # dict[pair.__str__()][period{int}]:    pd.DataFrame
        download_marketprices = {}
        n_print = 0
        loop_starttime = _MF.get_timestamp()
        n_turn = len(pairs)
        turn = 1
        for pair in pairs:
            overwrite_completed_trade = n_print == 0
            print(_MF.loop_progression(loop_starttime,
                  turn, n_turn, pair.__str__().upper()))
            turn += 1
            pair_completed_orders = completed_orders[completed_orders['pair'] == pair.__str__()].sort_values([
                'execution_time'])
            trade_ids = pair_completed_orders['trade_id'].drop_duplicates()
            not_treated_trade_ids = trade_ids[~trade_ids.isin(
                treated_trade_ids)]
            completed_trade_ids = not_treated_trade_ids if pair_completed_orders.shape[
                0] % 2 == 0 else not_treated_trade_ids[:-1]
            pair_backtests = None if loaded_completed_trades is None else loaded_completed_trades[
                loaded_completed_trades['pair'] == pair.__str__()]
            if completed_trade_ids.shape[0] > 0:
                marketprices_dict = Draft.download_marketprice(
                    broker, pair, [_1min_period], endtime, starttime)
                download_marketprices[pair.__str__()] = marketprices_dict
                i = 0
                while i < completed_trade_ids.shape[0]:
                    buy_sell_orders = pair_completed_orders[pair_completed_orders['trade_id']
                                                            == completed_trade_ids[i]]
                    buy_order = buy_sell_orders.iloc[0]
                    sell_order = buy_sell_orders.iloc[1]
                    backtest_datas = extract_backtest_datas(
                        marketprices_dict[_1min_period], buy_order, sell_order)
                    backtest_row = new_backtest_row(
                        pair_backtests, buy_order, sell_order, backtest_datas)
                    pair_backtests = backtest_row if pair_backtests is None else pair_backtests.append(
                        backtest_row, ignore_index=True)
                    i += 1
            if (pair_backtests is not None) and (pair_backtests.shape[0] > 0):
                complete_backtest(pair_backtests)
                pair_backtests = pair_backtests.sort_values(
                    ['date', 'buy_time'])
                backtests = pair_backtests if backtests is None else backtests.append(
                    pair_backtests, ignore_index=True)
                print_row(path_completed_trade_file, pair_backtests.replace(
                    {np.nan: None}).to_dict(orient='records'), overwrite=overwrite_completed_trade)
                n_print += 1
        # End
        Config.update(Config.STAGE_MODE, old_stage)

    @staticmethod
    def extract_stage2_metrics(download_marketprices: Map = Map()) -> None:
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)

        def print_row(file_path: str, rows: List[dict], overwrite) -> None:
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows,
                                  overwrite=overwrite, make_dir=False)

        def get_marketprice(pair: Pair, trade: pd.Series, period: int) -> MarketPrice:
            marketprice_df = download_marketprices.get(trade['pair'], period)
            if marketprice_df is None:
                marketprice_dict = Draft.download_marketprice(
                    broker, pair, [period], global_endtime, global_starttime)
                marketprice_df = marketprice_dict[period]
            buy_time = _MF.round_time(trade['buy_time']/1000, period)*1000
            market = marketprice_df[marketprice_df.iloc[:, 0]
                                    <= buy_time].to_numpy().tolist()
            return BinanceMarketPrice(market, BinanceAPI.convert_interval(period), pair)

        def new_metrics(pair_metrics: pd.DataFrame, pair: Pair, trades: pd.DataFrame) -> pd.DataFrame:
            # pair_metrics = None
            for pair_trade_id in trades['trade_id']:
                pair_trade = trades[trades['trade_id']
                                    == pair_trade_id].iloc[0]
                metric_row = {
                    'date': _MF.unix_to_date(_MF.get_timestamp()),
                    'pair': pair.__str__(),
                    'trade_id': pair_trade_id,
                    'buy_date': pair_trade['buy_date'],
                    'marketprice_date': _MF.unix_to_date(get_marketprice(pair, pair_trade, _1min_period).get_time())
                }
                vars_metric_row = Map()
                for period in periods:
                    marketprice = get_marketprice(pair, pair_trade, period)
                    metric_row = {
                        **metric_row,
                        **Analyse.test_metrics(vars_metric_row, marketprice)
                    }
                vars_metric_row.sort()
                metric_row = {
                    **metric_row,
                    **vars_metric_row.get_map()
                }
                pair_metrics = pd.DataFrame([metric_row]) if pair_metrics is None else pair_metrics.append(
                    metric_row, ignore_index=True)
            return pair_metrics

        # Default Vars
        broker = Draft.get_broker()
        periods = [60, 5*60, 15*60, 60*60, 6*60*60]
        _1min_period = 60
        # Paths
        path_session_dir, load_session_id = Draft.ask_session_id()
        project_dir = FileManager.get_project_directory()
        analyse_paths = Draft.stage2_analyse_file_paths(path_session_dir)
        path_completed_trade_file = analyse_paths[Map.trade]
        path_trades_metrics_file = analyse_paths[Map.metric]
        # Trades
        completed_trades = pd.read_csv(
            project_dir + path_completed_trade_file).sort_values(['buy_time'])
        str_pairs = completed_trades['pair'].drop_duplicates()
        pairs = [Pair(str_pair) for str_pair in str_pairs]
        global_starttime = int(completed_trades['buy_time'].min()/1000)
        global_endtime = int(completed_trades['sell_time'].max()/1000)
        # Metrics
        load_metrics = _MF.catch_exception(
            pd.read_csv, 'Draft', **{'filepath_or_buffer': project_dir + path_trades_metrics_file})
        is_metrics_loaded = load_metrics is not None
        load_trade_ids = load_metrics['trade_id'] if is_metrics_loaded else []
        # Loop
        metrics = None
        loop_starttime = _MF.get_timestamp()
        n_turn = len(pairs)
        turn = 0
        for pair in pairs:
            print(_MF.loop_progression(loop_starttime,
                  turn, n_turn, pair.__str__().upper()))
            turn += 1
            load_pair_metrics = load_metrics[load_metrics['pair'] == pair.__str__(
            )] if is_metrics_loaded else None
            pair_completed_trades = completed_trades[(completed_trades['pair'] == pair.__str__()) & (
                ~completed_trades['trade_id'].isin(load_trade_ids))]
            if pair_completed_trades.shape[0] > 0:
                pair_metrics = new_metrics(
                    load_pair_metrics, pair, pair_completed_trades)
            else:
                pair_metrics = load_pair_metrics
            pair_metrics = pair_metrics.sort_values(['date', 'buy_date'])
            metrics = pair_metrics if metrics is None else metrics.append(
                pair_metrics, ignore_index=True)
            print_row(path_trades_metrics_file, pair_metrics.replace(
                {np.nan: None}).to_dict('records'), overwrite=(pair == pairs[0]))
        # End
        Config.update(Config.STAGE_MODE, old_stage)

    @staticmethod
    def extract_stage2_rated_metrics() -> None:
        def print_rows(file_path: str, rows: List[dict], overwrite: bool) -> None:
            fields = list(rows[0].keys())
            FileManager.write_csv(file_path, fields, rows,
                                  overwrite=overwrite, make_dir=False)

        def new_rated_metric(collumn_name: str) -> pd.DataFrame:
            rated_metric_row = {}
            rated_metric_row['date'] = _MF.unix_to_date(_MF.get_timestamp())
            rated_metric_row['metric'] = collumn_name
            rated_metric_row['order_metric'] = metric_names.index(collumn_name)
            rated_metric_row['total_win'] = completed_trades[completed_trades['roi'] > 0].shape[0]
            rated_metric_row['total_loss'] = completed_trades[completed_trades['roi'] < 0].shape[0]

            rated_metric_row['n_win(True)'] = metrics[(
                metrics[collumn_name] == True) & (completed_trades['roi'] > 0)].shape[0]
            rated_metric_row['win_rate_on_total(True)'] = rated_metric_row['n_win(True)'] / \
                metrics.shape[0]
            rated_metric_row['win_rate_on_win(True)'] = rated_metric_row['n_win(True)'] / \
                rated_metric_row['total_win']

            rated_metric_row['n_win(False)'] = metrics[(
                metrics[collumn_name] == False) & (completed_trades['roi'] > 0)].shape[0]
            rated_metric_row['win_rate_on_total(False)'] = rated_metric_row['n_win(False)'] / \
                metrics.shape[0]
            rated_metric_row['win_rate_on_win(False)'] = rated_metric_row['n_win(False)'] / \
                rated_metric_row['total_win']

            rated_metric_row['n_loss(True)'] = metrics[(
                metrics[collumn_name] == True) & (completed_trades['roi'] < 0)].shape[0]
            rated_metric_row['loss_rate_on_total(True)'] = rated_metric_row['n_loss(True)'] / \
                metrics.shape[0]
            rated_metric_row['loss_rate_on_loss(True)'] = rated_metric_row['n_loss(True)'] / \
                rated_metric_row['total_loss']

            rated_metric_row['n_loss(False)'] = metrics[(
                metrics[collumn_name] == False) & (completed_trades['roi'] < 0)].shape[0]
            rated_metric_row['loss_rate_on_total(False)'] = rated_metric_row['n_loss(False)'] / \
                metrics.shape[0]
            rated_metric_row['loss_rate_on_loss(False)'] = rated_metric_row['n_loss(False)'] / \
                rated_metric_row['total_loss']
            return pd.DataFrame([rated_metric_row])

        # Paths
        path_session_dir, load_session_id = Draft.ask_session_id()
        project_dir = FileManager.get_project_directory()
        analyse_paths = Draft.stage2_analyse_file_paths(path_session_dir)
        path_completed_trade_file = analyse_paths[Map.trade]
        path_trades_metrics_file = analyse_paths[Map.metric]
        path_rated_metrics_file = analyse_paths[Map.rate]
        # Trades
        completed_trades = pd.read_csv(
            project_dir + path_completed_trade_file, index_col='trade_id').sort_values(['buy_time'])
        metrics = pd.read_csv(project_dir + path_trades_metrics_file,
                              index_col='trade_id').sort_values(['buy_date'])
        metric_names = list(metrics.columns)
        # Loop
        rated_metrics = None
        for metric_name in metric_names:
            if metrics[metric_name].iloc[0] in [True, False]:
                rated_metric_row = new_rated_metric(metric_name)
                rated_metrics = rated_metric_row if rated_metrics is None else rated_metrics.append(
                    rated_metric_row)
        print_rows(path_rated_metrics_file, rated_metrics.replace(
            {np.nan: None}).to_dict(orient='records'), overwrite=True)

    @staticmethod
    def select_flash() -> None:
        old_stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_3)
        # BinanceAPI.CONSTRAINT_KLINES_MAX_PERIOD = Draft.CONSTRAINT_KLINES_MAX_PERIOD
        # Start
        broker = Draft.get_broker()
        pairs = MarketPrice.history_pairs(
            broker.__class__.__name__, active_path=True)
        period = 60*60*6
        n_period = broker.get_max_n_period()
        perfs = pd.DataFrame()
        endtime = _MF.get_timestamp()
        for pair in pairs:
            print(pair)
            marketprice = _MF.catch_exception(MarketPrice.marketprice, 'draft', repport=True, **{
                                              Map.broker: broker, Map.pair: pair, Map.period: period, 'n_period': n_period, 'endtime': endtime})
            perf = {
                Map.pair: pair.__str__(),
                Map.number: None,
                Map.roi: None
            }
            if isinstance(marketprice, MarketPrice):
                highs = np.array(marketprice.get_highs())
                lows = np.array(marketprice.get_lows())
                perf[Map.roi] = (highs/lows - 1).mean()
                perf[Map.number] = highs.shape[0]
            perfs = perfs.append(perf, ignore_index=True)
        rows = perfs.to_dict(orient='records')
        FileManager.write_csv('flash_best_pair.csv', list(
            rows[0].keys()), rows, overwrite=False)
        # End
        Config.update(Config.STAGE_MODE, old_stage)

    @classmethod
    def push_trade_in_hand(cls) -> None:
        BinanceSocket._DEBUG = False
        stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_2)

        def new_executed_buy_order(pair: Pair, buy_date: str, buy_price: Price, amount: Price) -> Order:
            taker_fee = broker.get_trade_fee(pair).get(Map.taker)
            r_asset = pair.get_right()
            l_asset = pair.get_left()
            if not isinstance(buy_date, str):
                raise TypeError(f"Date must be string")
            if (buy_price.get_asset() != r_asset) or (amount.get_asset() != r_asset):
                raise TypeError(
                    f"Wrong asset: buy_price='{buy_price}' & amount='{amount}'")
            order = BinanceOrder(Order.TYPE_MARKET, params=Map({
                Map.pair: pair,
                Map.move: Order.MOVE_BUY,
                Map.amount: amount
            }))
            order._set_execution_time(_MF.date_to_unix(buy_date)*1000)
            order._set_execution_price(buy_price)
            order._set_executed_amount(amount)
            quantity_before_fee = Price(
                order.get_amount()/order.get_execution_price(), l_asset)
            quantity_after_fee = Price(
                quantity_before_fee * (1 - taker_fee), l_asset)
            l_fee = quantity_before_fee - quantity_after_fee
            order._set_executed_quantity(quantity_before_fee)
            order._set_fee(l_fee)
            order._set_status(Order.STATUS_COMPLETED)
            return order

        def new_executed_sell_order(pair: Pair, sell_date: str, sell_price: Price, quantity: Price) -> Order:
            taker_fee = broker.get_trade_fee(pair).get(Map.taker)
            r_asset = pair.get_right()
            l_asset = pair.get_left()
            if not isinstance(sell_date, str):
                raise TypeError(f"Date must be string")
            if (sell_price.get_asset() != r_asset) or (quantity.get_asset() != l_asset):
                raise TypeError(
                    f"Wrong asset: sell_price='{sell_price}' & quantity='{quantity}'")
            order = BinanceOrder(Order.TYPE_MARKET, params=Map({
                Map.pair: pair,
                Map.move: Order.MOVE_SELL,
                Map.quantity: quantity
            }))
            order._set_execution_time(_MF.date_to_unix(sell_date)*1000)
            order._set_execution_price(sell_price)
            order._set_executed_quantity(quantity)
            amount_before_fee = Price(quantity * sell_price, r_asset)
            amount_after_fee = Price(
                amount_before_fee * (1 - taker_fee), r_asset)
            # amount = Price(amount, r_asset)
            order._set_executed_amount(amount_before_fee)
            # fee = Price(quantity * sell_price, r_asset) - amount
            fee = amount_before_fee - amount_after_fee
            order._set_fee(fee)
            order._set_status(Order.STATUS_COMPLETED)
            return order

        def add_new_trade(hand: Hand, pair: Pair, buy_date: str, buy_price: Price, sell_date: str, sell_price: Price) -> None:
            l_asset = pair.get_left()
            if pair.get_right() != hand.get_wallet().get_initial().get_asset():
                raise TypeError(
                    f"Wrong asset: pair='{pair}' & hand's asset='{hand.get_wallet().get_initial().get_asset()}'")
            # Buy
            amount = hand._position_capital()
            buy_order = new_executed_buy_order(
                pair, buy_date, buy_price, amount)
            hand.get_wallet().buy(buy_order)
            # Sell
            quantity = hand.get_wallet().get_position(l_asset)
            sell_order = new_executed_sell_order(
                pair, sell_date, sell_price, quantity)
            hand.get_wallet().sell(sell_order)
            # Record
            trade = HandTrade(buy_order)
            trade.set_sell_order(sell_order)
            trade.extrem_prices(broker)
            hand._add_closed_position(trade)

        # Vars
        session_id = Config.get(Config.SESSION_ID)
        broker = cls.get_broker()
        file_path = f'content/sessions/running/{session_id}/new_trades.csv'
        df = pd.read_csv(FileManager.get_project_directory() + file_path)
        df = df.sort_values(by=[Map.id, 'buy_date', 'sell_date'])
        # Load Hand
        hand_id = df.loc[0, Map.id]
        hand = Hand.load(hand_id)
        r_asset = hand.get_wallet().get_initial().get_asset()
        # Add streams
        l_assets = hand.get_wallet().assets()
        wallet_streams = [broker.generate_stream(Map({Map.pair: Pair(
            l_asset, r_asset), Map.period: Broker.PERIOD_1MIN})) for l_asset in l_assets]
        trade_streams = [broker.generate_stream(Map({Map.pair: Pair(
            pair_str), Map.period: Broker.PERIOD_1MIN})) for pair_str in df[Map.pair]]
        streams = _MF.remove_duplicates([*wallet_streams, *trade_streams])
        streams.sort()
        broker.add_streams(streams)
        #
        roi_before = hand.get_wallet().get_roi(broker)
        for index in df.index:
            pair = Pair(df.loc[index, Map.pair])
            buy_date = df.loc[index, 'buy_date']
            buy_price = Price(df.loc[index, 'buy_price'], r_asset)
            sell_date = df.loc[index, 'sell_date']
            sell_price = Price(df.loc[index, 'sell_price'], r_asset)
            add_new_trade(hand, pair, buy_date, buy_price,
                          sell_date, sell_price)
        # End
        profits = ((df['sell_price']/df['buy_price']-1) -
                   ((1+0.1/100)**2-1))*100
        sum_profit = profits.sum()
        cls.get_view().output(f'profits:\n{profits}\n', is_success=True)
        cls.get_view().output(
            f'sum_profit: {_MF.rate_to_str(sum_profit/100)}\n', is_success=True)
        cls.get_view().output(
            f'wallet_roi: {_MF.rate_to_str(roi_before)} -> {_MF.rate_to_str(hand.get_wallet().get_roi(broker))}', is_success=True)
        _MF.console(**vars())
        # hand.backup()
        Config.update(Config.STAGE_MODE, stage)

    @classmethod
    def load_hand(cls) -> None:
        BinanceSocket._DEBUG = False
        stage = Config.get(Config.STAGE_MODE)
        Config.update(Config.STAGE_MODE, Config.STAGE_2)

        # Vars
        view = cls.get_view()
        broker = cls.get_broker()
        hand_ids = Hand.list_hand_ids()
        hand_id = hand_ids[view.menu("Select the Hand to load:", hand_ids)]
        hand = Hand.load(hand_id)
        r_asset = hand.get_wallet().get_initial().get_asset()
        # Add streams
        l_assets = hand.get_wallet().assets()
        wallet_streams = [broker.generate_stream(Map({Map.pair: Pair(
            l_asset, r_asset), Map.period: Broker.PERIOD_1MIN})) for l_asset in l_assets]
        streams = _MF.remove_duplicates(wallet_streams)
        streams.sort()
        broker.add_streams(streams)
        # End
        cls.get_view().output(
            f'wallet_roi: {hand.get_wallet().get_roi(broker)}\n', is_success=True)
        _MF.console(**vars())
        # hand.backup()
        Config.update(Config.STAGE_MODE, stage)

    @classmethod
    def print_analyse(cls) -> None:
        # BinanceSocket._DEBUG = False
        project_dir = FileManager.get_project_directory()
        trade_file_path = 'content/sessions/analyse/Icarus/2022-08-27_19.00.58_Icarus-v13.5.1/analyse/orders/2022-08-27_19.00.58_Icarus-v13.5.1_completed_trades.csv'
        trade_dir_path = FileManager.path_to_dir(trade_file_path)
        market_analyse_dir_path = '/'.join(trade_dir_path.split('/')
                                           [:-2]) + '/' + 'market_analyse/'
        market_analyse_file_path_pattern = market_analyse_dir_path + \
            f'market_analyse_$period.csv'
        trades = pd.read_csv(project_dir + trade_file_path)
        broker = cls.get_broker()
        pairs = MarketPrice.get_spot_pairs(
            broker.__class__.__name__, Asset('USDT'))
        periods = [broker.PERIOD_1MIN, broker.PERIOD_5MIN, broker.PERIOD_15MIN,
                   broker.PERIOD_30MIN, broker.PERIOD_1H, broker.PERIOD_6H]
        # Add stream
        # streams = broker.generate_streams(pairs, periods)
        # broker.add_streams(streams)
        #
        start_date = trades.loc[trades.index[0], Map.start]
        end_date = trades.loc[trades.index[-1], Map.end]
        starttime = int(_MF.date_to_unix(start_date) - 15 * max(periods))
        endtime = int(_MF.date_to_unix(end_date))
        analyses = MarketPrice.analyse_market(
            broker, pairs, periods, endtime=endtime, starttime=starttime)
        FileManager.make_directory(market_analyse_dir_path)
        for period, analyse in analyses.items():
            period_str = broker.period_to_str(period)
            market_analyse_file_path = market_analyse_file_path_pattern.replace(
                '$period', period_str)
            fields = list(analyse.columns)
            rows = analyse.to_dict('records')
            FileManager.write_csv(market_analyse_file_path,
                                  fields, rows, overwrite=True, make_dir=True)

    @classmethod
    def print_market_trend(cls) -> None:
        def absolut_to_relatif(absolut_path: str) -> str:
            project_dir = FileManager.get_project_directory()
            relatif_path = absolut_path.replace(project_dir, '')
            return relatif_path
        old_stage = Config.get(Config.STAGE_MODE)
        # new_stage = Config.STAGE_2
        new_stage = Config.STAGE_1
        Config.update(Config.STAGE_MODE, new_stage)
        #
        brokker_obj = Draft.get_broker()
        view = Draft.get_view()
        broker_class = brokker_obj.__class__
        broker_str = broker_class.__name__
        pairs = MarketPrice.history_pairs(broker_str, active_path=False) # [:3]
        if new_stage == Config.STAGE_1:
            starttime = int(_MF.date_to_unix('2020-01-01 0:00:00'))
            endtime =   int(_MF.date_to_unix('2023-07-15 00:00:00'))
        else:
            endtime =   _MF.get_timestamp()
            starttime = endtime - 24 * 3600 * 9
        periods = [
            # Broker.PERIOD_1MIN,
            Broker.PERIOD_5MIN,
            Broker.PERIOD_15MIN,
            Broker.PERIOD_30MIN,
            Broker.PERIOD_1H,
            Broker.PERIOD_6H
        ]
        #
        absolute_market_analyse_file_dir = FileManager.get_project_directory() + f'supertrend/'
        relatif_market_analyse_file_dir = absolut_to_relatif(absolute_market_analyse_file_dir)
        FileManager.make_directory(relatif_market_analyse_file_dir)
        for period in periods:
            marketprices = Map()
            for pair in pairs:
                _MF.static_output(_MF.prefix() + f"Loading {period}, {pair}...")
                try:
                    if new_stage == Config.STAGE_1:
                        marketprice_pd = MarketPrice.load_marketprice(broker_str, pair, period, active_path=False)
                    else:
                        marketprice_pd = MarketPrice.marketprices(brokker_obj, pair, period, endtime, starttime=starttime)
                    marketprice_obj = MarketPrice.new_marketprice(broker_class, marketprice_pd.to_numpy().tolist(), pair, period)
                    marketprices.put(marketprice_obj, pair, period)
                except Exception as e:
                    print(e)
            _MF.static_output(_MF.prefix() + f"Analysing {period}...")
            market_analyses = MarketPrice.analyse_market(brokker_obj, pairs, [period], endtime=endtime, starttime=starttime, marketprices=marketprices)
            market_analyse_file = f'{absolute_market_analyse_file_dir}{period}.csv'
            market_analyses[period].to_csv(market_analyse_file)
        _MF.output("End")
        #
        # for period, market_analyse in market_analyses.items():
        #
        Config.update(Config.STAGE_MODE, old_stage)

    @classmethod
    def draft(cls) -> None:
        file_dir = 'market_analyse-0/'
        files = FileManager.get_files(file_dir)
        new_file_dir = 'market_analyse-1/'
        project_dir = FileManager.get_project_directory()
        FileManager.make_directory(new_file_dir)
        for file in files:
            absolut_file = project_dir + file_dir + file
            # period = int(file.replace('.csv', ''))
            df = pd.read_csv(absolut_file, index_col=0)
            # df.set_index(df.columns[0], drop=False, inplace=True)
            df['sum_rise_drop'] =   df['n_rise'] + df['n_drop']
            df['rise_rate'] =       df['n_rise'] / df['sum_rise_drop']
            df['drop_rate'] =       df['n_drop'] / df['sum_rise_drop']
            df.to_csv(project_dir + new_file_dir + file)

    @classmethod
    def main(cls) -> None:
        def cancel() -> None:
            pass
        view = Draft.get_view()
        funcs = [
            cancel,
            cls.draft,
            cls.backtest2,
            cls.loop_backtest2,
            cls.download_market_histories,
            cls.print_market_trend
            # cls.analyse_market_trend,
            # cls.analyse_backtest,
            # cls.format_orders_to_trades,
            # cls.extract_stage2_metrics,
            # cls.extract_stage2_rated_metrics,
            # cls.listen_market,
            # cls.push_trade_in_hand
        ]
        executions = {func.__name__.__str__(): func for func in funcs}
        executions_list = list(executions.keys())
        execution = executions[executions_list[view.menu("Choose the execution:", executions_list)]]
        execution()


if __name__ == '__main__':
    view = Draft.get_view()
    change_session_id = view.ask_boolean("Do you want to change session's ID:")
    if change_session_id:
        session_id = view.input("Enter session ID:")
        Config.update_session_id(session_id)
    else:
        Config.label_session_id()
        session_id = Config.get(Config.SESSION_ID)
    View.RECORD_OUTPUT = True
    Draft.set_model_output()
    _main_starttime = _MF.get_timestamp()
    view.output(f"Start session '{session_id}'", richs=[view.B_CYAN])
    _MF.catch_exception(Draft.main, Draft.__name__)
    Draft.get_broker().close()
    _main_endtime = _MF.get_timestamp()
    exec_duration = _MF.delta_time(_main_starttime, _main_endtime)
    view.output(f"End session '{session_id}': '{exec_duration}'", richs=[view.B_CYAN])
