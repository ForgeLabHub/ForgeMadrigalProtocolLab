"""Regression tests for the bundled demo's rule application.

The defect: opening the demo ran only the whole-capture pass. That pass fills the
counterexample list but deliberately leaves the per-direction Messages table
alone, so the one-click demo landed on the empty Messages state even though the
rule had in fact been applied and the bytes annotated. These tests drive the
real window with the real samples; no widget is mocked.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtWidgets

from src.ui import theme
from src.ui.hex_view import MATCHED
from src.ui.main_window import SAMPLE_CAPTURE, SAMPLE_RULE, MainWindow


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


def _matched_bytes(window) -> int:
    """Bytes of the shown direction annotated with a matched verdict."""
    stream = window._capture.stream(window._session_id, window._direction)
    count = 0
    for offset in range(len(stream.data)):
        annotation = window.hex_view.annotation_at(offset)
        if annotation is not None and annotation.kind == MATCHED:
            count += 1
    return count


def test_open_demo_applies_the_rule_to_the_direction(window):
    """The demo shows decoded messages, not the empty Messages state."""
    window.open_demo()
    QtWidgets.QApplication.processEvents()

    assert window._capture is not None
    assert window._rule is not None
    assert window._journal, "the demo journal is paired"
    assert window._rule.root is not None, "the rule was applied to the direction"
    assert window._rule.root.messages, "the direction run produced messages"

    rows = window.validation_view.messages_table.rowCount()
    assert rows > 1, "the demo is not stuck on the one-row empty state"
    assert rows == len(window._rule.root.messages)
    assert window.validation_view._message_count == rows
    assert window._rule_applied is True


def test_open_demo_annotates_the_bytes(window):
    """The hex view carries the verdict of the run the demo just made."""
    window.open_demo()
    QtWidgets.QApplication.processEvents()

    first = window.hex_view.annotation_at(0)
    assert first is not None, "byte 0 is annotated"
    assert first.kind == MATCHED
    assert _matched_bytes(window) > 0, "the matched verdict reaches the hex view"


def test_open_demo_keeps_the_whole_capture_verdict(window):
    """The direction run does not displace the corpus counterexample pass."""
    window.open_demo()
    QtWidgets.QApplication.processEvents()

    assert window._corpus_report is not None
    assert window._rule.corpus_report is window._corpus_report
    assert "capture" in window.validation_view.rule_status.text().lower()


def test_open_demo_does_not_duplicate_on_reopen(window):
    """Opening the demo twice leaves one set of rows, annotations and counters."""
    window.open_demo()
    QtWidgets.QApplication.processEvents()
    rows = window.validation_view.messages_table.rowCount()
    matched = _matched_bytes(window)
    counters = window.validation_view.counterexample_count

    window.open_demo()
    QtWidgets.QApplication.processEvents()

    assert window.validation_view.messages_table.rowCount() == rows
    assert _matched_bytes(window) == matched
    assert window.validation_view.counterexample_count == counters


def test_open_demo_matches_a_manual_run(app):
    """The demo result equals loading the same capture and rule by hand."""
    demo = MainWindow()
    demo.open_demo()
    QtWidgets.QApplication.processEvents()
    demo_rows = demo.validation_view.messages_table.rowCount()
    demo_matched = _matched_bytes(demo)
    demo.close()

    manual = MainWindow()
    manual.open_capture(SAMPLE_CAPTURE)
    manual.load_rule(SAMPLE_RULE)
    manual.apply_rule()
    QtWidgets.QApplication.processEvents()
    manual_rows = manual.validation_view.messages_table.rowCount()
    manual_matched = _matched_bytes(manual)
    manual.close()

    assert demo_rows == manual_rows
    assert demo_matched == manual_matched


def test_typed_rule_is_still_applied(window):
    """A rule that exists only as editor text is adopted and run."""
    window.open_capture(SAMPLE_CAPTURE)
    window.validation_view.set_rule_text(
        '{"schema_version": 1, "rule_id": "typed", "rule_version": 1,'
        ' "name": "typed", "scope": {"direction": "A_to_B"},'
        ' "framing": {"type": "fixed_size", "size": 8}, "fields": []}'
    )
    QtWidgets.QApplication.processEvents()

    window.apply_rule()

    assert window._rule is not None
    assert window._rule_applied is True
    assert window.validation_view.messages_table.rowCount() > 1
