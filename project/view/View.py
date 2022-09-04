import getpass
from typing import Any


class View:
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
        if secure:
            entry = getpass.getpass(message)
        else:
            entry = input(message)
        if (not secure) and (type_func is not None):
            converted = False
            while not converted:
                try:
                    entry = type_func(entry)
                    converted = True
                except Exception as e:
                    self.output(f"Can't convert entry '{entry}' into type '{type_func}'", is_error=True)
                    entry = input()
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
            self.output(f"Option '{entry}' don't exit in menu", is_error=True) if not success else None
        index = entry if isinstance(entry, int) else options.index(entry)
        return index

    def output(self, out: Any, is_error: bool = False) -> None:
        """
        To display datas

        Parameters:
        -----------
        out: Any
            Datas to display
        is_error: bool = False
            Set True to display error message else False
        """
        print('\033[93m', out, '\033[0m') if is_error else print(out)

