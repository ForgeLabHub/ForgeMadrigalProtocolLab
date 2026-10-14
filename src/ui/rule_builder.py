"""Form-based rule builder.

Writing a rule as JSON is exact but not something a researcher should have to do
to describe a message they can already see. This dialog builds the same document
from a form: the framing that cuts the stream into messages, and one row per
field.

The dialog is the single source of truth for the common shape of a rule. The
generated JSON is shown live, so the form and the document never disagree, and
advanced attributes that the form does not cover can still be added by editing
the document afterwards.
"""

from __future__ import annotations

import json

from PySide6 import QtCore, QtWidgets

from ..protocol.framing import LENGTH_COVERS_VALUES
from ..protocol.rule import ALL_FIELD_TYPES
from . import theme
from .constants import FONT_SIZE_BODY

_FRAMING_TYPES = ("length_prefixed", "fixed_size", "marker_based", "manual")
_BYTE_ORDERS = ("big", "little")
_FIELD_COLUMNS = (
    "name",
    "offset",
    "type",
    "order",
    "length",
    "values",
    "hypothesis",
    "expected",
)


def _parse_expected(text: str) -> list | None:
    """Parse a comma-separated expected-value list into ints and strings."""
    tokens = [token.strip() for token in text.split(",") if token.strip()]
    if not tokens:
        return None
    values: list = []
    for token in tokens:
        try:
            values.append(int(token, 0))
        except ValueError:
            values.append(token)
    return values


def _parse_enum(text: str) -> dict[str, int] | None:
    """Parse ``name=value`` pairs into an enum mapping."""
    mapping: dict[str, int] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        name, _, value = part.partition("=")
        try:
            mapping[name.strip()] = int(value.strip(), 0)
        except ValueError:
            continue
    return mapping or None


def _format_enum(mapping: dict | None) -> str:
    if not mapping:
        return ""
    return ", ".join(f"{name}={value}" for name, value in mapping.items())


def _format_expected(values: list | None) -> str:
    if not values:
        return ""
    return ", ".join(str(value) for value in values)


def _hex_dump(data: bytes, width: int = 16) -> str:
    """A plain hex dump with byte offsets, used beside the field form."""
    lines = []
    for start in range(0, len(data), width):
        chunk = data[start : start + width]
        hexpart = " ".join(f"{byte:02x}" for byte in chunk).ljust(width * 3 - 1)
        lines.append(f"{start:04x}  {hexpart}")
    return "\n".join(lines)


class _FieldRow:
    """The widgets of one field row, read back when the rule is generated."""

    def __init__(self) -> None:
        self.name = QtWidgets.QLineEdit()
        self.offset = QtWidgets.QSpinBox()
        self.offset.setRange(0, 1_000_000)
        self.type = QtWidgets.QComboBox()
        self.type.addItems(sorted(ALL_FIELD_TYPES))
        self.type.setCurrentText("uint8")
        self.order = QtWidgets.QComboBox()
        self.order.addItems(_BYTE_ORDERS)
        self.length = QtWidgets.QSpinBox()
        self.length.setRange(0, 1_000_000)
        self.length.setSpecialValueText("-")
        self.values = QtWidgets.QLineEdit()
        self.values.setPlaceholderText("name=1, other=2")
        self.hypothesis = QtWidgets.QCheckBox()
        self.hypothesis.setToolTip(
            QtCore.QCoreApplication.translate(
                "RuleBuilder",
                "The field's meaning is an assumption, not an observation",
            )
        )
        self.expected = QtWidgets.QLineEdit()
        self.expected.setPlaceholderText("1, 2, 3")

    def widgets(self) -> list[QtWidgets.QWidget]:
        return [
            self.name,
            self.offset,
            self.type,
            self.order,
            self.length,
            self.values,
            self.hypothesis,
            self.expected,
        ]

    def to_dict(self) -> dict:
        field: dict = {
            "name": self.name.text().strip(),
            "offset": self.offset.value(),
            "type": self.type.currentText(),
        }
        if self.order.currentText() != "big":
            field["byte_order"] = self.order.currentText()
        if self.length.value():
            field["length"] = self.length.value()
        enum = _parse_enum(self.values.text())
        if enum:
            field["enum"] = enum
        if self.hypothesis.isChecked():
            field["hypothesis"] = True
        expected = _parse_expected(self.expected.text())
        if expected is not None:
            field["expected"] = expected
        return field


class RuleBuilderDialog(QtWidgets.QDialog):
    """Build a rule document from a framing form and a field table."""

    def __init__(
        self,
        rule: dict | None = None,
        parent: QtWidgets.QWidget | None = None,
        message: bytes | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Build rule"))
        self.setMinimumWidth(760)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._build_identity())
        layout.addWidget(self._build_framing())
        layout.addWidget(self._build_fields(), 1)
        # The bytes of the message under the cursor sit beside the form so the
        # field offsets can be read off the wire while they are typed. The pane is
        # absent when the builder is opened with no capture.
        if message:
            layout.addWidget(self._build_message_pane(message))
        layout.addWidget(self._build_preview(), 1)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(
            self.tr("Use rule")
        )
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText(
            self.tr("Cancel")
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._rows: list[_FieldRow] = []
        if rule:
            self._load(rule)
        else:
            self._add_row()
        self._refresh_preview()
        self.apply_theme()

    # -- construction ------------------------------------------------------

    def _build_identity(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(self.tr("Identity"))
        form = QtWidgets.QHBoxLayout(box)
        form.setSpacing(8)
        self.rule_id = QtWidgets.QLineEdit("rule")
        self.rule_name = QtWidgets.QLineEdit()
        self.rule_name.setPlaceholderText(self.tr("short name"))
        self.rule_version = QtWidgets.QSpinBox()
        self.rule_version.setRange(1, 1_000_000)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItem(self.tr("any direction"), "")
        self.direction.addItem("A_to_B", "A_to_B")
        self.direction.addItem("B_to_A", "B_to_A")
        for label, widget in (
            (self.tr("id"), self.rule_id),
            (self.tr("name"), self.rule_name),
            (self.tr("version"), self.rule_version),
            (self.tr("scope"), self.direction),
        ):
            column = QtWidgets.QVBoxLayout()
            caption = QtWidgets.QLabel(label)
            caption.setProperty("role", "secondary")
            column.addWidget(caption)
            column.addWidget(widget)
            form.addLayout(column)
        return box

    def _build_framing(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(
            self.tr("Framing: how the stream is cut into messages")
        )
        outer = QtWidgets.QVBoxLayout(box)
        outer.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        head.addWidget(QtWidgets.QLabel(self.tr("strategy")))
        self.framing_type = QtWidgets.QComboBox()
        self.framing_type.addItems(_FRAMING_TYPES)
        head.addWidget(self.framing_type)
        head.addStretch(1)
        outer.addLayout(head)

        self.framing_stack = QtWidgets.QStackedWidget()
        self.framing_stack.addWidget(self._length_page())
        self.framing_stack.addWidget(self._fixed_page())
        self.framing_stack.addWidget(self._marker_page())
        self.framing_stack.addWidget(self._manual_page())
        outer.addWidget(self.framing_stack)
        self.framing_type.currentIndexChanged.connect(
            self.framing_stack.setCurrentIndex
        )
        self.framing_type.currentIndexChanged.connect(self._refresh_preview)
        return box

    def _length_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.length_offset = QtWidgets.QSpinBox()
        self.length_offset.setRange(0, 1_000_000)
        self.length_size = QtWidgets.QComboBox()
        self.length_size.addItems(["1", "2", "4"])
        self.length_order = QtWidgets.QComboBox()
        self.length_order.addItems(_BYTE_ORDERS)
        self.length_covers = QtWidgets.QComboBox()
        self.length_covers.addItems(list(LENGTH_COVERS_VALUES))
        for label, widget in (
            (self.tr("length at offset"), self.length_offset),
            (self.tr("length size"), self.length_size),
            (self.tr("byte order"), self.length_order),
            (self.tr("length counts"), self.length_covers),
        ):
            column = QtWidgets.QVBoxLayout()
            caption = QtWidgets.QLabel(label)
            caption.setProperty("role", "secondary")
            column.addWidget(caption)
            column.addWidget(widget)
            row.addLayout(column)
        for widget in (
            self.length_offset,
            self.length_size,
            self.length_order,
            self.length_covers,
        ):
            if isinstance(widget, QtWidgets.QSpinBox):
                widget.valueChanged.connect(self._refresh_preview)
            else:
                widget.currentIndexChanged.connect(self._refresh_preview)
        return page

    def _fixed_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QtWidgets.QLabel(self.tr("message size")))
        self.fixed_size = QtWidgets.QSpinBox()
        self.fixed_size.setRange(1, 1_000_000)
        self.fixed_size.valueChanged.connect(self._refresh_preview)
        row.addWidget(self.fixed_size)
        row.addStretch(1)
        return page

    def _marker_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.start_bytes = QtWidgets.QLineEdit()
        self.start_bytes.setPlaceholderText("hex:1B02")
        self.end_bytes = QtWidgets.QLineEdit()
        self.end_bytes.setPlaceholderText("hex:03")
        self.include_markers = QtWidgets.QCheckBox(
            self.tr("keep markers in the message")
        )
        for label, widget in (
            (self.tr("start marker"), self.start_bytes),
            (self.tr("end marker"), self.end_bytes),
        ):
            column = QtWidgets.QVBoxLayout()
            caption = QtWidgets.QLabel(label)
            caption.setProperty("role", "secondary")
            column.addWidget(caption)
            column.addWidget(widget)
            row.addLayout(column)
        row.addWidget(self.include_markers)
        for widget in (self.start_bytes, self.end_bytes):
            widget.textChanged.connect(self._refresh_preview)
        self.include_markers.toggled.connect(self._refresh_preview)
        return page

    def _manual_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        row = QtWidgets.QVBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        hint = QtWidgets.QLabel(
            self.tr(
                "Boundaries are marked by hand in the workspace; the rule keeps the field layout only."
            )
        )
        hint.setProperty("role", "secondary")
        hint.setWordWrap(True)
        row.addWidget(hint)
        return page

    def _build_fields(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(self.tr("Fields: what each byte range means"))
        layout = QtWidgets.QVBoxLayout(box)
        layout.setSpacing(6)

        self.fields_table = QtWidgets.QTableWidget(0, len(_FIELD_COLUMNS))
        self.fields_table.setHorizontalHeaderLabels(
            [self.tr(column) for column in _FIELD_COLUMNS]
        )
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.fields_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.fields_table, 1)

        buttons = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton(self.tr("Add field"))
        add.clicked.connect(self._on_add)
        remove = QtWidgets.QPushButton(self.tr("Remove field"))
        remove.clicked.connect(self._on_remove)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return box

    def _build_message_pane(self, message: bytes) -> QtWidgets.QGroupBox:
        """A read-only hex dump of the message the form describes."""
        box = QtWidgets.QGroupBox(self.tr("Message bytes"))
        layout = QtWidgets.QVBoxLayout(box)
        view = QtWidgets.QPlainTextEdit()
        view.setReadOnly(True)
        view.setFont(theme.mono_font(FONT_SIZE_BODY))
        view.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        view.setMaximumHeight(120)
        view.setPlainText(_hex_dump(message))
        layout.addWidget(view)
        return box

    def _build_preview(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(self.tr("Rule document"))
        layout = QtWidgets.QVBoxLayout(box)
        self.preview = QtWidgets.QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(theme.mono_font(FONT_SIZE_BODY))
        self.preview.setMinimumHeight(120)
        layout.addWidget(self.preview)
        return box

    # -- rows --------------------------------------------------------------

    def _add_row(self, field: dict | None = None) -> None:
        row = _FieldRow()
        if field:
            row.name.setText(str(field.get("name", "")))
            row.offset.setValue(int(field.get("offset", 0)))
            index = row.type.findText(str(field.get("type", "uint8")))
            row.type.setCurrentIndex(max(0, index))
            order = str(field.get("byte_order", "big"))
            row.order.setCurrentIndex(max(0, row.order.findText(order)))
            row.length.setValue(int(field.get("length", 0) or 0))
            row.values.setText(_format_enum(field.get("enum")))
            row.hypothesis.setChecked(bool(field.get("hypothesis", False)))
            row.expected.setText(_format_expected(field.get("expected")))
        index = self.fields_table.rowCount()
        self.fields_table.insertRow(index)
        for column, widget in enumerate(row.widgets()):
            self.fields_table.setCellWidget(index, column, widget)
        self._rows.append(row)
        row.name.textChanged.connect(self._refresh_preview)
        row.offset.valueChanged.connect(self._refresh_preview)
        row.type.currentIndexChanged.connect(self._refresh_preview)
        row.order.currentIndexChanged.connect(self._refresh_preview)
        row.length.valueChanged.connect(self._refresh_preview)
        row.values.textChanged.connect(self._refresh_preview)
        row.hypothesis.toggled.connect(self._refresh_preview)
        row.expected.textChanged.connect(self._refresh_preview)

    def _on_add(self) -> None:
        self._add_row()
        self._refresh_preview()

    def _on_remove(self) -> None:
        row = self.fields_table.currentRow()
        if row < 0 or row >= len(self._rows):
            return
        self.fields_table.removeRow(row)
        self._rows.pop(row)
        self._refresh_preview()

    # -- document ----------------------------------------------------------

    def _framing_dict(self) -> dict:
        kind = self.framing_type.currentText()
        if kind == "length_prefixed":
            return {
                "type": "length_prefixed",
                "length_offset": self.length_offset.value(),
                "length_size": int(self.length_size.currentText()),
                "byte_order": self.length_order.currentText(),
                "length_covers": self.length_covers.currentText(),
            }
        if kind == "fixed_size":
            return {"type": "fixed_size", "size": self.fixed_size.value()}
        if kind == "marker_based":
            framing = {"type": "marker_based"}
            if self.start_bytes.text().strip():
                framing["start_bytes"] = self.start_bytes.text().strip()
            if self.end_bytes.text().strip():
                framing["end_bytes"] = self.end_bytes.text().strip()
            framing["include_markers"] = self.include_markers.isChecked()
            return framing
        return {"type": "manual"}

    def rule_dict(self) -> dict:
        """The rule document the form currently describes."""
        scope = {}
        if self.direction.currentData():
            scope["direction"] = self.direction.currentData()
        return {
            "schema_version": 1,
            "rule_id": self.rule_id.text().strip() or "rule",
            "rule_version": self.rule_version.value(),
            "name": self.rule_name.text().strip(),
            "scope": scope,
            "framing": self._framing_dict(),
            "fields": [row.to_dict() for row in self._rows],
        }

    def rule_text(self) -> str:
        """The rule document as JSON text."""
        return json.dumps(self.rule_dict(), indent=2, ensure_ascii=False)

    def _refresh_preview(self) -> None:
        self.preview.setPlainText(self.rule_text())

    def _load(self, rule: dict) -> None:
        self.rule_id.setText(str(rule.get("rule_id", "rule")))
        self.rule_name.setText(str(rule.get("name", "")))
        self.rule_version.setValue(int(rule.get("rule_version", 1)))
        direction = str((rule.get("scope") or {}).get("direction", ""))
        index = self.direction.findData(direction)
        self.direction.setCurrentIndex(max(0, index))

        framing = rule.get("framing") or {}
        kind = str(framing.get("type", "manual"))
        self.framing_type.setCurrentIndex(max(0, self.framing_type.findText(kind)))
        self.length_offset.setValue(int(framing.get("length_offset", 0)))
        size = str(framing.get("length_size", 2))
        self.length_size.setCurrentIndex(max(0, self.length_size.findText(size)))
        self.length_order.setCurrentIndex(
            max(0, self.length_order.findText(str(framing.get("byte_order", "big"))))
        )
        covers = str(framing.get("length_covers", LENGTH_COVERS_VALUES[0]))
        self.length_covers.setCurrentIndex(max(0, self.length_covers.findText(covers)))
        self.fixed_size.setValue(int(framing.get("size", 1) or 1))
        self.start_bytes.setText(str(framing.get("start_bytes", "")))
        self.end_bytes.setText(str(framing.get("end_bytes", "")))
        self.include_markers.setChecked(bool(framing.get("include_markers", True)))

        for field in rule.get("fields", []):
            self._add_row(field)

    # -- presentation ------------------------------------------------------

    def apply_theme(self) -> None:
        """Read the active theme for the mono preview and the dialog font."""
        self.preview.setFont(theme.mono_font(FONT_SIZE_BODY))
        self.setFont(theme.body_font(FONT_SIZE_BODY))
