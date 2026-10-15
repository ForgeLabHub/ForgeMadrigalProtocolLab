"""Corpus verification dialog.

A rule that holds on one message is a guess. The dialog puts the rule against
every direction of the open capture at once and reports, per status, how much of
the corpus it explains and where it is contradicted. Each counterexample carries
its session, direction and byte range, so selecting one asks the window to jump
to the bytes that disagree.

The result table is virtualised through a ``QAbstractTableModel``, so a corpus
with a hundred thousand messages is a scrolling list, not a hundred thousand
widgets.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from . import theme
from .constants import FONT_SIZE_BODY, FONT_SIZE_CAPTION

_DIALOG_SIZE = (900, 620)
_NO_PARENT = QtCore.QModelIndex()


class _CounterexampleModel(QtCore.QAbstractTableModel):
    """Virtualised model over a report's counterexamples."""

    _HEADERS = ("#", "session", "offset", "bytes", "why")

    def _header_text(self, section: int) -> str:
        """The translated caption for a column.

        Literal ``translate`` calls rather than indexing a table built from
        ``_HEADERS``: lupdate only extracts a string it can see at the call
        site, and a table built at import time would freeze the language.
        """
        captions = (
            QtCore.QCoreApplication.translate("CorpusDialog", "#"),
            QtCore.QCoreApplication.translate("CorpusDialog", "session"),
            QtCore.QCoreApplication.translate("CorpusDialog", "offset"),
            QtCore.QCoreApplication.translate("CorpusDialog", "bytes"),
            QtCore.QCoreApplication.translate("CorpusDialog", "why"),
        )
        return captions[section]

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list = []

    def set_rows(self, rows: list) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_at(self, row: int):
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def rowCount(self, parent=_NO_PARENT) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=_NO_PARENT) -> int:
        return 0 if parent.isValid() else len(self._HEADERS)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation != QtCore.Qt.Orientation.Horizontal:
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._header_text(section)
        return None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        counter = self._rows[index.row()]
        column = index.column()
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return {
                0: str(index.row() + 1),
                1: f"{counter.session_id} {counter.direction}",
                2: f"0x{counter.message_offset:04x}",
                3: counter.bytes_hex or "",
                4: counter.reason or "",
            }.get(column, "")
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return counter
        return None


class _CountBar(QtWidgets.QWidget):
    """One status count with a proportional bar."""

    def __init__(self, label: str, value: int, total: int, kind: str) -> None:
        super().__init__()
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.label = QtWidgets.QLabel(label)
        self.label.setFixedWidth(120)
        row.addWidget(self.label)
        self.value = QtWidgets.QLabel(str(value))
        self.value.setFixedWidth(56)
        row.addWidget(self.value)
        self.bar = QtWidgets.QProgressBar()
        self.bar.setRange(0, max(1, total))
        self.bar.setValue(value)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        row.addWidget(self.bar, 1)
        self.percent = QtWidgets.QLabel(f"{round(100 * value / max(1, total))}%")
        self.percent.setFixedWidth(48)
        row.addWidget(self.percent)
        for widget in (self.label, self.value, self.percent):
            widget.setFont(theme.body_font(FONT_SIZE_CAPTION + 2))
        self.bar.setStyleSheet(_bar_stylesheet(kind))


def _bar_stylesheet(kind: str) -> str:
    token = theme.current()
    colour = {
        "matched": token.status_matched_text,
        "mismatched": token.status_mismatched_text,
        "incomplete": token.status_incomplete_text,
        "ambiguous": token.status_ambiguous_text,
    }.get(kind, token.text_secondary)
    return (
        f"QProgressBar {{ background: {token.surface_alt}; border: none;"
        f" border-radius: 2px; }}"
        f"QProgressBar::chunk {{ background: {colour}; border-radius: 2px; }}"
    )


class CorpusDialog(QtWidgets.QDialog):
    """Whole-capture verification of one rule, with its counterexamples."""

    counterexampleSelected = QtCore.Signal(
        str, str, int, int
    )  # session, dir, offset, len
    exportReportRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("corpusDialog")
        self.setModal(False)
        self.resize(*_DIALOG_SIZE)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        self.heading = QtWidgets.QLabel()
        self.heading.setObjectName("corpusHeading")
        outer.addWidget(self.heading)

        self.context = QtWidgets.QLabel()
        self.context.setProperty("role", "secondary")
        outer.addWidget(self.context)

        self.bars_host = QtWidgets.QWidget()
        self._bar_layout = QtWidgets.QVBoxLayout(self.bars_host)
        self._bar_layout.setContentsMargins(0, 0, 0, 0)
        self._bar_layout.setSpacing(4)
        outer.addWidget(self.bars_host)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        outer.addWidget(line)

        self.model = _CounterexampleModel(self)
        self.table = QtWidgets.QTableView()
        self.table.setModel(self.model)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(theme.body_font(FONT_SIZE_BODY))
        self.table.horizontalHeader().setSectionResizeMode(
            4, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.clicked.connect(self._on_clicked)
        outer.addWidget(self.table, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.export_button = QtWidgets.QPushButton()
        self.export_button.setObjectName("secondaryButton")
        self.export_button.clicked.connect(self.exportReportRequested.emit)
        buttons.addWidget(self.export_button)
        self.close_button = QtWidgets.QPushButton()
        self.close_button.setObjectName("secondaryButton")
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)
        outer.addLayout(buttons)

        self.retranslate_ui()
        self.apply_theme()

    # -- data --------------------------------------------------------------

    def show_report(self, report, sessions: int) -> None:
        """Fill the dialog from a verification report."""
        counts = report.counts()
        total = max(1, report.total)
        self.context.setText(
            self.tr("Corpus: {0} sessions, {1} messages. Rule: {2} v{3}").format(
                sessions, report.total, report.rule_id, report.rule_version
            )
        )
        while self._bar_layout.count():
            item = self._bar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for label, key, kind in (
            (self.tr("Matched"), "matched", "matched"),
            (self.tr("Mismatched"), "mismatched", "mismatched"),
            (self.tr("Incomplete"), "incomplete", "incomplete"),
            (self.tr("Ambiguous"), "ambiguous", "ambiguous"),
        ):
            self._bar_layout.addWidget(
                _CountBar(label, counts.get(key, 0), total, kind)
            )
        self.model.set_rows(list(report.contradictions))

    def _on_clicked(self, index: QtCore.QModelIndex) -> None:
        counter = self.model.row_at(index.row())
        if counter is not None:
            self.counterexampleSelected.emit(
                counter.session_id,
                counter.direction,
                counter.message_offset,
                counter.message_length,
            )

    # -- presentation ------------------------------------------------------

    def retranslate_ui(self) -> None:
        """Re-apply the captions in the active interface language."""
        self.setWindowTitle(self.tr("Corpus check"))
        self.heading.setText(self.tr("Rule check on the corpus"))
        self.export_button.setText(self.tr("Export Markdown report"))
        self.close_button.setText(self.tr("Close"))

    def apply_theme(self) -> None:
        """Re-read the active theme for the dialog."""
        token = theme.current()
        self.setStyleSheet(
            f"""
            QDialog#corpusDialog {{ background: {token.background}; }}
            QLabel#corpusHeading {{
                color: {token.text_primary};
                font-size: {FONT_SIZE_BODY + 6}pt;
                font-weight: 600;
            }}
            """
        )
        self.heading.setFont(theme.heading_font(FONT_SIZE_BODY + 6))
