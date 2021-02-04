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
        ied = False
        ms = View.get_menus()
        cs = ms[m_home][View.MENUS_KEY_TXT]
        while not ied:
            i = vw.menu("Choose an execution", cs)
            fc = ms[m_home][View.MENUS_KEY_FUNC][i]
            ied = eval("self." + fc + "()")

    def quit(self):
        return True

    def new_bot(self):
        md = self.__get_model()
        vw = self.__get_view()
        # params
        bkrs = md.list_brokers()
        stgs = md.list_strategies()
        bkr = bkrs[vw.menu("Choose a Broker:", bkrs)]
        stg = stgs[vw.menu("Choose a Strategy:", stgs)]
        prcds = md.list_paires(bkr)
        prcd = prcds[vw.menu("Choose a Pair to trade:", prcds)]
        # configs
        cfgs_map = Map()
        cfgs_map.put(vw.input(msg=f"Enter the public key for {bkr}", secure=True), bkr, Map.api_pb)
        cfgs_map.put(vw.input(msg=f"Enter the secret key for {bkr}", secure=True), bkr, Map.api_sk)
        mds = {"Test mode": True, "Real mode": False}
        mds_ks = list(mds.keys())
        cfgs_map.put(mds[mds_ks[vw.menu("Choose your mode:", mds_ks)]], bkr, Map.test_mode)
        print(cfgs_map.get_map())
        # create Bot
        md.create_bot(bkr, stg, prcd, cfgs_map.get_map())
        vw.output(View.FILE_MESSAGE, "✅ new Bot created!")

    def start_bot(self):
        md = self.__get_model()
        vw = self.__get_view()
        bt_ids = list(md.get_bots().keys())
        if len(bt_ids) <= 0:
            vw.output(View.FILE_ERROR, "You have no Bot created")
            return None
        bt_id = bt_ids[vw.menu("Choose the Bot to start:", bt_ids)]
        md.start_bot(bt_id)
        vw.output(View.FILE_MESSAGE, f"❌ Bot stopped: {bt_id}!")

    def stop_bot(self):
        pass

    def stop_bots(self):
        pass
