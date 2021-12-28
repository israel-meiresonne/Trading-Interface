from abc import ABC, abstractmethod
from collections import Iterable
from typing import Any

import numpy as np

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager


class MyJson(ABC):
    _TOKEN_CLASS_NAME = '@class_name'
    _TOKEN_ITERABLE = '@'
    _REGEX_REPLACE_ATTRIBUTE = f'^.+{_TOKEN_CLASS_NAME}'
    _EXECUTABLE_json_instantiate = None
    _EXECUTABLE_test_json_encode_decode = None
    _IMPORTS = None

    def json_encode(self) -> str:
        """
        To convert a custom class object to a JSON string\n
        Returns
        -------
        serialized: str
            Custom class object's JSON string
        """
        self._json_encode_prepare()
        _class_token = MyJson.get_class_name_token()
        class_name = self.__class__.__name__
        attrs = self._json_encode_to_dict()
        json_dict = {_class_token: class_name}
        for attr, value in attrs.items():
            value_serialized = MyJson.__root_encoding(value)
            json_dict[attr] = value_serialized
        json_str = _MF.json_encode(json_dict)
        return json_str
    
    def _json_encode_prepare(self) -> None:
        """
        To prepare Object to be encoded
        NOTE: first function called in function MyJson.json_encode()
        """
        pass
    
    def _json_encode_to_dict(self) -> dict:
        """
        To convert Object to dict
        """
        return self.__dict__

    def copy(self) -> object:
        obj_copy = MyJson.json_decode(self.json_encode())
        return obj_copy        

    @staticmethod
    def __root_encoding(value: Any) -> Any:
        serializables = MyJson.get_imports().get_keys()
        class_name = value.__class__.__name__
        if class_name == 'Thread':
            value_serialized = None
        elif class_name in serializables:
            value_serialized = _MF.json_decode(value.json_encode())
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            value_serialized = MyJson.__encode_iterable(value)
        else:
            value_serialized = value
        return value_serialized

    @staticmethod
    def __encode_iterable(iterable_value: Iterable) -> Iterable:
        iter_type = type(iterable_value)
        if iter_type == dict:
            value_encoded = {}
            for key, value in iterable_value.items():
                iter_token = MyJson._TOKEN_ITERABLE
                json_key = f"{key.__class__.__name__}{iter_token}{key}"
                value_encoded[json_key] = MyJson.__root_encoding(value)
        elif (iter_type == list) or (iter_type == tuple):
            iter_name = iter_type.__name__
            value_encoded = [iter_name]
            for value in iterable_value:
                value_encoded.append(MyJson.__root_encoding(value))
        elif iter_type == np.ndarray:
            iter_name = iter_type.__name__
            np_list = iterable_value.tolist()
            np_list_json = MyJson.__root_encoding(np_list)
            value_encoded = [iter_name, np_list_json]
        else:
            raise ValueError(f"This iterable type '{iter_type}' is not supported")
        return value_encoded

    @staticmethod
    def get_class_name_token() -> str:
        return MyJson._TOKEN_CLASS_NAME

    @staticmethod
    def _set_imports() -> None:
        token = MyJson.get_class_name_token()
        # Import tools
        tools_dir = 'model/tools/'
        tools_format = f'from model.tools.{token} import {token}'
        tool_imports = MyJson._generate_imports(token, tools_dir, tools_format, contain_file=True)
        # Import structure
        structure_dir = 'model/structure/'
        struc_format = f'from model.structure.{token} import {token}'
        struct_imports = MyJson._generate_imports(token, structure_dir, struc_format, contain_file=True)
        # Import strategies
        stg_dir = 'model/structure/strategies/'
        stg_format = f'from model.structure.strategies.{token}.{token} import {token}'
        stg_imports = MyJson._generate_imports(token, stg_dir, stg_format, contain_file=False)
        # Import brokers
        bkr_folder_dir = 'model/API/brokers/'
        bkr_classes = FileManager.get_dirs(bkr_folder_dir)
        bkr_imports = {}
        for bkr_class in bkr_classes:
            bkr_dir = f'{bkr_folder_dir}{bkr_class}/'
            bkr_format = f'from model.API.brokers.{bkr_class}.{token} import {token}'
            bkr_imports = {
                **bkr_imports,
                **MyJson._generate_imports(token, bkr_dir, bkr_format, contain_file=True)
            }
        from model.tools.Map import Map
        MyJson._IMPORTS = Map({
            **tool_imports,
            **struct_imports,
            **stg_imports,
            **bkr_imports
        })

    @staticmethod
    def _generate_imports(token: str, class_dir: str, import_format: str, contain_file: bool) -> dict:
        class_names = FileManager.get_files(class_dir, extension=False) if contain_file else FileManager.get_dirs(class_dir)
        tool_imports = {class_name: import_format.replace(token, class_name) for class_name in class_names}
        return tool_imports

    @staticmethod
    def get_imports() -> 'Map':
        if MyJson._IMPORTS is None:
            MyJson._set_imports()
        return MyJson._IMPORTS

    @staticmethod
    def get_import(class_name: str) -> str:
        """
        To get import instruction of the given class\n
        Parameters
        ----------
        class_name: str
            Name of the class  to  import

        Returns
        -------
        import_str: str
            Import instruction of the given class
        """
        import_str = MyJson.get_imports().get(class_name)
        if import_str is None:
            raise ValueError(f"Import instruction for this class '{class_name}' don't exist")
        return import_str

    @staticmethod
    def get_executable() -> str:
        if MyJson._EXECUTABLE_json_instantiate is None:
            from config.Config import Config
            path = Config.get(Config.FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE)
            MyJson._EXECUTABLE_json_instantiate = FileManager.read(path)
        return MyJson._EXECUTABLE_json_instantiate

    @staticmethod
    def get_executable_test_json_encode_decode() -> str:
        if MyJson._EXECUTABLE_test_json_encode_decode is None:
            from config.Config import Config
            path = Config.get(Config.FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE)
            MyJson._EXECUTABLE_test_json_encode_decode = FileManager.read(path)
        return MyJson._EXECUTABLE_test_json_encode_decode

    @staticmethod
    def json_decode(json_str: str) -> object:
        """
        To decode JSON string of custom class object\n
        Parameters
        ----------
        json_str: str
            Json string to decode

        Returns
        -------
        custom_object: object
            Custom class object
        """
        _class_token = MyJson.get_class_name_token()
        object_dic = _MF.json_decode(json_str)
        if not isinstance(object_dic, dict):
            raise ValueError(f"Type of JSON object must be dict, instead '{type(object_dic)}'")
        json_obj = MyJson._generate_instance(object_dic)
        return json_obj

    @staticmethod
    def _root_decoding(value: Any) -> Any:
        _class_token = MyJson.get_class_name_token()
        if isinstance(value, dict) and (_class_token in value):
            decoded_value = MyJson._generate_instance(value)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            decoded_value = MyJson.__decode_iterable(value)
        else:
            decoded_value = value
        return decoded_value

    @staticmethod
    def __decode_iterable(iterable_value: Iterable) -> Iterable:
        iterable_value_copy = iterable_value.copy()
        iter_type = type(iterable_value_copy)
        if iter_type == dict:
            value_decoded = {}
            for json_key, value in iterable_value_copy.items():
                iter_token = MyJson._TOKEN_ITERABLE
                key_type, str_key = json_key.split(iter_token)
                key = eval(f"{key_type}(str_key)")
                value_decoded[key] = MyJson._root_decoding(value)
        elif iter_type == list:
            list_type = iterable_value_copy[0]
            del iterable_value_copy[0]
            if (list_type == list.__name__) or (list_type == tuple.__name__):
                value_decoded = []
                for value in iterable_value_copy:
                    value_decoded.append(MyJson._root_decoding(value))
                value_decoded = eval(f"{list_type}(value_decoded)")
            elif list_type == np.ndarray.__name__:
                np_list = MyJson._root_decoding(iterable_value_copy[0])
                value_decoded = np.array(np_list)
            else:
                raise ValueError(f"This list type '{list_type}' is not supported")
        else:
            raise ValueError(f"This iterable type '{iter_type}' is not supported")
        return value_decoded

    @staticmethod
    def _generate_instance(object_dic: dict) -> object:
        """
        To instantiate new given class with given attributes\n
        Parameters
        ----------
        object_dic: dic
            Attributes for new instance
        Returns
        -------
        instance: object
            New instance of given class
        """
        _class_token = MyJson.get_class_name_token()
        if _class_token not in object_dic:
            raise KeyError(f"Miss key '{_class_token}' in JSON object")
        class_name = object_dic[_class_token]
        import_exec = MyJson.get_import(class_name)
        exec(import_exec)
        instnace = eval(f"{class_name}.json_instantiate({object_dic})")
        return instnace

    @staticmethod
    @abstractmethod
    def json_instantiate(object_dic: dict) -> object:
        """
        To instantiate class with given attributes\n
        Parameters
        ----------
        object_dic: dict
            Attributes to instantiate class

        Returns
        -------
        instance: object
            Class instance
        """
        pass

    def __eq__(self, other) -> bool:
        self_dict = self.__dict__
        other_dict = other.__dict__
        return (type(self) == type(other)) and (self_dict == other_dict)
