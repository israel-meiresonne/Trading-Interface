from abc import ABC
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
    ID_TOKE = "ID_TOKE"
    # Stages
    STAGE_MODE = "STAGE_MODE"
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    # Files
    DIR_HISTORIC_BNB = "DIR_HISTORIC_BNB"
    FILE_SESSION_CONFIG = "FILE_SESSION_CONFIG"
    FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE'
    FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE'
    FILE_FAKE_API_ORDERS = 'FILE_FAKE_API_ORDERS'
    FILE_MODEL_OUTPUT = "FILE_MODEL_OUTPUT"
    FILE_VIEW_HAND_STALK = "FILE_VIEW_HAND_STALK"
    FILE_VIEW_HAND_POSITION = "FILE_VIEW_HAND_POSITION"
    FILE_SAVE_HAND = "FILE_SAVE_HAND"
    FILE_VIEW_HAND_MARKET_TREND = "FILE_VIEW_HAND_MARKET_TREND"
    FILE_SAVE_BOT = "FILE_SAVE_BOT"
    FILE_VIEW_OUTPUT = "FILE_VIEW_OUTPUT"
    FILE_BACKTEST_TEST = "FILE_BACKTEST_TEST"
    FILE_BACKTEST_TRADE = "FILE_BACKTEST_TRADE"
    FILE_BACKTEST_CONDITION = "FILE_BACKTEST_CONDITION"
    # Configuration
    DIR_BROKERS = "DIR_BROKERS"
    DIR_STRATEGIES = "DIR_STRATEGIES"
    # Directories
    DIR_VIEW = "DIR_VIEW"
    DIR_SESSIONS = "DIR_SESSIONS"
    DIR_DATABASE = "DIR_DATABASE"
    DIR_ACTUAL_SESSION = "DIR_ACTUAL_SESSION"
    DIR_SESSION_CONFIG = "DIR_SESSION_CONFIG"
    DIR_SAVE_FAKE_API_RQ = "DIR_SAVE_FAKE_API_RQ"
    FILE_PATH_MARKET_HISTORY = "FILE_PATH_MARKET_HISTORY"
    DIR_SAVE_ORDER_ACTIONS = "DIR_SAVE_ORDER_ACTIONS"
    DIR_SAVE_MOVES = "DIR_SAVE_MOVES"
    DIR_SAVE_SELL_CONDITIONS = "DIR_SAVE_SELL_CONDITIONS"
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
    DIR_STRATEGY_STORAGE = "DIR_STRATEGY_STORAGE"
    # Predictor
    PREDICTOR_FILE_PATH_HISTORY = "PREDICTOR_FILE_PATH_HISTORY"
    PREDICTOR_PATH_LEARN = "PREDICTOR_PATH_LEARN"
    TOKEN_PREDICTOR_LEARN_PATH = '$stock_path'
    # Constants
    CONST_STABLECOINS = "CONST_STABLECOINS"
    MAIN_STABLECOINS = "MAIN_STABLECOINS"
    CONST_FIATS = "CONST_FIATS"
    START_DATE = "START_DATE"
    SESSION_ID = "SESSION_ID"
    API_KEY_BINANCE_PUBLIC = 'API_KEY_BINANCE_PUBLIC'
    API_KEY_BINANCE_SECRET = 'API_KEY_BINANCE_SECRET'
    FAKE_API_START_END_TIME = "FAKE_API_START_END_TIME"


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
        _env_cls.update(old_value, new_value) if isinstance(new_value, str) and (old_value is not None) else None

    def update_session_id(new_id: str) -> None:
        """
        To update session's id

        Parameters:
        -----------
        new_id: str
            The new id
        """
        Config.update(Config.SESSION_ID, '@xxx@')
        Config.update(Config.SESSION_ID, new_id)

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

    @classmethod
    def label_session_id(cls) -> str:
        """
        To append git branch's name in session's id
        """
        from model.structure.database.ModelFeature import ModelFeature as _MF
        command = "git branch | grep '*' | awk -F ' ' '{print $NF}' | sed 's#)##'"
        branch_name = _MF.shell(command)
        branch_name = branch_name.replace("\n", "")
        session_id = cls.get(cls.SESSION_ID)
        token = cls.get(cls.ID_TOKE)
        session_id = session_id.replace(token, "")
        new_session_id = f"{session_id}_{branch_name}"
        Config.update_session_id(new_session_id)

    @classmethod
    def print_session_config(cls) -> None:
        from model.structure.database.ModelFeature import ModelFeature as _MF
        config_cmd = 'commit=$(git log --oneline | head -n 1)'
        config_cmd += ' ; commit_id=$(git log | head -n 1 | cut -d " " -f 2)'
        config_cmd += ' ; commit_m=$(git log --oneline | head -n 1 | cut -d " " -f 2-)'
        config_cmd += ' ; branch=$(git branch | grep "*" | awk -F " " "{print \$NF}" | sed "s#)##")'
        config_cmd += ' ; now_date=$(date -u "+%Y-%m-%d %H:%M:%S")'
        config_cmd += ' ; pyv=$(python3 -V)'
        config_cmd += ' ; echo "Date:       $now_date"'
        config_cmd += ' ; echo "USER:       $USER"'
        config_cmd += ' ; echo "PWD:        $PWD"'
        config_cmd += ' ; echo "UID:        $UID"'
        config_cmd += ' ; echo "PPID:       $PPID"'
        config_cmd += ' ; echo "PID:        $$"'
        config_cmd += ' ; echo "Version:    $pyv"'
        config_cmd += ' ; echo "Branch:     $branch"'
        config_cmd += ' ; echo "ID:         $commit_id"'
        config_cmd += ' ; echo "Subject:    $commit_m"'
        config_cmd += ' ; echo "Stage:      {}"'.format(cls.get(cls.STAGE_MODE))
        config_cmd += ' ; echo "#"'
        FileManager.write(Config.get(Config.FILE_SESSION_CONFIG), _MF.shell(config_cmd), overwrite=False, make_dir=True, line_return=False)
