from model.structure.database.ModelFeature import ModelFeature as _MF


class Dev:
    ID_TOKE = "@"
    # Variables
    START_DATE = _MF.unix_to_date(_MF.get_timestamp(), form=_MF.FORMAT_D_H_M_S_FOR_FILE)
    SESSION_ID = ID_TOKE + START_DATE + ID_TOKE
    # Stage Modes
    STAGE_MODE = None
    # Static Files
    DIR_HISTORIC_BNB = 'tests/datas/structure/strategies/MinMax/historic-BNB-2021.03.26 00.52.00.csv'
    FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'content/executable/model/tools/MyJson/json_instantiate.py'
    FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'content/executable/model/tools/MyJson/test_json_encode_decode.py'
    # Static paths
    DIR_BROKERS = "model/API/brokers"
    DIR_STRATEGIES = "model/structure/strategies"
    DIR_SESSIONS = 'content/sessions/running/'
    DIR_ANALYSES =  'content/sessions/analyse/'
    DIR_ACTUAL_SESSION = f'{DIR_SESSIONS}{SESSION_ID}/'
    DIR_SAVE_DATAS = f'{DIR_ACTUAL_SESSION}datas/active/{SESSION_ID}/'
    # View
    DIR_VIEW = f'{DIR_ACTUAL_SESSION}view/'
    DIR_VIEW_HAND = f'{DIR_VIEW}Hand/'
    FILE_VIEW_HAND_STALK = f'{DIR_VIEW_HAND}trade/{SESSION_ID}_stalk_view.csv'
    FILE_VIEW_HAND_POSITION = f'{DIR_VIEW_HAND}trade/{SESSION_ID}_position_view.csv'
    FILE_VIEW_HAND_MARKET_TREND = f'{DIR_VIEW_HAND}analyse/$period/{SESSION_ID}_$period_market_trend_view.csv'
    FILE_MODEL_OUTPUT = f'{DIR_VIEW}model/{START_DATE}_model_output.txt'
    FILE_VIEW_OUTPUT = f'{DIR_VIEW}view/{START_DATE}_view_output.txt'
    # Dynamic paths
    DIR_DATABASE = f'{DIR_ACTUAL_SESSION}storage/$stage/$class/'
    FILE_SESSION_CONFIG = f'{DIR_ACTUAL_SESSION}session.conf'
    FILE_FAKE_API_ORDERS = f'{DIR_ACTUAL_SESSION}storage/$stage/$class/orders/{SESSION_ID}_orders.json'
    DIR_BEGIN_BACKUP = f'{DIR_SAVE_DATAS}{SESSION_ID}_a_a————————————————————.csv'
    DIR_SAVE_BOT_ERRORS = f'{DIR_SAVE_DATAS}{SESSION_ID}_b_bot_error.csv'
    DIR_SAVE_FAKE_API_RQ = f'{DIR_SAVE_DATAS}{SESSION_ID}_c_logs.csv'
    DIR_SAVE_API_RSP = f'{DIR_SAVE_DATAS}{SESSION_ID}_d_broker_response.csv'
    DIR_SAVE_MARKET = f'{DIR_SAVE_DATAS}{SESSION_ID}_e_market_historic.csv'
    DIR_SAVE_MARKET_STALK = f'{DIR_SAVE_DATAS}{SESSION_ID}_f_market_stalk.csv'
    DIR_SAVE_GLOBAL_STATE = f'{DIR_SAVE_DATAS}{SESSION_ID}_fa_global_capital.csv'
    DIR_SAVE_GLOBAL_MOVES = f'{DIR_SAVE_DATAS}{SESSION_ID}_fb_$class_moves.csv'
    DIR_SAVE_CAPITAL = f'{DIR_SAVE_DATAS}{SESSION_ID}_g_capital_$pair.csv'
    DIR_SAVE_MOVES = f'{DIR_SAVE_DATAS}{SESSION_ID}_h_moves_$pair.csv'
    DIR_SAVE_SELL_CONDITIONS = f'{DIR_SAVE_DATAS}{SESSION_ID}_ha_sell_conditions_$pair.csv'
    DIR_SAVE_ORDER_ACTIONS = f'{DIR_SAVE_DATAS}{SESSION_ID}_j_order_updates_$pair.csv'
    DIR_SAVE_PERIOD_RANKING = f'{DIR_SAVE_DATAS}{SESSION_ID}_k_period_ranking_$pair.csv'
    DIR_END_BACKUP = f'{DIR_SAVE_DATAS}{SESSION_ID}_z————————————————————.csv'
    DIR_SAVE_TOP_ASSET = f'content/backups/top_asset/{SESSION_ID}_top_asset.csv'
    FILE_SAVE_HAND = f'{DIR_DATABASE}$id/{START_DATE}||$id||hand_backup.json'
    FILE_SAVE_BOT = f'{DIR_DATABASE}$id/{START_DATE}||$id||bot_backup.json'
    # Storage
    DIR_STORAGE = 'content/storage/'
    FILE_PATH_MARKET_HISTORY = f'{DIR_STORAGE}MarketPrice/histories/$stock_path/$broker/$pair/$period.csv'
    DIR_STRATEGY_STORAGE = f'{DIR_STORAGE}Strategy/'

    # Predictor
    PREDICTOR_FILE_PATH_HISTORY = '$class/market-histories/$pair/$period.csv'
    PREDICTOR_PATH_LEARN = '$class/learns/$stock_path/$pair/$period/$price_type/'
    # Constants
    MAIN_STABLECOINS = ['busd', 'dai', 'usdc', 'usdt']
    CONST_STABLECOINS = [*MAIN_STABLECOINS, 'bidr', 'fei', 'frax', 'gusd', 'husd', 'idrt', 'lusd', 'pax', 'rsr', 'susd', 'tribe', 'tusd', 'usdn', 'usdp', 'usds', 'usdsb', 'usdx', 'ust', 'vai', 'xsgd']
    CONST_FIATS = [
        'aed', 'afn', 'all', 'amd', 'ang', 'aoa', 'ars', 'aud', 'awg', 'azn', 'bam', 'bbd', 'bdt', 'bgn', 'bhd', 
        'bif', 'bmd', 'bnd', 'bob', 'bov', 'brl', 'bsd', 'btn', 'bwp', 'byn', 'bzd', 'cad', 'cdf', 'che', 'chf', 
        'chw', 'clf', 'clp', 'cny', 'cop', 'cou', 'crc', 'cuc', 'cup', 'cve', 'czk', 'djf', 'dkk', 'dop', 'dzd', 
        'egp', 'etb', 'eur', 'fjd', 'fkp', 'gbp', 'gel', 'ghs', 'gip', 'gmd', 'gnf', 'gtq', 'gyd', 'hkd', 
        'hnl', 'hrk', 'htg', 'huf', 'idr', 'ils', 'inr', 'iqd', 'irr', 'isk', 'jmd', 'jod', 'jpy', 'kes', 'kgs', 
        'khr', 'kmf', 'kpw', 'krw', 'kwd', 'kyd', 'kzt', 'lak', 'lbp', 'lkr', 'lrd', 'lsl', 'lyd', 'mad', 'mdl', 
        'mga', 'mkd', 'mmk', 'mnt', 'mop', 'mru', 'mur', 'mvr', 'mwk', 'mxn', 'mxv', 'myr', 'mzn', 'nad', 'ngn', 
        'nio', 'nok', 'npr', 'nzd', 'omr', 'pab', 'pen', 'pgk', 'php', 'pkr', 'pln', 'pyg', 'qar', 'ron', 'rsd', 
        'rub', 'rwf', 'sar', 'sbd', 'scr', 'sdg', 'sek', 'sgd', 'shp', 'sll', 'sos', 'srd', 'ssp', 'stn', 'svc', 
        'syp', 'szl', 'thb', 'tjs', 'tmt', 'tnd', 'top', 'try', 'ttd', 'twd', 'tzs', 'uah', 'ugx', 'usd', 'usn', 
        'uyi', 'uyu', 'uyw', 'uzs', 'ved', 'ves', 'vnd', 'vuv', 'wst', 'xaf', 'xag', 'xau', 'xba', 'xbb', 'xbc', 
        'xbd', 'xcd', 'xdr', 'xof', 'xpd', 'xpf', 'xpt', 'xsu', 'xts', 'xua', 'xxx', 'yer', 'zar', 'zmw', 'zwl']
    API_KEY_BINANCE_PUBLIC = 'mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5'
    API_KEY_BINANCE_SECRET = 'xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr'
    FAKE_API_START_END_TIME = {
        'start': 1608537600,  # UTC 2020-12-21 8:00:00
        'end': 1614556800     # UTC 2021-03-01 0:00:00
        }

    @staticmethod
    def update(old: str, new: str) -> None:
        """
        To replace occurence of old word with new word in some constants
        NOTE: need to update only constant that contain other constant

        Parameters
        ----------
        old: str
            Old word to search
        new: str
            New word to replace old occurences
        """
        Dev.SESSION_ID =                    Dev.SESSION_ID.replace(old, new)
        Dev.FILE_MODEL_OUTPUT =             Dev.FILE_MODEL_OUTPUT.replace(old, new, 1)
        Dev.FILE_VIEW_OUTPUT =              Dev.FILE_VIEW_OUTPUT.replace(old, new)
        Dev.DIR_SAVE_DATAS =                Dev.DIR_SAVE_DATAS.replace(old, new)
        Dev.DIR_ACTUAL_SESSION =            Dev.DIR_ACTUAL_SESSION.replace(old, new)
        Dev.FILE_FAKE_API_ORDERS =          Dev.FILE_FAKE_API_ORDERS.replace(old, new)
        Dev.DIR_DATABASE =                  Dev.DIR_DATABASE.replace(old, new)
        Dev.DIR_BEGIN_BACKUP =              Dev.DIR_BEGIN_BACKUP.replace(old, new)
        Dev.DIR_SAVE_BOT_ERRORS =           Dev.DIR_SAVE_BOT_ERRORS.replace(old, new)
        Dev.DIR_SAVE_FAKE_API_RQ =          Dev.DIR_SAVE_FAKE_API_RQ.replace(old, new)
        Dev.DIR_SAVE_API_RSP =              Dev.DIR_SAVE_API_RSP.replace(old, new)
        Dev.DIR_SAVE_MARKET =               Dev.DIR_SAVE_MARKET.replace(old, new)
        Dev.DIR_SAVE_MARKET_STALK =         Dev.DIR_SAVE_MARKET_STALK.replace(old, new)
        Dev.DIR_SAVE_GLOBAL_STATE =         Dev.DIR_SAVE_GLOBAL_STATE.replace(old, new)
        Dev.DIR_SAVE_GLOBAL_MOVES =         Dev.DIR_SAVE_GLOBAL_MOVES.replace(old, new)
        Dev.DIR_SAVE_CAPITAL =              Dev.DIR_SAVE_CAPITAL.replace(old, new)
        Dev.DIR_SAVE_MOVES =                Dev.DIR_SAVE_MOVES.replace(old, new)
        Dev.DIR_SAVE_SELL_CONDITIONS =      Dev.DIR_SAVE_SELL_CONDITIONS.replace(old, new)
        Dev.DIR_SAVE_ORDER_ACTIONS =        Dev.DIR_SAVE_ORDER_ACTIONS.replace(old, new)
        Dev.DIR_SAVE_PERIOD_RANKING =       Dev.DIR_SAVE_PERIOD_RANKING.replace(old, new)
        Dev.DIR_END_BACKUP =                Dev.DIR_END_BACKUP.replace(old, new)
        Dev.DIR_SAVE_TOP_ASSET =            Dev.DIR_SAVE_TOP_ASSET.replace(old, new)
        Dev.DIR_VIEW =                      Dev.DIR_VIEW.replace(old, new)
        Dev.DIR_VIEW_HAND =                 Dev.DIR_VIEW_HAND.replace(old, new)
        Dev.FILE_VIEW_HAND_STALK =          Dev.FILE_VIEW_HAND_STALK.replace(old, new)
        Dev.FILE_VIEW_HAND_POSITION =       Dev.FILE_VIEW_HAND_POSITION.replace(old, new)
        Dev.FILE_SAVE_HAND =                Dev.FILE_SAVE_HAND.replace(old, new)
        Dev.FILE_VIEW_HAND_MARKET_TREND =   Dev.FILE_VIEW_HAND_MARKET_TREND.replace(old, new)
        Dev.FILE_SAVE_BOT =                 Dev.FILE_SAVE_BOT.replace(old, new)
        Dev.FILE_SESSION_CONFIG =           Dev.FILE_SESSION_CONFIG.replace(old, new)
