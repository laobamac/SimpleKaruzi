import os
import json
import urllib.request
import ssl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot, QTimer
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CardWidget, StrongBodyLabel, 
    FluentIcon, ScrollArea, themeColor, isDarkTheme, qconfig
)

from Scripts.styles import COLORS, SPACING
from Scripts import ui_utils

# === 公告获取线程 ===
class NoticeWorker(QObject):
    finished = pyqtSignal(dict) # 返回 json 数据

    def __init__(self):
        super().__init__()
        self.notice_url = "https://next.oclpapi.simplehac.cn/SKSP/notice.json"

    @pyqtSlot()
    def run(self):
        try:
            # 忽略 SSL 错误防止部分环境报错
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # 设置超时
            req = urllib.request.Request(self.notice_url, headers={'User-Agent': 'SimpleKaruzi-Client'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.finished.emit(data)
        except Exception:
            self.finished.emit({})

class HomePage(ScrollArea):
    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        
        self.scrollWidget.setStyleSheet("QWidget { background: transparent; }")
        
        self.notice_thread = None
        self.notice_worker = None
        self.notice_card = None
        
        self._init_ui()
        
        # 初始化样式并监听主题变化
        self.update_style()
        qconfig.themeChanged.connect(self.update_style)
        
        # 延时 1秒 启动公告检查
        QTimer.singleShot(1000, self.fetch_notice)

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        self.expandLayout.addWidget(self._create_title_label())
        
        # === 公告卡片 (默认隐藏) ===
        self.notice_card = self._create_notice_placeholder()
        self.expandLayout.addWidget(self.notice_card)
        
        self.expandLayout.addWidget(self._create_hero_section())
        
        self.expandLayout.addWidget(self._create_note_card())
        
        self.expandLayout.addWidget(self._create_warning_card())
        
        self.expandLayout.addWidget(self._create_guide_card())

        self.expandLayout.addStretch()
        
        # === 版权信息 ===
        self.expandLayout.addWidget(self._create_footer())
        self.expandLayout.addSpacing(SPACING["small"])

    def _create_title_label(self):
        self.title_label = SubtitleLabel("欢迎使用 SimpleKaruzi")
        return self.title_label

    def _create_notice_placeholder(self):
        """创建一个初始隐藏的公告卡片占位"""
        card = self.ui_utils.custom_card(
            card_type="info",
            title="正在获取公告...",
            body=""
        )
        card.setVisible(False) # 默认隐藏
        return card

    def _create_hero_section(self):
        hero_card = CardWidget()
        
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        hero_layout.setSpacing(SPACING["large"])

        hero_text = QVBoxLayout()
        hero_text.setSpacing(SPACING["medium"])

        self.hero_title = StrongBodyLabel("简介")
        hero_text.addWidget(self.hero_title)

        self.hero_body = BodyLabel(
            "这是一个专门用于简化 OpenCore EFI 制作流程的工具，通过自动化核心设置步骤并提供标准化配置，"
            "旨在减少手动操作的工作量，同时确保黑苹果折腾过程中的准确性。"
        )
        self.hero_body.setWordWrap(True)
        hero_text.addWidget(self.hero_body)

        hero_layout.addLayout(hero_text, 1)

        # === 图标部分 ===
        icon_label = QLabel()
        icon_path = "icon.png"
        
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(pixmap)
        else:
            icon_label = self.ui_utils.build_icon_label(FluentIcon.CARE_LEFT_SOLID, COLORS["primary"], size=64)

        icon_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        hero_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignRight)

        return hero_card

    def fetch_notice(self):
        """启动线程获取公告"""
        # 如果已有线程在运行，先不处理
        if self.notice_thread is not None:
            return

        self.notice_thread = QThread()
        self.notice_worker = NoticeWorker()
        self.notice_worker.moveToThread(self.notice_thread)
        
        self.notice_thread.started.connect(self.notice_worker.run)
        self.notice_worker.finished.connect(self.on_notice_received)
        self.notice_worker.finished.connect(self.notice_thread.quit)
        self.notice_worker.finished.connect(self.notice_worker.deleteLater)
        
        # [修复关键] 连接 finished 信号到清理函数，而不是在槽函数里直接置 None
        self.notice_thread.finished.connect(self._cleanup_thread)
        self.notice_thread.finished.connect(self.notice_thread.deleteLater)
        
        self.notice_thread.start()

    def _cleanup_thread(self):
        """线程彻底结束后清理引用"""
        self.notice_thread = None
        self.notice_worker = None

    @pyqtSlot(dict)
    def on_notice_received(self, data):
        """处理公告数据"""
        # 注意：这里不要设置 self.notice_thread = None，由 _cleanup_thread 处理
        
        if not data or not data.get("show"):
            if self.notice_card:
                self.notice_card.setVisible(False)
            return

        # 获取数据
        msg_type = data.get("type", "info")
        title = data.get("title", "公告")
        message = data.get("message", "")

        # 移除旧的占位卡片
        if self.notice_card:
            self.expandLayout.removeWidget(self.notice_card)
            self.notice_card.deleteLater()

        icon_map = {
            "info": FluentIcon.INFO,
            "warning": FluentIcon.INFO,
            "error": FluentIcon.CLOSE,
            "success": FluentIcon.ACCEPT
        }
        
        # 创建新卡片
        self.notice_card = self.ui_utils.custom_card(
            card_type=msg_type,
            icon=icon_map.get(msg_type, FluentIcon.INFO),
            title=title,
            body=message,
            parent=self.scrollWidget
        )
        
        # 插入到标题下方
        self.expandLayout.insertWidget(1, self.notice_card)
        self.notice_card.setVisible(True)

    def _create_note_card(self):
        return self.ui_utils.custom_card(
            card_type="note",
            title="OCLP-Mod III - 现已支持 macOS Tahoe 26！",
            body=(
                "期待已久的OCLP-Mod 3.x.x 版本已经发布，为社区带来了<b>对macOS Tahoe 26的初始支持</b>！<br><br>"
                "<b>请注意：</b><br>"
                "- 只有来自<a href=\"https://github.com/laobamac/OCLP-Mod\" style=\"color: #0078D4; text-decoration: none;\">laobamac/OCLP-Mod</a>仓库的OCLP-Mod 3.x.x为macOS Tahoe 26提供了早期补丁支持。<br>"
                "- 官方的Dortania版本或旧版补丁<b>将无法工作</b>于macOS Tahoe 26。"
            )
        )

    def _create_warning_card(self):
        return self.ui_utils.custom_card(
            card_type="warning",
            title="警告",
            body=(
                "虽然SimpleKaruzi显著减少了设置时间，但Hackintosh之旅仍然需要：<br><br>"
                "- 理解<a href=\"https://dortania.github.io/OpenCore-Install-Guide/\" style=\"color: #F57C00; text-decoration: none;\">Dortania指南</a>中的基本概念<br>"
                "- 在安装过程中进行测试和故障排除<br>"
                "- 耐心和坚持解决出现的任何问题<br><br>"
                "我们的工具不能保证第一次尝试就能成功安装，但它应该能帮助您开始。"
            )
        )

    def _create_guide_card(self):
        guide_card = CardWidget()
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        guide_layout.setSpacing(SPACING["medium"])

        self.guide_title = StrongBodyLabel("快速开始")
        guide_layout.addWidget(self.guide_title)

        step_items = [
            (FluentIcon.FOLDER_ADD, "1. 选择硬件报告", "选择你要为其构建 EFI 的目标系统的硬件报告。"),
            (FluentIcon.CHECKBOX, "2. 检查兼容性", "审查硬件与 macOS 的兼容性。"),
            (FluentIcon.EDIT, "3. 配置设置", "自定义 OpenCore EFI 的 ACPI 补丁、驱动（Kexts）和配置。"),
            (FluentIcon.DEVELOPER_TOOLS, "4. 生成 EFI", "生成你的 OpenCore EFI。"),
        ]
        
        self.guide_labels = [] 

        for idx, (icon, title, desc) in enumerate(step_items):
            row_widget, t_label, d_label = self._create_guide_row(icon, title, desc)
            self.guide_labels.append((t_label, d_label))
            guide_layout.addWidget(row_widget)

            if idx < len(step_items) - 1:
                guide_layout.addWidget(self._create_divider())

        return guide_card

    def _create_guide_row(self, icon, title, desc):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACING["medium"])

        icon_container = QWidget()
        icon_container.setFixedWidth(40)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        row_icon = self.ui_utils.build_icon_label(icon, COLORS["primary"], size=24)
        icon_layout.addWidget(row_icon)
        
        row_layout.addWidget(icon_container)

        text_col = QVBoxLayout()
        text_col.setSpacing(SPACING["tiny"])
        
        title_label = StrongBodyLabel(title)
        
        desc_label = BodyLabel(desc)
        desc_label.setWordWrap(True)
        
        text_col.addWidget(title_label)
        text_col.addWidget(desc_label)
        row_layout.addLayout(text_col)

        return row, title_label, desc_label

    def _create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("class", "divider")
        return divider

    def _create_footer(self):
        footer_widget = QWidget()
        layout = QVBoxLayout(footer_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.footer_label = BodyLabel(
            "Author: <a href='https://github.com/laobamac' style='text-decoration: none;'>laobamac</a> | "
            "Project: <a href='https://github.com/laobamac/SimpleKaruzi' style='text-decoration: none;'>SimpleKaruzi</a>"
        )
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setOpenExternalLinks(True)
        
        self.license_label = BodyLabel(
            "Licensed under <a href='https://github.com/laobamac/SimpleKaruzi/blob/main/LICENSE' style='text-decoration: none;'>AGPL-3.0 License</a>"
        )
        self.license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.license_label.setOpenExternalLinks(True)
        
        layout.addWidget(self.footer_label)
        layout.addWidget(self.license_label)
        
        return footer_widget

    def update_style(self):
        is_dark = isDarkTheme()
        
        if is_dark:
            primary_text = "#ffffff"
            secondary_text = "#d2d2d2"
            footer_text_color = "#888888"
            footer_link_color = "#4CC2FF"
            theme_color = themeColor().name()
            divider_color = "rgba(255, 255, 255, 0.1)"
        else:
            primary_text = "#000000"
            secondary_text = "#605E5C"
            footer_text_color = "#707070"
            footer_link_color = "#0078D4"
            theme_color = themeColor().name()
            divider_color = "#E0E0E0"

        self.title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {primary_text};")
        
        self.hero_title.setStyleSheet(f"font-size: 18px; color: {theme_color};")
        self.hero_body.setStyleSheet(f"line-height: 1.6; font-size: 14px; color: {primary_text};")
        
        self.guide_title.setStyleSheet(f"font-size: 18px; color: {primary_text};")
        
        for t_label, d_label in self.guide_labels:
            t_label.setStyleSheet(f"font-size: 14px; color: {primary_text};")
            d_label.setStyleSheet(f"line-height: 1.4; color: {secondary_text};")
            
        for divider in self.findChildren(QFrame):
            if divider.property("class") == "divider":
                divider.setStyleSheet(f"color: {divider_color};")

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

    def refresh(self):
        pass