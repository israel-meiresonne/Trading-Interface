from model.structure.Log import Log
from model.tools.Map import Map
from view.structure.View import View

# from model.API.brokers.Binance.BinanceAPI import BinanceAPI

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
        """
        api_pb = "mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5"
        api_sk = "xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr"
        rq = BinanceAPI.RQ_KLINES
        prms_map = Map()
        prms_map.put("BTCUSDT", Map.symbol)
        prms_map.put("1m", Map.interval)
        prms_map.put(10, Map.limit)

        bapi = BinanceAPI(api_pb, api_sk, True)
        brq = bapi.request_api(rq, prms_map)
        print("type: ", type(brq))
        hdrs = brq.get_headers()
        ctnt = brq.get_content()
        cd = brq.get_status_code()
        url = brq.get_url()
        print(f"status code: {type(cd)}", cd)
        print(f"url: {type(url)}", url)
        print(f"header({type(hdrs)}): ", hdrs)
        print(f"content: {type(ctnt)}", ctnt)
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
        cfgs_map.put(vw.input(f"Enter the public key for {bkr}"), bkr, Map.api_pb)
        cfgs_map.put(vw.input(f"Enter the secret key for {bkr}"), bkr, Map.api_sk)
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
        # bt_ids = ["hello"]
        bt_id = bt_ids[vw.menu("Choose the Bot to start:", bt_ids)]
        md.start_bot(bt_id)
        vw.output(View.FILE_MESSAGE, f"❌ Bot stopped: {bt_id}!")

    def stop_bot(self):
        pass

    def stop_bots(self):
        pass
