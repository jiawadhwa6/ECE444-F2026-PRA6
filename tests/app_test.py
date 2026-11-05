import os
import pytest
from pathlib import Path

from project.app import app, db
import json
from project.models import Post

TEST_DB = "test.db"


@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()  # setup
        yield app.test_client()  # tests run here
        db.drop_all()  # teardown


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """initial test. ensure that the database exists"""
    tester = Path("test.db").is_file()
    assert tester


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data

def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get('/delete/1')
    data = json.loads(rv.data)
    assert data["status"] == 1

def add_post(client, title, text):
    """Helper: log in and add one post."""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post("/add", data=dict(title=title, text=text), follow_redirects=True)
    logout(client)


def test_search_page_loads(client):
    """Search page with no query renders and shows no posts."""
    rv = client.get("/search/")
    assert rv.status_code == 200
    assert b'class="entry"' not in rv.data


def test_search_matches_title(client):
    add_post(client, "Flask tips", "blueprints are useful")
    add_post(client, "Cooking", "pasta needs salt")
    rv = client.get("/search/?query=flask")
    assert b"Flask tips" in rv.data
    assert b"Cooking" not in rv.data


def test_search_matches_text(client):
    add_post(client, "Cooking", "pasta needs salt")
    rv = client.get("/search/?query=salt")
    assert b"Cooking" in rv.data




def test_delete_requires_login(client):
    """Logged-out delete returns 401 and the post is NOT removed."""
    add_post(client, "keep me", "should survive")
    rv = client.get("/delete/1")
    assert rv.status_code == 401
    assert db.session.get(Post, 1) is not None


def test_delete_removes_post_when_logged_in(client):
    """Logged-in delete actually removes the row from the database."""
    add_post(client, "temporary", "delete me")
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    assert json.loads(rv.data)["status"] == 1
    assert db.session.get(Post, 1) is None
# from project.app import app, init_db
# from pathlib import Path

# def test_index():
#     tester = app.test_client()
#     response = tester.get("/", content_type="html/text")

#     assert response.status_code == 200
#     assert response.data == b"Hello, World!"


# def test_database():
#     init_db()
#     assert Path("flaskr.db").is_file()