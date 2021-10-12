from config.Config import Config
from model.structure.Log import Log
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from view.ViewInterface import ViewInterface
from view.structure.View import View


class Controller:
    def __init__(self):
        self.model = Log()
        self.view = View()

    def _get_model(self):
        """
        To get Controller's access to the model\n
        :return: Controller's access to the model
        """
        return self.model

    def _get_view(self):
        """
        To get Controller's access to the view\n
        :return: Controller's access to the view
        """
        return self.view

    def start(self):
        """
        To start the application\n
        """
        view = self._get_view()
        home_key = View.MENUS_KEY_HOME
        menu = View.get_menus()
        options = menu[home_key][View.MENUS_KEY_OPTION]
        self._set_session()
        self._set_stage()
        FileManager.write_csv(Config.get(Config.DIR_BEGIN_BACKUP), ["title"], [{"title": "start file"}], make_dir=True)
        FileManager.write_csv(Config.get(Config.DIR_END_BACKUP), ["title"], [{"title": "end file"}], make_dir=True)
        end = False
        while not end:
            i = view.menu("Choose an execution", options)
            fc = menu[home_key][View.MENUS_KEY_FUNC][i]
            end = eval("self." + fc + "()")

    @staticmethod
    def quit() -> bool:
        return True

    def _set_session(self) -> None:
        view = self._get_view()
        session_dir = Config.get(Config.DIR_SESSIONS)
        session_ids = FileManager.get_dirs(session_dir, make_dir=True)
        if len(session_ids) == 0:
            view.output(View.FILE_ERROR, "There's no session to load!")
            return None
        menu_1 = {'No': False, 'Yes': True}
        options = list(menu_1.keys())
        load_session = menu_1[options[view.menu("Do you want to load a session?", options)]]
        if not isinstance(load_session, bool):
            raise Exception(f"Wrong type: load_session='{load_session}({type(load_session)})'")
        if load_session:
            end_word = View.WORD_END
            load_options = [end_word, *session_ids]
            end = False
            message = f"Select a session ID (or '{end_word}' to end the loading process):"
            while not end:
                entry = load_options[view.menu(message, load_options)]
                # entry = view.input(f"Enter a session ID or '{end_word}' to end the loading process:")
                session_id = entry if entry in session_ids else None
                end = (session_id is not None) or (entry == end_word)
            Config.update(Config.SESSION_ID, session_id) if session_id is not None else None

    def _set_stage(self) -> None:
        view = self._get_view()
        stage_modes = [Config.STAGE_1, Config.STAGE_2, Config.STAGE_3]
        stage = stage_modes[view.menu("Choose the stage mode:", stage_modes)]
        Config.update(Config.STAGE_MODE, stage)

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
            if stg == 'MinMax':
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
                        Map.period: 60 * 5
                    }
                })
            elif stg == 'MinMaxFloor':
                configs = Map({
                    bkr: {
                        Map.public: api_pb,
                        Map.secret: api_sk,
                        Map.test_mode: False
                    },
                    stg: {
                        Map.maximum: None,
                        Map.capital: 20,
                        Map.rate: 1,
                        Map.period: 60 * 60,
                        Map.green: {
                            Map.period: 60 * 15
                        },
                        Map.red: {
                            Map.period: 60 * 5
                        }
                    }
                })
            elif stg == 'Stalker':
                no_selected_stgs = [class_name for class_name in stgs if class_name != stg]
                configs = Map({
                    bkr: {
                        Map.public: api_pb,
                        Map.secret: api_sk,
                        Map.test_mode: False
                    },
                    stg: {
                        Map.maximum: None,
                        Map.capital: 1000,  # 6100,
                        Map.rate: 1,
                        # Map.period: 60 * 60,
                        Map.strategy: no_selected_stgs[vw.menu(f"Choose the Strategy to use in '{stg}' Strategy:", no_selected_stgs)],
                        Map.param: {
                            Map.maximum: None,
                            Map.capital: 1000,
                            Map.rate: 1,
                            Map.period: 60 * 5,
                        }
                    }
                })
            elif stg == 'Icarus':
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
                        Map.period: 60 * 5
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
                        Map.period: 60 * 30,
                        Map.strategy: no_selected_stgs[vw.menu(f"Choose the Strategy to use in '{stg}' Strategy:",
                                                               no_selected_stgs)],
                        Map.param: {
                            Map.maximum: None,
                            Map.capital: -1,
                            Map.rate: 1,
                            Map.period: 60 * 5,
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
            if stg == 'MinMax':
                raise Exception(f"Strategy '{stg}' no available in for this stage '{_stage}'.")
            elif stg == 'MinMaxFloor':
                raise Exception(f"Strategy '{stg}' no available in for this stage '{_stage}'.")
            elif stg == 'Stalker':
                no_selected_stgs = [class_name for class_name in stgs if class_name != stg]
                stg_params = {
                    Map.maximum: None,
                    Map.capital: vw.input(message="Enter initial capital to use:", type_func="float"),
                    Map.rate: 1,
                    Map.strategy: no_selected_stgs[vw.menu(f"Choose the child Strategy for your main Strategy '{stg}':",
                                                           no_selected_stgs)],
                    Map.param: {
                        Map.maximum: None,
                        Map.capital: None,
                        Map.rate: 1,
                        Map.period: 60 * 5,
                    }
                }
            else:
                raise Exception(f"Must implement menu for this Strategy '{stg}'.")
            configs.put(stg_params, stg)
        else:
            raise Exception(f"Unknown stage '{_stage}'.")
        print(configs.get_map())
        # create Bot
        configs.put(pair_code, stg, Map.pair)
        bot = md.create_bot(bkr, stg, pair_code, configs)
        vw.output(View.FILE_MESSAGE, f"✅ new Bot created (Bot's id: '{bot.get_id()}')")
        """
        if (_stage == Config.STAGE_2) or (_stage == Config.STAGE_3):
            # Select period
            bots = md.get_bots()
            bt_ids = list(bots.keys())
            bot = bots[bt_ids[0]]
            period_ranking = bot.get_period_ranking()
            options = []
            best_periods = []
            for rank, struc in period_ranking.get(Map.period).items():
                period = struc[Map.period]
                best_periods.append(period)
                roi = round(struc[Map.roi]*100, 2)
                roi_per_day = round(struc[Map.day]*100, 2)
                option = f"rank:{rank} | minutes:{period / 60} | " \
                         f"roi:{roi}% | day:{roi_per_day}%"
                options.append(option)
            best_period = best_periods[vw.menu(f"Select a trading interval for your pair '{pair_code.upper()}':", options)]
            bot.set_best_period(best_period)
            vw.output(View.FILE_MESSAGE, "✅ Trading interval set!")
        """

    def start_bot(self):
        md = self._get_model()
        vw = self._get_view()
        bots = md.get_bots()
        bt_ids = bots.get_keys()
        bot_refs = [bots.get(bot_id).__str__() for bot_id in bt_ids]
        if len(bt_ids) <= 0:
            vw.output(View.FILE_ERROR, "You have no Bot created")
            return None
        bt_id = bt_ids[vw.menu("Choose the Bot to start:", bot_refs)]
        md.start_bot(bt_id)
        vw.output(View.FILE_MESSAGE, f"❌ Bot stopped: {bt_id}!")

    def stop_bot(self):
        pass

    def stop_bots(self):
        pass
