from typing import List, Tuple, Union

import numpy as np
import pandas as pd
from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.BrokerRequest import BrokerRequest
from model.tools.DeepLearning import DeepLearning
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair


class Predictor(MyJson):
    _DEBUG = True
    _MARKET_MAX_N_PERIOD = 1000
    _N_FEATURE = 60
    _FILE_PATH_HISTORY = Config.get(Config.PREDICTOR_FILE_PATH_HISTORY)
    _PATH_LEARN = Config.get(Config.PREDICTOR_PATH_LEARN)
    _FILE_LEARN_JSON = f'{DeepLearning.__name__}.json'
    _FILE_LEARN_MODEL = 'keras_model.xyz'
    _FILE_LEARN_CONFIG = 'config.csv'
    _LEARN_PERIODS = [
        60 * 60
    ]
    _DATASET_SIZES = {
        Map.minimum: 1*10**(4),
        Map.maximum: 1.6*10**(4)
    }
    _LOADED_MODELS = Map()
    CLOSE = Map.close
    HIGH = Map.high
    LOW = Map.low
    _HIGH_OCCUP_N_MEAN = 50
    _HIGH_OCCUP_N_SCORE = 3

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
    
    def get_model(self, price_type: str) -> DeepLearning:
        models = self.get_models()
        if price_type not in models.get_keys():
            raise ValueError(f"This price type '{price_type}' is not supported")
        model = models.get(price_type)
        if model is None:
            pair = self.get_pair()
            period = self.get_period()
            model = self.load_model(pair, period, price_type=price_type)
            models.put(model, price_type)
        return model

    def predict(self, prices: np.ndarray, price_type: str) -> np.ndarray:
        """
        To predict next market price

        Parameters:
        -----------
        market: MarketPrice
            Market prices with shape=(n_sample, n_feature)
        price_type: str
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
        prices = list(eval(f"market.get_{price_type}s()"))
        prices.reverse()
        """
        model = self.get_model(price_type)
        predictions = model.predict(prices)
        return predictions

    def score_high_occupation(self, marketprice: MarketPrice, n_score: int = _HIGH_OCCUP_N_SCORE, n_mean: int = _HIGH_OCCUP_N_MEAN) -> float:
        closes = list(marketprice.get_closes())
        closes.reverse()
        highs = list(marketprice.get_highs())
        highs.reverse()
        model = self.get_model(self.HIGH)
        n_feature = model.n_feature()
        x_highs, y_highs = self.generate_dataset(highs, n_feature)
        pred_y_highs = model.predict(x_highs, fixe_offset=True, xs_offset=x_highs, ys_offset=y_highs)
        x_closes, _ = self.generate_dataset(closes, n_feature)
        last_closes = x_closes[:,-1]
        pred_y_highs = pred_y_highs.ravel()
        y_highs = y_highs.ravel()
        occups = (y_highs - last_closes)/(pred_y_highs - last_closes)
        occups = [1 if c > 1 else c for c in occups]
        occups = np.array([0 if c < 0 else c for c in occups])
        times = []
        n_occup = occups.shape[0]
        max_idx = n_occup - n_score
        for i in range(max_idx):
            reached_highs = y_highs[i:i+n_score]
            max_high = max(reached_highs)
            idx = np.where(reached_highs == max_high)[0][0]
            period_coef = idx + 1
            times.append(period_coef)
        times = np.array(times)
        scores = occups[:max_idx]/times
        mean_score = sum(scores[-n_mean:])/n_mean
        return mean_score

    def _json_encode_prepare(self) -> None:
        models = self.get_models()
        keys = models.get_keys()
        [models.put(None, key) for key in keys]
    
    # ——————————————————————————————————————————— STATIC GETTTER DOWN ——————————————————————————————————————————————————

    @staticmethod
    def get_learn_periods() -> list:
        return Predictor._LEARN_PERIODS

    @staticmethod
    def get_dataset_sizes() -> dict:
        return Predictor._DATASET_SIZES
    
    @staticmethod
    def get_loaded_models() -> Map:
        return Predictor._LOADED_MODELS

    @staticmethod
    def get_n_feature() -> int:
        return Predictor._N_FEATURE
        
    @staticmethod
    def get_learn_json_file() -> str:
        return Predictor._FILE_LEARN_JSON
        
    @staticmethod
    def get_learn_model_file() -> str:
        return Predictor._FILE_LEARN_MODEL
    
    @staticmethod
    def get_learn_path(stock_path: bool = True) -> str:
        """
        To get path where models are stored
            - 'stock' is space to work on model
            - 'active' is space used by running sessions

        Parameters:
        -----------
        stock_path: bool = True
            Set True to get path to stock of models else False for path to active models
        
        Return:
        -------
        return: str
            The path where models are stored
        """
        new_str = 'stock' if stock_path else 'active'
        old_str = Config.TOKEN_PREDICTOR_LEARN_PATH
        new_path = Predictor._PATH_LEARN.replace(old_str, new_str)
        return new_path

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
    def update_market_histories(bkr: Broker, fiat_asset: Asset, pairs: List[Pair] = None, periods: List[int] = None) -> None:
        """
        To create new histories if enought period and push most recent period in existing histories

        Parameters:
        ----------
        bkr: Broker
            Access to a Broker's API
        fiat_asset: Asset
            The right asset to use on Pair
        pairs: List[Pair] = None
            List of Pair
        periods: List[int] = None
            List of period interval in second
        """
        bkr_cls = bkr.__class__.__name__
        pairs = pairs if pairs is not None else MarketPrice.get_spot_pairs(bkr_cls, fiat_asset)
        periods = periods if periods is not None else Predictor.get_learn_periods()
        starttime = _MF.get_timestamp()
        n_turn = len(pairs)
        i = 0
        for pair in pairs:
            turn = i + 1
            print(_MF.loop_progression(starttime, turn, n_turn, pair.__str__().upper())) if Predictor._DEBUG else None
            if Predictor._enough_period(bkr, pair, periods):
                Predictor._maintain_market_history(bkr, pair, periods)
            i += 1
    
    @staticmethod
    def update_learns(pairs: List[Pair] = None, periods: List[int] = None) -> None:
        """
        To generate learn model on market hisories for given period

        Parameters:
        ----------
        periods: List[int] = None
            List of period interval in second
        pairs: List[Pair] = None
            List of Pair
        """
        periods = periods if periods is not None else Predictor.get_learn_periods()
        pairs = pairs if pairs is not None else Predictor.market_history_pairs()
        starttime = _MF.get_timestamp()
        n_turn = len(pairs)
        i = 0
        for pair in pairs:
            turn = i + 1
            print(_MF.loop_progression(starttime, turn, n_turn, pair.__str__().upper())) if Predictor._DEBUG else None
            for period in periods:
                if Predictor.exist_market_history(pair, period):
                    Predictor._learn(pair, [period])
            i += 1

    @staticmethod
    def _maintain_market_history(bkr: Broker, pair: Pair, periods: List[int] = None) -> None:
        """
        To create new market history if there's none else add histories since last add

        Parameters
        ----------
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            Pair to download
        periods: List[int] = None
            List of period interval in second
        """
        _cyan = '\033[36m'
        _normal = '\033[0m'
        periods = periods if periods is not None else Predictor.get_learn_periods()
        unix_time = _MF.get_timestamp()
        for period in periods:
            endtime = _MF.round_time(unix_time, period)
            if Predictor.exist_market_history(pair, period):
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
    def _learn(pair: Pair, periods: List[int] = None) -> None:
        """
        To create and store learn model for existing market history

        Parameters
        ----------
        pair: Pair
            Pair to learn of
        periods: List[int] = None
            List of period interval in second
        """
        _cyan = '\033[36m' + '\033[30m'
        _normal = '\033[0m'
        n_feature = Predictor.get_n_feature()
        periods = periods if periods is not None else Predictor.get_learn_periods()
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
            [Predictor._print_model(pair, period, price_type, model) for price_type, model in models.items()]

    @staticmethod
    def model(prices: np.ndarray, n_feature: int) -> DeepLearning:
        Predictor._check_shape(prices, (prices.shape[0],1))
        xs, ys = Predictor.generate_dataset(prices, n_feature)
        dl = DeepLearning(ys, xs, train=True)
        return dl

    @staticmethod
    def generate_dataset(prices: Union[list[float], np.ndarray], n_feature: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        To generate Xs and Ys with prices

        Pamaters:
        ---------
        prices: Union[list[float], np.ndarray]
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
        if isinstance(prices, list):
            prices = np.array(prices).reshape((len(prices), 1))
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
    def _print_model(pair: Pair, period: int, price_type: str, model: DeepLearning) -> None:
        stock_path = True
        json_file_path = Predictor.learn_file_path(pair, period, price_type, Predictor.get_learn_json_file(), stock_path=stock_path)
        model_file_path = Predictor.learn_file_path(pair, period, price_type, Predictor.get_learn_model_file(), stock_path=stock_path)
        coef_determ = model.get_coef_determination()
        model.save(json_file_path, model_file_path)
        config = [{
            Map.date: _MF.unix_to_date(_MF.get_timestamp()),
            Map.pair: pair,
            Map.period: period,
            Map.type: price_type,
            Map.shape: model.get_xs().shape,
            Map.coefficient: _MF.rate_to_str(coef_determ)
        }]
        conf_file_path = json_file_path.replace(Predictor.get_learn_json_file(), Predictor._FILE_LEARN_CONFIG)
        fields = list(config[0].keys())
        FileManager.write_csv(conf_file_path, fields, config, overwrite=True, make_dir=True)

    @staticmethod
    def load_model(pair: Pair, period: int, price_type: str) -> DeepLearning:
        model_key = f"{pair.__str__()}_{period}_{price_type}"
        loaded_models = Predictor.get_loaded_models()
        dl = loaded_models.get(model_key)
        if dl is None:
            file_name = Predictor.get_learn_json_file()
            json_file_path = Predictor.learn_file_path(pair, period, price_type, file_name=file_name, stock_path=True)
            dl = DeepLearning.load(json_file_path)
            loaded_models.put(dl, model_key)
        return dl

    @staticmethod
    def learned_pairs(stock_path: bool) -> List[Pair]:
        """
        To get list of Pair with learned model

        Parameters:
        -----------
        stock_path: bool
            Set True to get path to stock of models else False for path to active models

        Returns:
        --------
        return: List[Pair]
            List of Pair with learned model
        """
        pair_path = Predictor.learn_dir(stock_path)
        pairs_str = FileManager.get_dirs(pair_path, make_dir=True)
        pairs = [Pair(pair_str.replace(Pair.UNDERSCORE, Pair.SEPARATOR)) for pair_str in pairs_str]
        return pairs

    @staticmethod
    def learn_dir(stock_path: bool) -> str:
        """
        To get directory where model of pair are stored
        ie: 'content/storage/Predictor/learns/'

        Parameters:
        -----------
        stock_path: bool
            Set True to get path to stock of models else False for path to active models
        """
        learn_path = Config.get(Config.DIR_STORAGE)
        learn_path += Predictor.get_learn_path(stock_path)
        learn_path = learn_path.replace('$class', Predictor.__name__)
        regex = r'\$pair.*'
        learn_path = _MF.regex_replace(regex, '', learn_path)
        return learn_path

    @staticmethod
    def learn_file_path(pair: Pair, period: int, price_type: str, file_name: str, stock_path: bool) -> str:
        """
        To get path to file that contain model for a given Pair

        Parameters:
        -----------
        pair: Pair
            The Pair of the model to get
        period: int
            The period interval of the model to get
        price_type: str
            Predictor.[HIGHT, LOW, CLOSE]
        file_name: str
            Predictor.[_FILE_LEARN_JSON, _FILE_LEARN_MODEL]
        stock_path: bool
            Set True to get path to stock of models else False for path to active models
        """
        files = [Predictor.get_learn_json_file(), Predictor.get_learn_model_file()]
        if file_name not in files:
            raise ValueError(f"This file '{file_name}' is not a learn file")
        hist_types = [Predictor.CLOSE, Predictor.HIGH, Predictor.LOW]
        if price_type not in hist_types:
            raise ValueError(f"This history type '{file_name}' is not supported")
        file_path = Config.get(Config.DIR_STORAGE)
        file_path += Predictor.get_learn_path(stock_path)
        file_path += file_name
        pair_str = pair.format(Pair.FORMAT_UNDERSCORE).upper()
        file_path = file_path.replace('$class', Predictor.__name__)
        file_path = file_path.replace('$price_type', price_type)
        file_path = file_path.replace('$pair', pair_str)
        file_path = file_path.replace('$period', str(period))
        return file_path

    # ——————————————————————————————————————————— STATIC FUNCTION LEARN UP —————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION MARKET UP ————————————————————————————————————————————

    @staticmethod
    def market_history_pairs() -> List[Pair]:
        """
        To get list of Pair with a market history
        
        Returns:
        --------
        return: List[Pair]
            List of Pair with a market history
        """
        pair_histories_dir = Predictor.history_dir()
        pairs_str = FileManager.get_dirs(pair_histories_dir)
        pairs = [Pair(pair_str.replace(Pair.UNDERSCORE, Pair.SEPARATOR)) for pair_str in pairs_str]
        return pairs

    @staticmethod
    def market_price_to_np(marketprice: MarketPrice, price_type: str, n_feature: int) -> np.ndarray:
        """
        To prepare list of MarketPrice to be predicted

        Parameters:
        -----------
        marketprice: MarketPrice
            MarketPrice
        price_type: str
            The list or MarketPrice to convert
        n_feature: int
            The number of feature neccessary to predict

        Returns:
        --------
        return: np.ndarray
            list of MarketPrice prepared to be predicted shape=(1, n_feature)
        """
        prices = list(eval(f"marketprice.get_{price_type}s()"))
        prices.reverse()
        return np.array(prices[-n_feature:]).reshape((1, n_feature))

    @staticmethod
    def _enough_period(bkr: Broker, pair: Pair, periods: List[int] = None) -> bool:
        """
        To check if there's enough period history on a Pair
        bkr: Broker
            Access to a Broker's API
        pairs: List[Pair]
            Pair to check
        periods: List[int] = None
            List of period interval in second
        """
        enough_period = False
        periods = periods if periods is not None else Predictor.get_learn_periods()
        max_period = max(periods)
        ds_min_size = Predictor.get_dataset_sizes()[Map.minimum]
        endtime = _MF.get_timestamp() - max_period * ds_min_size
        try:
            marketprice = Predictor._market_price(
                bkr, pair, max_period, n_period=1, endtime=endtime)
            enough_period = len(marketprice.get_closes()) > 0
        except Exception as error:
            enough_period = False
        return enough_period

    @staticmethod
    def _market_price(bkr: Broker, pair: Pair, period: int, n_period: int = _MARKET_MAX_N_PERIOD, starttime: int = None, endtime: int = None) -> MarketPrice:
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
        n_period: int
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
            Map.number: n_period
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
        n_period: int
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
                bkr, pair, period, n_period=max_n_period, endtime=endtime_copy)
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
        def sec_to_milli(time: int) -> int:
            return int(time * 1000)
        file_path = Predictor.history_file_path(pair, period)
        project_dir = FileManager.get_project_directory()
        market_hist = pd.read_csv(project_dir + file_path)
        market_hist = _MF.df_apply(market_hist, ['0'], sec_to_milli)
        return market_hist

    @staticmethod
    def _print_market_history(pair: Pair, period: int, marketprices: pd.DataFrame, overwrite: bool) -> None:
        # if period not in Predictor.get_learn_periods():
        #     raise Exception(f"This period '{period}' is not supported")
        file_path = Predictor.history_file_path(pair, period)
        content = marketprices.to_csv(index=False, header=overwrite)
        FileManager.write(file_path, content,
                          overwrite=overwrite, make_dir=True)

    @staticmethod
    def exist_market_history(pair: Pair, period: int) -> bool:
        """
        To check if a market history exist by checking  if file exist

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
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Predictor(Pair('@json/@json'), -1)
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
