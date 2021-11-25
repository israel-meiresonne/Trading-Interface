import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.Icarus.Icarus import Icarus
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction


class TestTraderClass(unittest.TestCase):
    def setUp(self) -> None:
        self.stg_params1 = Map({
            Map.pair: Pair('DOGE/USDT'),
            Map.period: 60 * 5,
            Map.capital: Price(1000, 'USDT'),
            Map.maximum: None,
            Map.rate: None
        })
        stg_params = self.stg_params1
        self.stg = Icarus(stg_params)

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

    def test_get_marketprice(self) -> None:
        bkr = self.broker_switch(True)
        stg = self.stg
        stg._set_broker(bkr)
        stg_period = stg.get_period()
        n_period = 10
        period = 60
        marketprice_1 = stg.get_marketprice(stg_period, n_period)
        marketprice_2 = stg.get_marketprice(period)
        # MarketPrice 1
        self.assertEqual(stg.get_pair(), marketprice_1.get_pair())
        self.assertEqual(n_period, len(marketprice_1.get_closes()))
        # MarketPrice 2
        self.assertEqual(stg.get_pair(), marketprice_2.get_pair())
        self.assertEqual(stg.get_marketprice_n_period(), len(marketprice_2.get_closes()))
        # List of MarketPrice
        marketprices = stg._get_marketprices()
        exp1 = Map({
            stg_period: marketprice_1,
            period: marketprice_2,
        })
        self.assertEqual(exp1, marketprices)
        # Same instance
        exp2 = stg.get_marketprice(period)
        self.assertEqual(id(exp2), id(marketprice_2))
        self.broker_switch(False)

    def test_new_buy_order(self) -> None:
        bkr = self.broker_switch(True)
        stg = self.stg
        stg_params = self.stg_params1
        pair = stg_params.get(Map.pair)
        initial = stg_params.get(Map.capital)
        _bkr_cls = bkr.__class__.__name__
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_BUY,
            Map.amount: initial
        })
        exp1 = Order.generate_broker_order(_bkr_cls, Order.TYPE_MARKET, odr_params)
        result1 = stg._new_buy_order(bkr)
        self.assertIsInstance(result1, Order)
        self.assertNotEqual(exp1.get_id(), result1.get_id())
        self.assertEqual(pair, result1.get_pair())
        self.assertEqual(Order.MOVE_BUY, result1.get_move())
        self.assertEqual(initial, result1.get_amount())
        self.assertIsNone(result1.get_quantity())
        self.broker_switch(False)

    def test_new_sell_order(self) -> None:
        bkr = self.broker_switch(True)
        stg = self.stg
        stg_params = self.stg_params1
        pair = stg_params.get(Map.pair)
        r_asset = pair.get_right()
        l_asset = pair.get_left()
        initial = stg_params.get(Map.capital)
        fee_rate = 1/100
        _bkr_cls = bkr.__class__.__name__
        # ———
        close1 = 25*10**(-3)
        righ1 = Price(initial*(75/100), r_asset)
        left1 = Price(righ1/close1, l_asset)
        fee1 = Price(righ1 * fee_rate, r_asset)
        transac1 =  Transaction(type=Transaction.TYPE_BUY, pair=pair, right=righ1, left=left1, fee=fee1)
        stg.get_wallet().buy(transac1)
        # ———
        odr_params = Map({
            Map.pair: pair,
            Map.move: Order.MOVE_SELL,
            Map.quantity: left1
        })
        exp1 = Order.generate_broker_order(_bkr_cls, Order.TYPE_MARKET, odr_params)
        result1 = stg._new_sell_order(bkr)
        self.assertIsInstance(result1, Order)
        self.assertNotEqual(exp1.get_id(), result1.get_id())
        self.assertEqual(pair, result1.get_pair())
        self.assertEqual(Order.MOVE_SELL, result1.get_move())
        self.assertEqual(left1, result1.get_quantity())
        self.assertIsNone(result1.get_amount())
        self.broker_switch(False)
