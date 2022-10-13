import sys
from typing import Any, List
def push_path() -> None:
    project_dir = '/Users/israelmeiresonne/MY-MAC/ROQUETS/companies/apollo21/dev/apollo21/dev/apollo21/project/'
    sys.path.append(project_dir) if project_dir not in sys.path else None

def get_import(class_name: str) -> str:
    imports = [
        f'from tests.API.brokers.{class_name}.{class_name} import {class_name}',
        f'from tests.structure.database.{class_name} import {class_name}',
        f'from tests.structure.strategies.{class_name} import {class_name}',
        f'from tests.structure.strategies.' + class_name.replace('Test', '') + f'.{class_name} import {class_name}',
        f'from tests.tools.{class_name} import {class_name}'
    ]
    found = None
    i = 0
    while not found:
        try:
            exec(imports[i])
            break
        except ModuleNotFoundError as e:
            i += 1
            if i >= len(imports):
                raise e
    return imports[i]

def extract_tests(class_ref: Any) -> List[str]:
    from model.structure.database.ModelFeature import ModelFeature as _MF
    regex = r'^test_.*$'
    str_funcs = dir(class_ref)
    tests = [str_func for str_func in str_funcs if _MF.regex_match(regex, str_func)]
    if 'test_mode' in tests:
        del tests[tests.index('test_mode')]
    return tests

def dynamic_exec(class_ref: Any, str_func: str) -> None:
    test_obj = class_ref()
    test_obj.setUp()
    exec(f'test_obj.{str_func}()')
    test_obj.tearDown()
    print('\033[32m')
    print(f"Test '{str_func}' of class '{class_ref.__name__}' exceted!")
    print('\033[0m')

def run_Test(class_name: str, str_func: str = None) -> None:
    exec(get_import(class_name))
    class_ref = eval(class_name)
    str_funcs = extract_tests(class_ref)
    if str_func is None:
        [dynamic_exec(class_ref, str_func) for str_func in str_funcs]
    else:
        dynamic_exec(class_ref, str_func)


if __name__ == '__main__':
    push_path()
    run_Test(class_name='', str_func='')
