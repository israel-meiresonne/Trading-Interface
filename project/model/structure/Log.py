from typing import Any, Dict, List, Union
from config.Config import Config
from model.ModelInterface import ModelInterface
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Bot import Bot
from model.structure.Broker import Broker
from model.structure.Hand import Hand
from model.structure.strategies.Strategy import Strategy
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class Log(ModelInterface, _MF):
    def __init__(self):
        super().__init__()
        self.__bots =   None
        self.__hands =  None

    # ——————————————————————————————————————————— FUNCTION BOT DOWN ———————————————————————————————————————————————————

    def resset_bots(self) -> None:
        self.__bots = None

    def _get_bots(self) -> Dict[str, Bot]:
        """
        To get collection of Bot

        Returns:
        --------
        return: Dict[str, Bot]
            Collection of Bot

            bots[bot_id{str}] -> {Bot}
        """
        bots = self.__bots
        if bots is None:
            self.__bots = bots = {}
        return bots

    def new_bot(self, capital_num: float, asset_str: str, strategy_str: str, broker_str: str, pair_str: str = None) -> str:
        exec(_MF.get_import(broker_str))
        exec(_MF.get_import(strategy_str))
        broker_class = eval(broker_str)
        strategy_class = eval(strategy_str)
        capital = Price(capital_num, asset_str)
        pair = Pair(pair_str) if pair_str is not None else None
        bot = Bot(capital, strategy_class, broker_class, pair)
        self._add_bot(bot)
        bot.backup()
        return bot.get_id()

    def _get_bot(self, bot_id: str) -> Bot:
        """
        To get the Bot

        Parameters:
        -----------
        bot_id: str
            ID of the Bot to get

        Returns:
        --------
        return: Bot
            Bot of thee given ID
        """
        bots = self._get_bots()
        if bot_id not in bots:
            bot = Bot.load(bot_id)
            self._add_bot(bot)
        bot = bots[bot_id]
        return bot

    def _add_bot(self, bot: Bot) -> None:
        bots = self._get_bots()
        bot_id = bot.get_id()
        if bot_id in bots:
            raise ValueError(f"This Bot '{bot_id}' already exist in list of Bot")
        bots[bot_id] = bot

    def start_bot(self, bot_id: str, public_key: str, secret_key: str, is_test_mode: bool) -> None:
        bot = self._get_bot(bot_id)
        broker_class = bot.get_strategy().get_broker_class()
        broker_params = Map({
            Map.public: public_key,
            Map.secret: secret_key,
            Map.test_mode: is_test_mode
        })
        broker = Broker.retrieve(broker_class, broker_params)
        bot.set_broker(broker)
        bot.start()
        bot.backup()

    def stop_bot(self, bot_id: str) -> None:
        self._get_bot(bot_id).stop()

    def stop_bots(self):
        bots = self._get_bots()
        [self.stop_bot(bot_id) for bot_id in bots]

    def set_bot_attribut(self, bot_id: str, attribut: str, value: Any) -> None:
        bot = self._get_hand(bot_id)
        if None:
            pass
        else:
            raise ValueError(f"Unkwon attribut from '{bot.__class__.__name__}' '{attribut}'")

    def get_bot_attribut(self, bot_id: str, attribut: str) -> Any:
        value = None
        bot = self._get_bot(bot_id)
        if attribut == Map.broker:
            value = bot.get_strategy().get_broker_class()
        elif attribut == Map.market:
            value = bot.get_strategy().get_broker_pairs()
        else:
            raise ValueError(f"Unkwon attribut from '{bot.__class__.__name__}' '{attribut}'")
        return value

    @classmethod
    def list_bot_ids(cls) -> List[str]:
        return Bot.list_bot_ids()

    # ——————————————————————————————————————————— FUNCTION BOT UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION HAND DOWN ——————————————————————————————————————————————————

    def resset_hands(self) -> None:
        self.__hands = None

    def _get_hands(self) -> Dict[str, Hand]:
        if self.__hands is None:
            self.__hands = {}
        return self.__hands

    def new_hand(self, capital: float, asset_str: str, broker_class: str) -> str:
        import_exec = _MF.get_import(broker_class)
        exec(import_exec)
        broker_class = eval(broker_class)
        capital = Price(capital, asset_str)
        hand = Hand(capital, broker_class)
        self._add_hand(hand)
        hand.backup()
        return hand.get_id()

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
        if hand_id in hands:
            raise ValueError(f"This Hand '{hand_id}' already exist in list of Hand")
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
        hand.reset_trading()
        hand.set_stalk_on(on=False)
        hand.set_position_on(on=False)
        hand.set_market_analyse_on(on=False)
        hand.backup()

    def stop_hands(self) -> None:
        hands = self._get_hands()
        [self.stop_hand(hand_id) for hand_id in hands]

    def buy_hand_position(self, hand_id: str, pair: str, order_type: str, stop: float = None, limit: float = None, buy_function: str = None) ->  Union[str, None]:
        hand = self._get_hand(hand_id)
        pair_obj = Pair(pair)
        r_asset_str = pair_obj.get_right()
        stop = Price(stop, r_asset_str) if stop is not None else None
        limit = Price(limit, r_asset_str) if limit is not None else None
        buy_function = buy_function if buy_function is not None else None
        return hand.buy(pair_obj, order_type, stop, limit, buy_function)

    def sell_hand_position(self, hand_id: str, pair: str, order_type: str, stop: float = None, limit: float = None, sell_function: str = None) ->  Union[str, None]:
        hand = self._get_hand(hand_id)
        pair_obj = Pair(pair)
        r_asset_str = pair_obj.get_right()
        stop = Price(stop, r_asset_str) if stop is not None else None
        limit = Price(limit, r_asset_str) if limit is not None else None
        sell_function = sell_function if sell_function is not None else None
        return hand.sell(pair_obj, order_type, stop, limit, sell_function)

    def cancel_hand_position(self, hand_id: str, pair: str) ->  Union[str, None]:
        hand = self._get_hand(hand_id)
        pair = Pair(pair)
        return hand.cancel(pair)

    def set_hand_attribut(self, hand_id: str, attribut: str, value: Any) -> None:
        hand = self._get_hand(hand_id)
        if attribut == Map.maximum:
            hand.set_max_position(value)
        else:
            raise ValueError(f"Unkwon attribut from Hand '{attribut}'")

    def get_hand_attribut(self, hand_id: str, attribut: str, **kwargs) -> Any:
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
            value = hand.is_broker_set() and hand.is_position_on() and hand.is_stalk_on()
        elif attribut == Map.maximum:
            value = hand.get_max_position()
        elif attribut == Map.algo:
            positions = hand.get_positions().copy()
            value = [position.get_buy_order().get_pair() for _, position in positions.items() if position.get_sell_order() is not None]
        elif attribut == Map.reason:
            order = hand.get_failed_order(**kwargs)
            value = order.get_content()
        else:
            raise ValueError(f"Unkwon attribut from Hand '{attribut}'")
        return value

    @classmethod
    def list_hand_ids(cls) -> List[str]:
        return Hand.list_hand_ids()

    # ——————————————————————————————————————————— FUNCTION HAND UP ————————————————————————————————————————————————————

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
    def list_main_stablecoins(cls) -> List[str]:
        """
        To get list of main stablecoin allowed

        Returns:
        --------
        return: List[str]
            List of main stablecoin allowed
            NOTE: stablecoins are in upper case and sorted in ascending order
        """
        stablecoins = Config.get(Config.MAIN_STABLECOINS)
        stablecoins = [stablecoin.upper() for stablecoin in stablecoins]
        stablecoins.sort()
        return stablecoins

    @classmethod
    def close_brokers(cls) -> None:
        brokers = cls.list_brokers()
        for broker in brokers:
            exec(f"from model.API.brokers.{broker}.{broker} import {broker}")
            exec(f"{broker}.close()")

    @classmethod
    def get_order_types(cls) -> List[str]:
        return Order.TYPES
