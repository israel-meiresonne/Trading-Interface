from datetime import datetime

from config.Config import Config

# Variables
_DATE = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
# Stage Modes
# STAGE_MODE = Config.STAGE_2
STAGE_MODE = None
# Files
DIR_BINANCE_EXCHANGE_INFOS = "tests/datas/API/brokers/Binance/BinanceFakeAPI/response_exchange_infos.json"
DIR_BINANCE_TRADE_FEE = "tests/datas/API/brokers/Binance/BinanceFakeAPI/trade_fee.json"
DIR_HISTORIC_BNB = 'tests/datas/structure/strategies/MinMax/historic-BNB-2021.03.26 00.52.00.csv'
# Directories
DIR_BROKERS = "model/API/brokers"
DIR_STRATEGIES = "model/structure/strategies"
# Backup Files
DIR_HISTORIC_PRICES = 'content/v0.01/market-historic/active.csv'
DIR_BEGIN_BACKUP = f'content/v0.01/tests/{_DATE}_a_a————————————————————.csv'
DIR_SAVE_BOT_ERRORS = f'content/v0.01/tests/{_DATE}_b_bot_error.csv'
DIR_SAVE_FAKE_API_RQ = f'content/v0.01/tests/{_DATE}_c_logs.csv'
DIR_SAVE_API_RSP = f'content/v0.01/tests/{_DATE}_d_broker_response.csv'
DIR_SAVE_MARKET = f'content/v0.01/tests/{_DATE}_e_market_historic.csv'
DIR_SAVE_MARKET_STALK = f'content/v0.01/tests/{_DATE}_f_market_stalk.csv'
DIR_SAVE_GLOBAL_STATE = f'content/v0.01/tests/{_DATE}_fa_global_state.csv'
DIR_SAVE_CAPITAL = f'content/v0.01/tests/{_DATE}_g_capital_$pair.csv'
DIR_SAVE_MOVES = f'content/v0.01/tests/{_DATE}_h_moves_$pair.csv'
DIR_SAVE_ORDER_RQ = f'content/v0.01/tests/{_DATE}_i_submitted_orders.csv'
DIR_SAVE_ORDER_ACTIONS = f'content/v0.01/tests/{_DATE}_j_order_updates_$pair.csv'
DIR_SAVE_PERIOD_RANKING = f'content/v0.01/tests/{_DATE}_k_period_ranking_$pair.csv'
DIR_END_BACKUP = f'content/v0.01/tests/{_DATE}_z————————————————————.csv'
DIR_SAVE_TOP_ASSET = f'content/v0.01/backups/top_asset/{_DATE}_top_asset.csv'
# Constants
CONST_STABLECOINS = ['busd', 'dai', 'husd', 'pax', 'susd', 'tusd', 'usdc', 'usdn', 'usdt', 'ust', 'usdsb', 'usds']
CONST_FIATS = ['aud', 'brl', 'eur', 'gbp', 'ghs', 'hkd', 'kes', 'kzt', 'ngn', 'nok', 'pen', 'rub', 'try', 'uah', 'ugx',
               'usd']
