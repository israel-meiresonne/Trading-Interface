import sys
def push_path() -> None:
    project_dir = '/Users/israelmeiresonne/MY-MAC/ROQUETS/companies/apollo21/dev/apollo21/dev/apollo21/project/'
    sys.path.append(project_dir) if project_dir not in sys.path else None

def dynamic_exec(class_name: str, test_func: str) -> None:
    exec(f'from tests.tools.{class_name} import {class_name}')
    # exec(f'from tests.structure.database.{class_name} import {class_name}')
    test_obj = eval(f'{class_name}()')
    test_obj.setUp()
    exec(f'test_obj.{test_func}()')
    print('\033[32m')
    print(f"Test '{test_func}' of class '{class_name}' exceted!")
    print('\033[0m')

push_path()
# dynamic_exec(class_name='TestDeepLearning', test_func='test_save')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_predict')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_perso')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_offset_mean')

# dynamic_exec(class_name='TestPredictor', test_func='test_market_history_pairs')
# dynamic_exec(class_name='TestPredictor', test_func='test_predict')
# dynamic_exec(class_name='TestPredictor', test_func='test_add_learns')
# dynamic_exec(class_name='TestPredictor', test_func='resume_learn')

# dynamic_exec(class_name='TestModelFeature', test_func='test_df_apply')

a = [
    'test_set_initial',
    'test_get_position_value',
    'test_get_marketprice',
    'test_deposit',
    'test_withdraw',
    'test_buy',
    'test_sell',
    'test_add_position',
    'test_remove_position',
    'test_multiple_transaction',
    'test_json_encode_decode'
]
[dynamic_exec(class_name='TestWallet', test_func=func) for func in a]
# dynamic_exec(class_name='TestWallet', test_func='test_json_encode_decode')

