from typing import Callable, List
import pandas as pd

from config.Config import Config
from model.structure.Log import Log
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from view.Console.View import View


class Controller:
    TXT_CANCEL = "cancel"
    CANCEL = "CANCEL"
    MENUS_MAIN = None
    MENUS_HAND = None
    MENUS_VARS = None
    OPTIONS_BOOLEAN = {'No': False, 'Yes': True}

    def __init__(self):
        self.model = Log()
        self.view = View()

    def _set_session(self) -> None:
        view = self._get_view()
        session_dir = Config.get(Config.DIR_SESSIONS)
        session_ids = FileManager.get_dirs(session_dir, make_dir=True)
        if len(session_ids) == 0:
            view.output("There's no session to load!", is_error=True)
            return None
        menu_1 = {'No': False, 'Yes': True}
        options = list(menu_1.keys())
        load_session = menu_1[options[view.menu("Do you want to load a session?", options)]]
        if load_session:
            end_word = self.TXT_CANCEL
            load_options = [end_word, *session_ids]
            message = f"Select a session ID (or '{end_word}' to end the loading process):"
            entry = load_options[view.menu(message, load_options)]
            Config.update(Config.SESSION_ID, entry) if entry != self.TXT_CANCEL else None

    def _set_stage(self) -> None:
        view = self._get_view()
        stage_modes = [Config.STAGE_1, Config.STAGE_2, Config.STAGE_3]
        stage = stage_modes[view.menu("Choose the stage mode:", stage_modes)]
        Config.update(Config.STAGE_MODE, stage)

    def _get_model(self) -> Log:
        """
        To get Controller's access to the model\n
        :return: Controller's access to the model
        """
        return self.model

    def _get_view(self) -> View:
        """
        To get Controller's access to the view\n
        :return: Controller's access to the view
        """
        return self.view

    def get_menus_main(self) -> dict:
        if self.MENUS_MAIN is None:
            self.MENUS_MAIN = {
                Map.message: "Main menu:",
                Map.option: {
                    "Manage Bots": {
                        Map.message: "Bot menu:",
                        Map.option: {
                            "new Bot":      self.new_bot,
                            "start Bot":    self.start_bot,
                            "stop Bot":     self.stop_bot,
                            "stop Bots":    self.stop_bots
                            }
                    },
                    "Manage Hands": {
                        Map.message: "Hand menu:",
                        Map.option: {
                            "New Hand": self.new_hand,
                            "Select Hand": self.manage_hand,
                            "Unload Hands": self.unload_hands
                            }
                        },
                    "Settings": {
                        Map.message: "Application settings:",
                        Map.option: {
                            "Stop Bots": self.stop_bots,
                            "Stop Hands": self.stop_hands,
                            "Close Brokers": self.close_brokers
                        }
                    }
                }
            }
        return self.MENUS_MAIN

    def get_menus_hand(self) -> dict:
        if self.MENUS_HAND is None:
            self.MENUS_HAND = {
                Map.message: "Choose a Hand action:",
                Map.option: {
                    "Start Hand": self.start_hand,
                    "Buy position": self.buy_hand_position,
                    "Sell position": self.sell_hand_position,
                    "Cancel position": self.cancel_hand_position,
                    "Settings": self.hand_setting,
                    "Stop Hand": self.stop_hand
                }
            }
        return self.MENUS_HAND

    def reset_menu_vars(self) -> dict:
        self.MENUS_VARS = None

    def _get_menu_vars(self) -> dict:
        if self.MENUS_VARS is None:
            self.MENUS_VARS = {}
        return self.MENUS_VARS

    def get_menu_var(self, key: str) -> dict:
        menu_vars = self._get_menu_vars()
        if key not in menu_vars:
            raise ValueError(f"This key '{key}' don't exist in menu's variables")
        return menu_vars[key]

    def add_menu_var(self, key: str, value) -> dict:
        menu_vars = self._get_menu_vars()
        if key in menu_vars:
            raise ValueError(f"This key '{key}' already exist in menu's variables")
        menu_vars[key] = value

    def delete_menu_var(self, key: str) -> dict:
        menu_vars = self._get_menu_vars()
        if key in menu_vars:
            del menu_vars[key]

    def start(self) -> None:
        """
        To start the application\n
        """
        Config.label_session_id()
        view = self._get_view()
        self._set_session()
        self._set_stage()
        FileManager.write_csv(Config.get(Config.DIR_BEGIN_BACKUP), ["title"], [{"title": "start file"}], make_dir=True)
        FileManager.write_csv(Config.get(Config.DIR_END_BACKUP), ["title"], [{"title": "end file"}], make_dir=True)
        menus = self.get_menus_main()
        quit_message="Are sure you want to close the application?:"
        self.menu_wrap(quit_message, menus)
        self.quit()

    def menu_wrap(self, quit_message: str, to_wrap_menu: dict) -> None:
        end = False
        while end != True:
            self.menu(to_wrap_menu)
            end = self.ask_confirmation(quit_message)

    def menu(self, menu: dict) -> None:
        def repport_error(callback: Callable, **kwargs) -> None:
            returned = None
            try:
                returned = callback(**kwargs)
            except Exception as e:
                from model.structure.Bot import Bot
                Bot.save_error(e, Controller.__name__)
                view.output(f"Error raised: {e}", is_error=True)
            return returned

        view = self._get_view()
        end = False
        message = menu[Map.message]
        options = {
            Map.cancel: lambda : self.CANCEL,
            **menu[Map.option]
            }
        options_keys = list(options.keys())
        while (end != True) and (end != self.CANCEL):
            key = options_keys[view.menu(message, options_keys)]
            option = options[key]
            if type(option) == dict:
                repport_error(self.menu, **{'menu': option})
            elif callable(option):
                end = repport_error(option)
            else:
                raise Exception(f"Unkwon option '{option}(type={type(option)})'")

    def quit(self) -> None:
        model = self._get_model()
        self.stop_bots()
        model.stop_hands()
        model.close_brokers()

    def ask_confirmation(self, message: str) -> bool:
        view = self._get_view()
        bool_menu = self.OPTIONS_BOOLEAN
        bool_options = list(bool_menu.keys())
        response = bool_menu[bool_options[view.menu(message, bool_options)]]
        return response

    def close_brokers(self) -> None:
        self._get_model().close_brokers()

    # ——————————————————————————————————————————— FUNCTION MENU DOWN ———————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION MENU UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION BOTS DOWN ———————————————————————————————————————————————————

    def new_bot(self):
        _stage = Config.get(Config.STAGE_MODE)
        md = self._get_model()
        vw = self._get_view()
        # params
        if (_stage == Config.STAGE_1) or (_stage == Config.STAGE_2):
            api_pb = Config.get(Config.API_KEY_BINANCE_PUBLIC)
            api_sk = Config.get(Config.API_KEY_BINANCE_SECRET)
            bkr = 'Binance'
            stgs = md.list_strategies()
            stg = stgs[vw.menu("Choose a Strategy:", stgs)]
            pair_codes = md.list_paires(bkr)
            pair_code = pair_codes[vw.menu("Choose the Pair to trade:", pair_codes)]
            if stg == 'Icarus':
                configs = Map({
                    bkr: {
                        Map.public: api_pb,
                        Map.secret: api_sk,
                        Map.test_mode: False
                    },
                    stg: {
                        Map.maximum: None,
                        Map.capital: 1000,
                        Map.rate: 1,
                        Map.period: 60 * 15
                    }
                })
            elif stg == 'IcarusStalker':
                no_selected_stgs = [class_name for class_name in stgs if class_name != stg]
                configs = Map({
                    bkr: {
                        Map.public: api_pb,
                        Map.secret: api_sk,
                        Map.test_mode: False
                    },
                    stg: {
                        Map.maximum: None,
                        Map.capital: 1000,
                        Map.rate: 1,
                        Map.period: 60 * 15,
                        Map.strategy: no_selected_stgs[vw.menu(f"Choose the Strategy to use in '{stg}' Strategy:",
                                                               no_selected_stgs)],
                        Map.param: {
                            Map.maximum: None,
                            Map.capital: -1,
                            Map.rate: 1,
                            Map.period: 60 * 15,
                        }
                    }
                })
            elif stg == 'FlashStalker':
                no_selected_stgs = [class_name for class_name in stgs if class_name != stg]
                configs = Map({
                    bkr: {
                        Map.public: api_pb,
                        Map.secret: api_sk,
                        Map.test_mode: False
                    },
                    stg: {
                        Map.maximum: None,
                        Map.capital: 1000,
                        Map.rate: 1,
                        Map.period: 60,
                        Map.strategy: no_selected_stgs[vw.menu(f"Choose the Strategy to use in '{stg}' Strategy:",
                                                               no_selected_stgs)],
                        Map.param: {
                            Map.maximum: None,
                            Map.capital: -1,
                            Map.rate: 1,
                            Map.period: 60,
                        }
                    }
                })
            else:
                raise Exception(f"Must implement menu for this Strategy '{stg}'.")
        elif _stage == Config.STAGE_3:
            bkrs = md.list_brokers()
            stgs = md.list_strategies()
            bkr = bkrs[vw.menu("Choose a Broker:", bkrs)]
            stg = stgs[vw.menu("Choose a Strategy:", stgs)]
            pair_codes = md.list_paires(bkr)
            pair_code = pair_codes[vw.menu("Choose a Pair to trade:", pair_codes)]
            # configs
            bkr_modes = {"Test mode": True, "Real mode": False}
            bkr_modes_ks = list(bkr_modes.keys())
            configs = Map()
            bkr_params = {
                Map.public: vw.input(message=f"Enter the public key for {bkr}:", secure=True),
                Map.secret: vw.input(message=f"Enter the secret key for {bkr}:", secure=True),
                Map.test_mode: bkr_modes[bkr_modes_ks[vw.menu("Choose the Broker mode:", bkr_modes_ks)]]
            }
            configs.put(bkr_params, bkr)
            if stg == 'IcarusStalker':
                no_selected_stgs = [class_name for class_name in stgs if class_name != stg]
                stg_params = {
                        Map.maximum: None,
                        Map.capital: vw.input(message="Enter initial capital to use:", type_func=float),
                        Map.rate: 1,
                        Map.period: 60 * 15,
                        Map.strategy: no_selected_stgs[vw.menu(f"Choose the Strategy to use in '{stg}' Strategy:",
                                                               no_selected_stgs)],
                        Map.param: {
                            Map.maximum: None,
                            Map.capital: -1,
                            Map.rate: 1,
                            Map.period: 60 * 15,
                        }
                    }
            else:
                raise Exception(f"Must implement menu for this Strategy '{stg}'.")
            configs.put(stg_params, stg)
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        configs.put(pair_code, stg, Map.pair)
        bot = md.create_bot(bkr, stg, pair_code, configs)
        vw.output(f"✅ new Bot created: '{bot}'")

    def start_bot(self) -> None:
        model = self._get_model()
        view = self._get_view()
        bots = model.get_bots()
        bot_ids = bots.get_keys()
        bot_refs = [bots.get(bot_id).__str__() for bot_id in bot_ids]
        if len(bot_ids) <= 0:
            view.output("You have no Bot created", is_error=True)
            return None
        bot_id = bot_ids[view.menu("Choose the Bot to start:", bot_refs)]
        model.start_bot(bot_id)
        view.output(f"✅ Bot started: {bot_id}!")

    def stop_bot(self) -> None:
        model = self._get_model()
        view = self._get_view()
        bots = model.get_bots()
        bot_ids = bots.get_keys()
        bot_menu = [bot.__str__() for bot in list(bots.get_map().values())]
        bot_menu.insert(0, self.TXT_CANCEL)
        choice_index = view.menu("Select the Bot to stop:", bot_menu)
        if choice_index > 0:
            bot_id = bot_ids[choice_index-1]
            model.stop_bot(bot_id)
            view.output(f"❌ Bot stopped: {bot_id}!")

    def stop_bots(self):
        pass

    # ——————————————————————————————————————————— FUNCTION BOTS UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION HAND DOWN ———————————————————————————————————————————————————

    def new_hand(self) -> None:
        view = self._get_view()
        model = self._get_model()
        brokers = model.list_brokers()
        stablecoins = Config.get(Config.MAIN_STABLECOINS)
        stablecoins = [stablecoin.upper() for stablecoin in stablecoins]
        stablecoins.sort()
        params = {
            Map.capital: view.input("Enter capital for the new Hand:", type_func=float),
            Map.asset: stablecoins[view.menu("Choose an Asset in witch to express Hand's capital:", stablecoins)],
            'broker_class': brokers[view.menu("Choose a Broker for the new Hand:", brokers)]
        }
        can_submit = self.ask_confirmation(f"Are you sur you want create a new Hand:\n{pd.DataFrame([params])}\n")
        if can_submit:
            hand_id = model.new_hand(**params)
            view.output(f"New Hand created: '{hand_id}'", is_success=True)
    
    def manage_hand(self) -> None:
        def select_hand_id() -> str:
            hand_id = hand_ids[view.menu("Select a Hand to trade with:", hand_ids)]
            self.add_menu_var(Map.id, hand_id)
            return hand_id

        view = self._get_view()
        model = self._get_model()
        hand_ids = model.list_hand_ids()
        if len(hand_ids) == 0:
            view.output("There is no Hand available!", is_error=True)
            return None
        # Select Hand
        hand_id = select_hand_id()
        # Manage Hand
        hand_menus = self.get_menus_hand()
        quit_message = f"Are you sur you whant to quit Hand '{hand_id}'?"
        self.menu_wrap(quit_message, hand_menus)
        self.reset_menu_vars()

    def unload_hands(self) -> None:
        self._get_model().resset_hands()
        self._get_view().output("Hand unloaded!", is_success=True)

    def start_hand(self) -> None:
        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        if Config.get(Config.STAGE_MODE) == Config.STAGE_3:
            broker_name = model.get_hand_attribut(hand_id, Map.broker)
            params = {
                'public_key': view.input(f"Enter the public key to access {broker_name}'s API:"),
                'secret_key': view.input(f"Enter the secret key to access {broker_name}'s API:", secure=True),
                'is_test_mode': self.ask_confirmation(f"Access {broker_name}'s API in test mode?")
                }
        else:
            params = {
                'public_key': '-',
                'secret_key': '-',
                'is_test_mode': False
                }
        model.start_hand(hand_id, **params)
        view.output("Hand started!", is_success=True)

    def buy_hand_position(self) -> None:
        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        max_position = model.get_hand_attribut(hand_id, Map.maximum)
        n_position = len(model.get_hand_attribut(hand_id, Map.position))
        if n_position >= max_position:
            view.output(f"The max number of position '{max_position}' is reached!", is_error=True)
            return None
        if model.get_hand_attribut(hand_id, Map.start) == False:
            view.output("Must start Hand before!", is_error=True)
            return None
        params = self.input_hand_order(hand_id, Map.buy)
        if isinstance(params, dict):
            model.buy_hand_position(hand_id, **params)
            view.output(f"Buy Order placed for '{params[Map.pair].upper()}'!", is_success=True)

    def sell_hand_position(self) -> None:
        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        if model.get_hand_attribut(hand_id, Map.start) == False:
            view.output("Must start Hand before!", is_error=True)
            return None
        params = self.input_hand_order(hand_id, Map.sell)
        if isinstance(params, dict):
            model.sell_hand_position(hand_id, **params)
            view.output(f"Sell Order placed for '{params[Map.pair].upper()}'!", is_success=True)

    def input_hand_order(self, hand_id: str, move: str) -> dict:
        def get_positions() -> List[Pair]:
            return model.get_hand_attribut(hand_id, Map.position)
    
        def get_selable_positions() -> List[Pair]:
            return model.get_hand_attribut(hand_id, Map.sell)

        def get_available_pairs() -> List[Pair]:
            return model.get_hand_attribut(hand_id, Map.pair)

        def get_sell_algo_order() -> List[Pair]:
            return model.get_hand_attribut(hand_id, Map.algo)

        def get_initial_capital() -> Price:
            return model.get_hand_attribut(hand_id, Map.capital)

        def input_pair(move: str, params: dict) -> None:
            if move == Map.buy:
                positions = [position.__str__().upper() for position in get_positions()]
                capital = get_initial_capital()
                r_asset = capital.get_asset()
                pair_format = f"BTC/{r_asset.__str__().upper()}"
                available_pairs = [available_pair.__str__().upper() for available_pair in get_available_pairs()]
                while True:
                    pair_str = view.input(f"Enter the Pair to {move.capitalize()} (i.e.: '{pair_format}'):", type_func=str)
                    pair_str = pair_str.upper()
                    if pair_str in positions:
                        view.output(f"A position in this Pair '{pair_str}' already exist!", is_error=True)
                        continue
                    if pair_str not in available_pairs:
                        view.output(f"This pair '{pair_str}' is not available to {move.capitalize()}!", is_error=True)
                        continue
                    break
                params[Map.pair] = pair_str
            else:
                hold_positions = [hold_position.__str__().upper() for hold_position in get_selable_positions()]
                if len(hold_positions) == 0:
                    view.output(f"There is no position to sell!", is_error=True)
                    return None
                sell_pair_str = hold_positions[view.menu(f"Choose the position to {move.capitalize()}:", hold_positions)]
                sell_algo_orders = [sell_algo_order.__str__().upper() for sell_algo_order in get_sell_algo_order()]
                if sell_pair_str.upper() in sell_algo_orders:
                    view.output(f"There's already a sell order placed on this position '{sell_pair_str}'!", is_error=True)
                    return None
                params[Map.pair] = sell_pair_str

        def input_prices(params: dict) -> None:
            if params['order_type'] in [Order.TYPE_STOP, Order.TYPE_STOP_LIMIT]:
                params[Map.stop] =  view.input(f"Enter the Stop Price for the {move.capitalize()} Order:", type_func=float)
            if params['order_type'] in [Order.TYPE_LIMIT, Order.TYPE_STOP_LIMIT]:
                params[Map.limit] =  view.input(f"Enter the Limit Price for the {move.capitalize()} Order:", type_func=float)

        if move not in [Map.buy, Map.sell]:
            raise ValueError(f"The move must be {' or '.join([Map.buy, Map.sell])}, instead '{move}(type={type(move)})'")
        model = self._get_model()
        view = self._get_view()
        order_types = model.get_order_types()
        params = {}
        input_pair(move, params)
        if Map.pair in params:
            params['order_type'] = order_types[view.menu(f"Choose the type of the Order to {move.capitalize()} with:", order_types)]
            input_prices(params)
            can_submit = self.ask_confirmation(f"Are you sur you want to submit this Order:\n{pd.DataFrame([params])}\n")
        else:
            can_submit = False
        return params if can_submit else None

    def cancel_hand_position(self) -> None:
        def get_cancellable_positions() -> List[Pair]:
            return model.get_hand_attribut(hand_id, Map.cancel)

        view = self._get_view()
        model = self._get_model()
        hand_id = self.get_menu_var(Map.id)
        if model.get_hand_attribut(hand_id, Map.start) == False:
            view.output("Must start Hand before!", is_error=True)
            return None
        positions = [position.__str__().upper() for position in get_cancellable_positions()]
        if len(positions) == 0:
            view.output("There is no position to cancel!", is_error=True)
            return None
        pair_str = positions[view.menu("Choose the position to cancel:", positions)]
        can_submit = self.ask_confirmation(f"Are you sur you want to cancel this position '{pair_str.upper()}':")
        if can_submit:
            model.cancel_hand_position(hand_id, pair_str)
            view.output(f"Canceled position '{pair_str.upper()}'!", is_success=True)

    def stop_hand(self) -> None:
        model = self._get_model()
        hand_id = self.get_menu_var(Map.id)
        model.stop_hand(hand_id)
        self._get_view().output("Hand stopped!", is_success=True)

    def hand_setting(self) -> None:
        def show_setting() -> None:
            settings = [
                {Map.param: 'Max position', Map.value: model.get_hand_attribut(hand_id, Map.maximum)}
            ]
            df = pd.DataFrame(settings)
            view.output(f"\n{df}\n")

        def update_max_position() -> None:
            max_position = model.get_hand_attribut(hand_id, Map.maximum)
            new_max_position = view.input("Enter the new number of position allowed:", type_func=int)
            model.set_hand_attribut(hand_id, Map.maximum, new_max_position)
            view.output(f"Updated number of position allowed from '{max_position}' to '{new_max_position}'!", is_success=True)

        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        setting_menu = {
            Map.message: 'Hand settings',
            Map.option:{
                "Show settings": show_setting,
                "Update max position allowed": update_max_position
            }
        }
        self.menu(setting_menu)

    def stop_hands(self) -> None:
        self._get_model().stop_hands()

    # ——————————————————————————————————————————— FUNCTION HAND UP —————————————————————————————————————————————————————

