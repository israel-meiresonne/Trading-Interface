from csv import DictReader
from abc import ABC, abstractmethod
from os import walk
from os import path as os_path
import re as rgx


class FileManager(ABC):
    ROOT_DIR = os_path.abspath(__file__).replace("FileManager.py", "../../")

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get_files(p: str, ex=True) -> list:
        """
        To list files of a directory\n
        :param p: the path of the directory
        :param ex: set True to get files with their extension else False
        :return: list of files
        """
        root = FileManager.ROOT_DIR
        _, _, fs = next(walk(root + p))
        if not ex:
            ptr = "\.[A-z]*$"
            for i in range(len(fs)):
                f = fs[i]
                fs[i] = rgx.sub(ptr, "", f)
        return fs

    @staticmethod
    def get_dirs(p: str, include: bool) -> list:
        """
         To list directories of a directory\n
         :param p: the path of the directory
         :param include: set True to include special directories else False.
                        Special file supported: .ignore, __pychache__
         :return: list of directories
         """
        root = FileManager.ROOT_DIR
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
    def get_csv(p: str, fields=None) -> list:
        """
        To get content of a csv file\n
        :param p: the path to the csv file ended by the file's name, ie: path/to/file.csv
        :param fields: name of the filed to keep
        :return: list of each row in the csv file
                 [{index}] => {dict}    # [{str}] => {str}
        """
        patern = "^.*\.csv$"
        if not rgx.match(patern, p):
            raise ValueError(f"This file '{p}' has not a csv extension")
        root = FileManager.ROOT_DIR
        with open(root + p, encoding='utf-8') as f:
            reader = DictReader(f, fieldnames=fields)
            rows = [{k: v for k, v in row.items() if k is not None} for row in reader]
        return rows