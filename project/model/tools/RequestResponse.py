from requests import Response

from model.tools.Map import Map


class RequestResponse:
    STATUS_CODE_SUCCESS = 200

    def __init__(self, response: Response):
        self.__status_code = response.status_code
        self.__url = response.url
        self.__headers = dict(response.headers)
        self.__content = response.content.decode('utf-8') if response.content is not None else response.content
        response_dict = response.__dict__
        self.__content_consumed = response_dict['_content_consumed']
        self.__next = response_dict['_next']
        self.__encoding = response.encoding
        self.__history = response.history
        self.__reason = response.reason
        self.__elapsed = response.elapsed.total_seconds()
        self.__request = None
        self._set_request(response)

    def _set_request(self, response: Response) -> None:
        request = response.request
        if request is not None:
            request_map = Map(request) if isinstance(request, dict) else Map(request.__dict__)
            keys = request_map.get_keys()
            if '_cookies' in keys:
                del request_map.get_map()['_cookies']
            if 'headers' in keys:
                new_headers = dict(request_map.get('headers'))
                request_map.put(new_headers, 'headers')
        else:
            request_map = Map()
        self.__request = request_map

    def _get_response(self) -> 'RequestResponse':
        # return self.__response
        return self

    def get_status_code(self) -> int:
        return self.__status_code

    def get_url(self) -> str:
        return self.__url

    def get_headers(self) -> dict:
        return self.__headers

    def get_content(self) -> str:
        return self.__content

    def get_request(self) -> Map:
        return self.__request

    def __str__(self):
        rsp_dict = self.__dict__
        opt = "\n—————\n|Response|\n—————\n"
        for k, v in rsp_dict.items():
            opt += f"{k}: {v}\n"
            if k == "request":
                v_dict = v
                opt += "*****\n|Response.request|\n*****\n"
                for v_k, v_v in v_dict.items():
                    opt += f"{v_k}: {v_v}\n"
                opt += "*****\n|END Response.request|\n*****\n"
        opt += "—————\n|END Response|\n—————"
        return opt
