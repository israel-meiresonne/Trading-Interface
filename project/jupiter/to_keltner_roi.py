PROJECT_DIR =   '/Users/i.meiresonne.2018/MY-MAC/Dev/apollo21/project/'
STRATEGY_STR =  'Solomon'
BROKER_STR =    'Binance'

import os
import sys

if PROJECT_DIR not in sys.path:
    JUPYTER_FILE_PATH = sys.path[0]
    sys.path.append(PROJECT_DIR)

import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
# exec(_MF.get_import(STRATEGY_STR))
exec(_MF.get_import(BROKER_STR))

def get_broker(broker_str: str) -> Broker:
    return eval(broker_str)
def get_strategy(strategy_str: str) -> Strategy:
    return eval(strategy_str)
def check_type(value, expected_type) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected type '{expected_type}', instead '{type(value)}'")

_MF.OUTPUT = False
Config.update(Config.STAGE_MODE, Config.STAGE_1)
slpited_jupyter_file_path = JUPYTER_FILE_PATH.split('/')
# SESSION_DIR = '/'.join(slpited_jupyter_file_path[:-1]) + '/'
# SESSION_ID = slpited_jupyter_file_path[-2]
# Config.update_session_id(SESSION_ID)
# Config.update(Config.DIR_ACTUAL_SESSION, SESSION_DIR)
# STRATEGY_CLASS =        get_strategy(STRATEGY_STR)
# BACKTEST_FILE_PATH =    STRATEGY_CLASS.get_path_backtest_file(Map.test)
BROKER_CLASS =          get_broker(BROKER_STR)
# PERIODS =               STRATEGY_CLASS._REQUIRED_PERIODS
PERIODS =               []
PERIOD_1MIN =           Broker.PERIOD_1MIN
PERIOD_5MIN =           Broker.PERIOD_5MIN
PERIOD_15MIN =          Broker.PERIOD_15MIN
PERIODS.append(PERIOD_1MIN) if PERIOD_1MIN not in PERIODS else None
PERIODS.append(PERIOD_5MIN) if PERIOD_5MIN not in PERIODS else None
PERIODS.append(PERIOD_15MIN) if PERIOD_15MIN not in PERIODS else None
MARKETPRICES =          Map()
PAIRS =                 None
# PAIR =                  None
# BACKTEST_PD =           None
PLOTS =                 Map()
START_TIME =            None
END_TIME =              None
# Keys
K_OPEN_TIME =       Map.key(Map.open, Map.time)
K_OPEN_DATE =       Map.key(Map.open, Map.date)
# K_BUY_TIME =    Map.key(Map.buy, Map.time)
# K_BUY_PRICE =   Map.key(Map.buy, Map.price)
# K_SELL_PRICE =  Map.key(Map.sell, Map.price)
K_KELTNER_LOW =     Map.key(Map.keltner, Map.low)
K_KELTNER_MIDDLE =  Map.key(Map.keltner, Map.middle)
K_KELTNER_HIGH =    Map.key(Map.keltner, Map.high)
K_KELTNER_ROI =     Map.key(Map.keltner, Map.roi)

def get_marketprice(pair: Pair, period) -> MarketPrice:
    check_type(pair, Pair)
    check_type(period, int)
    return MARKETPRICES.get(pair, period)
def set_plot(pair: Pair, period: int) -> None:
    check_type(pair, Pair)
    check_type(period, int)
    marketprice = get_marketprice(pair, period)
    marketprice_pd = marketprice.to_pd()
    plot = marketprice_pd.loc[(marketprice_pd[Map.time] >= START_TIME) & (marketprice_pd[Map.time] <= END_TIME)]
    plot.set_index(Map.time, drop=False, inplace=True)
    open_dates_pd = _MF.df_apply(plot, [Map.time], _MF.unix_to_date)[Map.time]
    plot.insert(0, K_OPEN_DATE, open_dates_pd)
    plot.insert(1, Map.pair, pair)
    PLOTS.put(plot, pair, period)
def get_plot(pair: Pair, period: int) -> pd.DataFrame:
    check_type(pair, Pair)
    check_type(period, int)
    plot = PLOTS.get(pair, period)
    if plot is None:
        set_plot(pair, period)
        plot = PLOTS.get(pair, period)
    return plot
def add_keltner(plot: pd.DataFrame, marketprice: MarketPrice) -> pd.DataFrame:
    check_type(plot, pd.DataFrame)
    check_type(marketprice, MarketPrice)
    if K_KELTNER_LOW not in plot.columns:
        keltners = marketprice.get_keltnerchannel(multiple=1)
        keltner_low = list(keltners.get(Map.low))
        keltner_low.reverse()
        keltner_middle = list(keltners.get(Map.middle))
        keltner_middle.reverse()
        keltner_high = list(keltners.get(Map.high))
        keltner_high.reverse()
        keltners_dict = {
            K_OPEN_TIME:        marketprice.to_pd()[Map.time],
            K_KELTNER_LOW:      keltner_low,
            K_KELTNER_MIDDLE:   keltner_middle,
            K_KELTNER_HIGH:     keltner_high
        }
        keltner_dict_keys = list(keltners_dict.keys())
        keltners_pd = pd.DataFrame(keltners_dict)
        keltners_pd.set_index(K_OPEN_TIME, inplace=True)
        plot.loc[plot.index, keltner_dict_keys[1:]] = keltners_pd[keltner_dict_keys[1:]]
        plot[K_KELTNER_ROI] = (plot[K_KELTNER_HIGH] / plot[K_KELTNER_LOW]) - 1
    return plot

pair_strs = ['aave/usdt', 'aca/usdt', 'ach/usdt', 'acm/usdt', 'ada/usdt', 'adx/usdt', 'agld/usdt', 'aion/usdt',
             'akro/usdt', 'alcx/usdt', 'algo/usdt', 'alice/usdt', 'alpaca/usdt', 'alpha/usdt', 'alpine/usdt',
             'amp/usdt', 'anc/usdt', 'ankr/usdt', 'ant/usdt', 'any/usdt', 'ape/usdt', 'api3/usdt', 'apt/usdt',
             'ar/usdt', 'ardr/usdt', 'arpa/usdt', 'asr/usdt', 'astr/usdt', 'ata/usdt', 'atm/usdt', 'atom/usdt',
             'auction/usdt', 'audio/usdt', 'auto/usdt', 'ava/usdt', 'avax/usdt', 'axs/usdt', 'badger/usdt',
             'bake/usdt', 'bal/usdt', 'band/usdt', 'bar/usdt', 'bat/usdt', 'bch/usdt', 'beam/usdt', 'bel/usdt',
             'beta/usdt', 'bico/usdt', 'bifi/usdt', 'bkrw/usdt', 'blz/usdt', 'bnb/usdt', 'bnt/usdt', 'bnx/usdt',
             'bond/usdt', 'bsw/usdt', 'btc/usdt', 'btcst/usdt', 'btg/usdt', 'bts/usdt', 'btt/usdt', 'bttc/usdt',
             'burger/usdt', 'bzrx/usdt', 'c98/usdt', 'cake/usdt', 'celo/usdt', 'celr/usdt', 'cfx/usdt', 'chess/usdt',
             'chr/usdt', 'chz/usdt', 'city/usdt', 'ckb/usdt', 'clv/usdt', 'cocos/usdt', 'comp/usdt', 'cos/usdt',
             'coti/usdt', 'crv/usdt', 'ctk/usdt', 'ctsi/usdt', 'ctxc/usdt', 'cvc/usdt', 'cvp/usdt', 'cvx/usdt',
             'dar/usdt', 'dash/usdt', 'data/usdt', 'dcr/usdt', 'dego/usdt', 'dent/usdt', 'dexe/usdt', 'df/usdt',
             'dgb/usdt', 'dia/usdt', 'dnt/usdt', 'dock/usdt', 'dodo/usdt', 'doge/usdt', 'dot/usdt', 'drep/usdt',
             'dusk/usdt', 'dydx/usdt', 'egld/usdt', 'elf/usdt', 'enj/usdt', 'ens/usdt', 'eos/usdt', 'eps/usdt',
             'epx/usdt', 'ern/usdt', 'etc/usdt', 'eth/usdt', 'farm/usdt', 'fet/usdt', 'fida/usdt', 'fil/usdt',
             'fio/usdt', 'firo/usdt', 'fis/usdt', 'flm/usdt', 'flow/usdt', 'flux/usdt', 'for/usdt', 'forth/usdt',
             'front/usdt', 'ftm/usdt', 'ftt/usdt', 'fun/usdt', 'fxs/usdt', 'gal/usdt', 'gala/usdt', 'ghst/usdt',
             'glmr/usdt', 'gmt/usdt', 'gmx/usdt', 'gno/usdt', 'grt/usdt', 'gtc/usdt', 'gto/usdt', 'gxs/usdt',
             'hard/usdt', 'hbar/usdt', 'hc/usdt', 'hft/usdt', 'high/usdt', 'hive/usdt', 'hnt/usdt', 'hook/usdt',
             'hot/usdt', 'icp/usdt', 'icx/usdt', 'idex/usdt', 'ilv/usdt', 'imx/usdt', 'inj/usdt', 'iost/usdt',
             'iota/usdt', 'iotx/usdt', 'iris/usdt', 'jasmy/usdt', 'joe/usdt', 'jst/usdt', 'juv/usdt', 'kava/usdt',
             'kda/usdt', 'keep/usdt', 'key/usdt', 'klay/usdt', 'kmd/usdt', 'knc/usdt', 'kp3r/usdt', 'ksm/usdt',
             'lazio/usdt', 'ldo/usdt', 'lend/usdt', 'lever/usdt', 'lina/usdt', 'link/usdt', 'lit/usdt', 'loka/usdt',
             'lpt/usdt', 'lrc/usdt', 'lsk/usdt', 'ltc/usdt', 'lto/usdt', 'luna/usdt', 'lunc/usdt', 'magic/usdt',
             'mana/usdt', 'mask/usdt', 'matic/usdt', 'mbl/usdt', 'mbox/usdt', 'mc/usdt', 'mco/usdt', 'mdt/usdt',
             'mdx/usdt', 'mft/usdt', 'mina/usdt', 'mir/usdt', 'mith/usdt', 'mkr/usdt', 'mln/usdt', 'mob/usdt',
             'movr/usdt', 'mtl/usdt', 'multi/usdt', 'nano/usdt', 'nbs/usdt', 'nbt/usdt', 'near/usdt', 'nebl/usdt',
             'neo/usdt', 'nexo/usdt', 'nkn/usdt', 'nmr/usdt', 'npxs/usdt', 'nu/usdt', 'nuls/usdt', 'ocean/usdt',
             'og/usdt', 'ogn/usdt', 'om/usdt', 'omg/usdt', 'one/usdt', 'ong/usdt', 'ont/usdt', 'ooki/usdt',
             'op/usdt', 'orn/usdt', 'osmo/usdt', 'oxt/usdt', 'paxg/usdt', 'people/usdt', 'perl/usdt', 'perp/usdt',
             'pha/usdt', 'phb/usdt', 'pla/usdt', 'pnt/usdt', 'pols/usdt', 'poly/usdt', 'polyx/usdt', 'pond/usdt',
             'porto/usdt', 'powr/usdt', 'psg/usdt', 'pundix/usdt', 'pyr/usdt', 'qi/usdt', 'qnt/usdt', 'qtum/usdt',
             'quick/usdt', 'rad/usdt', 'ramp/usdt', 'rare/usdt', 'ray/usdt', 'reef/usdt', 'rei/usdt', 'ren/usdt',
             'rep/usdt', 'req/usdt', 'rgt/usdt', 'rif/usdt', 'rlc/usdt', 'rndr/usdt', 'rose/usdt', 'rune/usdt',
             'rvn/usdt', 'sand/usdt', 'santos/usdt', 'sc/usdt', 'scrt/usdt', 'sfp/usdt', 'shib/usdt', 'skl/usdt',
             'slp/usdt', 'snx/usdt', 'sol/usdt', 'spell/usdt', 'srm/usdt', 'steem/usdt', 'stg/usdt', 'stmx/usdt',
             'storj/usdt', 'stpt/usdt', 'strat/usdt', 'strax/usdt', 'stx/usdt', 'sun/usdt', 'super/usdt',
             'sushi/usdt', 'sxp/usdt', 'sys/usdt', 't/usdt', 'tct/usdt', 'tfuel/usdt', 'theta/usdt', 'tko/usdt',
             'tlm/usdt', 'tomo/usdt', 'torn/usdt', 'trb/usdt', 'troy/usdt', 'tru/usdt', 'trx/usdt', 'tvk/usdt',
             'twt/usdt', 'uma/usdt', 'unfi/usdt', 'uni/usdt', 'utk/usdt', 'vet/usdt', 'vgx/usdt', 'vidt/usdt',
             'vite/usdt', 'voxel/usdt', 'vtho/usdt', 'wan/usdt', 'waves/usdt', 'waxp/usdt', 'win/usdt', 'wing/usdt',
             'wnxm/usdt', 'woo/usdt', 'wrx/usdt', 'wtc/usdt', 'xec/usdt', 'xem/usdt', 'xlm/usdt', 'xmr/usdt', 'xno/usdt',
             'xrp/usdt', 'xtz/usdt', 'xvg/usdt', 'xvs/usdt', 'xzc/usdt', 'yfi/usdt', 'yfii/usdt', 'ygg/usdt', 'zec/usdt',
             'zen/usdt', 'zil/usdt', 'zrx/usdt']
PAIRS = [Pair(pair_str) for pair_str in pair_strs]

START_TIME =    _MF.date_to_unix("2021-01-01 00:00:00")
END_TIME =      _MF.date_to_unix("2023-01-01 00:00:00")
period_1min =   PERIOD_1MIN
broker_class =  BROKER_CLASS
broker_str =    BROKER_STR
sub_pairs =     PAIRS
#
older_time = START_TIME - period_1min * broker_class.get_max_n_period()
older_time_milli = older_time * 1000
#
n_above_x_list = []
keltner_trigger_1 = 1/100
keltner_trigger_2 = 2/100
#
starttime = _MF.get_timestamp()
n_turn = len(sub_pairs)
for pair in sub_pairs:
    try:
        turn = sub_pairs.index(pair) + 1
        progresse_message = _MF.loop_progression(starttime, turn, n_turn, f"Loading {pair.__str__().upper()}")
        _MF.static_output(progresse_message)
        #
        # if turn == 1:
        #     raise Exception('Test try catch')
        # Load
        marketprice_pd = MarketPrice.load_marketprice(broker_str, pair, period_1min, False)
        marketprice_sliced_pd = marketprice_pd[(marketprice_pd['0'] >= older_time_milli) & (marketprice_pd['0'] <= END_TIME*1000)]
        period_str = broker_class.period_to_str(period_1min)
        marketprice_list = marketprice_sliced_pd.to_numpy().tolist()
        marketprice = MarketPrice.new_marketprice(broker_class, marketprice_list, pair, period_1min)
        MARKETPRICES.put(marketprice, pair, period_1min)
        # Analyse
        progresse_message = _MF.loop_progression(starttime, turn, n_turn, f"Analyse of {pair.__str__().upper()}")
        _MF.static_output(progresse_message)
        plot = get_plot(pair, PERIOD_1MIN)
        marketprice_1min = get_marketprice(pair, PERIOD_1MIN)
        add_keltner(plot, marketprice_1min)
        n_above_trigger_1 = plot[plot[K_KELTNER_ROI] >= keltner_trigger_1].shape[0]
        n_above_trigger_2 = plot[plot[K_KELTNER_ROI] >= keltner_trigger_2].shape[0]
        row = {
            Map.pair:           pair,
            Map.start:          plot[K_OPEN_DATE].iloc[0],
            Map.end:            plot[K_OPEN_DATE].iloc[-1],
            Map.interval:       _MF.delta_time(int(plot.index[0]), int(plot.index[-1])),
            keltner_trigger_1:  n_above_trigger_1,
            keltner_trigger_2:  n_above_trigger_2
        }
        n_above_x_list.append(row)
    except Exception as e:
        def xxx() -> None:
            raise e
        _MF.catch_exception(xxx, 'to_keltner_roi.py')
    del MARKETPRICES
    MARKETPRICES = Map()
    del PLOTS
    PLOTS = Map()

prefix = _MF.unix_to_date(_MF.get_timestamp(), form=_MF.FORMAT_D_H_M_S_FOR_FILE)
rows = sorted(n_above_x_list, key=lambda row: row[keltner_trigger_2], reverse=True)
fields = list(rows[0].keys())
path = f'jupiter/{prefix}_top_keltner_roi.csv'
FileManager.write_csv(path, fields, rows)
_MF.output('\n' + _MF.prefix() + 'End print stats')
