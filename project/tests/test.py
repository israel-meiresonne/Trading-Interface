import sys
def push_path() -> None:
    project_dir = '/Users/israelmeiresonne/MY-MAC/ROQUETS/companies/apollo21/dev/apollo21/dev/apollo21/project/'
    sys.path.append(project_dir) if project_dir not in sys.path else None

def dynamic_exec(class_name: str, test_func: str) -> None:
    imports = [
        f'from tests.API.brokers.Binance.{class_name} import {class_name}',
        f'from tests.structure.database.{class_name} import {class_name}',
        f'from tests.structure.strategies.{class_name} import {class_name}',
        f'from tests.tools.{class_name} import {class_name}'
    ]
    found = None
    i = 0
    while not found:
        try:
            exec(imports[i])
            break
        except Exception as e:
            i += 1
            if i >= len(imports):
                raise e
    test_obj = eval(f'{class_name}()')
    test_obj.setUp()
    exec(f'test_obj.{test_func}()')
    print('\033[32m')
    print(f"Test '{test_func}' of class '{class_name}' exceted!")
    print('\033[0m')

def run_Test(class_name: str, test_func: str = None) -> None:
    if class_name ==  'TestWallet':
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
    elif class_name ==  'TestOrder':
        a = []
    elif class_name ==  'TestPredictor':
        a = []
    elif class_name ==  'TestWebSocket':
        a = []
    elif class_name ==  'TestBinanceSocket':
        a = [
            'test_urls_url',
            'test_add_delete_streams',
            'test_add_new_streams',
            'test_add_delete_websocket',
            'test_set_get_market_history',
            'test_websocket_are_running',
            'test_new_websocket',
            'test_new_websockets',
            'test_can_update_market_history',
            'test_update_market_history',
            'test_manage_update_market_histories',
            'test_run_close',
            'test_surcharge_run',
            'test_check_stream',
            'test_generate_stream',
            'test_split_stream',
            'test_group_streams',
            'test_generate_url',
            'test_url_to_streams',
        ]
    elif test_func is not None:
        pass
    else:
        raise ValueError(f"Any test selected (class_name='{class_name}', test_func='{test_func}')")

    [dynamic_exec(class_name=class_name, test_func=func) for func in a] \
        if test_func is None else dynamic_exec(class_name=class_name, test_func=test_func)


if __name__ == '__main__':
    push_path()
    run_Test(class_name='TestPredictor', test_func='test_load_occupation_rate')
