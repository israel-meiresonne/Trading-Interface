from pickle import Pickler, Unpickler
from csv import DictReader
from csv import DictWriter
from abc import ABC
from os import path as os_path, remove as os_remove, walk
from pathlib import Path
import re as rgx
import threading
import time
from types import FunctionType
from typing import Any, List

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.WaitingRoom import WaitingRoom


class FileManager(ABC):
    _PROJECT_DIR = None
    _THREAD_WRITE = None
    _ROOM_WRITE = None
    _QUEU_WRITE = None
    _THREAD_NAME_WRITE = "files_writer"

    @staticmethod
    def get_project_directory() -> str:
        """
        To get the path from '/' to this project\n
        :return: the path from '/' to this project
        """
        if FileManager._PROJECT_DIR is None:
            FileManager._PROJECT_DIR = os_path.abspath(__file__).replace('model/tools/FileManager.py', '')
        return FileManager._PROJECT_DIR

    @classmethod
    def is_writting(cls) -> bool:
        """
        To check if FileManager is writting

        Returns:
        --------
        return: bool
            True if FileManager is writting else False
        """
        return cls._get_write_thread().is_alive()

    @classmethod
    def _get_write_thread(cls) -> threading.Thread:
        if (cls._THREAD_WRITE is None) or (not cls._THREAD_WRITE.is_alive()):
            thread, output = _MF.generate_thread(cls._thread_write, cls._THREAD_NAME_WRITE)
            cls._THREAD_WRITE = thread
        return cls._THREAD_WRITE

    @classmethod
    def _get_writing_room(cls) -> WaitingRoom:
        if cls._ROOM_WRITE is None:
            cls._ROOM_WRITE = WaitingRoom('WriteRoom')
        return cls._ROOM_WRITE

    @classmethod
    def _get_write_queu(cls)  -> List[dict]:
        """
        To get list of write to execute

        Returns:
        --------
        return: List[dict]
            List of write to execute
            list[index{int}][Map.callback]: {FunctionType}
            list[index{int}][Map.data]:     {**kwargs}
        """
        if cls._QUEU_WRITE is None:
            cls._QUEU_WRITE = []
        return cls._QUEU_WRITE

    @classmethod
    def _join_write_queu(cls, callback: FunctionType, **kwargs) -> None:
        """
        To submit write request

        Parameters:
        -----------
        callback: FunctionType
            The write function to call
        **kwargs:
            Params to pass to the callback
        """
        from model.tools.Map import Map
        room = cls._get_writing_room()
        ticket = room.join_room()
        while not room.my_turn(ticket):
            time.sleep(0.0001)
        cls._get_write_queu().append({Map.callback: callback, Map.data: kwargs})
        cls._get_write_thread().start() if not cls._get_write_thread().is_alive() else None
        room.quit_room(ticket)

    @classmethod
    def _thread_write(cls) -> None:
        from model.tools.Map import Map
        write_queu = cls._get_write_queu()
        while len(write_queu) > 0:
            callback = write_queu[0][Map.callback]
            datas = write_queu[0][Map.data]
            callback(**datas)
            del write_queu[0]

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
        kwargs = {
            'path': path,
            'content': content,
            'binary': binary,
            'overwrite': overwrite,
            'make_dir': make_dir,
            'line_return': line_return
        }
        FileManager._join_write_queu(FileManager._write, **kwargs)

    @staticmethod
    def _write(path: str, content: Any, binary: bool = False, overwrite: bool = True, make_dir: bool = False, line_return=True) -> None:
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

    @classmethod
    def write_csv(cls, path: str, fields: list, rows: list, overwrite=True, make_dir: bool = False, ignore_extra=False) -> None:
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
        kwargs = {
            'path': path,
            'fields': fields,
            'rows': rows,
            'overwrite': overwrite,
            'make_dir': make_dir,
            'ignore_extra': ignore_extra
        }
        cls._join_write_queu(cls._write_csv, **kwargs)

    @classmethod
    def _write_csv(cls, path: str, fields: list, rows: list, overwrite=True, make_dir: bool = False, ignore_extra=False) -> None:
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
    def get_files(path: str, extension: bool = True, special: bool = False, make_dir: bool = False) -> List[str]:
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
    def get_dirs(path: str, special: bool = False, make_dir: bool = False) -> List[str]:
        """
         To list directories of a directory\n
         :param path: the path of the directory
         :param special: set True to include special directories else False.
                        Special file supported: .ignore, __pychache__
         :param make_dir: Set True create missing directory else False to raise error if miss directory
         :return: list of directories
         """
        path = path + '/' if path[-1] != '/' else path
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

    @classmethod
    def map_dir(cls, start_dir_path: str, file_regex: str = None, folder_regex: str = None) -> List[str]:
        """
        To get recursively file path of all files in the given directory

        Parameters:
        -----------
        start_dir_path: str
            Path of the directory to start from
            NOTE: Must be relative to the project's directory
        file_regex: str
            Regular expression that must match all file returned
            - r'.+'             -> will return all file found
            - r'^[\d]+\w\.csv'  -> will return files starting with a number followed by one letter and with the extension '.csv'
        
        folder_regex: str
            Regular expression that must match name of each folder to keep

        Returns:
        --------
        return: List[str]
            List of file path
            NOTE: paths are sorted in ascending order
        """
        concat_dir_path = start_dir_path
        file_paths = cls._rec_map_dir(concat_dir_path, file_regex, folder_regex)
        file_paths.sort()
        return file_paths

    @classmethod
    def _rec_map_dir(cls, concat_dir_path: str, file_regex: str = None, folder_regex: str = None) -> List[str]:
        def filter(regex: str, strings: List[str]) -> List[str]:
            return [string for string in strings if _MF.regex_match(regex, string)]
        # Files
        new_files = cls.get_files(concat_dir_path, special=True)
        filtered_files = new_files if file_regex is None else filter(file_regex, new_files)
        file_paths = [concat_dir_path + filtered_file for filtered_file in filtered_files]
        # Directories
        new_dirs = cls.get_dirs(concat_dir_path, special=True)
        filtered_dirs = new_dirs if folder_regex is None else filter(folder_regex, new_dirs)
        for filtered_dir in filtered_dirs:
            new_concat_dir_path = f'{concat_dir_path}{filtered_dir}/'
            file_paths = [
                *file_paths,
                *cls._rec_map_dir(new_concat_dir_path, file_regex, folder_regex)
                ]
        return file_paths

    @classmethod
    def exist_file(cls, file_path: str) -> bool:
        """
        To check if file exist

        Parameters:
        -----------
        file_path: str
            The path to the file to check existance of

        Return:
        -------
        return: bool
            True if file exist else False
        """
        from model.tools.Map import Map
        dir_path = cls.path_to_dir(file_path)
        file_name = file_path.replace(dir_path, "")
        files = _MF.catch_exception(cls.get_files, FileManager.__name__, repport=False, **{Map.path: dir_path})
        file_exist = (files is not None) and (file_name in files)
        return file_exist
