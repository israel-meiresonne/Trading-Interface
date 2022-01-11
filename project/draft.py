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

def load_icarus_pairs() -> None:
    stock_pairs = Predictor.learned_pairs(stock_path=True)
    occup_df = Predictor.load_occupation_rate()
    df = occup_df[occup_df[Map.mean] >= 40/100]
    df = df[df[">= 100"] >= 20/100]
    filtered_pair = df[Map.pair].to_list()
    allowed_pairs = [stock_pair for stock_pair in stock_pairs if stock_pair.__str__() in filtered_pair]
    print(allowed_pairs)

def main() -> None:
    load_icarus_pairs()

if __name__ == '__main__':
    starttime = _MF.get_timestamp()
    Config.update(Config.STAGE_MODE, Config.STAGE_3)
    print(_MF.prefix() + '\033[46m' +f"Start execution:" + '\033[0m')
    main()
    get_broker().close()
    endtime = _MF.get_timestamp()
    print(_MF.prefix() + '\033[46m' + f"End execution: {_MF.delta_time(starttime, endtime)}" + '\033[0m')