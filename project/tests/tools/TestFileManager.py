import shutil
import time
from typing import List
import unittest

from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Price import Price
from model.structure.database.ModelFeature import ModelFeature as _MF


class TestFileManager(unittest.TestCase, FileManager):
    def setUp(self) -> None:
        pass

    def test_paths(self) -> None:
        exp2 = "/Users/israelmeiresonne/Library/Mobile Documents/com~apple~CloudDocs" \
               "/Documents/ROQUETS/apolloXI/i&meim projects/apollo21/versions/v0.1/apollo21/project/"
        self.assertEqual(exp2, FileManager.get_project_directory())

    def test_read_and_write(self) -> None:
        def read(path: str, binary: bool) -> str:
            content = None
            time.sleep(1)
            while (content is None) or ((not binary) and len(content) == 0) or (binary and (not isinstance(content, object))):
                content = _MF.catch_exception(_cls.read, _cls.__name__, repport=False, **{'path': path, 'binary': binary})
                time.sleep(1)
            return content

        _cls = FileManager
        project_dir = FileManager.get_project_directory()
        test_path = 'tests/datas/tools/TestFileManager/test_write/'
        # Error: directory don't exist
        random_file_dir = 'tests/datas/tools/TestFileManager/random_path/'
        random_file_path = random_file_dir + 'random_file.random'
        random_content = 'Random content.'
        # Create missing directory
        exp0 = random_content
        _cls.write(random_file_path, random_content, binary=False, overwrite=True, make_dir=True, line_return=False)
        result0 = read(random_file_path, binary=False)
        self.assertEqual(exp0, result0)
        _cls.remove_file(random_file_path)
        _cls.remove_directory(random_file_dir)
        # Simple Write
        path_txt_file1 = test_path + 'simple_write.txt'
        content_txt1 = 'My file content.\n'
        exp1 = content_txt1
        _cls.write(path_txt_file1, content_txt1, binary=False, overwrite=True, make_dir=True, line_return=False)
        result1 = read(path_txt_file1, binary=False)
        self.assertEqual(exp1, result1)
        # Overwrite
        content_txt2 = 'I overwrited the last content.\n'
        exp2 = content_txt2
        _cls.write(path_txt_file1, content_txt2, binary=False, overwrite=True, make_dir=True, line_return=False)
        result2 = read(path_txt_file1, binary=False)
        self.assertEqual(exp2, result2)
        # Append
        content_txt3 = "Just Added new line in file's end.\n"
        exp3 = content_txt2 + content_txt3
        _cls.write(path_txt_file1, content_txt3, binary=False, overwrite=False, make_dir=True, line_return=False)
        result3 = read(path_txt_file1, binary=False)
        self.assertEqual(exp3,result3)
        _cls.remove_file(path_txt_file1)
        # Binary write
        path_binary_file = test_path + 'price.bin'
        price_obj = Price(10, 'USDT')
        exp4 = price_obj
        _cls.write(path_binary_file, price_obj, binary=True, overwrite=True, make_dir=True, line_return=False)
        result4 = read(path_binary_file, binary=True)
        self.assertEqual(exp4, result4)
        _cls.remove_file(path_binary_file)
        _cls.remove_directory(test_path)

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

    def test_map_dir(self) -> None:
        def func_file_paths(base_path: str, dirs: List[str], files: List[str]) -> List[str]:
            concat_path = base_path
            file_paths = rec_file_paths(concat_path, dirs, files)
            return file_paths
        def rec_file_paths(concat_path: str, dirs: List[str], files: List[str]) -> List[str]:
            file_paths = [concat_path + file for file in files]
            new_dirs = dirs[1:] if len(dirs) > 0 else dirs
            for dir in new_dirs:
                new_concat_path = concat_path + dir
                file_paths = [
                    *file_paths,
                    *rec_file_paths(new_concat_path, new_dirs, files)
                ]
            return file_paths
        start_dir_path = 'to_delete/'
        dirs = [
            start_dir_path,
            'dir123/',
            '.hidden/',
            'dir.py/'
        ]
        files = [
            f'File1.py',
            f'.gitigore1'
        ]
        file_paths = func_file_paths(start_dir_path, dirs, files)
        file_paths.sort()
        [FileManager.write(file_path, 'to_delete', make_dir=True) for file_path in file_paths]
        _MF.wait_while(FileManager.is_writting, False, 60*2, Exception(f"write time out"))
        # No filter
        exp1 = file_paths
        result1 = FileManager.map_dir(start_dir_path)
        self.assertListEqual(exp1, result1)
        # Filter file
        regex2 = r'.*\.py'
        exp2 = [file_path for file_path in file_paths if file_path.split('/')[-1] == files[0]]
        result2 = FileManager.map_dir(start_dir_path, file_regex=regex2)
        self.assertListEqual(exp2, result2)
        # Filter folder
        regex3 = r'^\..*'
        exp3 = [file_path for file_path in file_paths if 0 not in [1 if sib_dir+'/' == dirs[2] else 0 for sib_dir in file_path.split('/')[1:-1]]]
        result3 = FileManager.map_dir(start_dir_path, folder_regex=regex3)
        self.assertListEqual(exp3, result3)
        # Filter file and folder
        regex_file4 = regex2
        regex_folder4 = regex3
        exp4 = [file_path for file_path in exp3 if file_path in exp2]
        exp4.sort()
        result4 = FileManager.map_dir(start_dir_path, file_regex=regex_file4, folder_regex=regex_folder4)
        self.assertListEqual(exp4, result4)
        # End
        shutil.rmtree(start_dir_path)

    def test_exist_file(self) -> None:
        class_name = self.__class__.__name__
        dir_path = f'{class_name}/'
        file_path = f'{dir_path}{class_name}_test_exist_file.empty'
        _MF.catch_exception(FileManager.remove_file, class_name, repport=False, **{Map.path: file_path})
        _MF.catch_exception(FileManager.remove_directory, class_name, repport=False, **{Map.path: dir_path})
        # Directory don't exist
        self.assertFalse(FileManager.exist_file(file_path))
        # Directory exist but File don't
        FileManager.make_directory(dir_path)
        self.assertFalse(FileManager.exist_file(file_path))
        # File exist
        FileManager.write(file_path, f'{class_name} test content')
        _MF.wait_while(FileManager.is_writting, False, 10, to_raise=Exception('Time to wait the writting is out'))
        self.assertTrue(FileManager.exist_file(file_path))
        # End
        FileManager.remove_file(file_path)
        FileManager.remove_directory(dir_path)
