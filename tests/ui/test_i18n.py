"""Tests for the interface-language switching.

The tests exercise the real Qt translator: a ``.qm`` catalogue is loaded for
Russian, the window relabels itself, and switching back to English restores the
source strings. No widget is mocked; only the stored preference is redirected to
a throwaway ``QSettings`` scope so the developer's own choice is untouched.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PySide6 import QtWidgets

    from src.ui import i18n, theme
    from src.ui.main_window import MainWindow
except ImportError as exc:  # pragma: no cover - depends on the runner
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = REPO_ROOT / "src" / "ui" / "locale" / "madrigal_ru.qm"

catalogue_required = pytest.mark.skipif(
    not CATALOGUE.is_file(), reason="Russian catalogue is not compiled"
)


@pytest.fixture(scope="session")
def app():
    try:
        application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as exc:
        pytest.skip(f"Qt platform could not start: {exc}")
    theme.load_fonts(application)
    application.setStyleSheet(theme.build_stylesheet())
    return application


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Point the language preference at a throwaway settings file."""
    monkeypatch.setattr(i18n, "_SETTINGS_ORG", "madrigal-test")
    monkeypatch.setattr(i18n, "_SETTINGS_APP", f"protocol-lab-{tmp_path.name}")
    yield


@pytest.fixture
def english_window(app, isolated_settings):
    """A window that is restored to English afterwards."""
    window = MainWindow()
    yield window
    window._language_manager.set_language("en")
    window.close()


def test_resolve_language_maps_system_locale():
    assert i18n.resolve_language("system", "ru_RU") == "ru"
    assert i18n.resolve_language("system", "ru") == "ru"
    assert i18n.resolve_language("system", "en_US") == "en"
    assert i18n.resolve_language("system", "fr_FR") == "en"


def test_resolve_language_keeps_explicit_choice():
    assert i18n.resolve_language("ru", "en_US") == "ru"
    assert i18n.resolve_language("en", "ru_RU") == "en"


def test_language_manager_emits_and_loads_catalogue(app, isolated_settings):
    manager = i18n.LanguageManager(app)
    seen: list[str] = []
    manager.languageChanged.connect(seen.append)

    manager.set_language("ru")
    assert manager.language == "ru"
    assert seen == ["ru"]

    manager.set_language("en")
    assert manager.language == "en"
    assert seen == ["ru", "en"]


def test_language_manager_rejects_unknown_code(app, isolated_settings):
    manager = i18n.LanguageManager(app)
    manager.set_language("de")
    assert manager.preference == "system"


@catalogue_required
def test_window_retranslates_to_russian(english_window):
    window = english_window
    assert window.windowTitle() == "Madrigal protocol laboratory"

    window.set_language("ru")
    assert window.windowTitle() == "Лаборатория протоколов Мадригал"
    assert window._menus["file"].title() == "&Файл"
    assert window._actions["quit"].text() == "Вы&ход"
    assert window.right_tabs.tabText(0) == "Анализ"
    assert window._bytes_box.title() == "Байты"
    assert window.validation_view.apply_button.text() == "Применить к текущему направлению"


@catalogue_required
def test_window_language_switch_is_reversible(english_window):
    window = english_window
    window.set_language("ru")
    window.set_language("en")
    assert window.windowTitle() == "Madrigal protocol laboratory"
    assert window._menus["file"].title() == "&File"
    assert window.right_tabs.tabText(0) == "Interpretation"


@catalogue_required
def test_language_choice_is_stored(english_window, app):
    window = english_window
    window.set_language("ru")
    reopened = MainWindow()
    try:
        assert reopened._language_manager.preference == "ru"
        assert reopened.windowTitle() == "Лаборатория протоколов Мадригал"
    finally:
        reopened._language_manager.set_language("en")
        reopened.close()


@catalogue_required
def test_language_menu_checks_current_choice(english_window):
    window = english_window
    window.set_language("ru")
    assert window._language_actions["ru"].isChecked()
    window.set_language("en")
    assert window._language_actions["en"].isChecked()


@catalogue_required
def test_switching_language_keeps_open_capture(english_window):
    window = english_window
    capture = REPO_ROOT / "tests" / "corpus" / "reference_export" / "corpus_capture_01.normalized.json"
    if not capture.is_file():
        pytest.skip("reference corpus not present")
    window.open_capture(capture)
    session_before = window._session_id
    window.set_language("ru")
    assert window._capture is not None
    assert window._session_id == session_before
    assert window._capture_name in window.windowTitle()


@catalogue_required
def test_dynamic_status_lines_retranslate(english_window):
    """The rule-status line and the provenance card follow the language.

    Both hold a finished string the window built itself, not a caption Qt
    re-translates on its own, so a switch has to rebuild them from what is
    kept. Without that the line stays in the previous language while the rest
    of the window changes around it.
    """
    window = english_window
    capture = REPO_ROOT / "tests" / "corpus" / "reference_export" / "corpus_capture_01.normalized.json"
    rule = REPO_ROOT / "examples" / "corpus_rule_v1.json"
    if not capture.is_file() or not rule.is_file():
        pytest.skip("reference corpus not present")

    window.open_capture(capture)
    window.load_rule(rule)
    window.apply_rule()
    window.apply_to_capture()

    status_en = window.validation_view.rule_status.text()
    provenance_en = window._provenance_label.text()
    assert "rule v" in status_en
    assert "sessions" in provenance_en

    window.set_language("ru")
    status_ru = window.validation_view.rule_status.text()
    provenance_ru = window._provenance_label.text()
    assert "правило v" in status_ru
    assert "сессий" in provenance_ru
    assert status_ru != status_en

    window.set_language("en")
    assert window.validation_view.rule_status.text() == status_en
    assert window._provenance_label.text() == provenance_en


_CATALOGUE_SOURCE = REPO_ROOT / "src" / "ui" / "locale" / "madrigal_ru.ts"
_CATALOGUES = (
    REPO_ROOT / "src" / "ui" / "locale" / "madrigal_ru.ts",
    REPO_ROOT / "src" / "ui" / "locale" / "madrigal_en.ts",
)


@pytest.mark.parametrize("catalogue", _CATALOGUES, ids=lambda p: p.stem)
def test_catalogue_has_no_unfinished_translations(catalogue):
    """Every message in each source catalogue is translated.

    A message left ``unfinished`` compiles anyway, so a user of that language
    would see one caption in another language among the rest. Both catalogues
    are checked, the English one included, because it is the catalogue the
    English build actually loads.
    """
    import xml.etree.ElementTree as ElementTree

    tree = ElementTree.parse(catalogue)
    unfinished = [
        message.findtext("source")
        for message in tree.getroot().iter("message")
        if message.find("translation") is not None
        and message.find("translation").get("type") in ("unfinished", "vanished", "obsolete")
    ]
    assert unfinished == [], f"untranslated messages: {unfinished}"


def test_english_catalogue_matches_the_source_strings():
    """The English catalogue is filled one for one from the source strings.

    English is the source language, so each translation must equal its source;
    a divergence would mean the filler script missed a message.
    """
    import xml.etree.ElementTree as ElementTree

    tree = ElementTree.parse(REPO_ROOT / "src" / "ui" / "locale" / "madrigal_en.ts")
    mismatched = [
        (message.findtext("source"), message.findtext("translation"))
        for message in tree.getroot().iter("message")
        if message.findtext("source") != message.findtext("translation")
    ]
    assert mismatched == [], f"not filled from source: {mismatched}"


def test_catalogue_covers_the_navigable_captions():
    """The catalogue carries the menu, tab and group-box captions.

    A hand-picked list of the captions a user navigates by, so a caption added
    without a translation fails here rather than shipping as English into the
    Russian build.
    """
    import xml.etree.ElementTree as ElementTree

    tree = ElementTree.parse(_CATALOGUE_SOURCE)
    known = {message.findtext("source") for message in tree.getroot().iter("message")}
    expected = {
        "&File", "&Rule", "&Report", "&View", "&Help", "&Language",
        "Interpretation", "Compare", "Hypotheses", "Report", "Version diff",
        "Bytes", "Sessions", "direction", "session", "traffic",
        "&Settings...", "&Quick help", "&About", "&Dark theme", "&Light theme",
        "matched", "mismatched", "gap", "ambiguity", "uncovered", "incomplete",
    }
    missing = sorted(expected - known)
    assert missing == [], f"missing from the catalogue: {missing}"
