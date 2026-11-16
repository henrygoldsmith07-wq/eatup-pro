import json

from api.index import handler


class FakeRequest:
    def __init__(self, method="GET", url="http://localhost/api/v1/health", body=b"", headers=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self._body = body

    def get_data(self):
        return self._body


def test_handler_routes_api_requests():
    response = handler(FakeRequest())
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["status"] == "healthy"
    assert "Content-Security-Policy" in response["headers"]


def test_handler_preserves_query_strings():
    response = handler(FakeRequest(url="http://localhost/api/v1/analytics/trends?days=7"))
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["days_analyzed"] == 7
