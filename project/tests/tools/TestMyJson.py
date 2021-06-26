import unittest

from model.tools.MyJson import MyJson


class MyTestCase(unittest.TestCase, MyJson):
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



if __name__ == '__main__':
    unittest.main()
