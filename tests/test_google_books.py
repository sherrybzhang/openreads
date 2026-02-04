import json
import pytest

from app.services.google_books import BookQuery, retrieve_book


class DummyResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_retrieve_book_invalid_isbn_returns_fallback_json():
    result = retrieve_book("bad-isbn", BookQuery.JSON)
    payload = json.loads(result)
    assert payload["error"]
    assert payload["review_count"] == 0


def test_retrieve_book_valid_isbn_uses_api(monkeypatch):
    def fake_get(url, params, timeout):
        return DummyResponse(
            200,
            {
                "items": [
                    {
                        "volumeInfo": {
                            "title": "Example",
                            "authors": ["Alice"],
                            "publishedDate": "2020-01-01",
                            "averageRating": 4.5,
                            "ratingsCount": 12,
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr("app.services.google_books.requests.get", fake_get)
    result = retrieve_book("9780132350884", BookQuery.JSON)
    payload = json.loads(result)
    assert payload["title"] == "Example"
    assert payload["average_rating"] == 4.5
    assert payload["review_count"] == 12
