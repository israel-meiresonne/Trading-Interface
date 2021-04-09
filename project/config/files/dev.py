from datetime import datetime

from config.Config import Config

# Variables
_DATE = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
# Stage Modes
# STAGE_MODE = Config.STAGE_2
STAGE_MODE = None
# Directories
DIR_BROKERS = "model/API/brokers"
DIR_STRATEGIES = "model/structure/strategies"
# Backup Files
DIR_SAVE_ORDER_RQ = f'content/v0.01/tests/{_DATE}_submitted_orders.csv'
DIR_SAVE_FAKE_API_RQ = f'content/v0.01/tests/{_DATE}_Logs.csv'
DIR_HISTORIC_PRICES = 'content/v0.01/market-historic/active.csv'
DIR_SAVE_ORDER_ACTIONS = f'content/v0.01/tests/{_DATE}_Order_Actions.csv'
DIR_SAVE_MOVES = f'content/v0.01/tests/{_DATE}_moves.csv'
DIR_SAVE_CAPITAL = f'content/v0.01/tests/{_DATE}_capital.csv'
DIR_SAVE_MARKET = f'content/v0.01/tests/{_DATE}_market.csv'
