from requests import Response


class RequestResponse:
    def __init__(self, rsp: Response):
        self.__response = rsp

    def get_status_code(self) -> int:
        return self.__response.status_code

    def get_url(self) -> str:
        return self.__response.url

    def get_headers(self) -> dict:
        return dict(self.__response.headers)

    def get_content(self) -> str:
        return self.__response.content.decode('utf-8')
