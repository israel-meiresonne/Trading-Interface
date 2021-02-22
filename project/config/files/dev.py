from datetime import datetime
# Variables
_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Directories
DIR_BROKERS = "model/API/brokers"
DIR_STRATEGIES = "model/structure/strategies"
# v0.01
DIR_SAVE_ORDER_RQ = f'content/v0.01/tests/{_DATE}_submitted_orders.csv'
DIR_SAVE_FAKE_API_RQ = f'content/v0.01/tests/{_DATE}_Logs.csv'
DIR_HISTORIC_PRICES = 'content/v0.01/BTC-USD.csv'
DIR_SAVE_ORDER_ACTIONS = f'content/v0.01/tests/{_DATE}_Order_Actions.csv'
