from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Icarus.Icarus import Icarus
from model.structure.strategies.StalkerClass import StalkerClass
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Price import Price


class IcarusStalker(StalkerClass):
<<<<<<< HEAD
<<<<<<< HEAD
=======
    _CONST_MAX_STRATEGY = 20
=======
    _CONST_MAX_STRATEGY = 5
>>>>>>> Icarus-v13.1.4
    _RESET_INTERVAL_ALLOWED_PAIR = 60*15    # in second
    CHILD_STRATEGY = Icarus
    _MARKETPRICE_N_PERIOD = CHILD_STRATEGY.get_marketprice_n_period()

>>>>>>> Icarus-test
    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:               {Stalker.__init__()}    # Same structure
        """
        super().__init__(params)

    def _manage_trades(self, bkr: Broker) -> None:
        _cls = self
        _normal = _cls._TO_REMOVE_STYLE_NORMAL
        _color_black = _cls._TO_REMOVE_STYLE_BLACK
        _color_cyan = _cls._TO_REMOVE_STYLE_CYAN
        _color_green = _cls._TO_REMOVE_STYLE_GREEN
        _color_purple = _cls._TO_REMOVE_STYLE_PURPLE
        _color_red = _cls._TO_REMOVE_STYLE_RED
        _color_yellow = _cls._TO_REMOVE_STYLE_YELLOW
        _back_cyan = _cls._TO_REMOVE_STYLE_BACK_CYAN
<<<<<<< HEAD
        #
        active_stgs_copy = Map(self.get_active_strategies().get_map())
        pairs_to_delete = []  # ❌
        pair_closes = Map()  # ❌
        rows = []  # ❌
        print(f"{_MF.prefix()}" + _back_cyan + _color_black + f"Star manage strategies "
                                                              f"({len(active_stgs_copy.get_map())}):".upper() + _normal)
        self._manage_trades_add_streams(bkr, active_stgs_copy)
        market_analyse = self.get_market_analyse()
        market_trend = MarketPrice.get_market_trend(bkr, analyse=market_analyse) if market_analyse is not None else '—'
        market_analyse = Map() if market_analyse is None else market_analyse
        for pair_str, active_stg in active_stgs_copy.get_map().items():
            print(f"{_MF.prefix()}" + _color_cyan + f"Managing pair '{pair_str.upper()}'..." + _normal)
            # Prepare active Strategy
            pair = active_stg.get_pair()
            stg_period = active_stg.get_period()
            market_price = self._get_market_price(bkr, pair, stg_period)
            # Prepare closes
            closes = list(market_price.get_closes())
=======

        pair = child.get_pair()
        pair_str = pair.__str__()
        _MF.output(f"{_MF.prefix()}" + _color_cyan + f"Managing pair '{pair_str.upper()}'..." + _normal)
        # Prepare active Strategy
        stg_wallet = child.get_wallet()
        pair = child.get_pair()
        stg_period = child.get_period()
        # Before trade
        stg_roi = stg_wallet.get_roi(bkr)
        fee = stg_wallet.trade_fee()
        initial_capital = stg_wallet.get_initial()
        fee_initial_capital_rate = fee / initial_capital
        actual_capital = stg_wallet.get_total(bkr)
        fee_actual_capital_rate = fee / actual_capital
        # Trade
        child._update_orders(bkr)
        has_position_before = child._has_position()
        keep_stg = (child.get_nb_trade() == 0) or has_position_before
        child.trade(bkr) if keep_stg else None
        has_position_after = child._has_position() if keep_stg else None
        if keep_stg and has_position_after:
            _MF.output(f"{_MF.prefix()}" + _color_green + f"Pair {pair_str.upper()} trade with SUCCESS." + _normal)
        else:
            self._delete_active_strategy(bkr, pair)
            # self._blacklist_pair(pair, stg_period)
            _MF.output(f"{_MF.prefix()}" + _color_red + f"Pair {pair_str.upper()} is DELETED." + _normal)
        # After trade
        stg_roi_after = stg_wallet.get_roi(bkr)
        fee_after = stg_wallet.trade_fee()
        fee_initial_capital_rate_after = fee_after / initial_capital
        # Prepare closes
        market_price = child.get_marketprice(stg_period, bkr=bkr)
        closes = list(market_price.get_closes())
        closes.reverse()
        # Print
        endtime = _MF.get_timestamp()
        interval = _MF.delta_time(starttime, endtime)
        rows = [{
            Map.index: self._get_trade_index(),
            Map.trade: self.get_nb_trade(),
            Map.date: _MF.unix_to_date(endtime),
            Map.start: _MF.unix_to_date(starttime),
            Map.interval: interval,
            Map.id: self.get_id(),
            'child_id': child.get_id(),
            'child_n_trade': child.get_nb_trade(),
            Map.pair: pair,
            Map.roi: _MF.rate_to_str(stg_roi),
            'roi_after': _MF.rate_to_str(stg_roi_after),
            'fee': fee,
            'fee_after': fee_after,
            'initial_capital': initial_capital,
            'actual_capital': actual_capital,
            'fee_initial_capital_rate': _MF.rate_to_str(fee_initial_capital_rate),
            'fee_initial_capital_rate_after': _MF.rate_to_str(fee_initial_capital_rate_after),
            'fee_actual_capital_rate': _MF.rate_to_str(fee_actual_capital_rate),
            'has_position_before': has_position_before,
            'keep_stg': keep_stg,
            'has_position_after': has_position_after,
            Map.close: closes[-1]
            }]
        self._save_moves(rows)
        self._reset_thread_manage_trade(pair)

    def _add_streams_periods(self) -> list:
        return [
            self.get_period(),
            self.get_strategy_params().get(Map.period),
            Wallet.get_period(),
            *self.CHILD_STRATEGY.get_periods_required()
        ]

    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> Tuple[bool, dict]:
        pair = market_price.get_pair()
        # Big
<<<<<<< HEAD
<<<<<<< HEAD
        big_period = self.CHILD_STRATEGY.MARKETPRICE_BUY_BIG_PERIOD
        big_marketprice = self._get_market_price(broker, pair, big_period)
<<<<<<< HEAD
        # min
        min_period = self.CHILD_STRATEGY.get_min_period()
        min_marketprice = self._get_market_price(broker, pair, min_period)
        child_ok, child_datas = self.CHILD_STRATEGY.can_buy(market_price, big_marketprice, min_marketprice)
=======
=======
        # big_period = self.CHILD_STRATEGY.MARKETPRICE_BUY_BIG_PERIOD
        # big_marketprice = self._get_market_price(broker, pair, big_period)
>>>>>>> Icarus-v13.1.4
        # little
        # little_period = self.CHILD_STRATEGY.MARKETPRICE_BUY_LITTLE_PERIOD
        # little_marketprice = self._get_market_price(broker, pair, little_period)
        # min
        min_period = self.CHILD_STRATEGY.get_min_period()
        min_marketprice = self._get_market_price(broker, pair, min_period)
<<<<<<< HEAD
        child_ok, child_datas = self.CHILD_STRATEGY.can_buy(market_price, big_marketprice, little_marketprice, min_marketprice)
>>>>>>> Icarus-v11.3.2
=======
        # min
        min_period = self.CHILD_STRATEGY.get_min_period()
        min_marketprice = self._get_market_price(broker, pair, min_period)
        child_ok, child_datas = self.CHILD_STRATEGY.can_buy(market_price, min_marketprice)
>>>>>>> Icarus-v13.1.3
=======
        child_ok, child_datas = self.CHILD_STRATEGY.can_buy(market_price, min_marketprice)
>>>>>>> Icarus-v13.1.4
        eligible = child_ok
        # Repport
        key = self._eligible.__name__
        repport = {
            f'{key}.child_time': _MF.unix_to_date(market_price.get_time()),
            f'{key}.pair': pair,
            f'{key}.eligible': eligible,
            f'{key}.child_ok': child_ok,
            f'{key}.child_period': market_price.get_period_time(),
            **child_datas
        }
        repport_formated = self._format_stalk(Map(repport))
        return eligible, repport_formated

    def _format_stalk(self, repport: Map) -> dict:
        # Repport
        key = self.CHILD_STRATEGY._can_buy_indicator.__name__
        indicator_datas = {
            f'{key}.can_buy_indicator': None,
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.histogram_switch_positive': None,
=======
            f'{key}.price_switch_up': None,
            f'{key}.supertrend_rising': None,
            f'{key}.min_macd_histogram_switch_up': None,

            f'{key}.price_change_1': None,
            f'{key}.price_change_2': None,

            f'{key}.mean_candle_change_60_mean_positive_candle': None,

>>>>>>> Icarus-v13.1.4
            f'{key}.closes[-1]': None,
            f'{key}.opens[-1]': None,
            f'{key}.min_closes[-1]': None,
            f'{key}.min_opens[-1]': None,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.big_closes[-1]': None,
            f'{key}.histogram[-1]': None,
            f'{key}.histogram[-2]': None
=======
            f'{key}.price_switch_up': None,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.price_above_prev_high': None,
=======
            f'{key}.macd_histogram_positive': None,
<<<<<<< HEAD
            f'{key}.little_edited_macd_histogram_positive': None,
            f'{key}.edited_macd_histogram_positive': None,
            f'{key}.close_3_bellow_keltner_middle_3': None,
>>>>>>> Icarus-v11.1.13
=======
            f'{key}.close_above_high_2': None,
>>>>>>> Icarus-v11.1.5
=======
            f'{key}.price_change_1_above_2': None,
<<<<<<< HEAD
            f'{key}.min_macd_signal_peak_nearest_than_min': None,
            f'{key}.tangent_min_macd_positive': None,
>>>>>>> Icarus-v11.3.2
=======
            f'{key}.edited_min_macd_histogram_positive': None,
>>>>>>> Icarus-v11.3.3
=======
            f'{key}.edited_macd_above_peak': None,
            f'{key}.rsi_above_peak_macd_posive_histogram': None,
>>>>>>> Icarus-v11.4.4

            f'{key}.switch_up_price_change_2': None,
            f'{key}.switch_up_price_change_3': None,

            f'{key}.above_prev_high_price_change_2': None,

            f'{key}.close_above_high_2_price_change_2': None,

            f'{key}.min_macd_signal_peak_date': None,
            f'{key}.min_macd_signal_min_date': None,

            f'{key}.rsi_above_peak_start_interval': None,
            f'{key}.rsi_above_peak_peak_date': None,
            f'{key}.rsi_above_peak_rsi_peak': None,

            f'{key}.closes[-1]': None,
            f'{key}.opens[-1]': None,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            f'{key}.highs[-1]': None,
=======
            f'{key}.highs[-1]': None,
            f'{key}.highs[-2]': None,
>>>>>>> Icarus-v11.1.5
            f'{key}.big_closes[-1]': None
>>>>>>> Icarus-v11.1.1
=======
            f'{key}.big_closes[-1]': None,
            f'{key}.macd[-1]': None,
            f'{key}.signal[-1]': None,
            f'{key}.histogram[-1]': None,
<<<<<<< HEAD
            f'{key}.little_edited_macd_histogram[-1]': None,
            f'{key}.edited_macd_histogram_positive[-1]': None,
=======
>>>>>>> Icarus-v13.1.3
            f'{key}.keltner_middle[-1]': None,
            f'{key}.keltner_middle[-2]': None,
            f'{key}.keltner_middle[-3]': None
>>>>>>> Icarus-v11.1.13
=======
            f'{key}.big_closes[-1]': None,
            f'{key}.min_macd_signal[-1]': None,
            f'{key}.min_macd[-1]': None,
            f'{key}.min_macd[-2]': None
>>>>>>> Icarus-v11.3.2
=======
            f'{key}.big_closes[-1]': None,
            f'{key}.min_edited_histogram[-1]': None,
>>>>>>> Icarus-v11.3.3
=======
            f'{key}.edited_macd[-1]': None,
            f'{key}.edited_signal[-1]': None,
            f'{key}.edited_histogram[-1]': None,
            f'{key}.min_edited_histogram[-1]': None,
            f'{key}.rsi[-1]': None
>>>>>>> Icarus-v11.4.4
=======
            # f'{key}.big_closes[-1]': None,
=======
            f'{key}.supertrend[-1]': None,
            f'{key}.supertrend[-2]': None,
<<<<<<< HEAD
>>>>>>> Icarus-v13.4.2
            f'{key}.min_keltner_middle[-1]': None
>>>>>>> Icarus-v13.1.4
=======
            f'{key}.min_histogram[-1]': None,
            f'{key}.min_histogram[-2]': None
>>>>>>> Icarus-v13.5
        }
        # Repport
        key = self.CHILD_STRATEGY.can_buy.__name__
        child_datas = {
            f'{key}.indicator': None,
            **indicator_datas
        }
        # Repport
        key = self._eligible.__name__
        canvas = {
            f'{key}.child_time': None,
            f'{key}.pair': None,
            f'{key}.eligible': None,
            f'{key}.child_ok': None,
            f'{key}.child_period': None,
            **child_datas
        }
        content = {key: repport.get(key) for key in canvas}
        return content

    def _reset_next_reset_allowed_pair(self) -> None:
        interval = self._RESET_INTERVAL_ALLOWED_PAIR
        unix_time = _MF.get_timestamp()
        self.__next_reset_allowed_pair = _MF.round_time(unix_time, interval) + interval

    def get_next_reset_allowed_pair(self) -> int:
        """
        To get the next time that the allowed pair to trade must be reset
        """
        return self.__next_reset_allowed_pair

    def _get_allowed_pairs(self, bkr: Broker) -> List[Pair]:
        # if (self._allowed_pairs is None) or (_MF.get_timestamp() >= self.get_next_reset_allowed_pair()):
        # if self._allowed_pairs is None:
        #     allowed_pairs = self.CHILD_STRATEGY.best_pairs()
        #     self._set_allowed_pairs(allowed_pairs)
        #     self._reset_next_reset_allowed_pair()
        if self._allowed_pairs is None:
            spot_pairs = MarketPrice.get_spot_pairs(bkr.__class__.__name__, self.get_pair().get_right())
            self._set_allowed_pairs(spot_pairs)
            self._reset_next_reset_allowed_pair()
        return self._allowed_pairs

    @classmethod
    def _sort_stalk_marketprices(cls, marketprices: List[MarketPrice]) -> List[MarketPrice]:
        pair_to_variation = {}
        pair_to_marketprice = {}
        n_candle = cls.CHILD_STRATEGY.CANDLE_CHANGE_N_CANDLE
        # Get variation
        for marketprice in marketprices:
            closes = list(marketprice.get_closes())
>>>>>>> Icarus-test
            closes.reverse()
            pair_closes.put(closes, pair_str)
            # Prepare capital
            stg_roi = active_stg.get_roi(market_price)
            # Fee
            fee = active_stg.get_fee()
            initial_capital = active_stg._get_capital()
            actual_capital = active_stg.get_actual_capital_merged(market_price)
            fee_initial_capital_rate = fee / initial_capital
            fee_actual_capital = fee / actual_capital
            # Trade
            active_stg._update_orders(bkr, market_price)
            has_position_before = active_stg._has_position()
            keep_stg = (active_stg.get_nb_trade() == 0) or has_position_before
            active_stg.trade(bkr) if keep_stg else None
            has_position_after = active_stg._has_position() if keep_stg else None
            if keep_stg and has_position_after:
                print(f"{_MF.prefix()}" + _color_green + f"Pair {pair_str.upper()} trade with SUCCESS." + _normal)
            else:
                active_stg.stop_trading(bkr)
                self._delete_active_strategy(bkr, pair)
                last_exec_order = active_stg._get_orders().get_last_execution()
                self._blacklist_pair(pair, stg_period) \
                    if (last_exec_order is not None) and (last_exec_order.get_type() != Order.TYPE_MARKET) else None
                pairs_to_delete.append(pair_str)
                print(f"{_MF.prefix()}" + _color_red + f"Pair {pair_str.upper()} is DELETED." + _normal)
            # Print
            stg_roi_after = active_stg.get_roi(market_price)
            fee_after = active_stg.get_fee()
            fee_initial_capital_rate_after = fee_after / initial_capital
            row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
                'child_id': active_stg.get_id(),
                Map.pair: pair,
                Map.roi: _MF.rate_to_str(stg_roi),
                'roi_after': _MF.rate_to_str(stg_roi_after),
                'fee': fee,
                'fee_after': fee_after,
                'initial_capital': initial_capital,
                'actual_capital': actual_capital,
                'fee_initial_capital_rate': _MF.rate_to_str(fee_initial_capital_rate),
                'fee_initial_capital_rate_after': _MF.rate_to_str(fee_initial_capital_rate_after),
                'fee_actual_capital': _MF.rate_to_str(fee_actual_capital),
                'has_position_before': has_position_before,
                'keep_stg': keep_stg,
                'has_position_after': has_position_after,
                'market_trend': market_trend,
                Map.close: closes[-1]
            }
            rows.append(row)
        self._save_state(pair_closes, pairs_to_delete, market_trend, market_analyse)
        self._save_moves(rows) if len(rows) > 0 else None

    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> bool:
        pair = market_price.get_pair()
        child_period = self.get_strategy_params().get(Map.period)
        child_market_price = self._get_market_price(broker, pair, child_period)
        return Icarus.stalker_can_add(market_price) and Icarus.can_buy(child_market_price)

    @staticmethod
    def generate_strategy(stg_class: str, params: Map) -> 'IcarusStalker':
        pair = params.get(Map.pair)
        maximum = params.get(Map.maximum)
        capital = params.get(Map.capital)
        right_symbol = pair.get_right().get_symbol()
        new_params = Map({
            Map.pair: pair,
            Map.maximum: Price(maximum, right_symbol) if maximum is not None else None,
            Map.capital: Price(capital, right_symbol),
            Map.rate: params.get(Map.rate),
            Map.period: params.get(Map.period),
            Map.strategy: params.get(Map.strategy),
            Map.param: params.get(Map.param)
        })
        return IcarusStalker(new_params)

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = IcarusStalker(Map({
            Map.pair: Pair('@json/@json'),
            Map.maximum: None,
            Map.capital: 0,
            Map.rate: 1,
            Map.strategy: '@json',
            Map.period: 0,
            Map.param: {
                Map.maximum: None,
                Map.capital: 0,
                Map.rate: 1,
                Map.period: 0,
            }
        }))
        exec(MyJson.get_executable())
        return instance
