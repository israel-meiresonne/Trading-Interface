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
    elif test_func is not None:
        pass
    else:
        raise ValueError(f"Any test selected (class_name='{class_name}', test_func='{test_func}')")

    [dynamic_exec(class_name=class_name, test_func=func) for func in a] \
        if test_func is None else dynamic_exec(class_name=class_name, test_func=test_func)


if __name__ == '__main__':
    push_path()
    run_Test(class_name='TestPredictor', test_func='test_get_learn_path')
