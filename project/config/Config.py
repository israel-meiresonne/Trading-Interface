from abc import ABC, abstractmethod
from model.tools.FileManager import FileManager


class Config(ABC):
    __ENV_DEV = "dev"
    __ENV_PROD = "prod"
    # keys down
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"

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

