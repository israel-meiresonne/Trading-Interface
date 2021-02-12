from abc import ABC, abstractmethod
from os import walk
import re as rgx


class FileManager(ABC):
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
        _, _, fs = next(walk(p))
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
        _, drs, _ = next(walk(p))
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
