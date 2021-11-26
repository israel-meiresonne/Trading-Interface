from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.Asset import Asset
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price
from model.tools.Transaction import Transaction
from model.tools.Transactions import Transactions


class Wallet(MyJson):
    PREFIX_ID = 'wallet_'
    _MARKET_PERIOD = 60
    _MARKET_N_PERIOD = 10
    _DEFAULT_BUY_RATE = 1
    ATTR_POSITONS = 'POSITIONS'                 # Pair(left/right)
    ATTR_ADDED_POSIIONS = 'ADDED_POSIIONS'      # Pair(left/left)
    ATTR_REMOVED_POSIIONS = 'REMOVED_POSIIONS'  # Pair(left/left)
    _BUY_CAPITAL_N_DECIMAL = 3
    SUM_LEFT = Map.left
    SUM_RIGHT = Map.right
    SUM_FEE = Map.fee

    def __init__(self, initial: Price) -> None:
        self.__id = self.PREFIX_ID + _MF.new_code()
        self.__settime = _MF.get_timestamp(unit=_MF.TIME_MILLISEC)
        self.__max_buy = None
        self.__buy_rate = None
        self.__initial = None
        self.__depot = None
        self.__withdrawal = None
        self.__spot = None
        self.__buy = None
        self.__sell = None
        self.__positions = None
        self.__added_positions = None
        self.__removed_positions = None
        self.__historic = None
        self.__marketprices = None
        self.__total = None
        self.__roi = None
        self._set_initial(initial)

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER DOWN ——————————————————————————————————————————

    def get_id(self) -> str:
        return self.__id

    def get_settime(self) -> int:
        """
        To get the creation time in millisecond

        Returns:
        --------
        return: int
            The creation time in millisecond
        """
        return self.__settime

    def reset_max_buy(self) -> None:
        self.__max_buy = None

    def set_max_buy(self, max_buy: Price) -> None:
        if max_buy.get_value() <= 0:
            raise ValueError(f"The max buy capital must be > 0")
        r_asset = self.get_initial().get_asset()
        if max_buy.get_asset() != self.get_initial().get_asset():
            raise ValueError(f"The max buy capital's Asset must be '{r_asset}', instead '{max_buy.get_asset()}'")
        n_decimal = self.get_n_decimal()
        self.__max_buy = Price(max_buy.get_value(), r_asset, n_decimal=n_decimal)

    def get_max_buy(self) -> Price:
        """
        To get the max amount of Wallet.spot that can be used to buy

        Return:
        -------
        return: Price
            The max amount of Wallet.spot that can be used to buy
        """
        return self.__max_buy

    def set_buy_rate(self, buy_rate: float) -> None:
        if not (0 < buy_rate <= 1):
            raise ValueError(f"The Wallet.buy_rate must respect domain ]0,1]")
        self.__buy_rate = buy_rate

    def get_buy_rate(self) -> float:
        """
        To get the max rate of Wallet.spot that can be used to buy
        
        Returns:
        --------
        return: float
            The max rate of Wallet.spot that can be used to buy
        """
        buy_rate = self.__buy_rate
        return buy_rate if buy_rate is not None else self.get_default_buy_rate()

    def _set_initial(self, initial: Price) -> None:
        # Check
        if not isinstance(initial, Price):
            raise ValueError(f"The initial Price '{initial}' must be type Price, instead type='{type(initial)}'")
        self._not_negative(initial)
        # Initial
        self.__initial = initial
        # Depot
        pair = self._new_pair(initial.get_asset())
        fee = Price(0, initial.get_asset())
        transac = Transaction(Transaction.TYPE_DEPOSIT, pair, right=initial, left=initial, fee=fee)
        self._get_spot_transactions().add(transac)
    
    def get_initial(self) -> Price:
        """
        To get the initial capital

        Returns:
        --------
        return: Price
            The initial capital
        """
        return self.__initial

    def _get_depot_transactions(self) -> Transactions:
        if self.__depot is None:
            pair = self._new_pair()
            self.__depot = Transactions(pair)
        return self.__depot
    
    def get_depot(self, sum_key: str = SUM_RIGHT) -> Price:
        return self._get_depot_transactions().sum().get(sum_key)

    def _get_withdrawal_transactions(self) -> Transactions:
        if self.__withdrawal is None:
            pair = self._new_pair()
            self.__withdrawal = Transactions(pair)
        return self.__withdrawal
    
    def get_withdrawal(self, sum_key: str = SUM_RIGHT) -> Price:
        return self._get_withdrawal_transactions().sum().get(sum_key)
        
    def _get_spot_transactions(self) -> Transactions:
        if self.__spot is None:
            pair = self._new_pair()
            self.__spot = Transactions(pair)
        return self.__spot
    
    def get_spot(self, sum_key: str = SUM_RIGHT) -> Price:
        return self._get_spot_transactions().sum().get(sum_key)
        
    def _get_buy_transactions(self) -> Transactions:
        if self.__buy is None:
            pair = self._new_pair()
            self.__buy = Transactions(pair)
        return self.__buy
    
    def get_buy(self, sum_key: str = SUM_RIGHT) -> Price:
        """
        To get Amount spend

        Returns:
        --------
        return: Price
            The Amount of sells
        """
        return self._get_buy_transactions().sum().get(sum_key)
        
    def _get_sell_transactions(self) -> Transactions:
        if self.__sell is None:
            pair = self._new_pair()
            self.__sell = Transactions(pair)
        return self.__sell
    
    def get_sell(self, sum_key: str = SUM_RIGHT) -> Price:
        """
        To get Amount of sells

        Returns:
        --------
        return: Price
            The Amount of sells
        """
        return self._get_sell_transactions().sum().get(sum_key)

    def _get_positions(self, attribute: str = ATTR_POSITONS) -> Map:
        """
        To get positions holds in each Asset
        
        Returns:
        --------
        return: Map
            Positions holds in each Asset
            positions[Pair{str}]: {Transactions}
        """
        if attribute == self.ATTR_POSITONS:
            if self.__positions is None:
                self.__positions = Map()
            return self.__positions
        elif attribute == self.ATTR_ADDED_POSIIONS:
            if self.__added_positions is None:
                self.__added_positions = Map()
            return self.__added_positions
        elif attribute == self.ATTR_REMOVED_POSIIONS:
            if self.__removed_positions is None:
                self.__removed_positions = Map()
            return self.__removed_positions
        else:
            raise ValueError(f"This positions attribut '{attribute}' is not supported")
    
    def _get_position_transactions(self, asset: Asset, attribute: str = ATTR_POSITONS) -> Transactions:
        positions = self._get_positions(attribute)
        pair = self._new_pair(asset) if attribute == self.ATTR_POSITONS else Pair(asset, asset)
        pair_str = pair.__str__()
        if pair_str not in positions.get_keys():
            transacs = Transactions(pair)
            positions.put(transacs, pair_str)
        return positions.get(pair_str)

    def get_position(self, asset: Asset, attribute: str = ATTR_POSITONS) -> Price:
        """
        To get position on the given Asset

        Parameters:
        -----------
        asset: Asset
            The left Asset to get position of

        Returns:
        --------
        return: Price
            The position on the given Asset
        """
        positions = self._get_positions(attribute)
        pair = self._new_pair(asset) if attribute == self.ATTR_POSITONS else Pair(asset, asset)
        pair_str = pair.__str__()
        transacs = positions.get(pair_str)
        return transacs.sum().get(Map.left) if isinstance(transacs, Transactions) else Price(0, asset)
    
    def get_position_value(self, bkr: Broker, asset: Asset, attribute: str = ATTR_POSITONS) -> Price:
        """
        To get the given Asset's value in Wallet.initial's Asset

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API
        asset: Asset
            The left Asset to get position of

        Returns:
        --------
        return: Price
            The given Asset's value in Wallet.initial's Asset
        """
        right_asset = self.get_initial().get_asset()
        pos_value = Price(0, right_asset)
        position = self.get_position(asset, attribute)
        if position.get_value() > 0:
            marketprice = self.get_marketprice(bkr, asset)
            close = marketprice.get_close()
            pos_value = Price(position * close, right_asset)
        return pos_value

    def get_all_position_value(self, bkr: Broker, attribute: str = ATTR_POSITONS) -> Price:
        """
        To get value of all positions in Wallet.initial's Asset

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API

        Returns:
        --------
        return: Price
            The value of all positions in Wallet.initial's Asset
        """
        assets = self.assets(attribute)
        value = Price.sum([self.get_position_value(bkr, asset, attribute) for asset in assets]) \
            if len(assets) > 0 else Price(0, self.get_initial().get_asset())
        return value

    def get_historic(self) -> dict:
        pass

    def reset_marketprices(self) -> None:
        self._reset_total()
        self._reset_roi()
        self.__marketprices = None

    def _get_marketprices(self) -> Map:
        """
        To get MarketPrice stored

        Return:
        -------
        return: Map
            MarketPrice stored
            marketprices[Pair{str}]: {MarketPrice}
        """
        if self.__marketprices is None:
            self.__marketprices = Map()
        return self.__marketprices

    def get_marketprice(self, bkr: Broker, asset: Asset) -> MarketPrice:
        marketprices = self._get_marketprices()
        pair = self._new_pair(asset)
        pair_str = pair.__str__()
        marketprice = marketprices.get(pair_str)
        if marketprice is None:
            period = self.get_period()
            n_period = self.get_n_period()
            marketprice = MarketPrice.marketprice(bkr, pair, period, n_period)
            marketprices.put(marketprice, pair_str)
        return marketprice

    def _reset_total(self) -> None:
        self.__total = None

    def _set_total(self, bkr: Broker) -> None:
        def total() -> Price:
            spot = self.get_spot()
            position = self.get_all_position_value(bkr, self.ATTR_POSITONS)
            return spot + position
        self.__total = total()

    def get_total(self, bkr: Broker) -> Price:
        """
        To get Wallet’s total value in Wallet.initial’s Asset

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API
        
        Returns:
        --------
        return: Price
            Wallet’s total value in Wallet.initial’s Asset
        """
        self._set_total(bkr) if self.__total is None else None
        return self.__total

    def _reset_roi(self) -> None:
        self.__roi = None

    def _set_roi(self, bkr: Broker) -> None:
        def func_roi() -> float:
            roi = 0
            buy = self.get_buy()
            if buy.get_value() != 0:
                sell = self.get_sell()
                buy_fee = self.get_buy(sum_key=self.SUM_FEE)
                position = self.get_all_position_value(bkr, self.ATTR_POSITONS)
                add_position = self.get_all_position_value(bkr, self.ATTR_ADDED_POSIIONS)
                removed_position = self.get_all_position_value(bkr, self.ATTR_REMOVED_POSIIONS)
                roi = (position + sell - add_position + removed_position) / (buy + buy_fee) - 1
            return roi
        self.__roi = func_roi()

    def get_roi(self, bkr: Broker) -> float:
        """
        To get Wallet’s Return On Invest (ROI)

        Parameters:
        -----------
        bkr: Broker
            Access to Broker's API
        
        Returns:
        --------
        return: float
            Wallet’s Return On Invest (ROI)
        """
        self._set_roi(bkr) if self.__roi is None else None
        return self.__roi

    # ——————————————————————————————————————————— FUNCTION SETTER/GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— FUNCTION SELF DOWN ———————————————————————————————————————————————————

    def _new_pair(self, asset: Asset = None) -> Pair:
        if (asset is not None) and (not isinstance(asset, Asset)):
            raise ValueError(f"The asset '{asset}' must be type Asset, instead '{type(asset)}'")
        wallet_asset = self.get_initial().get_asset()
        return Pair(asset, wallet_asset) if asset is not None else Pair(wallet_asset, wallet_asset)
    
    def assets(self, attribute: str = ATTR_POSITONS) -> list[Asset]:
        pair_strs = self._get_positions(attribute)
        assets = [Pair(pair_str).get_left() for pair_str in pair_strs.get_keys()]
        return assets
    
    def deposit(self, amount: Price, fee: Price = None) -> None:
        """
        To add fund in Wallet

        Parameters:
        -----------
        amount: Price
            The amount to add
        fee: Price = None
            Transaction fee
        
        Raises:
        -------
        raise: ValueException
            if the amount to add is negative
            if the fee to is negative
        """
        # Check
        self._not_negative(amount)
        pair = self._new_pair(amount.get_asset())
        fee = fee if fee is not None else Price(0, pair.get_right())
        self._not_negative(fee)
        right = left = amount
        # Depot
        depot = Transaction(Transaction.TYPE_DEPOSIT, pair, right, left, fee)
        self._get_depot_transactions().add(depot)
        # Spot
        spot = depot.clone()
        self._get_spot_transactions().add(spot)
        # Link
        depot.link(spot)
        # Reset
        self._reset_total()

    def withdraw(self, amount: Price, fee: Price = None) -> None:
        """
        To withdraw fund from Wallet

        Parameters:
        -----------
        amount: Price
            The amount to withdraw
        fee: Price = None
            Transaction fee
        
        Raises:
        -------
        raise: ValueException
            if the amount to withdraw is negative
            if the fee to is negative
            if amount exced available fund
        """
        # Check
        self._not_negative(amount)
        pair = self._new_pair(amount.get_asset())
        fee = fee if fee is not None else Price(0, pair.get_right())
        self._not_negative(fee)
        fund = self.get_spot()
        self._enough_fund(fund, amount)
        # Prepare
        right = left = amount
        # Withdraw
        withdraw = Transaction(Transaction.TYPE_WITHDRAWAL, pair, right, left, fee)
        self._get_withdrawal_transactions().add(withdraw)
        # Spot
        spot = withdraw.clone(right=-right, left=-left)
        self._get_spot_transactions().add(spot)
        # Link
        withdraw.link(spot)
        # Reset
        self._reset_total()

    def buy(self, transaction: Transaction) -> None:
        """
        To buy Asset

        Parameters:
        -----------
        transaction: Transaction
            A buy Transaction executed
        
        Raises:
        -------
        raise: ValueException
            if the Transaction.right is negative
            if the Transaction.left is negative
            if the Transaction.fee is negative
            if Transaction.right exced available fund
            if Transaction.type is wrong
        """
        # Check
        transac_right = transaction.get_right()
        transac_left = transaction.get_left()
        transac_fee = transaction.get_transaction_fee()
        self._not_negative(transac_right)
        self._not_negative(transac_left)
        self._not_negative(transac_fee)
        fund = self.get_spot()
        self._enough_fund(fund, transac_right)
        self._transaction_type(transaction, Transaction.TYPE_BUY)
        buy_capital = self.buy_capital()
        if transac_right.get_value() > buy_capital.get_value():
            raise ValueError(f"The buy amount '{transac_right}' exceed the max buy capital '{buy_capital}'")
        # Prepare
        neg_transac_right = -transac_right
        pos_pair = transaction.get_pair()
        double_pair = self._new_pair(pos_pair.get_right())
        # Position
        position = transaction.clone()
        self._get_position_transactions(pos_pair.get_left()).add(position)
        # Buy
        buy = position.clone(pair=double_pair, right=transac_right, left=transac_right, fee=transac_fee)
        self._get_buy_transactions().add(buy)
        # Spot
        spot = position.clone(pair=double_pair, right=neg_transac_right, left=neg_transac_right, fee=transac_fee)
        self._get_spot_transactions().add(spot)
        # Link
        position.link(buy)
        position.link(spot)
        # Reset
        self._reset_total()
        self._reset_roi()

    def sell(self, transaction: Transaction) -> None:
        """
        To sell Asset

        Parameters:
        -----------
        transaction: Transaction
            A sell Transaction executed
                    
        Raises:
        -------
        raise: ValueException
            if the Transaction.right is negative
            if the Transaction.left is negative
            if the Transaction.fee is negative
            if Transaction.left exced available fund
            if Transaction.type is wrong
        """
        # Check
        transac_right = transaction.get_right()
        transac_left = transaction.get_left()
        transac_fee = transaction.get_transaction_fee()
        self._not_negative(transac_right)
        self._not_negative(transac_left)
        self._not_negative(transac_fee)
        fund = self.get_position(transac_left.get_asset(), self.ATTR_POSITONS)
        self._enough_fund(fund, transac_left)
        self._transaction_type(transaction, Transaction.TYPE_SELL)
        # Prepare
        neg_transac_right = -transac_right
        neg_transac_left = -transac_left
        pos_pair = transaction.get_pair()
        double_pair = self._new_pair(pos_pair.get_right())
        # Position
        position = transaction.clone(right=neg_transac_right, left=neg_transac_left, fee=transac_fee)
        self._get_position_transactions(pos_pair.get_left()).add(position)
        # Sell
        sell = transaction.clone(pair=double_pair, right=transac_right, left=transac_right, fee=transac_fee)
        self._get_sell_transactions().add(sell)
        # Spot
        spot = position.clone(pair=double_pair, right=transac_right, left=transac_right, fee=transac_fee)
        self._get_spot_transactions().add(spot)
        # Link
        position.link(sell)
        position.link(spot)
        # Reset
        self._reset_total()
        self._reset_roi()

    def add_position(self, quantity: Price, fee: Price = None) -> None:
        """
        To add Asset to Wallet.added_position

        Parameters:
        -----------
        quantity: Price
            The Asset to add
        fee: Price = None
            Transaction fee in Wallet.initial's Asset
        
        Raises:
        -------
        raise: ValueException
            if the quantity is negative
            if the fee to is negative
        """
        # Check
        self._not_negative(quantity)
        asset = quantity.get_asset()
        pair = self._new_pair(asset)
        fee = fee if fee is not None else Price(0, pair.get_right())
        self._not_negative(fee)
        # Prepare
        pair_double = Pair(asset, asset)
        # Added Position
        add_pos_fee = Price(0, asset)
        add_pos = Transaction(Transaction.TYPE_DEPOSIT, pair=pair_double, right=quantity, left=quantity, fee=add_pos_fee)
        self._get_position_transactions(asset, self.ATTR_ADDED_POSIIONS).add(add_pos)
        # Position
        pos_right = Price(0, pair.get_right())
        position = add_pos.clone(pair=pair, right=pos_right, left=quantity, fee=fee)
        self._get_position_transactions(asset, self.ATTR_POSITONS).add(position)
        # Link
        add_pos.link(position)
        # Reset
        self._reset_total()

    def remove_position(self, quantity: Price, fee: Price = None) -> None:
        """
        To remove Asset to Wallet.added_position

        Parameters:
        -----------
        quantity: Price
            The Asset to remove
        fee: Price = None
            Transaction fee in Wallet.initial's Asset
        
        Raises:
        -------
        raise: ValueException
            if the quantity to remove is negative
            if the fee to is negative
            if quantity exced available fund
        """
        # Check
        self._not_negative(quantity)
        asset = quantity.get_asset()
        pair = self._new_pair(asset)
        fee = fee if fee is not None else Price(0, pair.get_right())
        self._not_negative(fee)
        fund = self.get_position(asset, self.ATTR_POSITONS)
        self._enough_fund(fund, quantity)
        # Remove Position
        pair_double = Pair(asset, asset)
        remove_pos_fee = Price(0, asset)
        remove_pos = Transaction(Transaction.TYPE_WITHDRAWAL, pair=pair_double, right=quantity, left=quantity, fee=remove_pos_fee)
        self._get_position_transactions(asset, self.ATTR_REMOVED_POSIIONS).add(remove_pos)
        # Position
        pos_right = Price(0, pair.get_right())
        position = remove_pos.clone(pair=pair, right=pos_right, left=-quantity, fee=fee)
        self._get_position_transactions(asset, self.ATTR_POSITONS).add(position)
        # Link
        remove_pos.link(position)
        # Reset
        self._reset_total()

    def buy_capital(self) -> Price:
        """
        To get amount of Wallet.spot available to buy

        Returns:
        --------
        return: Price
            The amount of Wallet.spot available to buy
        """
        n_decimal = self.get_n_decimal()
        max_buy = self.get_max_buy()
        buy_rate = self.get_buy_rate()
        spot = self.get_spot()
        r_asset = self.get_initial().get_asset()
        buy_capital = Price(spot * buy_rate, r_asset, n_decimal=n_decimal)
        max_reached = (max_buy is not None) and (buy_capital.get_value() > max_buy.get_value())
        buy_capital = max_buy if max_reached else buy_capital
        return buy_capital

    def spot_fee(self) -> Price:
        """
        To get total fee charged for all deposit and withdrawal
        NOTE: spot_fee = sum(Wallet.depot.fee) + sum(Wallet.withdrawal.fee)

        Returns:
        --------
        return: Price
            Total fee charged for all deposit and withdrawal
        """
        depot_fee = self._get_depot_transactions().sum().get(Map.fee)
        withdrawal_fee = self._get_withdrawal_transactions().sum().get(Map.fee)
        return depot_fee + withdrawal_fee

    def trade_fee(self) -> Price:
        """
        To get total fee charged for all buy and sell
        NOTE: trade_fee = sum(Wallet.buy.fee) + sum(Wallet.sell.fee)

        Returns:
        --------
        return: Price
            Total fee charged for all buy and sell
        """
        buy_fee = self._get_buy_transactions().sum().get(Map.fee)
        sell_fee = self._get_sell_transactions().sum().get(Map.fee)
        return buy_fee + sell_fee

    def _json_encode_prepare(self) -> None:
        self.reset_marketprices()

    # ——————————————————————————————————————————— FUNCTION SELF UP —————————————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION GETTER DOWN ——————————————————————————————————————————

    @staticmethod
    def get_period() -> int:
        """
        To get period interval to request MarketPrice
        
        Return:
        -------
        return: int
            The default period to request MarketPrice
        """
        return Wallet._MARKET_PERIOD

    @staticmethod
    def get_n_period() -> int:
        """
        To get number of period to request MarketPrice
        
        Return:
        -------
        return: int
            The number of period to request MarketPrice
        """
        return Wallet._MARKET_N_PERIOD

    @staticmethod
    def get_default_buy_rate() -> float:
        """
        To get default buy rate

        Return:
        -------
        return: float
            The default buy rate
        """
        return Wallet._DEFAULT_BUY_RATE

    @staticmethod
    def get_n_decimal() -> int:
        return Wallet._BUY_CAPITAL_N_DECIMAL

    # ——————————————————————————————————————————— STATIC FUNCTION GETTER UP ————————————————————————————————————————————
    # ——————————————————————————————————————————— STATIC FUNCTION DOWN —————————————————————————————————————————————————

    @staticmethod
    def _not_negative(price: Price) -> bool:
        if price.get_value() < 0:
            raise ValueError(f"The Price '{price}' must be >= 0")
        return True
    
    @staticmethod
    def _transaction_type(transaction: Transaction, transac_type: str) -> None:
        if transaction.get_transaction_type() != transac_type:
            raise TypeError(f"The transaction's type must be '{transac_type}', instead '{transaction.get_transaction_type()}'")
    
    @staticmethod
    def _enough_fund(fund: Price, amount: Price) -> bool:
        if amount.get_value() > fund.get_value():
            raise ValueError(f"The amount '{amount}' exced available fund '{fund}'")
        return True

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = Wallet(Price(0, Asset('@json')))
        exec(MyJson.get_executable())
        return instance

    # ——————————————————————————————————————————— STATIC FUNCTION UP ———————————————————————————————————————————————————
