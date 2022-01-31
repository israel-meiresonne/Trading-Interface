from pickle import Pickler, Unpickler
from csv import DictReader
from csv import DictWriter
from abc import ABC, abstractmethod
from os import path as os_path, remove as os_remove, walk
from pathlib import Path
import re as rgx
from typing import Any, List

from model.structure.database.ModelFeature import ModelFeature as _MF


class FileManager(ABC):
    _PROJECT_DIR = None

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get_project_directory() -> str:
        """
        To get the path from '/' to this project\n
        :return: the path from '/' to this project
        """
        if FileManager._PROJECT_DIR is None:
            FileManager._PROJECT_DIR = os_path.abspath(__file__).replace('model/tools/FileManager.py', '')
        return FileManager._PROJECT_DIR

    @staticmethod
    def read(path: str, binary: bool = False) -> Any:
        """
        To read a file\n
        :param path: The path to the file
        :param binary: Set True to read binary file else False to just read file
        :return: The content of the file
        """
        path = FileManager.get_project_directory() + path
        bin_mode = 'b' if binary else ''
        with open(path, 'r' + bin_mode) as file:
            if binary:
                record = Unpickler(file)
                content = record.load()
            else:
                content = file.read()
        return content

    @staticmethod
    def write(path: str, content: Any, binary: bool = False, overwrite: bool = True, make_dir: bool = False, line_return=True) -> None:
        """
        To write in a file\n
        :param path: The path to the file
        :param content: The content to write in file
        :param binary: Set True to write in binary else False
        :param overwrite: Set True to overwrite the file's content else False to add new line at file's end
        :param make_dir: Set True create missing directory else False to raise error if miss directory
        :param line_return: Set True to end with new line else False
        """
        full_path = FileManager.get_project_directory() + path
        bin_mode = 'b' if binary else ''
        write_mode = 'w' if overwrite else 'a'
        if line_return:
            content = f'{content}\r\n'
        if make_dir:
            file_dir = FileManager.path_to_dir(path)
            FileManager.make_directory(file_dir)
        with open(full_path, write_mode + bin_mode) as file:
            if binary:
                record = Pickler(file)
                record.dump(content)
            else:
                file.write(content)

    @staticmethod
    def get_csv(p: str, fields: list = None) -> list:
        """
        To get content of a csv file\n
        :param p: the path to the csv file ended by the file's name, ie: path/to/file.csv
        :param fields: name of fileds to keep
        :return: list of each row in the csv file
                 List[Dict[]+]+
        """
        if rgx.match('^.*\.csv$', p) is None:
            raise ValueError(f"This file '{p}' has not a csv extension")
        root = FileManager.get_project_directory()
        with open(root + p, encoding='utf-8') as f:
            reader = DictReader(f, fieldnames=fields)
            rows = [{k: v for k, v in row.items() if k is not None} for row in reader]
        return rows

    @staticmethod
    def write_csv(path: str, fields: list, rows: list,
                  overwrite=True, make_dir: bool = False, ignore_extra=False) -> None:
        """
        To write a csv file\n
        :param path: the path to the csv file ended by the file's name, ie: path/to/file.csv
        :Note : if the file don't exist a new one is created
        :param fields: name of fields to write
        :param rows: rows to write
                     List[Disct[]+]+
        :param overwrite: set True to replace to overwrite the file's content else False
                          to add new row in the end of the file
        :param make_dir: Set True create missing directory else False to raise error if miss directory
        :param ignore_extra: set True to ignore format errors else False
        """
        if rgx.match(r'^.*\.csv$', path) is None:
            raise ValueError(f"This file '{path}' has not a csv extension")
        if not ignore_extra:
            fields = list(fields)
            for i in range(len(rows)):
                ks = list(rows[i].keys())
                if fields != ks:
                    raise ValueError(f"This row's fields '{i}:{ks}' don't match the given fields '{fields}")
        project_dir = FileManager.get_project_directory()
        full_path = project_dir + path
        extrasaction = 'ignore' if ignore_extra else 'raise'
        mode = 'w' if overwrite else 'a'
        if make_dir:
            file_dir = FileManager.path_to_dir(path)
            FileManager.make_directory(file_dir)
        with open(full_path, mode=mode, newline='') as f:
            writer = DictWriter(f, fieldnames=fields, extrasaction=extrasaction)
            f_size = os_path.getsize(full_path)
            writer.writeheader() if (f_size <= 0) or overwrite else None
            for row in rows:
                writer.writerow(row)

    @staticmethod
    def get_files(path: str, extension: bool = True, special: bool = False, make_dir: bool = False) -> list:
        """
        To list files of a directory
        NOTE: files are sorted low to hight following their name

        Parameters:
        -----------
        path: str
            The path to the directory
        extension: bool = True
            Set True to get files with their extension else False
        special: bool = False
            Set True to get special files (.ignore, .DS_Store, etc...) else False to exclude them
        make_dir: bool = False
            Set True create missing directory else False to raise error if miss directory

        Returns:
        --------
        return: list
            List files name in the given directory
        """
        project_dir = FileManager.get_project_directory()
        FileManager.make_directory(path) if make_dir else None
        _, _, files = next(walk(project_dir + path))
        if not extension:
            ptr = r"\.[A-z]*$"
            for i in range(len(files)):
                file = files[i]
                files[i] = rgx.sub(ptr, "", file)
        files = files
        if not special:
            regex_special = r'^\..+'
            files = [file for file in files if not _MF.regex_match(regex_special, file)]
        files.sort()
        return files

    @staticmethod
    def get_dirs(path: str, special: bool = False, make_dir: bool = False) -> list[str]:
        """
         To list directories of a directory\n
         :param path: the path of the directory
         :param special: set True to include special directories else False.
                        Special file supported: .ignore, __pychache__
         :param make_dir: Set True create missing directory else False to raise error if miss directory
         :return: list of directories
         """
        project_dir = FileManager.get_project_directory()
        FileManager.make_directory(path) if make_dir else None
        _, drs, _ = next(walk(project_dir + path))
        if not special:
            ptr = r"^__[\w]*__$|^\.[\w]"
            ndrs = []
            for i in range(len(drs)):
                f = drs[i]
                if not rgx.match(ptr, f):
                    ndrs.append(f)
        else:
            ndrs = drs
        ndrs.sort()
        return ndrs

    @staticmethod
    def remove_file(path: str) -> None:
        """
        To remove file\n
        :param path: The path the file to remove from the project's directory, i.e.: content/my/file.txt
        """
        path = FileManager.get_project_directory() + path
        os_remove(path)

    @staticmethod
    def path_to_dir(file_path: str) -> str:
        """
        To extract path to file's directory from file's path
        NOTE: 'path/to/my/file.py' => 'path/to/my/'

        Parameters:
        -----------
        file_path: str
            Path to a file

        Return:
        -------
        return: str
            Path to file's directory
        """
        if file_path[-1] == '/':
            raise ValueError(f"This path '{file_path}' is a directory")
        if '/' not in file_path:
            raise ValueError(f"This path '{file_path}' don't contain directory")
        dir_path = '/'.join(file_path.split('/')[:-1]) + '/'
        return dir_path

    @staticmethod
    def make_directory(path: str) -> None:
        """
        To create a new directory\n
        :param path: The path from the project's directory to the new directory, i.e.: 'model/path/new/directory/'
        """
        full_path = FileManager.get_project_directory() + path
        Path(full_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def remove_directory(path: str) -> None:
        """
        To create a new directory\n
        :param path: The path from '/' to the new directory, i.e.: 'model/path/new/directory/'
        """
        full_path = FileManager.get_project_directory() + path
        Path(full_path).rmdir()