"""First-run guide: the four steps from a capture to a checked rule.

The window is dense by design, and a newcomer cannot tell from the panels alone
in which order they are meant to be used. This panel names the four steps, marks
the ones already done, and offers the button that performs the next one, so the
tool can be driven without reading the manual first.

The panel is a plain widget, not a dialog: it lives above the workspace and is
hidden once a capture, a rule and an applied rule are all present, because by
then the workspace itself shows what to do.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from . import theme
from .constants import FONT_SIZE_BODY, FONT_SIZE_CAPTION


class _Step(QtWidgets.QFrame):
    """One numbered step: a title, a hint, an action and a done marker."""

    def __init__(self, number: int, title: str, hint: str, action: str | None) -> None:
        super().__init__()
        self.setObjectName("guideStep")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.number = QtWidgets.QLabel(str(number))
        self.number.setObjectName("guideStepNumber")
        self.number.setFixedWidth(18)
        self.number.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        layout.addWidget(self.number)

        text = QtWidgets.QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)
        self.title = QtWidgets.QLabel(title)
        self.title.setObjectName("guideStepTitle")
        self.hint = QtWidgets.QLabel(hint)
        self.hint.setObjectName("guideStepHint")
        self.hint.setWordWrap(True)
        text.addWidget(self.title)
        text.addWidget(self.hint)
        layout.addLayout(text, 1)

        self.marker = QtWidgets.QLabel()
        self.marker.setObjectName("guideStepMarker")
        self.marker.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.marker)

        self.button: QtWidgets.QPushButton | None = None
        if action is not None:
            self.button = QtWidgets.QPushButton(action)
            self.button.setObjectName("guideStepAction")
            self.button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self.button)

    def set_state(self, state: str) -> None:
        """Colour the step: ``done``, ``next`` or ``todo``."""
        self.setProperty("state", state)
        self.marker.setText({"done": "✓", "next": "→"}.get(state, ""))
        self.title.setProperty("state", state)
        for widget in (self, self.number, self.title, self.marker):
            widget.style().unpolish(widget)
            widget.style().polish(widget)


class GuidePanel(QtWidgets.QFrame):
    """The four-step guide shown above the workspace on a fresh window.

    Emits the same three intentions the menu offers, so the window wires the
    buttons to the existing slots and the guide stays free of application logic.
    """

    openCaptureRequested = QtCore.Signal()
    openRuleRequested = QtCore.Signal()
    applyRequested = QtCore.Signal()
    dismissRequested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("guidePanel")

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(8)

        head = QtWidgets.QHBoxLayout()
        head.setSpacing(8)
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("guideTitle")
        head.addWidget(self.title)
        head.addStretch(1)
        self.hide_button = QtWidgets.QPushButton()
        self.hide_button.setObjectName("guideDismiss")
        self.hide_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.hide_button.clicked.connect(self.dismissRequested.emit)
        head.addWidget(self.hide_button)
        outer.addLayout(head)

        self.status = QtWidgets.QLabel()
        self.status.setObjectName("guideStatus")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)

        self.step_capture = _Step(1, "", "", "")
        self.step_session = _Step(2, "", "", None)
        self.step_rule = _Step(3, "", "", "")
        self.step_apply = _Step(4, "", "", "")
        for step in (
            self.step_capture,
            self.step_session,
            self.step_rule,
            self.step_apply,
        ):
            outer.addWidget(step)
        self.step_capture.button.clicked.connect(self.openCaptureRequested.emit)
        self.step_rule.button.clicked.connect(self.openRuleRequested.emit)
        self.step_apply.button.clicked.connect(self.applyRequested.emit)

        self._capture_name: str | None = None
        self._session_ready = False
        self._rule_name: str | None = None
        self._applied = False
        self.retranslate_ui()
        self.apply_theme()

    # -- state -------------------------------------------------------------

    def set_capture(self, name: str | None) -> None:
        """Record the open capture (its file name), or ``None`` when closed."""
        self._capture_name = name
        self._refresh()

    def set_session_ready(self, ready: bool) -> None:
        """Record whether a session and a direction are selected."""
        self._session_ready = bool(ready)
        self._refresh()

    def set_rule(self, name: str | None) -> None:
        """Record the open rule (its file name or title), or ``None``."""
        self._rule_name = name
        self._refresh()

    def set_applied(self, applied: bool) -> None:
        """Record whether the rule has been applied at least once."""
        self._applied = bool(applied)
        self._refresh()

    def _refresh(self) -> None:
        capture_done = self._capture_name is not None
        session_done = capture_done and self._session_ready
        rule_done = self._rule_name is not None
        apply_done = rule_done and session_done and self._applied

        if capture_done and rule_done and apply_done:
            # Nothing left to explain; the workspace is self-describing now.
            self.setVisible(False)
            return
        self.setVisible(True)

        self.step_capture.set_state("done" if capture_done else "next")
        self.step_session.set_state(
            "done" if session_done else ("next" if capture_done else "todo")
        )
        self.step_rule.set_state(
            "done" if rule_done else ("next" if session_done else "todo")
        )
        self.step_apply.set_state(
            "done" if apply_done else ("next" if rule_done else "todo")
        )

        if self.step_capture.button is not None:
            self.step_capture.button.setVisible(not capture_done)
        if self.step_rule.button is not None:
            self.step_rule.button.setVisible(not rule_done)
        if self.step_apply.button is not None:
            self.step_apply.button.setVisible(
                rule_done and session_done and not apply_done
            )

        self.status.setText(self._status_text())

    def _status_text(self) -> str:
        if self._capture_name is None:
            return self.tr(
                "Nothing is open yet. The tool reads a capture file (pcap, pcapng "
                "or the normalized JSON) and a rule that says how to read it."
            )
        parts = [self.tr("capture: {0}").format(self._capture_name)]
        if self._rule_name is not None:
            parts.append(self.tr("rule: {0}").format(self._rule_name))
        else:
            parts.append(self.tr("no rule yet"))
        return "   ·   ".join(parts)

    # -- presentation ------------------------------------------------------

    def retranslate_ui(self) -> None:
        """Re-apply every caption in the active interface language."""
        self.title.setText(self.tr("Start here"))
        self.hide_button.setText(self.tr("Hide"))
        self.hide_button.setToolTip(
            self.tr("Hide the guide; Help - Quick help brings it back")
        )
        self.status.setToolTip(self.tr("What is open right now"))
        self.step_capture.title.setText(self.tr("Open a capture"))
        self.step_capture.hint.setText(
            self.tr("pcap, pcapng or normalized JSON. Ctrl+O.")
        )
        self.step_capture.button.setText(self.tr("Open capture..."))
        self.step_session.title.setText(self.tr("Pick a session and a direction"))
        self.step_session.hint.setText(
            self.tr(
                "Choose the connection on the left; A to B and B to A are listed under it."
            )
        )
        self.step_rule.title.setText(self.tr("Load or build a rule"))
        self.step_rule.hint.setText(
            self.tr(
                "A rule says how the bytes are cut into messages and what each field means. Ctrl+R."
            )
        )
        self.step_rule.button.setText(self.tr("Open rule..."))
        self.step_apply.title.setText(self.tr("Apply the rule and read the verdicts"))
        self.step_apply.hint.setText(
            self.tr(
                "F5 applies it to the current direction, F6 to the whole capture. Mismatches are kept as counterexamples."
            )
        )
        self.step_apply.button.setText(self.tr("Apply to direction"))
        self._refresh()

    def apply_theme(self) -> None:
        """Re-read the active theme for the panel and its steps."""
        token = theme.current()
        radius = token.radius
        self.setStyleSheet(
            f"""
            QFrame#guidePanel {{
                background: {token.surface_alt};
                border: 1px solid {token.border};
                border-radius: {radius}px;
            }}
            QLabel#guideTitle {{
                color: {token.text_primary};
                font-size: {FONT_SIZE_BODY + 2}pt;
            }}
            QLabel#guideStatus {{ color: {token.text_secondary}; font-size: {FONT_SIZE_CAPTION}pt; }}
            QPushButton#guideDismiss {{
                background: transparent;
                color: {token.text_secondary};
                border: 1px solid {token.border};
                border-radius: {radius}px;
                padding: 2px 10px;
            }}
            QPushButton#guideDismiss:hover {{ color: {token.text_primary}; }}
            QFrame#guideStep {{
                background: {token.surface};
                border: 1px solid {token.border};
                border-radius: {radius}px;
            }}
            QFrame#guideStep[state="next"] {{ border: 1px solid {token.accent}; }}
            QLabel#guideStepNumber {{ color: {token.text_secondary}; font-size: {FONT_SIZE_BODY}pt; }}
            QLabel#guideStepTitle {{ color: {token.text_primary}; font-size: {FONT_SIZE_BODY}pt; }}
            QLabel#guideStepTitle[state="done"] {{ color: {token.status_matched_text}; }}
            QLabel#guideStepHint {{ color: {token.text_secondary}; font-size: {FONT_SIZE_CAPTION}pt; }}
            QLabel#guideStepMarker {{ color: {token.status_matched_text}; font-size: {FONT_SIZE_BODY}pt; }}
            QPushButton#guideStepAction {{
                background: {token.accent};
                color: {token.text_on_accent};
                border: none;
                border-radius: {radius}px;
                padding: 4px 12px;
            }}
            QPushButton#guideStepAction:hover {{ background: {token.accent_hover}; }}
            """
        )
        self.title.setFont(theme.heading_font(FONT_SIZE_BODY + 2))
        self.status.setFont(theme.body_font(FONT_SIZE_CAPTION))
        for step in (
            self.step_capture,
            self.step_session,
            self.step_rule,
            self.step_apply,
        ):
            step.title.setFont(theme.body_font(FONT_SIZE_BODY))
            step.hint.setFont(theme.body_font(FONT_SIZE_CAPTION))
            step.number.setFont(theme.body_font(FONT_SIZE_BODY))
            step.marker.setFont(theme.body_font(FONT_SIZE_BODY))
