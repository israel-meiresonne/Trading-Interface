from config.Config import Config
from model.structure.Log import Log
from model.tools.Map import Map
from view.structure.View import View


class Controller:
    def __init__(self):
        self.model = Log()
        self.view = View()

    def __get_model(self):
        """
        To get Controller's access to the model\n
        :return: Controller's access to the model
        """
        return self.model

    def __get_view(self):
        """
        To get Controller's access to the view\n
        :return: Controller's access to the view
        """
        return self.view

    def start(self):
        """
        To start the application\n
        """
        vw = self.__get_view()
        m_home = "home"
        end = False
        ms = View.get_menus()
        cs = ms[m_home][View.MENUS_KEY_TXT]
        stage_modes = [Config.STAGE_1, Config.STAGE_2, Config.STAGE_3]
        stage = stage_modes[vw.menu("Choose the stage mode:", stage_modes)]
        Config.update(Config.STAGE_MODE, stage)
        while not end:
            i = vw.menu("Choose an execution", cs)
            fc = ms[m_home][View.MENUS_KEY_FUNC][i]
            end = eval("self." + fc + "()")

    def quit(self):
        return True

    def new_bot(self):
        md = self.__get_model()
        vw = self.__get_view()
        """
        # params
        bkrs = md.list_brokers()
        stgs = md.list_strategies()
        bkr = bkrs[vw.menu("Choose a Broker:", bkrs)]
        stg = stgs[vw.menu("Choose a Strategy:", stgs)]
        prcds = md.list_paires(bkr)
        prcd = prcds[vw.menu("Choose a Pair to trade:", prcds)]
        # configs
        mds = {"Test mode": True, "Real mode": False}
        mds_ks = list(mds.keys())
        configs = Map({
            bkr: {
                Map.api_pb: vw.input(msg=f"Enter the public key for {bkr}", secure=True),
                Map.api_sk: vw.input(msg=f"Enter the secret key for {bkr}", secure=True),
                Map.test_mode: mds[mds_ks[vw.menu("Choose your mode:", mds_ks)]]
            },
            stg: {
                Map.capital: 1000,
                Map.rate: None
            }
        })
        print(configs.get_map())
        """
        bkr = 'Binance'
        stg = 'MinMax'
        pair_codes = md.list_paires(bkr)
        pair_code = pair_codes[vw.menu("Choose a Pair to trade:", pair_codes)]
        # prcd = 'BTC/USDT'
        configs = Map({
            bkr: {
                Map.api_pb: 'mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5',
                Map.api_sk: 'xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr',
                Map.test_mode: False
            },
            stg: {
                Map.maximum: None,
                Map.capital: 20,
                Map.rate: 1
            }
        })
        print(configs.get_map())
        # """
        # create Bot
        md.create_bot(bkr, stg, pair_code, configs)
        vw.output(View.FILE_MESSAGE, "✅ new Bot created!")

    def start_bot(self):
        md = self.__get_model()
        vw = self.__get_view()
        bt_ids = list(md.get_bots().keys())
        """
        if len(bt_ids) <= 0:
            vw.output(View.FILE_ERROR, "You have no Bot created")
            return None
        bt_id = bt_ids[vw.menu("Choose the Bot to start:", bt_ids)]
        """
        bt_id = bt_ids[0]
        md.start_bot(bt_id)
        vw.output(View.FILE_MESSAGE, f"❌ Bot stopped: {bt_id}!")

    def stop_bot(self):
        pass

    def stop_bots(self):
        pass
