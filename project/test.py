
def dynamic_exec(class_name: str, test_func: str) -> None:
    exec(f'from tests.tools.{class_name} import {class_name}')
    test_obj = eval(f'{class_name}()')
    test_obj.setUp()
    exec(f'test_obj.{test_func}()')
    print('\033[32m')
    print(f"Test '{test_func}' of class '{class_name}' exceted!")
    print('\033[0m')


# dynamic_exec(class_name='TestDeepLearning', test_func='test_save')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_predict')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_perso')
# dynamic_exec(class_name='TestDeepLearning', test_func='test_offset_mean')

# dynamic_exec(class_name='TestPredictor', test_func='test_learn')
dynamic_exec(class_name='TestPredictor', test_func='test_predict')
# dynamic_exec(class_name='TestPredictor', test_func='test_add_learns')
# dynamic_exec(class_name='TestPredictor', test_func='resume_learn')
# dynamic_exec(class_name='TestPredictor', test_func='test_market_price_to_np')
