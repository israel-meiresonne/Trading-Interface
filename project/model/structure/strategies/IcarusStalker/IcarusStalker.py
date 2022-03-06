from typing import List, Tuple
from config.Config import Config
from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Icarus.Icarus import Icarus
from model.structure.strategies.StalkerClass import StalkerClass
from model.structure.strategies.TraderClass import TraderClass
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Order import Order
from model.tools.Pair import Pair
from model.tools.Predictor import Predictor
from model.tools.Price import Price
from model.tools.Wallet import Wallet


class IcarusStalker(StalkerClass):
    _CONST_MAX_STRATEGY = 5
    _STALKER_BOT_SLEEP_TIME = 1  # in second
    _PAIR_FILTER_MEAN = 40/100
    _PAIR_FILTER_100 = 20/100

    def __init__(self, params: Map):
        """
        Constructor\n
        :param params: params
               params[*]:   {Stalker.__init__()}    # Same structure
        """
        super().__init__(params)
        self.__last_reset_allowed_pair = None

    def _manage_trade(self, bkr: Broker, child: TraderClass) -> None:
        starttime = _MF.get_timestamp()
        _cls = self
        _normal = _cls._TO_REMOVE_STYLE_NORMAL
        _color_black = _cls._TO_REMOVE_STYLE_BLACK
        _color_cyan = _cls._TO_REMOVE_STYLE_CYAN
        _color_green = _cls._TO_REMOVE_STYLE_GREEN
        _color_purple = _cls._TO_REMOVE_STYLE_PURPLE
        _color_red = _cls._TO_REMOVE_STYLE_RED
        _color_yellow = _cls._TO_REMOVE_STYLE_YELLOW
        _back_cyan = _cls._TO_REMOVE_STYLE_BACK_CYAN

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
            last_exec_order = child._get_orders().get_last_execution()
            blacklist = (stg_roi < 0) or ((last_exec_order is not None) and (last_exec_order.get_type() != Order.TYPE_MARKET)) 
            self._blacklist_pair(pair, stg_period) if blacklist else None
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
            Wallet.get_period()
        ]

    def _eligible(self, market_price: MarketPrice, broker: Broker = None) -> Tuple[bool, dict]:
        pair = market_price.get_pair()
        child_ok, child_datas = Icarus.can_buy(market_price)
        eligible = child_ok
        # Repport
        key = IcarusStalker._eligible.__name__
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
        key = Icarus._can_buy_indicator.__name__
        indicator_datas = {
            f'{key}.can_buy_indicator': None,
            f'{key}.macd_switch_up': None,
            f'{key}.rsi_reached': None,
            f'{key}.rsi_trigger': None,
            f'{key}.closes[-1]': None,
            f'{key}.closes[-2]': None,
            f'{key}.closes[-3]': None,
            f'{key}.histogram[-1]': None,
            f'{key}.histogram[-2]': None,
            f'{key}.histogram[-3]': None,
            f'{key}.macd[-1]': None,
            f'{key}.macd[-2]': None,
            f'{key}.macd[-3]': None,
            f'{key}.rsi[-1]': None,
            f'{key}.rsi[-2]': None,
            f'{key}.rsi[-3]': None
        }
        # Repport
        key = Icarus.can_buy.__name__
        child_datas = {
            f'{key}.indicator': None,
            **indicator_datas
        }
        # Repport
        key = IcarusStalker._eligible.__name__
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

    def _reset_last_reset_allowed_pair(self) -> int:
        interval = Icarus.get_predictor_period()
        unix_time = _MF.get_timestamp()
        self.__last_reset_allowed_pair = _MF.round_time(unix_time, interval)

    def get_last_reset_allowed_pair(self) -> int:
        """
        To get last time that the pair to stalk have been reseted
        """
        return self.__last_reset_allowed_pair

    def _get_allowed_pairs(self, bkr: Broker) -> List[Pair]:

        if self._allowed_pairs is None:
            if Config.get_stage() == Config.STAGE_1:
                allowed_pairs = MarketPrice.history_pairs(bkr.__class__.__name__, active_path=True)
            else:
                right_asset = self.get_pair().get_right()
                allowed_pairs = MarketPrice.get_spot_pairs(bkr.__class__.__name__, right_asset)
            self._allowed_pairs = allowed_pairs
        return self._allowed_pairs

    @staticmethod
    def get_bot_sleep_time() -> int:
        return IcarusStalker._STALKER_BOT_SLEEP_TIME

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
        pair = Pair('?/json')
        instance = IcarusStalker(Map({
            Map.pair: pair,
            Map.maximum: None,
            Map.capital: Price(1, pair.get_right()),
            Map.rate: 1,
            Map.strategy: 'IcarusStalker',
            Map.period: 0,
            Map.param: {
                Map.maximum: None,
                Map.capital: 0,
                Map.rate: 1,
                Map.period: 0
            }
        }))
        exec(MyJson.get_executable())
        return instance
