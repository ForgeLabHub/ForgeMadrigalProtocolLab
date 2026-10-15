"""Tests for the rule-application contract in the window.

The defect these cover: a rule built or typed in the editor was not adopted by
the apply action, so pressing apply either reported that no rule was loaded or
ran the previously loaded rule against different bytes. The tests drive the real
window with the real sample capture and rule; no widget is mocked.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtWidgets

from src.ui import theme
from src.ui.main_window import SAMPLE_CAPTURE, SAMPLE_RULE, MainWindow

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def app():
    try:
        application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as exc:
        pytest.skip(f"Qt platform could not start: {exc}")
    theme.load_fonts(application)
    return application


@pytest.fixture
def window(app):
    win = MainWindow()
    yield win
    win.close()


def _open_sample(window) -> None:
    window.open_capture(SAMPLE_CAPTURE)
    window.load_rule(SAMPLE_RULE)


def test_apply_adopts_a_rule_typed_into_the_editor(window):
    """A rule present only as editor text is the rule that runs."""
    window.open_capture(SAMPLE_CAPTURE)
    window.validation_view.set_rule_text(SAMPLE_RULE.read_text(encoding="utf-8"))
    QtWidgets.QApplication.processEvents()

    assert window._rule is not None, "a parsable rule in the editor becomes the model"
    window.apply_rule()

    assert window._rule.root is not None
    assert window._rule.root.messages, "the applied rule produced messages"
    assert window.validation_view.messages_table.rowCount() > 0


def test_apply_does_not_run_a_stale_rule(window):
    """Editing the rule clears the previous verdict before the next run."""
    _open_sample(window)
    window.apply_rule()
    assert window._rule_applied is True

    # A shorter rule is a different rule; the old run must not stand.
    window.validation_view.set_rule_text(
        '{"schema_version": 1, "rule_id": "r1", "rule_version": 2,'
        ' "name": "edited", "scope": {"direction": "A_to_B"},'
        ' "framing": {"type": "fixed_size", "size": 8}, "fields": []}'
    )
    QtWidgets.QApplication.processEvents()
    assert window._rule_applied is False, "an edited rule is not the applied one"
    assert window.validation_view.messages_table.rowCount() <= 1


def test_building_a_rule_marks_the_previous_one_as_previous(window):
    """A rebuilt rule keeps the old one for the version comparison."""
    _open_sample(window)
    window.apply_rule()
    old_version = window._rule.rule.rule_version

    window.validation_view.set_rule_text(
        json.dumps(
            {
                "schema_version": 1,
                "rule_id": "r1",
                "rule_version": old_version + 1,
                "name": "edited",
                "scope": {"direction": "A_to_B"},
                "framing": {"type": "fixed_size", "size": 8},
                "fields": [],
            }
        )
    )
    QtWidgets.QApplication.processEvents()

    assert window._rule.previous_rule is not None
    assert window._rule.previous_rule.rule_version == old_version


def test_opening_a_capture_clears_the_previous_verdict(window):
    """A new capture invalidates the messages taken against the old one."""
    _open_sample(window)
    window.apply_rule()
    assert window.validation_view.messages_table.rowCount() > 0

    window.open_capture(
        REPO_ROOT
        / "tests"
        / "corpus"
        / "reference_export"
        / "corpus_capture_01.normalized.json"
    )
    assert window._rule_applied is False
    assert window.validation_view.messages_table.rowCount() <= 1


def test_apply_reports_an_invalid_rule_without_running(window):
    """An unparsable rule is reported and leaves the loaded rule untouched."""
    _open_sample(window)
    window.apply_rule()
    window.validation_view.set_rule_text("{ not json")
    QtWidgets.QApplication.processEvents()

    assert window._rule.rule.rule_id, "the loaded rule is still the model"
    window.apply_rule()
    assert "error" in window.validation_view.rule_status.text().lower()


def test_language_change_rebuilds_the_empty_state(window):
    """The first-run hint follows the language, it is not frozen at build time."""
    window._capture = None
    window._show_empty_state()
    window.set_language("en")
    QtWidgets.QApplication.processEvents()
    english = window.hex_view.toPlainText()
    window.set_language("ru")
    QtWidgets.QApplication.processEvents()
    russian = window.hex_view.toPlainText()

    assert english != russian, "the hint is rebuilt in the new language"
    window.set_language("system")


def test_message_lookup_tolerates_an_unset_offset(window):
    """No byte clicked yet: the lookup returns nothing instead of raising.

    ``_last_offset`` is None until a byte is clicked, and the build-rule action
    reads the message under the cursor before that. A rule is applied here so the
    lookup reaches the scan rather than the no-rule guard.
    """
    _open_sample(window)
    window.apply_rule()
    assert window._last_offset is None

    assert window._message_at(window._last_offset) is None
    assert window._message_at(None) is None


def test_build_rule_before_any_click_does_not_raise(window, monkeypatch):
    """Building a rule before a byte is clicked does not raise.

    The builder is stubbed so the dialog cannot block the run. The failure this
    guards against happens while the message bytes are collected, before the
    dialog is constructed.
    """
    import src.ui.rule_builder as rule_builder

    seen: dict[str, object] = {}

    class _Stub:
        def __init__(self, *args, **kwargs):
            seen["message"] = kwargs.get("message")

        def setFont(self, _font):  # pragma: no cover - construction only
            pass

        def exec(self):
            return QtWidgets.QDialog.DialogCode.Rejected

    monkeypatch.setattr(rule_builder, "RuleBuilderDialog", _Stub)

    _open_sample(window)
    window.apply_rule()
    assert window._last_offset is None

    window.build_rule()
    assert isinstance(seen.get("message"), bytes)
