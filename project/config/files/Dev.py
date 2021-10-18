from model.structure.database.ModelFeature import ModelFeature as _MF


class Dev:
    # Variables
    START_DATE = _MF.unix_to_date(_MF.get_timestamp(), form=_MF.FORMAT_D_H_M_S_FOR_FILE)
    SESSION_ID = START_DATE
    # Stage Modes
    STAGE_MODE = None
    # Static Files
    DIR_BINANCE_EXCHANGE_INFOS = "tests/datas/API/brokers/Binance/BinanceFakeAPI/response_exchange_infos.json"
    DIR_BINANCE_TRADE_FEE = "tests/datas/API/brokers/Binance/BinanceFakeAPI/trade_fee.json"
    DIR_HISTORIC_BNB = 'tests/datas/structure/strategies/MinMax/historic-BNB-2021.03.26 00.52.00.csv'
    FILE_NAME_BOT_BACKUP = '$bot_ref_bot_backup.json'
    FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'content/executable/model/tools/MyJson/json_instantiate.py'
    FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'content/executable/model/tools/MyJson/test_json_encode_decode.py'
    DIR_PRINT_HISTORIC = 'content/market-historic/Broker/$broker/$pair/$pair_ref/$period.csv'
    # Static paths
    DIR_BROKERS = "model/API/brokers"
    DIR_STRATEGIES = "model/structure/strategies"
    DIR_SESSIONS = 'content/sessions/running/'
    DIR_ACTUAL_SESSION = f'{DIR_SESSIONS}{SESSION_ID}/'
    DIR_MARKET_HISTORICS = 'content/market-historic/Active/$broker/$pair/'
    DIR_SAVE_DATAS = f'{DIR_ACTUAL_SESSION}datas/active/{SESSION_ID}/'
    # Dynamic paths
    DIR_DATABASE = f'{DIR_ACTUAL_SESSION}storage/$stage/$class/'
    FILE_BINANCE_FAKE_API_ORDERS = f'{DIR_ACTUAL_SESSION}storage/$stage/BinanceFakeAPI/orders/{SESSION_ID}_orders.json'
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
    DIR_SAVE_ORDER_RQ = f'{DIR_SAVE_DATAS}{SESSION_ID}_i_submitted_orders.csv'
    DIR_SAVE_ORDER_ACTIONS = f'{DIR_SAVE_DATAS}{SESSION_ID}_j_order_updates_$pair.csv'
    DIR_SAVE_PERIOD_RANKING = f'{DIR_SAVE_DATAS}{SESSION_ID}_k_period_ranking_$pair.csv'
    DIR_END_BACKUP = f'{DIR_SAVE_DATAS}{SESSION_ID}_z————————————————————.csv'
    DIR_SAVE_TOP_ASSET = f'content/backups/top_asset/{SESSION_ID}_top_asset.csv'
    # Storage
    DIR_STORAGE = 'content/storage/'
    # Predictor
    PREDICTOR_FILE_PATH_HISTORY = '$class/market-histories/$pair/$period.csv'
    PREDICTOR_PATH_LEARN = '$class/learns/$pair/$period/$model_type/'
    # Constants
    CONST_STABLECOINS = ['busd', 'dai', 'husd', 'pax', 'susd', 'tusd', 'usdc', 'usdn', 'usdt', 'ust', 'usdsb', 'usds']
    CONST_FIATS = ['aud', 'brl', 'eur', 'gbp', 'ghs', 'hkd', 'kes', 'kzt', 'ngn', 'nok', 'pen', 'rub', 'try', 'uah',
                   'ugx', 'usd']
    API_KEY_BINANCE_PUBLIC = 'mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5'
    API_KEY_BINANCE_SECRET = 'xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr'

    @staticmethod
    def update(old: str, new: str) -> None:
        """
        To replace occurence of old word with new word in some constants

        Parameters
        ----------
        old: str
            Old word to search
        new: str
            New word to replace old occurences
        """
        Dev.DIR_SAVE_DATAS =                Dev.DIR_SAVE_DATAS.replace(old, new)
        Dev.DIR_ACTUAL_SESSION =            Dev.DIR_ACTUAL_SESSION.replace(old, new)
        Dev.FILE_BINANCE_FAKE_API_ORDERS =  Dev.FILE_BINANCE_FAKE_API_ORDERS.replace(old, new)
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
        Dev.DIR_SAVE_ORDER_RQ =             Dev.DIR_SAVE_ORDER_RQ.replace(old, new)
        Dev.DIR_SAVE_ORDER_ACTIONS =        Dev.DIR_SAVE_ORDER_ACTIONS.replace(old, new)
        Dev.DIR_SAVE_PERIOD_RANKING =       Dev.DIR_SAVE_PERIOD_RANKING.replace(old, new)
        Dev.DIR_END_BACKUP =                Dev.DIR_END_BACKUP.replace(old, new)
        Dev.DIR_SAVE_TOP_ASSET =            Dev.DIR_SAVE_TOP_ASSET.replace(old, new)
