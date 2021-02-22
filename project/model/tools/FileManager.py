from csv import DictReader
from csv import DictWriter
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
        :param fields: name of fileds to keep
        :return: list of each row in the csv file
                 List[Dict[]+]+
        """
        if rgx.match('^.*\.csv$', p) is None:
            raise ValueError(f"This file '{p}' has not a csv extension")
        root = FileManager.ROOT_DIR
        with open(root + p, encoding='utf-8') as f:
            reader = DictReader(f, fieldnames=fields)
            rows = [{k: v for k, v in row.items() if k is not None} for row in reader]
        return rows

    @staticmethod
    def write_csv(p: str, fields: list, rows: list, overwrite=True, ignore_extra=False) -> None:
        """
        To write a csv file\n
        :param p: the path to the csv file ended by the file's name, ie: path/to/file.csv
        :Note : if the file don't exist a new one is created
        :param fields: name of fields to write
        :param rows: rows to write
                     List[Disct[]+]+
        :param overwrite: set True to replace to overwrite the file's content else False
                          to add new row in the end of the file
        :param ignore_extra: set True to ignore format errors else False
        """
        if rgx.match('^.*\.csv$', p) is None:
            raise ValueError(f"This file '{p}' has not a csv extension")
        if not ignore_extra:
            fields = list(fields)
            for i in range(len(rows)):
                ks = list(rows[i].keys())
                if fields != ks:
                    raise ValueError(f"This row's fields '{i}:{ks}' don't match the given fields '{fields}")
        root = FileManager.ROOT_DIR
        obs_p = root + p
        extrasaction = 'ignore' if ignore_extra else 'raise'
        mode = 'w' if overwrite else 'a'
        with open(root + p, mode=mode, newline='') as f:
            writer = DictWriter(f, fieldnames=fields, extrasaction=extrasaction)
            f_size = os_path.getsize(obs_p)
            writer.writeheader() if (f_size <= 0) or overwrite else None
            for row in rows:
                writer.writerow(row)
