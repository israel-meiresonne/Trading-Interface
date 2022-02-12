from abc import ABC, abstractmethod
from typing import Any

from model.tools.FileManager import FileManager

from config.files.Dev import Dev

# from config.files.Prod import Prod


class Config(ABC):
    # Configs Constants
    __ENVIRONMENT = None
    __ENV_DEV = "Dev"
    __ENV_PROD = "Prod"
    _FILES_DIR = "config/files"
    # Stages
    STAGE_MODE = "STAGE_MODE"
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    # Files
    DIR_HISTORIC_BNB = "DIR_HISTORIC_BNB"
    FILE_NAME_BOT_BACKUP = 'FILE_NAME_BOT_BACKUP'
    FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE'
    FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE'
    FILE_FAKE_API_ORDERS = 'FILE_FAKE_API_ORDERS'
    FILE_OUTPUT = "FILE_OUTPUT"
    # Configuration
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"
    # Directories
    DIR_SESSIONS = "DIR_SESSIONS"
    DIR_DATABASE = "DIR_DATABASE"
    DIR_ACTUAL_SESSION = "DIR_ACTUAL_SESSION"
    DIR_SAVE_FAKE_API_RQ = "DIR_SAVE_FAKE_API_RQ"
    FILE_PATH_MARKET_HISTORY = "FILE_PATH_MARKET_HISTORY"
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
    TOKEN_PREDICTOR_LEARN_PATH = '$stock_path'
    # Constants
    CONST_STABLECOINS = "CONST_STABLECOINS"
    CONST_FIATS = "CONST_FIATS"
    START_DATE = "START_DATE"
    SESSION_ID = "SESSION_ID"
    API_KEY_BINANCE_PUBLIC = 'API_KEY_BINANCE_PUBLIC'
    API_KEY_BINANCE_SECRET = 'API_KEY_BINANCE_SECRET'


    @staticmethod
    def get(key: str):
        env = Config.get_environment()
        value = eval(f"{env}.{key}")
        return value

    @staticmethod
    def get_environment() -> str:
        _cls = Config
        if _cls.__ENVIRONMENT is None:
            fs = FileManager.get_files(_cls._FILES_DIR, False)
            _cls.__ENVIRONMENT = _cls.__ENV_DEV if (_cls.__ENV_DEV in fs) else _cls.__ENV_PROD
        return _cls.__ENVIRONMENT

    @staticmethod
    def update(key: str, new_value: Any) -> None:
        env = Config.get_environment()
        _env_cls = eval(env)
        old_value = Config.get(key)
        exec(f"{env}.{key} = new_value")
        _env_cls.update(old_value, new_value) if old_value is not None else None

    @staticmethod
    def get_stage() -> str:
        """
        To get actual stage

        Return:
        -------
        return: str
            The actual stage
        """
        return Config.get(Config.STAGE_MODE)

    @staticmethod
    def check_stage(expected_stages: list[str], message: str = None) -> bool:
        """
        To check if the stages are valid

        Paramaters:
        -----------
        expected_stage: str
            List of valid stages
        message: str
            The error message

        Return:
        -------
        return: bool
            True if the stage is valid else raise exception
        """
        message = message if message is not None else "The stage must be '{}', instead stage='{}'"
        stage = Config.get_stage()
        if stage not in expected_stages:
            raise Exception(message.format("' or '".join(expected_stages), stage))
        return True
