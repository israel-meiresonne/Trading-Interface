from view.ViewInterface import ViewInterface
from view.tools.Buffer import Buffer
from model.tools.Map import Map


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

    def input(self, msg=None, t=None) -> [str, int, float, bool]:
        print(msg) if msg is not None else None
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

    def menu(self, msg: str, cs: list) -> int:
        """
        To display a list as menu choices
        :param cs: list of choices
        :param msg: message to display
        :return: the menu choice selected
        """
        dv_mp = Map({Map.msg: msg, Map.cs: cs})
        self.output("menu", dv_mp)
        s = False
        while not s:
            v = self.input(t="int")
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
