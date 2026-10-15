"""Regression tests for the build-rule flow and the state it must reset.

Three defects are pinned here, all on the path a first-run reader walks. They
were found on the audited baseline and are fixed on the integration branch; the
tests are the contract that keeps them fixed.

* D1 — building a rule through the form left only text in the editor, not a
  rule model, so pressing Apply (or "verify on the corpus") silently did
  nothing. The form must leave a rule the window can actually run.
* D2 — the first-run hint in the hex view was written once and never redrawn,
  so switching to Russian left the English hint on screen.
* D3 — loading or re-building a rule kept the previous rule's "already applied"
  state, so the coach's step and the outdated marks did not reset.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PySide6 import QtWidgets

    from src.ui import rule_builder, theme
    from src.ui.main_window import MainWindow, open_default_window
except ImportError as exc:  # pragma: no cover - depends on the runner
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURE = (
    REPO_ROOT / "tests" / "corpus" / "reference_export" / "corpus_capture_01.normalized.json"
)
RULE = REPO_ROOT / "examples" / "corpus_rule_v1.json"

corpus_required = pytest.mark.skipif(
    not CAPTURE.is_file() or not RULE.is_file(),
    reason="reference corpus not present",
)


@pytest.fixture(scope="session")
def app():
    try:
        application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as exc:  # pragma: no cover - depends on the runner
        pytest.skip(f"Qt platform could not start: {exc}")
    theme.load_fonts(application)
    application.setStyleSheet(theme.build_stylesheet())
    return application


@pytest.fixture
def accepting_builder(monkeypatch):
    """Make the rule-builder dialog fill a field and accept, as a user would."""

    def fake_exec(self):
        self._rows[0].name.setText("command")
        return QtWidgets.QDialog.DialogCode.Accepted

    monkeypatch.setattr(rule_builder.RuleBuilderDialog, "exec", fake_exec)


@corpus_required
def test_build_rule_leaves_a_runnable_rule(app, accepting_builder):
    """D1: a rule built from the form can be applied, not only shown."""
    window = open_default_window(app, capture=CAPTURE, rule=None)
    assert window._rule is None

    window.build_rule()
    assert window._rule is not None, "building a rule must create a rule model"

    window.apply_rule()
    assert window._rule.root is not None, "apply must run on the built rule"
    assert window.validation_view.rule_status.text(), "apply must report a result"
    window.close()


@corpus_required
def test_built_rule_can_be_verified_on_the_corpus(app, accepting_builder):
    """D1: the built rule also runs over the whole capture."""
    window = open_default_window(app, capture=CAPTURE, rule=None)
    window.build_rule()
    window.apply_to_capture()
    assert window._corpus_report is not None
    window.close()


def test_first_run_hint_follows_the_language(app):
    """D2: the empty-state hint is redrawn when the language changes."""
    window = open_default_window(app, capture=None, rule=None)
    english = window.hex_view.toPlainText()
    assert english.strip()

    window.set_language("ru")
    app.processEvents()
    russian = window.hex_view.toPlainText()
    assert russian != english, "the hint must change with the language"
    assert "no capture loaded" not in russian

    window.set_language("en")
    app.processEvents()
    assert window.hex_view.toPlainText() == english
    window.close()


@corpus_required
def test_loading_a_rule_clears_the_applied_state(app):
    """D3: a freshly loaded rule has not been applied yet."""
    window = open_default_window(app, capture=CAPTURE, rule=RULE)
    window.apply_rule()
    app.processEvents()
    assert window._rule_applied is True

    window.load_rule(RULE)
    app.processEvents()
    assert window._rule_applied is False, "loading a rule resets 'applied'"
    window.close()


@corpus_required
def test_rebuilding_a_rule_clears_the_applied_state(app, accepting_builder):
    """D3: editing a rule through the form also resets 'applied'."""
    window = open_default_window(app, capture=CAPTURE, rule=RULE)
    window.apply_rule()
    app.processEvents()
    assert window._rule_applied is True

    window.build_rule()
    app.processEvents()
    assert window._rule_applied is False
    assert window._rule is not None
    window.close()


def test_window_accepts_no_input_without_crashing(app):
    """The empty window stays usable: no capture, no rule, no crash."""
    window = MainWindow()
    window.apply_rule()
    assert "error" not in window.validation_view.rule_status.text().lower()
    window.close()
