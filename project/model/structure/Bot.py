from time import sleep
from model.structure.database.ModelFeature import ModelFeature
from model.structure.Broker import Broker
from model.structure.Strategy import Strategy
from model.tools.Map import Map
from model.tools.Paire import Pair


class Bot(ModelFeature):
    SEPARATOR = "-"

    def __init__(self, bkr: str, stg: str, prcd: str, cfgs: dict):
        """
        To create a new Bot\n
        :param bkr: name of a supported Broker
        :param stg: name of a supported Strategy
        :param prcd: code of the pair to Trade, i.e.: "BTC/USDT"
        :param cfgs: holds additional configs for the Bot
                    cfgs[{Bot}]    => Bot configs
                    cfgs[{Broker}] => Broker configs
        """
        self.__id = Bot._generate_id(bkr, stg, prcd)
        self.__broker = Broker.retrieve(bkr, cfgs[bkr])
        self.__strategy = Strategy.retrieve(stg)
        self.__pair = Pair(prcd)

    def get_id(self) -> str:
        return self.__id

    def _get_broker(self) -> Broker:
        return self.__broker

    def _get_strategy(self) -> Strategy:
        return self.__strategy

    def _get_pair(self) -> Pair:
        return self.__pair

    def start(self) -> None:
        """
        To start trade
        """
        bkr = self._get_broker()
        stg = self._get_strategy()
        end = False
        print("Bot started to trade...")
        mkt_prc = {
            Map.symbol: self._get_pair().get_merged_symbols().upper(),
            Map.interval: "1m",
            Map.startTime: None,
            Map.endTime: None,
            Map.limit: 3
        }
        while not end:
            mkpc = bkr.get_market_price(mkt_prc)
            print("——————————————\n|Market price|\n——————————————")
            print(mkpc.get_market())
            odr = stg.get_order(mkpc)
            odr_rsp = bkr.execute(odr)
            print("————————————————\n|Order response|\n————————————————", odr_rsp.__str__())
            nxtm = bkr.get_next_trade_time()
            print(f"Bot sleep for {nxtm}sec...")
            sleep(nxtm)
            end = self.__stillActive()

    def __stillActive(self) -> bool:
        print("still trading...")
        return False

    @staticmethod
    def _generate_id(bkr: str, stg: str, prsbl: str) -> str:
        return bkr.lower() + Bot.SEPARATOR + stg.lower() + Bot.SEPARATOR + prsbl.lower()
