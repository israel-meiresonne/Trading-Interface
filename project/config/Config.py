from abc import ABC, abstractmethod
from typing import Any

from model.tools.FileManager import FileManager


class Config(ABC):
    # Configs Constants
    __ENV_DEV = "dev"
    __ENV_PROD = "prod"
    _FILES_DIR = "config/files"
    # Stages
    STAGE_MODE = "STAGE_MODE"
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    # Files
    DIR_BINANCE_EXCHANGE_INFOS = "DIR_BINANCE_EXCHANGE_INFOS"
    DIR_BINANCE_TRADE_FEE = "DIR_BINANCE_TRADE_FEE"
    DIR_HISTORIC_BNB = "DIR_HISTORIC_BNB"
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
    DIR_SAVE_MARKET = "DIR_SAVE_MARKET"
    DIR_SAVE_API_RSP = "DIR_SAVE_API_RSP"
    DIR_SAVE_BOT_ERRORS = "DIR_SAVE_BOT_ERRORS"
    DIR_SAVE_TOP_ASSET = "DIR_SAVE_TOP_ASSET"
    DIR_SAVE_PERIOD_RANKING = "DIR_SAVE_PERIOD_RANKING"
    DIR_BEGIN_BACKUP = "DIR_BEGIN_BACKUP"
    DIR_END_BACKUP = "DIR_END_BACKUP"
    DIR_SAVE_MARKET_STALK = "DIR_SAVE_MARKET_STALK"
    DIR_SAVE_GLOBAL_STATE = "DIR_SAVE_GLOBAL_STATE"
    DIR_SAVE_GLOBAL_MOVES = "DIR_SAVE_GLOBAL_MOVES"
    # Constants
    CONST_STABLECOINS = "CONST_STABLECOINS"
    CONST_FIATS = "CONST_FIATS"

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get(k: str):
        env = Config.get_environment()
        if env == Config.__ENV_DEV:
            exec("from config.files.dev import " + k)
            v = eval(k)
        elif env == Config.__ENV_PROD:
            exec("from config.files.prod import " + k)
            v = eval(k)
        else:
            raise Exception(f"Unknown environment '{env}'")
        return v

    @staticmethod
    def get_environment() -> str:
        fs = FileManager.get_files(Config._FILES_DIR, False)
        return Config.__ENV_DEV if (Config.__ENV_DEV in fs) else Config.__ENV_PROD

    @staticmethod
    def update(k: str, v: Any) -> None:
        env = Config.get_environment()
        if env == Config.__ENV_DEV:
            exec("import config.files.dev as CONF_FILE")
            exec(f"CONF_FILE.{k} = v")
        elif env == Config.__ENV_PROD:
            exec("import config.files.prod as CONF_FILE")
            exec(f"CONF_FILE.{k} = v")
