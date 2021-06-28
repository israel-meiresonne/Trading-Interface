from model.tools.RequestResponse import RequestResponse


class Request:
    def __init__(self):
        self.__response = None
        self.__method = None
        self.__response = None
        self.__method = None
        self.__url = None
        self.__headers = None
        self.__body = None
        self.__hooks = None
        self.__body_position = None

    def _set_response(self, response: RequestResponse) -> None:
        request = response.get_request()
        self.__response = response
        self.__method = request.get('method')
        self.__url = response.get_url()
        # self.__headers = dict(request['headers'])
        self.__headers = request.get('headers')
        self.__body = request.get('body')
        self.__hooks = request.get('hooks')
        self.__body_position = request.get('_body_position')

    def _get_response(self) -> RequestResponse:
        if self.__response is None:
            raise Exception("Request's response is not set")
        return self.__response

    def handle_response(self, rsp: RequestResponse) -> None:
        """
        To handle response returned after a request\n
        :param rsp: response returned after a request
        """
        self._set_response(rsp)
