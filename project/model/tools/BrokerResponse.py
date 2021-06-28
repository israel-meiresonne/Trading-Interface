from json import loads as json_loads
from requests import Response

from model.tools.MyJson import MyJson
from model.tools.RequestResponse import RequestResponse


class BrokerResponse(RequestResponse, MyJson):
    def __init__(self, rsp: Response):
        RequestResponse.__init__(self, rsp)

    def get_content(self) -> [list, dict]:
        return json_loads(super(BrokerResponse, self).get_content())

    @staticmethod
    def json_instantiate(object_dic: dict) -> object:
        _class_token = MyJson.get_class_name_token()
        instance = BrokerResponse(Response())
        exec(MyJson.get_executable())
        return instance
