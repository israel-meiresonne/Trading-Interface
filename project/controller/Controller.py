from typing import Callable, List

import pandas as pd

from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.Log import Log
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from view.Console.View import View


class Controller:
    CANCEL =                    "CANCEL"
    MENUS =                     None
    MENU_MAIN =                 "MENU_MAIN"
    MENU_HAND =                 "MENU_HAND"
    MENUS_SUPPORTED =           [MENU_MAIN, MENU_HAND]
    MENUS_VARS =                None
    MENUS_VAR_HEADER =          Map.header
    MENUS_HEADER_SEPARATOR =    ' > '
    MENUS_KEEP_VARS =           [MENUS_VAR_HEADER]
    OPTIONS_BOOLEAN =           {'No': False, 'Yes': True}

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
            end_word = self.CANCEL
            load_options = [end_word, *session_ids]
            message = f"Select a session ID (or '{end_word}' to end the loading process):"
            entry = load_options[view.menu(message, load_options)]
            Config.update(Config.SESSION_ID, entry) if entry != self.CANCEL else None

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

    def get_menu(self, menu_name: str) -> dict:
        if menu_name not in self.MENUS_SUPPORTED:
            raise ValueError(f"This menue '{menu_name}' is not supported")
        if self.MENUS is None:
            self.MENUS = {}
        menus = self.MENUS
        if (menu_name == self.MENU_MAIN) and (menu_name not in menus):
            menu = {
                Map.menu: "Main menu:",
                Map.option: {
                    "Manage Bots": {
                        Map.menu: "Bot menu:",
                        Map.option: {
                            "new Bot":      self.new_bot,
                            "start Bot":    self.start_bot,
                            "stop Bot":     self.stop_bot,
                            "stop Bots":    self.stop_bots,
                            "Unload Bots":  self.unload_bots
                            }
                    },
                    "Manage Hands": {
                        Map.menu: "Hand menu:",
                        Map.option: {
                            "New Hand":     self.new_hand,
                            "Select Hand":  self.manage_hand,
                            "Unload Hands": self.unload_hands
                            }
                        },
                    "Settings": {
                        Map.menu: "Application settings:",
                        Map.option: {
                            "Stop Bots":        self.stop_bots,
                            "Stop Hands":       self.stop_hands,
                            "Close Brokers":    self.close_brokers
                        }
                    }
                }
            }
            menus[menu_name] = menu
        elif (menu_name == self.MENU_HAND) and (menu_name not in menus):
            menu = {
                Map.menu: "put_hand_id",
                Map.option: {
                    "Start Hand":       self.start_hand,
                    "Buy position":     self.buy_hand_position,
                    "Sell position":    self.sell_hand_position,
                    "Cancel position":  self.cancel_hand_position,
                    "Settings":         self.hand_setting,
                    "Stop Hand":        self.stop_hand
                }
            }
            menus[menu_name] = menu
        return menus[menu_name].copy()

    def reset_menu_vars(self) -> dict:
        menu_vars = self._get_menu_vars()
        menu_var_keys = list(menu_vars.keys())
        for menu_var_key in menu_var_keys:
            if menu_var_key not in self.MENUS_KEEP_VARS:
                menu_vars[menu_var_key] = None
                del menu_vars[menu_var_key]

    def _get_menu_vars(self) -> dict:
        if self.MENUS_VARS is None:
            self.MENUS_VARS = {}
        return self.MENUS_VARS

    def exist_menu_var(self, key: str) -> bool:
        """
        To check if the key exist in menu's vars

        Parameters:
        -----------
        key: str
            The key to check

        Returns:
        --------
        return: bool
            True if the key exist else False
        """
        return key in self._get_menu_vars()

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
        self._set_session()
        self._set_stage()
        FileManager.write_csv(Config.get(Config.DIR_BEGIN_BACKUP), ["title"], [{"title": "start file"}], make_dir=True)
        FileManager.write_csv(Config.get(Config.DIR_END_BACKUP), ["title"], [{"title": "end file"}], make_dir=True)
        config_cmd = 'commit=$(git log --oneline | head -n 1) ; commit_id=$(git log | head -n 1 | cut -d " " -f 2) ; commit_m=$(git log --oneline | head -n 1 | cut -d " " -f 2-) ; branch=$(git branch | grep "*" | awk -F " " "{print \$NF}" | sed "s#)##") ; now_date=$(date -u "+%Y-%m-%d %H:%M:%S") ; pyv=$(python3 -V) ; echo "Date:\t\t$now_date\nUSER:\t\t$USER\nPWD:\t\t$PWD\nVersion:\t$pyv\nBranch:\t\t$branch\nID:\t\t\t$commit_id\nMessage:\t$commit_m\n#"'
        FileManager.write(Config.get(Config.FILE_SESSION_CONFIG), _MF.shell(config_cmd), overwrite=False ,make_dir=True, line_return=False)
        menus = self.get_menu(self.MENU_MAIN)
        quit_message="Are sure you want to close the application?:"
        self.menu_wrap(quit_message, menus)
        self.quit()

    # ——————————————————————————————————————————— FUNCTION MENU DOWN ——————————————————————————————————————————————————

    def menu_wrap(self, quit_message: str, to_wrap_menu: dict) -> None:
        end = False
        while end != True:
            self.menu(to_wrap_menu)
            end = self.ask_confirmation(quit_message)

    def menu(self, menu: dict) -> None:
        def repport_error(view: View, callback: Callable, **kwargs) -> None:
            returned = None
            try:
                returned = callback(**kwargs)
            except Exception as e:
                from model.structure.Bot import Bot
                Bot.save_error(e, Controller.__name__)
                view.output(f"⛔️ Fatal Error raised: {e}", richs=[view.S_BOLD, view.C_RED])
            return returned
        def push_header(separator: str, menu_name: str) -> str:
            if not self.exist_menu_var(menu_header_key):
                self.add_menu_var(menu_header_key, menu_name)
            else:
                menu_header = self.get_menu_var(menu_header_key)
                new_menu_header = f'{menu_header}{separator}{menu_name}'
                self.delete_menu_var(menu_header_key)
                self.add_menu_var(menu_header_key, new_menu_header)
            return self.get_menu_var(menu_header_key)
        def remove_menu(separator: str) -> None:
            menu_header = self.get_menu_var(menu_header_key)
            new_menu_header = f'{separator}'.join(menu_header.split(separator)[:-1])
            self.delete_menu_var(menu_header_key)
            self.add_menu_var(menu_header_key, new_menu_header) if len(new_menu_header) > 0 else None
        def ouput_menu_path(view: View, separator: str, menu_header: str) -> None:
            menu_header_split = menu_header.split(separator)
            menu_header_split[-1] = view.B_LIGHT_GREEN + menu_header_split[-1]
            new_menu_header = separator.join(menu_header_split)
            view.output(new_menu_header, richs=[view.B_LIGHT_GRAY, view.C_BLACK])
        view = self._get_view()
        menu_header_key = self.MENUS_VAR_HEADER
        end = False
        separator = self.MENUS_HEADER_SEPARATOR
        menu_name = menu[Map.menu]
        menu_path = push_header(separator, menu_name)
        options = {
            Map.cancel: lambda : self.CANCEL,
            **menu[Map.option]
            }
        options_keys = list(options.keys())
        while (end != True) and (end != self.CANCEL):
            ouput_menu_path(view, separator, menu_path)
            key = options_keys[view.menu(menu_name, options_keys)]
            option = options[key]
            if type(option) == dict:
                repport_error(view, self.menu, **{'menu': option})
            elif callable(option):
                end = repport_error(view, option)
            else:
                raise Exception(f"Unkwon option '{option}(type={type(option)})'")
        remove_menu(separator)

    def quit(self) -> None:
        model = self._get_model()
        model.stop_bots()
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

    # ——————————————————————————————————————————— FUNCTION MENU UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION BOTS DOWN ——————————————————————————————————————————————————

    def new_bot(self) -> None:
        def pair_menu() -> str:
            pair_message = f"How many Pair do you want to trade with the new Bot:"
            pair_options = [
                'Trade with one Pair only',
                'Trade with all available Pair'
            ]
            pair_option = pair_options[view.menu(pair_message, pair_options)]
            pair_str = input_pair() if pair_option == pair_options[0] else None
            return pair_str
        def input_pair() -> str:
            while True:
                pair = view.input(f"Enter the Pair to use in new Bot (format: 'Asset/{asset_str.upper()}'):", type_func=Pair)
                if pair.get_right().__str__() == asset_str.lower():
                    break
                else:
                    view.output(f"The Pair must be in format 'Asset/{asset_str.upper()}' (with '{asset_str.upper()}' as right Asset)!", is_error=True)
            return pair.__str__()
        model = self._get_model()
        view = self._get_view()
        # Prepare vars
        brokers = model.list_brokers()
        strategies = model.list_strategies()
        stablecoins = model.list_main_stablecoins()
        params = {}
        # Input
        params['capital_num'] = view.input("Enter capital for the new Bot:", type_func=float)
        params['asset_str'] = asset_str = stablecoins[view.menu("Choose an Asset in witch to express Bot's capital:", stablecoins)]
        params['strategy_str'] = strategy_str = strategies[view.menu("Choose the Strategy to use with the new Bot:", strategies)]
        params['broker_str'] = brokers[view.menu("Choose a Broker for the new Bot:", brokers)]
        params['pair_str'] = pair_menu()
        # End
        can_submit = self.ask_confirmation(f"Are you sur you want create a new Bot:\n{pd.DataFrame([params])}\n")
        if can_submit:
            bot_id = model.new_bot(**params)
            view.output(f"New Bot created: '{bot_id}'", is_success=True)

    def start_bot(self) -> None:
        model = self._get_model()
        view = self._get_view()
        bot_ids = model.list_bot_ids()
        if len(bot_ids) == 0:
            view.output("There is not Bot to start!", is_error=True)
            return None
        options = [self.CANCEL, *bot_ids]
        option = bot_id = options[view.menu(f"Select the Bot to start:", options)]
        if option != options[0]:
            broker_name = model.get_bot_attribut(bot_id, Map.broker)
            params = self.input_broker(broker_name)
            model.start_bot(bot_id, **params)
            view.output(f"Bot started: '{bot_id}'", is_success=True)

    def stop_bot(self) -> None:
        model = self._get_model()
        view = self._get_view()
        bot_ids = model.list_bot_ids()
        options = [self.CANCEL, *bot_ids]
        option = bot_id = options[view.menu(f"Select the Bot to stop:", options)]
        if option != options[0]:
            model.stop_bot(bot_id)
            view.output(f"Bot stopped: '{bot_id}'", is_success=True)

    def stop_bots(self) -> None:
        can_stop = self.ask_confirmation("Are you sur you want to stop all Bots?")
        if can_stop:
            self._get_model().stop_bots()
            self._get_view().output(f"Stopped all Bot", is_success=True)

    def unload_bots(self) -> None:
        can_unload = self.ask_confirmation("Are you sur you want to unload all Bots?")
        if can_unload:
            self._get_model().resset_bots()
            self._get_view().output("Bot unloaded!", is_success=True)

    # ——————————————————————————————————————————— FUNCTION BOTS UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION HAND DOWN ——————————————————————————————————————————————————

    def new_hand(self) -> None:
        view = self._get_view()
        model = self._get_model()
        brokers = model.list_brokers()
        stablecoins = model.list_main_stablecoins()
        params = {
            Map.capital: view.input("Enter capital for the new Hand:", type_func=float),
            'asset_str': stablecoins[view.menu("Choose an Asset in witch to express Hand's capital:", stablecoins)],
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
        hand_menus = self.get_menu(self.MENU_HAND)
        hand_menus[Map.menu] = f"Hand '{hand_id}'"
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
        is_hand_started = model.get_hand_attribut(hand_id, Map.start)
        if not is_hand_started:
            broker_name = model.get_hand_attribut(hand_id, Map.broker)
            params = self.input_broker(broker_name)
            model.start_hand(hand_id, **params)
            view.output("Hand started!", is_success=True)
        else:
            view.output("Hand is started already!")

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
            failed_order_id = model.buy_hand_position(hand_id, **params)
            if failed_order_id is None:
                view.output(f"Buy Order placed for '{params[Map.pair].upper()}'!", is_success=True)
            else:
                fail_reason = model.get_hand_attribut(hand_id, Map.reason, order_id=failed_order_id)
                view.output(f"Failed to buy Position '{params[Map.pair].upper()}' with Order of id '{failed_order_id}' cause: '{fail_reason}'!", is_error=True)

    def sell_hand_position(self) -> None:
        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        if model.get_hand_attribut(hand_id, Map.start) == False:
            view.output("Must start Hand before!", is_error=True)
            return None
        params = self.input_hand_order(hand_id, Map.sell)
        if isinstance(params, dict):
            failed_order_id = model.sell_hand_position(hand_id, **params)
            if failed_order_id is None:
                view.output(f"Sell Order placed for '{params[Map.pair].upper()}'!", is_success=True)
            else:
                fail_reason = model.get_hand_attribut(hand_id, Map.reason, order_id=failed_order_id)
                view.output(f"Failed to sell Position '{params[Map.pair].upper()}' with Order of id '{failed_order_id}' cause: '{fail_reason}'!", is_error=True)

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
            failed_order_id = model.cancel_hand_position(hand_id, pair_str)
            if failed_order_id is None:
                view.output(f"Canceled position '{pair_str.upper()}'!", is_success=True)
            else:
                fail_reason = model.get_hand_attribut(hand_id, Map.reason, order_id=failed_order_id)
                view.output(f"Failed to cancel Position '{pair_str.upper()}' with Order of id '{failed_order_id}' cause: '{fail_reason}'!", is_error=True)

    def stop_hand(self) -> None:
        model = self._get_model()
        hand_id = self.get_menu_var(Map.id)
        model.stop_hand(hand_id)
        self._get_view().output("Hand stopped!", is_success=True)

    def hand_setting(self) -> None:
        def show_setting() -> None:
            settings = [
                {Map.param: 'Max position',     Map.value: model.get_hand_attribut(hand_id, Map.maximum)},
                {Map.param: 'Stalk Thread',     Map.value: model.get_hand_attribut(hand_id, threads[Map.stalk])},
                {Map.param: 'Position Thread',  Map.value: model.get_hand_attribut(hand_id, threads[Map.position])},
                {Map.param: 'Analyse Thread',   Map.value: model.get_hand_attribut(hand_id, threads[Map.analyse])},
            ]
            df = pd.DataFrame(settings)
            view.output(f"\n{df}\n")
        def update_max_position() -> None:
            max_position = model.get_hand_attribut(hand_id, Map.maximum)
            new_max_position = view.input("Enter the new number of position allowed:", type_func=int)
            model.set_hand_attribut(hand_id, Map.maximum, new_max_position)
            view.output(f"Updated number of position allowed from '{max_position}' to '{new_max_position}'!", is_success=True)
        def update_thread() -> None:
            thread_options = list(threads.keys())
            option = thread_options[view.menu('Select the thread to switch:', thread_options)]
            thread_attribut = threads[option]
            is_on = self.ask_confirmation('Select Yes->{switch on} OR No->{switch off}')
            can_submit = self.ask_confirmation(f"Are you sur you want to switch '{'ON' if is_on else 'OFF'}' the '{option.capitalize()}' thread")
            model.set_hand_attribut(hand_id, thread_attribut, is_on) if can_submit else None
        model = self._get_model()
        view = self._get_view()
        hand_id = self.get_menu_var(Map.id)
        threads = {
            Map.stalk:      f"{Map.thread}_{Map.stalk}",
            Map.position:   f"{Map.thread}_{Map.position}",
            Map.analyse:    f"{Map.thread}_{Map.analyse}"
        }
        setting_menu = {
            Map.menu: 'Hand settings',
            Map.option:{
                "Show settings": show_setting,
                "Update max position allowed": update_max_position,
                "Switch on/off thread": update_thread,
            }
        }
        self.menu(setting_menu)

    def stop_hands(self) -> None:
        can_stop = self.ask_confirmation("Are you sur you want to stop all Hands?")
        if can_stop:
            self._get_model().stop_hands()
            view = self._get_view()
            view.output(f"Stopped all Hands", is_success=True)

    # ——————————————————————————————————————————— FUNCTION HAND UP ————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION COMMON DOWN ————————————————————————————————————————————————

    def input_broker(self, broker_name: str) -> dict:
        view = self._get_view()
        if Config.get(Config.STAGE_MODE) == Config.STAGE_3:
            params = {
                'public_key':   view.input(f"Enter the public key to access {broker_name}'s API:"),
                'secret_key':   view.input(f"Enter the secret key to access {broker_name}'s API:", secure=True),
                'is_test_mode': False   #self.ask_confirmation(f"Access {broker_name}'s API in test mode?")
                }
        else:
            params = {
                'public_key':   '-',
                'secret_key':   '-',
                'is_test_mode': False
                }
        return params

    # ——————————————————————————————————————————— FUNCTION COMMON UP ——————————————————————————————————————————————————

