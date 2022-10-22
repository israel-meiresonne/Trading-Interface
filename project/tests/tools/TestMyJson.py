import unittest
from model.tools.Map import Map

from model.tools.MyJson import MyJson
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Price import Price


class TestMyJson(unittest.TestCase):
    def setUp(self) -> None:
        self.price = Price(19, 'USDT')
        self.map1 = Map({'k1': 'v1'})

    def test_json_encode(self) -> None:
        prc = self.price
        json_str = prc.json_encode()
        self.assertTrue(isinstance(json_str, str))

    def test_json_decode(self) -> None:
        prc = self.price
        json_str = prc.json_encode()
        new_prc = MyJson.json_decode(json_str)
        # Encode decode
        self.assertEqual(prc, new_prc)
        self.assertNotEqual(id(prc), id(new_prc))
        # JSON string is not dict
        with self.assertRaises(ValueError):
            MyJson.json_decode(_MF.json_encode([]))

    def test_copy(self) -> None:
        def test(obj: MyJson) -> None:
            obj_dict = obj.__dict__.copy()
            obj_copy = obj.copy()
            self.assertNotEqual(id(obj), id(obj_copy))
            self.assertEqual(obj, obj_copy)
            self.assertDictEqual(obj_dict, obj_copy.__dict__)
        test(self.price)
        test(self.map1)

    def test_generate_instance(self) -> None:
        prc = self.price
        json_str = prc.json_encode()
        json_dic = _MF.json_decode(json_str)
        del json_dic[MyJson.get_class_name_token()]
        new_json_str = _MF.json_encode(json_dic)
        with self.assertRaises(KeyError):
            MyJson.json_decode(new_json_str)

    def test__eq__(self) -> None:
        def test(obj1: object, obj2: object, obj3: object) -> None:
            obj1_copy = obj1.__dict__.copy()
            obj2_copy = obj2.__dict__.copy()
            obj3_copy = obj3.__dict__.copy()
            # Object with an attribut 'id'
            self.assertEqual(obj1, obj2)
            self.assertNotEqual(obj1, obj3)
            self.assertDictEqual(obj1.__dict__, obj1_copy)
            self.assertDictEqual(obj2.__dict__, obj2_copy)
            self.assertDictEqual(obj3.__dict__, obj3_copy)
        # Object with an attribut 'id'
        map1 = Map({'k1': 'v1'})
        map2 = Map({'k1': 'v1'})
        map3 = Map({'k3': 'v3'})
        test(map1, map2, map3)
        # Object without an attribut 'id'
        price1 = Price(1, 'USDT')
        price2 = Price(1, 'USDT')
        price3 = Price(3, 'USDT')
        test(price1, price2, price3)


if __name__ == '__main__':
    unittest.main()
