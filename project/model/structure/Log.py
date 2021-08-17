from config.Config import Config
from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson


class Log(ModelInterface, _MF):
    PREFIX_ID = 'log_'

    def __init__(self):
        super().__init__(Log.PREFIX_ID)
        self.__bots = None

    def get_log_id(self):
        return self.log_id

    def _set_bots(self):
        self.__bots = Map()
        _stage = Config.get(Config.STAGE_MODE)
        path = Config.get(Config.DIR_DATABASE)
        bot_id_dir = path.replace('$stage', _stage).replace('$class', Bot.__name__)
        bot_id_folders = FileManager.get_dirs(bot_id_dir, make_dir=True)
        for bot_id_folder in bot_id_folders:
            bot_backup_dir = f"{bot_id_dir}{bot_id_folder}/"
            bot_backup_files = FileManager.get_files(bot_backup_dir)
            for bot_backup_file in bot_backup_files:
                bot_file_path = bot_backup_dir + bot_backup_file
                json_str = FileManager.read(bot_file_path, binary=False)
                bot = MyJson.json_decode(json_str)
                bot_id = bot.get_id()
                if (self.__bots is not None) and (bot_id in self.get_bots().get_keys()):
                    bot_in = self.get_bot(bot_id)
                    new_is_newest = bot.get_last_backup() > bot_in.get_last_backup()
                    self._add_bot(bot) if new_is_newest else None
                else:
                    self._add_bot(bot)

    def _add_bot(self, bot: Bot) -> None:
        self.get_bots().put(bot, bot.get_id())

    def get_bots(self) -> Map:
        """
         To get Log's set of Bot\n
         @:return\n
            dict: set of Bot
        """
        self._set_bots() if self.__bots is None else None
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

    def create_bot(self, broker: str, strategy: str, pair_str: str, configs: Map) -> Bot:
        configs = Map() if configs is None else configs
        ks = configs.get_keys()
        configs.put(Map(), broker) if broker not in ks else None
        configs.put(Map(), strategy) if strategy not in ks else None
        bot = Bot(broker, strategy, configs)
        self._add_bot(bot)
        bot.backup()
        return bot

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
