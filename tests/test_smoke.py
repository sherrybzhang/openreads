from app import app


def test_index() -> None:
    app.testing = True
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_api_books_fetches_without_local_book_check(monkeypatch) -> None:
    app.testing = True
    client = app.test_client()

    def fake_retrieve_book(isbn: str, query: object) -> str:
        return (
            '{"title":"Example","author":"Alice","year":"2020","isbn":"'
            + isbn
            + '","average_rating":4.5,"review_count":12}'
        )

    monkeypatch.setattr("app.routes.retrieve_book", fake_retrieve_book)

    response = client.get("/api/books/9780132350884")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Example" in html
    assert "9780132350884" in html
