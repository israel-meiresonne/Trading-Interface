from model.structure.Broker import Broker
from model.structure.database.ModelFeature import ModelFeature as _MF
from model.structure.strategies.Icarus.Icarus import Icarus
from model.structure.strategies.StalkerClass import StalkerClass
from model.tools.Map import Map
from model.tools.MarketPrice import MarketPrice
from model.tools.MyJson import MyJson
from model.tools.Pair import Pair
from model.tools.Price import Price


class IcarusStalker(StalkerClass):
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
            market_price = self._get_market_price(bkr, pair)
            # Prepare closes
            closes = list(market_price.get_closes())
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
            active_stg.trade(bkr)
            has_position = active_stg._has_position()
            if has_position:
                print(f"{_MF.prefix()}" + _color_green + f"Pair {pair_str.upper()} trade with SUCCESS." + _normal)
            else:
                active_stg.stop_trading(bkr)
                self._delete_active_strategy(bkr, pair)
                pairs_to_delete.append(pair_str)
                print(f"{_MF.prefix()}" + _color_red + f"Pair {pair_str.upper()} is DELETED." + _normal)
            # Print
            stg_roi_after = active_stg.get_roi(market_price)
            fee_after = active_stg.get_fee()
            fee_initial_capital_rate_after = fee_after / initial_capital
            row = {
                Map.date: _MF.unix_to_date(_MF.get_timestamp()),
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
                'has_position': has_position,
                'market_trend': market_trend,
                Map.close: closes[-1]
            }
            rows.append(row)
        self._save_state(pair_closes, pairs_to_delete, market_trend, market_analyse)
        self._save_moves(rows) if len(rows) > 0 else None

    @staticmethod
    def _eligible(market_price: MarketPrice) -> bool:
        """
        To check if a pair is interesting to trade\n
        :param market_price: Market price historic
        :return: True if pair is interesting else False
        """
        return Icarus.stalker_can_add(market_price) and Icarus.can_buy(market_price)

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
