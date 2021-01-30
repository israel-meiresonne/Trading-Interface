from model.structure.Log import Log
from view.structure.View import View
from model.structure.Strategy import Strategy

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
        v = self.__get_view()
        m_home = "home"
        ied = False
        ms = View.get_menus()
        cs = ms[m_home][View.MENUS_KEY_TXT]
        while not ied:
            i = v.menu("Choose an execution", cs)
            fc = ms[m_home][View.MENUS_KEY_FUNC][i]
            ied = eval("self."+fc+"()")

    def quit(self):
        return True
    
    def new_bot(self):
        md = self.__get_model()
        vw = self.__get_view()
        bkrs = md.list_brokers()
        stgs = md.list_strategies()
        bkr = bkrs[vw.menu("Choose a Broker", bkrs)]
        stg = stgs[vw.menu("Choose a Strategy", stgs)]
        prcds = md.list_paires(bkr)
        prcd = prcds[vw.menu("Choose a Pair to trade", prcds)]
        # print
        vw.output(View.FILE_MESSAGE, "Broker: "+bkr)
        vw.output(View.FILE_MESSAGE, "Strategy: "+stg)
        vw.output(View.FILE_MESSAGE, "Pair to trade: "+prcd)

        md.create_bot(bkr, stg, prcd)
        self.__get_view().output(View.FILE_MESSAGE, "✅ new Bot created!")

    
    def start_bot(self):
        pass
    
    def stop_bot(self):
        pass
    
    def stop_bots(self):
        pass
    