from model.tools.MyJson import MyJson


class Asset(MyJson):
    def __init__(self, sbl: str):
        self.__symbol = sbl.lower()
        self.__name = None

    def get_symbol(self) -> str:
        return self.__symbol

    def get_name(self) -> str:
        return self.__name

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Asset('@json')
        exec(MyJson.get_executable())
        return instance

    def __eq__(self, other):
        return self.get_symbol() == other.get_symbol() and\
               self.get_name() == other.get_name()

    def __str__(self) -> str:
        return self.get_symbol()

    def __repr__(self) -> str:
        return self.__str__()
