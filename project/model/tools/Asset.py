class Asset:
    def __init__(self, sbl: str):
        self.__symbol = sbl.lower()
        self.__name = None

    def get_symbol(self) -> str:
        return self.__symbol

    def get_name(self) -> str:
        return self.__name

    def __eq__(self, other):
        return self.get_symbol() == other.get_symbol() and\
               self.get_name() == other.get_name()

    def __str__(self) -> str:
        return self.get_symbol()

    def __repr__(self) -> str:
        return self.__str__() + f"({id(self)})"
