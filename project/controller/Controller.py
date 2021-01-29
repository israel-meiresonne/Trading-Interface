from model.structure.Log import Log
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
        v = self.__get_view()
        m_home = "home"
        ied = False
        ms = View.get_menus()
        cs = ms[m_home][View.MENUS_KEY_TXT]
        while not ied:
            i = v.menu(cs)
            fc = ms[m_home][View.MENUS_KEY_FUNC][i]
            v.output(View.FILE_MESSAGE, fc)
            ied = eval("self."+fc+"()")

    def quit(self):
        return True
    
    def new_bot(self):
        md = self.__get_model()
        md.create_bot()
        self.__get_view().output(View.FILE_MESSAGE, "✅ new Bot created!")

    
    def start_bot(self):
        pass
    
    def stop_bot(self):
        pass
    
    def stop_bots(self):
        pass
    