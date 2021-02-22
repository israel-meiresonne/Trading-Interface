from abc import ABC, abstractmethod
from model.tools.FileManager import FileManager


class Config(ABC):
    # Environment
    __ENV_DEV = "dev"
    __ENV_PROD = "prod"
    # Stage
    STATEGE_1 = "STATEGE_1"
    STATEGE_2 = "STATEGE_2"
    # Configuration
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"
    # v0.01
    DIR_SAVE_ORDER_RQ = "DIR_SAVE_ORDER_RQ"
    DIR_SAVE_FAKE_API_RQ = "DIR_SAVE_FAKE_API_RQ"
    DIR_HISTORIC_PRICES = "DIR_HISTORIC_PRICES"
    DIR_SAVE_ORDER_ACTIONS = "DIR_SAVE_ORDER_ACTIONS"

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get(k: str):
        fs = FileManager.get_files("config/files", False)
        if Config.__ENV_DEV in fs:
            exec("from config.files.dev import "+k)
            v = eval(k)
        else:
            exec("from config.files.prod import "+k)
            v = eval(k)
        return v

