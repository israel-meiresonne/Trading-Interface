import unittest

from config.Config import Config
from model.API.brokers.Binance.Binance import Binance
from model.structure.Broker import Broker
from model.structure.strategies.Icarus.Icarus import Icarus
from model.structure.strategies.IcarusStalker.IcarusStalker import IcarusStalker
from model.structure.strategies.StalkerClass import StalkerClass
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction
from model.tools.Wallet import Wallet


class TestStalkerClass(unittest.TestCase, StalkerClass):
    def setUp(self) -> None:
        r_asset = Asset('USDT')
        self.params = Map({
            Map.pair: Pair('?', r_asset),
            Map.capital: Price(1000, r_asset),
            Map.maximum: None,
            Map.rate: None,
            Map.period: 60 * 15,
            Map.strategy: Icarus.__name__,
            Map.param: {
                Map.period: 60 * 5
            }
        })
        params = self.params
        self.stk1_pair = params.get(Map.pair)
        self.stk1 = IcarusStalker(params)

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

    def test_get_children_total(self) -> None:
        bkr = self.broker_switch(True)
        stk = self.stk1
        r_asset = stk.get_wallet().get_initial().get_asset()
        fee_rate = 1/100
        pair1 = Pair('BTC', r_asset)
        pair2 = Pair('DOGE', r_asset)
        l_asset2 = pair2.get_left()
        # Check child total without any child positions
        exp1 = Price(0, r_asset)
        result1 = stk.get_children_total(bkr)
        self.assertEqual(exp1, result1)
        # 
        stk._add_active_strategy(pair1)
        stk._add_active_strategy(pair2)
        stg1_initial = stk.get_active_strategy(pair1).get_wallet().get_initial()
        stg2 = stk.get_active_strategy(pair2)
        stg2_initial = stg2.get_wallet().get_initial()
        marketprice = stg2.get_wallet().get_marketprice(bkr, l_asset2)
        close2 = marketprice.get_close()
        # Transaction
        righ2 = Price(stg2_initial*(80/100), r_asset)
        left2 = Price(righ2/close2, l_asset2)
        fee2 = Price(righ2 * fee_rate, r_asset)
        transac2 =  Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2, left=left2, fee=fee2)
        stg2.get_wallet().buy(transac2)
        # Check child total with child positions
        exp2 = stg1_initial + stg2_initial
        result2 = stk.get_children_total(bkr)
        self.assertEqual(exp2, result2)
        # Check if child has position
        exp3 = righ2
        result3 = stg2.get_wallet().get_buy()
        self.assertEqual(exp3, result3)
        # ——
        exp4 = left2
        result4 = stg2.get_wallet().get_position(l_asset2)
        self.assertEqual(exp4, result4)
        # End
        self.broker_switch(False)

    def test_get_total(self) -> None:
        bkr = self.broker_switch(True)
        stk = self.stk1
        stk_initial = stk.get_wallet().get_initial()
        exp1 = stk_initial
        result1 = stk.get_total(bkr)
        self.assertEqual(exp1, result1)
        self.broker_switch(False)

    def test_get_fee(self) -> None:
        bkr = self.broker_switch(True)
        stk = self.stk1
        r_asset = stk.get_wallet().get_initial().get_asset()
        fee_rate = 1/100
        pair1 = Pair('BTC', r_asset)
        pair2 = Pair('DOGE', r_asset)
        pair3 = Pair('BNB', r_asset)
        l_asset2 = pair2.get_left()
        l_asset3 = pair3.get_left()
        # 
        stk._add_active_strategy(pair1)
        stk._add_active_strategy(pair2)
        stk._add_active_strategy(pair3)
        # stg1 = stk.get_active_strategy(pair1)
        stg2 = stk.get_active_strategy(pair2)
        stg3 = stk.get_active_strategy(pair3)
        stg2_initial = stg2.get_wallet().get_initial()
        stg3_initial = stg3.get_wallet().get_initial()
        marketprice2 = stg2.get_wallet().get_marketprice(bkr, l_asset2)
        close2 = marketprice2.get_close()
        marketprice3 = stg2.get_wallet().get_marketprice(bkr, l_asset3)
        close3 = marketprice3.get_close()
        # # Transaction 1
        righ2 = Price(stg2_initial*(80/100), r_asset)
        left2 = Price(righ2/close2, l_asset2)
        fee2 = Price(righ2 * fee_rate, r_asset)
        transac2 =  Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2, left=left2, fee=fee2)
        # Transaction 1
        righ3 = Price(stg3_initial*(40/100), r_asset)
        left3 = Price(righ3/close3, l_asset3)
        fee3 = Price(righ3 * fee_rate, r_asset)
        transac3 =  Transaction(type=Transaction.TYPE_BUY, pair=pair3, right=righ3, left=left3, fee=fee3)
        stg2.get_wallet().buy(transac2)
        stg3.get_wallet().buy(transac3)
        stk._delete_active_strategy(bkr, pair3)
        # Check child total with child positions
        exp1 = fee2 + fee3
        result1 = stk.get_fee()
        self.assertEqual(exp1, result1)
        # End
        self.broker_switch(False)

    def test_get_strategy_capital(self) -> None:
        stk = self.stk1
        stk._set_max_strategy(3)
        r_asset = stk.get_pair().get_right()
        pair1 = Pair('BTC', r_asset)
        pair2 = Pair('DOGE', r_asset)
        pair3 = Pair('BNB', r_asset)
        max_stg = stk.get_max_strategy()
        # N active Strategy = 0
        n_active_stg = len(stk.get_active_strategies().get_map())
        exp1 = stk.get_wallet().buy_capital() / (max_stg - n_active_stg)
        exp1 = Price(exp1, r_asset)
        result1 = stk._get_strategy_capital()
        self.assertEqual(exp1, result1)
        # N active Strategy > 0
        stk._add_active_strategy(pair1)
        stk._add_active_strategy(pair2)
        n_active_stg = len(stk.get_active_strategies().get_map())
        exp2 = stk.get_wallet().buy_capital() / (max_stg - n_active_stg)
        exp2 = Price(exp2, r_asset)
        result2 = stk._get_strategy_capital()
        self.assertEqual(exp2, result2)
        # N active Strategy == max active Strategy
        stk._add_active_strategy(pair3)
        with self.assertRaises(ValueError):
            stk._get_strategy_capital()

    def test_add_active_strategy(self) -> None:
        stk = self.stk1
        stk_initial = stk.get_wallet().get_initial()
        r_asset = stk.get_pair().get_right()
        pair1 = Pair('DOGE', r_asset)
        l_asset1 = pair1.get_left()
        """
        Add without residue
        """
        stk._add_active_strategy(pair1)
        child_stg1 = stk.get_active_strategy(pair1)
        child_initial1 = child_stg1.get_wallet().get_initial()
        # —— Check child Stategy's class
        exp2 = stk.get_strategy_class()
        result2 = child_stg1.__class__.__name__
        self.assertEqual(exp2, result2)
        # —— Check child Stategy's Pair
        self.assertEqual(pair1, child_stg1.get_pair())
        # —— Check child Stategy's initial capital
        exp3 = stk._get_strategy_capital()
        result3 = child_stg1.get_wallet().get_spot()
        self.assertEqual(exp3, result3)
        # —— Check child Strategy's initial left
        exp1 = Price(0, l_asset1)
        result1 = child_stg1.get_wallet().get_position(l_asset1)
        self.assertEqual(exp1, result1)
        # —— Check Stalker withdraw
        exp4 = stk._get_strategy_capital()
        result4 = stk.get_wallet().get_withdrawal()
        self.assertEqual(exp4, result4)
        # —— Check Stalker left
        exp5 = stk.get_wallet().get_position(l_asset1, Wallet.ATTR_REMOVED_POSIIONS)
        result5 = Price(0, l_asset1)
        self.assertEqual(exp5, result5)
        # —— Check Stalker capital
        exp6 = stk_initial - child_initial1
        result6 = stk.get_wallet().get_spot()
        self.assertEqual(exp6, result6)
        """
        Add with residue
        """
        # self.setUp()
        pair2 = Pair('BTC', r_asset)
        l_asset2 = pair2.get_left()
        residue = Price(15, l_asset2)
        stk.get_wallet().add_position(residue)
        stk._add_active_strategy(pair2)
        child_stg2 = stk.get_active_strategy(pair2)
        # —— Check child Stategy's initial capital
        exp7 = stk._get_strategy_capital()
        result7 = child_stg2.get_wallet().get_spot()
        self.assertEqual(exp7, result7)
        # —— Check child Strategy's initial left
        exp8 = residue
        result8 = child_stg2.get_wallet().get_position(l_asset2)
        self.assertEqual(exp8, result8)

    def test_delete_active_strategy(self) -> None:
        bkr = self.broker_switch(True)
        stk = self.stk1
        stk_wallet = stk.get_wallet()
        stk_initial = stk_wallet.get_initial()
        child_initial = stk._get_strategy_capital()
        r_asset = stk_initial.get_asset()
        """
        Delete without residue nor fee
        """
        pair1 = Pair('DOGE', r_asset)
        l_asset1 = pair1.get_left()
        stk._add_active_strategy(pair1)
        stg1 = stk.get_active_strategy(pair1)
        stg1_spot = stg1.get_wallet().get_spot()
        stg1_residue = stg1.get_wallet().get_position(l_asset1)
        stg1_fee = stg1.get_wallet().trade_fee()
        stk._delete_active_strategy(bkr, pair1)
        # Stalker's spot == Stalker.initial
        exp1 = stk_initial
        result1 = stk_wallet.get_spot()
        self.assertEqual(exp1, result1)
        # Child's spot == Stalker.child_initial_capital
        exp2 = stg1_spot
        result2 = child_initial
        self.assertEqual(exp2, result2)
        # Child's residue == Stalker.residue
        exp3 = stg1_residue
        result3 = stk_wallet.get_position(l_asset1)
        self.assertEqual(exp3, result3)
        # Child's fee == Stalker.fee
        exp4 = stg1_fee
        result4 = stk.get_fee()
        self.assertEqual(exp4, result4)
        """
        Delete with residue & fee
        """
        pair2 = Pair('BTC', r_asset)
        l_asset2 = pair2.get_left()
        close2 = 5*10**4
        fee_rate = 1/100
        # Buy and Sell to create fee & residue
        # ————————————————————————————————————
        # —— Add child
        stk._add_active_strategy(pair2)
        stg2 = stk.get_active_strategy(pair2)
        # —— Transaction 1
        righ2_1 = child_initial
        left2_1 = Price(righ2_1/close2, l_asset2)
        fee2_1 = Price(righ2_1 * fee_rate, r_asset)
        transac2_1 =  Transaction(type=Transaction.TYPE_BUY, pair=pair2, right=righ2_1, left=left2_1, fee=fee2_1)
        # —— Transaction 2
        left2_2 = Price(left2_1*(80/100), l_asset2)
        residue2 = left2_1 - left2_2
        righ2_2 = Price(left2_2*close2, r_asset)
        fee2_2 = Price(righ2_2 * fee_rate, r_asset)
        transac2_2 =  Transaction(type=Transaction.TYPE_SELL, pair=pair2, right=righ2_2, left=left2_2, fee=fee2_2)
        stg2.get_wallet().buy(transac2_1)
        stg2.get_wallet().sell(transac2_2)
        # —— Delete child
        stk._delete_active_strategy(bkr, pair2)
        stg2_spot = stg2.get_wallet().get_spot()
        stg2_fee = stg2.get_wallet().trade_fee()
        # ————————————————————————————————————
        # Stalker's spot after child have buy & sell
        exp5 = stk_initial - righ2_1 + righ2_2
        result5 = stk_wallet.get_spot() 
        self.assertEqual(exp5, result5)
        # Child's spot == 0
        exp6 = Price(0, r_asset)
        result6 = stg2_spot
        self.assertEqual(exp6, result6)
        # Child's residue == Stalker.residue
        exp7 = residue2
        result7 = stk_wallet.get_position(l_asset2)
        self.assertEqual(exp7, result7)
        # Child's fee == Stalker.fee
        exp8 = stg2_fee
        result8 = stk.get_fee()
        self.assertEqual(exp8, result8)
        # End
        self.broker_switch(False)

    # ——————————————————————————————————————————— FUNCTION TEST UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION INHERITANCE DOWN ————————————————————————————————————————————

    def _manage_trades(self, bkr: Broker) -> None:
        pass

    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> bool:
        pass

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'StalkerClass':
        pass
