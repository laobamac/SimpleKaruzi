from enum import Enum
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QFrame, QGraphicsOpacityEffect, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QPainter, QPen


class InfoBarPosition(Enum):
    TOP = 0
    BOTTOM = 1
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5


class InfoBar(QWidget):
    closed = pyqtSignal()

    def __init__(self, info_type, title, content, duration=3000, parent=None):
        super().__init__(parent)
        self.info_type = info_type
        self.title = title
        self.content = content
        self.duration = duration
        
        self._init_ui()
        self._setup_animation()
        
        if duration > 0:
            QTimer.singleShot(duration, self.close_animation)

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        text_layout.addWidget(title_label)
        
        if self.content:
            content_label = QLabel(self.content)
            content_label.setStyleSheet("font-size: 13px;")
            text_layout.addWidget(content_label)
        
        layout.addLayout(text_layout, 1)
        
        self._apply_colors()

    def _apply_colors(self):
        colors = {
            "success": {"bg": "#F3FAF3", "border": "#107C10", "text": "#107C10"},
            "error": {"bg": "#FDE7E9", "border": "#E81123", "text": "#E81123"},
            "warning": {"bg": "#FFF4CE", "border": "#FF8C00", "text": "#F57C00"},
            "info": {"bg": "#F3F9FD", "border": "#0078D4", "text": "#0078D4"},
        }
        
        c = colors.get(self.info_type, colors["info"])
        self.setStyleSheet(f"""
        InfoBar {{
            background-color: {c["bg"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        QLabel {{
            color: {c["text"]};
            background-color: transparent;
        }}
        """)

    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.show_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.show_animation.setDuration(300)
        self.show_animation.setStartValue(0.0)
        self.show_animation.setEndValue(1.0)
        self.show_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.hide_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hide_animation.setDuration(300)
        self.hide_animation.setStartValue(1.0)
        self.hide_animation.setEndValue(0.0)
        self.hide_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.hide_animation.finished.connect(self._on_close_finished)

    def show_animation(self):
        self.show()
        self.show_animation.start()

    def close_animation(self):
        self.hide_animation.start()

    def _on_close_finished(self):
        self.hide()
        self.closed.emit()
        self.deleteLater()

    @staticmethod
    def _get_position_geometry(position, parent, width, height):
        if parent is None:
            parent = QApplication.activeWindow()
        
        if parent is None:
            screen = QApplication.primaryScreen()
            if screen:
                rect = screen.availableGeometry()
            else:
                rect = QApplication.desktop().availableGeometry()
        else:
            rect = parent.geometry()
        
        margin = 20
        
        if position == InfoBarPosition.TOP_RIGHT:
            x = rect.right() - width - margin
            y = rect.top() + margin
        elif position == InfoBarPosition.TOP_LEFT:
            x = rect.left() + margin
            y = rect.top() + margin
        elif position == InfoBarPosition.BOTTOM_RIGHT:
            x = rect.right() - width - margin
            y = rect.bottom() - height - margin
        elif position == InfoBarPosition.BOTTOM_LEFT:
            x = rect.left() + margin
            y = rect.bottom() - height - margin
        elif position == InfoBarPosition.TOP:
            x = rect.left() + (rect.width() - width) // 2
            y = rect.top() + margin
        elif position == InfoBarPosition.BOTTOM:
            x = rect.left() + (rect.width() - width) // 2
            y = rect.bottom() - height - margin
        else:
            x = rect.right() - width - margin
            y = rect.top() + margin
        
        return (x, y)

    @classmethod
    def success(cls, title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=None):
        bar = cls("success", title, content, duration, parent)
        bar._show_at_position(position)
        return bar

    @classmethod
    def error(cls, title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=5000, parent=None):
        bar = cls("error", title, content, duration, parent)
        bar._show_at_position(position)
        return bar

    @classmethod
    def warning(cls, title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=4000, parent=None):
        bar = cls("warning", title, content, duration, parent)
        bar._show_at_position(position)
        return bar

    @classmethod
    def info(cls, title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=None):
        bar = cls("info", title, content, duration, parent)
        bar._show_at_position(position)
        return bar

    def _show_at_position(self, position):
        width = max(300, self.sizeHint().width())
        height = max(60, self.sizeHint().height())
        self.setFixedSize(width, height)
        
        x, y = self._get_position_geometry(position, self.parent(), width, height)
        self.move(x, y)
        self.show_animation()
