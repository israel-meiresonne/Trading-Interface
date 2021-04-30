from abc import ABC, abstractmethod


class ViewInterface(ABC):
    @abstractmethod
    def input(self, message: str = None, type_func: str = None, secure: bool = False) -> [str, int, float, bool]:
        """
        To input value\n
        :param message: Message to display
        :param type_func: Function used to convert input into a other type
        :param secure: Set True to hide input in console else False to display input typed
        :return: the value typed
        """
        pass

    '''
    @abstractmethod
    def menu(self, menu: list) -> str:
        """
        To select a value in a menu\n
        :param menu: list of menu option
        :return: the selected value
        """
        pass
    '''

    @abstractmethod
    def output(self, f: str, vd=None) -> None:
        """
        To display data\n
        :param f: the file to load to display data
        :param vd: data view to display
        """
        pass

    '''
    @abstractmethod
    def error(self, file: str, view_data: dict) -> None:
        """
        To display errors\n
        :param file: the file to load to display data
        :param view_data: error data to display
        """
        pass
    '''

