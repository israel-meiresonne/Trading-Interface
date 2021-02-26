from abc import ABC, abstractmethod
from model.tools.FileManager import FileManager


class Config(ABC):
    # Environments
    __ENV_DEV = "dev"
    __ENV_PROD = "prod"
    # Stages
    STAGE_MODE = "STAGE_MODE"
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    # Configuration
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"
    # v0.01
    DIR_SAVE_ORDER_RQ = "DIR_SAVE_ORDER_RQ"
    DIR_SAVE_FAKE_API_RQ = "DIR_SAVE_FAKE_API_RQ"
    DIR_HISTORIC_PRICES = "DIR_HISTORIC_PRICES"
    DIR_SAVE_ORDER_ACTIONS = "DIR_SAVE_ORDER_ACTIONS"
    DIR_SAVE_MOVES = "DIR_SAVE_MOVES"
    DIR_SAVE_CAPITAL = "DIR_SAVE_CAPITAL"

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

