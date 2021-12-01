from typing import List, Union

import numpy as np
from keras.layers import LSTM, Dense
from keras.models import Sequential, load_model
from sklearn.preprocessing import MinMaxScaler
from model.tools.FileManager import FileManager

from model.tools.MyJson import MyJson


class DeepLearning(MyJson):
    PREDICT_MODE_MODEL = 'PREDICT_MODE_MODEL'
    PREDICT_MODE_RECURSIVE = 'PREDICT_MODE_RECURSIVE'

    def __init__(self, ys: Union[List[list], np.ndarray], xs: Union[List[list], np.ndarray], train: bool = True) -> None:
        self.__ys = None
        self.__ys_predicted = None
        self.__xs = None
        self.__offset_mean = None
        self.__coef_determination = None
        self.__scaler = None
        self.__model = None
        self.__model_file_path = None
        self._set_dataset(ys, xs)
        self.train() if train else None

    def _set_dataset(self, ys: Union[List[list], np.ndarray], xs: Union[List[list], np.ndarray]) -> None:
        ys = np.array(ys)
        if (ys.shape != (ys.shape[0],)) and (ys.shape != (ys.shape[0], 1)):
            raise ValueError(
                f"Dataset's Ys must have shape '{(ys.shape[0],)}' or '{(ys.shape[0],1)}', instead '{ys.shape}'")
        ys = ys.reshape(ys.shape[0], 1)
        xs = np.array(xs)
        xs = xs.reshape(xs.shape[0], 1) if xs.shape == (xs.shape[0],) else xs
        if xs.shape != (ys.shape[0], xs.shape[1]):
            raise ValueError(
                f"Dataset's Xs must have shape '{(ys.shape[0],xs.shape[1])}', instead '{xs.shape}'")
        self.__ys = ys
        self.__xs = xs

    def get_ys(self) -> np.ndarray:
        return self.__ys

    def get_ys_predicted(self) -> np.ndarray:
        if self.__ys_predicted is None:
            self.__ys_predicted = self.predict(self.get_xs(), fixe_offset=False)
        return self.__ys_predicted

    def get_xs(self) -> np.ndarray:
        return self.__xs
    
    def get_offset_mean(self) -> float:
        if self.__offset_mean is None:
            ys = self.get_ys()
            ys_predicted = self.get_ys_predicted()
            self.__offset_mean = DeepLearning.offset_mean(ys, ys_predicted)
        return self.__offset_mean
    
    def _reset_scaler(self) -> None:
        self.__scaler = None

    def get_scaler(self) -> MinMaxScaler:
        if self.__scaler is None:
            scaler = MinMaxScaler(feature_range=(0, 1))
            xs = self.get_xs()
            ys = self.get_ys()
            values = np.hstack((xs[0,:], xs[1:,-1], ys[-1,:]))
            values = values.reshape((values.size, 1))
            scaler.fit(values)
            self.__scaler = scaler
        return self.__scaler
    
    def _init_model(self, model: Sequential) -> None:
        self.__model = model

    def _set_model(self) -> None:
        if self.__model is not None:
            raise Exception("The model is set already")
        ys_scaled = self.scaler_transforme(self.get_ys())
        xs_scaled = self.scaler_transforme(self.get_xs())
        self.__model = self.model(ys_scaled, xs_scaled)

    def get_model(self) -> Sequential:
        return self.__model
    
    def _set_model_file_path(self, model_file_path: str) -> None:
        self.__model_file_path = model_file_path
    
    def get_model_file_path(self) -> None:
        return self.__model_file_path.replace('learns/', 'learns/active/')
    
    def _freeze_class(self) -> None:
        """
        To remove objects than can't be serialized into json
        """
        model_path = self.get_model_file_path()
        if model_path is None:
            raise Exception("The save file path must be set before freeze model")
        self.__model = model_path
        self._reset_scaler()
    
    def get_coef_determination(self) -> float:
        if self.__coef_determination is None:
            ys_predicted = self.get_ys_predicted()
            self.__coef_determination = float(self.coef_determination(self.get_ys(), ys_predicted))
        return self.__coef_determination
    
    def n_feature(self) -> int:
        return int(self.get_xs().shape[1])

    # ——————————————————————————————————————————— STATIC SCALER DOWN ———————————————————————————————————————————————————

    def scaler_transforme(self, values: np.ndarray) -> np.ndarray:
        """
        To scale given values without change its shape

        Parameters:
        -----------
        values: np.ndarray
            Values to scale
        
        Returns:
        --------
            Values scaled
        """
        # values_flattened = values.reshape((values.size, 1))
        # values_flattened_scaled = self.get_scaler().transform(values_flattened)
        # values_scaled = values_flattened_scaled.reshape(values.shape)
        # return values_scaled
        return values
    
    def scaler_inverse_transform(self, values_scaled: np.ndarray) -> np.ndarray:
        """
        To unscale given values without change its shape

        Parameters:
        -----------
        values_scaled: np.ndarray
            Values to unscale
        
        Returns:
        --------
            Values unscaled
        """
        # values_scaled_flattened = values_scaled.reshape((values_scaled.size, 1))
        # values_flattened = self.get_scaler().inverse_transform(values_scaled_flattened)
        # values = values_flattened.reshape(values_scaled.shape)
        # return values
        return values_scaled

    # ——————————————————————————————————————————— STATIC SCALER UP —————————————————————————————————————————————————————

    def is_trained(self) -> bool:
        return self.get_model() is not None

    def train(self) -> None:
        self._set_model() if not self.is_trained() else None

    def predict(self, xs: Union[List[list], np.ndarray], mode: str = PREDICT_MODE_MODEL, n_prediction: int = None, fixe_offset: bool = True, xs_offset: Union[List[list], np.ndarray] = None, ys_offset: Union[List[list], np.ndarray] = None) -> np.ndarray:
        """
        To predict Ys

        Parameters
        ----------
        xs: Union[List[list], np.ndarray]
            The Xs to use to predict Ys
        mode: str = PREDICT_MODE_MODEL
            If mode=PREDICT_MODE_MODEL function return Ys of each row in xs.
            If mode=PREDICT_MODE_RECURSIVE function will use first line to build recursively n_prediction
        n_prediction: int = None
            If mode=PREDICT_MODE_RECURSIVE the number of prediction to build recursively
        fixe_offset: bool = True
            Set True to fixe prediction with mean offset else False
        xs_offset: Union[List[list], np.ndarray] = None
            Xs to use to evaluate the offset to  apply on prediction if fixe_offset=True
        ys_offset: Union[List[list], np.ndarray] = None
            Ys to use to evaluate the offset to  apply on prediction if fixe_offset=True

        Raise
        -----
        raise: ValueException
            xs don't have same number of column than self.__xs
        raise: ValueException
            if mode=PREDICT_MODE_RECURSIVE and n_prediction is not set
        raise: Exception
            if model is not train
        raise: ValueException
            if xs_offset or ys_offset have wrong shape

        Return
        ------
        return: np.ndarray
            Predicted Ys with shape (n_row, 1)
        """
        xs = np.array(xs)
        have_offset_datas = xs_offset is not None
        if xs.shape[1] != self.get_xs().shape[1]:
            raise ValueError(
                f"xs must have '{self.get_xs().shape[1]}' column, instead '{xs.shape[1]}'")
        if have_offset_datas:
            xs_offset = np.array(xs_offset)
            ys_offset = np.array(ys_offset)
            if xs_offset.shape[1] != self.get_xs().shape[1]:
                raise ValueError(
                    f"xs_offset must have '{self.get_xs().shape[1]}' column, instead '{xs_offset.shape[1]}'")
            if ys_offset.shape != (xs_offset.shape[0], 1):
                raise ValueError(
                    f"ys_offset must have shape '{(xs_offset.shape[0], 1)}', instead '{ys_offset.shape}'")
        if not self.is_trained():
            raise Exception("The model must be train before predict")
        if (mode == self.PREDICT_MODE_RECURSIVE) and (n_prediction is None):
            raise ValueError(
                "The n_prediction must be set if mode=PREDICT_MODE_RECURSIVE")
        predictions = None
        if mode == self.PREDICT_MODE_MODEL:
            predictions = self._predict_model(xs)
            if fixe_offset and have_offset_datas:
                predictions_offset = self._predict_model(xs_offset)
                offset_mean = self.offset_mean(ys_offset, predictions_offset)
                predictions = predictions + offset_mean
        elif mode == self.PREDICT_MODE_RECURSIVE:
            raise Exception(f"This prediction mode '{mode}' is not supported")
            predictions = self._predict_recursive(xs, n_prediction)
        else:
            raise ValueError(f"This prediction mode '{mode}' is not supported")
        predictions = predictions.reshape((predictions.shape[0], 1))
        predictions = predictions + self.get_offset_mean() if fixe_offset and (not have_offset_datas) else predictions
        return predictions

    def _predict_model(self, xs: np.ndarray) -> np.ndarray:
        model = self.get_model()
        xs_scaled = self.scaler_transforme(xs)
        xs_scaled_3d = xs.reshape((xs_scaled.shape[0], xs_scaled.shape[1], 1))
        predictions = model.predict(xs_scaled_3d)
        predictions = self.scaler_inverse_transform(predictions)
        return predictions

    def _predict_recursive(self, xs: np.ndarray, n_prediction: int) -> np.ndarray:
        model = self.get_model()
        xs_scaled = self.scaler_transforme(xs)
        xs_row = xs_scaled[-1, :]
        predictions = np.array([])
        n_feature = self.get_xs().shape[1]
        for i in range(n_prediction):
            xs_build = np.hstack((xs_row, predictions))
            x = xs_build[-n_feature:].reshape((1, n_feature, 1))
            prediction = model.predict(x)
            predictions = np.hstack((predictions, prediction[0]))
        predictions = self.scaler_inverse_transform(predictions)
        return predictions

    def save(self, json_file_path: str, model_file_path: str) -> None:
        """
        To save instace in given path

        Parameters
        ----------
        path: str
            The  path where to save files
        json_file: str
            The path to save json file
        model_file: str
            The path to save model
        """
        self._set_model_file_path(model_file_path)
        # save model
        project_dir = FileManager.get_project_directory()
        self.get_model().save(project_dir + model_file_path)
        self._freeze_class()
        # save json
        json = self.json_encode()
        FileManager.write(json_file_path, json, overwrite=True, make_dir=True)

    def load(json_file_path: str) -> 'DeepLearning':
        json = FileManager.read(json_file_path)
        dl = MyJson.json_decode(json)
        return dl

    @staticmethod
    def model(ys: Union[List[float], np.ndarray], xs: Union[List[float], np.ndarray]) -> Sequential:
        xs_train = np.array(xs).reshape((xs.shape[0], xs.shape[1], 1))
        ys_train = np.array(ys).reshape((ys.shape[0], 1))
        model = Sequential()
        model.add(LSTM(50, return_sequences=True,
                  input_shape=(xs_train.shape[1], 1)))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dense(25))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.fit(xs_train, ys_train, batch_size=1, epochs=1)
        return model

    @staticmethod
    def coef_determination(ys: np.ndarray, predictions: np.ndarray) -> float:
        u = ((ys - predictions)**2).sum()
        v = ((ys - ys.mean())**2).sum()
        return 1 - u/v

    @staticmethod
    def offset_mean(ys: np.ndarray, predictions: np.ndarray) -> float:
        """
        To evaluate mean offset between Ys and Predictions
        NOTE: The mean offset is the value to Add(+) on Predictions to match Ys's values (ys = predictions + offset_mean)

        Parameters:
        -----------
        ys: np.ndarray
            Target to predict
        predictions: np.ndarray
            Predicted values

        Returns:
        --------
        return: float
            Mean offset between Ys and Predictions
        """
        if ys.shape != predictions.shape:
            raise ValueError(f"Ys'{ys.shape}' and Predictions'{predictions.shape}' must have same shape")
        offsets = ys - predictions
        offsets_pos = offsets[offsets>0]
        offsets_neg = offsets[offsets<0]
        if offsets_pos.shape[0] == offsets_neg.shape[0]:
            offset_mean = offsets_pos.mean() if abs(offsets_pos.mean()) > abs(offsets_neg.mean()) else offsets_neg.mean()
        else:
            offset_mean = offsets_pos.mean() if offsets_pos.shape[0] > offsets_neg.shape[0] else offsets_neg.mean()
        return float(offset_mean)

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = DeepLearning([[1]], [[-1]], train=False)
        exec(MyJson.get_executable())
        # load model
        project_dir = FileManager.get_project_directory()
        model = load_model(project_dir + instance.get_model_file_path())
        instance._init_model(model)
        return instance