from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication


class Theme(Enum):
    LIGHT = 0
    DARK = 1
    AUTO = 2


class QConfig(QObject):
    themeChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._theme = Theme.AUTO
        self._theme_color = QColor(0, 120, 212)
    
    def theme(self):
        return self._theme
    
    def setTheme(self, theme):
        self._theme = theme
        self.themeChanged.emit()
    
    def themeColor(self):
        return self._theme_color


qconfig = QConfig()


def setTheme(theme):
    qconfig.setTheme(theme)
    _apply_theme_to_application(theme)


def _apply_theme_to_application(theme):
    app = QApplication.instance()
    if not app:
        return
    
    if theme == Theme.DARK:
        app.setStyleSheet(_get_dark_stylesheet())
    elif theme == Theme.LIGHT:
        app.setStyleSheet(_get_light_stylesheet())
    else:
        pass


def _get_light_stylesheet():
    return """
    QWidget {
        background-color: #FFFFFF;
        color: #000000;
    }
    QPushButton {
        background-color: #F3F3F3;
        border: 1px solid #D1D1D1;
        border-radius: 4px;
        padding: 6px 16px;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #E8E8E8;
    }
    QPushButton:pressed {
        background-color: #D1D1D1;
    }
    QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #D1D1D1;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 32px;
    }
    QLineEdit:focus {
        border-color: #0078D4;
    }
    QScrollBar:vertical {
        background-color: #F3F3F3;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background-color: #C1C1C1;
        border-radius: 6px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #A1A1A1;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background-color: #F3F3F3;
        height: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background-color: #C1C1C1;
        border-radius: 6px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #A1A1A1;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QProgressBar {
        border: none;
        background-color: #E0E0E0;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #0078D4;
        border-radius: 4px;
    }
    QComboBox {
        background-color: #FFFFFF;
        border: 1px solid #D1D1D1;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 32px;
    }
    QComboBox:focus {
        border-color: #0078D4;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QCheckBox {
        spacing: 8px;
    }
    QRadioButton {
        spacing: 8px;
    }
    QTabWidget::pane {
        border: 1px solid #D1D1D1;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #F3F3F3;
        border: 1px solid #D1D1D1;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 8px 16px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        border-bottom: 1px solid #FFFFFF;
    }
    QTabBar::tab:hover {
        background-color: #E8E8E8;
    }
    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #D1D1D1;
        border-radius: 4px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    """


def _get_dark_stylesheet():
    return """
    QWidget {
        background-color: #202020;
        color: #FFFFFF;
    }
    QPushButton {
        background-color: #323232;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 6px 16px;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #404040;
    }
    QPushButton:pressed {
        background-color: #505050;
    }
    QLineEdit {
        background-color: #323232;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 32px;
        color: #FFFFFF;
    }
    QLineEdit:focus {
        border-color: #4CC2FF;
    }
    QScrollBar:vertical {
        background-color: #2B2B2B;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background-color: #555555;
        border-radius: 6px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #666666;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background-color: #2B2B2B;
        height: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background-color: #555555;
        border-radius: 6px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #666666;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QProgressBar {
        border: none;
        background-color: #323232;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #4CC2FF;
        border-radius: 4px;
    }
    QComboBox {
        background-color: #323232;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 32px;
        color: #FFFFFF;
    }
    QComboBox:focus {
        border-color: #4CC2FF;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QCheckBox {
        spacing: 8px;
    }
    QRadioButton {
        spacing: 8px;
    }
    QTabWidget::pane {
        border: 1px solid #404040;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #323232;
        border: 1px solid #404040;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 8px 16px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #202020;
        border-bottom: 1px solid #202020;
    }
    QTabBar::tab:hover {
        background-color: #404040;
    }
    QMenu {
        background-color: #323232;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #4CC2FF;
        color: #000000;
    }
    """


def isDarkTheme():
    theme = qconfig.theme()
    if theme == Theme.DARK:
        return True
    elif theme == Theme.LIGHT:
        return False
    else:
        app = QApplication.instance()
        if app:
            try:
                palette = app.palette()
                window_color = palette.color(palette.Window)
                return window_color.lightness() < 128
            except:
                pass
        return False


def themeColor():
    if isDarkTheme():
        return QColor(76, 194, 255)
    return QColor(0, 120, 212)
