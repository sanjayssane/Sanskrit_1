"""End-to-end smoke tests of the Streamlit app via streamlit.testing (AppTest)."""

import pytest
from streamlit.testing.v1 import AppTest

from db import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "shop.db")
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    conn = database.init_db(tmp_path / "shop.db")
    conn.close()


def _app() -> AppTest:
    return AppTest.from_file("app.py", default_timeout=30)


def _staff_login(at: AppTest) -> AppTest:
    return at.switch_page("pages/0_Staff_Login.py").run()


def test_login_rejects_bad_credentials():
    at = _staff_login(_app())
    assert not at.exception
    at.text_input[0].set_value("owner")
    at.text_input[1].set_value("wrong-password")
    at.button[0].click().run()
    assert not at.exception
    assert any("Invalid" in e.value for e in at.error)


def test_login_then_forced_password_change():
    at = _staff_login(_app())
    at.text_input[0].set_value("owner")
    at.text_input[1].set_value("change@123")
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["user"]["username"] == "owner"
    logged_in = dict(at.session_state["user"])
    at = _app()
    at.session_state["user"] = logged_in
    at.run()
    at.text_input[0].set_value("new-secret-1")
    at.text_input[1].set_value("new-secret-1")
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["user"]["must_change_pw"] is False


def test_dashboard_renders_for_logged_in_user():
    at = _app()
    at.session_state["user"] = {
        "id": 1, "username": "owner", "full_name": "Shop Owner",
        "role": "owner", "is_active": True, "must_change_pw": False,
    }
    at.run()
    assert not at.exception
    assert any("Dashboard" in t.value for t in at.title)


def test_user_guide_renders_without_login():
    at = _app().switch_page("pages/12_User_Guide.py").run()
    assert not at.exception
    assert any("User Guide" in m.value for m in at.markdown)
