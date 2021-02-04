class Asset:
    def __init__(self, sbl: str):
        self.__symbol = sbl.lower()
        self.__name = None

    def get_symbol(self) -> str:
        return self.__symbol
