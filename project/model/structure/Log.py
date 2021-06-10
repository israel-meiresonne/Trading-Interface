from config.Config import Config
from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map


class Log(ModelInterface, _MF):
    PREFIX_ID = 'log_'

    def __init__(self):
        # super(Log, self).__init__(Log.PREFIX_ID)
        super().__init__(Log.PREFIX_ID)
        self.__bots = None

    def get_log_id(self):
        return self.log_id

    def __set_bots(self):
        self.__bots = Map()
        _stage = Config.get(Config.STAGE_MODE)
        path = Config.get(Config.DIR_DATABASE)
        bot_dir = path.replace('$stage', _stage).replace('$class', Bot.__name__)
        bot_files = FileManager.get_files(bot_dir)
        for bot_file in bot_files:
            bot_file_path = bot_dir + bot_file
            bot = FileManager.read(bot_file_path, binary=True)
            self._add_bot(bot)

    def _add_bot(self, bot: Bot) -> None:
        self.get_bots().put(bot, bot.get_id())

    def get_bots(self) -> Map:
        """
         To get Log's set of Bot\n
         @:return\n
            dict: set of Bot
        """
        self.__set_bots() if (self.__bots is None) else None
        return self.__bots

    def get_bot(self, bot_id: str) -> Bot:
        """
        To get the Bot with the given id\n
        :param bot_id: a Bot's id
        :return: the Bot of the given id
        """
        bots = self.get_bots()
        if bot_id not in bots.get_keys():
            raise Exception(f"There's no Bot with this id '{bot_id}'")
        return bots.get(bot_id)

    def create_bot(self, bkr: str, stg: str, prcd: str, configs: Map):
        configs = Map() if configs is None else configs
        ks = configs.get_keys()
        configs.put(Map(), bkr) if bkr not in ks else None
        configs.put(Map(), stg) if stg not in ks else None
        bot = Bot(bkr, stg, prcd, configs)
        self._add_bot(bot)

    def start_bot(self, bot_id):
        bot = self.get_bot(bot_id)
        bot.start()

    def stop_bot(self, bot_id):
        pass

    def stop_bots(self):
        pass

    @staticmethod
    def list_brokers():
        return Broker.list_brokers()

    @staticmethod
    def list_paires(bkr: str):
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+".list_paires()")

    @staticmethod
    def list_strategies():
        return Strategy.list_strategies()
