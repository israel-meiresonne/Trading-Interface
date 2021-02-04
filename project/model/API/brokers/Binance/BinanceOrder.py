from model.structure.database.ModelFeature import ModelFeature
from model.API.brokers.Binance.BinanceAPI import BinanceAPI
from model.tools.Map import Map
from model.tools.Order import Order


class BinanceOrder(Order):
    def __init__(self, tp: str, params) -> None:
        super().__init__(tp, params)
        self.__type = tp
        self.__api_request = None
        eval(f"self.{tp}(params)")

    def __set_api_request(self, rq: str) -> None:
        self.__api_request = rq

    def get_api_request(self) -> str:
        return self.__api_request

    def _set_market(self, params: dict) -> None:
        """
        To set Order for a market Order\n
        :param params: params to make a market Order
        """
        mkt_prms = self._extract_market_params(params)
        self.__set_api_request(self._exract_market_request(mkt_prms))
        self._set_params(mkt_prms)

    def _extract_market_params(self, params: dict) -> dict:
        """
        To extract params required for a market Order\n
        :param params: where to extract params for a market Order
        :return: params required for a market Order
                        params[Map.symbol]              => {str}
                        params[Map.side]                => {str}
                        params[Map.type]                => "MARKET"
                        params[Map.quantity]            => {float}
                        params[Map.quoteOrderQty]       => {float}
                        params[Map.newClientOrderId]    => {str|None}
                        params[Map.recvWindow]          => {int|None}
        """
        # check keys
        ks = [Map.pair, Map.move, Map.market]
        rtn = ModelFeature.keys_exist(ks, params)
        if rtn is not None:
            raise ValueError(f"This param '{rtn}' is required to make a market Order")
        # check Pair and Price symbols
        prc = params[Map.market]
        prc_sbl = prc.get_asset().get_symbol()
        pr = params[Map.pair]
        pr_l_sbl = pr.get_left().get_symbol()
        pr_r_sbl = pr.get_right().get_symbol()
        if (prc_sbl != pr_l_sbl) and (prc_sbl != pr_r_sbl):
            raise ValueError(f"Price's symbol '{prc_sbl.upper()}' "
                             f"must match Pair's left '{pr_l_sbl}' or right '{pr_r_sbl}' asset")
        if (params[Map.move] != self.MOVE_BUY) and (params[Map.move] != self.MOVE_SELL):
            raise ValueError(f"This move '{params[Map.move]}' is not supported")
        # convert
        mkt_prms = {
            Map.symbol: pr.get_merged_symbols(),
            Map.side: BinanceAPI.SIDE_BUY if params[Map.move] == self.MOVE_BUY else BinanceAPI.SIDE_SELL,
            Map.type: BinanceAPI.TYPE_MARKET,
            Map.newClientOrderId: None,
            Map.recvWindow: None
        }
        if prc_sbl == pr_l_sbl:
            mkt_prms[Map.quantity] = prc.get_value()
        else:
            mkt_prms[Map.quoteOrderQty] = prc.get_value()
        return mkt_prms

    def _exract_market_request(self, params: dict) -> str:
        if (Map.quantity in params) and (Map.quoteOrderQty in params):
            raise ValueError(f"Params '{Map.quantity}' or '{Map.quoteOrderQty}' can't both be set")
        if Map.quantity in params:
            rq = BinanceAPI.RQ_ORDER_MARKET_qty
        elif Map.quoteOrderQty in params:
            rq = BinanceAPI.RQ_ORDER_MARKET_amount
        else:
            raise ValueError(f"Params '{Map.quantity}' or '{Map.quantity}' must be set")
        return rq

    def _set_limit(self, params: dict) -> None:
        pass

    def _set_stop(self, params: dict) -> None:
        pass

    def generate_order(self) -> dict:
        prms = self._get_params()
        prms[Map.symbol] = prms[Map.symbol].upper()
        prms[Map.side] = prms[Map.side].upper()
        return ModelFeature.clean(prms)
