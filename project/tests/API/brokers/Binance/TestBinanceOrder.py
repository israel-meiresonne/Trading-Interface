import unittest

from config.Config import Config
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.API.brokers.Binance.BinanceOrder import BinanceOrder
from model.tools.Map import Map
from model.tools.Order import Order
from model.tools.Paire import Pair
from model.tools.Price import Price


class TestBinanceOrder(unittest.TestCase, BinanceOrder):
    def setUp(self) -> None:
        Config.update(Config.STAGE_MODE, Config.STAGE_1)
        BinanceAPI("api_pb", "api_sk", True)
        self.lsbl = "BTC"
        self.rsbl = "USDT"
        # MARKET
        self.pr = Pair(self.lsbl, self.rsbl)
        self.prc1 = Price(250, self.rsbl)
        self.prc2 = Price(10, self.lsbl)
        self.mkt_prms1 = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.amount: self.prc1
        })
        self.mkt_prms1_extracted = Map({
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
            Map.quantity: None,
            Map.quoteOrderQty: self.prc1.get_value()
        })
        self.mkt_prms1_generated = Map({
            Map.symbol: self.pr.get_merged_symbols().upper(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.quoteOrderQty: self.prc1.get_value()
        })
        self.mkt_prms2 = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.quantity: self.prc2
        })
        self.mkt_prms2_extracted = Map({
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.newClientOrderId: None,
            Map.recvWindow: None,
            Map.quantity: self.prc2.get_value(),
            Map.quoteOrderQty: None
        })
        self.mkt_ordr1 = BinanceOrder(BinanceOrder.TYPE_MARKET, self.mkt_prms1)
        self.mkt_ordr2 = BinanceOrder(BinanceOrder.TYPE_MARKET, self.mkt_prms2)
        # STOP
        self.stop_prc1 = Price(12000, self.rsbl)
        self.qty1 = Price(3, self.lsbl)
        self.stop_prms1 = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_BUY,
            Map.stop: self.stop_prc1,
            Map.quantity: self.qty1
        })
        self.stop_prms1_extracted = Map({
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_STOP,
            Map.quantity: self.qty1.get_value(),
            Map.stopPrice: self.stop_prc1.get_value(),
            Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.quoteOrderQty: None,
            Map.price: None,
            Map.newClientOrderId: None,
            Map.icebergQty: None,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL,
            Map.recvWindow: None
        })
        self.stop_prms1_generated = Map({
            Map.symbol: self.pr.get_merged_symbols().upper(),
            Map.side: BinanceAPI.SIDE_BUY,
            Map.type: BinanceAPI.TYPE_STOP,
            Map.quantity: self.qty1.get_value(),
            Map.stopPrice: self.stop_prc1.get_value(),
            Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL
        })
        self.stop_prms2 = Map({
            Map.pair: self.pr,
            Map.move: self.MOVE_SELL,
            Map.stop: self.stop_prc1,
            Map.quantity: self.qty1
        })
        self.stop_prms2_extracted = Map({
            Map.symbol: self.pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_STOP,
            Map.quantity: self.qty1.get_value(),
            Map.stopPrice: self.stop_prc1.get_value(),
            Map.timeInForce: BinanceAPI.TIME_FRC_GTC,
            Map.quoteOrderQty: None,
            Map.price: None,
            Map.newClientOrderId: None,
            Map.icebergQty: None,
            Map.newOrderRespType: BinanceAPI.RSP_TYPE_FULL,
            Map.recvWindow: None
        })
        # self.stop_odr1 = BinanceOrder(BinanceOrder.TYPE_STOP, self.stop_prms1)
        # self.stop_odr2 = BinanceOrder(BinanceOrder.TYPE_STOP, self.stop_prms2)

    def test_constructor_market(self):
        # amount set
        BinanceOrder(BinanceOrder.TYPE_MARKET, self.mkt_prms1)
        # quantity set
        BinanceOrder(BinanceOrder.TYPE_MARKET, self.mkt_prms2)

    def test_extract_market_params(self):
        # amount set
        exp1 = self.mkt_prms1_extracted
        result1 = self.mkt_ordr1._extract_market_params()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # quantity set
        exp2 = self.mkt_prms2_extracted
        result2 = self.mkt_ordr2._extract_market_params()
        self.assertDictEqual(exp2.get_map(), result2.get_map())

    def test_exract_market_request(self):
        # amount set
        exp1 = BinanceAPI.RQ_ORDER_MARKET_amount
        result1 = self.mkt_ordr1._exract_market_request()
        self.assertEqual(exp1, result1)
        # quantity set
        exp2 = BinanceAPI.RQ_ORDER_MARKET_qty
        result2 = self.mkt_ordr2._exract_market_request()
        self.assertEqual(exp2, result2)
        # amount and quantity are both set
        self.mkt_ordr2._set_amount(self.prc1)
        with self.assertRaises(ValueError):
            self.mkt_ordr2._exract_market_request()
        # neither amount and quantity are set
        self.setUp()
        self.mkt_ordr1._set_amount(None)
        with self.assertRaises(ValueError):
            self.mkt_ordr1._exract_market_request()

    def test_constructor_stop(self):
        # Buy
        BinanceOrder(BinanceOrder.TYPE_STOP, self.stop_prms1)
        # Sell
        BinanceOrder(BinanceOrder.TYPE_STOP, self.stop_prms2)

    def test_extract_stop_params(self):
        # Buy
        exp1 = self.stop_prms1_extracted
        result1 = self.stop_odr1._extract_stop_params()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Sell
        exp2 = self.stop_prms2_extracted
        result2 = self.stop_odr2._extract_stop_params()
        self.assertDictEqual(exp2.get_map(), result2.get_map())

    def test_generate_order(self):
        # Market
        exp1 = self.mkt_prms1_generated
        result1 = self.mkt_ordr1.generate_order()
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Stop
        exp2 = self.stop_prms1_generated
        result2 = self.stop_odr1.generate_order()
        self.assertDictEqual(exp2.get_map(), result2.get_map())

    def test_handle_response(self):
        raise Exception("Must implement this test")

    def test_generate_cancel_order(self):
        raise Exception("Must implement this test")

    """
    def test_resume_subexecution(self) -> None:
        symbol = "USDT"
        fills = [
            {
                "price": "130.8575",
                "qty": "1.007",
                "commission": "1.00000000",
                "commissionAsset": symbol
            },
            {
                "price": "130.8839",
                "qty": "6.511",
                "commission": "2.00000000",
                "commissionAsset": symbol
            },
            {
                "price": "130.8857",
                "qty": "0.057",
                "commission": "3.00000000",
                "commissionAsset": symbol
            }
        ]
        exp1 = Map({
            Map.price: Price(130.880, symbol),
            Map.fee: 6.0
        })
        result1 = self.resume_subexecution(fills)
        self.assertDictEqual(exp1.get_map(), result1.get_map())
        # Rise error
        with self.assertRaises(ValueError):
            self.resume_subexecution([])
    """

    def test_structure_trades(self) -> None:
        pair = Pair("DOGE/USDT")
        order_bkr_id = "order_bkr_id_001"
        exec_time = 700
        move = Order.MOVE_SELL
        is_buy = False
        rsp_trades = [
            {
                "price": "4000.00000000",
                "qty": "1.00000000",
                "commission": "4.00000000",
                "commissionAsset": "USDT"
            },
            {
                "price": "3999.00000000",
                "qty": "5.00000000",
                "commission": "19.99500000",
                "commissionAsset": "USDT"
            }
        ]
        """,
            {
                "price": "3998.00000000",
                "qty": "2.00000000",
                "commission": "7.99600000",
                "commissionAsset": "USDT"
            },
            {
                "price": "3997.00000000",
                "qty": "1.00000000",
                "commission": "3.99700000",
                "commissionAsset": "USDT"
            },
            {
                "price": "3995.00000000",
                "qty": "1.00000000",
                "commission": "3.99500000",
                "commissionAsset": "USDT"
            }
        ]
        """
        exp1 = Map()
        for i in range(len(rsp_trades)):
            trade_id = f"{order_bkr_id}_{i}"
            rsp_trade = rsp_trades[i]
            fee_symbol = rsp_trade[Map.commissionAsset]
            left_symbol = pair.get_left().get_symbol()
            right_symbol = pair.get_right().get_symbol()
            exec_price = Price(rsp_trade[Map.price], right_symbol)
            exec_quantity = Price(rsp_trade[Map.qty], left_symbol)
            exec_amount = Price(exec_price * exec_quantity, right_symbol)
            fee = Price(rsp_trade[Map.commission], fee_symbol)
            trade = {
                Map.pair: pair,
                Map.order: order_bkr_id,
                Map.trade: None,
                Map.price: exec_price,
                Map.quantity: exec_quantity,
                Map.amount: exec_amount,
                Map.fee: fee,
                Map.time: exec_time,
                Map.buy: is_buy,
                Map.maker: False
            }
            exp1.put(trade, trade_id)
        result1 = BinanceOrder._structure_trades(rsp_trades, pair, exec_time, order_bkr_id, move)
        print(exp1, '\n')
        print(result1)
        self.assertDictEqual(exp1.get_map(), result1.get_map())


if __name__ == '__main__':
    unittest.main
