from enum import Enum
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
    QScrollArea, QLabel
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen

from .theme import isDarkTheme, themeColor, qconfig
from .fluent_icon import FluentIcon


class NavigationItemPosition(Enum):
    TOP = 0
    BOTTOM = 1


class NavigationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._init_ui()
        qconfig.themeChanged.connect(self._update_style)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.top_list = QListWidget()
        self.top_list.setFrameShape(QFrame.NoFrame)
        self.top_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.top_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.top_list.setFocusPolicy(Qt.NoFocus)

        self.bottom_list = QListWidget()
        self.bottom_list.setFrameShape(QFrame.NoFrame)
        self.bottom_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bottom_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bottom_list.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(self.top_list, 1)
        layout.addWidget(self.bottom_list, 0)

        self._update_style()

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            hover_color = "#333333"
            selected_color = "#3A3A3A"
            text_color = "#FFFFFF"
            selected_text_color = "#4CC2FF"
        else:
            bg_color = "#F7F7F7"
            hover_color = "#E8E8E8"
            selected_color = "#E5F3FF"
            text_color = "#201F1E"
            selected_text_color = "#0078D4"

        style = f"""
        QListWidget {{
            background-color: {bg_color};
            border: none;
            padding: 4px;
        }}
        QListWidget::item {{
            border-radius: 4px;
            padding: 8px 12px;
            margin: 2px 4px;
            min-height: 24px;
            color: {text_color};
        }}
        QListWidget::item:hover {{
            background-color: {hover_color};
        }}
        QListWidget::item:selected {{
            background-color: {selected_color};
            color: {selected_text_color};
        }}
        """
        self.top_list.setStyleSheet(style)
        self.bottom_list.setStyleSheet(style)


class FluentWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._navigation = None
        self._stacked_widget = None
        self._interfaces = {}
        self._current_index = -1
        self._init_ui()
        qconfig.themeChanged.connect(self._update_style)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._navigation = NavigationWidget(self)
        layout.addWidget(self._navigation, 0)

        self._stacked_widget = QStackedWidget()
        layout.addWidget(self._stacked_widget, 1)

        self._navigation.top_list.itemClicked.connect(self._on_top_item_clicked)
        self._navigation.bottom_list.itemClicked.connect(self._on_bottom_item_clicked)

        self._update_style()

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#202020"
        else:
            bg_color = "#FFFFFF"

        self._stacked_widget.setStyleSheet(f"""
        QStackedWidget {{
            background-color: {bg_color};
        }}
        """)

    def addSubInterface(self, interface, icon, text, position=NavigationItemPosition.TOP):
        if isinstance(icon, FluentIcon):
            icon = icon.icon()
        
        index = self._stacked_widget.addWidget(interface)
        self._interfaces[index] = interface

        item = QListWidgetItem(icon, text)
        item.setData(Qt.UserRole, index)
        item.setSizeHint(QSize(0, 40))

        if position == NavigationItemPosition.TOP:
            self._navigation.top_list.addItem(item)
        else:
            self._navigation.bottom_list.addItem(item)

        if self._current_index == -1:
            self.switchTo(interface)

    def _on_top_item_clicked(self, item):
        index = item.data(Qt.UserRole)
        self._stacked_widget.setCurrentIndex(index)
        self._current_index = index
        self._navigation.bottom_list.clearSelection()

    def _on_bottom_item_clicked(self, item):
        index = item.data(Qt.UserRole)
        self._stacked_widget.setCurrentIndex(index)
        self._current_index = index
        self._navigation.top_list.clearSelection()

    def switchTo(self, interface):
        for index, widget in self._interfaces.items():
            if widget == interface:
                self._stacked_widget.setCurrentIndex(index)
                self._current_index = index
                
                top_count = self._navigation.top_list.count()
                for i in range(top_count):
                    item = self._navigation.top_list.item(i)
                    if item.data(Qt.UserRole) == index:
                        self._navigation.top_list.setCurrentItem(item)
                        self._navigation.bottom_list.clearSelection()
                        return
                
                bottom_count = self._navigation.bottom_list.count()
                for i in range(bottom_count):
                    item = self._navigation.bottom_list.item(i)
                    if item.data(Qt.UserRole) == index:
                        self._navigation.bottom_list.setCurrentItem(item)
                        self._navigation.top_list.clearSelection()
                        return
                break

    def navigationInterface(self):
        return self._navigation

    def addSeparator(self):
        pass
