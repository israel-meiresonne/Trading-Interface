import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.tools.Asset import Asset
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction
from model.tools.Wallet import Wallet


class TestWallet(unittest.TestCase, Wallet):
    def setUp(self) -> None:
        self.asset1 = Asset('DOGE')
        asset1 = self.asset1
        self.asset2 = Asset('BTC')
        self.initial1 = Price(1000, 'USDT')
        initial1 = self.initial1
        self.pair1 = Pair(asset1, initial1.get_asset())
        self.amount1 = Price(100, initial1.get_asset())
        self.amount2 = Price(50, initial1.get_asset())
        self.w1 = Wallet(initial1)
        self.init_stage = None
        self.bkr = None
    
    def tearDown(self) -> None:
        self.broker_switch(False)

    def broker_switch(self, on: bool = False) -> Broker:
        if on:
            self.init_stage = Config.get(Config.STAGE_MODE)
            Config.update(Config.STAGE_MODE, Config.STAGE_2)
            self.bkr = Binance(Map({
                Map.public: '-',
                Map.secret: '-',
                Map.test_mode: False
            }))
        else:
            init_stage = self.init_stage
            self.bkr.close() if self.bkr is not None else None
            Config.update(Config.STAGE_MODE,
                          init_stage) if init_stage is not None else None
        return self.bkr
    
    def test_set_initial(self) -> None:
        initial = self.initial1
        wallet = self.w1
        # Setted
        self.assertEqual(initial, wallet.get_initial())
        # Wrong type
        with self.assertRaises(ValueError):
            Wallet(initial.get_value())
        # Negative Price
        with self.assertRaises(ValueError):
            Wallet(-initial)

    def test_set_max_buy(self) -> None:
        wallet = self.w1
        initial = self.initial1
        r_asset = initial.get_asset()
        # max_buy is None
        self.assertIsNone(wallet.get_max_buy())
        # Correct
        max_buy1 = Price(10, r_asset)
        wallet.set_max_buy(max_buy1)
        self.assertEqual(max_buy1, wallet.get_max_buy())
        # max_buy == 0
        max_buy2 = Price(0, r_asset)
        with self.assertRaises(ValueError):
            wallet.set_max_buy(max_buy2)
        # max_buy < 0
        max_buy3 = Price(-1, r_asset)
        with self.assertRaises(ValueError):
            wallet.set_max_buy(max_buy3)

    def test_set_get_buy_rate(self) -> None:
        wallet = self.w1
        # Getter: buy_rate is None
        exp1 = Wallet.get_default_buy_rate()
        result1 = wallet.get_buy_rate()
        self.assertEqual(exp1, result1)
        # Setter: correct
        exp2 = 0.018
        wallet.set_buy_rate(exp2)
        result2 = wallet.get_buy_rate()
        self.assertEqual(exp2, result2)
        # buy_rate > 1
        with self.assertRaises(ValueError):
            wallet.set_buy_rate(10)
        # buy_rate == 0
        with self.assertRaises(ValueError):
            wallet.set_buy_rate(0)
        # buy_rate < 0
        with self.assertRaises(ValueError):
            wallet.set_buy_rate(-10)

    def test_get_position_value(self) -> None:
        bkr = self.broker_switch(True)
        wallet = self.w1
        initial = self.initial1
        fee_rate = 0.001
        asset1 = self.asset1
        asset2 = self.asset2
        marketprice1 = wallet.get_marketprice(bkr, asset1)
        marketprice2 = wallet.get_marketprice(bkr, asset2)
        close1 = marketprice1.get_close()
        close2 = marketprice2.get_close()
        # # Transaction 1
        pair1 = Pair(asset1, initial.get_asset())
        right1 = Price(300, pair1.get_right())
        fee1 = Price(right1*fee_rate, pair1.get_right())
        left1 = Price((right1 - fee1) / close1, pair1.get_left())
        transac1 = Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=right1, left=left1, fee=fee1)
        # Transaction 2
        pair2 = Pair(asset2, initial.get_asset())
        right2 = Price(50, pair2.get_right())
        fee2 = Price(right2*fee_rate, pair2.get_right())
        left2 = Price((right2 - fee2) / close2, pair2.get_left())
        transac2 = Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=right2, left=left2, fee=fee2)
        # Transaction 1
        pair3 = pair1
        right3 = Price(70, pair3.get_right())
        fee3 = Price(right3*fee_rate, pair3.get_right())
        left3 = Price((right3 - fee3) / close1, pair3.get_left())
        transac3 = Transaction(type=Transaction.TYPE_BUY, pair=pair3, right=right3, left=left3, fee=fee3)
        # Buy
        wallet.buy(transac1)
        wallet.buy(transac2)
        wallet.buy(transac3)
        # Position value
        # —— Asset1
        exp1 = (left1 + left3) * close1
        exp1 = Price(exp1, initial.get_asset())
        result1 = wallet.get_position_value(bkr, asset1)
        self.assertEqual(exp1, result1)
        # —— Asset2
        exp2 = left2 * close2
        exp2 = Price(exp2, initial.get_asset())
        result2 = wallet.get_position_value(bkr, asset2)
        self.assertEqual(exp2, result2)
        # —— Total Position
        exp3 = exp1 + exp2
        result3 = wallet.get_all_position_value(bkr)
        self.assertEqual(exp3, result3)
        # End
        self.broker_switch(False)

    def test_get_marketprice(self) -> None:
        bkr = self.broker_switch(True)
        wallet = self.w1
        asset1 = self.asset1
        asset2 = self.asset2
        # Keep MarketPrice
        marketprice1 = wallet.get_marketprice(bkr, asset1)
        marketprice2 = wallet.get_marketprice(bkr, asset2)
        self.assertEqual(marketprice1.get_id(), wallet.get_marketprice(bkr, asset1).get_id())
        self.assertEqual(marketprice2.get_id(), wallet.get_marketprice(bkr, asset2).get_id())
        # Reset
        wallet.reset_marketprices()
        result1 = len(wallet._get_marketprices().get_map())
        self.assertTrue(result1 == 0)
        self.broker_switch(False)
    
    def test_deposit(self) -> None:
        wallet = self.w1
        initial = self.initial1
        amount1 = self.amount1
        amount2 = self.amount2
        wallet.deposit(amount1)
        wallet.deposit(amount2)
        # Spot
        exp1 = initial + amount1 + amount2
        result1 = wallet.get_spot()
        self.assertEqual(exp1, result1)
        # Depot
        exp2 = amount1 + amount2
        result2 = wallet.get_depot()
        self.assertEqual(exp2, result2)
        # amount < 0
        with self.assertRaises(ValueError):
            wallet.deposit(-amount2)
        # fee < 0
        with self.assertRaises(ValueError):
            wallet.deposit(amount2, -amount1)

    def test_withdraw(self) -> None:
        wallet = self.w1
        initial = self.initial1
        amount1 = self.amount1
        amount2 = self.amount2
        wallet.withdraw(amount1)
        wallet.withdraw(amount2)
        # Spot
        exp1 = initial - (amount1 + amount2)
        result1 = wallet.get_spot()
        self.assertEqual(exp1, result1)
        # Withdrawal
        exp2 = amount1 + amount2
        result2 = wallet.get_withdrawal()
        self.assertEqual(exp2, result2)
        # amount < 0
        with self.assertRaises(ValueError):
            wallet.withdraw(-amount2)
        # fee < 0
        with self.assertRaises(ValueError):
            wallet.withdraw(amount2, -amount1)
        # Exced available fund
        amount3 = initial + amount1 + amount2
        with self.assertRaises(ValueError):
            wallet.withdraw(amount3)

    def test_buy(self) -> None:
        wallet = self.w1
        initial = self.initial1
        fee_rate = 0.01
        # Transaction 1
        pair1 = Pair('DOGE/USDT')
        righ1 = Price(100, pair1.get_right())
        left1 = Price(10, pair1.get_left())
        fee1 = Price(righ1 * fee_rate, pair1.get_right())
        transac1 =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ1, left=left1, fee=fee1)
        # Transaction 2
        pair2 = Pair('BTC/USDT')
        righ2 = Price(250, pair2.get_right())
        left2 = Price(righ2*10**(-3), pair2.get_left())
        fee2 = Price(righ2 * fee_rate, pair2.get_right())
        transac2 =  Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2, left=left2, fee=fee2)
        # Transaction 3
        righ3 = Price(300, pair1.get_right())
        left3 = Price(30, pair1.get_left())
        fee3 = Price(righ3 * fee_rate, pair1.get_right())
        transac3 =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ3, left=left3, fee=fee3)
        wallet.buy(transac1)
        wallet.buy(transac2)
        wallet.buy(transac3)
        # Position
        exp1 = left1 + left3
        result1 = wallet.get_position(pair1.get_left(), self.ATTR_POSITONS)
        self.assertEqual(exp1, result1)
        exp2 = left2
        result2 = wallet.get_position(pair2.get_left(), self.ATTR_POSITONS)
        self.assertEqual(exp2, result2)
        # Buy
        exp3 = righ1 + righ2 + righ3
        result3 = wallet.get_buy()
        self.assertEqual(exp3, result3)
        # Spot
        exp4 = initial - (righ1 + righ2 + righ3)
        result4 = wallet.get_spot()
        self.assertEqual(exp4, result4)
        # Sell
        exp5 = Price(0, initial.get_asset())
        result5 = wallet.get_sell()
        self.assertEqual(exp5, result5)
        # Transaction.right < 0
        transacx =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=-righ3, left=left3, fee=fee3)
        with self.assertRaises(ValueError):
            wallet.buy(transacx)
        # Transaction.left < 0
        transacx =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ3, left=-left3, fee=fee3)
        with self.assertRaises(ValueError):
            wallet.buy(transacx)
        # Transaction.fee < 0
        transacx =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ3, left=left3, fee=-fee3)
        with self.assertRaises(ValueError):
            wallet.buy(transacx)
        # Exced available fund
        transacx =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=(initial + righ1), left=left3, fee=fee3)
        with self.assertRaises(ValueError):
            wallet.buy(transacx)
        # Wrong Transaction type
        transacx =  Transaction(type=Transaction.TYPE_WITHDRAWAL, pair=pair1, right=righ1, left=left3, fee=fee3)
        with self.assertRaises(TypeError):
            wallet.buy(transacx)
        # Exceed buy_capital available
        self.setUp()
        wallet = self.w1
        max_buy = Price(1, initial.get_asset())
        wallet.set_max_buy(max_buy)
        transacx = Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ1, left=left3, fee=fee3)
        with self.assertRaises(ValueError):
            wallet.buy(transacx)

    def test_sell(self) -> None:
        wallet = self.w1
        initial = self.initial1
        fee_rate = 0.01
        pair1_rate = 10/100
        pair2_rate = 10**(-3)
        # Transaction 1
        pair1 = Pair('DOGE/USDT')
        righ1 = Price(100, pair1.get_right())
        left1 = Price(righ1*pair1_rate, pair1.get_left())
        fee1 = Price(righ1 * fee_rate, pair1.get_right())
        transac1 =  Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ1, left=left1, fee=fee1)
        # Transaction 2
        pair2 = Pair('BTC/USDT')
        righ2 = Price(250, pair2.get_right())
        left2 = Price(righ2*pair2_rate, pair2.get_left())
        fee2 = Price(righ2 * fee_rate, pair2.get_right())
        transac2 =  Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2, left=left2, fee=fee2)
        # Transaction 3
        pair3 = pair1
        righ3 = Price(300, pair3.get_right())
        left3 = Price(righ3*pair1_rate, pair3.get_left())
        fee3 = Price(righ3 * fee_rate, pair3.get_right())
        transac3 =  Transaction(type=Transaction.TYPE_BUY, pair=pair3, right=righ3, left=left3, fee=fee3)
        # Transaction 4
        pair4 = pair1
        righ4 = Price(50, pair4.get_right())
        left4 = Price(righ4*pair1_rate, pair4.get_left())
        fee4 = Price(righ4 * fee_rate, pair4.get_right())
        transac4 =  Transaction(type=Transaction.TYPE_SELL, pair=pair4, right=righ4, left=left4, fee=fee4)
        # Transaction 5
        pair5 = pair2
        righ5 = Price(30, pair5.get_right())
        left5 = Price(righ5*pair2_rate, pair5.get_left())
        fee5 = Price(righ5 * fee_rate, pair5.get_right())
        transac5 =  Transaction(type=Transaction.TYPE_SELL, pair=pair5, right=righ5, left=left5, fee=fee5)
        # Transaction 6
        pair6 = pair1
        righ6 = Price(100, pair6.get_right())
        left6 = Price(righ6*pair1_rate, pair6.get_left())
        fee6 = Price(righ6 * fee_rate, pair6.get_right())
        transac6 =  Transaction(type=Transaction.TYPE_SELL, pair=pair6, right=righ6, left=left6, fee=fee6)
        # Trade
        wallet.buy(transac1)
        wallet.buy(transac2)
        wallet.buy(transac3)
        wallet.sell(transac4)
        wallet.sell(transac5)
        wallet.sell(transac6)
        # Position
        # —— Pair1
        exp1 = left1 + left3 - left4 - left6
        result1 = wallet.get_position(pair1.get_left(), self.ATTR_POSITONS)
        self.assertEqual(exp1, result1)
        # —— Pair2
        exp2 = left2 - left5
        result2 = wallet.get_position(pair2.get_left(), self.ATTR_POSITONS)
        self.assertEqual(exp2, result2)
        # Buy
        exp3 = righ1 + righ2 + righ3
        result3 = wallet.get_buy()
        self.assertEqual(exp3, result3)
        # Spot
        exp4 = initial - (righ1 + righ2 + righ3) + (righ4 + righ5 + righ6)
        result4 = wallet.get_spot()
        self.assertEqual(exp4, result4)
        # Sell
        exp5 = righ4 + righ5 + righ6
        result5 = wallet.get_sell()
        self.assertEqual(exp5, result5)
        # Transaction.right < 0
        pairx = pair1
        righx = Price(1, pairx.get_right())
        leftx = Price(righx*pair1_rate, pairx.get_left())
        feex = Price(righx * fee_rate, pairx.get_right())
        transacx =  Transaction(type=Transaction.TYPE_SELL, pair=pairx, right=-righx, left=leftx, fee=feex)
        with self.assertRaises(ValueError):
            wallet.sell(transacx)
        # Transaction.left < 0
        transacx =  Transaction(type=Transaction.TYPE_SELL, pair=pairx, right=righx, left=-leftx, fee=feex)
        with self.assertRaises(ValueError):
            wallet.sell(transacx)
        # Transaction.fee < 0
        transacx =  Transaction(type=Transaction.TYPE_SELL, pair=pairx, right=righx, left=leftx, fee=-feex)
        with self.assertRaises(ValueError):
            wallet.sell(transacx)
        # Exced available fund
        transacx =  Transaction(type=Transaction.TYPE_SELL, pair=pairx, right=righx, left=Price(initial*2, pair1.get_left()), fee=fee3)
        with self.assertRaises(ValueError):
            wallet.sell(transacx)
        # Wrong Transaction type
        transacx =  Transaction(type=Transaction.TYPE_DEPOSIT, pair=pairx, right=righx, left=leftx, fee=feex)
        with self.assertRaises(TypeError):
            wallet.sell(transacx)

    def test_add_position(self) -> None:
        wallet = self.w1
        asset1 = self.asset1
        asset2 = self.asset2
        quantity1 = Price(90, asset1)
        quantity2 = Price(25, asset2)
        quantity3 = Price(15, asset1)
        # Add
        wallet.add_position(quantity1)
        wallet.add_position(quantity2)
        wallet.add_position(quantity3)
        # Added Position
        # —— Asset1
        exp1 = quantity1 + quantity3
        result1 = wallet.get_position(asset1, Wallet.ATTR_ADDED_POSIIONS)
        self.assertEqual(exp1, result1)
        # —— Asset2
        exp2 = quantity2
        result2 = wallet.get_position(asset2, Wallet.ATTR_ADDED_POSIIONS)
        self.assertEqual(exp2, result2)
        # Position
        # —— Asset1
        exp3 = exp1
        result3 = wallet.get_position(asset1, Wallet.ATTR_POSITONS)
        self.assertEqual(exp3, result3)
        # —— Asset2
        exp4 = exp2
        result4 = wallet.get_position(asset2, Wallet.ATTR_POSITONS)
        self.assertEqual(exp4, result4)
        # quantity < 0
        with self.assertRaises(ValueError):
            wallet.add_position(-quantity1)
        # fee < 0
        with self.assertRaises(ValueError):
            wallet.add_position(quantity1, -quantity1)

    def test_remove_position(self) -> None:
        wallet = self.w1
        asset1 = self.asset1
        asset2 = self.asset2
        quantity1 = Price(90, asset1)
        quantity2 = Price(25, asset2)
        quantity3 = Price(15, asset1)
        quantity4 = Price(9, asset1)
        quantity5 = Price(25, asset2)
        quantity6 = Price(50, asset1)
        # Add
        wallet.add_position(quantity1)
        wallet.add_position(quantity2)
        wallet.add_position(quantity3)
        wallet.remove_position(quantity4)
        wallet.remove_position(quantity5)
        wallet.remove_position(quantity6)
        # Added Position
        # —— Asset1
        exp1 = quantity1 + quantity3
        result1 = wallet.get_position(asset1, Wallet.ATTR_ADDED_POSIIONS)
        self.assertEqual(exp1, result1)
        # —— Asset2
        exp2 = quantity2
        result2 = wallet.get_position(asset2, Wallet.ATTR_ADDED_POSIIONS)
        self.assertEqual(exp2, result2)
        # Removed Position
        # —— Asset1
        exp4 = quantity4 + quantity6
        result4 = wallet.get_position(asset1, Wallet.ATTR_REMOVED_POSIIONS)
        self.assertEqual(exp4, result4)
        # —— Asset2
        exp5 = quantity5
        result5 = wallet.get_position(asset2, Wallet.ATTR_REMOVED_POSIIONS)
        self.assertEqual(exp5, result5)
        # Positione
        # —— Asset1
        exp3 = exp1 - exp4
        result3 = wallet.get_position(asset1, Wallet.ATTR_POSITONS)
        self.assertEqual(exp3, result3)
        # —— Asset2
        exp6 = exp2 - exp5
        result6 = wallet.get_position(asset2, Wallet.ATTR_POSITONS)
        self.assertEqual(exp6, result6)
        # quantity < 0
        with self.assertRaises(ValueError):
            wallet.deposit(-quantity1)
        # fee < 0
        with self.assertRaises(ValueError):
            wallet.remove_position(quantity1, -quantity1)
        # Exced available fund
        quantityx = Price(quantity2*10, quantity2.get_asset())
        with self.assertRaises(ValueError):
            wallet.remove_position(quantityx)

    def test_buy_capital(self) -> None:
        wallet = self.w1
        initial = self.initial1
        r_asset = initial.get_asset()
        # buy_capital = Wallet.spot
        exp1 = initial
        result1 = wallet.buy_capital()
        self.assertEqual(exp1, result1)
        # buy_rate
        buy_rate2 = 0.5
        wallet.set_buy_rate(buy_rate2)
        exp2 = Price(initial * buy_rate2, r_asset)
        result2 = wallet.buy_capital()
        self.assertEqual(exp2, result2)
        # max_buy
        self.setUp()
        wallet = self.w1
        max_buy3 = Price(initial/3, r_asset)
        wallet.set_max_buy(max_buy3)
        exp3 = max_buy3
        result3 = wallet.buy_capital()
        self.assertEqual(exp3, result3)
        # buy_rate & max_buy
        self.setUp()
        buy_rate4 = 0.2
        max_buy4 = Price(initial/10, r_asset)
        wallet.set_max_buy(max_buy4)
        wallet.set_buy_rate(buy_rate4)
        exp4 = max_buy4
        result4 = wallet.buy_capital()
        self.assertEqual(exp4, result4)
        self.assertEqual(max_buy4, wallet.get_max_buy())
        self.assertEqual(buy_rate4, wallet.get_buy_rate())

    def test_trade_fee(self) -> None:
        wallet = self.w1
        r_asset = wallet.get_initial().get_asset()
        fee_rate = 1/100
        # Transaction 1
        close1 = 50000
        pair1 = Pair('BTC', r_asset)
        righ1 = Price(100, pair1.get_right())
        left1 = Price(righ1/close1, pair1.get_left())
        fee1 = Price(righ1 * fee_rate, pair1.get_right())
        transac1 = Transaction(type=Transaction.TYPE_BUY, pair=pair1, right=righ1, left=left1, fee=fee1)
        # Transaction 2
        close2 = 0.5
        pair2 = Pair('DOGE', r_asset)
        righ2 = Price(150, pair2.get_right())
        left2 = Price(righ2/close2, pair2.get_left())
        fee2 = Price(righ2 * fee_rate, pair2.get_right())
        transac2 = Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2, left=left2, fee=fee2)
        # Transaction 3
        pair3 = pair1
        righ3 = Price(100, pair3.get_right())
        left3 = Price(righ3/close1, pair3.get_left())
        fee3 = Price(righ3 * fee_rate, pair3.get_right())
        transac3 = Transaction(type=Transaction.TYPE_SELL, pair=pair3, right=righ3, left=left3, fee=fee3)
        # Transaction 4
        pair4 = pair2
        righ4 = Price(20, pair4.get_right())
        left4 = Price(righ4/close2, pair4.get_left())
        fee4 = Price(righ4 * fee_rate, pair4.get_right())
        transac4 = Transaction(type=Transaction.TYPE_SELL, pair=pair4, right=righ4, left=left4, fee=fee4)
        # Before fee
        exp1 = Price(0, r_asset)
        result1 = wallet.trade_fee()
        self.assertEqual(exp1, result1)
        # Execute
        wallet.buy(transac1)
        wallet.buy(transac2)
        wallet.sell(transac3)
        wallet.sell(transac4)
        # fee
        exp2 = fee1 + fee2 + fee3 + fee4
        result2 = wallet.trade_fee()
        self.assertEqual(exp2, result2)

    def test_spot_fee(self) -> None:
        wallet = self.w1
        r_asset = wallet.get_initial().get_asset()
        fee_rate = 1/100
        # Transaction 1
        pair1 = Pair('BTC', r_asset)
        righ1 = Price(100, pair1.get_right())
        fee1 = Price(righ1 * fee_rate, pair1.get_right())
        # Transaction 2
        pair2 = Pair('DOGE', r_asset)
        righ2 = Price(150, pair2.get_right())
        fee2 = Price(righ2 * fee_rate, pair2.get_right())
        # Transaction 3
        pair3 = pair1
        righ3 = Price(100, pair3.get_right())
        fee3 = Price(righ3 * fee_rate, pair3.get_right())
        # Transaction 4
        pair4 = pair2
        righ4 = Price(20, pair4.get_right())
        fee4 = Price(righ4 * fee_rate, pair4.get_right())
        # Before fee
        exp1 = Price(0, r_asset)
        result1 = wallet.spot_fee()
        self.assertEqual(exp1, result1)
        # Execute
        wallet.deposit(righ1, fee1)
        wallet.deposit(righ2, fee2)
        wallet.withdraw(righ3, fee3)
        wallet.withdraw(righ4, fee4)
        # fee
        exp2 = fee1 + fee2 + fee3 + fee4
        result2 = wallet.spot_fee()
        self.assertEqual(exp2, result2)

    def test_multiple_transaction(self) -> None:
        state_idx = 0
        def test_state() -> int:
            wallet_stage = new_wallet_stages[state_idx]
            wallet._reset_roi()
            wallet._reset_total()
            self.assertEqual(wallet_stage[cols['initial']], wallet.get_initial())
            self.assertEqual(wallet_stage[cols['depot']], wallet.get_depot())
            self.assertEqual(wallet_stage[cols['spot']], wallet.get_spot())
            self.assertEqual(wallet_stage[cols['withdrawal']], wallet.get_withdrawal())
            self.assertEqual(wallet_stage[cols['buy']], wallet.get_buy())
            self.assertEqual(wallet_stage[cols['sell']], wallet.get_sell())
            self.assertEqual(wallet_stage[cols['added_positions']], wallet.get_all_position_value(bkr, Wallet.ATTR_ADDED_POSIIONS))
            self.assertEqual(wallet_stage[cols['positions']], wallet.get_all_position_value(bkr, Wallet.ATTR_POSITONS))
            self.assertEqual(wallet_stage[cols['removed_positions']], wallet.get_all_position_value(bkr, Wallet.ATTR_REMOVED_POSIIONS))
            self.assertEqual(wallet_stage[cols['roi']], wallet.get_roi(bkr))
            self.assertEqual(wallet_stage[cols['total']], wallet.get_total(bkr))
            return state_idx + 1

        bkr = self.broker_switch(True)
        file_path = 'tests/datas/tools/TestWallet/test_multiple_transaction/wallet-states.csv'
        wallet_stages = FileManager.get_csv(file_path)
        cols = {
            'initial': 'initial',
            'depot': 'depot',
            'spot': 'spot',
            'withdrawal': 'withdrawal',
            'buy': 'buy',
            'sell': 'sell',
            'added_positions': 'added_positions',
            'positions': 'positions',
            'removed_positions': 'removed_positions',
            'roi': 'roi',
            'total': 'total'
        }
        pair = Pair('DOGE/USDT')
        initial = Price(100, pair.get_right())
        wallet = Wallet(initial)
        fee_rate = 0.1/100
        new_wallet_stages = []
        for row in wallet_stages:
            new_row = {}
            new_wallet_stages.append(new_row)
            for col in cols:
                new_row[col] = float(row[col]) if col == cols['roi'] else Price(row[col], pair.get_right())
        # 1. New wallet
        state_idx = test_state()
        # 2. Buy assets
        marketprice = wallet.get_marketprice(bkr, pair.get_left())
        close = marketprice.get_close()
        righ1 = Price(90, pair.get_right())
        left1 = Price(righ1/close, pair.get_left())
        fee1 = Price(righ1 * fee_rate, pair.get_right())
        transac1 = Transaction(type=Transaction.TYPE_BUY, pair=pair, right=righ1, left=left1, fee=fee1)
        wallet.buy(transac1)
        state_idx = test_state()
        # 3. Assets take value
        increase_rate = new_wallet_stages[state_idx][cols['roi']]
        righ2 = Price(0, pair.get_right())
        left2 = Price(left1*increase_rate, pair.get_left())
        fee2 = Price(0, pair.get_right())
        transac2 = Transaction(type=Transaction.TYPE_DEPOSIT, pair=pair, right=righ2, left=left2, fee=fee2)
        wallet._get_position_transactions(pair.get_left()).add(transac2)
        state_idx = test_state()
        # 4. Sell profit on assets
        righ3 = Price(left2*close, pair.get_right())
        left3 = left2
        fee3 = Price(righ3*fee_rate, pair.get_right())
        transac3 = Transaction(type=Transaction.TYPE_SELL, pair=pair, right=righ3, left=left3, fee=fee3)
        wallet.sell(transac3)
        state_idx = test_state()
        # 5. Withdraw spot
        wallet.withdraw(righ3)
        state_idx = test_state()
        # 6. Deposit
        depot = Price(30, pair.get_right())
        wallet.deposit(depot)
        state_idx = test_state()
        # 7. Add position
        add_pos = Price(9/close, pair.get_left())
        wallet.add_position(add_pos)
        state_idx = test_state()
        # 8. Remove position
        remove_pos = Price(18/close, pair.get_left())
        wallet.remove_position(remove_pos)
        state_idx = test_state()
        # End
        self.broker_switch(False)

    def test_json_encode_decode(self) -> None:
        wallet = self.w1
        json = wallet.json_encode()
        wallet_decoded = MyJson.json_decode(json)
        self.assertIsInstance(wallet_decoded, Wallet)
        self.assertNotEqual(id(wallet), id(wallet_decoded))
        self.assertEqual(wallet.get_id(), wallet_decoded.get_id())
        self.assertEqual(wallet, wallet_decoded)
