"""Interpretation panel.

Three tabs: the rule (editable text with an apply button), the decoded messages
of the current direction, and the counterexamples. A field that the rule marks
as a hypothesis is labelled as such, so an assumption is never shown as a fact.
Selecting a counterexample asks the window to reveal its bytes.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from ..protocol.rule import ALL_FIELD_TYPES, load_rule_text, parse_rule
from . import theme
from .constants import FONT_SIZE_BODY, FONT_SIZE_CAPTION
from .layout import FlowLayout
from .model import (
    MISMATCHED,
    RuleApplication,
)

_STATUS_RANK = {
    "mismatched": 0,
    "incomplete": 1,
    "ambiguous": 2,
    "unknown": 3,
    "uncovered": 4,
    "not_applicable": 5,
    "outdated": 6,
    "matched": 7,
}


def _field_summary(message) -> str:
    parts = []
    marker = " " + QtCore.QCoreApplication.translate("ValidationView", "(hypothesis)")
    for field in message.fields:
        if field.status.value == "not_applicable":
            continue
        value = field.value
        field_marker = marker if field.hypothesis else ""
        if value is None:
            parts.append(
                f"{field.field_name}: {field.reason or field.status.value}{field_marker}"
            )
        else:
            parts.append(f"{field.field_name}={value}{field_marker}")
    return "  ".join(parts)


class ValidationView(QtWidgets.QWidget):
    """Rule editor, message table and counterexample list."""

    applyRequested = QtCore.Signal()
    applyCaptureRequested = QtCore.Signal()
    loadExampleRequested = QtCore.Signal()
    buildRuleRequested = QtCore.Signal()
    counterexampleSelected = QtCore.Signal(
        str, str, int, int
    )  # session, direction, offset, length
    ruleLoaded = QtCore.Signal(str)
    ruleValidityChanged = QtCore.Signal(bool, str)  # valid, message

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._context = QtWidgets.QLabel(self.tr("no capture open"))
        self._context.setProperty("role", "secondary")
        self._context.setFont(theme.body_font(FONT_SIZE_BODY))
        layout.addWidget(self._context)

        self._tabs = QtWidgets.QTabWidget()
        # The rule dock is the narrowest panel; elide its captions rather than
        # let the three of them set a floor on the panel width.
        self._tabs.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self._tabs.setUsesScrollButtons(True)
        layout.addWidget(self._tabs, 1)

        # Rule tab.
        rule_page = QtWidgets.QWidget()
        rule_layout = QtWidgets.QVBoxLayout(rule_page)
        rule_layout.setContentsMargins(0, 0, 0, 0)

        # The overview is what a reader sees first: the rule's name, its state,
        # its framing and its fields, in words. The document editor that produces
        # the rule is one toggle away, not the default surface.
        self._overview = QtWidgets.QWidget()
        overview_layout = QtWidgets.QVBoxLayout(self._overview)
        overview_layout.setContentsMargins(6, 6, 6, 6)
        overview_layout.setSpacing(4)
        self.rule_name = QtWidgets.QLabel()
        self.rule_name.setObjectName("ruleName")
        overview_layout.addWidget(self.rule_name)
        self.rule_state = QtWidgets.QLabel()
        self.rule_state.setProperty("role", "secondary")
        overview_layout.addWidget(self.rule_state)
        self.framing_label = QtWidgets.QLabel()
        self.framing_label.setProperty("role", "secondary")
        overview_layout.addWidget(self.framing_label)
        self.fields_table = QtWidgets.QTableWidget(0, 3)
        self.fields_table.setHorizontalHeaderLabels(["", "", ""])
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.fields_table.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.fields_table.setFont(theme.body_font(FONT_SIZE_BODY))
        overview_layout.addWidget(self.fields_table, 1)
        rule_layout.addWidget(self._overview, 1)

        self.rule_edit = QtWidgets.QPlainTextEdit()
        self.rule_edit.setFont(theme.mono_font(FONT_SIZE_BODY))
        self.rule_edit.setPlaceholderText(self.tr("rule JSON or YAML"))
        self.rule_edit.setVisible(False)
        self._completer = QtWidgets.QCompleter(sorted(ALL_FIELD_TYPES), self)
        self._completer.setWidget(self.rule_edit)
        self._completer.setCompletionMode(
            QtWidgets.QCompleter.CompletionMode.PopupCompletion
        )
        self._completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseSensitive)
        self._completer.activated.connect(self._insert_completion)
        self.rule_edit.installEventFilter(self)
        self.rule_edit.textChanged.connect(self._on_rule_text_changed)
        rule_layout.addWidget(self.rule_edit, 1)
        rule_buttons = FlowLayout(spacing=6)
        self.apply_button = QtWidgets.QPushButton(self.tr("Apply to current direction"))
        self.apply_button.setProperty("accent", "true")
        self.apply_button.clicked.connect(self.applyRequested.emit)
        rule_buttons.addWidget(self.apply_button)
        self.apply_capture_button = QtWidgets.QPushButton(
            self.tr("Apply to whole capture")
        )
        self.apply_capture_button.clicked.connect(self.applyCaptureRequested.emit)
        rule_buttons.addWidget(self.apply_capture_button)
        self.build_button = QtWidgets.QPushButton(self.tr("Build rule..."))
        self.build_button.setToolTip(
            self.tr("Describe the message in a form instead of writing JSON by hand")
        )
        self.build_button.clicked.connect(self.buildRuleRequested.emit)
        rule_buttons.addWidget(self.build_button)
        self.example_button = QtWidgets.QPushButton(self.tr("Load example"))
        self.example_button.setToolTip(self.tr("Load the first rule from examples/"))
        self.example_button.clicked.connect(self.loadExampleRequested.emit)
        rule_buttons.addWidget(self.example_button)
        self.edit_toggle = QtWidgets.QPushButton(self.tr("Edit JSON"))
        self.edit_toggle.setCheckable(True)
        self.edit_toggle.toggled.connect(self._toggle_editor)
        rule_buttons.addWidget(self.edit_toggle)
        rule_layout.addLayout(rule_buttons)
        self.rule_status = QtWidgets.QLabel("")
        self.rule_status.setProperty("role", "secondary")
        self.rule_status.setFont(theme.body_font(FONT_SIZE_BODY))
        self.rule_status.setWordWrap(True)
        rule_layout.addWidget(self.rule_status)
        self._tabs.addTab(rule_page, self.tr("Rule"))
        self._tabs.setTabToolTip(0, self.tr("Rule"))

        # Messages tab.
        self.messages_table = QtWidgets.QTableWidget(0, 4)
        self.messages_table.setHorizontalHeaderLabels(
            [self.tr("offset"), self.tr("len"), self.tr("status"), self.tr("fields")]
        )
        self.messages_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.messages_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.messages_table.setFont(theme.body_font(FONT_SIZE_BODY))
        self.messages_table.verticalHeader().setVisible(False)
        header = self.messages_table.horizontalHeader()
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.messages_table.itemSelectionChanged.connect(self._on_message_selected)
        self._tabs.addTab(self.messages_table, self.tr("Messages"))
        self._show_messages_empty_state()

        # Counterexamples tab.
        counter_page = QtWidgets.QWidget()
        counter_layout = QtWidgets.QVBoxLayout(counter_page)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        self.counter_list = QtWidgets.QListWidget()
        self.counter_list.setFont(theme.body_font(FONT_SIZE_BODY))
        self.counter_list.itemSelectionChanged.connect(self._on_counter_selected)
        counter_layout.addWidget(self.counter_list, 1)
        self._tabs.addTab(counter_page, self.tr("Counterexamples"))

        self._application: RuleApplication | None = None
        self._session_id = ""
        self._direction = ""
        self._status_error = False
        self._message_count = 0

        # The provenance inspector ties a selected byte to its packet. It is part
        # of the primary workspace, not the status line, because a reader checks
        # it constantly while deciding what a field means.
        self.provenance = QtWidgets.QLabel()
        self.provenance.setObjectName("provenanceCard")
        self.provenance.setWordWrap(True)
        self.provenance.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.provenance.setMinimumHeight(64)
        layout.addWidget(self.provenance)

        self.set_provenance([])
        self._has_capture = False
        self._has_rule = False
        self._refresh_apply_state()
        self.set_rule_overview(None, applied=False)

    # -- readiness ---------------------------------------------------------

    def set_ready(self, *, capture: bool, rule: bool) -> None:
        """Record what is open so the apply button can gate itself.

        Applying a rule needs both a capture and a rule. Until both are present
        the apply buttons are disabled rather than left to fail on a click.
        """
        self._has_capture = bool(capture)
        self._has_rule = bool(rule)
        self._refresh_apply_state()

    def _refresh_apply_state(self) -> None:
        ready = self._has_capture and self._has_rule
        for button in (self.apply_button, self.apply_capture_button):
            button.setEnabled(ready)
            button.setToolTip(
                "" if ready else self.tr("Open a capture and a rule first")
            )

    def set_provenance(self, lines: list[str]) -> None:
        """Fill the provenance inspector with the chain for a selected byte."""
        self._provenance_lines = list(lines)
        self.provenance.setText(
            "\n".join(lines) if lines else self.tr("No byte selected")
        )

    def set_rule_overview(self, rule, applied: bool) -> None:
        """Fill the Rule overview from *rule*: its name, framing and fields."""
        self._rule = rule
        self._applied = applied
        if rule is None:
            self.rule_name.setText(self.tr("No rule loaded"))
            self.rule_state.setText("")
            self.framing_label.setText("")
            self.fields_table.setRowCount(0)
            return
        self.rule_name.setText(self.tr("Rule: {0}").format(rule.name or rule.rule_id))
        self.rule_state.setText(
            self.tr("Status: checked") if applied else self.tr("Status: not checked")
        )
        self.framing_label.setText(
            self.tr("Framing: {0}").format(_framing_label(rule.framing))
        )
        fields = rule.fields or []
        self.fields_table.setRowCount(len(fields))
        for row, field in enumerate(fields):
            cells = (
                field.name,
                self.tr("offset {0}, {1}").format(field.offset, field.type),
                self.tr("assumption") if field.hypothesis else "",
            )
            for column, text in enumerate(cells):
                item = QtWidgets.QTableWidgetItem(str(text))
                item.setForeground(QtGui.QColor(theme.current().text_secondary))
                self.fields_table.setItem(row, column, item)
        self.fields_table.resizeColumnsToContents()

    def _toggle_editor(self, editing: bool) -> None:
        """Switch the Rule tab between the overview and the JSON editor."""
        self._overview.setVisible(not editing)
        self.rule_edit.setVisible(editing)
        self.edit_toggle.setText(
            self.tr("View overview") if editing else self.tr("Edit JSON")
        )

    # -- rule --------------------------------------------------------------

    def set_rule_text(self, text: str) -> None:
        """Replace the rule editor contents with ``text``."""
        self.rule_edit.setPlainText(text)

    def rule_text(self) -> str:
        """The current rule editor contents."""
        return self.rule_edit.toPlainText()

    def set_rule_status(self, text: str, error: bool = False) -> None:
        """Show ``text`` in the rule status line, red when ``error``."""
        self._status_error = error
        self._style_status()
        self.rule_status.setText(text)

    def _style_status(self) -> None:
        colour = (
            theme.current().status_mismatched_text
            if self._status_error
            else theme.current().text_secondary
        )
        self.rule_status.setStyleSheet(f"color: {colour};")

    def set_context(self, session_id: str, direction: str) -> None:
        """Show which session and direction the panel is working on."""
        self._session_id = session_id
        self._direction = direction
        self._context.setText(
            self.tr("session {0}   {1}").format(session_id, direction)
        )

    # -- editor feedback ---------------------------------------------------

    def _on_rule_text_changed(self) -> None:
        """Validate the rule text as it is typed.

        An empty editor is not an error: it is the state before a rule is
        loaded. Any other text must parse and build a rule; a failure is
        reported in the status line and by :attr:`ruleValidityChanged` without
        touching the current application.
        """
        text = self.rule_edit.toPlainText()
        if not text.strip():
            self.set_rule_status("")
            self.ruleValidityChanged.emit(False, "empty")
            return
        try:
            parse_rule(load_rule_text(text))
        except Exception as exc:
            self.set_rule_status(self.tr("invalid rule: {0}").format(exc), error=True)
            self.ruleValidityChanged.emit(False, str(exc))
            return
        self.set_rule_status(self.tr("rule parses"))
        self.ruleValidityChanged.emit(True, "")

    def _insert_completion(self, completion: str) -> None:
        """Insert ``completion`` at the text cursor, replacing the prefix."""
        cursor = self.rule_edit.textCursor()
        prefix = self._completion_prefix(cursor)
        cursor.movePosition(
            QtGui.QTextCursor.MoveOperation.Left,
            QtGui.QTextCursor.MoveMode.KeepAnchor,
            len(prefix),
        )
        cursor.insertText(completion)
        self.rule_edit.setTextCursor(cursor)

    def _completion_prefix(self, cursor: QtGui.QTextCursor) -> str:
        """The identifier characters immediately before ``cursor``."""
        text = self.rule_edit.toPlainText()
        position = cursor.position()
        start = position
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            start -= 1
        return text[start:position]

    def eventFilter(self, obj, event):
        """Offer a field-type completion while the rule editor is typed into.

        The completer lives on the panel but the keystrokes go to the editor, so
        the editor's events are filtered here rather than handled in a
        ``keyPressEvent`` the panel would never receive.
        """
        if obj is self.rule_edit and event.type() == QtCore.QEvent.Type.KeyPress:
            completer = self._completer
            if completer.popup().isVisible() and event.key() in (
                QtCore.Qt.Key.Key_Enter,
                QtCore.Qt.Key.Key_Return,
                QtCore.Qt.Key.Key_Escape,
                QtCore.Qt.Key.Key_Tab,
                QtCore.Qt.Key.Key_Backtab,
            ):
                event.ignore()
                return True
            is_shortcut = (
                event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
                and event.key() in (QtCore.Qt.Key.Key_E, QtCore.Qt.Key.Key_J)
            )
            if not is_shortcut and event.text() and not event.text().isspace():
                prefix = self._completion_prefix(self.rule_edit.textCursor())
                if prefix:
                    completer.setCompletionPrefix(prefix)
                    if completer.completionCount():
                        rect = self.rule_edit.cursorRect()
                        rect.setWidth(
                            completer.popup().sizeHintForColumn(0)
                            + completer.popup().verticalScrollBar().sizeHint().width()
                        )
                        completer.complete(rect)
        return super().eventFilter(obj, event)

    def show_rule_validity(self, valid: bool, message: str) -> None:
        """Report the parse state of the rule editor."""
        if valid:
            self.set_rule_status(self.tr("rule parses"))
        elif message == "empty":
            self.set_rule_status("")
        else:
            self.set_rule_status(
                self.tr("invalid rule: {0}").format(message), error=True
            )

    # -- results -----------------------------------------------------------

    def _show_messages_empty_state(self) -> None:
        """State in the table why it is empty, instead of leaving it blank."""
        self.messages_table.setRowCount(1)
        self.messages_table.setSpan(0, 0, 1, 4)
        item = QtWidgets.QTableWidgetItem(
            self.tr(
                "no messages yet - apply a rule to this direction (F5) or to the capture (F6)"
            )
        )
        item.setForeground(QtGui.QColor(theme.current().text_secondary))
        self.messages_table.setItem(0, 0, item)

    def show_application(self, application: RuleApplication) -> None:
        """Fill the message table and counterexample list from *application*."""
        self._application = application
        self.messages_table.clearSpans()
        self.messages_table.setRowCount(0)
        ordered = sorted(
            application.messages,
            key=lambda m: (_STATUS_RANK.get(m.status.value, 9), m.offset),
        )
        if not ordered:
            self._show_messages_empty_state()
            self._message_count = 0
        else:
            self._message_count = len(ordered)
        self.messages_table.setRowCount(len(ordered))
        for row, message in enumerate(ordered):
            self._fill_row(row, message)

        self.counter_list.clear()
        counterexamples = sorted(application.counterexamples, key=lambda m: m.offset)
        for message in counterexamples:
            item = QtWidgets.QListWidgetItem(
                f"offset {message.offset}  {message.bytes_hex}  {message.reason or ''}"
            )
            item.setForeground(QtGui.QColor(theme.current().status_mismatched_text))
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                (
                    application.session_id,
                    application.direction,
                    message.offset,
                    message.length,
                ),
            )
            item.setToolTip(_provenance_tooltip(message))
            self.counter_list.addItem(item)
        if not counterexamples:
            # A run with no mismatch in this direction is not a proof; say so,
            # and point at the corpus run, which is where mismatches appear.
            self.counter_list.addItem(
                QtWidgets.QListWidgetItem(
                    self.tr("no counterexamples in this direction")
                )
            )

        counts = application.counts
        summary = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        self._tabs.setTabText(1, self.tr("Messages ({0})").format(len(ordered)))
        self._tabs.setTabText(
            2, self.tr("Counterexamples ({0})").format(len(counterexamples))
        )
        if not self.rule_status.text():
            self.set_rule_status(
                self.tr("rule v{0}  {1}").format(application.rule.rule_version, summary)
            )

    def _fill_row(self, row: int, message) -> None:
        cells = [
            f"{message.offset}",
            f"{message.length}",
            message.status.value,
            _field_summary(message),
        ]
        for column, text in enumerate(cells):
            item = QtWidgets.QTableWidgetItem(text)
            if column == 3:
                item.setFont(theme.mono_font(FONT_SIZE_BODY))
            if message.status.value == MISMATCHED:
                item.setForeground(QtGui.QColor(theme.current().status_mismatched_text))
            elif message.status.value == "matched":
                item.setForeground(QtGui.QColor(theme.current().status_matched_text))
            self.messages_table.setItem(row, column, item)
        self.messages_table.item(row, 0).setData(
            QtCore.Qt.ItemDataRole.UserRole, message.offset
        )

    def _on_message_selected(self) -> None:
        rows = self.messages_table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        item = self.messages_table.item(row, 0)
        if item is None or item.data(QtCore.Qt.ItemDataRole.UserRole) is None:
            return  # the empty-state row carries no offset
        length = int(self.messages_table.item(row, 1).text())
        self.counterexampleSelected.emit(
            self._session_id,
            self._direction,
            int(item.data(QtCore.Qt.ItemDataRole.UserRole)),
            length,
        )

    def _on_counter_selected(self) -> None:
        items = self.counter_list.selectedItems()
        if not items:
            return
        data = items[0].data(QtCore.Qt.ItemDataRole.UserRole)
        if data is None:  # the "no counterexamples" placeholder
            return
        session_id, direction, offset, length = data
        self.counterexampleSelected.emit(session_id, direction, offset, length)

    def show_corpus_report(self, report) -> None:
        """Fill the counterexample list from a whole-capture report.

        A whole-capture run frames every direction, so its counterexamples carry
        their own session and direction. The list is filled here so the tab and
        the status line agree after a capture-wide run, and so a corpus
        counterexample can be jumped to. The message table is not rebuilt: it
        shows one direction, and mixing directions into it would be misleading.
        """
        self.counter_list.clear()
        for counter in sorted(
            report.contradictions,
            key=lambda c: (c.session_id, c.direction, c.message_offset),
        ):
            text = (
                f"{counter.session_id} {counter.direction}  "
                f"offset {counter.message_offset}  {counter.bytes_hex or ''}  {counter.reason or ''}"
            )
            item = QtWidgets.QListWidgetItem(text)
            item.setForeground(QtGui.QColor(theme.current().status_mismatched_text))
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                (
                    counter.session_id,
                    counter.direction,
                    counter.message_offset,
                    counter.message_length,
                ),
            )
            item.setToolTip(_counter_provenance_tooltip(counter))
            self.counter_list.addItem(item)
        if not report.contradictions:
            self.counter_list.addItem(
                QtWidgets.QListWidgetItem(self.tr("no counterexamples in this capture"))
            )
        self._tabs.setTabText(
            2, self.tr("Counterexamples ({0})").format(len(report.contradictions))
        )

    @property
    def counterexample_count(self) -> int:
        """Number of real counterexample rows, excluding the empty-state note."""
        return sum(
            1
            for row in range(self.counter_list.count())
            if self.counter_list.item(row).data(QtCore.Qt.ItemDataRole.UserRole)
            is not None
        )

    def show_message_count(self, count: int) -> None:
        """Show that the rule was applied to ``count`` messages."""
        self.set_rule_status(self.tr("rule applied to {0} messages").format(count))

    def retranslate_ui(self) -> None:
        """Re-apply the static labels to the active interface language.

        Only labels the view owns are refreshed. Table contents are rebuilt
        when a rule is next applied, so a language switch never leaves stale
        translations on the controls themselves.
        """
        self.rule_edit.setPlaceholderText(self.tr("rule JSON or YAML"))
        self.apply_button.setText(self.tr("Apply to current direction"))
        self.apply_capture_button.setText(self.tr("Apply to whole capture"))
        self.build_button.setText(self.tr("Build rule..."))
        self.build_button.setToolTip(
            self.tr("Describe the message in a form instead of writing JSON by hand")
        )
        self.example_button.setText(self.tr("Load example"))
        self.example_button.setToolTip(self.tr("Load the first rule from examples/"))
        self.edit_toggle.setText(
            self.tr("View overview")
            if self.edit_toggle.isChecked()
            else self.tr("Edit JSON")
        )
        self.fields_table.setHorizontalHeaderLabels(
            [self.tr("field"), self.tr("layout"), self.tr("note")]
        )
        if self._rule is not None:
            self.set_rule_overview(self._rule, applied=getattr(self, "_applied", False))
        else:
            self.set_rule_overview(None, applied=False)
        if not self._context.text() or not self._session_id:
            self._context.setText(self.tr("no capture open"))
        self._tabs.setTabText(0, self.tr("Rule"))
        self._tabs.setTabToolTip(0, self.tr("Rule"))
        self._refresh_apply_state()
        self.messages_table.setHorizontalHeaderLabels(
            [self.tr("offset"), self.tr("len"), self.tr("status"), self.tr("fields")]
        )
        self._tabs.setTabText(1, self.tr("Messages ({0})").format(self._message_count))
        self._tabs.setTabToolTip(
            1, self.tr("Messages ({0})").format(self._message_count)
        )
        self._tabs.setTabText(
            2, self.tr("Counterexamples ({0})").format(self.counterexample_count)
        )
        self._tabs.setTabToolTip(
            2, self.tr("Counterexamples ({0})").format(self.counterexample_count)
        )
        if self._context.text() and self._session_id:
            self._context.setText(
                self.tr("session {0}   {1}").format(self._session_id, self._direction)
            )
        # The provenance inspector and the rule-status line are stored as
        # content, not as controls, so they are re-rendered here from what is
        # kept rather than left in the previous language.
        self.set_provenance(getattr(self, "_provenance_lines", []))

    def apply_theme(self) -> None:
        """Recolour the status line and rebuild the table in the active theme."""
        self._style_status()
        self.provenance.setStyleSheet(
            f"""
            QLabel#provenanceCard {{
                background: {theme.current().surface_alt};
                border: 1px solid {theme.current().border};
                border-radius: {theme.current().radius}px;
                padding: 6px 8px;
                color: {theme.current().text_secondary};
                font-size: {FONT_SIZE_CAPTION}pt;
            }}
            """
        )
        self.provenance.setFont(theme.mono_font(FONT_SIZE_CAPTION))
        self.rule_name.setFont(theme.heading_font(FONT_SIZE_BODY + 2))
        if self._application is not None:
            self.show_application(self._application)


def _framing_label(framing) -> str:
    """A short human label for a rule's framing section (a plain mapping)."""
    if not isinstance(framing, dict):
        return "-"
    kind = str(framing.get("type", ""))
    if kind == "length_prefixed":
        size = framing.get("length_size", framing.get("size", 0))
        return f"length_prefix ({size} bytes)"
    if kind == "fixed_size":
        return f"fixed_size ({framing.get('size', 0)} bytes)"
    if kind == "marker_based":
        return "marker_based"
    return kind or "-"


def _provenance_tooltip(message) -> str:
    for field in message.fields:
        provenance = field.provenance_range
        if provenance:
            packets = provenance.get("packets")
            label = f"packets {packets}" if packets else ""
            if provenance.get("seq") is not None:
                label += f"  seq {provenance['seq']}"
            if provenance.get("ts") is not None:
                label += f"  ts {provenance['ts']}"
            label += f"\n{message.bytes_hex}"
            return label.strip()
    return message.bytes_hex


def _counter_provenance_tooltip(counter) -> str:
    """A tooltip for a corpus counterexample: session, direction and packets."""
    parts = [
        f"{counter.session_id} {counter.direction}",
        f"offset {counter.message_offset}",
    ]
    provenance = counter.provenance_range or {}
    packets = provenance.get("packets")
    if packets:
        parts.append(f"packets {packets}")
    if provenance.get("seq") is not None:
        parts.append(f"seq {provenance['seq']}")
    if provenance.get("ts") is not None:
        parts.append(f"ts {provenance['ts']}")
    if counter.bytes_hex:
        parts.append(counter.bytes_hex)
    return "\n".join(str(p) for p in parts)
