import os
import threading

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel
from qfluentwidgets import (
    PushButton, SubtitleLabel, BodyLabel, CardWidget, FluentIcon, 
    StrongBodyLabel, PrimaryPushButton, ProgressBar,
    IconWidget, ExpandGroupSettingCard, isDarkTheme
)

from Scripts.datasets import os_data
from Scripts.custom_dialogs import show_info, show_confirmation
from Scripts.state import HardwareReportState, macOSVersionState, SMBIOSState
from Scripts.styles import SPACING, COLORS
from Scripts import ui_utils

class ReportDetailsGroup(ExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(
            FluentIcon.INFO,
            "硬件报告详情",
            "查看选定的报告路径和验证状态",
            parent
        )
        
        self.reportIcon = IconWidget(FluentIcon.INFO)
        self.reportIcon.setFixedSize(16, 16)
        self.reportIcon.setVisible(False)
        
        self.acpiIcon = IconWidget(FluentIcon.INFO)
        self.acpiIcon.setFixedSize(16, 16)
        self.acpiIcon.setVisible(False)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.reportCard = self.addGroup(
            FluentIcon.DOCUMENT,
            "报告路径",
            "未选择",
            self.reportIcon
        )
        
        self.acpiCard = self.addGroup(
            FluentIcon.FOLDER,
            "ACPI 目录",
            "未选择",
            self.acpiIcon
        )
        
        # 根据主题设置默认文字颜色
        text_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
        self.reportCard.contentLabel.setStyleSheet(f"color: {text_color};")
        self.acpiCard.contentLabel.setStyleSheet(f"color: {text_color};")

    def update_status(self, section, path, status_type, message):
        card = self.reportCard if section == "report" else self.acpiCard
        icon_widget = self.reportIcon if section == "report" else self.acpiIcon
        
        if path and path != "未选择" and path != "未选择":
            path = os.path.normpath(path)
        
        card.setContent(path)
        card.setToolTip(message if message else path)

        icon = FluentIcon.INFO
        # 默认次要文本颜色
        color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
        
        if status_type == "success": 
            # 成功状态：亮色模式用主色，暗色模式用白色
            color = "#ffffff" if isDarkTheme() else COLORS["text_primary"]
            icon = FluentIcon.ACCEPT
        elif status_type == "error": 
            color = COLORS["error"]
            icon = FluentIcon.CANCEL
        elif status_type == "warning": 
            color = COLORS["warning"]
            icon = FluentIcon.INFO
        
        card.contentLabel.setStyleSheet(f"color: {color};")
        icon_widget.setIcon(icon)
        icon_widget.setVisible(True)

class SelectHardwareReportPage(QWidget):
    export_finished_signal = pyqtSignal(bool, str, str, str)
    load_report_progress_signal = pyqtSignal(str, str, int)
    load_report_finished_signal = pyqtSignal(bool, str, str, str)
    report_validated_signal = pyqtSignal(str, str)
    compatibility_checked_signal = pyqtSignal()

    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("SelectHardwareReport")
        self.controller = parent
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        self._connect_signals()
        self._init_ui()

    def _connect_signals(self):
        self.export_finished_signal.connect(self._handle_export_finished)
        self.load_report_progress_signal.connect(self._handle_load_report_progress)
        self.load_report_finished_signal.connect(self._handle_load_report_finished)
        self.report_validated_signal.connect(self._handle_report_validated)
        self.compatibility_checked_signal.connect(self._handle_compatibility_checked)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.main_layout.setSpacing(SPACING["large"])

        self.main_layout.addWidget(self.ui_utils.create_step_indicator(1))
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(SPACING["small"])
        title = SubtitleLabel("选择硬件报告")
        subtitle = BodyLabel("选择你要为其构建 EFI 的目标系统的硬件报告")
        
        # 适配暗夜模式颜色
        subtitle_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
        subtitle.setStyleSheet(f"color: {subtitle_color};")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.main_layout.addLayout(header_layout)

        self.main_layout.addSpacing(SPACING["medium"])

        self.create_instructions_card()

        self.create_action_card()
        
        self.create_report_details_group()

        self.main_layout.addStretch()

    def create_instructions_card(self):
        card = self.ui_utils.custom_card(
            card_type="note",
            title="快速指南",
            body=(
                "<b>Windows 用户：</b>点击 <span style=\"color:#0078D4; font-weight:600;\">导出硬件报告</span> 按钮为当前系统生成硬件报告。或者，您可以使用 Hardware Sniffer 工具手动生成报告。<br>"
                "<b>Linux/macOS 用户：</b>请传输在 Windows 上生成的报告。不支持本机生成。"
            )
        )
        self.main_layout.addWidget(card)

    def create_action_card(self):
        self.action_card = CardWidget()
        layout = QVBoxLayout(self.action_card)
        layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        layout.setSpacing(SPACING["medium"])

        title = StrongBodyLabel("选择方式")
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING["medium"])

        self.select_btn = PrimaryPushButton(FluentIcon.FOLDER_ADD, "选择硬件报告")
        self.select_btn.clicked.connect(self.select_hardware_report)
        btn_layout.addWidget(self.select_btn)

        if os.name == "nt":
            self.export_btn = PushButton(FluentIcon.DOWNLOAD, "导出硬件报告")
            self.export_btn.clicked.connect(self.export_hardware_report)
            btn_layout.addWidget(self.export_btn)

        layout.addLayout(btn_layout)
        
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, SPACING["small"], 0, 0)
        progress_layout.setSpacing(SPACING["medium"])
        
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING["medium"])
        
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(28, 28)
        status_row.addWidget(self.status_icon_label)
        
        self.progress_label = StrongBodyLabel("就绪")
        
        # 适配暗夜模式颜色
        progress_label_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
        self.progress_label.setStyleSheet(f"color: {progress_label_color}; font-size: 15px; font-weight: 600;")
        
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        
        progress_layout.addLayout(status_row)
        
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        self.progress_helper = ui_utils.ProgressStatusHelper(
            self.status_icon_label,
            self.progress_label,
            self.progress_bar,
            self.progress_container
        )

        self.main_layout.addWidget(self.action_card)

    def create_report_details_group(self):
        self.report_group = ReportDetailsGroup(self)
        self.main_layout.addWidget(self.report_group)

    def select_report_file(self):
        report_path, _ = QFileDialog.getOpenFileName(
            self, "选择硬件报告", "", "JSON 文件 (*.json)"
        )
        return report_path if report_path else None

    def select_acpi_folder(self):
        acpi_dir = QFileDialog.getExistingDirectory(self, "选择 ACPI 文件夹", "")
        return acpi_dir if acpi_dir else None
    
    def select_hardware_report(self):
        report_path = self.select_report_file()
        if not report_path:
            return

        report_dir = os.path.dirname(report_path)
        potential_acpi = os.path.join(report_dir, "ACPI")
        
        acpi_dir = None
        if os.path.isdir(potential_acpi):
            if show_confirmation("检测到 ACPI 文件夹", "在以下位置发现了 ACPI 文件夹：{}\n\n您想使用此 ACPI 文件夹吗？".format(potential_acpi)):
                acpi_dir = potential_acpi

        if not acpi_dir:
            acpi_dir = self.select_acpi_folder()

        if not acpi_dir:
            return
        
        self.load_hardware_report(report_path, acpi_dir)

    def set_detail_status(self, section, path, status_type, message):
        self.report_group.update_status(section, path, status_type, message)

    def suggest_macos_version(self):
        if not self.controller.hardware_state.hardware_report or not self.controller.macos_state.native_version:
            return None

        hardware_report = self.controller.hardware_state.hardware_report
        native_macos_version = self.controller.macos_state.native_version

        suggested_macos_version = native_macos_version[1]

        for device_type in ("GPU", "Network", "Bluetooth", "SD Controller"):
            if device_type in hardware_report:
                for device_name, device_props in hardware_report[device_type].items():
                    if device_props.get("Compatibility", (None, None)) != (None, None):
                        if device_type == "GPU" and device_props.get("Device Type") == "Integrated GPU":
                            device_id = device_props.get("Device ID", " " * 8)[5:]

                            if device_props.get("Manufacturer") == "AMD" or device_id.startswith(("59", "87C0")):
                                suggested_macos_version = "22.99.99"
                            elif device_id.startswith(("09", "19")):
                                suggested_macos_version = "21.99.99"

                        if self.controller.backend.u.parse_darwin_version(suggested_macos_version) > self.controller.backend.u.parse_darwin_version(device_props.get("Compatibility")[0]):
                            suggested_macos_version = device_props.get("Compatibility")[0]

        while True:
            if "Beta" in os_data.get_macos_name_by_darwin(suggested_macos_version):
                suggested_macos_version = "{}{}".format(
                    int(suggested_macos_version[:2]) - 1, suggested_macos_version[2:])
            else:
                break

        self.controller.macos_state.suggested_version = suggested_macos_version

    def load_hardware_report(self, report_path, acpi_dir, from_export=False):
        self.controller.hardware_state = HardwareReportState(report_path=report_path, acpi_dir=acpi_dir)
        self.controller.macos_state = macOSVersionState()
        self.controller.smbios_state = SMBIOSState()
        self.controller.backend.ac.acpi.acpi_tables = {}
        self.controller.backend.ac.acpi.dsdt = None
        
        self.controller.compatibilityPage.update_display()
        self.controller.configurationPage.update_display()
        
        if not from_export:
            self.progress_container.setVisible(True)
            self.select_btn.setEnabled(False)
            if hasattr(self, "export_btn"):
                self.export_btn.setEnabled(False)
        
        progress_offset = 40 if from_export else 0
        self.progress_helper.update("loading", "正在验证报告...", progress_offset)
        self.report_group.setExpand(True)
        
        def load_thread():
            try:
                progress_scale = 0.5 if from_export else 1.0
                
                def get_progress(base_progress):
                    return progress_offset + int(base_progress * progress_scale)
                
                self.load_report_progress_signal.emit("loading", "正在验证报告...", get_progress(10))
                
                is_valid, errors, warnings, validated_data = self.controller.backend.v.validate_report(report_path)
                
                if not is_valid or errors:
                    error_msg = "报告错误：\n" + "\n".join(errors)
                    self.load_report_finished_signal.emit(False, "validation_error", report_path, acpi_dir)
                    return
                
                self.load_report_progress_signal.emit("loading", "正在验证报告...", get_progress(30))
                
                self.report_validated_signal.emit(report_path, "硬件报告验证成功。")
                
                self.load_report_progress_signal.emit("loading", "正在检查兼容性...", get_progress(35))
                
                self.controller.hardware_state.hardware_report = validated_data
                
                self.controller.hardware_state.hardware_report, self.controller.macos_state.native_version, self.controller.macos_state.ocl_patched_version, self.controller.hardware_state.compatibility_error = self.controller.backend.c.check_compatibility(validated_data)
                
                self.load_report_progress_signal.emit("loading", "正在检查兼容性...", get_progress(55))

                self.compatibility_checked_signal.emit()

                if self.controller.hardware_state.compatibility_error:
                    error_msg = self.controller.hardware_state.compatibility_error
                    if isinstance(error_msg, list):
                        error_msg = "\n".join(error_msg)
                    self.load_report_finished_signal.emit(False, "compatibility_error", report_path, acpi_dir)
                    return
                
                self.load_report_progress_signal.emit("loading", "正在加载 ACPI 表...", get_progress(60))
                
                self.controller.backend.ac.read_acpi_tables(acpi_dir)
                
                self.load_report_progress_signal.emit("loading", "正在加载 ACPI 表...", get_progress(90))
                
                if not self.controller.backend.ac._ensure_dsdt():
                    self.load_report_finished_signal.emit(False, "acpi_error", report_path, acpi_dir)
                    return
                
                self.load_report_finished_signal.emit(True, "success", report_path, acpi_dir)
                
            except Exception as e:
                self.load_report_finished_signal.emit(False, "异常：{}".format(e), report_path, acpi_dir)
        
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _handle_load_report_progress(self, status, message, progress):
        self.progress_helper.update(status, message, progress)

    def _handle_report_validated(self, report_path, message):
        self.set_detail_status("report", report_path, "success", message)

    def _handle_compatibility_checked(self):
        self.controller.compatibilityPage.update_display()

    def _handle_load_report_finished(self, success, error_type, report_path, acpi_dir):
        self.select_btn.setEnabled(True)
        if hasattr(self, "export_btn"):
            self.export_btn.setEnabled(True)
        
        if success:
            count = len(self.controller.backend.ac.acpi.acpi_tables)
            self.set_detail_status("acpi", acpi_dir, "success", "ACPI 表已加载：找到 {} 个表。".format(count))
            
            self.progress_helper.update("success", "硬件报告加载成功", 100)
            
            self.controller.update_status("硬件报告加载成功", "success")
            self.suggest_macos_version()
            self.controller.configurationPage.update_display()
        else:
            if error_type == "validation_error":
                is_valid, errors, warnings, validated_data = self.controller.backend.v.validate_report(report_path)
                msg = "报告错误：\n" + "\n".join(errors)
                self.set_detail_status("report", report_path, "error", msg)
                self.progress_helper.update("error", "报告验证失败", None)
                show_info("报告验证失败", "硬件报告包含错误：\n{}\n\n请选择有效的报告文件。".format("\n".join(errors)))
            elif error_type == "compatibility_error":
                error_msg = self.controller.hardware_state.compatibility_error
                if isinstance(error_msg, list):
                    error_msg = "\n".join(error_msg)
                compat_text = "\n兼容性错误：\n{}".format(error_msg)
                self.set_detail_status("report", report_path, "error", compat_text)
                show_info("硬件不兼容", "您的硬件与 macOS 不兼容：\n\n" + error_msg)
            elif error_type == "acpi_error":
                self.set_detail_status("acpi", acpi_dir, "error", "在选定的文件夹中未找到 ACPI 表。")
                self.progress_helper.update("error", "未找到 ACPI 表", None)
                show_info("无 ACPI 表", "ACPI 文件夹中未找到 ACPI 表。")
            else:
                self.progress_helper.update("error", "错误：{}".format(error_type), None)
                self.controller.update_status("加载硬件报告失败：{}".format(error_type), "error")

    def export_hardware_report(self):
        self.progress_container.setVisible(True)
        self.select_btn.setEnabled(False)
        if hasattr(self, "export_btn"):
            self.export_btn.setEnabled(False)
        
        self.progress_helper.update("loading", "正在收集硬件信息...", 10)
        
        current_dir = os.path.dirname(os.path.realpath(__file__))
        main_dir = os.path.dirname(os.path.dirname(current_dir))
        report_dir = os.path.join(main_dir, "SysReport")

        def export_thread():
            try:
                hardware_sniffer = self.controller.backend.o.gather_hardware_sniffer()
                
                if not hardware_sniffer:
                    self.export_finished_signal.emit(False, "未找到 Hardware Sniffer", "", "")
                    return
                
                self.export_finished_signal.emit(True, "gathering_complete", hardware_sniffer, report_dir)
            except Exception as e:
                self.export_finished_signal.emit(False, "收集信息时发生异常：{}".format(e), "", "")
        
        thread = threading.Thread(target=export_thread, daemon=True)
        thread.start()

    def _handle_export_finished(self, success, message, hardware_sniffer_or_error, report_dir):
        if not success:
            self.progress_container.setVisible(False)
            self.select_btn.setEnabled(True)
            if hasattr(self, "export_btn"):
                self.export_btn.setEnabled(True)
            self.progress_helper.update("error", "导出失败", 0)
            self.controller.update_status(hardware_sniffer_or_error, "error")
            return
        
        if message == "gathering_complete":
            self.progress_helper.update("loading", "正在导出硬件报告...", 50)
            
            def run_export_thread():
                try:
                    import subprocess
        
                    # 构建命令
                    cmd = [hardware_sniffer_or_error, "-e", "-o", report_dir]
        
                    # 创建启动信息来隐藏控制台窗口
                    startupinfo = None
                    if os.name == "nt":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
        
                    self.controller.backend.u.log_message("[导出] 正在静默运行 Hardware Sniffer...", level="INFO")
        
                    # 使用 subprocess 运行，捕获输出
                    result = subprocess.run(
                        cmd,
                        startupinfo=startupinfo,
                        capture_output=True,  # 捕获标准输出和错误输出
                        text=True,            # 以文本形式返回输出
                        encoding='utf-8',     # 指定编码
                        errors='ignore',      # 忽略解码错误
                        timeout=300,          # 5分钟超时
                    )
        
                    success = result.returncode == 0
                    error_message = ""
                    report_path = ""
                    acpi_dir = ""

                    if success:
                        report_path = os.path.join(report_dir, "Report.json")
                        acpi_dir = os.path.join(report_dir, "ACPI")
                        error_message = "导出成功"
            
                        # 记录成功日志
                        self.controller.backend.u.log_message("[导出] Hardware Sniffer 运行成功", level="INFO")
                        if result.stdout:
                            self.controller.backend.u.log_message(f"[导出] 输出: {result.stdout[:200]}", level="DEBUG")
                    else:
                        error_code = result.returncode
                        # 尝试从标准错误中获取更多信息
                        stderr_output = result.stderr.strip() if result.stderr else ""
            
                        if error_code == 3: 
                            error_message = "收集硬件信息出错。"
                        elif error_code == 4: 
                            error_message = "生成硬件报告出错。"
                        elif error_code == 5: 
                            error_message = "导出 ACPI 表出错。"
                        else: 
                            error_message = f"未知错误 (代码: {error_code})。"
            
                        if stderr_output:
                            error_message += f"\n详细错误: {stderr_output[:500]}"  # 限制长度
            
                        # 记录错误日志
                        self.controller.backend.u.log_message(f"[导出] Hardware Sniffer 失败: {error_message}", level="ERROR")
                        if stderr_output:
                            self.controller.backend.u.log_message(f"[导出] 错误输出: {stderr_output}", level="ERROR")

                    paths = "{}|||{}".format(report_path, acpi_dir) if report_path and acpi_dir else ""
                    self.export_finished_signal.emit(success, "export_complete", error_message, paths)
        
                except subprocess.TimeoutExpired:
                    error_msg = "Hardware Sniffer 运行超时 (5分钟)"
                    self.controller.backend.u.log_message(f"[导出] {error_msg}", level="ERROR")
                    self.export_finished_signal.emit(False, "export_complete", error_msg, "")
                except FileNotFoundError:
                    error_msg = f"找不到可执行文件: {hardware_sniffer_or_error}"
                    self.controller.backend.u.log_message(f"[导出] {error_msg}", level="ERROR")
                    self.export_finished_signal.emit(False, "export_complete", error_msg, "")
                except Exception as e:
                    error_msg = f"运行 Hardware Sniffer 时发生异常: {e}"
                    self.controller.backend.u.log_message(f"[导出] {error_msg}", level="ERROR")
                    self.export_finished_signal.emit(False, "export_complete", error_msg, "")
            
            thread = threading.Thread(target=run_export_thread, daemon=True)
            thread.start()
            return
        
        if message == "export_complete":
            self.progress_container.setVisible(False)
            self.select_btn.setEnabled(True)
            if hasattr(self, "export_btn"):
                self.export_btn.setEnabled(True)

            self.controller.backend.u.log_message("[导出] 导出至：{}".format(report_dir), level="INFO")
            
            if success:
                if report_dir and "|||" in report_dir:
                    report_path, acpi_dir = report_dir.split("|||", 1)
                else:
                    report_path = ""
                    acpi_dir = ""
                
                if report_path and acpi_dir:
                    self.load_hardware_report(report_path, acpi_dir, from_export=True)
                else:
                    self.progress_helper.update("error", "导出完成但路径无效", None)
                    self.controller.update_status("导出完成但路径无效", "error")
            else:
                self.progress_helper.update("error", "导出失败：{}".format(hardware_sniffer_or_error), None)
                self.controller.update_status("导出失败：{}".format(hardware_sniffer_or_error), "error")