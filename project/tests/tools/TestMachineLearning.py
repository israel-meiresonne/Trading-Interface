import unittest

import matplotlib.pyplot as plt
import numpy as np
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager
from model.tools.MachineLearning import ML


class TestMachineLearning(unittest.TestCase, ML):
    def setUp(self) -> None:
        # Degree 1
        self.coef1 = 2
        self.y1 = 1
        a = self.coef1
        b = self.y1
        self.xs1 = [[x] for x in range(1, 51)]
        self.ys1 = [[a * x[0] + b] for x in self.xs1]
        self.ml1 = ML(self.ys1, self.xs1, degree=1)
        # Degree 2
        a = 3
        b = 5
        self.xs2 = [[x] for x in range(1, 51)]
        self.ys2 = [[a * x[0]**2 + b] for x in self.xs1]
        self.ml2 = ML(self.ys2, self.xs2, degree=2)
        # Degree 11
        degree = 11
        self.xs11 = [[x] for x in range(1, 51)]
        self.ys11 = [[a * x[0]**degree + b] for x in self.xs11]
        self.ml11 = ML(self.ys11, self.xs11, degree=degree)

    @staticmethod
    def generate_ml(n_sample: int, degree: int, n_features: int = None) -> ML:
        n_value = int(n_sample / 2)
        xs = [[x] for x in range(-n_value, n_value)]
        ys = [[x[0] ** degree] for x in xs]
        ml = ML(ys, xs, degree=degree)
        return ml

    def test_set_dataset(self) -> None:
        ml = ML(self.ys1, self.xs1, degree=1)
        # Check Ys
        exp1 = np.array(self.ys1).reshape((len(self.ys1), 1))
        result1 = ml.get_ys()
        self.assertListEqual(exp1.tolist(), result1.tolist())
        self.assertEqual(exp1.shape, result1.shape)
        # Check Xs
        exp2 = np.array(self.xs1).reshape((len(self.xs1), 1))
        result2 = ml.get_xs()
        self.assertListEqual(exp2.tolist(), result2.tolist())
        self.assertEqual(exp2.shape, result2.shape)
        # Wrong Ys shape
        xs = [[x] for x in range(50)]
        ys = [[x[0]*2, x] for x in xs]
        with self.assertRaises(ValueError):
            ML(ys, xs, 1)
        # Wrong Xs shape
        xs = [[x] for x in range(50)]
        ys = [[x[0]*2] for x in xs]
        del xs[-5:-1]
        with self.assertRaises(ValueError):
            ML(ys, xs, 1)

    def test_set_degree(self) -> None:
        ml = ML(self.ys1, self.xs1, degree=1)
        self.assertEqual(1, ml.get_degree())
        # Degree is None
        with self.assertRaises(Exception):
            ml = ML(self.ys1, self.xs1, degree=None)
            ml.get_degree()
        # Degree < 0
        with self.assertRaises(ValueError):
            ml = ML(self.ys1, self.xs1, degree=-1)
        # Degree == 0
        with self.assertRaises(ValueError):
            ml = ML(self.ys1, self.xs1, degree=0)
        
    def test_search_degree(self) -> None:
        # Degree = 1
        degree = 1
        n_value = int(100 / 2)
        xs = [[x] for x in range(-n_value, n_value)]
        ys = [[x[0] ** degree] for x in xs]
        ml1 = ML(ys, xs, degree=None)
        exp1 = degree
        result1 = ml1.get_degree()
        self.assertEqual(exp1, result1)
        # Degree = 7
        degree = 7
        ys = [[x[0] ** degree] for x in xs]
        ml2 = ML(ys, xs, degree=None)
        exp2 = degree
        result2 = ml2.get_degree()
        self.assertEqual(exp2, result2)

    def test_get_X(self) -> None:
        ml = self.ml1
        exp = len(self.xs1[0]) * ml.get_degree() + 1
        self.assertEqual(exp, ml.get_X().shape[1])

    def test_set_theta(self) -> None:
        ml1 = self.ml1
        # Theta is None
        ml1._set_theta(theta=None)
        theta1 = ml1.get_theta()
        self.assertIsInstance(theta1, np.ndarray)
        # Theta is not None
        ml2 = ML(self.ys1, self.xs1, degree=1)
        n_param = ml2.get_X().shape[1]
        exp2 = np.random.randn(n_param, 1)
        ml2._set_theta(theta=exp2)
        result2 = ml2.get_theta()
        self.assertListEqual(exp2.tolist(), result2.tolist())
        self.assertEqual(id(exp2), id(result2))

    def test_predict(self) -> None:
        print_dir = FileManager.get_project_directory() + "tests/"
        a = self.coef1
        b = self.y1
        if True:
            ml1 = ML(self.ys1, self.xs1, degree=1)
            perf_coef = ml1.get_coef_determination()
            self.assertTrue(perf_coef >= 0.9)
            self.assertIsInstance(ml1.get_cost_historic(), list)
            self.assertIsInstance(ml1.get_cost_rates(), list)
            print(perf_coef)
        # Graph
        if False:
            plt.scatter(self.xs1, self.ys1)
            predictions = ml1.predict(self.xs1)
            plt.plot(self.xs1, predictions, 'r')
            plt.savefig('../graph1.png')
        # Graph 2
        if False:
            ml2 = self.ml2
            plt.figure()
            plt.scatter(ml2.get_xs(), ml2.get_ys())
            predictions = ml2.predict(ml2.get_xs())
            plt.plot(ml2.get_xs(), predictions, 'r')
            plt.savefig('../graph2.png')
        # Graph X
        if False:
            degree = 4
            n_sample = int(50/2)
            xs = [[x] for x in range(-n_sample, n_sample)]
            ys = [[a * x[0] ** degree + b] for x in xs]
            ml = ML(ys, xs, degree=degree)
            plt.figure()
            predictions = ml.predict(ml.get_xs())
            plt.scatter(ml.get_xs(), ml.get_ys())
            plt.plot(ml.get_xs(), predictions, 'r')
            plt.savefig(f'{print_dir}graphX-{degree}.png')
            print(f"coef_determ: {ml.get_coef_determination()}")
        # Graph 11
        if False:
            ml11 = self.ml11
            plt.figure()
            plt.scatter(ml11.get_xs(), ml11.get_ys())
            predictions = ml11.predict(ml11.get_xs())
            plt.plot(ml11.get_xs(), predictions, 'r')
            plt.savefig('../graph3.png')

    def test_generate_X(self) -> None:
        # n_features=1 AND Degree=1
        xs1 = [[2], [5]]
        exp1 = _MF.json_decode(_MF.json_encode(xs1))
        [row.append(1) for row in exp1]
        result1 = ML.generate_X(xs1, degree=1)
        self.assertListEqual(exp1, result1.tolist())
        # n_features=2 AND Degree=1
        xs2 = [[2, 3], [5, 7]]
        exp2 = _MF.json_decode(_MF.json_encode(xs2))
        [row.append(1) for row in exp2]
        result2 = ML.generate_X(xs2, degree=1)
        self.assertListEqual(exp2, result2.tolist())
        # n_features=2 AND Degree=3
        xs3 = [[2, 3], [5, 7]]
        np_xs3 = np.array(xs3)
        exp3 = np.hstack((np_xs3**3, np_xs3**2, np_xs3,
                         np.ones((np_xs3.shape[0], 1))))
        result3 = ML.generate_X(xs3, degree=3)
        self.assertListEqual(exp3.tolist(), result3.tolist())
