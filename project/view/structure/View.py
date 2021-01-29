from view.ViewInterface import ViewInterface
from view.tools.Buffer import Buffer


class View(ViewInterface):
    FILE_MESSAGE = "message"
    FILE_ERROR = "error"
    MENUS_KEY_TXT = "choices"
    MENUS_KEY_FUNC = "func"
    __MENUS = {
        "home": {
            "choices": ["quit",
                        "new Bot",
                        "start Bot",
                        "stop Bot",
                        "stop Bots"
                        ],
            "func": [
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

    def input(self, t=None):
        v = input()
        if t is not None:
            s = False
            while not s:
                try:
                    # exec("v = "+t+"(v)")
                    v = eval(t + "(v)")
                    s = True
                except BaseException as e:
                    self.output(View.FILE_ERROR, e.__str__())
                    v = input()
        return v

    def menu(self, cs: list) -> str:
        """
        To display a list as menu choices
        :param cs: list of choices
        :return: the menu choice selected
        """
        self.output("menu", cs)
        s = False
        while not s:
            v = self.input("int")
            s = (0 <= v < len(cs))
            self.output(View.FILE_ERROR, "Option '{}' don't exit in menu".format(v)) \
                if not s else None
        return v

    def output(self, f: str, vd=None) -> None:
        print(self.__generate_file(f, vd))

    def __generate_file(self, fc: str, vd=None) -> str:
        c = ""
        with Buffer() as ls:
            exec("from view.files.view_func import " + fc)
            exec(fc + "(vd)")
        for x in ls:
            c += x + "\n"
        return c
