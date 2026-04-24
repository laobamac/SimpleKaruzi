from enum import Enum
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtWidgets import QApplication


class FluentIcon(Enum):
    HOME = "home"
    SETTING = "setting"
    FOLDER = "folder"
    FOLDER_ADD = "folder_add"
    CHECKBOX = "checkbox"
    EDIT = "edit"
    DEVELOPER_TOOLS = "developer_tools"
    INFO = "info"
    CLOSE = "close"
    ACCEPT = "accept"
    COMPLETED = "completed"
    SYNC = "sync"
    MEGAPHONE = "megaphone"
    CARE_LEFT_SOLID = "care_left_solid"
    CANCEL = "cancel"
    GITHUB = "github"
    BOOK_SHELF = "book_shelf"
    UPDATE = "update"
    BRUSH = "brush"

    def icon(self, color=None):
        if color is None:
            from .theme import isDarkTheme
            if isDarkTheme():
                color = QColor(76, 194, 255)
            else:
                color = QColor(0, 120, 212)
        elif isinstance(color, str):
            color = QColor(color)
        return self._render_icon(color)

    def _render_icon(self, color):
        renderers = {
            FluentIcon.HOME: self._render_home,
            FluentIcon.SETTING: self._render_setting,
            FluentIcon.FOLDER: self._render_folder,
            FluentIcon.FOLDER_ADD: self._render_folder_add,
            FluentIcon.CHECKBOX: self._render_checkbox,
            FluentIcon.EDIT: self._render_edit,
            FluentIcon.DEVELOPER_TOOLS: self._render_developer_tools,
            FluentIcon.INFO: self._render_info,
            FluentIcon.CLOSE: self._render_close,
            FluentIcon.ACCEPT: self._render_accept,
            FluentIcon.COMPLETED: self._render_accept,
            FluentIcon.SYNC: self._render_sync,
            FluentIcon.MEGAPHONE: self._render_megaphone,
            FluentIcon.CARE_LEFT_SOLID: self._render_care_left_solid,
            FluentIcon.CANCEL: self._render_cancel,
            FluentIcon.GITHUB: self._render_github,
            FluentIcon.BOOK_SHELF: self._render_book_shelf,
            FluentIcon.UPDATE: self._render_update,
            FluentIcon.BRUSH: self._render_brush,
        }
        renderer = renderers.get(self, self._render_default)
        return renderer(color)

    def _render_default(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(4, 4, 24, 24))
        painter.end()
        return QIcon(pixmap)

    def _render_home(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)
        painter.drawRect(8, 16, 16, 12)
        painter.drawPolygon([
            QPoint(16, 4),
            QPoint(28, 16),
            QPoint(4, 16)
        ])
        painter.end()
        return QIcon(pixmap)

    def _render_setting(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(10, 10, 12, 12))
        import math
        for i in range(8):
            angle = i * 45
            rad = math.radians(angle)
            x1 = 16 + 8 * math.cos(rad)
            y1 = 16 + 8 * math.sin(rad)
            x2 = 16 + 14 * math.cos(rad)
            y2 = 16 + 14 * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        painter.end()
        return QIcon(pixmap)

    def _render_folder(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(4, 10, 24, 16)
        painter.drawRect(4, 6, 12, 6)
        painter.end()
        return QIcon(pixmap)

    def _render_folder_add(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(4, 10, 24, 16)
        painter.drawRect(4, 6, 12, 6)
        painter.drawLine(16, 18, 16, 22)
        painter.drawLine(14, 20, 18, 20)
        painter.end()
        return QIcon(pixmap)

    def _render_checkbox(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(6, 6, 20, 20))
        painter.drawLine(10, 16, 14, 20)
        painter.drawLine(14, 20, 22, 12)
        painter.end()
        return QIcon(pixmap)

    def _render_edit(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(8, 24, 20, 12)
        painter.drawLine(18, 10, 24, 16)
        painter.end()
        return QIcon(pixmap)

    def _render_developer_tools(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(6, 6, 20, 20)
        painter.drawLine(10, 12, 14, 16)
        painter.drawLine(14, 16, 10, 20)
        painter.drawLine(18, 12, 22, 20)
        painter.end()
        return QIcon(pixmap)

    def _render_info(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(6, 6, 20, 20))
        painter.drawLine(16, 12, 16, 20)
        painter.drawPoint(16, 10)
        painter.end()
        return QIcon(pixmap)

    def _render_close(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.drawLine(10, 10, 22, 22)
        painter.drawLine(22, 10, 10, 22)
        painter.end()
        return QIcon(pixmap)

    def _render_cancel(self, color):
        return self._render_close(color)

    def _render_accept(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(6, 6, 20, 20))
        painter.drawLine(10, 16, 14, 20)
        painter.drawLine(14, 20, 22, 12)
        painter.end()
        return QIcon(pixmap)

    def _render_sync(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(6, 6, 20, 20), 30 * 16, 270 * 16)
        painter.drawLine(24, 12, 28, 8)
        painter.drawLine(24, 12, 28, 16)
        painter.end()
        return QIcon(pixmap)

    def _render_update(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(6, 6, 20, 20), 45 * 16, 270 * 16)
        painter.drawLine(16, 12, 16, 8)
        painter.drawLine(12, 12, 16, 8)
        painter.drawLine(20, 12, 16, 8)
        painter.end()
        return QIcon(pixmap)

    def _render_megaphone(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(8, 12, 8, 8)
        painter.drawLine(16, 10, 24, 6)
        painter.drawLine(16, 22, 24, 26)
        painter.drawLine(24, 6, 24, 26)
        painter.end()
        return QIcon(pixmap)

    def _render_care_left_solid(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPolygon([
            QPoint(20, 8),
            QPoint(20, 24),
            QPoint(10, 16)
        ])
        painter.end()
        return QIcon(pixmap)

    def _render_github(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)
        
        painter.drawEllipse(QRectF(8, 8, 16, 16))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(14, 16, 4, 8)
        painter.drawRect(10, 18, 4, 4)
        painter.drawRect(18, 18, 4, 4)
        
        painter.end()
        return QIcon(pixmap)

    def _render_book_shelf(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        
        painter.drawRect(4, 6, 24, 20)
        
        painter.drawLine(8, 6, 8, 26)
        painter.drawLine(16, 6, 16, 26)
        painter.drawLine(24, 6, 24, 26)
        
        painter.drawLine(4, 12, 28, 12)
        painter.drawLine(4, 18, 28, 18)
        painter.drawLine(4, 24, 28, 24)
        
        painter.end()
        return QIcon(pixmap)

    def _render_brush(self, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        
        painter.drawEllipse(QRectF(10, 6, 12, 12))
        painter.setBrush(color)
        painter.drawEllipse(QRectF(10, 6, 12, 12))
        
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(13, 16, 6, 10)
        
        painter.end()
        return QIcon(pixmap)

    def colored(self, tint1, tint2=None):
        return self
