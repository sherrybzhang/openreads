from flask import render_template

from app import app


def test_home_page_has_skip_link_and_main_landmark() -> None:
    app.testing = True
    client = app.test_client()
    response = client.get("/")

    html = response.get_data(as_text=True)

    assert 'href="#main-content"' in html
    assert 'id="main-content"' in html
    assert "<title>OpenReads | Create Account</title>" in html


def test_search_page_has_labeled_results_select() -> None:
    with app.test_request_context("/search"):
        html = render_template(
            "search.html",
            page_title="OpenReads | Search Books",
            message=None,
            form_data={"isbn": "", "title": "", "author": ""},
            books=[
                {
                    "isbn": "1234567890",
                    "title": "Example Book",
                    "year": 2024,
                    "author": "Example Author",
                }
            ],
        )

    assert '<label for="book">Choose a book</label>' in html
    assert 'id="book"' in html


def test_home_page_renders_username_error_below_input() -> None:
    with app.test_request_context("/"):
        html = render_template(
            "home.html",
            page_title="OpenReads | Create Account",
            message=None,
            form_data={"username": "taken_name"},
            field_errors={"username": "Username is already taken."},
        )

    assert 'aria-describedby="username-error"' in html
    assert 'id="username-error"' in html
    assert "Username is already taken." in html


def test_sign_in_page_renders_password_error_below_input() -> None:
    with app.test_request_context("/sign-in"):
        html = render_template(
            "sign-in.html",
            page_title="OpenReads | Sign In",
            message=None,
            form_data={"username": "reader1"},
            field_errors={"password": "Username and/or password is incorrect."},
        )

    assert 'aria-describedby="password-error"' in html
    assert 'id="password-error"' in html
    assert "Username and/or password is incorrect." in html


def test_book_detail_rating_inputs_have_accessible_names() -> None:
    with app.test_request_context("/book"):
        html = render_template(
            "book-detail.html",
            page_title="OpenReads | Example",
            title="Example Book",
            author="Author Name",
            year=2024,
            isbn="1234567890",
            reviews=[],
            local_review_count=0,
            local_average_rating=None,
            review_text="",
            selected_rating="",
        )

    assert 'aria-label="5 stars"' in html
    assert 'type="hidden" name="isbn" value="1234567890"' in html
