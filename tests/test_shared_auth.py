from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests import conftest as setup
from tests.browser_session import AuthSnapshot, restore_auth_state


@pytest.fixture
def controller_config():
    return SimpleNamespace(
        stash=pytest.Stash(),
        option=SimpleNamespace(collectonly=False),
        pluginmanager=SimpleNamespace(getplugin=lambda _: None),
    )


@pytest.mark.parametrize("worker_count", [1, 2, 4])
def test_workers_and_replacement_worker_share_one_login(
    monkeypatch: pytest.MonkeyPatch, controller_config, worker_count: int
) -> None:
    original = {"local": {"auth": "test-value"}, "cookies": [], "session": {}}
    capture = Mock(return_value=deepcopy(original))
    monkeypatch.setattr(setup, "capture_auth_state", capture)
    workers = [
        SimpleNamespace(config=controller_config, workerinput={})
        for _ in range(worker_count + 1)
    ]
    for worker in workers:
        setup.pytest_configure_node(worker)

    assert capture.call_count == 1
    workers[0].workerinput["auth_state"]["local"]["auth"] = "changed"
    assert workers[-1].workerinput["auth_state"] == original
    assert setup.shared_auth_state(controller_config) == original
    setup.pytest_unconfigure(controller_config)
    assert setup.AUTH_STATE not in controller_config.stash


def test_collect_only_does_not_log_in(
    monkeypatch: pytest.MonkeyPatch, controller_config
) -> None:
    controller_config.option.collectonly = True
    capture = Mock()
    monkeypatch.setattr(setup, "capture_auth_state", capture)
    node = SimpleNamespace(config=controller_config, workerinput={})
    setup.pytest_configure_node(node)
    capture.assert_not_called()
    assert node.workerinput == {}


def test_failed_bootstrap_is_not_retried_or_exposed(
    monkeypatch: pytest.MonkeyPatch, controller_config
) -> None:
    capture = Mock(side_effect=RuntimeError("private-token-example"))
    monkeypatch.setattr(setup, "capture_auth_state", capture)
    for _ in range(2):
        with pytest.raises(pytest.UsageError) as failure:
            setup.shared_auth_state(controller_config)
        assert "private-token-example" not in str(failure.value)
    assert capture.call_count == 1
    snapshot = AuthSnapshot(local={"auth": "private-token-example"})
    assert "private-token-example" not in repr(snapshot)


def test_rejected_snapshot_does_not_trigger_another_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restore = Mock(side_effect=RuntimeError("private-token-example"))
    capture = Mock()
    monkeypatch.setattr(setup, "restore_auth_state", restore)
    monkeypatch.setattr(setup, "capture_auth_state", capture)
    with pytest.raises(RuntimeError, match="no login retry") as failure:
        setup.authenticated_driver.__wrapped__(AuthSnapshot(), Mock(), "https://example.test")
    capture.assert_not_called()
    assert restore.call_count == 1
    assert "private-token-example" not in str(failure.value)


def test_snapshot_from_another_origin_is_rejected() -> None:
    browser = Mock()
    with pytest.raises(RuntimeError, match="another origin"):
        restore_auth_state(browser, {"origin": "https://example.test"}, "https://other.test")
    browser.get.assert_not_called()
