import getpass
from typing import Any, List
from config.Config import Config

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.FileManager import FileManager


class View:
    SEPARATOR =         "——————————————————————————————"
    REGEX_RICH =        r'^\\033\[([0-4]|(3|4|9|10)[0-7]){1}m'
    RECORD_OUTPUT =     False
    OPTIONS_BOOLEAN =   {'No': False, 'Yes': True}
    # Styles
    S_NORMAL =          '\033[0m'
    S_BOLD =            '\033[1m'
    S_FAINT =           '\033[2m'
    S_ITALIC =          '\033[3m'
    S_UNDERLINE =       '\033[4m'
    # Colors
    C_BLACK =           '\033[30m'
    C_RED =             '\033[31m'
    C_GREEN =           '\033[32m'
    C_YELLOW =          '\033[33m'
    C_BLUE =            '\033[34m'
    C_MAGENTA =         '\033[35m'
    C_CYAN =            '\033[36m'
    C_LIGHT_GRAY =      '\033[37m'
    C_GRAY =            '\033[90m'
    C_LIGHT_RED =       '\033[91m'
    C_LIGHT_GREEN =     '\033[92m'
    C_LIGHT_YELLOW =    '\033[93m'
    C_LIGHT_BLUE =      '\033[94m'
    C_LIGHT_MAGENTA =   '\033[95m'
    C_LIGHT_CYAN =      '\033[96m'
    C_WHITE =           '\033[97m'
    # Background
    B_BLACK =           '\033[40m'
    B_RED =             '\033[41m'
    B_GREEN =           '\033[42m'
    B_YELLOW =          '\033[43m'
    B_BLUE =            '\033[44m'
    B_MAGENTA =         '\033[45m'
    B_CYAN =            '\033[46m'
    B_LIGHT_GRAY =      '\033[47m'
    B_GRAY =            '\033[100m'
    B_LIGHT_RED =       '\033[101m'
    B_LIGHT_GREEN =     '\033[102m'
    B_LIGHT_YELLOW =    '\033[103m'
    B_LIGHT_BLUE =      '\033[104m'
    B_LIGHT_MAGENTA =   '\033[105m'
    B_LIGHT_CYAN =      '\033[106m'
    B_WHITE =           '\033[107m'
    STYLES = [S_NORMAL, S_BOLD, S_FAINT, S_ITALIC, S_UNDERLINE,
    C_BLACK, C_RED, C_GREEN, C_YELLOW, C_BLUE, C_MAGENTA, C_CYAN, 
    C_LIGHT_GRAY, C_GRAY, C_LIGHT_RED, C_LIGHT_GREEN, C_LIGHT_YELLOW, 
    C_LIGHT_BLUE, C_LIGHT_MAGENTA, C_LIGHT_CYAN, C_WHITE, B_BLACK, 
    B_RED, B_GREEN, B_YELLOW, B_BLUE, B_MAGENTA, B_CYAN, B_LIGHT_GRAY, 
    B_GRAY, B_LIGHT_RED, B_LIGHT_GREEN, B_LIGHT_YELLOW, B_LIGHT_BLUE, 
    B_LIGHT_MAGENTA, B_LIGHT_CYAN, B_WHITE
    ]

    def input(self, message: str = None, type_func: Any = None, secure: bool = False) -> Any:
        """
        To input value

        Parameters:
        -----------
        message: str = None
            Message to display
        type_func: Union[FunctionType, MethodType] = None
            Function used to convert input into a other type
        secure: bool = False
            Set True to hide input in console else False to display input

        Returns:
        --------
        return: Any
            The input typed
        """
        is_message_none = message is None
        message = "" if is_message_none else message + "\n"
        prefix = (lambda : "") if is_message_none else (lambda : self.prefix())
        input_sufix = f'{self.C_MAGENTA}>>>{self.S_NORMAL} '
        if secure:
            entry = self._input(self.prefix() + message + prefix() + input_sufix, secure)
        else:
            entry = self._input(self.prefix() + message + prefix() + input_sufix)
        if (not secure) and (type_func is not None):
            converted = False
            while not converted:
                try:
                    entry = type_func(entry)
                    converted = True
                except Exception as e:
                    self.output(f"Can't convert entry '{entry}' into type '{type_func}'", is_error=True)
                    entry = self._input(self.prefix() + input_sufix)
        return entry

    def menu(self, message: str, options: list) -> int:
        """
        To display a list as menu with options and read the option selected

        Parameters:
        -----------
        message: str
            Message to display
        options: list
            Menu's list of options

        Returns:
        --------
        return: int
            Index from list of option corresponding to the selected option
        """
        def display_choices(choices: list):
            for i in range(len(choices)):
                o = f"{i}. {choices[i]}"
                self.output(o)

        if len(options) == 0:
            raise ValueError(f"The list of option can't be empty")
        self.output(self.SEPARATOR)
        self.output(message)
        display_choices(options)
        n_choice = len(options)
        success = False
        while not success:
            entry = self.input()
            if entry.isdigit():
                entry = int(entry)
                success = (0 <= entry < n_choice)
            else:
                success = entry in options
            self.output(f"This option '{entry}' don't exist in menu", is_error=True) if not success else None
        index = entry if isinstance(entry, int) else options.index(entry)
        self.output(self.SEPARATOR)
        return index

    def output(self, out: Any, is_error: bool = False, is_success: bool = False, richs: List[str] = None) -> None:
        """
        To display datas

        Parameters:
        -----------
        out: Any
            Datas to display
        is_error: bool = False
            Set True to display error message else False
        """
        if richs:
            for rich in richs:
                if rich not in self.STYLES:
                    raise ValueError(f"This style '{rich}' is not supported")
            style = ''.join(richs)
            self._print(style + out + self.S_NORMAL)
            return None
        if is_success:
            self._print(self.C_GREEN + out + self.S_NORMAL)
            return None
        if is_error:
            self._print(self.C_LIGHT_RED + out + self.S_NORMAL)
            return None
        self._print(out)

    def ask_boolean(self, message: str) -> bool:
        """
        To ask a boolean question

        Parameters:
        -----------
        message: str
            The boolean question

        Return:
        -------
        return: bool
            The response to the boolean question
        """
        bool_menu = self.OPTIONS_BOOLEAN
        bool_options = list(bool_menu.keys())
        response = bool_menu[bool_options[self.menu(message, bool_options)]]
        return response

    @classmethod
    def prefix(cls) -> str:
        return cls.S_ITALIC + _MF.prefix() + cls.S_NORMAL

    @classmethod
    def _input(cls, message: str, secure: bool = False) -> str:
        entry = secret = ""
        if secure:
            secret = getpass.getpass(message)
        else:
            entry = input(message)
        cls._record_ouput(message + entry) if cls.RECORD_OUTPUT else None
        return entry + secret

    @classmethod
    def _print(cls, output: str) -> str:
        output = cls.prefix() + output
        cls._record_ouput(output) if cls.RECORD_OUTPUT else None
        print(output)

    @classmethod
    def _record_ouput(cls, output: str) -> None:
        file_path = Config.get(Config.FILE_VIEW_OUTPUT)
        FileManager.write(file_path, output, overwrite=False, make_dir=True)
