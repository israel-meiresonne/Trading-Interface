from typing import Tuple
import numpy as np

import pandas as pd

from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class Flash(Icarus):
    @classmethod
    def backtest_trade_history(cls, pair: Pair, period: int, broker: Broker)  -> pd.DataFrame:
        import sys
        from model.API.brokers.Binance.BinanceAPI import BinanceAPI
        from model.structure.Bot import Bot

        def is_buy_period(marketprice: MarketPrice, buy_time: int, period: int) -> bool:
            buy_time_rounded = _MF.round_time(buy_time, period)
            first_open_time = buy_time_rounded + period
            open_time = marketprice.get_time()
            return open_time < first_open_time

        def get_unban_time(buy_time: int, period: int) -> int:
            unban_time = _MF.round_time(buy_time, period) + period
            return unban_time

        buy_repports = []
        n_period = 300
        fees = broker.get_trade_fee(pair)
        taker_fee_rate = fees.get(Map.taker)
        buy_sell_fee = ((1+taker_fee_rate)**2 - 1)
        pair_merged = pair.format(Pair.FORMAT_MERGED)
        str_period = BinanceAPI.convert_interval(period)
        unban_time = 0
        big_period = cls.MARKETPRICE_BUY_BIG_PERIOD
        trades = None
        trade = {}
        market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: period,
            'n_period': n_period
            }
        big_market_params = {
            Map.broker: broker,
            Map.pair: pair,
            Map.period: big_period,
            'n_period': n_period
            }
        broker.add_streams([
            broker.generate_stream(Map({Map.pair: pair, Map.period: period})),
            broker.generate_stream(Map({Map.pair: pair, Map.period: big_period}))
        ])
        i = 0
        Bot.update_trade_index(i)
        marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=True, **market_params)
        while isinstance(marketprice, MarketPrice):
            big_marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **big_market_params)
            open_times = list(marketprice.get_times())
            open_times.reverse()
            closes = list(marketprice.get_closes())
            closes.reverse()
            highs = list(marketprice.get_highs())
            highs.reverse()
            lows = list(marketprice.get_lows())
            lows.reverse()
            opens = list(marketprice.get_opens())
            opens.reverse()
            # Update High/Low price
            if i == 0:
                higher_price = 0
                start_date = _MF.unix_to_date(open_times[-1])
                end_date = _MF.unix_to_date(open_times[-1])
                start_price = closes[-1]
            else:
                end_date = _MF.unix_to_date(open_times[-1])
                end_price = closes[-1]
                higher_price = highs[-1] if highs[-1] > higher_price else higher_price
            # Print time
            sys.stdout.write(f'\r{_MF.prefix()}{_MF.unix_to_date(open_times[-1])}')
            sys.stdout.flush()
            has_position = len(trade) != 0
            period_is_ban = not (open_times[-1] >= unban_time)
            # Update Max/Min roi
            if has_position:
                high_roi = _MF.progress_rate(highs[-1], trade['buy_price'])
                low_roi = _MF.progress_rate(lows[-1], trade['buy_price'])
                min_roi_position = low_roi if (min_roi_position is None) or (low_roi < min_roi_position) else min_roi_position
                max_roi_position = high_roi if (max_roi_position is None) or high_roi > max_roi_position else max_roi_position
            # Try buy/sell
            if (not period_is_ban) and (not has_position):
                unban_time = 0
                can_buy, buy_repport = cls.can_buy(marketprice, big_marketprice)
                buy_repport = {
                    Map.time: _MF.unix_to_date(open_times[-1]),
                    **buy_repport
                }
                buy_repports.append(buy_repport)
                if can_buy:
                    big_marketprice.reset_collections()
                    keltner_high = big_marketprice.get_keltnerchannel(multiple=cls.KELTNER_LARGE_MULTIPLE_BUY).get(Map.high)[0]
                    buy_time = marketprice.get_time()
                    exec_price = max([keltner_high, opens[-1]])
                    min_roi_position = None
                    max_roi_position = None
                    cls._add_buy_time(pair, buy_time)
                    trade = {
                        Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                        Map.pair: pair,
                        Map.period: str_period,
                        Map.id: f'{pair_merged}_{str_period}_{i}',
                        Map.start: start_date,
                        Map.end: end_date,
                        'buy_time': buy_time,
                        'buy_date': _MF.unix_to_date(buy_time),
                        'buy_price': exec_price
                    }
            elif has_position and cls._can_sell_indicator(marketprice):
                # Ban
                sell_in_buy_period = is_buy_period(marketprice, buy_time, period)
                unban_time = get_unban_time(buy_time, period) if sell_in_buy_period else 0
                # Prepare
                sell_time = marketprice.get_time()
                # exec_price = marketprice.get_close()
                exec_price = (closes[-1] + opens[-1])/2
                # Put
                trade['sell_time'] = sell_time
                trade['sell_date'] = _MF.unix_to_date(sell_time)
                trade['sell_price'] = exec_price
                trade['unban_time'] = _MF.unix_to_date(unban_time) if unban_time > 0 else None
                trade[Map.roi] = (trade['sell_price']/trade['buy_price'] - 1) - buy_sell_fee
                trade['roi_losses'] = trade[Map.roi] if trade[Map.roi] < 0 else None
                trade['roi_wins'] = trade[Map.roi] if trade[Map.roi] > 0 else None
                trade['roi_neutrals'] = trade[Map.roi] if trade[Map.roi] == 0 else None
                trade['min_roi_position'] = min_roi_position
                trade['max_roi_position'] = max_roi_position
                trade['min_roi'] = None
                trade['mean_roi'] = None
                trade['max_roi'] = None
                trade['mean_win_roi'] = None
                trade['mean_loss_roi'] = None
                trade[Map.sum] = None
                trade['min_sum_roi'] = None
                trade['max_sum_roi'] = None
                trade['final_roi'] = None
                trade[Map.fee] = buy_sell_fee
                trade['sum_fee'] = None
                trade['sum_roi_no_fee'] = None
                trade['start_price'] = None
                trade['end_price'] = None
                trade['higher_price'] = None
                trade['market_performence'] = None
                trade['max_profit'] = None
                trade['n_win'] = None
                trade['win_rate'] = None
                trade['n_loss'] = None
                trade['loss_rate'] = None
                trades = pd.DataFrame([trade], columns=list(trade.keys())) if trades is None else trades.append(trade, ignore_index=True)
                sum_roi = trades[Map.roi].sum()
                sum_fee = trades[Map.fee].sum()
                trades.loc[trades.index[-1], Map.sum] = sum_roi
                trades.loc[trades.index[-1], f'sum_fee'] = sum_fee
                trades.loc[trades.index[-1], f'sum_roi_no_fee'] = sum_roi + sum_fee
                trade = {}
                buy_time = None
            i += 1
            Bot.update_trade_index(i)
            marketprice = _MF.catch_exception(MarketPrice.marketprice, cls.__name__, repport=False, **market_params)
        print()
        if trades is None:
            default = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.pair: pair,
                Map.period: str_period
                }
            trades = pd.DataFrame([default], columns=list(default.keys()))
        else:
            win_trades = trades[trades[Map.roi] > 0]
            loss_trades = trades[trades[Map.roi] < 0]
            n_trades = win_trades.shape[0] + loss_trades.shape[0]
            trades.loc[:,'higher_price'] = higher_price
            trades.loc[:,'start_price'] = start_price
            trades.loc[:,'end_price'] = end_price
            trades.loc[:,'higher_price'] = higher_price
            trades.loc[:,'market_performence'] = _MF.progress_rate(end_price, start_price)
            trades.loc[:,'max_profit'] = _MF.progress_rate(higher_price, start_price)
            trades.loc[:,'mean_roi'] = trades[Map.roi].mean()
            trades.loc[:,'min_roi'] = trades[Map.roi].min()
            trades.loc[:,'max_roi'] = trades[Map.roi].max()
            trades.loc[:,'mean_win_roi'] = win_trades[Map.roi].mean()
            trades.loc[:,'mean_loss_roi'] = loss_trades[Map.roi].mean()
            trades.loc[:,'min_sum_roi'] = trades[Map.sum].min()
            trades.loc[:,'max_sum_roi'] = trades[Map.sum].max()
            trades.loc[:,'final_roi'] = trades.loc[trades.index[-1], Map.sum]
            trades.loc[:,'n_win'] = win_trades.shape[0]
            trades.loc[:,'win_rate'] = win_trades.shape[0]/n_trades
            trades.loc[:,'n_loss'] = loss_trades.shape[0]
            trades.loc[:,'loss_rate'] = loss_trades.shape[0]/n_trades
        if len(buy_repports) > 0:
            repport_file_path = cls.file_path_backtest_repport(buy_file=True)
            fields = list(buy_repports[0].keys())
            rows = buy_repports
            FileManager.write_csv(repport_file_path, fields, rows, overwrite=False, make_dir=True)
        return trades

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Flash(Map({
            Map.pair: Pair('@json/@json'),
            Map.maximum: None,
            Map.capital: Price(1, '@json'),
            Map.rate: 1,
            Map.period: 0
        }))
        exec(MyJson.get_executable())
        return instance
