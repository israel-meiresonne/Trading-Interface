from datetime import date, datetime
from operator import itemgetter
from time import sleep
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceMarketPrice import BinanceMarketPrice
from model.API.brokers.Binance.BinanceRequest import BinanceRequest
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Log import Log
from model.structure.strategies.Floor.Floor import Floor
from model.structure.strategies.Icarus.Icarus import Icarus
from model.structure.strategies.MinMax.MinMax import MinMax
from model.structure.strategies.MinMaxFloor.MinMaxFloor import MinMaxFloor
from model.structure.Strategy import Strategy
from model.tools.Asset import Asset
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.MachineLearning import MachineLearning
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor
from model.tools.Price import Price

_PRINT_SUCCESS = '🖨 File printed ✅'
_BROKER = Binance(Map({Map.public: "-", Map.secret: "-", Map.test_mode: False}))

def get_broker() -> Broker:
    return _BROKER

def predictor() -> None:
    bkr = get_broker()
    fiat_asset = Asset('USDT')
    all_pairs = MarketPrice.get_spot_pairs(bkr.__class__.__name__, fiat_asset)
    model_pairs = Predictor.learned_pairs(stock_path=True)
    miss_pairs = [pair for pair in all_pairs if pair not in model_pairs]
    hist_periods = [60 * 60]
    learn_periods = hist_periods
    Predictor.update_market_histories(bkr, fiat_asset, pairs=miss_pairs, periods=hist_periods)
    Predictor.update_learns(pairs=miss_pairs, periods=learn_periods)

def download_market_histories() -> None:
    # _MF.OUTPUT = True
    broker = get_broker()
    broker_name = broker.__class__.__name__
    endtime = int(_MF.date_to_unix('2022-01-01 00:00:00'))
    starttime = int(_MF.date_to_unix('2020-10-31 00:00:00'))
    fiat_asset = Asset('USDT')
    # all_pairs = MarketPrice.get_spot_pairs(broker_name, fiat_asset)
    # existing_pairs = MarketPrice.history_pairs(broker_name, active_path=False)
    # miss_pairs = [pair for pair in all_pairs if pair not in existing_pairs]
    pairs = [Pair('atom/usdt')]
    # periods = [60, 60*5, 60*15, 60*60]
    periods = [60*30]
    MarketPrice.save_marketprices(broker, pairs, periods, endtime, starttime)

def load_market_history_pd() -> None:
    broker = get_broker()
    broker_name = broker.__class__.__name__
    pair = Pair('AAVE/USDT')
    period = 60
    file_path = MarketPrice.file_path_market_history(broker_name, pair, period, active_path=False)
    project_dir = FileManager.get_project_directory()
    history = pd.read_csv(project_dir + file_path)
    print(history.shape)

def load_market_history_dict() -> None:
    broker = get_broker()
    broker_name = broker.__class__.__name__
    pair = Pair('AAVE/USDT')
    period = 60
    file_path = MarketPrice.file_path_market_history(broker_name, pair, period, active_path=False)
    history = FileManager.get_csv(file_path)
    print(len(history), len(history[0]))

def backtest_icarus() -> None:
    # _MF.OUTPUT = True
    old_stage = Config.get(Config.STAGE_MODE)
    Config.update(Config.STAGE_MODE, Config.STAGE_1)
    broker = get_broker()
    broker_name = broker.__class__.__name__
    starttime = 1608537600  # December 21, 2020 8:00:00
    endtime = 1614556800    # March 1, 2021 0:00:00
    periods = [60*15]
    # pairs = [Pair('BCH/USDT')]
    pairs = MarketPrice.history_pairs(broker_name, active_path=True)
    Icarus.backtest(broker, starttime, endtime, periods, pairs)
    Config.update(Config.STAGE_MODE, old_stage)

def draft() -> None:
    pairs = Icarus.best_pairs()
    print(pairs)

def main() -> None:
    pass

if __name__ == '__main__':
    _main_starttime = _MF.get_timestamp()
    Config.update(Config.STAGE_MODE, Config.STAGE_3)
    print(_MF.prefix() + '\033[46m' +f"Start execution:" + '\033[0m')
    main()
    get_broker().close()
    _main_endtime = _MF.get_timestamp()
    print(_MF.prefix() + '\033[46m' + f"End execution: {_MF.delta_time(_main_starttime, _main_endtime)}" + '\033[0m')