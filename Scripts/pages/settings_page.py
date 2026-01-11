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
    SubtitleLabel, SettingCard, setTheme, Theme, PrimaryPushSettingCard
)

from Scripts import ui_utils
from Scripts.custom_dialogs import show_confirmation, show_info, show_download_dialog
from Scripts.styles import COLORS, SPACING
import updater

# === SKSP Worker ===
class SKSPCheckWorker(QObject):
    finished = pyqtSignal(bool, dict)
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
                self.finished.emit(False, {"error": "无法获取信息"} if not remote_info else {})
        except Exception as e:
            self.finished.emit(False, {"error": str(e)})

class SKSPDownloadWorker(QObject):
    finished = pyqtSignal(bool, str)
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

# === App 更新下载 Worker (已修复) ===
class AppUpdateWorker(QObject):
    update_ready = pyqtSignal(str) 
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    finished = pyqtSignal() # [修复] 补上缺失的信号

    def __init__(self, updater_inst, download_info, cancel_callback=None):
        super().__init__()
        self.updater = updater_inst
        self.info = download_info
        self.cancel_callback = cancel_callback

    @pyqtSlot()
    def run(self):
        def callback(p, m):
            self.progress.emit(p, m)
            
        try:
            # 传入取消检查函数
            new_path = self.updater.perform_update_process(
                self.info, 
                progress_callback=callback,
                cancel_callback=self.cancel_callback
            )
            self.update_ready.emit(new_path)
        except Exception as e:
            # 如果是用户取消，通常抛出特定异常，这里统一当作错误处理或忽略
            # 如果是 "用户取消" 异常，前端可以选择不弹错误框
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class SettingsPage(ScrollArea):
    request_sksp_download = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.settings = self.controller.backend.settings
        self.ui_utils = ui_utils.UIUtils()
        
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        
        # 线程引用
        self.sksp_check_thread = None
        self.sksp_check_worker = None
        self.sksp_dl_thread = None
        self.sksp_dl_worker = None
        
        self.app_check_thread = None
        self.app_dl_thread = None
        self.app_dl_worker = None
        
        self.sksp_dialog = None
        self.update_dialog = None
        
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

        self.expandLayout.addSpacing(SPACING["large"])
        self.expandLayout.addWidget(self.ui_utils.create_footer())
        self.expandLayout.addSpacing(SPACING["small"])

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

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "选择构建输出目录", os.path.expanduser("~"))
        if folder:
            self.settings.set("build_output_directory", folder)
            self.output_dir_card.setContent(folder)
            self.controller.update_status("输出目录更新成功", "success")

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

    # === SKSP 逻辑 ===
    def refresh_sksp_status(self):
        if hasattr(self.controller.backend, 'o'):
            exists, version = self.controller.backend.o.check_sksp_status()
            self.sksp_status_card.setTitle("当前版本: {}".format(version))
            self.sksp_status_card.setContent("状态: {}".format("已安装" if exists else "未安装"))

    def check_sksp_update(self):
        self.update_sksp_btn.setEnabled(False)
        self.update_sksp_btn.setText("检查中...")
        
        self.sksp_check_thread = QThread()
        self.sksp_check_worker = SKSPCheckWorker(self.controller.backend)
        self.sksp_check_worker.moveToThread(self.sksp_check_thread)
        self.sksp_check_thread.started.connect(self.sksp_check_worker.run)
        self.sksp_check_worker.finished.connect(self.on_sksp_check_finished)
        self.sksp_check_worker.finished.connect(self.sksp_check_thread.quit)
        self.sksp_check_thread.finished.connect(self.sksp_check_worker.deleteLater)
        self.sksp_check_thread.finished.connect(self._cleanup_sksp_check)
        self.sksp_check_thread.start()

    def _cleanup_sksp_check(self):
        if self.sksp_check_thread:
            self.sksp_check_thread.deleteLater()
            self.sksp_check_thread = None
        self.sksp_check_worker = None

    @pyqtSlot(bool, dict)
    def on_sksp_check_finished(self, has_update, info):
        self.update_sksp_btn.setText("检查更新")
        self.update_sksp_btn.setEnabled(True)
        if has_update:
            self.update_sksp_btn.setText("更新")
            content = "发现 SKSP 新版本: {} ({})\n\n是否立即更新？".format(info.get('version'), info.get('release_date'))
            if show_confirmation("发现新版本", content):
                self.start_sksp_download()
        else:
            if "error" in info and info["error"]:
                show_info("检查失败", "获取更新信息时出错: {}".format(info["error"]))
            else:
                show_info("已是最新", "当前的 SKSP 资源包已是最新版本。")

    def start_sksp_download(self):
        self.update_sksp_btn.setEnabled(False)
        self.sksp_dialog = show_download_dialog()
        
        self.sksp_dl_thread = QThread()
        self.sksp_dl_worker = SKSPDownloadWorker(self.controller.backend, self.sksp_dialog)
        self.sksp_dl_worker.moveToThread(self.sksp_dl_thread)
        self.sksp_dl_thread.started.connect(self.sksp_dl_worker.run)
        self.sksp_dl_worker.finished.connect(self.on_sksp_update_finished)
        self.sksp_dl_worker.finished.connect(self.sksp_dl_thread.quit)
        self.sksp_dl_thread.finished.connect(self.sksp_dl_worker.deleteLater)
        self.sksp_dl_thread.finished.connect(self._cleanup_sksp_dl)
        self.sksp_dl_thread.start()

    def _cleanup_sksp_dl(self):
        self.sksp_dl_thread = None
        self.sksp_dl_worker = None

    @pyqtSlot(bool, str)
    def on_sksp_update_finished(self, success, msg):
        if self.sksp_dialog:
            self.sksp_dialog.close()
            self.sksp_dialog = None
        self.update_sksp_btn.setText("检查更新")
        self.update_sksp_btn.setEnabled(True)
        if success:
            show_info("成功", "SKSP 更新成功！")
            self.refresh_sksp_status()
        elif msg != "用户取消":
            show_info("失败", "更新失败: {}".format(msg))

    # === 软件更新部分 ===
    def create_update_settings_group(self):
        group = SettingCardGroup("软件更新", self.scrollWidget)
        
        current_ver = getattr(updater, 'CURRENT_VERSION', 'Unknown')
        self.version_card = SettingCard(
            FluentIcon.INFO,
            f"当前版本: v{current_ver}",
            "SimpleKaruzi",
            group
        )
        group.addSettingCard(self.version_card)

        self.auto_update_card = SwitchSettingCard(
            FluentIcon.UPDATE, "启动时检查更新", "启动时自动检查新版本。",
            configItem=None, parent=group
        )
        self.auto_update_card.setObjectName("auto_update_check")
        self.auto_update_card.switchButton.setChecked(self.settings.get_auto_update_check())
        self.auto_update_card.switchButton.checkedChanged.connect(lambda c: self.settings.set("auto_update_check", c))
        group.addSettingCard(self.auto_update_card)

        self.manual_update_card = PrimaryPushSettingCard(
            "检查更新", FluentIcon.SYNC, "检查软件更新", "立即检查 SimpleKaruzi 是否有新版本", group
        )
        self.manual_update_card.clicked.connect(self.manual_check_app_update)
        group.addSettingCard(self.manual_update_card)
        return group

    def manual_check_app_update(self):
        self.manual_update_card.setEnabled(False)
        self.manual_update_card.button.setText("正在检查...")
        
        backend = self.controller.backend
        self.upd_instance = updater.Updater(
            utils_instance=backend.u,
            github_instance=backend.github,
            resource_fetcher_instance=backend.resource_fetcher,
            run_instance=backend.r,
            integrity_checker_instance=backend.integrity_checker
        )
        
        self.app_check_thread = self.upd_instance.create_checker_thread()
        self.app_check_thread.update_available.connect(self._on_app_update_available)
        self.app_check_thread.no_update.connect(self._on_app_no_update)
        self.app_check_thread.check_failed.connect(self._on_app_check_failed)
        self.app_check_thread.finished.connect(self._on_app_check_finished)
        self.app_check_thread.start()

    def _on_app_check_finished(self):
        self.manual_update_card.setEnabled(True)
        self.manual_update_card.button.setText("检查更新")
        if self.app_check_thread:
            self.app_check_thread.deleteLater()
            self.app_check_thread = None

    def _on_app_update_available(self, info):
        self.manual_update_card.setContent(f"发现新版本 v{info['version']}")
        self.controller.update_status("发现更新", "success")
        
        msg = f"""
<h3>发现新版本 v{info['version']}</h3>
<p><b>发布日期:</b> {info.get('date', '未知')}</p>
<hr>
<b>更新日志:</b><br>
{info.get('changelog', '无更新日志')}
<br><br>
是否立即下载并安装？<br>程序将在下载完成后重启。
"""
        if show_confirmation("发现更新", msg):
            self.start_app_download_process(info)

    def _on_app_no_update(self):
        self.manual_update_card.setContent("已是最新")
        self.controller.update_status("已是最新版本", "success")
        show_info("检查完成", "当前已是最新版本！")

    def _on_app_check_failed(self, error_msg):
        self.manual_update_card.setContent("检查失败")
        self.controller.update_status("更新检查失败", "error")
        show_info("检查失败", error_msg)

    def start_app_download_process(self, info):
        self.manual_update_card.setEnabled(False)
        self.manual_update_card.button.setText("下载中...")
        self.controller.update_status("正在下载更新，请勿关闭...", "INFO")
        
        self.update_dialog = show_download_dialog()
        # 这里不需要 update_dialog.show()，因为 show_download_dialog 内部通常已经 exec 或者 show 了
        # 如果 show_download_dialog 是非模态的，可以保留 show()。假设它是 CustomDialogs 里的非模态。
        
        self.app_dl_thread = QThread()
        # 传递取消回调 self.update_dialog.is_canceled
        self.app_dl_worker = AppUpdateWorker(self.upd_instance, info, cancel_callback=self.update_dialog.is_canceled)
        self.app_dl_worker.moveToThread(self.app_dl_thread)
        
        self.app_dl_thread.started.connect(self.app_dl_worker.run)
        self.app_dl_worker.progress.connect(self.update_dialog.update_progress)
        self.app_dl_worker.error.connect(self._on_app_download_error)
        self.app_dl_worker.update_ready.connect(self._on_app_download_success)
        
        self.app_dl_worker.finished.connect(self.app_dl_thread.quit)
        self.app_dl_thread.finished.connect(self._cleanup_app_dl)
        self.app_dl_thread.finished.connect(self.app_dl_worker.deleteLater)
        self.app_dl_thread.finished.connect(self.app_dl_thread.deleteLater)
        
        self.app_dl_thread.start()

    def _on_app_download_success(self, new_path):
        if self.update_dialog:
            self.update_dialog.close()
        show_info("更新成功", "新版本下载解压完成。\n\n点击确定后程序将自动重启以完成安装。")
        self.upd_instance.finalize_update(new_path)

    def _on_app_download_error(self, err_msg):
        if self.update_dialog:
            self.update_dialog.close()
        
        # 如果是“用户取消”，则不弹报错框
        if "用户取消" not in str(err_msg):
            show_info("更新失败", f"错误详情: {err_msg}")

    def _cleanup_app_dl(self):
        self.app_dl_thread = None
        self.app_dl_worker = None
        if self.update_dialog:
            self.update_dialog.close()
            self.update_dialog = None
        self.manual_update_card.setEnabled(True)
        self.manual_update_card.button.setText("检查更新")

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
        self.theme_card = ComboBoxSettingCard(self.theme_config, FluentIcon.BRUSH, "主题", "选择应用程序的颜色主题。", theme_items, group)
        self.theme_card.setObjectName("theme")
        group.addSettingCard(self.theme_card)
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