from abc import ABC, abstractmethod
from typing import Any

from model.tools.FileManager import FileManager
from config.files.Dev import Dev
# from config.files.Prod import Prod


class Config(ABC):
    # Configs Constants
    __ENV_DEV = "Dev"
    __ENV_PROD = "Prod"
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
    FILE_NAME_BOT_BACKUP = 'FILE_NAME_BOT_BACKUP'
    FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE'
    FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE'
    FILE_BINANCE_FAKE_API_ORDERS = 'FILE_BINANCE_FAKE_API_ORDERS'
    # Configuration
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"
    # Directories
    DIR_SESSIONS = "DIR_SESSIONS"
    DIR_DATABASE = "DIR_DATABASE"
    DIR_SAVE_ORDER_RQ = "DIR_SAVE_ORDER_RQ"
    DIR_SAVE_FAKE_API_RQ = "DIR_SAVE_FAKE_API_RQ"
    DIR_MARKET_HISTORICS = "DIR_MARKET_HISTORICS"
    DIR_PRINT_HISTORIC = "DIR_PRINT_HISTORIC"
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
    DIR_STORAGE = "DIR_STORAGE"
    DIR_SAVE_DATAS = "DIR_SAVE_DATAS"
    DIR_ANALYSES = "DIR_ANALYSES"
    # Predictor
    PREDICTOR_FILE_PATH_HISTORY = "PREDICTOR_FILE_PATH_HISTORY"
    PREDICTOR_PATH_LEARN = "PREDICTOR_PATH_LEARN"
    # Constants
    CONST_STABLECOINS = "CONST_STABLECOINS"
    CONST_FIATS = "CONST_FIATS"
    START_DATE = "START_DATE"
    SESSION_ID = "SESSION_ID"
    API_KEY_BINANCE_PUBLIC = 'API_KEY_BINANCE_PUBLIC'
    API_KEY_BINANCE_SECRET = 'API_KEY_BINANCE_SECRET'

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get(key: str):
        env = Config.get_environment()
        value = eval(f"{env}.{key}")
        """
        if env == Config.__ENV_DEV:
            exec("from config.files.Dev import " + k)
            value = eval(k)
        elif env == Config.__ENV_PROD:
            exec("from config.files.prod import " + k)
            value = eval(k)
        else:
            raise Exception(f"Unknown environment '{env}'")
        """
        return value

    @staticmethod
    def get_environment() -> str:
        fs = FileManager.get_files(Config._FILES_DIR, False)
        return Config.__ENV_DEV if (Config.__ENV_DEV in fs) else Config.__ENV_PROD

    @staticmethod
    def update(key: str, new_value: Any) -> None:
        env = Config.get_environment()
        _env_cls = eval(env)
        old_value = Config.get(key)
        exec(f"{env}.{key} = new_value")
        """
        if env == Config.__ENV_DEV:
            import config.files.dev as CONF_FILE
            exec(f"CONF_FILE.{key} = new_value")
        elif env == Config.__ENV_PROD:
            import config.files.prod as CONF_FILE
            exec(f"CONF_FILE.{key} = new_value")
        else:
            raise Exception(f"Unknown environment '{env}'")
        """
        _env_cls.update(old_value, new_value) if old_value is not None else None
