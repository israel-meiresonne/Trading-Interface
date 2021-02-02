from requests import Response

from model.tools.RequestResponse import RequestResponse


class BrokerResponse(RequestResponse):
    def __init__(self, rsp: Response):
        RequestResponse.__init__(self, rsp)
