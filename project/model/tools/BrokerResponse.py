from json import loads as json_loads
from requests import Response

from model.tools.RequestResponse import RequestResponse


class BrokerResponse(RequestResponse):
    def __init__(self, rsp: Response):
        RequestResponse.__init__(self, rsp)

    def get_content(self) -> [list, dict]:
        return json_loads(super(BrokerResponse, self).get_content())
