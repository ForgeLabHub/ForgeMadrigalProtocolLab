"""Tests for the form-based rule builder.

The builder must produce a document the rule parser accepts, and it must load a
document back into the form without losing what it can represent, so editing a
rule never silently drops the parts the form covers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PySide6 import QtWidgets

    from src.protocol.rule import parse_rule
    from src.ui import theme
    from src.ui.rule_builder import RuleBuilderDialog
except ImportError as exc:  # pragma: no cover - depends on the runner
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "corpus_rule_v1.json"


@pytest.fixture(scope="session")
def app():
    try:
        application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as exc:  # pragma: no cover - depends on the runner
        pytest.skip(f"Qt platform could not start: {exc}")
    theme.load_fonts(application)
    return application


def test_empty_form_yields_a_parsable_rule(app):
    dialog = RuleBuilderDialog()
    dialog._rows[0].name.setText("command")
    document = json.loads(dialog.rule_text())
    rule = parse_rule(document)
    assert rule.rule_id
    assert [field.name for field in rule.fields] == ["command"]


def test_field_attributes_reach_the_document(app):
    dialog = RuleBuilderDialog()
    row = dialog._rows[0]
    row.name.setText("target")
    row.type.setCurrentText("enum")
    row.values.setText("temperature=16, humidity=17")
    row.hypothesis.setChecked(True)
    row.expected.setText("16, 17")
    document = json.loads(dialog.rule_text())
    field = document["fields"][0]
    assert field["enum"] == {"temperature": 16, "humidity": 17}
    assert field["hypothesis"] is True
    assert field["expected"] == [16, 17]


def test_example_rule_loads_into_the_form(app):
    """A rule written outside the form opens in it without losing its fields."""
    seed = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    dialog = RuleBuilderDialog(seed)
    document = json.loads(dialog.rule_text())
    assert document["rule_id"] == seed["rule_id"]
    assert document["framing"]["type"] == seed["framing"]["type"]
    assert [f["name"] for f in document["fields"]] == [
        f["name"] for f in seed["fields"]
    ]
    assert parse_rule(document).direction == "A_to_B"


def test_framing_switch_changes_the_document(app):
    dialog = RuleBuilderDialog()
    dialog.framing_type.setCurrentText("fixed_size")
    dialog.fixed_size.setValue(16)
    framing = json.loads(dialog.rule_text())["framing"]
    assert framing == {"type": "fixed_size", "size": 16}


def test_remove_field_drops_the_row(app):
    dialog = RuleBuilderDialog()
    dialog._rows[0].name.setText("command")
    dialog._add_row({"name": "value", "offset": 1, "type": "uint16"})
    dialog.fields_table.setCurrentCell(1, 0)
    dialog._on_remove()
    document = json.loads(dialog.rule_text())
    assert [f["name"] for f in document["fields"]] == ["command"]
