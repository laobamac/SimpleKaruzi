from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CardWidget, StrongBodyLabel, 
    FluentIcon, ScrollArea, themeColor, isDarkTheme, qconfig
)

from Scripts.styles import COLORS, SPACING
from Scripts import ui_utils


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
        
        self._init_ui()
        
        # 初始化样式并监听主题变化
        self.update_style()
        qconfig.themeChanged.connect(self.update_style)

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        self.expandLayout.addWidget(self._create_title_label())
        
        self.expandLayout.addWidget(self._create_hero_section())
        
        self.expandLayout.addWidget(self._create_note_card())
        
        self.expandLayout.addWidget(self._create_warning_card())
        
        self.expandLayout.addWidget(self._create_guide_card())

        self.expandLayout.addStretch()

    def _create_title_label(self):
        self.title_label = SubtitleLabel("欢迎使用 SimpleKaruzi")
        # 初始样式在 update_style 中设置，这里只设静态属性
        return self.title_label

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

        hero_layout.addLayout(hero_text, 2)

        robot_icon = self.ui_utils.build_icon_label(FluentIcon.CARE_LEFT_SOLID, COLORS["primary"], size=64)
        hero_layout.addWidget(robot_icon, 1, Qt.AlignmentFlag.AlignVCenter)

        return hero_card

    def _create_note_card(self):
        # 由 ui_utils.py 接管样式
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

        # 改为 self
        self.guide_title = StrongBodyLabel("快速开始")
        guide_layout.addWidget(self.guide_title)

        step_items = [
            (FluentIcon.FOLDER_ADD, "1. 选择硬件报告", "选择你要为其构建 EFI 的目标系统的硬件报告。"),
            (FluentIcon.CHECKBOX, "2. 检查兼容性", "审查硬件与 macOS 的兼容性。"),
            (FluentIcon.EDIT, "3. 配置设置", "自定义 OpenCore EFI 的 ACPI 补丁、驱动（Kexts）和配置。"),
            (FluentIcon.DEVELOPER_TOOLS, "4. 生成 EFI", "生成你的 OpenCore EFI。"),
        ]
        
        # 这里的子项需要单独处理，比较麻烦，但我们可以利用 QWidget 的 findChildren 或者简单的 CSS 继承。
        # 为了简单且高效，我们让 create_guide_row 返回的 label 能够被管理
        # 但鉴于 guide row 也是普通文本，我们可以通过 update_style 里的通用逻辑处理，
        # 或者在 create_guide_row 里给它们加一个特殊的 objectName，然后用 CSS 统一设置。
        
        # 方案：保存引用列表
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
        divider.setProperty("class", "divider") # 标记一下方便管理
        return divider

    def update_style(self):
        """当主题改变时，强制更新文本颜色"""
        is_dark = isDarkTheme()
        
        # 定义颜色
        if is_dark:
            primary_text = "#ffffff"
            secondary_text = "#d2d2d2"
            theme_color = themeColor().name()
            divider_color = "rgba(255, 255, 255, 0.1)"
        else:
            primary_text = "#000000"
            secondary_text = "#605E5C"
            theme_color = themeColor().name() # 亮色模式下的主题色通常较深
            divider_color = "#E0E0E0"

        # 更新大标题
        self.title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {primary_text};")
        
        # 更新 Hero 区域
        self.hero_title.setStyleSheet(f"font-size: 18px; color: {theme_color};")
        self.hero_body.setStyleSheet(f"line-height: 1.6; font-size: 14px; color: {primary_text};")
        
        # 更新 Guide 区域标题
        self.guide_title.setStyleSheet(f"font-size: 18px; color: {primary_text};")
        
        # 更新 Guide 列表项
        for t_label, d_label in self.guide_labels:
            t_label.setStyleSheet(f"font-size: 14px; color: {primary_text};")
            d_label.setStyleSheet(f"line-height: 1.4; color: {secondary_text};")
            
        # 更新分割线
        for divider in self.findChildren(QFrame):
            if divider.property("class") == "divider":
                divider.setStyleSheet(f"color: {divider_color};")

    def refresh(self):
        pass