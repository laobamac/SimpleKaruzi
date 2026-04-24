from enum import Enum as PyEnum
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QProgressBar,
    QFrame, QScrollArea, QVBoxLayout, QHBoxLayout, QDialog,
    QGraphicsOpacityEffect, QSizePolicy, QComboBox, QSpinBox,
    QCheckBox, QTextEdit
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QObject
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QIcon, QPixmap

from .theme import isDarkTheme, themeColor, qconfig
from .fluent_icon import FluentIcon


class IndicatorPosition(PyEnum):
    LEFT = 0
    RIGHT = 1


class PrimaryPushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        text = ""
        parent = None
        icon = None
        
        if len(args) >= 1:
            if isinstance(args[0], FluentIcon):
                icon = args[0]
                if len(args) >= 2:
                    text = args[1]
            elif isinstance(args[0], str):
                text = args[0]
        
        if len(args) >= 2:
            if isinstance(args[1], QWidget):
                parent = args[1]
        
        parent = kwargs.get('parent', parent)
        
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self._icon = icon
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        primary_color = themeColor().name()
        
        if is_dark:
            bg_color = primary_color
            hover_color = "#66D1FF"
            pressed_color = "#33A8E0"
            text_color = "#000000"
        else:
            bg_color = primary_color
            hover_color = "#106EBE"
            pressed_color = "#005A9E"
            text_color = "#FFFFFF"
        
        self.setStyleSheet(f"""
        PrimaryPushButton {{
            background-color: {bg_color};
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            color: {text_color};
            font-size: 14px;
            font-weight: bold;
        }}
        PrimaryPushButton:hover {{
            background-color: {hover_color};
        }}
        PrimaryPushButton:pressed {{
            background-color: {pressed_color};
        }}
        PrimaryPushButton:disabled {{
            background-color: #9E9E9E;
            color: #FFFFFF;
        }}
        """)
        
        if self._icon:
            self.setIcon(self._icon.icon())
            self.setIconSize(QSize(20, 20))


class PushSettingCard(QWidget):
    def __init__(self, *args, **kwargs):
        text = ""
        icon = None
        title = ""
        content = ""
        parent = None
        
        arg_idx = 0
        if arg_idx < len(args) and isinstance(args[arg_idx], str):
            text = args[arg_idx]
            arg_idx += 1
        
        if arg_idx < len(args) and isinstance(args[arg_idx], FluentIcon):
            icon = args[arg_idx]
            arg_idx += 1
        
        if arg_idx < len(args) and isinstance(args[arg_idx], str):
            title = args[arg_idx]
            arg_idx += 1
        
        if arg_idx < len(args) and isinstance(args[arg_idx], str):
            content = args[arg_idx]
            arg_idx += 1
        
        if arg_idx < len(args) and isinstance(args[arg_idx], QWidget):
            parent = args[arg_idx]
        
        parent = kwargs.get('parent', parent)
        
        super().__init__(parent)
        self._title = title
        self._content = content
        self._button_text = text
        self._icon = icon
        
        self.clicked = pyqtSignal()
        
        self._init_ui()
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _init_ui(self):
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(24, 16, 24, 16)
        self.hBoxLayout.setSpacing(16)
        
        if self._icon:
            icon_label = QLabel()
            icon_label.setFixedSize(28, 28)
            icon_label.setPixmap(self._icon.icon().pixmap(28, 28))
            self.hBoxLayout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self._title_label = StrongBodyLabel(self._title)
        text_layout.addWidget(self._title_label)
        
        if self._content:
            self._content_label = BodyLabel(self._content)
            text_layout.addWidget(self._content_label)
        else:
            self._content_label = BodyLabel("")
            text_layout.addWidget(self._content_label)
        
        self.hBoxLayout.addLayout(text_layout, 1)
        
        self._button = PushButton(self._button_text)
        self._button.clicked.connect(self._on_button_clicked)
        self.hBoxLayout.addWidget(self._button)
    
    def _on_button_clicked(self):
        self.clicked.emit()
    
    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            border_color = "#404040"
        else:
            bg_color = "#FAFAFA"
            border_color = "#E0E0E0"
        
        self.setStyleSheet(f"""
        PushSettingCard {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
        """)
    
    def setContent(self, content):
        if hasattr(self, '_content_label'):
            self._content_label.setText(content)
    
    def setIcon(self, icon):
        pass


class SettingCard(QWidget):
    def __init__(self, icon=None, title="", content="", parent=None):
        super().__init__(parent)
        self._title = title
        self._content = content
        self._icon = icon
        
        self._init_ui()
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _init_ui(self):
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(24, 16, 24, 16)
        self.hBoxLayout.setSpacing(16)
        
        if self._icon:
            icon_label = QLabel()
            icon_label.setFixedSize(28, 28)
            icon_label.setPixmap(self._icon.icon().pixmap(28, 28))
            self.hBoxLayout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self._title_label = StrongBodyLabel(self._title)
        text_layout.addWidget(self._title_label)
        
        if self._content:
            self._content_label = BodyLabel(self._content)
            text_layout.addWidget(self._content_label)
        
        self.hBoxLayout.addLayout(text_layout, 1)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            border_color = "#404040"
        else:
            bg_color = "#FAFAFA"
            border_color = "#E0E0E0"
        
        self.setStyleSheet(f"""
        SettingCard {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
        """)
    
    def setTitle(self, title):
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)
    
    def setContent(self, content):
        if hasattr(self, '_content_label'):
            self._content_label.setText(content)
        elif hasattr(self, '_title_label'):
            pass
    
    def setIcon(self, icon):
        pass
    
    def setIconSize(self, width, height):
        pass


class SwitchButton(QWidget):
    checkedChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(44, 22)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._update_style()
            self.checkedChanged.emit(checked)
    
    def toggle(self):
        self.setChecked(not self._checked)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        primary = themeColor().name()
        
        if self._checked:
            bg_color = primary
            knob_color = "#FFFFFF"
        else:
            if is_dark:
                bg_color = "#555555"
                knob_color = "#888888"
            else:
                bg_color = "#C1C1C1"
                knob_color = "#FFFFFF"
        
        knob_x = 24 if self._checked else 4
        
        self.setStyleSheet(f"""
        SwitchButton {{
            background-color: {bg_color};
            border-radius: 11px;
        }}
        """)
        
        self._knob_x = knob_x
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        is_dark = isDarkTheme()
        primary = themeColor()
        
        if self._checked:
            bg_color = primary
            knob_color = QColor(255, 255, 255)
        else:
            if is_dark:
                bg_color = QColor(85, 85, 85)
                knob_color = QColor(136, 136, 136)
            else:
                bg_color = QColor(193, 193, 193)
                knob_color = QColor(255, 255, 255)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, 44, 22, 11, 11)
        
        knob_x = 24 if self._checked else 2
        painter.setBrush(knob_color)
        painter.drawEllipse(knob_x, 2, 18, 18)
        
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()


class SwitchSettingCard(SettingCard):
    def __init__(self, icon=None, title="", content="", configItem=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.switchButton = SwitchButton(self)
        
        self.hBoxLayout.addWidget(self.switchButton)


class SettingCardGroup(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self._title = title
        self._cards = []
        self._init_ui()
    
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)
        
        if self._title:
            title_label = SubtitleLabel(self._title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.main_layout.addWidget(title_label)
            self.main_layout.addSpacing(8)
    
    def addSettingCard(self, card):
        self._cards.append(card)
        self.main_layout.addWidget(card)


class SpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(32)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#323232"
            border_color = "#404040"
            focus_color = "#4CC2FF"
            text_color = "#FFFFFF"
        else:
            bg_color = "#FFFFFF"
            border_color = "#D1D1D1"
            focus_color = "#0078D4"
            text_color = "#000000"
        
        self.setStyleSheet(f"""
        SpinBox {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 4px 8px;
            color: {text_color};
            font-size: 14px;
        }}
        SpinBox:focus {{
            border-color: {focus_color};
        }}
        SpinBox::up-button, SpinBox::down-button {{
            width: 24px;
            border: none;
            background-color: transparent;
        }}
        """)


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(32)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#323232"
            border_color = "#404040"
            focus_color = "#4CC2FF"
            text_color = "#FFFFFF"
        else:
            bg_color = "#FFFFFF"
            border_color = "#D1D1D1"
            focus_color = "#0078D4"
            text_color = "#000000"
        
        self.setStyleSheet(f"""
        ComboBox {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 4px 8px;
            color: {text_color};
            font-size: 14px;
        }}
        ComboBox:focus {{
            border-color: {focus_color};
        }}
        ComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        ComboBox QAbstractItemView {{
            background-color: {bg_color};
            color: {text_color};
            selection-background-color: {focus_color};
            selection-color: #FFFFFF;
        }}
        """)


class OptionsConfigItem(QObject):
    valueChanged = pyqtSignal(object)
    
    def __init__(self, group, name, default, validator=None):
        super().__init__()
        self._group = group
        self._name = name
        self._default = default
        self._value = default
        self._validator = validator
    
    def value(self):
        return self._value
    
    def setValue(self, value):
        if self._value != value:
            self._value = value
            self.valueChanged.emit(value)


class OptionsValidator:
    def __init__(self, options):
        self._options = options
    
    def validate(self, value):
        return value in self._options


class ComboBoxSettingCard(SettingCard):
    def __init__(self, configItem, icon=None, title="", content="", options=None, parent=None):
        super().__init__(icon, title, content, parent)
        self._configItem = configItem
        self._options = options or []
        
        self.comboBox = ComboBox(self)
        if self._options:
            self.comboBox.addItems(self._options)
        
        if configItem:
            current_val = configItem.value()
            if current_val in self._options:
                self.comboBox.setCurrentText(current_val)
        
        self.comboBox.currentTextChanged.connect(self._on_text_changed)
        self.hBoxLayout.addWidget(self.comboBox)
    
    def _on_text_changed(self, text):
        if self._configItem:
            self._configItem.setValue(text)
    
    def setValue(self, value):
        if isinstance(value, str):
            index = self.comboBox.findText(value)
            if index >= 0:
                self.comboBox.setCurrentIndex(index)


class HyperlinkCard(SettingCard):
    def __init__(self, url, text, icon=None, title="", content="", parent=None):
        super().__init__(icon, title, content, parent)
        self._url = url
        
        link_btn = PushButton(text)
        link_btn.clicked.connect(self._open_url)
        self.hBoxLayout.addWidget(link_btn)
    
    def _open_url(self):
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(self._url))


class PrimaryPushSettingCard(SettingCard):
    def __init__(self, text, icon=None, title="", content="", parent=None):
        super().__init__(icon, title, content, parent)
        self.clicked = pyqtSignal()
        
        self.button = PrimaryPushButton(text)
        self.button.clicked.connect(self._on_clicked)
        self.hBoxLayout.addWidget(self.button)
    
    def _on_clicked(self):
        self.clicked.emit()


class TextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)
    
    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            border_color = "#404040"
            text_color = "#E0E0E0"
        else:
            bg_color = "#FAFAFA"
            border_color = "#E0E0E0"
            text_color = "#424242"
        
        self.setStyleSheet(f"""
        TextEdit {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 8px;
            color: {text_color};
            font-size: 13px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
        }}
        """)


class IconWidget(QLabel):
    def __init__(self, icon=None, parent=None):
        super().__init__(parent)
        self._icon = icon
        if icon:
            self.setPixmap(icon.icon().pixmap(24, 24))
    
    def setIcon(self, icon):
        self._icon = icon
        if icon:
            self.setPixmap(icon.icon().pixmap(24, 24))


class ExpandGroupSettingCard(SettingCard):
    def __init__(self, icon=None, title="", content="", parent=None):
        super().__init__(icon, title, content, parent)
        self._is_expanded = False
        self._group_widgets = []
        
        self._expand_btn = QPushButton("▼")
        self._expand_btn.setFixedSize(24, 24)
        self._expand_btn.clicked.connect(self.toggle)
        self.hBoxLayout.addWidget(self._expand_btn)
    
    def toggle(self):
        self._is_expanded = not self._is_expanded
        self._expand_btn.setText("▲" if self._is_expanded else "▼")
        for widget in self._group_widgets:
            widget.setVisible(self._is_expanded)
    
    def addGroup(self, icon, title, content, widget):
        group = CardGroupWidget(icon, title, content, widget, self)
        self._group_widgets.append(group)
        group.setVisible(self._is_expanded)
        return group


class SubtitleLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            text_color = "#FFFFFF"
        else:
            text_color = "#000000"
        
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f"color: {text_color}; background-color: transparent;")


class BodyLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            text_color = "#E0E0E0"
        else:
            text_color = "#424242"
        
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        self.setStyleSheet(f"color: {text_color}; background-color: transparent;")


class StrongBodyLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            text_color = "#FFFFFF"
        else:
            text_color = "#000000"
        
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f"color: {text_color}; background-color: transparent;")


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            border_color = "#404040"
        else:
            bg_color = "#FAFAFA"
            border_color = "#E0E0E0"
        
        self.setStyleSheet(f"""
        CardWidget {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
        """)

    def setBorderRadius(self, radius):
        pass


class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#202020"
            scroll_bg = "#2B2B2B"
            scroll_handle = "#555555"
        else:
            bg_color = "#FFFFFF"
            scroll_bg = "#F3F3F3"
            scroll_handle = "#C1C1C1"
        
        self.setStyleSheet(f"""
        ScrollArea {{
            background-color: {bg_color};
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {scroll_bg};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {scroll_handle};
            border-radius: 6px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {scroll_bg};
            height: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {scroll_handle};
            border-radius: 6px;
            min-width: 30px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        """)

    def enableTransparentBackground(self):
        self.setStyleSheet(self.styleSheet() + """
        ScrollArea {
            background-color: transparent;
        }
        """)


class PushButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#323232"
            hover_color = "#404040"
            pressed_color = "#505050"
            border_color = "#404040"
            text_color = "#FFFFFF"
        else:
            bg_color = "#F3F3F3"
            hover_color = "#E8E8E8"
            pressed_color = "#D1D1D1"
            border_color = "#D1D1D1"
            text_color = "#000000"
        
        self.setStyleSheet(f"""
        PushButton {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 6px 16px;
            color: {text_color};
            font-size: 14px;
        }}
        PushButton:hover {{
            background-color: {hover_color};
        }}
        PushButton:pressed {{
            background-color: {pressed_color};
        }}
        """)


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(32)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#323232"
            border_color = "#404040"
            focus_color = "#4CC2FF"
            text_color = "#FFFFFF"
            placeholder_color = "#888888"
        else:
            bg_color = "#FFFFFF"
            border_color = "#D1D1D1"
            focus_color = "#0078D4"
            text_color = "#000000"
            placeholder_color = "#A19F9D"
        
        self.setStyleSheet(f"""
        LineEdit {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 6px 12px;
            color: {text_color};
            font-size: 14px;
        }}
        LineEdit:focus {{
            border-color: {focus_color};
        }}
        LineEdit::placeholder {{
            color: {placeholder_color};
        }}
        """)


class ProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#323232"
            chunk_color = "#4CC2FF"
        else:
            bg_color = "#E0E0E0"
            chunk_color = "#0078D4"
        
        self.setStyleSheet(f"""
        ProgressBar {{
            border: none;
            background-color: {bg_color};
            border-radius: 4px;
            text-align: center;
            font-size: 13px;
        }}
        ProgressBar::chunk {{
            background-color: {chunk_color};
            border-radius: 4px;
        }}
        """)


class MessageBoxBase(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        
        self._init_ui()
        self._update_style()
        qconfig.themeChanged.connect(self._update_style)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.widget = QFrame()
        layout.addWidget(self.widget)
        
        widget_layout = QVBoxLayout(self.widget)
        widget_layout.setContentsMargins(24, 24, 24, 24)
        widget_layout.setSpacing(16)
        
        self.viewLayout = QVBoxLayout()
        self.viewLayout.setSpacing(12)
        widget_layout.addLayout(self.viewLayout)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.yesButton = PushButton("确定")
        self.yesButton.setMinimumWidth(100)
        button_layout.addWidget(self.yesButton)
        
        self.cancelButton = PushButton("取消")
        self.cancelButton.setMinimumWidth(100)
        button_layout.addWidget(self.cancelButton)
        
        widget_layout.addLayout(button_layout)
        
        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def _update_style(self):
        is_dark = isDarkTheme()
        if is_dark:
            bg_color = "#2B2B2B"
            border_color = "#404040"
        else:
            bg_color = "#FFFFFF"
            border_color = "#E0E0E0"
        
        self.widget.setStyleSheet(f"""
        QFrame {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
        """)

    def setMinimumWidth(self, width):
        self.widget.setMinimumWidth(width)
        super().setMinimumWidth(width + 48)


class GroupHeaderCardWidget(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups = []
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

    def addGroup(self, icon, title, content, widget):
        group = CardGroupWidget(icon, title, content, widget, self)
        self._groups.append(group)
        self.main_layout.addWidget(group)
        return group


class CardGroupWidget(QWidget):
    def __init__(self, icon, title, content, widget, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(24, 10, 24, 10)
        self.hBoxLayout.setSpacing(12)
        
        if isinstance(icon, FluentIcon):
            icon = icon.icon()
        
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setPixmap(icon.pixmap(24, 24))
        self.hBoxLayout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = StrongBodyLabel(title)
        text_layout.addWidget(title_label)
        
        if content:
            content_label = BodyLabel(content)
            text_layout.addWidget(content_label)
        
        self.hBoxLayout.addLayout(text_layout, 1)
        
        if widget:
            self.hBoxLayout.addWidget(widget)
