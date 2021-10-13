import unittest

import numpy as np
from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor


class TestPredictor(unittest.TestCase, Predictor):
    def setUp(self) -> None:
        self.init_stage = None
        self.bkr = None
    
    def tearDown(self) -> None:
        self.broker_switch(False)

    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.init_stage = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
            self.bkr = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.init_stage
            self.bkr.close()
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self.bkr

    def test_predict(self) -> None:
        bkr = self.broker_switch(True)
        pair = Pair('ada/usdt')
        period = 60 * 60
        n_period = 1000
        predictor = Predictor(pair, period)
        mkt_obj = self._market_price(bkr, pair, period, n_period=n_period)
        highs = list(mkt_obj.get_highs())
        highs.reverse()
        highs = np.array(highs).reshape((len(highs), 1))
        lows = list(mkt_obj.get_lows())
        lows.reverse()
        lows = np.array(lows).reshape((len(lows), 1))
        closes = list(mkt_obj.get_closes())
        closes.reverse()
        closes = np.array(closes).reshape((len(closes), 1))
        mkts = {
            self.CLOSE: closes,
            self.HIGH: highs,
            self.LOW: lows
        }
        rows = []
        for model_type, prices in mkts.items():
            model = predictor.get_model(model_type)
            n_feature = model.n_feature()
            xs, ys = self.generate_dataset(prices, n_feature)
            predictions = model.predict(xs, fixe_offset=True, xs_offset=xs, ys_offset=ys)
            model_coef = model.get_coef_determination()
            market_coef = model.coef_determination(ys, predictions)
            print(f"{model_type.upper()} Global coef: {model_coef}")
            print(f"{model_type.upper()} coef: {market_coef}")
            print_dir = self.plot(ys, predictions, f'{pair.format()}_plot_{model_type}_')
            row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                Map.pair: pair,
                Map.type: model_type,
                Map.shape: xs.shape,
                'offset': model.get_offset_mean(),
                Map.model: _MF.rate_to_str(model_coef),
                Map.market: _MF.rate_to_str(market_coef)
            }
            rows.append(row)
        print_file_path = print_dir + 'config.csv'
        fields = list(rows[0].keys())
        FileManager.write_csv(print_file_path, fields, rows, overwrite=True, make_dir=False)
        self.broker_switch(False)
    
    def test_add_learns(self) -> None:
        from model.tools.MarketPrice import MarketPrice
        from model.tools.Asset import Asset
        bkr = self.broker_switch(True)
        """
        n_row2 = 5*10**(4)
        self._DATASET_SIZES[Map.minimum] = n_row2
        self._DATASET_SIZES[Map.maximum] = n_row2
        self._LEARN_PERIODS = [60 * 5]
        """
        # pairs = MarketPrice.get_spot_pairs(bkr.__class__.__name__, Asset('USDT'))
        pairs = [Pair('bch/usdt')]
        self.add_learns(bkr, pairs)
        self.broker_switch(False)
    
    def test_maintain_market_history(self) -> None:
        bkr = self.broker_switch(True)
        self._DATASET_SIZES[Map.minimum] = 1 * 10**(3)
        self._DATASET_SIZES[Map.maximum] = 250
        self._maintain_market_history(bkr, Pair('DOGE/USDT'))
        self.broker_switch(False)
    
    def test_learn(self) -> None:
        pair = Pair('coti/usdt')
        self._learn(pair)

    def test_model(self) -> None:
        n_feature = self.get_n_feature()
        n_row = 100
        prices = np.arange(0, n_row, 1).reshape((n_row, 1))
        model = self.model(prices, n_feature)

    def test_generate_dataset(self) -> None:
        n_feature = 10
        n_row = 300
        prices = np.arange(0, n_row, 1).reshape((n_row, 1))
        xs, ys = self.generate_dataset(prices, n_feature)
        # Check shape
        self.assertTupleEqual((n_row-n_feature, n_feature), xs.shape)
        self.assertTupleEqual((n_row-n_feature, 1), ys.shape)
        # Check last column
        sum_last_col = sum([xs[i,-1] - xs[i-1,-1] for i in range(1, xs.shape[0])])
        self.assertEqual(n_row-n_feature-1, sum_last_col)
        # Check ys
        sum_ys = sum([ys[i,-1] - ys[i-1,-1] for i in range(1, ys.shape[0])])
        self.assertEqual(n_row-n_feature-1, sum_ys)
        # Check last column and ys
        sum_xs_to_ys = sum([ys[i,-1] - xs[i,-1] for i in range(ys.shape[0])])
        self.assertEqual(n_row-n_feature, sum_xs_to_ys)
        # Prices is list
        prices = [i for i in range(n_row)]
        ys_exp1 = [i for i in range(n_feature, n_row)]
        xs, ys = self.generate_dataset(prices, n_feature)
        self.assertTupleEqual((n_row-n_feature, n_feature), xs.shape)
        self.assertTupleEqual((n_row-n_feature, 1), ys.shape)
        self.assertListEqual(ys_exp1, ys[:,0].tolist())

    def test_learned_pairs(self) -> None:
        pairs = self.learned_pairs()
        self.assertIsInstance(pairs, list)
        self.assertIsInstance(pairs[0], Pair)

    def test_learn_dir(self) -> None:
        exp1 = 'content/storage/Predictor/learns/'
        result1 = self.learn_dir()
        self.assertEqual(exp1, result1)
        self.assertIsInstance(FileManager.get_dirs(result1), list)

    def test_market_price_to_np(self) -> None:
        bkr = self.broker_switch(True)
        pair = Pair('DOGE/USDT')
        period = 60 * 5
        n_period = 100
        n_feature = self.get_n_feature()
        marketprice = self._market_price(bkr, pair, period, n_period=n_period)
        xs = self.market_price_to_np(marketprice, self.HIGH, n_feature)
        self.assertEqual(n_feature, xs.size)
        self.assertEqual(marketprice.get_highs()[0], xs[0,-1])
        self.assertEqual(marketprice.get_highs()[n_feature-1], xs[0,0])
        self.assertTupleEqual((1, n_feature), xs.shape)
        self.broker_switch(False)
    
    def test_enough_period(self) -> None:
        bnc = self.broker_switch(True)
        # Change FIDA with new listed token if test fail
        self.assertFalse(self._enough_period(bnc, Pair('FIDA/USDT')))
        self.assertTrue(self._enough_period(bnc, Pair('DOGE/USDT')))
        bnc = self.broker_switch(False)

    def test_market_prices(self) -> None:
        bnc = self.broker_switch(True)
        pair = Pair('DOGE/USDT')
        period = 60 * 3
        n_period = 5*10**(3)
        unix_time = _MF.get_timestamp()
        endtime = _MF.round_time(unix_time, period)
        if True:
            starttime = unix_time - n_period * period
            marketprices = self._market_prices(
                bnc, pair, period, endtime, starttime=starttime)
            times_np = marketprices['0'].to_numpy()
            # Period interval is correct
            intervals = [(times_np[i] - times_np[i-1])
                        for i in range(1, len(times_np))]
            mean_period = sum(intervals) / len(intervals)
            self.assertEqual(period, _MF.round_time(mean_period, period))
            # Row sorted from olders ([0]) to most recents ([-1])
            n_rows_increasing = sum([times_np[i] > times_np[i-1]
                                    for i in range(1, len(times_np))])
            self.assertEqual(len(times_np) - 1, n_rows_increasing)
        if True:
            # Number row is bellow API's max
            n_row1 = 250
            self._DATASET_SIZES[Map.minimum] = 1 * 10**(3)
            self._DATASET_SIZES[Map.maximum] = n_row1
            mkt1 = self._market_prices(bnc, pair, period, endtime, n_history=n_row1)
            self.assertEqual(n_row1, len(mkt1))
            # Number row is over API's max
            n_row2 = 1350
            self._DATASET_SIZES[Map.minimum] = 1 * 10**(3)
            self._DATASET_SIZES[Map.maximum] = n_row2
            mkt2 = self._market_prices(bnc, pair, period, endtime, n_history=n_row2)
            self.assertEqual(n_row2, len(mkt2))
        self.broker_switch(False)

    def test_market_history_exist(self) -> None:
        self.assertTrue(self.market_history_file_exist(Pair('TEST/USDT'), 123))
        self.assertFalse(self.market_history_file_exist(Pair('FALSE/USDT'), 123))

    def test_history_file_path(self) -> None:
        pair = Pair("DOGE/USDT")
        period = 60 * 15
        exp1 = Config.get(Config.DIR_STORAGE) + \
            f"{Predictor.__name__}/market-histories/{pair.format(Pair.FORMAT_UNDERSCORE).upper()}/{period}.csv"
        result1 = Predictor.history_file_path(pair, period)
        self.assertEqual(exp1, result1)
    
    def test_history_dir(self) -> None:
        storage_dir = Config.get(Config.DIR_STORAGE)
        exp1 = storage_dir + f'{Predictor.__name__}/market-histories/'
        result1 = self.history_dir()
        self.assertEqual(exp1, result1)
    
    def test_history_file_path(self) -> None:
        pair = Pair("DOGE/USDT")
        period = 60 * 15
        hist_type = Map.close
        exp1 = f'content/storage/Predictor/learns/DOGE_USDT/900/{hist_type}/DeepLearning.json'
        result1 = Predictor.learn_file_path(pair, period, hist_type, Predictor.get_learn_json_file())
        self.assertEqual(exp1, result1)
        hist_type = Map.low
        exp2 = f'content/storage/Predictor/learns/DOGE_USDT/900/{hist_type}/model.xyz'
        result2 = Predictor.learn_file_path(pair, period, hist_type, Predictor.get_learn_model_file())
        self.assertEqual(exp2, result2)
    
    def test_json_encode_decode(self) -> None:
        pair = Pair("DOGE/USDT")
        period = 60 * 60
        predictor = Predictor(pair, period)
        model = predictor.get_model(Predictor.CLOSE)
        model = predictor.get_model(Predictor.HIGH)
        model = predictor.get_model(Predictor.LOW)
        json_str = predictor.json_encode()
        new_predictor = MyJson.json_decode(json_str)
        self.assertEqual(pair, new_predictor.get_pair())
        self.assertEqual(period, new_predictor.get_period())
        self.assertNotEqual(id(predictor), id(new_predictor))

    def plot(self, ys, predictions, plot_name: str = 'plot_') -> str:
        import matplotlib.pyplot as plt
        project_dir = FileManager.get_project_directory()
        plt.style.use('fivethirtyeight')
        plt.figure(figsize=(16,8))
        plt.title('Model')
        plt.xlabel('Date', fontsize=18)
        plt.ylabel('Prices USDT', fontsize=18)
        plt.plot(ys)
        plt.plot(predictions)
        plt.legend(['Prices', 'Predictions'], loc='lower right')
        path = f'tests/datas/tools/{self.__class__.__name__}/graphs/{Config.get(Config.SESSION_ID)}/'
        file_path = path + f'{plot_name}.png'
        FileManager.make_directory(path)
        plt.savefig(project_dir + file_path)
        return path
    
    def resume_learn(self) -> None:
        _back_cyan = '\033[46m' + '\033[30m'
        _normal = '\033[0m'
        hist_dir = 'content/storage/Predictor/market-histories/'
        learn_dir = 'content/storage/Predictor/learns/'
        hist_pairs_str = FileManager.get_dirs(hist_dir, make_dir=True)
        learn_pairs_str = FileManager.get_dirs(learn_dir, make_dir=True)
        pairs_to_learn = [Pair(pair_str.replace('_', '/')) for pair_str in hist_pairs_str if pair_str not in learn_pairs_str]
        # pair = Pair('DOGE/USDT')
        for pair in pairs_to_learn:
            print(_MF.prefix() + _back_cyan + f"Start learning '{pair.__str__().upper()}'..." + _normal)
            self._learn(pair)
            print(_MF.prefix() + _back_cyan + f"End learning '{pair.__str__().upper()}'" + _normal)
