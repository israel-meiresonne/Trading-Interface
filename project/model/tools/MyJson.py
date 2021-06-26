from model.tools.FileManager import FileManager
from model.tools.Map import Map


class MyJson:
    _IMPORTS = None
    _TOKEN_CLASS_NAME = '$class_name'

    @staticmethod
    def _set_imports() -> None:
        token = MyJson._TOKEN_CLASS_NAME
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
        MyJson._IMPORTS = Map({
            **tool_imports,
            **struct_imports,
            **stg_imports,
        })

    @staticmethod
    def _generate_imports(token: str, class_dir: str, import_format: str, contain_file: bool) -> dict:
        class_names = FileManager.get_files(class_dir, extension=False) if contain_file else FileManager.get_dirs(class_dir)
        tool_imports = {class_name: import_format.replace(token, class_name) for class_name in class_names}
        return tool_imports

    @staticmethod
    def get_imports() -> Map:
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
            NName of the class  to  import

        Returns
        -------
        import_str: str
            Import instruction of the given class
        """
        import_str = MyJson.get_imports().get(class_name)
        if import_str is None:
            raise ValueError(f"Import instruction for this class '{class_name}' don't exist")
        return import_str
