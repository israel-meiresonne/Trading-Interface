# coding:utf-8
from abc import ABC, abstractmethod


class ModelInterface(ABC):
    def createBot(self, bkr, strg, buyCode, sellCode, configMap):
        """
         To create a new Bot\n
         @Attributes:\n
            bkr         (str): name of a supported Broker\n
            strg        (str): name of a supported Strategy\n
            buyCode     (str): code of the supported Currency to buy\n
            sellCode    (str): code of the supported Currency to buy\n
            configMap   (Map): holds additional config for the Bot\n
        """
        #—————————————————————————— DOCUMENTATION UP —————————————————————————#
        pass

    def getLogID(self):
        """
        To get the id of the log session\n
        @Returns:\n
            str: id of the log session\n
        """
        #—————————————————————————— DOCUMENTATION UP —————————————————————————#
        pass

    def startBot(self, botID):
        """
         To turn on the Bot with the given botID\n
         @Attributes:\n
            botID (str): id of a Bot\n
        """
        #—————————————————————————— DOCUMENTATION UP —————————————————————————#
        pass

    def stopBot(self, botID):
        """
         To turn off the Bot with the given botID\n
         @Attributes:\n
            botID (str): id of a Bot\n
        """
        pass

    def stopBots(self):
        """
         To turn off all  active Bot\n
        """
        pass
