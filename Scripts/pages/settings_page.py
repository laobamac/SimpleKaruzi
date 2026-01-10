import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QObject
from qfluentwidgets import (
    ScrollArea, BodyLabel, PushButton, LineEdit, FluentIcon,
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard,
    PushSettingCard, SpinBox,
    OptionsConfigItem, OptionsValidator, HyperlinkCard,
    SubtitleLabel, SettingCard, setTheme, Theme
)

from Scripts.custom_dialogs import show_confirmation, show_info, show_download_dialog
from Scripts.styles import COLORS, SPACING
import updater

class UpdateCheckWorker(QObject):
    finished = pyqtSignal(bool, dict) # has_update, info/error

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    @pyqtSlot()
    def run(self):
        try:
            local_info = self.backend.o.get_local_sksp_info()
            local_ver = local_info.get("version") if local_info else "0.0.0"
            
            remote_info = self.backend.o.fetch_remote_sksp_info()
            
            if remote_info and remote_info.get("version") > local_ver:
                self.finished.emit(True, remote_info)
            else:
                if not remote_info:
                    self.finished.emit(False, {"error": "无法获取远程信息"})
                else:
                    self.finished.emit(False, {})
        except Exception as e:
            self.finished.emit(False, {"error": str(e)})

class DownloadWorker(QObject):
    finished = pyqtSignal(bool, str) # success, message

    def __init__(self, backend, dialog):
        super().__init__()
        self.backend = backend
        self.dialog = dialog

    @pyqtSlot()
    def run(self):
        try:
            success, msg = self.backend.o.download_and_install_sksp(self.dialog)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

class SettingsPage(ScrollArea):
    # 信号
    request_sksp_download = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.settings = self.controller.backend.settings
        
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        
        self.check_thread = None
        self.check_worker = None
        self.download_thread = None
        self.download_worker = None
        self.sksp_dialog = None
        
        self.request_sksp_download.connect(self.start_sksp_download)
        
        self._init_ui()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["tiny"])
        header_layout.addWidget(SubtitleLabel("设置"))
        header_layout.addWidget(BodyLabel("配置 SimpleKaruzi 首选项"))
        self.expandLayout.addWidget(header_container)
        self.expandLayout.addSpacing(SPACING["medium"])

        self.build_output_group = self.create_build_output_group()
        self.expandLayout.addWidget(self.build_output_group)
        
        self.sksp_group = self.create_sksp_group()
        self.expandLayout.addWidget(self.sksp_group)

        self.macos_group = self.create_macos_version_group()
        self.expandLayout.addWidget(self.macos_group)

        self.appearance_group = self.create_appearance_group()
        self.expandLayout.addWidget(self.appearance_group)

        self.update_group = self.create_update_settings_group()
        self.expandLayout.addWidget(self.update_group)

        self.advanced_group = self.create_advanced_group()
        self.expandLayout.addWidget(self.advanced_group)

        self.help_group = self.create_help_group()
        self.expandLayout.addWidget(self.help_group)
        
        self.bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, SPACING["large"], 0, SPACING["large"])
        bottom_layout.addStretch()

        reset_btn = PushButton("重置所有设置", self.bottom_widget)
        reset_btn.setIcon(FluentIcon.CANCEL)
        reset_btn.clicked.connect(self.reset_to_defaults)
        bottom_layout.addWidget(reset_btn)

        self.expandLayout.addWidget(self.bottom_widget)

        for card in self.findChildren(SettingCard):
            card.setIconSize(18, 18)

    def _update_widget_value(self, widget, value):
        if widget is None: return
        if isinstance(widget, SwitchSettingCard):
            widget.switchButton.setChecked(value)
        elif isinstance(widget, (ComboBoxSettingCard, OptionsConfigItem)):
            widget.setValue(value)
        elif isinstance(widget, SpinBox):
            widget.setValue(value)
        elif isinstance(widget, LineEdit):
            widget.setText(value)
        elif isinstance(widget, PushSettingCard):
            widget.setContent(value or "使用临时目录（默认）")

    def create_build_output_group(self):
        group = SettingCardGroup("构建输出", self.scrollWidget)
        self.output_dir_card = PushSettingCard(
            "浏览", FluentIcon.FOLDER, "输出目录",
            self.settings.get("build_output_directory") or "使用临时目录（默认）", group
        )
        self.output_dir_card.setObjectName("build_output_directory")
        self.output_dir_card.clicked.connect(self.browse_output_directory)
        group.addSettingCard(self.output_dir_card)
        return group

    def create_sksp_group(self):
        group = SettingCardGroup("SKSP 资源包", self.scrollWidget)
        
        if hasattr(self.controller.backend, 'o'):
            exists, version = self.controller.backend.o.check_sksp_status()
        else:
            exists, version = False, "未知"
        
        self.sksp_status_card = SettingCard(
            FluentIcon.FOLDER, 
            "当前版本: {}".format(version),
            "状态: {}".format("已安装" if exists else "未安装"),
            group
        )
        
        self.update_sksp_btn = PushButton("检查更新", self.sksp_status_card)
        self.update_sksp_btn.clicked.connect(self.check_sksp_update)
        self.sksp_status_card.hBoxLayout.addWidget(self.update_sksp_btn)
        self.sksp_status_card.hBoxLayout.addSpacing(16)
        
        group.addSettingCard(self.sksp_status_card)
        
        self.auto_sksp_card = SwitchSettingCard(
            FluentIcon.SYNC, "自动检查更新", "在生成 EFI 时自动检查资源包更新。",
            configItem=None, parent=group
        )
        self.auto_sksp_card.setObjectName("auto_check_sksp_updates")
        self.auto_sksp_card.switchButton.setChecked(self.settings.get("auto_check_sksp_updates"))
        self.auto_sksp_card.switchButton.checkedChanged.connect(lambda c: self.settings.set("auto_check_sksp_updates", c))
        group.addSettingCard(self.auto_sksp_card)
        
        return group

    def refresh_sksp_status(self):
        """公开方法：刷新 SKSP 状态显示"""
        if hasattr(self.controller.backend, 'o'):
            exists, version = self.controller.backend.o.check_sksp_status()
            self.sksp_status_card.setTitle("当前版本: {}".format(version))
            self.sksp_status_card.setContent("状态: {}".format("已安装" if exists else "未安装"))

    def check_sksp_update(self):
        """使用 QThread 启动检查"""
        self.update_sksp_btn.setEnabled(False)
        self.update_sksp_btn.setText("检查中...")
        
        self.check_thread = QThread()
        self.check_worker = UpdateCheckWorker(self.controller.backend)
        self.check_worker.moveToThread(self.check_thread)
        
        self.check_thread.started.connect(self.check_worker.run)
        self.check_worker.finished.connect(self.on_sksp_check_finished)
        self.check_worker.finished.connect(self.check_thread.quit)
        self.check_worker.finished.connect(self.check_worker.deleteLater)
        
        self.check_thread.finished.connect(self._cleanup_check_thread)
        
        self.check_thread.start()

    def _cleanup_check_thread(self):
        """线程彻底结束后清理引用"""
        if self.check_thread:
            self.check_thread.deleteLater()
            self.check_thread = None

    @pyqtSlot(bool, dict)
    def on_sksp_check_finished(self, has_update, info):
        self.update_sksp_btn.setText("检查更新")
        self.update_sksp_btn.setEnabled(True)
        # 注意：这里不再设置 self.check_thread = None，由 _cleanup_check_thread 处理
        
        if has_update:
            self.update_sksp_btn.setText("更新")
            content = "发现 SKSP 新版本: {} ({})\n\n是否立即更新？".format(
                info.get('version'), info.get('release_date')
            )
            if show_confirmation("发现新版本", content):
                self.start_sksp_download()
        else:
            if "error" in info:
                show_info("错误", "检查更新失败: {}".format(info["error"]))
            else:
                show_info("已是最新", "当前的 SKSP 资源包已是最新版本。")

    def start_sksp_download(self):
        """使用 QThread 启动下载"""
        self.update_sksp_btn.setEnabled(False)
        self.sksp_dialog = show_download_dialog()
        
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(self.controller.backend, self.sksp_dialog)
        self.download_worker.moveToThread(self.download_thread)
        
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.on_sksp_update_finished)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        
        self.download_thread.finished.connect(self._cleanup_download_thread)
        
        self.download_thread.start()

    def _cleanup_download_thread(self):
        """线程彻底结束后清理引用"""
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    @pyqtSlot(bool, str)
    def on_sksp_update_finished(self, success, msg):
        if self.sksp_dialog:
            self.sksp_dialog.close()
            self.sksp_dialog = None
        
        self.update_sksp_btn.setText("检查更新")
        self.update_sksp_btn.setEnabled(True)
        # 注意：这里不再设置 self.download_thread = None，由 _cleanup_download_thread 处理
        
        if success:
            show_info("成功", "SKSP 更新成功！")
            self.refresh_sksp_status()
        elif msg != "用户取消":
            show_info("失败", "更新失败: {}".format(msg))

    def create_macos_version_group(self):
        group = SettingCardGroup("macOS 版本", self.scrollWidget)
        self.include_beta_card = SwitchSettingCard(
            FluentIcon.UPDATE, "包含测试版 (Beta)", "在版本列表中显示测试版 macOS。",
            configItem=None, parent=group
        )
        self.include_beta_card.setObjectName("include_beta_versions")
        self.include_beta_card.switchButton.setChecked(self.settings.get_include_beta_versions())
        self.include_beta_card.switchButton.checkedChanged.connect(lambda c: self.settings.set("include_beta_versions", c))
        group.addSettingCard(self.include_beta_card)
        return group

    def create_appearance_group(self):
        group = SettingCardGroup("外观", self.scrollWidget)
        
        self.theme_map = {"跟随系统": "Auto", "亮色": "Light", "暗色": "Dark"}
        theme_items = list(self.theme_map.keys())
        current_setting = self.settings.get("theme")
        display_val = {v: k for k, v in self.theme_map.items()}.get(current_setting, "跟随系统")

        self.theme_config = OptionsConfigItem("Appearance", "Theme", display_val, OptionsValidator(theme_items))
        
        def on_theme_changed(val):
            internal = self.theme_map.get(val, "Auto")
            self.settings.set("theme", internal)
            setTheme(Theme.DARK if internal == "Dark" else Theme.LIGHT if internal == "Light" else Theme.AUTO)

        self.theme_config.valueChanged.connect(on_theme_changed)
        
        self.theme_card = ComboBoxSettingCard(
            self.theme_config, FluentIcon.BRUSH, "主题", "选择应用程序的颜色主题。", theme_items, group
        )
        self.theme_card.setObjectName("theme")
        group.addSettingCard(self.theme_card)
        return group

    def create_update_settings_group(self):
        group = SettingCardGroup("更新与下载", self.scrollWidget)
        self.auto_update_card = SwitchSettingCard(
            FluentIcon.UPDATE, "启动时检查更新", "启动时自动检查新版本。",
            configItem=None, parent=group
        )
        self.auto_update_card.setObjectName("auto_update_check")
        self.auto_update_card.switchButton.setChecked(self.settings.get_auto_update_check())
        self.auto_update_card.switchButton.checkedChanged.connect(lambda c: self.settings.set("auto_update_check", c))
        group.addSettingCard(self.auto_update_card)

        self.manual_update_card = PushSettingCard(
            "检查更新", FluentIcon.SYNC, "手动检查", "立即检查是否有新版本可用", group
        )
        self.manual_update_card.clicked.connect(self.manual_check_update)
        group.addSettingCard(self.manual_update_card)
        return group

    def create_advanced_group(self):
        group = SettingCardGroup("高级设置", self.scrollWidget)
        self.debug_logging_card = SwitchSettingCard(
            FluentIcon.DEVELOPER_TOOLS, "启用调试日志", "启用详细日志用于故障排除。",
            configItem=None, parent=group
        )
        self.debug_logging_card.setObjectName("enable_debug_logging")
        self.debug_logging_card.switchButton.setChecked(self.settings.get_enable_debug_logging())
        self.debug_logging_card.switchButton.checkedChanged.connect(lambda c: self.settings.set("enable_debug_logging", c))
        group.addSettingCard(self.debug_logging_card)
        return group

    def create_help_group(self):
        group = SettingCardGroup("帮助与文档", self.scrollWidget)
        group.addSettingCard(HyperlinkCard(
            "https://dortania.github.io/OpenCore-Install-Guide/", "OpenCore 安装指南", FluentIcon.BOOK_SHELF, "OpenCore 文档", "安装 macOS 的完整指南", group
        ))
        group.addSettingCard(HyperlinkCard(
            "https://github.com/laobamac/SimpleKaruzi", "在 GitHub 上查看", FluentIcon.GITHUB, "SimpleKaruzi 仓库", "源码与 Issue", group
        ))
        return group

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "选择构建输出目录", os.path.expanduser("~"))
        if folder:
            self.settings.set("build_output_directory", folder)
            self.output_dir_card.setContent(folder)
            self.controller.update_status("输出目录更新成功", "success")

    def manual_check_update(self):
        self.manual_update_card.setEnabled(False)
        self.manual_update_card.button.setText("正在检查...")
        self.manual_update_card.setContent("正在连接服务器...")
        
        backend = self.controller.backend
        self.upd_instance = updater.Updater(
            utils_instance=backend.u,
            github_instance=backend.github,
            resource_fetcher_instance=backend.resource_fetcher,
            run_instance=backend.r,
            integrity_checker_instance=backend.integrity_checker
        )
        
        self.manual_check_thread = self.upd_instance.create_checker_thread()
        self.manual_check_thread.update_available.connect(self._on_manual_update_available)
        self.manual_check_thread.no_update.connect(self._on_manual_no_update)
        self.manual_check_thread.check_failed.connect(self._on_manual_check_failed)
        self.manual_check_thread.finished.connect(self._on_manual_check_finished)
        self.manual_check_thread.start()

    def _on_manual_update_available(self, files_to_update):
        self.manual_update_card.setContent("发现新版本")
        self.controller.update_status("发现更新", "success")
        self.upd_instance.perform_update_process(files_to_update)

    def _on_manual_no_update(self):
        self.manual_update_card.setContent("已是最新")
        self.controller.update_status("已是最新版本", "success")
        show_info("检查完成", "当前已是最新版本！")

    def _on_manual_check_failed(self, error_msg):
        self.manual_update_card.setContent("检查失败")
        self.controller.update_status("更新检查失败", "error")
        show_info("检查失败", error_msg)

    def _on_manual_check_finished(self):
        self.manual_update_card.setEnabled(True)
        self.manual_update_card.button.setText("检查更新")
        self.manual_check_thread = None

    def reset_to_defaults(self):
        if show_confirmation("重置设置", "确定要重置所有设置吗？"):
            self.settings.settings = self.settings.defaults.copy()
            self.settings.save_settings()
            
            for widget in self.findChildren(QWidget):
                key = widget.objectName()
                if key and key in self.settings.defaults:
                    self._update_widget_value(widget, self.settings.defaults.get(key))
            
            self.theme_card.setValue("跟随系统")
            self.controller.update_status("所有设置已重置", "success")