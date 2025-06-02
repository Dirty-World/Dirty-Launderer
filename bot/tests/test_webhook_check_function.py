import os
import pytest
from unittest.mock import patch, MagicMock
from webhook_check_function import main, get_secret, is_valid_url

class DummyRequests:
    def __init__(self, get_response=None, post_response=None, get_exception=None, post_exception=None):
        self._get_response = get_response
        self._post_response = post_response
        self._get_exception = get_exception
        self._post_exception = post_exception
        self.get_called = False
        self.post_called = 0
        self.last_post_args = None
        self.last_post_kwargs = None

    def get(self, *args, **kwargs):
        self.get_called = True
        if self._get_exception:
            raise self._get_exception
        return self._get_response

    def post(self, *args, **kwargs):
        self.post_called += 1
        self.last_post_args = args
        self.last_post_kwargs = kwargs
        if self._post_exception:
            raise self._post_exception
        return self._post_response

class DummyResponse:
    def __init__(self, json_data=None, raise_exc=None):
        self._json_data = json_data or {}
        self._raise_exc = raise_exc
        self.raise_for_status_called = False
    def json(self):
        return self._json_data
    def raise_for_status(self):
        self.raise_for_status_called = True
        if self._raise_exc:
            raise self._raise_exc

# Helper to make a dummy request object
class DummyRequest:
    pass

def test_webhook_update():
    """Test webhook update when current != expected."""
    get_resp = DummyResponse(json_data={"result": {"url": "https://old.url/webhook"}})
    post_resp = DummyResponse(json_data={"ok": True})
    dummy_requests = DummyRequests(get_response=get_resp, post_response=post_resp)
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 200
    assert result["status"] == "updated"
    assert dummy_requests.get_called
    assert dummy_requests.post_called == 2  # setWebhook + sendMessage

def test_webhook_already_correct():
    """Test when webhook is already correct."""
    get_resp = DummyResponse(json_data={"result": {"url": "https://new.url/webhook"}})
    dummy_requests = DummyRequests(get_response=get_resp)
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 200
    assert result["status"] == "ok"
    assert dummy_requests.get_called
    assert dummy_requests.post_called == 0

def test_missing_env_vars():
    """Test missing required environment variables."""
    env = {"TELEGRAM_TOKEN": "token"}  # missing EXPECTED_WEBHOOK_URL
    dummy_requests = DummyRequests()
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 500
    assert "error" in result

def test_invalid_url():
    """Test invalid EXPECTED_WEBHOOK_URL."""
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "not-a-url",
        "ALERT_CHAT_ID": "chatid"
    }
    dummy_requests = DummyRequests()
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 500
    assert "error" in result

def test_get_webhook_http_error():
    """Test HTTP error when getting current webhook."""
    class DummyHTTPError(Exception): pass
    dummy_requests = DummyRequests(get_exception=DummyHTTPError("fail"))
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 500
    assert "error" in result

def test_set_webhook_http_error():
    """Test HTTP error when setting webhook."""
    class DummyHTTPError(Exception): pass
    get_resp = DummyResponse(json_data={"result": {"url": "https://old.url/webhook"}})
    dummy_requests = DummyRequests(get_response=get_resp, post_exception=DummyHTTPError("fail"))
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 500
    assert "error" in result

def test_unexpected_exception():
    """Test unexpected exception in main."""
    def bad_secret(*a, **kw):
        raise RuntimeError("fail")
    env = {
        "GCP_PROJECT_ID": "pid",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    dummy_requests = DummyRequests()
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests, secret_func=bad_secret)
    assert code == 500
    assert "error" in result

# New tests for error handling and edge cases

def test_get_secret_error(monkeypatch):
    """Test get_secret error handling."""
    class DummyClient:
        def access_secret_version(self, request):
            raise Exception("secret fail")
    monkeypatch.setattr("google.cloud.secretmanager.SecretManagerServiceClient", lambda: DummyClient())
    with pytest.raises(Exception):
        get_secret("pid", "sid")

def test_is_valid_url_exception():
    """Test is_valid_url with an object that raises in urlparse."""
    class BadStr:
        def __str__(self):
            raise Exception("fail")
    # Should return False, not raise
    assert is_valid_url(BadStr()) is False

def test_alert_send_fails():
    """Test alert sending fails in main error path."""
    class DummyRequestsFail(DummyRequests):
        def post(self, *a, **k):
            raise Exception("fail post")
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    # This will trigger get_current_webhook to fail, which triggers alert
    class DummyHTTPError(Exception): pass
    dummy_requests = DummyRequests(get_exception=DummyHTTPError("fail"))
    # Patch post to fail
    dummy_requests.post = lambda *a, **k: (_ for _ in ()).throw(Exception("fail post"))
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests)
    assert code == 500
    assert "error" in result

def test_alert_send_fails_in_exception_handler():
    """Test alert sending fails in the main exception handler itself."""
    env = {
        "TELEGRAM_TOKEN": "token",
        "EXPECTED_WEBHOOK_URL": "https://new.url/webhook",
        "ALERT_CHAT_ID": "chatid"
    }
    def bad_secret(*a, **kw):
        raise RuntimeError("fail")
    class DummyRequestsFail(DummyRequests):
        def post(self, *a, **k):
            raise Exception("fail post")
    dummy_requests = DummyRequestsFail()
    result, code = main(DummyRequest(), env=env, requests_mod=dummy_requests, secret_func=bad_secret)
    assert code == 500
    assert "error" in result 