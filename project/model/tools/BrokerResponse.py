from json import loads as json_loads
from requests import Response

from model.tools.RequestResponse import RequestResponse


class BrokerResponse(RequestResponse):
    def __init__(self, rsp: Response):
        RequestResponse.__init__(self, rsp)

    def get_content(self) -> [list, dict]:
        return json_loads(super(BrokerResponse, self).get_content())

    def __str__(self):
        rsp = self._get_response()
        rsp_dict = rsp.__dict__.items()
        opt = "\n—————\n|Response|\n—————\n"
        for k, v in rsp_dict:
            opt += f"{k}: {v}\n"
            if k == "request":
                v_dict = v.__dict__
                opt += "*****\n|Response.request|\n*****\n"
                for v_k, v_v in v_dict.items():
                    opt += f"{v_k}: {v_v}\n"
                opt += "*****\n|END Response.request|\n*****\n"
        opt += "—————\n|END Response|\n—————"
        return opt
