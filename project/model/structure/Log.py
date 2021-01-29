from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature
from model.structure import Bot


class Log(ModelInterface, ModelFeature):
    def __init__(self):
        super(Log, self).__init__()
        self.bots = None

    def get_log_id(self):
        return self.log_id

    def __set_bots(self):
        self.bots = {}

    def __get_bots(self):
        """
         To get Log's set of Bot\n
         @:return\n
            dict: set of Bot
        """
        self.__set_bots() if (self.bots is None) else None
        return self.bots

    def __get_bot(self, bot_id: str) -> Bot:
        """
        To get the Bot with the given id\n
        :param bot_id: a Bot's id
        :return: the Bot of the given id
        """
        pass

    def create_bot(self):
        pass

    def start_bot(self, bot_id):
        pass

    def stop_bot(self, bot_id):
        pass

    def stop_bots(self):
        pass
