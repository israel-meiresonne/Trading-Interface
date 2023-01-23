import unittest
from config.Config import Config

from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
from model.API.brokers.Binance.BinanceFakeOrder import BinanceFakeOrder
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class TestBinanceFakeOrder(unittest.TestCase, BinanceFakeOrder):
    N_SETUP = 0
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        _MF.update_bot_trade_index(0)
        self.pair = pair = Pair('BTC/USDT')
        if self.N_SETUP == 0:
            self.N_SETUP += 1
            Config.update(Config.STAGE_MODE, Config.STAGE_1)
            fake_api_times = {
                Map.start:  1671062400, # 2022-12-15 0:00:00
                Map.end:    1672531200  # 2023-01-01 0:00:00
                }
            Config.update(Config.FAKE_API_START_END_TIME, fake_api_times)
            broker_params = Map({
                Map.public:     'xxx',
                Map.secret:     'yyy',
                Map.test_mode:  False
            })
            self.broker = broker = Broker.retrieve('Binance', broker_params)
            stream = broker.generate_stream(Map({Map.pair: pair, Map.period: Broker.PERIOD_1MIN}))
            broker.add_streams([stream])
        self.stop = stop = Price(30000, pair.get_right())
        self.price = price = Price(45000, pair.get_right())
        self.quantity = quantity = Price(10, pair.get_left())
        self.binance_order = binance_order = BinanceOrder(BinanceOrder.TYPE_STOP_LIMIT, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_BUY,
            Map.stop: stop,
            Map.limit: price,
            Map.quantity: quantity
        }))
        self.params = params = binance_order.generate_order()
        self.market_datas, self.market_data_history = market_datas, market_data_history = BinanceFakeAPI._actual_market_datas(pair.format(Pair.FORMAT_MERGED))
        self.fake_order = BinanceFakeOrder(params, market_datas)
        self.attribut_types = {
            Map.symbol: str,
            Map.type: str,
            Map.side: str,
            Map.status: str,
            Map.orderId: int,
            Map.clientOrderId: str,
            Map.origClientOrderId: (str, type(None)),
            Map.orderListId: int,
            Map.price: (int, float, type(None)),
            Map.stopPrice: (int, float, type(None)),
            Map.origQty: (int, float, type(None)),
            Map.icebergQty: (int, float, type(None)),
            Map.executedQty: (int, float, type(None)),
            Map.cummulativeQuoteQty: (int, float, type(None)),
            Map.timeInForce: (str, type(None)),
            Map.time: int,
            'isWorking': type(None),
            Map.updateTime: int,
            Map.transactTime: (int, type(None)),
            Map.fills: (list, type(None))
        }

    def to_executed_state(self, order: BinanceFakeOrder, executed: BinanceFakeOrder, params: Map, initial_market_datas: Map, exec_datas: dict) -> None:
        if id(order) == id(executed):
            raise ValueError("Order instance must be different")
        symbol = exec_datas[Map.symbol]
        exec_amount = exec_datas[Map.amount]
        exec_quantity = exec_datas[Map.quantity]
        exec_price = exec_datas[Map.execution]
        fee = exec_datas[Map.fee]
        side = exec_datas[Map.side]
        if not isinstance(fee, Price):
            raise TypeError(f"Fee must be of type '{Price}', instead '{type(fee)}'")
        if side == BinanceAPI.SIDE_BUY:
            isBuyer = True
        elif side == BinanceAPI.SIDE_SELL:
            isBuyer = False
        order._set_attribut(Map.symbol, symbol)
        order._set_attribut(Map.type, exec_datas[Map.type])
        order._set_attribut(Map.side, side)
        order._set_attribut(Map.status, BinanceAPI.STATUS_ORDER_FILLED)
        order._set_attribut(Map.orderId, executed.get_attribut(Map.orderId))
        order._set_attribut(Map.clientOrderId, params.get(Map.newClientOrderId))
        order._set_attribut(Map.origClientOrderId, None)
        order._set_attribut(Map.orderListId, -1)
        order._set_attribut(Map.price, exec_datas[Map.price])
        order._set_attribut(Map.stopPrice, exec_datas[Map.stopPrice])
        order._set_attribut(Map.origQty, exec_quantity)
        order._set_attribut(Map.icebergQty, None)
        order._set_attribut(Map.executedQty, exec_quantity)
        order._set_attribut(Map.cummulativeQuoteQty, exec_amount)
        order._set_attribut(Map.timeInForce, params.get(Map.timeInForce))
        order._set_attribut(Map.time, executed.get_attribut(Map.time))
        order._set_attribut(Map.isWorking, None)
        order._set_attribut(Map.updateTime, executed.get_attribut(Map.updateTime))
        order._set_attribut(Map.transactTime, executed.get_attribut(Map.transactTime))
        order._set_attribut(Map.ready, True)
        order._set_attribut(Map.submit, initial_market_datas.get_map()[Map.close])
        order._set_attribut(Map.param, params)
        order._set_attribut(Map.market, initial_market_datas)
        fills = []
        order._set_attribut(Map.fills, fills)
        fills.append({
            Map.symbol: symbol,
            Map.id: executed.get_attribut(Map.fills)[0][Map.id],
            Map.orderId: executed.get_attribut(Map.orderId),
            Map.tradeId: executed.get_attribut(Map.fills)[0][Map.id],
            Map.orderListId: -1,
            Map.price: exec_price,
            Map.qty: exec_quantity,
            Map.commission: fee.get_value(),
            Map.commissionAsset: fee.get_asset().__str__().upper(),
            Map.quoteQty: exec_amount,
            Map.time: executed.get_attribut(Map.fills)[0][Map.time],
            Map.isBuyer: isBuyer,
            Map.isMaker: exec_datas[Map.isMaker],
            Map.isBestMatch: None
            })

    def compare_order_execution(self, exp: BinanceFakeOrder, result: BinanceFakeOrder, attribut_types: dict) -> None:
        def test_types(attribut_to_values: dict, attribut_types: dict) -> None:
            for attribut, types in attribut_types.items():
                if not isinstance(types, dict):
                    self.assertIsInstance(attribut_to_values[attribut], types)
                else:
                    test_types(attribut_to_values[attribut][0], types)

        attributs = [*exp.attribut_to_values().keys(), *result.attribut_to_values().keys()]
        [self.assertEqual(exp.get_attribut(attribut), result.get_attribut(attribut)) for attribut in attributs]
        test_types(result.attribut_to_values(), attribut_types)

    def test_constructor(self) -> None:
        attribut_types = self.attribut_types
        params = self.params
        market_datas = self.market_datas
        order = BinanceFakeOrder(params, market_datas)
        [self.assertIsInstance(order.get_attribut(attribut), types) for attribut, types in attribut_types.items()]
        self.assertEqual(params, order.get_attribut(Map.param))
        self.assertEqual(market_datas, order.get_attribut(Map.market))

    def test_try_execute(self) -> None:
        from model.API.brokers.Binance.BinanceFakeAPI import BinanceFakeAPI
        pair = Pair('BTC/USDT')
        quantity_obj = Price(7, pair.get_left())
        amount_obj = Price(3, pair.get_right())
        fees_rates = BinanceFakeAPI.get_trade_fee(pair)
        attribut_types = {
            Map.orderId: int,
            Map.time: int,
            Map.transactTime: int,
            Map.fills: {
                Map.id: int,
                Map.orderId: int,
                Map.tradeId: int,
                Map.time: int
            }
        }
        attribut_types_unexecuted = {
            Map.orderId: int,
            Map.time: int,
            Map.transactTime: type(None),
            Map.fills: type(None)
        }
        self.__try_execute_market(pair, quantity_obj, amount_obj, fees_rates, attribut_types, attribut_types_unexecuted)
        self.__try_execute_stop_loss(pair, quantity_obj, amount_obj, fees_rates, attribut_types, attribut_types_unexecuted)
        self.__try_execute_limit(pair, quantity_obj, amount_obj, fees_rates, attribut_types, attribut_types_unexecuted)
        self.__try_execute_stop_limit(pair, quantity_obj, amount_obj, fees_rates, attribut_types, attribut_types_unexecuted)

    def __try_execute_market(self, pair: Pair, quantity_obj: Price, amount_obj: Price, fees_rates: Map, attribut_types: dict, attribut_types_unexecuted: dict) -> None:
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        exec_quantity = quantity_obj.get_value()
        exec_amount = amount_obj.get_value()
        market_datas = self.market_datas
        market_data_history = self.market_data_history
        param_buy_market_quantity = BinanceOrder(BinanceOrder.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_BUY,
            Map.quantity: quantity_obj
        })).generate_order()
        param_buy_market_amount = BinanceOrder(BinanceOrder.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_BUY,
            Map.amount: amount_obj
        })).generate_order()
        param_sell_market_quantity = BinanceOrder(BinanceOrder.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_SELL,
            Map.quantity: quantity_obj
        })).generate_order()
        param_sell_market_amount = BinanceOrder(BinanceOrder.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_SELL,
            Map.amount: amount_obj
        })).generate_order()
        '''
        # Test buy_market_quantity
        '''
        order_buy_market_quantity = BinanceFakeOrder(param_buy_market_quantity, market_datas)
        exp1 = order_buy_market_quantity.copy()
        self.assertTrue(order_buy_market_quantity.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp1, order_buy_market_quantity, param_buy_market_quantity, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       BinanceAPI.TYPE_MARKET,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  market_datas.get(Map.close),
            Map.price:      None,
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*market_datas.get(Map.close),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp1, result=order_buy_market_quantity, attribut_types=attribut_types)
        '''
        # Test buy_market_amount
        '''
        order_buy_market_amount = BinanceFakeOrder(param_buy_market_amount, market_datas)
        exp2 = order_buy_market_amount.copy()
        self.assertTrue(order_buy_market_amount.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp2, order_buy_market_amount, param_buy_market_amount, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       BinanceAPI.TYPE_MARKET,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  market_datas.get(Map.close),
            Map.price:      None,
            Map.stopPrice:  None,
            Map.amount:     exec_amount,
            Map.quantity:   exec_amount/market_datas.get(Map.close),
            Map.fee:        Price((exec_amount/market_datas.get(Map.close))*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp2, result=order_buy_market_amount, attribut_types=attribut_types)
        '''
        # Test sell_market_quantity
        '''
        order_sell_market_quantity = BinanceFakeOrder(param_sell_market_quantity, market_datas)
        exp3 = order_sell_market_quantity.copy()
        self.assertTrue(order_sell_market_quantity.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp3, order_sell_market_quantity, param_sell_market_quantity, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       BinanceAPI.TYPE_MARKET,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  market_datas.get(Map.close),
            Map.price:      None,
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*market_datas.get(Map.close),
            Map.quantity:   exec_quantity,
            Map.fee:        Price((exec_quantity*market_datas.get(Map.close))*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp3, result=order_sell_market_quantity, attribut_types=attribut_types)
        '''
        # Test sell_market_amount
        '''
        order_sell_market_amount = BinanceFakeOrder(param_sell_market_amount, market_datas)
        exp4 = order_sell_market_amount.copy()
        self.assertTrue(order_sell_market_amount.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp4, order_sell_market_amount, param_sell_market_amount, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       BinanceAPI.TYPE_MARKET,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  market_datas.get(Map.close),
            Map.price:      None,
            Map.stopPrice:  None,
            Map.amount:     exec_amount,
            Map.quantity:   exec_amount/market_datas.get(Map.close),
            Map.fee:        Price(exec_amount*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp4, result=order_sell_market_amount, attribut_types=attribut_types)

    def __try_execute_stop_loss(self, pair: Pair, quantity_obj: Price, amount_obj: Price, fees_rates: Map, attribut_types: dict, attribut_types_unexecuted: dict) -> None:
        def new_request_params(pair: Pair, side: str, stop: Price, quantity) -> Map:
            request_params = BinanceOrder(BinanceOrder.TYPE_STOP, Map({
                Map.pair:       pair,
                Map.move:       side,
                Map.stop:       stop,
                Map.quantity:   quantity
                })).generate_order()
            return request_params
        r_asset = pair.get_right()
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        exec_quantity = quantity_obj.get_value()
        order_type = BinanceAPI.TYPE_STOP_LOSS
        market_data_history = self.market_data_history
        market_datas = self.market_datas
        market_datas_close = market_datas.get(Map.close)
        stop_price_obj = Price(market_datas_close, r_asset)
        '''
        BUY close > stop
        '''
        stop_price_obj1 = Price(stop_price_obj/2, r_asset)
        stop_price_obj_fixed1 = BinanceAPI.fixe_price(pair, stop_price_obj1)
        rq_params1 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop_price_obj1, quantity_obj)
        order1 = BinanceFakeOrder(rq_params1, market_datas)
        exp1 = order1.copy()
        self.assertTrue(order1.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp1, order1, rq_params1, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  market_datas_close,
            Map.price:      None,
            Map.stopPrice:  stop_price_obj_fixed1.get_value(),
            Map.amount:     exec_quantity*market_datas_close,
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp1, result=order1, attribut_types=attribut_types)
        '''
        BUY close == stop
        '''
        stop_price_obj2 = stop_price_obj
        stop_price_obj_fixed2 = BinanceAPI.fixe_price(pair, stop_price_obj2)
        rq_params2 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop_price_obj2, quantity_obj)
        order2 = BinanceFakeOrder(rq_params2, market_datas)
        exp2 = order2.copy()
        self.assertTrue(order2.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp2, order2, rq_params2, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  market_datas_close,
            Map.price:      None,
            Map.stopPrice:  stop_price_obj_fixed2.get_value(),
            Map.amount:     exec_quantity*market_datas_close,
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp2, result=order2, attribut_types=attribut_types)
        '''
        BUY close < stop
        '''
        stop_price_obj3 = Price(stop_price_obj*2, r_asset)
        rq_params3 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop_price_obj3, quantity_obj)
        order3 = BinanceFakeOrder(rq_params3, market_datas)
        exp3 = order3.copy()
        self.assertFalse(order3.try_execute(market_datas, market_data_history))
        self.compare_order_execution(exp=exp3, result=order3, attribut_types=attribut_types_unexecuted)
        '''
        SELL close > stop
        '''
        stop_price_obj4 = Price(stop_price_obj/2, r_asset)
        rq_params4 = new_request_params(pair, BinanceOrder.MOVE_SELL, stop_price_obj4, quantity_obj)
        order4 = BinanceFakeOrder(rq_params4, market_datas)
        exp4 = order4.copy()
        self.assertFalse(order4.try_execute(market_datas, market_data_history))
        self.compare_order_execution(exp=exp4, result=order4, attribut_types=attribut_types_unexecuted)
        '''
        SELL close == stop
        '''
        # market_datas5 = market_datas.copy()
        # market_datas5.put(stop_price_obj.get_value(), Map.close)
        stop_price_obj5 = stop_price_obj
        stop_price_obj_fixed5 = BinanceAPI.fixe_price(pair, stop_price_obj5)
        rq_params5 = new_request_params(pair, BinanceOrder.MOVE_SELL, stop_price_obj5, quantity_obj)
        order5 = BinanceFakeOrder(rq_params5, market_datas)
        exp5 = order5.copy()
        self.assertTrue(order5.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp5, order5, rq_params5, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  market_datas_close,
            Map.price:      None,
            Map.stopPrice:  stop_price_obj_fixed5.get_value(),
            Map.amount:     exec_quantity*market_datas_close,
            Map.quantity:   exec_quantity,
            Map.fee:        Price((exec_quantity*market_datas_close)*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp5, result=order5, attribut_types=attribut_types)
        '''
        SELL close < stop
        '''
        # market_datas6 = market_datas.copy()
        # market_datas6.put(stop_price_obj.get_value()/2, Map.close)
        stop_price_obj6 = Price(stop_price_obj*2, r_asset)
        stop_price_obj_fixed6 = BinanceAPI.fixe_price(pair, stop_price_obj6)
        rq_params6 = new_request_params(pair, BinanceOrder.MOVE_SELL, stop_price_obj6, quantity_obj)
        order6 = BinanceFakeOrder(rq_params6, market_datas)
        exp6 = order6.copy()
        self.assertTrue(order6.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp6, order6, rq_params6, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  market_datas_close,
            Map.price:      None,
            Map.stopPrice:  stop_price_obj_fixed6.get_value(),
            Map.amount:     exec_quantity*market_datas_close,
            Map.quantity:   exec_quantity,
            Map.fee:        Price((exec_quantity*market_datas_close)*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    False
        })
        self.compare_order_execution(exp=exp6, result=order6, attribut_types=attribut_types)

    def __try_execute_limit(self, pair: Pair, quantity_obj: Price, amount_obj: Price, fees_rates: Map, attribut_types: dict, attribut_types_unexecuted: dict) -> None:
        def new_request_params(pair: Pair, side: str, limit: Price, quantity) -> Map:
            request_params = BinanceOrder(BinanceOrder.TYPE_LIMIT, Map({
                Map.pair:       pair,
                Map.move:       side,
                Map.limit:      limit,
                Map.quantity:   quantity
                })).generate_order()
            return request_params
        r_asset = pair.get_right()
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        exec_quantity = quantity_obj.get_value()
        order_type = BinanceAPI.TYPE_LIMIT
        market_datas = self.market_datas
        market_data_history = self.market_data_history
        market_datas_close = market_datas.get(Map.close)
        limit_price_obj = Price(market_datas_close, r_asset)
        '''
        BUY close > limit
        '''
        limit_price_obj1 = Price(limit_price_obj/2, r_asset)
        rq_params1 = new_request_params(pair, BinanceOrder.MOVE_BUY, limit_price_obj1, quantity_obj)
        order1 = BinanceFakeOrder(rq_params1, market_datas)
        exp1 = order1.copy()
        self.assertFalse(order1.try_execute(market_datas, market_data_history))
        self.compare_order_execution(exp=exp1, result=order1, attribut_types=attribut_types_unexecuted)
        '''
        BUY close == limit
        '''
        limit_price_obj2 = limit_price_obj
        rq_params2 = new_request_params(pair, BinanceOrder.MOVE_BUY, limit_price_obj2, quantity_obj)
        order2 = BinanceFakeOrder(rq_params2, market_datas)
        exp2 = order2.copy()
        self.assertTrue(order2.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp2, order2, rq_params2, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_price_obj2.get_value(),
            Map.price:      limit_price_obj2.get_value(),
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*limit_price_obj2.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp2, result=order2, attribut_types=attribut_types)
        '''
        BUY exec_close < limit
        '''
        limit_price_obj3 = Price(limit_price_obj*2, r_asset)
        limit_price_obj_fixed3 = BinanceAPI.fixe_price(pair, limit_price_obj3)
        rq_params3 = new_request_params(pair, BinanceOrder.MOVE_BUY, limit_price_obj3, quantity_obj)
        order3 = BinanceFakeOrder(rq_params3, market_datas)
        exp3 = order3.copy()
        self.assertTrue(order3.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp3, order3, rq_params3, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_price_obj_fixed3.get_value(),
            Map.price:      limit_price_obj_fixed3.get_value(),
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*limit_price_obj_fixed3.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp3, result=order3, attribut_types=attribut_types)
        '''
        SELL close > limit
        '''
        limit_price_obj4 = Price(limit_price_obj/2, r_asset)
        limit_price_obj_fixed4 = BinanceAPI.fixe_price(pair, limit_price_obj4)
        rq_params4 = new_request_params(pair, BinanceOrder.MOVE_SELL, limit_price_obj4, quantity_obj)
        order4 = BinanceFakeOrder(rq_params4, market_datas)
        exp4 = order4.copy()
        self.assertTrue(order4.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp4, order4, rq_params4, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  limit_price_obj_fixed4.get_value(),
            Map.price:      limit_price_obj_fixed4.get_value(),
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*limit_price_obj_fixed4.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price((exec_quantity*limit_price_obj_fixed4.get_value())*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp4, result=order4, attribut_types=attribut_types)
        '''
        SELL close == limit
        '''
        limit_price_obj5 = limit_price_obj
        limit_price_obj_fixed5 = BinanceAPI.fixe_price(pair, limit_price_obj5)
        rq_params5 = new_request_params(pair, BinanceOrder.MOVE_SELL, limit_price_obj5, quantity_obj)
        order5 = BinanceFakeOrder(rq_params5, market_datas)
        exp5 = order5.copy()
        self.assertTrue(order5.try_execute(market_datas, market_data_history))
        self.to_executed_state(exp5, order5, rq_params5, market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_SELL,
            Map.execution:  limit_price_obj_fixed5.get_value(),
            Map.price:      limit_price_obj_fixed5.get_value(),
            Map.stopPrice:  None,
            Map.amount:     exec_quantity*limit_price_obj_fixed5.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price((exec_quantity*limit_price_obj_fixed5.get_value())*fees_rates.get(Map.taker), pair.get_right()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp5, result=order5, attribut_types=attribut_types)
        '''
        SELL exec_close < limit
        '''
        limit_price_obj6 = Price(limit_price_obj*2, r_asset)
        rq_params6 = new_request_params(pair, BinanceOrder.MOVE_SELL, limit_price_obj6, quantity_obj)
        order6 = BinanceFakeOrder(rq_params6, market_datas)
        exp6 = order6.copy()
        self.assertFalse(order6.try_execute(market_datas, market_data_history))
        self.compare_order_execution(exp=exp6, result=order6, attribut_types=attribut_types_unexecuted)

    def __try_execute_stop_limit(self, pair: Pair, quantity_obj: Price, amount_obj: Price, fees_rates: Map, attribut_types: dict, attribut_types_unexecuted: dict) -> None:
        def new_request_params(pair: Pair, side: str, stop: Price, limit: Price, quantity) -> Map:
            request_params = BinanceOrder(BinanceOrder.TYPE_STOP_LIMIT, Map({
                Map.pair:       pair,
                Map.move:       side,
                Map.stop:       stop,
                Map.limit:      limit,
                Map.quantity:   quantity
                })).generate_order()
            return request_params
        def fixe_price(price: Price) -> Price:
            return BinanceAPI.fixe_price(pair, price)
        def price_and_fixed(price_value: float) -> tuple[Price, Price]:
            price = Price(price_value, r_asset)
            price_fixed = fixe_price(price)
            return price, price_fixed
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        r_asset = pair.get_right()
        order_type = BinanceAPI.TYPE_STOP_LOSS_LIMIT
        # Market datas
        _MF.update_bot_trade_index(0)
        submit_market_datas, submit_market_data_history = BinanceFakeAPI._actual_market_datas(merged_pair)
        _MF.update_bot_trade_index(16)
        exec_market_datas_16, exec_market_data_history_16 = BinanceFakeAPI._actual_market_datas(merged_pair)
        _MF.update_bot_trade_index(2860)
        exec_market_datas, exec_market_data_history = BinanceFakeAPI._actual_market_datas(merged_pair)
        # Prices
        exec_quantity = quantity_obj.get_value()
        submit_market_datas_close = submit_market_datas.get(Map.close)
        exec_market_datas_close = exec_market_datas.get(Map.close)
        exec_market_datas_close_16 = exec_market_datas_16.get(Map.close)
        # 2860
        min_close =     min([submit_market_datas_close, exec_market_datas_close])
        mean_close =    (submit_market_datas_close + exec_market_datas_close) / 2
        max_close =     max([submit_market_datas_close, exec_market_datas_close])
        # 16
        min_close_16 =  min([submit_market_datas_close, exec_market_datas_close_16])
        mean_close_16 = (submit_market_datas_close + exec_market_datas_close_16) / 2
        max_close_16 =  max([submit_market_datas_close, exec_market_datas_close_16])
        '''
        BUY FROM (submit_close > stop) TO (exec_close > stop) AND (exec_close < limit)
        submit_close > stop < exec_close
        '''
        stop_obj1,  stop_obj_fixed1 =   price_and_fixed(min_close/2)
        limit_obj1, limit_obj_fixed1 =  price_and_fixed(exec_market_datas_close * 2)
        rq_params1 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj1, limit=limit_obj1, quantity=quantity_obj)
        order1 = BinanceFakeOrder(rq_params1, submit_market_datas)
        exp1_1 = order1.copy()
        self.assertFalse(order1.try_execute(exec_market_datas, exec_market_data_history))
        self.compare_order_execution(exp=exp1_1, result=order1, attribut_types=attribut_types_unexecuted)
        '''
        BUY FROM (submit_close > stop) TO (exec_close == stop) AND (exec_close < limit)
        submit_close > stop == exec_close
        '''
        stop_obj2,  stop_obj_fixed2 =   price_and_fixed(exec_market_datas_close)
        limit_obj2, limit_obj_fixed2 =  price_and_fixed(exec_market_datas_close * 2)
        rq_params2 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj2, limit=limit_obj2, quantity=quantity_obj)
        order2 = BinanceFakeOrder(rq_params2, submit_market_datas)
        exp2 = order2.copy()
        self.assertTrue(order2.try_execute(exec_market_datas, exec_market_data_history))
        self.to_executed_state(exp2, order2, rq_params2, submit_market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_obj_fixed2.get_value(),
            Map.price:      limit_obj_fixed2.get_value(),
            Map.stopPrice:  stop_obj_fixed2.get_value(),
            Map.amount:     exec_quantity*limit_obj_fixed2.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp2, result=order2, attribut_types=attribut_types)
        '''
        BUY FROM (submit_close > stop) TO (exec_close < stop) AND (exec_close < limit)
        submit_close > stop > exec_close
        '''
        stop_obj3,  stop_obj_fixed3 =   price_and_fixed(mean_close)
        limit_obj3, limit_obj_fixed3 =  price_and_fixed(exec_market_datas_close * 2)
        rq_params3 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj3, limit=limit_obj3, quantity=quantity_obj)
        order3 = BinanceFakeOrder(rq_params3, submit_market_datas)
        exp3 = order3.copy()
        self.assertTrue(order3.try_execute(exec_market_datas, exec_market_data_history))
        self.to_executed_state(exp3, order3, rq_params3, submit_market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_obj_fixed3.get_value(),
            Map.price:      limit_obj_fixed3.get_value(),
            Map.stopPrice:  stop_obj_fixed3.get_value(),
            Map.amount:     exec_quantity*limit_obj_fixed3.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp3, result=order3, attribut_types=attribut_types)
        '''
        BUY FROM (submit_close < stop) TO (exec_close < stop) AND (exec_close < limit)
        submit_close < stop > exec_close
        '''
        stop_obj4,  stop_obj_fixed4 =   price_and_fixed(max_close * 2)
        limit_obj4, limit_obj_fixed4 =  price_and_fixed(exec_market_datas_close * 2)
        rq_params4 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj4, limit=limit_obj4, quantity=quantity_obj)
        order4 = BinanceFakeOrder(rq_params4, submit_market_datas)
        exp4 = order4.copy()
        self.assertFalse(order4.try_execute(exec_market_datas, exec_market_data_history))
        self.compare_order_execution(exp=exp4, result=order4, attribut_types=attribut_types_unexecuted)
        '''
        BUY FROM (submit_close < stop) TO (exec_close == stop) AND (exec_close < limit)
        submit_close < stop == exec_close
        '''
        stop_obj5,  stop_obj_fixed5 =   price_and_fixed(exec_market_datas_close_16)
        limit_obj5, limit_obj_fixed5 =  price_and_fixed(exec_market_datas_close_16 * 2)
        rq_params5 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj5, limit=limit_obj5, quantity=quantity_obj)
        order5 = BinanceFakeOrder(rq_params5, submit_market_datas)
        exp5 = order5.copy()
        self.assertTrue(order5.try_execute(exec_market_datas_16, exec_market_data_history_16))
        self.to_executed_state(exp5, order5, rq_params5, submit_market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_obj_fixed5.get_value(),
            Map.price:      limit_obj_fixed5.get_value(),
            Map.stopPrice:  stop_obj_fixed5.get_value(),
            Map.amount:     exec_quantity*limit_obj_fixed5.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp5, result=order5, attribut_types=attribut_types)
        '''
        BUY FROM (submit_close < stop) TO (exec_close > stop) AND (exec_close < limit)
        submit_close < stop < exec_close
        '''
        stop_obj6,  stop_obj_fixed6 =   price_and_fixed(mean_close_16)
        limit_obj6, limit_obj_fixed6 =  price_and_fixed(exec_market_datas_close_16 * 2)
        rq_params6 = new_request_params(pair, BinanceOrder.MOVE_BUY, stop=stop_obj6, limit=limit_obj6, quantity=quantity_obj)
        order6 = BinanceFakeOrder(rq_params6, submit_market_datas)
        exp6 = order6.copy()
        self.assertTrue(order6.try_execute(exec_market_datas_16, exec_market_data_history_16))
        self.to_executed_state(exp6, order6, rq_params6, submit_market_datas, exec_datas={
            Map.symbol:     merged_pair,
            Map.type:       order_type,
            Map.side:       BinanceAPI.SIDE_BUY,
            Map.execution:  limit_obj_fixed6.get_value(),
            Map.price:      limit_obj_fixed6.get_value(),
            Map.stopPrice:  stop_obj_fixed6.get_value(),
            Map.amount:     exec_quantity*limit_obj_fixed6.get_value(),
            Map.quantity:   exec_quantity,
            Map.fee:        Price(exec_quantity*fees_rates.get(Map.taker), pair.get_left()),
            Map.isMaker:    True
        })
        self.compare_order_execution(exp=exp6, result=order6, attribut_types=attribut_types)

    def test_cancel(self) -> None:
        pair = Pair('BTC/USDT')
        merged_pair = pair.format(Pair.FORMAT_MERGED).upper()
        quantity_obj = self.quantity
        limit_price_obj = self.price
        stop_price_obj = self.stop
        market_datas = self.market_datas
        sys_order = self.binance_order
        fake_order = BinanceFakeOrder(sys_order.generate_order(), market_datas)
        jump_keys = [Map.clientOrderId]
        exp = {
            Map.symbol: merged_pair,
            Map.origClientOrderId: sys_order.get_id(),
            Map.orderId: fake_order.get_attribut(Map.orderId),
            Map.orderListId: -1,
            Map.clientOrderId: "xbGwPz3fflNeiQW7uUbh2r",
            Map.price: limit_price_obj.get_value(),
            Map.origQty: quantity_obj.get_value(),
            Map.executedQty: 0,
            Map.cummulativeQuoteQty: 0,
            Map.status: BinanceAPI.STATUS_ORDER_CANCELED,
            Map.timeInForce: "GTC",
            Map.type: BinanceAPI.TYPE_STOP_LOSS_LIMIT,
            Map.side: BinanceAPI.SIDE_BUY,
            Map.stopPrice: stop_price_obj.get_value()
        }
        result = fake_order.cancel()
        [self.assertEqual(value, result[attribut]) for attribut, value in exp.items() if attribut not in jump_keys]

    def test_to_dict(self) -> None:
        pair = Pair('BTC/USDT')
        order = self.fake_order
        attribut_types = self.attribut_types
        api_order = order.to_dict()
        exp1 = 0
        for api_attribut in attribut_types.keys():
            del api_order[api_attribut]
        result1 = len(api_order)
        self.assertEqual(exp1, result1)
        # Exected order
        self.setUp()
        market_datas = self.market_datas
        market_data_history = self.market_data_history
        params = BinanceOrder(BinanceOrder.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: BinanceOrder.MOVE_BUY,
            Map.quantity: Price(5, pair.get_left())
        })).generate_order()
        order = BinanceFakeOrder(params, market_datas)
        order.try_execute(market_datas, market_data_history)
        api_order = order.to_dict()
        attribut_types[Map.fills] = list
        [self.assertIsInstance(api_order[attribut], types) for attribut, types in attribut_types.items()]

    def test_json_instantiate(self) -> None:
        order = self.fake_order
        str_json = order.json_encode()
        json_obj = MyJson.json_decode(str_json)
        self.assertIsInstance(json_obj, BinanceFakeOrder)
        self.assertNotEqual(id(order), id(json_obj))
        self.assertEqual(order, json_obj)
