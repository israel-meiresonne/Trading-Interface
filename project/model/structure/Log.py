from typing import Any, Dict, List
from config.Config import Config
from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.structure.strategies.Hand.Hand import Hand
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Log(ModelInterface, _MF):
    PREFIX_ID = 'log_'
    _BOT_THREADS = None

    def __init__(self):
        super().__init__(Log.PREFIX_ID)
        self.__bots =   None
        self.__hands =  None

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

    def start_bot(self, bot_id: str) -> None:
        bot = self.get_bot(bot_id)
        base_name = bot_id
        thread, output = _MF.generate_thread(bot.start, base_name, n_code=None)
        thread.start()
        self.get_bot_threads().put(thread, bot_id)
        _MF.output(_MF.prefix() + output)

    def stop_bot(self, bot_id: str) -> None:
        bot = self.get_bot(bot_id)
        bot.stop()
        bot_thread = self.get_bot_threads().get(bot_id)
        bot_thread.join() if (bot_thread is not None) and bot_thread.is_alive() else None

    def stop_bots(self):
        pass

    # ——————————————————————————————————————————— FUNCTION HAND DOWN ——————————————————————————————————————————————————

    def  resset_hands(self) -> None:
        self.__hands = None

    def new_hand(self, capital: float, asset: str, broker_class: str) -> str:
        import_exec = _MF.get_import(broker_class)
        exec(import_exec)
        broker_class = eval(broker_class)
        capital = Price(capital, asset)
        hand = Hand(capital, broker_class)
        self._add_hand(hand)
        hand.backup()
        return hand.get_id()

    def _get_hands(self) -> Dict[str, Hand]:
        if self.__hands is None:
            self.__hands = {}
        return self.__hands

    def _get_hand(self, hand_id: str) -> Hand:
        hands = self._get_hands()
        if hand_id not in hands:
            hand = Hand.load(hand_id)
            self._add_hand(hand)
        hand = hands[hand_id]
        return hand

    def _add_hand(self, hand: Hand) -> None:
        hands = self._get_hands()
        hand_id = hand.get_id()
        hands[hand_id] = hand

    def start_hand(self, hand_id: str, public_key: str, secret_key: str, is_test_mode: bool) -> None:
        hand = self._get_hand(hand_id)
        broker_class = hand.get_broker_class()
        broker_params = Map({
            Map.public: public_key,
            Map.secret: secret_key,
            Map.test_mode: is_test_mode
        })
        broker = Broker.retrieve(broker_class, broker_params)
        hand.set_broker(broker)
        hand.add_streams()
        hand.set_stalk_on(on=True)
        hand.set_position_on(on=True)
        hand.set_market_analyse_on(on=True)
        hand.backup()

    def stop_hand(self, hand_id: str) -> None:
        hand = self._get_hand(hand_id)
        hand.set_stalk_on(on=False)
        hand.set_position_on(on=False)
        hand.set_market_analyse_on(on=False)
        hand.backup()

    def stop_hands(self) -> None:
        hands = self._get_hands()
        [self.stop_hand(hand_id) for hand_id in hands]

    def buy_hand_position(self, hand_id: str, pair: str, order_type: str, stop: float = None, limit: float = None, buy_function: str = None) -> None:
        hand = self._get_hand(hand_id)
        pair = Pair(pair)
        r_asset = pair.get_right()
        stop = Price(stop, r_asset) if stop is not None else None
        limit = Price(limit, r_asset) if limit is not None else None
        buy_function = buy_function if buy_function is not None else None
        hand.buy(pair, order_type, stop, limit, buy_function)

    def sell_hand_position(self, hand_id: str, pair: str, order_type: str, stop: float = None, limit: float = None, sell_function: str = None) -> None:
        hand = self._get_hand(hand_id)
        pair = Pair(pair)
        r_asset = pair.get_right()
        stop = Price(stop, r_asset) if stop is not None else None
        limit = Price(limit, r_asset) if limit is not None else None
        sell_function = sell_function if sell_function is not None else None
        hand.sell(pair, order_type, stop, limit, sell_function)

    def cancel_hand_position(self, hand_id: str, pair: str) -> None:
        hand = self._get_hand(hand_id)
        pair = Pair(pair)
        hand.cancel(pair)

    def set_hand_attribut(self, hand_id: str, attribut: str, value: Any) -> Any:
        hand = self._get_hand(hand_id)
        if attribut == Map.maximum:
            hand.set_max_position(value)
        else:
            raise ValueError(f"Unkwon attribut from Hand '{attribut}'")

    def get_hand_attribut(self, hand_id: str, attribut: str) -> Any:
        value = None
        hand = self._get_hand(hand_id)
        if attribut == Map.broker:
            value = hand.get_broker_class()
        elif attribut == Map.position:
            positions = hand.get_positions().copy()
            value = [position.get_buy_order().get_pair() for _, position in positions.items()]
        elif attribut == Map.sell:
            positions = hand.get_positions().copy()
            value = [position.get_buy_order().get_pair() for _, position in positions.items() if position.has_position()]
        elif attribut == Map.cancel:
            positions = hand.get_positions().copy()
            value = []
            for _, position in positions.items():
                buy_is_cancelable = not position.is_executed(Map.buy)
                sell_is_cancelable = (position.get_sell_order() is not None) and (not position.is_executed(Map.sell))
                value.append(position.get_buy_order().get_pair()) if (buy_is_cancelable or sell_is_cancelable) else None
        elif attribut == Map.capital:
            value = hand.get_wallet().get_initial()
        elif attribut == Map.pair:
            value = hand.get_broker_pairs()
        elif attribut == Map.start:
            value = hand.is_position_on() and hand.is_stalk_on()
        elif attribut == Map.maximum:
            value = hand.get_max_position()
        elif attribut == Map.algo:
            positions = hand.get_positions().copy()
            value = [position.get_buy_order().get_pair() for _, position in positions.items() if position.get_sell_order() is not None]
        else:
            raise ValueError(f"Unkwon attribut from Hand '{attribut}'")
        return value

    @classmethod
    def list_hand_ids(cls) -> List[str]:
        return Hand.list_hand_ids()

    # ——————————————————————————————————————————— FUNCTION HAND UP ————————————————————————————————————————————————————

    @classmethod
    def get_bot_threads(cls) -> Map:
        """
        To get thread running Bot with the given id

        Parameters:
        -----------
        bot_id: str
            ID of Bot to get thread of

        Returns:
        --------
        return: dict[str, threading.Thread]
            All thread running bot
            dict[bot_id{str}]:  {Thread}
        """
        if cls._BOT_THREADS is None:
            cls._BOT_THREADS = Map()
        return cls._BOT_THREADS

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

    @classmethod
    def close_brokers(cls) -> None:
        brokers = cls.list_brokers()
        for broker in brokers:
            exec(f"from model.API.brokers.{broker}.{broker} import {broker}")
            exec(f"{broker}.close()")

    @classmethod
    def get_order_types(cls) -> List[str]:
        return Order.TYPES
