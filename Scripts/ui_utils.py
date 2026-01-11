from typing import Optional, Tuple, TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from qfluentwidgets import FluentIcon, BodyLabel, CardWidget, StrongBodyLabel, isDarkTheme, themeColor, qconfig

from .styles import SPACING, COLORS, RADIUS

if TYPE_CHECKING:
    from qfluentwidgets import GroupHeaderCardWidget, CardGroupWidget

class FooterWidget(QWidget):
    """
    一个独立的页脚组件，显示版权和协议信息。
    自动监听主题切换并更新链接颜色。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        # 版权信息
        self.footer_label = BodyLabel(
            "Author: <a href='https://github.com/laobamac' style='text-decoration: none;'>laobamac</a> | "
            "Project: <a href='https://github.com/laobamac/SimpleKaruzi' style='text-decoration: none;'>SimpleKaruzi</a>"
        )
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setOpenExternalLinks(True)
        
        # 协议信息
        self.license_label = BodyLabel(
            "Licensed under <a href='https://github.com/laobamac/SimpleKaruzi/blob/main/LICENSE' style='text-decoration: none;'>AGPL-3.0 License</a>"
        )
        self.license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.license_label.setOpenExternalLinks(True)
        
        self.layout.addWidget(self.footer_label)
        self.layout.addWidget(self.license_label)
        
        # 初始化样式并监听主题变化
        self.update_style()
        qconfig.themeChanged.connect(self.update_style)

    def update_style(self):
        """根据主题自动更新页脚文字颜色"""
        is_dark = isDarkTheme()
        
        if is_dark:
            footer_text_color = "#888888"
            footer_link_color = "#4CC2FF"
        else:
            footer_text_color = "#707070"
            footer_link_color = "#0078D4"

        footer_qss = f"""
            QLabel {{
                font-size: 12px;
                color: {footer_text_color};
            }}
            QLabel a {{
                color: {footer_link_color};
                text-decoration: none;
            }}
            QLabel a:hover {{
                text-decoration: underline;
            }}
        """
        self.footer_label.setStyleSheet(footer_qss)
        self.license_label.setStyleSheet(footer_qss)

class ProgressStatusHelper:
    def __init__(self, status_icon_label, progress_label, progress_bar, progress_container):
        self.status_icon_label = status_icon_label
        self.progress_label = progress_label
        self.progress_bar = progress_bar
        self.progress_container = progress_container
        
        # 监听主题变化以更新进度条文字颜色
        qconfig.themeChanged.connect(self._on_theme_changed)
        # 保存当前状态以便刷新
        self._current_status = None
        self._current_message = ""
    
    def _on_theme_changed(self):
        if self._current_status:
            self.update_text_color(self._current_status)

    def update_text_color(self, status):
        is_dark = isDarkTheme()
        style_base = "font-size: 15px; font-weight: 600;"
        
        if status == "success":
            color = "#6CCB5F" if is_dark else COLORS["success"]
        elif status == "error":
            color = "#FF99A4" if is_dark else COLORS["error"]
        elif status == "warning":
            color = "#FCE100" if is_dark else COLORS["warning"]
        else:
            color = themeColor().name() if is_dark else COLORS["primary"]
            
        self.progress_label.setStyleSheet(f"color: {color}; {style_base}")

    def update(self, status, message, progress=None):
        self._current_status = status
        self._current_message = message
        
        icon_size = 28
        icon_map = {
            "loading": (FluentIcon.SYNC, COLORS["primary"]),
            "success": (FluentIcon.COMPLETED, COLORS["success"]),
            "error": (FluentIcon.CLOSE, COLORS["error"]),
            "warning": (FluentIcon.INFO, COLORS["warning"]),
        }
        
        if status in icon_map:
            icon, color = icon_map[status]
            pixmap = icon.icon(color=color).pixmap(icon_size, icon_size)
            self.status_icon_label.setPixmap(pixmap)
        
        self.progress_label.setText(message)
        self.update_text_color(status)
        
        if progress is not None:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setRange(0, 0)
        
        self.progress_container.setVisible(True)

class ThemeAwareCardWidget(CardWidget):
    """
    一个能自动感知主题变化并更新自身样式的卡片组件。
    解决切换主题或启动时颜色不正确的 bug。
    """
    def __init__(self, card_type, icon, title, body, custom_widget, ui_utils, parent=None):
        super().__init__(parent)
        self.card_type = card_type
        self.target_icon = icon
        self.title_text = title
        self.body_text = body
        self.custom_widget = custom_widget
        self.ui_utils = ui_utils
        
        # 初始化 UI 结构
        self._init_layout()
        
        self.update_style()
        
        qconfig.themeChanged.connect(self.update_style)

    def _init_layout(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        self.main_layout.setSpacing(SPACING["large"])
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(52, 52) # 40 + 12
        self.main_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(SPACING["small"])
        
        self.title_label = None
        if self.title_text:
            self.title_label = StrongBodyLabel(self.title_text)
            self.text_layout.addWidget(self.title_label)
        
        self.body_label = None
        if self.body_text:
            self.body_label = BodyLabel(self.body_text)
            self.body_label.setWordWrap(True)
            self.body_label.setOpenExternalLinks(True)
            self.text_layout.addWidget(self.body_label)
        
        if self.custom_widget:
            self.text_layout.addWidget(self.custom_widget)
        
        self.main_layout.addLayout(self.text_layout)

    def update_style(self):
        """根据当前主题刷新样式表和图标"""
        is_dark = isDarkTheme()
        
        if is_dark:
            card_styles = {
                "note":    {"bg": "rgba(0, 120, 212, 0.08)", "text": "#4CC2FF", "body": "#E0E0E0", "border": "rgba(0, 120, 212, 0.3)",  "icon": FluentIcon.INFO},
                "warning": {"bg": "rgba(245, 124, 0, 0.08)", "text": "#FFAA44", "body": "#E0E0E0", "border": "rgba(245, 124, 0, 0.3)",  "icon": FluentIcon.MEGAPHONE},
                "success": {"bg": "rgba(16, 124, 16, 0.08)", "text": "#6CCB5F", "body": "#E0E0E0", "border": "rgba(16, 124, 16, 0.3)",  "icon": FluentIcon.COMPLETED},
                "error":   {"bg": "rgba(232, 17, 35, 0.08)", "text": "#FF99A4", "body": "#E0E0E0", "border": "rgba(232, 17, 35, 0.3)",  "icon": FluentIcon.CLOSE},
                "info":    {"bg": "rgba(0, 120, 212, 0.08)", "text": "#4CC2FF", "body": "#E0E0E0", "border": "rgba(0, 120, 212, 0.3)",  "icon": FluentIcon.INFO}
            }
        else:
            card_styles = {
                "note":    {"bg": COLORS["note_bg"],    "text": COLORS["note_text"],    "body": "#424242", "border": "rgba(21, 101, 192, 0.2)",  "icon": FluentIcon.INFO},
                "warning": {"bg": COLORS["warning_bg"], "text": COLORS["warning_text"], "body": "#424242", "border": "rgba(245, 124, 0, 0.25)", "icon": FluentIcon.MEGAPHONE},
                "success": {"bg": COLORS["success_bg"], "text": COLORS["success"],      "body": "#424242", "border": "rgba(16, 124, 16, 0.2)",   "icon": FluentIcon.COMPLETED},
                "error":   {"bg": "#FFEBEE",            "text": COLORS["error"],        "body": "#424242", "border": "rgba(232, 17, 35, 0.25)",  "icon": FluentIcon.CLOSE},
                "info":    {"bg": COLORS["note_bg"],    "text": COLORS["info"],         "body": "#424242", "border": "rgba(0, 120, 212, 0.2)",   "icon": FluentIcon.INFO}
            }

        style = card_styles.get(self.card_type, card_styles["note"])
        icon_to_use = self.target_icon if self.target_icon else style["icon"]

        self.setStyleSheet(f"""
            ThemeAwareCardWidget {{
                background-color: {style["bg"]};
                border: 1px solid {style["border"]};
                border-radius: {RADIUS["card"]}px;
            }}
        """)

        self.icon_label.setPixmap(icon_to_use.icon(color=style["text"]).pixmap(40, 40))

        if self.title_label:
            self.title_label.setStyleSheet(f"color: {style['text']}; font-size: 16px; background-color: transparent;")
        
        if self.body_label:
            self.body_label.setStyleSheet(f"color: {style['body']}; line-height: 1.6; background-color: transparent;")


class UIUtils:
    def __init__(self):
        pass

    def build_icon_label(self, icon: FluentIcon, color: str, size: int = 32) -> QLabel:
        label = QLabel()
        label.setPixmap(icon.icon(color=color).pixmap(size, size))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(size + 12, size + 12)
        return label

    def create_info_widget(self, text: str, color: Optional[str] = None) -> QWidget:
        if not text:
            return QWidget()
        
        label = BodyLabel(text)
        label.setWordWrap(True)
        if color:
            label.setStyleSheet("color: {};".format(color))
        return label

    def colored_icon(self, icon: FluentIcon, color_hex: str) -> FluentIcon:
        if not icon or not color_hex:
            return icon
        
        tint = QColor(color_hex)
        return icon.colored(tint, tint)

    def get_compatibility_icon(self, compat_tuple: Optional[Tuple[Optional[str], Optional[str]]]) -> FluentIcon:
        if not compat_tuple or compat_tuple == (None, None):
            return self.colored_icon(FluentIcon.CLOSE, COLORS["error"])
        return self.colored_icon(FluentIcon.ACCEPT, COLORS["success"])

    def add_group_with_indent(self, card: "GroupHeaderCardWidget", icon: FluentIcon, title: str, content: str, widget: Optional[QWidget] = None, indent_level: int = 0) -> "CardGroupWidget":
        if widget is None:
            widget = QWidget()
        
        group = card.addGroup(icon, title, content, widget)
        
        if indent_level > 0:
            base_margin = 24
            indent = 20 * indent_level
            group.hBoxLayout.setContentsMargins(base_margin + indent, 10, 24, 10)
        
        return group

    def create_step_indicator(self, step_number: int, total_steps: int = 4, color: str = "#0078D4") -> BodyLabel:
        # 暗夜模式下调整步骤指示器的颜色，使其更亮
        if isDarkTheme() and color == "#0078D4":
            color = themeColor().name() # 使用主题色
            
        label = BodyLabel("STEP {} OF {}".format(step_number, total_steps))
        # 增加主题监听可能需要将此 Label 也封装，但通常步骤条不那么敏感，这里保持静态或根据需求封装
        # 为了简单，这里只在创建时判断。如果需要动态切换，需要类似的 ThemeAwareLabel 封装。
        # 鉴于步骤条通常在刷新页面时重建，这里问题不大。
        label.setStyleSheet("color: {}; font-weight: bold;".format(color))
        return label

    def create_vertical_spacer(self, spacing: int = SPACING["medium"]) -> QWidget:
        spacer = QWidget()
        spacer.setFixedHeight(spacing)
        return spacer

    def custom_card(self, card_type: str = "note", icon: Optional[FluentIcon] = None, title: str = "", body: str = "", custom_widget: Optional[QWidget] = None, parent: Optional[QWidget] = None) -> CardWidget:
        # 使用新的 ThemeAwareCardWidget 替代原始 CardWidget
        return ThemeAwareCardWidget(card_type, icon, title, body, custom_widget, self, parent)

    def create_footer(self):
        return FooterWidget()