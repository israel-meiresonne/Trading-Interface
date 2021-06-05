from pickle import Pickler, Unpickler
from csv import DictReader
from csv import DictWriter
from abc import ABC, abstractmethod
from os import path as os_path, remove as os_remove, walk
from pathlib import Path
import re as rgx
from typing import Any

from model.structure.database.ModelFeature import ModelFeature as _MF


class FileManager(ABC):
    _PROJECT_DIR = None
    _REGEX_FILE_END_PATH = '[\w\.-]+$'

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
    def get_regex_file_end_path() -> str:
        return FileManager._REGEX_FILE_END_PATH

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
    def write(path: str, content: Any, binary: bool = False, overwrite: bool = True, make_dir: bool = False) -> None:
        """
        To write in a file\n
        :param path: The path to the file
        :param content: The content to write in file
        :param binary: Set True to write in binary else False
        :param binary: Set True to overwrite the file's content else False to add new line at file's end
        :param make_dir: Set True create missing directory else False to raise error if miss directory
        """
        full_path = FileManager.get_project_directory() + path
        bin_mode = 'b' if binary else ''
        write_mode = 'w' if overwrite else 'a'
        if make_dir:
            regex = FileManager.get_regex_file_end_path()  # '[\w\.-]+$'
            directory = _MF.regex_replace(regex, '', path)
            FileManager.make_directory(directory)
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
            regex = FileManager.get_regex_file_end_path()
            directory = _MF.regex_replace(regex, '', path)
            FileManager.make_directory(directory)
        with open(full_path, mode=mode, newline='') as f:
            writer = DictWriter(f, fieldnames=fields, extrasaction=extrasaction)
            f_size = os_path.getsize(full_path)
            writer.writeheader() if (f_size <= 0) or overwrite else None
            for row in rows:
                writer.writerow(row)

    @staticmethod
    def get_files(p: str, ex=True) -> list:
        """
        To list files of a directory\n
        :param p: the path of the directory
        :param ex: set True to get files with their extension else False
        :return: list of files
        """
        root = FileManager.get_project_directory()
        _, _, fs = next(walk(root + p))
        if not ex:
            ptr = "\.[A-z]*$"
            for i in range(len(fs)):
                f = fs[i]
                fs[i] = rgx.sub(ptr, "", f)
        return fs

    @staticmethod
    def get_dirs(p: str, include: bool = False) -> list:
        """
         To list directories of a directory\n
         :param p: the path of the directory
         :param include: set True to include special directories else False.
                        Special file supported: .ignore, __pychache__
         :return: list of directories
         """
        root = FileManager.get_project_directory()
        _, drs, _ = next(walk(root + p))
        if not include:
            ptr = "^__[\w]*__$|^\.[\w]"
            ndrs = []
            for i in range(len(drs)):
                f = drs[i]
                if not rgx.match(ptr, f):
                    ndrs.append(f)
        else:
            ndrs = drs
        return ndrs

    @staticmethod
    def remove_file(path: str) -> None:
        """
        To remove file
        :param path: The path the file to remove from the project's directory, i.e.: content/my/file.txt
        """
        path = FileManager.get_project_directory() + path
        os_remove(path)

    @staticmethod
    def make_directory(path: str) -> None:
        """
        To create a new directory\n
        :param path: The path from the project's directory to the new directory, i.e.: 'model/path/new/directory/'
        """
        full_path = project_path = FileManager.get_project_directory() + path
        Path(full_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def remove_directory(path: str) -> None:
        """
        To create a new directory\n
        :param path: The path from '/' to the new directory, i.e.: 'model/path/new/directory/'
        """
        full_path = project_path = FileManager.get_project_directory() + path
        Path(full_path).rmdir()