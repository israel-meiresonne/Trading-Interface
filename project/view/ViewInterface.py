from abc import ABC, abstractmethod


class ViewInterface(ABC):
    @abstractmethod
    def input(self, t=None):
        """
        To get input value\n
        :param t: function name to convert input into that type
        (i.e: str(), int(),...)
        :return: the value entered
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

