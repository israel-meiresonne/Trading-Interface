import unittest

from model.tools.MyJson import MyJson
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Price import Price


class TestMyJson(unittest.TestCase):
    def setUp(self) -> None:
        self.price = Price(19, 'USDT')

    def test_get_import(self) -> None:
        # Check import of class file
        exp1 = 'from model.structure.strategies.MinMax.MinMax import MinMax'
        result1 = MyJson.get_import('MinMax')
        self.assertEqual(exp1, result1)
        # Check import of class folder
        exp2 = 'from model.structure.strategies.Stalker.Stalker import Stalker'
        result2 = MyJson.get_import('Stalker')
        self.assertEqual(exp2, result2)
        # Execute all import
        imports = MyJson.get_imports()
        for class_name, import_exec in imports.get_map().items():
            if class_name == 'Paire':
                continue
            exec(import_exec)
            print(f"Class '{class_name}' imported with success ✅")

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

    def test_generate_instance(self) -> None:
        prc = self.price
        json_str = prc.json_encode()
        json_dic = _MF.json_decode(json_str)
        del json_dic[MyJson.get_class_name_token()]
        new_json_str = _MF.json_encode(json_dic)
        with self.assertRaises(KeyError):
            MyJson.json_decode(new_json_str)


if __name__ == '__main__':
    unittest.main()
