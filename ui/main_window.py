import sys
import math
import threading

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QSizePolicy,
)

# your project root must be on sys.path when running this file directly,
# e.g. `python -m ui.main_window` from the project root, or add the
# project root to sys.path before this import.
import main as orion_core


class OrionBridge(QObject):
    """
    Runs orion_core.start_orion() on a background QThread and re-emits
    its plain-callable hooks as Qt signals, so updates land on the UI
    thread safely instead of touching widgets from a worker thread.
    """
    status_changed = Signal(str)
    message_received = Signal(str, str)

    def run(self):
        orion_core.on_status = lambda s: self.status_changed.emit(s)
        orion_core.on_message = lambda t, r: self.message_received.emit(t, r)
        orion_core.start_orion()

    def stop(self):
        orion_core.stop_orion()


# ---------------------------------------------------------------------------
# Palette - matched to the reference: near-black bg, teal/cyan glow accent
# ---------------------------------------------------------------------------
BG = "#0A0B0D"
PANEL = "#14171C"
PANEL_2 = "#1B1F26"
BORDER = "#262B33"
TEXT = "#EDEDED"
MUTED = "#8A8F98"
TEAL = "#3ED6C5"
TEAL_DEEP = "#1FA394"
GOLD = "#F2C94C"

CARD_BLUE_BG, CARD_BLUE_TEXT = "#B9E6E2", "#0E4A45"
CARD_PINK_BG, CARD_PINK_TEXT = "#F3C9C9", "#6B1F1F"
CARD_GREEN_BG, CARD_GREEN_TEXT = "#C9EFC0", "#264D1B"

FONT_FAMILY = "Segoe UI, -apple-system, sans-serif"


class DotGrid(QWidget):
    """Faint background dot grid, matching the reference's textured canvas."""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 12)))
        step = 24
        for x in range(0, self.width(), step):
            for y in range(0, self.height(), step):
                p.drawEllipse(x, y, 1, 1)
        p.end()


class GlowOrb(QWidget):
    """Teal/cyan glow blob hero, pulsing like the reference's swirl orb."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 160)
        self._glow = 0.4
        self.active = False

        self._anim = QPropertyAnimation(self, b"glow")
        self._anim.setDuration(2600)
        self._anim.setStartValue(0.35)
        self._anim.setEndValue(0.85)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.finished.connect(self._reverse)
        self._forward = True
        self._anim.start()

    def _reverse(self):
        self._forward = not self._forward
        self._anim.setStartValue(0.85 if not self._forward else 0.35)
        self._anim.setEndValue(0.35 if not self._forward else 0.85)
        self._anim.start()

    def getGlow(self):
        return self._glow

    def setGlow(self, v):
        self._glow = v
        self.update()

    glow = Property(float, getGlow, setGlow)

    def set_listening(self, is_listening: bool):
        self.active = is_listening
        self._anim.setDuration(900 if is_listening else 2600)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 * 0.85

        accent = QColor(GOLD if self.active else TEAL)

        grad = QRadialGradient(cx, cy, r)
        c1 = QColor(accent)
        c1.setAlphaF(0.55 * self._glow)
        c2 = QColor(accent)
        c2.setAlphaF(0.0)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        core = QColor(accent)
        core.setAlphaF(0.85)
        p.setBrush(QBrush(core))
        cr = r * 0.28
        p.drawEllipse(cx - cr, cy - cr, cr * 2, cr * 2)
        p.end()


class MicButton(QPushButton):
    """
    Status indicator, not a push-to-talk toggle - Orion is always
    listening for its wake word. The ring animates while Orion is
    actively listening for a command; clicking mutes/unmutes it.
    """

    mute_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to mute/unmute Orion")
        self.listening = False
        self.speaking = False
        self.muted = False
        self._ring = 0.0

        self._anim = QPropertyAnimation(self, b"ring")
        self._anim.setDuration(1100)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.clicked.connect(self._toggle_mute)

    def _toggle_mute(self):
        self.muted = not self.muted
        self.mute_toggled.emit(self.muted)

    def set_status(self, status: str):
        """status: 'idle' | 'active' | 'listening' | 'speaking'"""
        self.listening = status == "listening"
        self.speaking = status == "speaking"
        if self.listening:
            self._anim.start()
        else:
            self._anim.stop()
            self._ring = 0.0
        self.update()

    def getRing(self):
        return self._ring

    def setRing(self, v):
        self._ring = v
        self.update()

    ring = Property(float, getRing, setRing)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        if self.muted:
            accent = QColor(MUTED)
        elif self.listening or self.speaking:
            accent = QColor(GOLD)
        else:
            accent = QColor(TEAL)

        if self.listening and not self.muted:
            p.setPen(Qt.NoPen)
            p.setOpacity(max(0.0, 0.5 - 0.5 * self._ring))
            p.setBrush(QBrush(accent))
            r = 15 + 12 * self._ring
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        p.setOpacity(1.0)
        p.setBrush(QBrush(accent))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 14, cy - 14, 28, 28)

        p.setBrush(QBrush(QColor(BG)))
        p.drawRoundedRect(cx - 3.5, cy - 8, 7, 11, 3.5, 3.5)
        pen = QPen(QColor(BG))
        pen.setWidthF(1.6)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(cx - 7, cy - 4, 14, 14, 0, -180 * 16)
        p.drawLine(cx, cy + 7, cx, cy + 10)
        p.end()


class ChatBubble(QFrame):
    def __init__(self, text: str, role: str = "orion"):
        super().__init__()
        is_user = role == "user"
        self.setStyleSheet(f"""
            QFrame {{
                background: {TEAL if is_user else PANEL};
                border-radius: 12px;
                border: 1px solid {BORDER if not is_user else 'transparent'};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {BG if is_user else TEXT}; font-size: 13px; border: none; font-family: {FONT_FAMILY};")
        layout.addWidget(label)
        self.setMaximumWidth(360)


class TranscriptArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setAlignment(Qt.AlignTop)
        self.vbox.setSpacing(10)
        self.setWidget(self.container)

    def add_message(self, text: str, role: str = "orion"):
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignRight if role == "user" else Qt.AlignLeft)
        bubble = ChatBubble(text, role)
        row.addWidget(bubble)
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setLayout(row)
        self.vbox.addWidget(wrapper)


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(56)
        self.setStyleSheet(f"background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignHCenter)

        logo = QLabel("\u2726")
        logo.setStyleSheet(f"color: {TEAL}; font-size: 18px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        layout.addSpacing(10)

        for label in ["Home", "History", "Skills", "Schedule"]:
            btn = QPushButton(label[0])
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: {MUTED}; background: transparent; border: none;
                    border-radius: 8px; font-size: 12px; font-family: {FONT_FAMILY};
                }}
                QPushButton:hover {{ background: {PANEL}; color: {TEXT}; }}
            """)
            layout.addWidget(btn)

        layout.addStretch()
        settings = QPushButton("S")
        settings.setFixedSize(32, 32)
        settings.setCursor(Qt.PointingHandCursor)
        settings.setStyleSheet(f"""
            QPushButton {{ color: {MUTED}; background: transparent; border: none; border-radius: 8px; font-family: {FONT_FAMILY}; }}
            QPushButton:hover {{ background: {PANEL}; color: {TEXT}; }}
        """)
        layout.addWidget(settings)


class QuickActionCard(QFrame):
    def __init__(self, label_text, label_bg, label_text_color, description):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 16)
        layout.setSpacing(10)

        pill = QLabel(label_text)
        pill.setFixedHeight(24)
        pill.setStyleSheet(f"""
            background: {label_bg}; color: {label_text_color};
            border-radius: 12px; padding: 0 10px; font-size: 12px;
            font-weight: 600; font-family: {FONT_FAMILY};
        """)
        pill.setAlignment(Qt.AlignCenter)
        pill_row = QHBoxLayout()
        pill_row.addWidget(pill)
        pill_row.addStretch()

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-family: {FONT_FAMILY};")

        layout.addLayout(pill_row)
        layout.addWidget(desc)
        self.setFixedWidth(210)


class InputBar(QWidget):
    message_sent = Signal(str)

    def __init__(self, mic_button: MicButton):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        top_row = QHBoxLayout()
        spark = QLabel("\u2726")
        spark.setStyleSheet(f"color: {TEAL}; font-size: 14px;")
        self.field = QLineEdit()
        self.field.setPlaceholderText("Ask me anything...")
        self.field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; color: {TEXT}; border: none;
                font-size: 14px; font-family: {FONT_FAMILY};
            }}
        """)
        self.field.returnPressed.connect(self._send)
        top_row.addWidget(spark)
        top_row.addSpacing(6)
        top_row.addWidget(self.field, 1)

        bottom_row = QHBoxLayout()
        attach_btn = QPushButton("\U0001F4CE  Attach file")
        attach_btn.setCursor(Qt.PointingHandCursor)
        attach_btn.setFixedHeight(30)
        attach_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PANEL_2}; color: {MUTED}; border: 1px solid {BORDER};
                border-radius: 15px; padding: 0 12px; font-size: 12px; font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ color: {TEXT}; }}
        """)

        send_btn = QPushButton("\u2191")
        send_btn.setFixedSize(32, 32)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TEAL}; color: {BG}; border: none; border-radius: 16px;
                font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {TEAL_DEEP}; }}
        """)
        send_btn.clicked.connect(self._send)

        bottom_row.addWidget(attach_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(mic_button)
        bottom_row.addSpacing(6)
        bottom_row.addWidget(send_btn)

        card_layout.addLayout(top_row)
        card_layout.addLayout(bottom_row)
        outer.addWidget(card)

    def _send(self):
        text = self.field.text().strip()
        if not text:
            return
        self.message_sent.emit(text)
        self.field.clear()


class MainWindow(QMainWindow):
    USER_NAME = "Gaurang"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orion")
        self.resize(900, 680)
        self.setStyleSheet(f"background: {BG};")

        central = DotGrid()
        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(0)

        root.addWidget(Sidebar())

        main_col = QWidget()
        main_col.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(main_col)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.addStretch()
        user_chip = QFrame()
        user_chip.setStyleSheet(f"background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px;")
        chip_layout = QHBoxLayout(user_chip)
        chip_layout.setContentsMargins(6, 4, 10, 4)
        chip_layout.setSpacing(8)
        avatar = QLabel(self.USER_NAME[0])
        avatar.setFixedSize(22, 22)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"background: {TEAL_DEEP}; color: {BG}; border-radius: 11px; font-size: 11px; font-weight: 700;")
        name_label = QLabel(self.USER_NAME)
        name_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-family: {FONT_FAMILY};")
        chip_layout.addWidget(avatar)
        chip_layout.addWidget(name_label)
        top_row.addWidget(user_chip)

        self.orb = GlowOrb()

        greeting = QLabel(f"Hey! {self.USER_NAME}")
        greeting.setAlignment(Qt.AlignCenter)
        greeting.setFont(QFont("Segoe UI", 26, QFont.DemiBold))
        greeting.setStyleSheet(f"color: {TEXT};")

        self.status = QLabel("What can I help with?")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color: {MUTED}; font-size: 14px; margin-top: 4px; margin-bottom: 20px; font-family: {FONT_FAMILY};")

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        cards_row.addStretch()
        cards_row.addWidget(QuickActionCard("Play music", CARD_BLUE_BG, CARD_BLUE_TEXT, "Say a song name and I'll play it on YouTube"))
        cards_row.addWidget(QuickActionCard("Control PC", CARD_PINK_BG, CARD_PINK_TEXT, "Lock, restart, screenshot, or adjust volume"))
        cards_row.addWidget(QuickActionCard("Open a site", CARD_GREEN_BG, CARD_GREEN_TEXT, "Gmail, GitHub, YouTube, and more"))
        cards_row.addStretch()

        self.mic = MicButton()
        self.mic.mute_toggled.connect(self._on_mute_toggled)

        self.transcript = TranscriptArea()
        self.transcript.add_message("Say \u201cHey Orion\u201d or type below to get started.", "orion")

        self.input_bar = InputBar(self.mic)
        self.input_bar.message_sent.connect(self._on_user_message)

        main_layout.addLayout(top_row)
        main_layout.addSpacing(8)
        main_layout.addWidget(self.orb, 0, Qt.AlignCenter)
        main_layout.addWidget(greeting)
        main_layout.addWidget(self.status)
        main_layout.addLayout(cards_row)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.transcript, 1)
        main_layout.addSpacing(12)
        main_layout.addWidget(self.input_bar)

        root.addWidget(main_col, 1)
        self.setCentralWidget(central)

        self._start_orion_thread()

    # ------------------------------------------------------------
    # Orion background thread lifecycle
    # ------------------------------------------------------------

    def _start_orion_thread(self):
        self.thread = QThread(self)
        self.bridge = OrionBridge()
        self.bridge.moveToThread(self.thread)

        self.thread.started.connect(self.bridge.run)
        self.bridge.status_changed.connect(self._on_status_changed)
        self.bridge.message_received.connect(self._on_orion_message)

        self.thread.start()

    def closeEvent(self, event):
        self.bridge.stop()
        self.thread.quit()
        self.thread.wait(3000)
        super().closeEvent(event)

    # ------------------------------------------------------------
    # UI reactions to Orion state
    # ------------------------------------------------------------

    def _on_status_changed(self, status: str):
        STATUS_TEXT = {
            "idle": "What can I help with?",
            "active": "Woke up \u2014 go ahead",
            "listening": "Listening\u2026",
            "speaking": "Speaking\u2026",
        }
        self.orb.set_listening(status in ("active", "listening"))
        self.mic.set_status(status)
        self.status.setText(STATUS_TEXT.get(status, status))

    def _on_orion_message(self, text: str, role: str):
        self.transcript.add_message(text, role)

    def _on_mute_toggled(self, muted: bool):
        # Wire this to your mic input stream (e.g. pause recognizer.listen)
        # if you want a real hardware mute rather than just a UI state.
        self.status.setText("Muted" if muted else "What can I help with?")

    def _on_user_message(self, text: str):
        # Typed input bypasses the mic - route it through the same
        # command handler Orion's voice loop uses.
        self.transcript.add_message(text, "user")
        threading.Thread(target=orion_core.handle_command, args=(text,), daemon=True).start()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()