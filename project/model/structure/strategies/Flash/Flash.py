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
    KELTNER_LARGE_MULTIPLE_BUY = 2.5
    KELTNER_SMALL_MULTIPLE_BUY = 1
    PSAR_STEP = 0.075
    VOLUME_ZERO_N_PERIOD = 10
    VOLUME_ZERO_RATIO = 0

    @classmethod
    def _can_sell_indicator(cls, marketprice: MarketPrice) ->  bool:
        def is_tangent_macd_dropping(vars_map: Map) -> bool:
            macd_map = marketprice.get_macd()
            macd = list(macd_map.get(Map.macd))
            macd.reverse()
            tangent_macd_dropping = macd[-1] <= macd[-2]
            return tangent_macd_dropping

        def is_edited_psar_dropping(vars_map: Map) -> bool:
            psar = list(marketprice.get_psar(step=cls.PSAR_STEP))
            psar.reverse()
            # Check
            edited_psar_dropping = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_DROPPING
            # Put
            vars_map.put(edited_psar_dropping, 'edited_psar_dropping')
            vars_map.put(psar, 'edited_psar')
            return edited_psar_dropping

        def is_tangent_rsi_dropping(vars_map: Map) -> bool:
            rsi = list(marketprice.get_rsis())
            rsi.reverse()
            tangent_rsi_dropping = rsi[-1] <= rsi[-2]
            return tangent_rsi_dropping

        vars_map = Map()
        # Close
        closes = list(marketprice.get_closes())
        closes.reverse()
        can_sell = is_tangent_macd_dropping(vars_map) or is_tangent_rsi_dropping(vars_map) or is_edited_psar_dropping(vars_map)
        return can_sell

    @classmethod
    def _can_buy_indicator(cls, child_marketprice: MarketPrice, big_marketprice: MarketPrice) -> Tuple[bool, dict]:
        def is_close_above_big_keltner(vars_map: Map) -> bool:
            big_marketprice.reset_collections()
            mult = cls.KELTNER_LARGE_MULTIPLE_BUY
            keltner = big_marketprice.get_keltnerchannel(multiple=mult)
            keltner_high = list(keltner.get(Map.high))
            keltner_high.reverse()
            # Check
            close_above_big_keltner = closes[-1] > keltner_high[-1]
            # Put
            vars_map.put(close_above_big_keltner, 'close_above_big_keltner')
            vars_map.put(keltner_high, f'big_keltner_high2_5')
            return close_above_big_keltner

        def is_macd_historgram_positive(vars_map: Map, marketprice: MarketPrice, repport: bool) -> None:
            macd_map = marketprice.get_macd()
            histogram = list(macd_map.get(Map.histogram))
            histogram.reverse()
            # Check
            macd_historgram_positive = histogram[-1] > 0
            # Put
            vars_map.put(macd_historgram_positive, 'macd_historgram_positive') if repport else None
            return macd_historgram_positive

        def is_big_macd_historgram_positive(vars_map: Map) -> None:
            # Check
            big_macd_historgram_positive = is_macd_historgram_positive(vars_map, big_marketprice, repport=False)
            # Put
            vars_map.put(big_macd_historgram_positive, 'big_macd_historgram_positive')
            return big_macd_historgram_positive

        def is_edited_psar_rising(vars_map: Map) -> bool:
            psar = list(child_marketprice.get_psar(step=cls.PSAR_STEP))
            psar.reverse()
            # Check
            edited_psar_rising = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_RISING
            # Put
            vars_map.put(edited_psar_rising, 'edited_psar_rising')
            vars_map.put(psar, 'edited_psar')
            return edited_psar_rising

        def have_not_bought_edited_psar(vars_map: Map) -> bool:
            open_times = list(child_marketprice.get_times())
            open_times.reverse()
            psar = list(child_marketprice.get_psar(step=cls.PSAR_STEP))
            psar.reverse()
            # Get psar's start and end time
            psar_swings = _MF.group_swings(closes, psar)
            now_index = len(psar) - 1
            interval = psar_swings[now_index]
            psar_starttime = open_times[interval[0]]
            psar_endtime = open_times[now_index]
            # Get psar's buy times
            buy_times = np.array(cls.get_buy_times(pair))
            psar_buy_times = buy_times[(buy_times >= psar_starttime) & (buy_times < psar_endtime)]
            # Check
            not_bought_edited_psar = psar_buy_times.shape[0] == 0
            # Put
            vars_map.put(not_bought_edited_psar, 'not_bought_edited_psar')
            vars_map.put(_MF.unix_to_date(psar_starttime), 'edited_psar_starttime')
            vars_map.put(_MF.unix_to_date(psar_endtime), 'edited_psar_endtime')
            vars_map.put(psar, 'edited_psar')
            return not_bought_edited_psar

        def is_zero_ratio_bellow_limit(vars_map: Map) -> bool:
            n_period = cls.VOLUME_ZERO_N_PERIOD
            ratio_limit = cls.VOLUME_ZERO_RATIO
            l_volumes = list(child_marketprice.get_volumes(Map.left))
            l_volumes.reverse()
            # Evaluate Ration
            l_volumes_np = np.array(l_volumes)
            sub_l_volumes_np = l_volumes_np[-n_period:]
            zero_l_volumes_np = sub_l_volumes_np[sub_l_volumes_np == 0]
            zero_ratio = zero_l_volumes_np.shape[0]/n_period
            # Check
            zero_ratio_bellow_limit = zero_ratio <= ratio_limit
            # Put
            vars_map.put(zero_ratio_bellow_limit, 'zero_ratio_bellow_limit')
            vars_map.put(zero_ratio, 'zero_ratio')
            vars_map.put(zero_l_volumes_np.shape[0], 'n_zero')
            vars_map.put(n_period, 'zero_n_period')
            vars_map.put(ratio_limit, 'zero_ratio_limit')
            vars_map.put(l_volumes, 'l_volumes')
            return zero_ratio_bellow_limit

        def is_big_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(big_marketprice.get_super_trend())
            supertrend.reverse()
            big_supertrend_rising = MarketPrice.get_super_trend_trend(big_closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            vars_map.put(big_supertrend_rising, 'big_supertrend_rising')
            vars_map.put(supertrend, 'big_supertrend')
            return big_supertrend_rising

        def is_supertrend_rising(vars_map: Map) -> bool:
            supertrend = list(child_marketprice.get_super_trend())
            supertrend.reverse()
            supertrend_rising = MarketPrice.get_super_trend_trend(closes, supertrend, -1) == MarketPrice.SUPERTREND_RISING
            vars_map.put(supertrend_rising, 'supertrend_rising')
            vars_map.put(supertrend, Map.supertrend)
            return supertrend_rising

        def is_big_psar_rising(vars_map: Map) -> bool:
            child_marketprice.reset_collections()
            psar = list(child_marketprice.get_psar())
            psar.reverse()
            # Check
            big_psar_rising = MarketPrice.get_psar_trend(closes, psar, -1) == MarketPrice.PSAR_RISING
            # Put
            vars_map.put(big_psar_rising, 'big_psar_rising')
            vars_map.put(psar, 'big_psar')
            return big_psar_rising

        def is_rsi_rising(vars_map: Map) -> bool:
            rsi = list(child_marketprice.get_rsis())
            rsi.reverse()
            rsi_rising = rsi[-1] > rsi[-2]
            # Put
            vars_map.put(rsi_rising, 'rsi_rising')
            vars_map.put(rsi, Map.rsi)
            return rsi_rising

        vars_map = Map()
        pair = child_marketprice.get_pair()
        # Close
        closes = list(child_marketprice.get_closes())
        closes.reverse()
        big_closes = list(big_marketprice.get_closes())
        big_closes.reverse()
        # Check
        can_buy_indicator = is_zero_ratio_bellow_limit(vars_map) and is_close_above_big_keltner(vars_map) \
            and is_big_macd_historgram_positive(vars_map) and is_macd_historgram_positive(vars_map, child_marketprice, repport=True) \
                and is_edited_psar_rising(vars_map) and have_not_bought_edited_psar(vars_map) and is_big_supertrend_rising(vars_map) \
                    and is_supertrend_rising(vars_map) and is_big_psar_rising(vars_map) and is_rsi_rising(vars_map)
        # Repport
        l_volumes = vars_map.get('l_volumes')
        big_supertrend = vars_map.get('big_supertrend')
        big_keltner_high2_5 = vars_map.get('big_keltner_high2_5')
        edited_psar = vars_map.get('edited_psar')
        supertrend = vars_map.get(Map.supertrend)
        big_psar = vars_map.get('big_psar')
        rsi = vars_map.get(Map.rsi)
        key = cls._can_buy_indicator.__name__
        repport = {
            f'{key}.can_buy_indicator': can_buy_indicator,
            f'{key}.zero_ratio_bellow_limit': vars_map.get('zero_ratio_bellow_limit'),
            f'{key}.close_above_big_keltner': vars_map.get('close_above_big_keltner'),
            f'{key}.big_macd_historgram_positive': vars_map.get('big_macd_historgram_positive'),
            f'{key}.macd_historgram_positive': vars_map.get('macd_historgram_positive'),
            f'{key}.edited_psar_rising': vars_map.get('edited_psar_rising'),
            f'{key}.not_bought_edited_psar': vars_map.get('not_bought_edited_psar'),
            f'{key}.big_supertrend_rising': vars_map.get('big_supertrend_rising'),
            f'{key}.supertrend_rising': vars_map.get('supertrend_rising'),
            f'{key}.big_psar_rising': vars_map.get('big_psar_rising'),
            f'{key}.rsi_rising': vars_map.get('rsi_rising'),
            f'{key}.zero_ratio': vars_map.get('zero_ratio'),
            f'{key}.n_zero': vars_map.get('n_zero'),
            f'{key}.zero_n_period': vars_map.get('zero_n_period'),
            f'{key}.zero_ratio_limit': vars_map.get('zero_ratio_limit'),
            f'{key}.edited_psar_starttime': vars_map.get('edited_psar_starttime'),
            f'{key}.edited_psar_endtime': vars_map.get('edited_psar_endtime'),
            f'{key}.closes[-1]': closes[-1],
            f'{key}.big_closes[-1]': big_closes[-1],
            f'{key}.l_volumes[-1]': l_volumes[-1] if l_volumes is not None else None,
            f'{key}.big_keltner_high2_5[-1]': big_keltner_high2_5[-1] if big_keltner_high2_5 is not None else None,
            f'{key}.edited_psar[-1]': edited_psar[-1] if edited_psar is not None else None,
            f'{key}.big_supertrend[-1]': big_supertrend[-1] if big_supertrend is not None else None,
            f'{key}.supertrend[-1]': supertrend[-1] if supertrend is not None else None,
            f'{key}.big_psar[-1]': big_psar[-1] if big_psar is not None else None,
            f'{key}.rsi[-1]': rsi[-1] if rsi is not None else None
        }
        return can_buy_indicator, repport

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
