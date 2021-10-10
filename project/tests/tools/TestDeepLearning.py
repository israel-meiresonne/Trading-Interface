import unittest

import numpy as np
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.DeepLearning import DeepLearning
from model.tools.FileManager import FileManager
from model.tools.MyJson import MyJson
from model.tools.Predictor import Predictor


class TestDeepLearning(unittest.TestCase, DeepLearning):
    def setUp(self) -> None:
        file_path = 'tests/datas/tools/TestDeepLearning/test_save/scaled/'
        self.json_file_path = file_path + 'DeepLearning.json'
        self.model_file_path = file_path + 'keras_model'
        n_feature = 10
        n_row = 300
        prices = np.arange(0, n_row, 1).reshape((n_row, 1))
        self.xs, self.ys = Predictor.generate_dataset(prices, n_feature)
    
    def load(self, json_file_path: str = None) -> DeepLearning:
        json_file_path = self.json_file_path if json_file_path is None else json_file_path
        json = FileManager.read(json_file_path)
        dl = MyJson.json_decode(json)
        return dl
    
    def load_doge(self) -> DeepLearning:
        json_file_path = 'tests/datas/tools/TestDeepLearning/test_save/DOGE_USDT/DeepLearning.json'
        dl = self.load(json_file_path)
        return dl
    
    def doge_hist(self) -> np.ndarray:
        import pandas as pd
        project_dir = FileManager.get_project_directory()
        file_path = project_dir + 'tests/datas/tools/TestDeepLearning/DOGE_USDT/900000.csv'
        df_duplic = pd.read_csv(file_path)
        df = df_duplic.drop_duplicates(subset=['0'], keep='last', ignore_index=True)
        # Exctract closes
        data = df.filter(['4'])
        # dataframe to np.array
        dataset = data.values
        return dataset

    def test_constructor(self) -> None:
        dl = DeepLearning(self.ys, self.xs, train=False)
    
    def test_save(self) -> None:
        dl = DeepLearning(self.ys, self.xs, train=True)
        json_file_path = self.json_file_path
        model_file_path = self.model_file_path
        dl.save(json_file_path, model_file_path)
    
    def test_predict(self) -> None:
        dataset = self.doge_hist()
        # dataset = dataset[:1000,:]
        xs, ys = Predictor.generate_dataset(dataset, 60)
        n_sample = xs.shape[0]
        n_pass = int(n_sample * 0.8)
        n_futur = n_sample - n_pass
        xs_pass = xs[:n_pass,:]
        ys_futur = ys[n_pass:,:]
        dl = self.load_doge()
        if True:
            predictions = dl.predict(xs_pass, n_prediction=n_futur, mode=DeepLearning.PREDICT_MODE_RECURSIVE)
            print(f"Global coef: {dl.get_coef_determination()}")
            print(f"Recursive prediction coef: {dl.coef_determination(ys_futur, predictions)}")
        else:
            predictions = dl.predict(xs)
            print(f"Global coef: {dl.get_coef_determination()}")
            print(f"Recursive prediction coef: {dl.coef_determination(ys, predictions)}")
        self.plot(ys, predictions)
    
    def test_json_decode(self) -> None:
        dl = self.load()
        dl.get_model()
    
    def test_perso(self) -> None:
        dataset = self.doge_hist()
        xs, ys = Predictor.generate_dataset(dataset, 60)
        """
        dl = DeepLearning(ys, xs, train=True)
        json_file_path = 'tests/datas/tools/TestDeepLearning/test_save/DOGE_USDT/DeepLearning.json'
        model_file_path = 'tests/datas/tools/TestDeepLearning/test_save/DOGE_USDT/keras_model'
        dl.save(json_file_path, model_file_path)
        """
        dl = self.load_doge()
        predictions = dl.predict(xs)
        print(dl.get_coef_determination())
        self.plot(ys, predictions)

    def plot(self, ys, predictions) -> None:
        import matplotlib.pyplot as plt
        project_dir = FileManager.get_project_directory()
        plt.style.use('fivethirtyeight')
        plt.figure(figsize=(16,8))
        plt.title('Model')
        plt.xlabel('Date', fontsize=18)
        plt.ylabel('Close Price USDT', fontsize=18)
        plt.plot(ys)
        plt.plot(predictions)
        plt.legend(['Closes', 'Predictions'], loc='lower right')
        file_path = f'tests/datas/tools/TestDeepLearning/graphs/plot_{_MF.get_timestamp()}.png'
        plt.savefig(project_dir + file_path)

