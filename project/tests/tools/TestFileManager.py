import unittest

from model.tools.FileManager import FileManager
from model.tools.Price import Price


class TestFileManager(unittest.TestCase, FileManager):
    def setUp(self) -> None:
        pass

    def test_paths(self) -> None:
        exp2 = "/Users/israelmeiresonne/Library/Mobile Documents/com~apple~CloudDocs" \
               "/Documents/ROQUETS/apolloXI/i&meim projects/apollo21/versions/v0.1/apollo21/project/"
        self.assertEqual(exp2, FileManager.get_project_directory())

    def test_read_and_write(self) -> None:
        project_dir = FileManager.get_project_directory()
        test_path = 'tests/datas/tools/TestFileManager/test_write/'
        # Error: directory don't exist
        random_file_dir = 'tests/datas/tools/TestFileManager/random_path/'
        random_file_path = random_file_dir + 'random_file.random'
        random_content = 'Random content.'
        with self.assertRaises(FileNotFoundError):
            FileManager.write(random_file_path, random_content, binary=False, overwrite=True, make_dir=False)
        # Create missing directory
        exp0 = random_content
        FileManager.write(random_file_path, random_content, binary=False, overwrite=True, make_dir=True)
        result0 = FileManager.read(random_file_path, binary=False)
        self.assertEqual(exp0, result0)
        FileManager.remove_file(random_file_path)
        FileManager.remove_directory(random_file_dir)
        # Simple Write
        path_txt_file1 = test_path + 'simple_write.txt'
        content_txt1 = 'My file content.\n'
        exp1 = content_txt1
        FileManager.write(path_txt_file1, content_txt1, binary=False, overwrite=True, make_dir=True)
        result1 = FileManager.read(path_txt_file1, binary=False)
        self.assertEqual(exp1, result1)
        # Overwrite
        content_txt2 = 'I overwrited the last content.\n'
        exp2 = content_txt2
        FileManager.write(path_txt_file1, content_txt2, binary=False, overwrite=True, make_dir=True)
        result2 = FileManager.read(path_txt_file1, binary=False)
        self.assertEqual(exp2, result2)
        # Append
        content_txt3 = "Just Added new line in file's end.\n"
        exp3 = content_txt2 + content_txt3
        FileManager.write(path_txt_file1, content_txt3, binary=False, overwrite=False, make_dir=True)
        result3 = FileManager.read(path_txt_file1, binary=False)
        self.assertEqual(exp3,result3)
        FileManager.remove_file(path_txt_file1)
        # Binary write
        path_binary_file = test_path + 'price.bin'
        price_obj = Price(10, 'USDT')
        exp4 = price_obj
        FileManager.write(path_binary_file, price_obj, binary=True, overwrite=True, make_dir=True)
        result4 = FileManager.read(path_binary_file, binary=True)
        self.assertEqual(exp4, result4)
        FileManager.remove_file(path_binary_file)
        FileManager.remove_directory(test_path)

    def test_path_to_dir(self) -> None:
        file_path = '/Users/israelmeiresonne/Library/Mobile Documents/com~apple~CloudDocs/Documents/ROQUETS/apolloXI/' \
                    'i&meim projects/apollo21/versions/v0.1/apollo21/project/content/storage/STAGE_2/Bot/' \
                    'bot_24n6a2e030y81j9z3f45/' \
                    '2021-06-30_07.40.29|2021-06-30_07.40.44|bot_24n6a2e030y81j9z3f45|Binance|Stalker_bot_backup.json'
        exp1 = '/Users/israelmeiresonne/Library/Mobile Documents/com~apple~CloudDocs/Documents/ROQUETS/apolloXI/' \
               'i&meim projects/apollo21/versions/v0.1/apollo21/project/content/storage/STAGE_2/Bot/' \
               'bot_24n6a2e030y81j9z3f45/'
        result1 = FileManager.path_to_dir(file_path)
        self.assertEqual(exp1, result1)
        with self.assertRaises(ValueError):
            FileManager.path_to_dir('path/to/my/dir/')
        with self.assertRaises(ValueError):
            FileManager.path_to_dir('file_without_path.ext')
