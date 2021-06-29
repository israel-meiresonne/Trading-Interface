from datetime import datetime

from config.Config import Config

# Variables
START_DATE = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
# Stage Modes
# STAGE_MODE = Config.STAGE_2
STAGE_MODE = None
# Files
DIR_BINANCE_EXCHANGE_INFOS = "tests/datas/API/brokers/Binance/BinanceFakeAPI/response_exchange_infos.json"
DIR_BINANCE_TRADE_FEE = "tests/datas/API/brokers/Binance/BinanceFakeAPI/trade_fee.json"
DIR_HISTORIC_BNB = 'tests/datas/structure/strategies/MinMax/historic-BNB-2021.03.26 00.52.00.csv'
FILE_NAME_BOT_BACKUP = '$bot_ref_bot_backup.data'
FILE_EXECUTABLE_MYJSON_JSON_INSTANTIATE = 'content/executable/model/tools/MyJson/json_instantiate.py'
FILE_EXECUTABLE_MYJSON_TEST_JSON_ENCODE_DECODE = 'content/executable/model/tools/MyJson/test_json_encode_decode.py'
# Directories
DIR_BROKERS = "model/API/brokers"
DIR_STRATEGIES = "model/structure/strategies"
# Backup Files
DIR_DATABASE = 'content/storage/$stage/$class/'    # i.e.: 'content/database/STAGE_3/Bot/'
DIR_MARKET_HISTORICS = 'content/v0.01/market-historic/Active/$broker/$pair/'
DIR_PRINT_HISTORIC = 'content/v0.01/market-historic/Broker/$broker/$pair/$pair_ref/$period.csv'
DIR_BEGIN_BACKUP = f'content/v0.01/tests/{START_DATE}_a_a————————————————————.csv'
DIR_SAVE_BOT_ERRORS = f'content/v0.01/tests/{START_DATE}_b_bot_error.csv'
DIR_SAVE_FAKE_API_RQ = f'content/v0.01/tests/{START_DATE}_c_logs.csv'
DIR_SAVE_API_RSP = f'content/v0.01/tests/{START_DATE}_d_broker_response.csv'
DIR_SAVE_MARKET = f'content/v0.01/tests/{START_DATE}_e_market_historic.csv'
DIR_SAVE_MARKET_STALK = f'content/v0.01/tests/{START_DATE}_f_market_stalk.csv'
DIR_SAVE_GLOBAL_STATE = f'content/v0.01/tests/{START_DATE}_fa_global_capital.csv'
DIR_SAVE_GLOBAL_MOVES = f'content/v0.01/tests/{START_DATE}_fb_$class_moves.csv'
DIR_SAVE_CAPITAL = f'content/v0.01/tests/{START_DATE}_g_capital_$pair.csv'
DIR_SAVE_MOVES = f'content/v0.01/tests/{START_DATE}_h_moves_$pair.csv'
DIR_SAVE_ORDER_RQ = f'content/v0.01/tests/{START_DATE}_i_submitted_orders.csv'
DIR_SAVE_ORDER_ACTIONS = f'content/v0.01/tests/{START_DATE}_j_order_updates_$pair.csv'
DIR_SAVE_PERIOD_RANKING = f'content/v0.01/tests/{START_DATE}_k_period_ranking_$pair.csv'
DIR_END_BACKUP = f'content/v0.01/tests/{START_DATE}_z————————————————————.csv'
DIR_SAVE_TOP_ASSET = f'content/v0.01/backups/top_asset/{START_DATE}_top_asset.csv'
# Constants
CONST_STABLECOINS = ['busd', 'dai', 'husd', 'pax', 'susd', 'tusd', 'usdc', 'usdn', 'usdt', 'ust', 'usdsb', 'usds']
CONST_FIATS = ['aud', 'brl', 'eur', 'gbp', 'ghs', 'hkd', 'kes', 'kzt', 'ngn', 'nok', 'pen', 'rub', 'try', 'uah', 'ugx',
               'usd']
API_KEY_BINANCE_PUBLIC = 'mHRSn6V68SALTzCyQggb1EPaEhIDVAcZ6VjnxKBCqwFDQCOm71xiOYJSrEIlqCq5'
API_KEY_BINANCE_SECRET = 'xDzXRjV8vusxpQtlSLRk9Q0pj5XCNODm6GDAMkOgfsHZZDZ1OHRUuMgpaaF5oQgr'
