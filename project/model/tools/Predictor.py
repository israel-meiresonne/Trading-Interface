from typing import List, Tuple, Union

import numpy as np
import pandas as pd
from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.DeepLearning import DeepLearning
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair


class Predictor:
    _DEBUG = True
    _MARKET_MAX_N_PERIOD = 1000
    _N_FEATURE = 60
    _FILE_PATH_HISTORY = Config.get(Config.PREDICTOR_FILE_PATH_HISTORY)
    _PATH_LEARN = Config.get(Config.PREDICTOR_PATH_LEARN)
    _FILE_LEARN_JSON = f'{DeepLearning.__name__}.json'
    _FILE_LEARN_MODEL = 'keras_model.xyz'
    _FILE_LEARN_CONFIG = 'config.csv'
    _LEARN_PERIODS = [
        # 60 * 1,
        # 60 * 3,
        # 60 * 5,
        # 60 * 15,
        # 60 * 30,
        60 * 60
    ]
    _DATASET_SIZES = {
        Map.minimum: 1*10**(4),
        Map.maximum: 1.6*10**(4)
    }
    CLOSE = Map.close
    HIGH = Map.high
    LOW = Map.low

    def __init__(self, pair: Pair, period: int) -> None:
        self.__pair = pair
        self.__period = period
        self.__models = Map({
            Predictor.CLOSE: None,
            Predictor.HIGH: None,
            Predictor.LOW: None
        })
    
    def get_pair(self) -> Pair:
        return self.__pair
    
    def get_period(self) -> int:
        return self.__period
    
    def get_models(self) -> Map:
        return self.__models
    
    def get_model(self, model_type: str) -> DeepLearning:
        models = self.get_models()
        if model_type not in models.get_keys():
            raise ValueError(f"This model type '{model_type}' is not supported")
        model = models.get(model_type)
        if model is None:
            models.put(self.load_model(self.get_pair(), self.get_period(), model_type=model_type), model_type)
        return models.get(model_type)
    
    def predict(self, prices: np.ndarray, model_type: str) -> float:
        """
        To predict next market price

        Parameters:
        -----------
        market: MarketPrice
            Market prices with shape=(n_sample, n_feature)
        model_type: str
            Model to use for prediction
        
        Raises:
        -------
        raise: ValueExecption
            If number element in prices is below number of feature necessary
        
        Returns:
        --------
            The next market price with shape=(n_sample, 1)
        """
        """
        prices = list(eval(f"market.get_{model_type}s()"))
        prices.reverse()
        """
        model = self.get_model(model_type)
        predictions = model.predict(prices)
        return predictions

    # ——————————————————————————————————————————— STATIC GETTTER DOWN ——————————————————————————————————————————————————

    @staticmethod
    def get_learn_periods() -> list:
        return Predictor._LEARN_PERIODS

    @staticmethod
    def get_dataset_sizes() -> dict:
        return Predictor._DATASET_SIZES

    @staticmethod
    def get_n_feature() -> int:
        return Predictor._N_FEATURE
        
    @staticmethod
    def get_learn_json_file() -> str:
        return Predictor._FILE_LEARN_JSON
        
    @staticmethod
    def get_learn_model_file() -> str:
        return Predictor._FILE_LEARN_MODEL

    # ——————————————————————————————————————————— STATIC GETTTER UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION LEARN DOWN ———————————————————————————————————————————

    @staticmethod
    def add_learns(bkr: Broker, pairs: List[Pair]) -> None:
        """
        To learn AI to predict market prices for given pairs
        NOTE: Add histories and learns only if history don't exist
        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            List of Pair to train AI for
        periods: List[int]
            List of periods to train AI on
        """
        _back_cyan = '\033[46m' + '\033[30m'
        _normal = '\033[0m'
        # Download histories
        pair_histories_dir = Predictor.history_dir()
        pair_histories = FileManager.get_dirs(pair_histories_dir)
        existing_hists = [pair_str.lower() for pair_str in pair_histories]
        not_existing_hists = [pair for pair in pairs if pair.format(Pair.FORMAT_UNDERSCORE) not in existing_hists]
        print(_MF.prefix() + _back_cyan + f"Start adding '{len(not_existing_hists)}' pairs histories..." + _normal) if Predictor._DEBUG else None
        can_add = []
        for pair in not_existing_hists:
            if Predictor._enough_period(bkr, pair):
                can_add.append(pair)
                Predictor._maintain_market_history(bkr, pair)
        print(_MF.prefix() + _back_cyan + f"End to add '{len(can_add)}' pairs histories" + _normal) if Predictor._DEBUG else None
        print(_MF.json_encode([pair.__str__() for pair in can_add])) if Predictor._DEBUG else None
        bkr.close()
        # Learn
        print(_MF.prefix() + _back_cyan + f"Start learning '{len(can_add)}' pairs..." + _normal) if Predictor._DEBUG else None
        [Predictor._learn(pair) for pair in can_add]
        print(_MF.prefix() + _back_cyan + f"End to learn pairs histories" + _normal) if Predictor._DEBUG else None

    @staticmethod
    def update_learns():
        pass

    @staticmethod
    def _maintain_market_history(bkr: Broker, pair: Pair) -> None:
        """
        To create new market history if there's none else add histories since last add

        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            Pair to download
        """
        _cyan = '\033[36m'
        _normal = '\033[0m'
        periods = Predictor.get_learn_periods()
        unix_time = _MF.get_timestamp()
        for period in periods:
            endtime = _MF.round_time(unix_time, period)
            if Predictor.market_history_file_exist(pair, period):
                print(_MF.prefix() + _cyan + f"({pair.__str__().upper()}) history exist for period '{int(period/60)}min'" + _normal) if Predictor._DEBUG else None
                overwrite = False
                starttime = Predictor.load_market_history(
                    pair, period).iloc[-1, 0]
            else:
                print(_MF.prefix() + _cyan + f"({pair.__str__().upper()}) history don't exist for period '{int(period/60)}min'" + _normal) if Predictor._DEBUG else None
                overwrite = True
                ds_max_size = Predictor.get_dataset_sizes()[Map.maximum]
                starttime = int(endtime - ds_max_size * period)
            if starttime < endtime:
                marketprices = Predictor._market_prices(
                    bkr, pair, period, endtime, starttime=starttime)
                Predictor._print_market_history(
                    pair, period, marketprices, overwrite)

    @staticmethod
    def _learn(pair: Pair) -> None:
        """
        To create and store learn for existing strored market history

        Parameters
        ----------
        pair: Pair
            Pair to learn of
        """
        _cyan = '\033[36m' + '\033[30m'
        _normal = '\033[0m'
        n_feature = Predictor.get_n_feature()
        periods = Predictor.get_learn_periods()
        print(_MF.prefix() + _cyan + f"Learn pair '{pair.__str__().upper()}'" + _normal) if Predictor._DEBUG else None
        for period in periods:
            print(_MF.prefix() + _cyan + f"Learn for period '{int(period/60)}min'" + _normal) if Predictor._DEBUG else None
            marketprices = Predictor.load_market_history(pair, period)
            # Get datas
            high = marketprices.filter(['2']).values
            low = marketprices.filter(['3']).values
            close = marketprices.filter(['4']).values
            # Create model
            models = {
                Predictor.HIGH: Predictor.model(high, n_feature),
                Predictor.LOW: Predictor.model(low, n_feature),
                Predictor.CLOSE: Predictor.model(close, n_feature)
            }
            # Save
            [Predictor._print_model(pair, period, model_type, model) for model_type, model in models.items()]

    @staticmethod
    def model(prices: np.ndarray, n_feature: int) -> DeepLearning:
        Predictor._check_shape(prices, (prices.shape[0],1))
        xs, ys = Predictor.generate_dataset(prices, n_feature)
        dl = DeepLearning(ys, xs, train=True)
        return dl

    @staticmethod
    def generate_dataset(prices: np.ndarray, n_feature: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        To generate Xs and Ys with prices

        Pamaters:
        ---------
        prices: np.ndarray
            Prices of shape=(n_samples, 1)
        n_feature: int
            The number of feature to place in Xs (number of columns)
        
        Returns:
        --------
        xs: np.ndarray
            [0] Xs of shape=(n_samples-1, n_feature)
        ys: np.ndarray
            [1] Ys of shape=(n_samples-1, 1)
        """
        Predictor._check_shape(prices, (prices.shape[0],1))
        n_row = prices.shape[0]
        xs = []
        ys = []
        for i in range(n_feature, n_row):
            xs.append(prices[i-n_feature:i, 0])
            ys.append(prices[i, 0])
        return np.array(xs), np.array(ys).reshape((len(ys), 1))

    @staticmethod
    def _check_shape(values: np.ndarray, shape: tuple) -> None:
        if values.shape != shape:
            raise ValueError(
                f"Shape must be '{shape}', instead '{values.shape}'")

    @staticmethod
    def _print_model(pair: Pair, period: int, model_type: str, model: DeepLearning) -> None:
        json_file_path = Predictor.learn_file_path(pair, period, model_type, Predictor.get_learn_json_file())
        model_file_path = Predictor.learn_file_path(pair, period, model_type, Predictor.get_learn_model_file())
        coef_determ = model.get_coef_determination()
        model.save(json_file_path, model_file_path)
        config = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            Map.pair: pair,
            Map.period: period,
            Map.type: model_type,
            Map.shape: model.get_xs().shape,
            Map.coefficient: _MF.rate_to_str(coef_determ)
        }]
        conf_file_path = json_file_path.replace(Predictor.get_learn_json_file(), Predictor._FILE_LEARN_CONFIG)
        fields = list(config[0].keys())
        FileManager.write_csv(conf_file_path, fields, config, overwrite=True, make_dir=True)

    @staticmethod
    def load_model(pair: Pair, period: int, model_type: str) -> DeepLearning:
        json_file_path = Predictor.learn_file_path(pair, period, model_type, Predictor.get_learn_json_file())
        dl = DeepLearning.load(json_file_path)
        return dl

    @staticmethod
    def learn_file_path(pair: Pair, period: int, model_type: str, file_name: str) -> str:
        files = [Predictor.get_learn_json_file(), Predictor.get_learn_model_file()]
        if file_name not in files:
            raise ValueError(f"This file '{file_name}' is not a learn file")
        hist_types = [Predictor.CLOSE, Predictor.HIGH, Predictor.LOW]
        if model_type not in hist_types:
            raise ValueError(f"This history type '{file_name}' is not supported")
        file_path = Config.get(Config.DIR_STORAGE)
        file_path += Predictor._PATH_LEARN
        file_path += file_name
        pair_str = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        file_path = file_path.replace('$class', Predictor.__name__)
        file_path = file_path.replace('$model_type', model_type)
        file_path = file_path.replace('$pair', pair_str)
        file_path = file_path.replace('$period', str(period))
        return file_path

    # ——————————————————————————————————————————— STATIC FUNCTION LEARN UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION MARKET UP ————————————————————————————————————————————

    @staticmethod
    def _enough_period(bkr: Broker, pair: Pair) -> bool:
        """
        To check if there's enough period history on a Pair
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            Pair to check
        """
        enough_period = False
        max_period = max(Predictor.get_learn_periods())
        ds_min_size = Predictor.get_dataset_sizes()[Map.minimum]
        endtime = _MF.get_timestamp() - max_period * ds_min_size
        try:
            marketprice = Predictor._market_price(
                bkr, pair, max_period, n_preiod=1, endtime=endtime)
            enough_period = len(marketprice.get_closes()) > 0
        except Exception as error:
            enough_period = False
        return enough_period

    @staticmethod
    def _market_price(bkr: Broker, pair: Pair, period: int, n_preiod: int = _MARKET_MAX_N_PERIOD, starttime: int = None, endtime: int = None) -> MarketPrice:
        """
        To request MarketPrice to Broker

        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pair: Pair
            Pair to get market prices for
        period: int
            The period interval to request
        n_preiod: int
            The number of period to retrieve
        starttime: int
            The older time
        endtime: int
            The most recent time

        Returns
        -------
        return: MarketPrice
            MarketPrice from Broker's API
        """
        _bkr_cls = bkr.__class__.__name__
        mkt_params = Map({
            Map.pair: pair,
            Map.period: period,
            Map.begin_time: starttime,
            Map.end_time: endtime,
            Map.number: n_preiod
        })
        bkr_rq = bkr.generate_broker_request(
            _bkr_cls, BrokerRequest.RQ_MARKET_PRICE, mkt_params)
        bkr.request(bkr_rq)
        return bkr_rq.get_market_price()

    @staticmethod
    def _market_prices(bkr: Broker, pair: Pair, period: int, endtime: int, starttime: int = None, n_history: int = None) -> pd.DataFrame:
        """
        To download recurisively market history from starttime (older) to endtime (recent)
        NOTE: if there's not enough period between starttime and endtime, market history already downloaded is returned

        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pair: Pair
            Pair to get market prices for
        period: int
            The period interval to request
        n_preiod: int
            The number of period to retrieve
        starttime: int
            The older time
        endtime: int
            The most recent time
        n_history: int
            The number of history to retrieve

        Raise
        ------
        raise: Exception
            endtime is before actual time
        raise: Exception
            starttime is after or equal endtime
        raise: Exception
            if starttime and n_history are both None
        raise: Exception
            if starttime and n_history are both set

        Returns
        -------
            The market history from starttime (older) to endtime (recent)
        """
        unix_time = _MF.get_timestamp()
        if starttime == n_history == None:
            raise ValueError(f"starttime and n_history can't both be None")
        if (starttime != None) and (n_history != None):
            raise ValueError(
                f"starttime '{starttime}' and n_history '{n_history}' can't both be set")
        if (starttime is not None) and (not isinstance(starttime, int)) and (not isinstance(starttime, np.int64)):
            raise ValueError(
                f"Param 'starttime' must be type int, instead '{type(starttime)}'")
        if (not isinstance(endtime, int)) and (not isinstance(endtime, np.int64)):
            raise ValueError(
                f"Param 'endtime' must be type int, instead '{type(endtime)}'")
        if endtime > unix_time:
            raise Exception(
                f"The endtime must be lower than actual time, instead endtime'{endtime}' > actual'{unix_time}'")
        if (starttime is not None) and (starttime >= endtime):
            raise Exception(
                f"The starttime must be lower than endtime, instead starttime'{starttime}' >= endtime'{endtime}'")
        if starttime is None:
            starttime = endtime - (n_history * period)
            starttime = _MF.round_time(starttime, period)
        max_n_period = Predictor._MARKET_MAX_N_PERIOD
        endtime = _MF.round_time(endtime, period)
        endtime_copy = endtime
        marketprices = None
        end = False
        while not end:
            marketprice = Predictor._market_price(
                bkr, pair, period, n_preiod=max_n_period, endtime=endtime_copy)
            market = list(marketprice.get_market())
            market.reverse()
            martket_np = np.array(market, dtype=np.float64)
            marketprices = martket_np if marketprices is None else np.vstack(
                (martket_np, marketprices))
            endtime_copy -= period * max_n_period
            end = (martket_np.shape[0] < max_n_period) \
                or (endtime_copy <= starttime)
        marketprices_pd = pd.DataFrame(
            marketprices, columns=[str(i) for i in range(marketprices.shape[1])])
        marketprices_pd = marketprices_pd.drop_duplicates(
            subset='0', keep='last', ignore_index=True)
        marketprices_pd.iloc[:, 0] = (
            marketprices_pd.iloc[:, 0] / 1000).astype(int)
        marketprices_pd = marketprices_pd.sort_values(
            by='0', axis=0, ascending=True)
        n_row = int(abs(endtime - starttime) / period)
        marketprices_pd = marketprices_pd[-int(n_row):]
        return marketprices_pd

    @staticmethod
    def load_market_history(pair: Pair, period: int) -> pd.DataFrame:
        file_path = Predictor.history_file_path(pair, period)
        return pd.read_csv(file_path)

    @staticmethod
    def _print_market_history(pair: Pair, period: int, marketprices: pd.DataFrame, overwrite: bool) -> None:
        if period not in Predictor.get_learn_periods():
            raise Exception(f"This period '{period}' is not supported")
        file_path = Predictor.history_file_path(pair, period)
        content = marketprices.to_csv(index=False, header=overwrite)
        FileManager.write(file_path, content,
                          overwrite=overwrite, make_dir=True)

    @staticmethod
    def market_history_file_exist(pair: Pair, period: int) -> bool:
        """
        To check if a market history exist

        Parameters
        ----------
        pairs: List[Pair]
            List of Pair to train AI for
        periods: List[int]
            List of periods to train AI on

        Returns
        -------
            True if a market history exist else False
        """
        exist = False
        file_path = Predictor.history_file_path(pair, period)
        file_dir = _MF.regex_replace(r'[0-9]+.csv', '', file_path)
        file = file_path.replace(file_dir, '')
        try:
            files = FileManager.get_files(file_dir)
            exist = file in files
        except Exception as e:
            exist = False
        return exist

    @staticmethod
    def history_file_path(pair: Pair, period: int) -> str:
        file_path = Config.get(Config.DIR_STORAGE) + \
            Predictor._FILE_PATH_HISTORY
        pair_str = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        file_path = file_path.replace('$class', Predictor.__name__)
        file_path = file_path.replace('$pair', pair_str)
        file_path = file_path.replace('$period', str(period))
        return file_path

    @staticmethod
    def history_dir() -> str:
        history_dir = Config.get(Config.DIR_STORAGE) + \
            Predictor._FILE_PATH_HISTORY
        regex = '\$pair.*'
        history_dir = _MF.regex_replace(regex, '', history_dir)
        history_dir = history_dir.replace('$class', Predictor.__name__)
        return history_dir

    # ——————————————————————————————————————————— STATIC FUNCTION MARKET DOWN ——————————————————————————————————————————
