from abc import abstractmethod
from typing import List

from model.structure.database.ModelFeature import ModelFeature as _MF
from model.tools.BrokerRequest import BrokerRequest
from model.tools.FileManager import FileManager
from model.tools.Map import Map
from model.tools.Order import Order
from config.Config import Config
from model.tools.Paire import Pair


class Broker(_MF):
    @abstractmethod
    def request(self, bkr_rq: BrokerRequest) -> None:
        """
        To submit a request to Broker's API\n
        :param bkr_rq: holds params for the request
        NOTE: The response is stored in the BrokerRequest
        """
        pass

    @abstractmethod
    def get_account_snapshot(self, bkr_rq: BrokerRequest) -> None:
        """
        To get a snapshot\n
        :param bkr_rq: holds params for the request
        :return: the result is stored the given BrokerRequest
        """
        pass

    @abstractmethod
    def get_market_price(self, bkr_rq: BrokerRequest) -> None:
        """
        To get the MarketPrice\n
        :param bkr_rq: holds parameters required
        """
        pass

    @abstractmethod
    def get_trade_fee(self, pair: Pair) -> Map:
        """
        To get trade fees of the given Pair from Binance's API\n
        :param pair: the pair to get the trade fees
        :return: trade fees of the given Pair
        """
        pass

    @staticmethod
    @abstractmethod
    def get_pairs(match: List[str] = None, no_match: List[str] = None) -> List[str]:
        """
        To get pairs available in Broker's API\n
        :param match: Include only pair that match this list of regex
        :param no_match: Exclude all pair that match this list of regex
        :return: Pairs available in Broker's API
        """
        pass

    @abstractmethod
    def execute(self, order: Order) -> None:
        """
        To submit Order to Broker's API\n
        :param order: the Order to execute
        """
        pass

    @abstractmethod
    def cancel(self, order: Order) -> None:
        """
        To cancel an Order\n
        :param order: the order to cancel
        """
        pass

    @abstractmethod
    def get_next_trade_time(self) -> int:
        """
        To get the time to wait before the next trade to avoid API ban\n
        :return: the time to wait before the next trade
        """
        pass

    @staticmethod
    @abstractmethod
    def list_paires() -> list:
        """
        To get all Pair that can be trade with the Broker\n
        :return: list of available Broker
        """
        pass

    @staticmethod
    def list_brokers():
        """
        To get all available Broker\n
        :return: list of available Broker
        """
        p = Config.get(Config.DIR_BROKERS)
        return FileManager.get_dirs(p, False)

    @staticmethod
    def retrieve(bkr: str, configs: Map):
        """
        To get access to a Broker\n
        :param bkr: name of a supported Broker
        :param configs: additional configs for the Broker
        :return: access to a Broker
        """
        exec("from model.API.brokers."+bkr+"."+bkr+" import "+bkr)
        return eval(bkr+"(configs)")

    @staticmethod
    def generate_broker_request(broker_class: str, request_enum: str, request_params: Map) -> BrokerRequest:
        """
        To generate a new BrokerRequest\n
        :param broker_class: Class name of the Broker where the request will be submitted
        :param request_enum: Name of the request (enum from BrokerRequest.RQ_{*} )
        :param request_params: Params of the request
        :return: an instance of BrokerRequest's children (i.e: BinanceRequest, KrakenRequest, etc...)
        """
        _bkr_rq_cls = BrokerRequest.get_request_class(broker_class)
        exec(f"from model.API.brokers.{broker_class}.{_bkr_rq_cls} import {_bkr_rq_cls}")
        bkr_rq = eval(_bkr_rq_cls + f"('{request_enum}', request_params)")
        return bkr_rq

    @staticmethod
    def _extract_market_historic(bkr: 'Broker', pair: Pair, periods: List[int], start_time: int, end_time: int) -> Map:
        max_nb_prd = 1000
        min_interval = 60
        periods.sort()
        start_rounded = _MF.round_time(start_time, 60 * 60)
        end_rounded = _MF.round_time(end_time, 60 * 60)
        historics = Map()
        interval = end_rounded - start_rounded
        rq_params = Map({
            Map.pair: pair,
            Map.period: None,
            Map.begin_time: None,
            Map.end_time: None,
            Map.number: None
        })
        for period in periods:
            index_time = end_rounded
            market_rows = []
            nb_full_tour = int(interval / period / max_nb_prd)
            nb_stilling_prd = int((interval % (period * max_nb_prd)) / period)
            rq_params.put(period, Map.period)
            for i in range(nb_full_tour):
                rq_end_time = index_time
                index_time -= max_nb_prd * period
                rq_start_time = index_time
                market_list = Broker._get_market_list(bkr, rq_params, rq_start_time, rq_end_time, max_nb_prd)
                market_rows = [*market_rows, *market_list]
            if nb_stilling_prd > 0:
                rq_end_time = index_time
                index_time -= nb_stilling_prd * period
                rq_start_time = index_time
                market_list = Broker._get_market_list(bkr, rq_params, rq_start_time, rq_end_time, nb_stilling_prd)
                market_rows = [*market_rows, *market_list]
            market_mapped = Map({int(row[0]/1000): row for row in market_rows})
            market_mapped.sort()
            # Broker._check_intervals(period, market_mapped)
            historics.put(market_mapped.get_map(), period)
        completed_hist = Map({period: [rows[next(iter(rows))]] for period, rows in historics.get_map().items()})
        index_time = start_rounded + min_interval
        print("Completing historic...")
        while index_time < end_rounded:
            to_extract = [period for period in periods if index_time % period == 0]
            to_repport = [period for period in periods if period not in to_extract]
            for period in to_extract:   # 1622538000
                # row = historics.get_map()[period][index_time] # 1613014860 don't exist
                if index_time in historics.get(period):
                    # row = historics.get(period, index_time)
                    row = historics.get_map()[period][index_time]
                    completed_hist.get(period).append(row)
                else:
                    to_repport.append(period)
            for period in to_repport:
                rows = completed_hist.get_map()[period]
                row = rows[-1]
                rows.append(row)
            index_time += min_interval
        return completed_hist

    @staticmethod
    def _check_intervals(period: int, market_mapped: Map) -> None:
        open_times = market_mapped.get_keys()
        for i in range(1, len(market_mapped.get_map())):
            interval = open_times[i] - open_times[i - 1]
            if period != interval:
                raise Exception(f"Interval between open time must be the same ('{period}'), "
                                f"instead '{open_times[i]}' - '{open_times[i - 1]}' = '{interval}'")

    @staticmethod
    def _get_market_list(bkr: 'Broker', rq_params: Map, rq_start_time: int, rq_end_time: int, nb_period: int) -> list:
        from time import sleep
        pair_str = rq_params.get(Map.pair).__str__().upper()
        period_str = f"{int(rq_params.get(Map.period)/60)}min."
        print(f"Get historic ('{pair_str}', '{period_str}'): "
              f"'{_MF.unix_to_date(rq_start_time)}'->'{_MF.unix_to_date(rq_end_time)}' for '{nb_period}' periods")
        rq_params.put(rq_start_time, Map.begin_time)
        rq_params.put(rq_end_time, Map.end_time)
        rq_params.put(nb_period, Map.number)
        bkr_rq = Broker.generate_broker_request(bkr.__class__.__name__, BrokerRequest.RQ_MARKET_PRICE, rq_params)
        max_error = 60
        nb_error = 0
        sleep_time = 30
        success = False
        while (not success) and (nb_error < max_error):
            try:
                bkr.request(bkr_rq)
                success = True
            except Exception as e:
                nb_error += 1
                print(e.__str__())
                print(f"sleep for '{sleep_time}sec.'")
                sleep(sleep_time)
        market_price = bkr_rq.get_market_price()
        market_list = list(market_price.get_market())
        market_list.reverse()
        return market_list

    @staticmethod
    def print_market_historic(bkr: 'Broker', pair: Pair, periods: List[int], start_time: int, end_time: int) -> None:
        # Get Historic
        min_period = 60
        periods.insert(0, min_period) if min_period not in periods else None
        hsitoric = Broker._extract_market_historic(bkr, pair, periods, start_time, end_time)
        # Print Historic
        _PRINT_SUCCESS = '🖨 File printed ✅'
        original_path = Config.get(Config.DIR_PRINT_HISTORIC)
        _bkr_cls = bkr.__class__.__name__
        unix_time = _MF.get_timestamp()
        merged_pair = pair.get_merged_symbols().upper()
        date_format = '%Y-%m-%d_%H.%M.%S'
        file_date = f"{_MF.unix_to_date(start_time, date_format)}->{_MF.unix_to_date(end_time, date_format)}"
        prepared_path = original_path.replace('$broker', _bkr_cls).replace('$pair_ref', f"{merged_pair}%{file_date}").replace('$pair', merged_pair)
        interval = end_time - start_time
        for period, datas_rows in hsitoric.get_map().items():
            final_path = prepared_path.replace('$period', str(period * 1000))
            rows = [{i: datas[i] for i in range(len(datas))} for datas in datas_rows]
            fields = list(rows[0].keys())
            FileManager.write_csv(final_path, fields, rows, make_dir=True)
            print(f"{_PRINT_SUCCESS}: period ('{merged_pair}'): '{int(period/60)}min.'")
        # Print config file
        config_path = prepared_path.replace('$period', 'config')
        day = int(interval/(3600*24))
        hour = int((interval % (3600*24)) / 3600)
        minute = int(((interval % (3600*24)) % 3600) / 60)
        second = ((interval % (3600*24)) % 3600) % 60
        interval_txt = f"{day}day.{hour}hour.{minute}min.{second}sec."
        config_rows = [{
            Map.date: _MF.unix_to_date(unix_time),
            Map.broker: _bkr_cls,
            Map.pair: pair.__str__().upper(),
            f"{Map.period}[min.]": _MF.json_encode([int(period/60) for period in periods]),
            Map.start_time: _MF.unix_to_date(start_time),
            Map.end_time: _MF.unix_to_date(end_time),
            Map.interval: interval_txt
        }]
        FileManager.write_csv(config_path, list(config_rows[0].keys()), config_rows)
        print(f"{_PRINT_SUCCESS}: config.csv")

