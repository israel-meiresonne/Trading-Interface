import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class TestOrder(unittest.TestCase, Order):
    def setUp(self) -> None:
        # _initial_stage = Config.get(Config.STAGE_MODE)
        # Config.update(Config.STAGE_MODE, Config.STAGE_1)
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        self.pr = Pair(self.lsbl, self.rsbl)
        self.exec_prc0 = Price(15000, self.rsbl)
        self.exec_prc1 = Price(20000, self.rsbl)
        self.odr0_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: Price(1000, self.rsbl)
        })
        self.odr1_prms = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.quantity: Price(1/15, self.lsbl)
        })
        self.odr0 = BinanceOrder(self.TYPE_MARKET, self.odr0_prms)
        self.odr1 = BinanceOrder(self.TYPE_MARKET, self.odr1_prms)
        self.odrs = Map({
            "0": self.odr0,
            "1": self.odr1
        })
        self.init_stage = None
        self.bkr = None
    
    def tearDown(self) -> None:
        self.broker_switch(False)
    
    INIT_STAGE = None
    BROKER = None

    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.INIT_STAGE = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
            self.BROKER = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.INIT_STAGE
            self.BROKER.close() if self.BROKER is not None else None
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self.BROKER

    @staticmethod
    def execute(order: Order, exec_price: Price, amount: Price = None, quantity: Price = None, fee_rate: float = 1/100) -> None:
        if (amount is None) and (quantity is None):
            raise ValueError("amount and quantity can't both be None")
        if (not isinstance(amount, Price)) and (not isinstance(quantity, Price)):
            raise ValueError("amount and quantity can't both set")
        pair = order.get_pair()
        if amount is not None:
            quantity = Price(amount/exec_price, pair.get_left())
        else:
            amount = Price(quantity * exec_price, pair.get_right())
        fee = Price(amount * fee_rate, pair.get_right())
        order._set_status(Order.STATUS_COMPLETED)
        order._set_broker_id(_MF.new_code())
        order._set_execution_time(_MF.get_timestamp(unit=_MF.TIME_MILLISEC))
        order._set_execution_price(exec_price)
        order._set_fee(fee)
        order._set_executed_amount(amount)
        order._set_executed_quantity(quantity)
    
    def _set_market(self) -> None:
        pass

    def _set_limit(self) -> None:
        pass

    def _set_stop(self) -> None:
        pass

    def _set_stop_limit(self) -> None:
        pass

    def generate_order(self) -> Map:
        pass

    def generate_cancel_order(self) -> Map:
        pass

    def test_check_market(self) -> None:
        raise Exception("Must implement this test")

    def test_check_stop(self) -> None:
        raise Exception("Must implement this test")

    def test_check_stop_limit(self) -> None:
        raise Exception("Must implement this test")

    def test_check_logic(self) -> None:
        raise Exception("Must implement this test")

    def test_set_get_fee(self) -> None:
        exec_price = Price(60, self.rsbl)
        # Fee Is Left
        self.odr1._set_execution_price(exec_price)
        l_fee = Price(0.00025, self.lsbl)
        self.odr1._set_fee(l_fee)
        exp1_1 = l_fee
        exp1_2 = Price(exec_price * l_fee, self.rsbl)
        result1_1 = self.odr1.get_fee(l_fee.get_asset())
        result1_2 = self.odr1.get_fee(exp1_2.get_asset())
        self.assertEqual(exp1_1, result1_1)
        self.assertEqual(exp1_2, result1_2)
        # Fee Is Right
        self.setUp()
        self.odr1._set_execution_price(exec_price)
        r_fee = Price(0.01498500, self.rsbl)
        self.odr1._set_fee(r_fee)
        exp2_1 = r_fee
        exp2_2 = Price(r_fee / exec_price, self.lsbl)
        result2_1 = self.odr1.get_fee(r_fee.get_asset())
        result2_2 = self.odr1.get_fee(exp2_2.get_asset())
        self.assertEqual(exp2_1, result2_1)
        self.assertEqual(exp2_2, result2_2)
        # Fee Already Set
        self.setUp()
        self.odr1._set_execution_price(exec_price)
        self.odr1._set_fee(l_fee)
        with self.assertRaises(Exception):
            self.odr1._set_fee(r_fee)
        # Symbol Don't Match Order's Pair
        self.setUp()
        self.odr1._set_execution_price(exec_price)
        with self.assertRaises(Exception):
            self.odr1._set_fee(Price(3.9, "BNB"))
        # Fee Not Set
        self.setUp()
        with self.assertRaises(Exception):
            self.odr1.get_fee(Asset("BNB"))
        # Symbol Not In Order's Pair
        self.setUp()
        self.odr1._set_execution_price(exec_price)
        self.odr1._set_fee(l_fee)
        with self.assertRaises(ValueError):
            self.odr1.get_fee(Asset("BNB"))

    def test_resume_subexecution(self) -> None:
        pair = Pair('DOGE/USDT')
        right_symbol = pair.get_right().get_symbol()
        left_symbol = pair.get_left().get_symbol()
        # """
        fills = [
            {
                "price": "130.8575",
                "qty": "1.007",
                "commission": "1.00000000",
                "commissionAsset": right_symbol
            },
            {
                "price": "130.8839",
                "qty": "6.511",
                "commission": "2.00000000",
                "commissionAsset": right_symbol
            },
            {
                "price": "130.8857",
                "qty": "0.057",
                "commission": "3.00000000",
                "commissionAsset": right_symbol
            }
        ]
        # """
        trades = Map()
        for i in range(len(fills)):
            trade_id = f'trade_id{i}'
            row = fills[i]
            trade = {
                Map.pair: pair,
                Map.order: 'orderid_001',
                Map.trade: trade_id,
                Map.price: Price(row[Map.price], right_symbol),
                Map.quantity: Price(row[Map.qty], left_symbol),
                Map.amount: None,
                Map.fee: Price(row[Map.commission], right_symbol),
                Map.time: i,
                Map.buy: True,
                Map.maker: False
            }
            trades.put(trade, trade_id)
        quantity_vals = [float(row[Map.qty]) for row in fills]
        sum_quantity = sum(quantity_vals)
        exec_price_obj = Price(130.880, right_symbol)
        exec_quantity_obj = Price(sum_quantity, left_symbol)
        exp1 = Map({
            Map.time: 0,
            Map.price: exec_price_obj,
            Map.left: exec_quantity_obj,
            # Map.right: Price(exec_price_obj * exec_quantity_obj, right_symbol),
            Map.right: Price(round(exec_price_obj * exec_quantity_obj, 2), right_symbol),
            Map.fee: Price(6.0, right_symbol)
        })
        result1 = self._exctract_trade_datas(trades)
        # Round exec Price
        exec_price_obj = result1.get(Map.price)
        rounded_exec_price = round(exec_price_obj.get_value(), 2)
        result1.put(Price(rounded_exec_price, exec_price_obj.get_asset().get_symbol()), Map.price)
        # Round executed amount
        exec_amount_obj = result1.get(Map.right)
        rounded_exec_emount = round(exec_amount_obj.get_value(), 2)
        result1.put(Price(rounded_exec_emount, exec_amount_obj.get_asset().get_symbol()), Map.right)
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        print(result1)
        # Rise error
        # with self.assertRaises(ValueError):
        #    self._exctract_trade_datas([])

    def test_inherit_from_transaction(self) -> None:
        def test_state(state) -> None:
            self.assertEqual(state['spot'], wallet.get_spot())
            self.assertEqual(state['buy'], wallet.get_buy())
            self.assertEqual(state['sell'], wallet.get_sell())
            self.assertEqual(state['positions'], wallet.get_all_position_value(bkr))
            self.assertEqual(state['roi'], wallet.get_roi(bkr))
            self.assertEqual(state['total'], wallet.get_total(bkr))
        
        bkr = self.broker_switch(True)
        pair = Pair('DOGE/USDT')
        r_asset = pair.get_right()
        l_asset = pair.get_left()
        r_zero = Price(0, r_asset)
        initial = Price(1000, r_asset)
        fee_rate = 1/100
        wallet = Wallet(initial)
        marketprice = wallet.get_marketprice(bkr, l_asset)
        close = marketprice.get_close()
        exec_price = Price(close, r_asset)
        buy = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: self.MOVE_BUY,
            # Map.amount: Price(115, r_asset)
            Map.amount: initial
        }))
        self.execute(order=buy, exec_price=exec_price, amount=buy.get_amount(), fee_rate=fee_rate)
        buy_fee = buy.get_fee(r_asset)
        sell_qty = buy.get_executed_quantity() - buy.get_fee(l_asset)
        sell = BinanceOrder(self.TYPE_MARKET, Map({
            Map.pair: pair,
            Map.move: self.MOVE_SELL,
            Map.quantity: sell_qty
        }))
        self.execute(order=sell, exec_price=exec_price, quantity=sell.get_quantity(), fee_rate=fee_rate)
        sell_fee = sell.get_fee(r_asset)
        # State
        buy_value = buy.get_executed_amount()
        sell_value = sell.get_executed_amount()
        states = [
            {
                'spot': r_zero,
                'buy': buy_value,
                'sell': r_zero,
                'positions': buy_value - buy_fee,
                'roi': (buy_value - buy_fee)/initial-1,
                'total': initial - buy_fee,
                },
            {
                'spot': initial - buy_value + sell_value - sell_fee,
                'buy': buy_value,
                'sell': sell_value,
                'positions': buy_value - buy_fee - sell_value,
                'roi': (initial - (buy_fee + sell_fee))/initial-1,
                'total': initial - buy_value + sell_value - sell_fee + (buy_value - buy_fee - sell_value)
                }
            ]
        # Buy
        wallet.buy(buy)
        test_state(states[0])
        # Sell
        wallet.sell(sell)
        test_state(states[1])
        # End
        self.broker_switch(False)


if __name__ == '__main__':
    unittest.main
