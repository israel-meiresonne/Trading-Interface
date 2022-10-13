from config.Config import Config
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.HandTrade import HandTrade
from model.tools.Order import Order
from tests.tools.TestTrade import TestTrade


class TestHandTrade(TestTrade, HandTrade):
    def setUp(self) -> None:
        super().setUp()

    def buy_function(self) -> bool:
        return True

    def sell_function(self) -> bool:
        return True

    def test_set_buy_sell_function(self) -> None:
        buy_order = self.buy_order
        handtrade = HandTrade(buy_order, self.buy_function, self.sell_function)
        self.assertTrue(handtrade.get_buy_function(self)())
        self.assertTrue(handtrade.get_sell_function(self)())
        # Wrong function
        with self.assertRaises(ValueError):
            HandTrade(buy_order, buy_function='not_callable')
        with self.assertRaises(ValueError):
            HandTrade(buy_order, sell_function='not_callable')
    
    def test_json_encode_decode(self) -> None:
        broker = self.broker_switch(on=True, stage=Config.STAGE_2)
        buy_order = self.buy_order
        sell_order = self.sell_order
        period_1min = broker.PERIOD_1MIN
        handtrade = HandTrade(buy_order, self.buy_function, self.sell_function)
        buy_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 5*period_1min*1000)
        buy_order._set_status(Order.STATUS_COMPLETED)
        handtrade.set_sell_order(sell_order)
        sell_order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC) - 2*period_1min*1000)
        sell_order._set_status(Order.STATUS_COMPLETED)
        min_price3, max_price3 = handtrade.extrem_prices(broker).get_map().values()
        original_obj = handtrade
        test_exec = self.get_executable_test_json_encode_decode()
        exec(test_exec)
        # End
        self.broker_switch(on=False)


