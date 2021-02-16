from model.tools.RequestResponse import RequestResponse


class Request:
    def __init__(self):
        self.__response = None

    def _get_response(self) -> RequestResponse:
        if self.__response is None:
            raise Exception("Request's response is not set")
        return self.__response

    def handle_response(self, rsp: RequestResponse) -> None:
        """
        To handle response returned after a request\n
        :param rsp: response returned after a request
        """
        self.__response = rsp
