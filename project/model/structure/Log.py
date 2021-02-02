from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy


class Log(ModelInterface, ModelFeature):
    def __init__(self):
        super(Log, self).__init__()
        self.bots = None

    def get_log_id(self):
        return self.log_id

    def __set_bots(self):
        self.bots = {}

    def get_bots(self) -> dict:
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
        bots = self.get_bots()
        if bot_id not in bots:
            raise Exception(f"There's no Bot with this id '{bot_id}'")
        return bots[bot_id]

    def create_bot(self, bkr: str, stg: str, prcd: str, cfgs=None):
        cfgs = {} if cfgs is None else cfgs
        cfgs[bkr] = {} if bkr not in cfgs else cfgs[bkr]
        bot = Bot(bkr, stg, prcd, cfgs)
        bt_id = bot.get_id()
        bts = self.get_bots()
        bts[bt_id] = bot

    def start_bot(self, bot_id):
        bot = self.__get_bot(bot_id)
        bot.start()

    def stop_bot(self, bot_id):
        pass

    def stop_bots(self):
        pass

    def list_brokers(self):
        return Broker.list_brokers()

    def list_paires(self, bkr: str):
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+".list_paires()")

    def list_strategies(self):
        return Strategy.list_strategies()
