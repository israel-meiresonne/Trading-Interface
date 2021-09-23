from typing import List, Union

import numpy as np
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.MyJson import MyJson


class ML(MyJson):
    _DEBUG = True
    _COEF_ALPHA_UP = 10
    _COEF_ALPHA_DOWN = _COEF_ALPHA_UP
    _LIMIT_COST_RATE = 10**(-3)
    _LIMIT_COEF_DETERMINATION = 0.005
    _MIN_COEF_DETERMINATION = 0.5

    def __init__(self, ys: List[list], xs: List[list], degree: int = None) -> None:
        self.__ys = None
        self.__xs = None
        self.__degree = None
        self.__X = None
        self.__theta = None
        self.__trained = False
        self.__cost_historic = None
        self.__cost_rates = None
        self._set_dataset(ys, xs)
        self._set_degree(degree)

    def _set_dataset(self, ys: List[list], xs: List[list]) -> None:
        ys = np.array(ys)
        if (ys.shape != (ys.shape[0],)) and (ys.shape != (ys.shape[0],1)):
            raise ValueError(f"Dataset's Ys must have shape '{(ys.shape[0],)}' or '{(ys.shape[0],1)}', instead '{ys.shape}'")
        ys = ys.reshape(ys.shape[0], 1)
        xs = np.array(xs)
        xs = ys.reshape(xs.shape[0], 1) if xs.shape == (xs.shape[0],) else xs
        if xs.shape != (ys.shape[0],xs.shape[1]):
            raise ValueError(f"Dataset's Xs must have shape '{(ys.shape[0],xs.shape[1])}', instead '{xs.shape}'")
        self.__ys = ys
        self.__xs = xs
    
    def get_ys(self) -> np.ndarray:
        return self.__ys
    
    def get_xs(self) -> np.ndarray:
        return self.__xs

    def _set_degree(self, degree: int = None) -> None:
        self._check_degree(degree) if degree is not None else None
        self.__degree = degree
    
    @staticmethod
    def _check_degree(degree: int) -> None:
        if (not isinstance(degree, int)) or (degree <= 0):
            raise ValueError(f"Degree must be type int and > 0, instead '{degree}'({type(degree)})")
    
    def _search_degree(self) -> None:
        raise Exception(f"Must implement")
    
    def get_degree(self) -> int:
        self._search_degree() if self.__degree is None else None
        return self.__degree
    
    def _set_X(self) -> None:
        degree = self.get_degree()
        xs = self.get_xs()
        self.__X = self.generate_X(xs, degree)
    
    def get_X(self) -> np.ndarray:
        """
        To get matrix X\n
        return: X
            Matrix X
        """
        self._set_X() if self.__X is None else None
        return self.__X
    
    def _set_theta(self, theta: np.ndarray = None) -> None:
        if theta is None:
            n_param = self.get_X().shape[1]
            self.__theta = np.zeros((n_param, 1))
        else:
            self.__theta = theta
    
    def get_theta(self) -> np.ndarray:
        self._set_theta() if self.__theta is None else None
        return self.__theta
    
    def _set_trained(self, is_trained: bool) -> None:
        self.__trained = is_trained
    
    def is_trained(self) -> bool:
        return self.__trained
    
    def _set_cost_historic(self, cost_historic: np.ndarray) -> None:
        self.__cost_historic = cost_historic
    
    def get_cost_historic(self) -> np.ndarray:
        return self.__cost_historic
    
    def _set_cost_rates(self, cost_rates: np.ndarray) -> None:
        self.__cost_rates = cost_rates
    
    def get_cost_rates(self) -> np.ndarray:
        return self.__cost_rates
    
    def _set_coef_determination(self) -> None:
        self.__coef_determination = self.coef_determination(self.get_ys(), self.predict(self.get_xs()))

    def get_coef_determination(self) -> float:
        return self.__coef_determination
    
    def train(self) -> None:
        X = self.get_X()
        ys = self.get_ys()
        theta = self.get_theta()
        new_theta, cost_hist, cost_rates = self.gradient_decsent(X, ys, theta)
        self._set_theta(new_theta)
        self._set_cost_historic(cost_hist)
        self._set_cost_rates(cost_rates)
        self._set_trained(is_trained=True)
        self._set_coef_determination()
    
    def predict(self, xs: List[list]) -> np.ndarray:
        """
        To predit Y values of given sample\n
        xs: List[list]
            Samples
        return: np.ndarray
            Y values prdicted
        """
        xs = np.array(xs)
        if xs.shape[1] != self.get_xs().shape[1]:
            raise ValueError(f"Dataset's Xs must have '{self.get_xs().shape[1]}' column, instead '{xs.shape[1]}'")
        self.train() if not self.is_trained() else None
        X = self.generate_X(xs, self.get_degree())
        return ML.model(X, self.get_theta())
    
    @staticmethod
    def generate_X(xs: Union[List[list], np.ndarray], degree: int) -> np.ndarray:
        ML._check_degree(degree)
        xs = np.array(xs) if not isinstance(xs, np.ndarray) else xs
        tab = [xs**i for i in range(degree, 0, -1)]
        tup = tuple([*tab, np.ones((xs.shape[0], 1))])
        return np.hstack(tup)
    
    @staticmethod
    def model(X: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """
        To generate model like F = X.Theta\n
        X: np.ndarray
            Matrix X
        theta: np.ndarray
            Matrix theta
        return: model
            Model like F = X.Theta
        """
        return X.dot(theta)
    
    @staticmethod
    def cost_function(X, ys, theta) -> float:
        m = len(ys)
        F = ML.model(X, theta)
        return 1/(2*m) * np.sum((F - ys)**2)
    
    @staticmethod
    def gradient(X, y, theta) -> float:
        m = len(y)
        F = ML.model(X, theta)
        return 1/m * X.T.dot(F - y)

    @staticmethod
    def gradient_decsent(X: np.ndarray, ys: np.ndarray, theta: np.ndarray, alpha: float = None, n_lesson: int = None) -> tuple:
        def get_new_theta(func_alpha: float, func_theta: np.ndarray) -> np.ndarray:
                func_new_theta = func_theta - func_alpha * ML.gradient(X, ys, func_theta)
                return func_new_theta

        def get_rate(new: float, hold: float) -> float:
            return new / hold - 1

        def get_coef(func_theta: np.ndarray) -> float:
            predictions = ML.model(X, func_theta)
            return ML.coef_determination(ys, predictions)
        
        def reduce_alpha(func_alpha: float) -> float:
            return func_alpha / ML._COEF_ALPHA_DOWN

        def increase_alpha(func_alpha: float) -> float:
            return func_alpha * ML._COEF_ALPHA_UP

        def init_alpha(func_theta: np.ndarray) -> float:
            func_alpha = 1
            last_cost = ML.cost_function(X, ys, func_theta)
            func_new_theta = get_new_theta(func_alpha, func_theta)
            new_cost = ML.cost_function(X, ys, func_new_theta)
            cost_dropping = new_cost <= last_cost
            if cost_dropping:
                # search rising cost
                cost_rising = False
                while not cost_rising:
                    last_cost = ML.cost_function(X, ys, func_theta)
                    func_new_theta = get_new_theta(func_alpha, func_theta)
                    new_cost = ML.cost_function(X, ys, func_new_theta)
                    cost_rising = new_cost > last_cost
                    func_alpha = increase_alpha(func_alpha) if not cost_rising else reduce_alpha(func_alpha)
            else:
                # search dropping cost
                cost_dropping = False
                while not cost_dropping:
                    last_cost = ML.cost_function(X, ys, func_theta)
                    func_new_theta = get_new_theta(func_alpha, func_theta)
                    new_cost = ML.cost_function(X, ys, func_new_theta)
                    cost_dropping = new_cost <= last_cost
                    func_alpha = reduce_alpha(func_alpha) if not cost_dropping else func_alpha
            print(_MF.prefix() + f"final alpha: {func_alpha}") if ML._DEBUG else None
            return func_alpha

        cost_hist = []
        cost_rates = []
        perf_coefs = []
        new_theta = np.array(theta.tolist())
        if n_lesson is not None:
            for i in range(n_lesson):
                new_theta = new_theta - alpha * ML.gradient(X, ys, new_theta)
                cost_hist.append(ML.cost_function(X, ys, new_theta))
                cost_rates.append(cost_hist[i]/cost_hist[i-1]-1) if (i > 0) else None
        else:
            # Found max alpha
            alpha = init_alpha(new_theta)
            # Train
            cost_rate_limit = ML._LIMIT_COST_RATE
            coef_determ_limit = ML._LIMIT_COEF_DETERMINATION
            coef_determ_min = ML._MIN_COEF_DETERMINATION
            perf_coefs.append(get_coef(new_theta))
            cost = ML.cost_function(X, ys, new_theta)
            cost_hist.append(cost)
            end = False
            i = 0
            while not end:
                # Update
                new_theta = get_new_theta(alpha, new_theta)
                cost = ML.cost_function(X, ys, new_theta)
                cost_hist.append(cost)
                cost_rates.append(get_rate(cost, cost_hist[-2])) if len(cost_hist) >= 2 else cost_rates.append(cost_rate_limit * 2)
                # Check limit
                cost_rising = cost >= cost_hist[-2]
                cost_rate_bellow_limit = abs(cost_rates[-1]) <= cost_rate_limit
                if cost_rising:
                    alpha = reduce_alpha(alpha)
                elif cost_rate_bellow_limit:
                    perf_coefs.append(get_coef(new_theta))
                    delta_coef = abs(perf_coefs[-1] - perf_coefs[-2])
                    end = (perf_coefs[-1] >= coef_determ_min) and (delta_coef <= coef_determ_limit)
                    if not end:
                        alpha = reduce_alpha(alpha)
                # end = True if (not end) and (i >= 5*10**(4)) else end
                print(_MF.prefix() + f"i: {i}") if ML._DEBUG else None
                print(_MF.prefix() + f"alpha: {alpha}") if ML._DEBUG else None
                print(_MF.prefix() + f"cost: {cost}") if ML._DEBUG else None
                i += 1
        return new_theta, cost_hist, cost_rates
    
    @staticmethod
    def coef_determination(ys: np.ndarray, predictions: np.ndarray) -> float:
        u = ((ys - predictions)**2).sum()
        v = ((ys - ys.mean())**2).sum()
        return 1 - u/v
    
    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = ML([],[])
        exec(MyJson.get_executable())
        return instance
