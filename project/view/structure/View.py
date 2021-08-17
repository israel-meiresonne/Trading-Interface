import getpass

from view.ViewInterface import ViewInterface
from view.tools.Buffer import Buffer
from model.tools.Map import Map


class View(ViewInterface):
    FILE_MESSAGE = "message"
    FILE_ERROR = "error"
    WORD_END = "end"
    MENUS_KEY_HOME = "home"
    MENUS_KEY_OPTION = "option"
    MENUS_KEY_FUNC = "func"
    __MENUS = {
        MENUS_KEY_HOME: {
            MENUS_KEY_OPTION: ["quit",
                               "new Bot",
                               "start Bot",
                               "stop Bot",
                               "stop Bots"
                               ],
            MENUS_KEY_FUNC: [
                "quit",
                "new_bot",
                "start_bot",
                "stop_bot",
                "stop_bots"
            ]
        }
    }

    @staticmethod
    def get_menus():
        return View.__MENUS

    def input(self, message: str = None, type_func: str = None, secure: bool = False) -> [str, int, float, bool]:
        """
        To input value\n
        :param message: Message to display
        :param type_func: Function used to convert input into a other type
        :param secure: Set True to hide input in console else False to display input typed
        :return: the value typed
        """
        message = message + "\n" if message is not None else ""
        if secure:
            v = getpass.getpass(message)
        else:
            v = input(message)
        if not secure and type_func is not None:
            s = False
            while not s:
                try:
                    v = eval(type_func + "(v)")
                    s = True
                except BaseException as e:
                    self.output(View.FILE_ERROR, e.__str__())
                    v = input()
        return v

    def menu(self, msg: str, choices: list) -> int:
        """
        To display a list as menu choices
        :param choices: list of choices
        :param msg: message to display
        :return: the menu choice selected
        """
        dv_mp = Map({Map.message: msg, Map.response: choices})
        self.output("menu", dv_mp)
        success = False
        while not success:
            entry = self.input()
            if View.check_int(entry):
                entry = int(entry)
                success = (0 <= entry < len(choices))
            else:
                success = entry in choices
            self.output(View.FILE_ERROR, "Option '{}' don't exit in menu".format(entry)) if not success else None
        index = entry if isinstance(entry, int) else choices.index(entry)
        return index

    @staticmethod
    def check_int(s: str) -> bool:
        if s[0] in ('-', '+'):
            return s[1:].isdigit()
        return s.isdigit()

    def output(self, f: str, vd=None) -> None:
        print(self.__generate_file(f, vd))

    @staticmethod
    def __generate_file(fc: str, vd=None) -> str:
        c = ""
        with Buffer() as ls:
            exec("from view.files.view_func import " + fc)
            exec(fc + "(vd)")
        for x in ls:
            c += x + "\n"
        return c
