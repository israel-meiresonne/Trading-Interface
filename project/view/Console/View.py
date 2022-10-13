import getpass
from typing import Any


class View:
    SEPARATOR = "——————————————————————————————"
    C_NORMAL =  '\033[0m'
    C_YELLOW =  '\033[33m'
    C_PURPLE =  '\033[35m'
    C_RED =     '\033[31m'
    C_GREEN =   '\033[32m'

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
        message = message + "\n" if message is not None else ""
        input_sufix = f'{self.C_PURPLE}>>>{self.C_NORMAL} '
        if secure:
            entry = getpass.getpass(message + input_sufix)
        else:
            entry = input(message + input_sufix)
        if (not secure) and (type_func is not None):
            converted = False
            while not converted:
                try:
                    entry = type_func(entry)
                    converted = True
                except Exception as e:
                    self.output(f"Can't convert entry '{entry}' into type '{type_func}'", is_error=True)
                    entry = input(input_sufix)
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

    def output(self, out: Any, is_error: bool = False, is_success: bool = False) -> None:
        """
        To display datas

        Parameters:
        -----------
        out: Any
            Datas to display
        is_error: bool = False
            Set True to display error message else False
        """
        if is_success:
            print(self.C_GREEN + out + self.C_NORMAL)
            return None
        if is_error:
            print(self.C_RED + out + self.C_NORMAL)
            return None
        print(out)

