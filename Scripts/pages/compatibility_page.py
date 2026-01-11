from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, ScrollArea, FluentIcon, 
    GroupHeaderCardWidget, CardWidget, StrongBodyLabel,
    SwitchButton, IndicatorPosition, isDarkTheme
)

from Scripts.styles import COLORS, SPACING
from Scripts import ui_utils
from Scripts.datasets import os_data, pci_data


class CompatibilityStatusBanner:
    def __init__(self, parent_widget, layout):
        self.parent = parent_widget
        self.ui_utils = ui_utils.UIUtils()
        self.layout = layout
        self.card = None

    def _create_card(self, card_type, icon, title, message, note=""):
        body_text = message
        if note:
            note_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
            body_text += "<br><br><i style=\"color: {}; font-size: 12px;\">{}</i>".format(note_color, note)
        
        if self.card:
            self.layout.removeWidget(self.card)
            self.card.deleteLater()
            self.card = None
        
        self.card = self.ui_utils.custom_card(
            card_type=card_type,
            icon=icon,
            title=title,
            body=body_text,
            parent=self.parent
        )
        self.card.setVisible(True)
        self.layout.addWidget(self.card)
        
        return self.card

    def show_error(self, title, message, note=""):
        self._create_card("error", FluentIcon.CLOSE, title, message, note)

    def show_success(self, title, message, note=""):
        self._create_card("success", FluentIcon.ACCEPT, title, message, note)
    
    def setVisible(self, visible):
        if self.card:
            self.card.setVisible(visible)

class CompatibilityPage(ScrollArea):
    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("compatibilityPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        self.contentWidget = None
        self.contentLayout = None
        
        # 统计状态
        self.found_unsupported = False
        self.found_oclp = False
        
        # 默认不显示详情 (简约模式)
        self.show_details = False
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        
        self._init_ui()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        self.expandLayout.addWidget(self.ui_utils.create_step_indicator(2))

        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["large"])

        title_block = QWidget()
        title_layout = QVBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(SPACING["tiny"])

        title_label = SubtitleLabel("硬件兼容性")
        title_layout.addWidget(title_label)

        subtitle_label = BodyLabel("查看硬件与 macOS 的兼容性")
        title_layout.addWidget(subtitle_label)

        header_layout.addWidget(title_block, 1)

        # 详细模式切换开关
        self.detail_switch = SwitchButton(parent=header_container)
        self.detail_switch.setOnText("详细信息")
        self.detail_switch.setOffText("简约视图")
        self.detail_switch.setChecked(self.show_details)
        self.detail_switch.checkedChanged.connect(self._on_detail_switch_changed)
        header_layout.addWidget(self.detail_switch, 0, Qt.AlignmentFlag.AlignRight)

        self.expandLayout.addWidget(header_container)
        
        self.bannerContainer = QWidget()
        self.bannerLayout = QVBoxLayout(self.bannerContainer)
        self.bannerLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.bannerContainer)
        
        self.status_banner = CompatibilityStatusBanner(self.bannerContainer, self.bannerLayout)
        
        self.expandLayout.addSpacing(SPACING["medium"])

        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(SPACING["large"])
        self.expandLayout.addWidget(self.contentWidget)

        self._show_placeholder()

        self.expandLayout.addWidget(self.ui_utils.create_footer())
        self.expandLayout.addSpacing(SPACING["small"])

    def _on_detail_switch_changed(self, checked):
        self.show_details = checked
        self.update_display()

    def _is_device_supported(self, compat):
        """判断设备是否被原生 macOS 支持"""
        if not compat or compat == (None, None):
            return False
        return True

    def update_status_banner(self):
        if not self.controller.hardware_state.hardware_report:
            self.status_banner.setVisible(False)
            return

        if self.controller.hardware_state.compatibility_error:
            self._show_error_banner()
            return

        self._show_support_banner()

    def _show_error_banner(self):
        codes = self.controller.hardware_state.compatibility_error
        if isinstance(codes, str):
            codes = [codes]

        code_map = {
            "ERROR_MISSING_SSE4": (
                "缺少必需的 SSE4.x 指令集。",
                "您的 CPU 不支持比 Sierra (10.12) 更新的 macOS 版本。"
            ),
            "ERROR_NO_COMPATIBLE_GPU": (
                "无法在没有受支持 GPU 的情况下安装 macOS。",
                "请不要再就此问题向我发送垃圾邮件或提交 issue！"
            ),
            "ERROR_INTEL_VMD": (
                "macOS 不支持 Intel VMD 控制器。",
                "请在 BIOS 设置中禁用 Intel VMD，然后重新生成硬件报告并重试。"
            ),
            "ERROR_NO_COMPATIBLE_STORAGE": (
                "未找到兼容 macOS 的存储控制器！",
                "建议为您的系统购买兼容的 NVMe SSD。"
            )
        }

        title = "硬件兼容性问题"
        messages = []
        notes = []
        for code in codes:
            msg, note = code_map.get(code, (code, ""))
            messages.append(msg)
            if note:
                notes.append(note)

        self.status_banner.show_error(
            title,
            "\n".join(messages),
            "\n".join(notes)
        )

    def _show_support_banner(self):
        if self.controller.macos_state.native_version:
            min_ver_name = os_data.get_macos_name_by_darwin(self.controller.macos_state.native_version[0])
            max_ver_name = os_data.get_macos_name_by_darwin(self.controller.macos_state.native_version[-1])
            native_range = min_ver_name if min_ver_name == max_ver_name else "{} 至 {}".format(min_ver_name, max_ver_name)
            
            message = "原生 macOS 支持：{}".format(native_range)
            
            if self.controller.macos_state.ocl_patched_version:
                 oclp_max_name = os_data.get_macos_name_by_darwin(self.controller.macos_state.ocl_patched_version[0])
                 oclp_min_name = os_data.get_macos_name_by_darwin(self.controller.macos_state.ocl_patched_version[-1])
                 oclp_range = oclp_min_name if oclp_min_name == oclp_max_name else "{} 至 {}".format(oclp_min_name, oclp_max_name)
                 message += "\n补丁扩展支持：{}".format(oclp_range)

            self.status_banner.show_success("硬件兼容", message)
        else:
            self.status_banner.show_error(
                "硬件不兼容",
                "未找到支持此硬件配置的 macOS 版本。"
            )

    def format_compatibility(self, compat_tuple):
        if not compat_tuple or compat_tuple == (None, None):
            return "不支持", "#D13438"

        max_ver, min_ver = compat_tuple

        if max_ver and min_ver:
            max_name = os_data.get_macos_name_by_darwin(max_ver)
            min_name = os_data.get_macos_name_by_darwin(min_ver)

            if max_name == min_name:
                return "最高支持 {}".format(max_name), "#0078D4"
            else:
                return "{} 至 {}".format(min_name, max_name), "#107C10"

        return "未知", "#605E5C"

    def update_display(self):
        if self.contentLayout:
            while self.contentLayout.count() > 0:
                item = self.contentLayout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        if not self.controller.hardware_state.hardware_report:
            self._show_placeholder()
            self.update_status_banner()
            return

        report = self.controller.hardware_state.hardware_report
        cards_added = 0
        
        # 重置统计
        self.found_unsupported = False
        self.found_oclp = False

        cards_added += self._add_cpu_card(report)
        cards_added += self._add_gpu_card(report)
        cards_added += self._add_sound_card(report)
        cards_added += self._add_network_card(report)
        cards_added += self._add_storage_card(report)
        cards_added += self._add_bluetooth_card(report)
        cards_added += self._add_biometric_card(report)
        cards_added += self._add_sd_card(report)

        # 逻辑判断：显示提示卡片
        if cards_added == 0 and not self.show_details:
            # 简约模式 + 无任何卡片显示 => 全部完美兼容
            self._show_all_good_label()
        elif not self.show_details and not self.found_unsupported and self.found_oclp:
            # 简约模式 + 有卡片显示 + 没有不兼容项 + 但有 OCLP 项 => 显示 OCLP 提示
            # 注意：这里的卡片就是 OCLP 的设备
            self._show_oclp_hint_label()
        elif cards_added == 0 and self.show_details:
            self._show_no_data_label()

        self.contentLayout.addStretch()
        self.update_status_banner()
        QApplication.processEvents()

    def _show_placeholder(self):
        self.placeholder_label = BodyLabel("加载硬件报告以查看兼容性信息")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_color = "#9E9E9E" if isDarkTheme() else "#605E5C"
        self.placeholder_label.setStyleSheet("color: {}; padding: 40px;".format(text_color))
        self.placeholder_label.setWordWrap(True)
        self.contentLayout.addWidget(self.placeholder_label)
        self.contentLayout.addStretch()

    def _show_no_data_label(self):
        no_data_card = self.ui_utils.custom_card(
            card_type="error",
            icon=FluentIcon.CLOSE,
            title="报告中未找到兼容的硬件信息。",
            body="请确保硬件报告包含有效的设备数据。",
            parent=self.scrollWidget
        )
        self.contentLayout.addWidget(no_data_card)

    def _show_all_good_label(self):
        """当简约模式下所有硬件都兼容时显示"""
        all_good_card = self.ui_utils.custom_card(
            card_type="success",
            icon=FluentIcon.COMPLETED,
            title="未检测到不兼容的硬件",
            body="太棒了！您的所有硬件组件（CPU、显卡、网卡等）似乎都兼容 macOS。<br>您可以点击右上角的“详细信息”开关查看完整规格列表。",
            parent=self.scrollWidget
        )
        self.contentLayout.addWidget(all_good_card)

    def _show_oclp_hint_label(self):
        """当所有硬件都支持但部分需要 OCLP 时显示"""
        oclp_card = self.ui_utils.custom_card(
            card_type="warning", # 使用黄色警告样式
            icon=FluentIcon.INFO,
            title="检测到需要 OCLP 补丁的硬件",
            body="您的部分硬件在较新版本的 macOS 上需要使用 <b>OCLP(-Mod)</b> 才能正常工作。<br>SimpleKaruzi 将在构建过程中自动协助您配置补丁。",
            parent=self.scrollWidget
        )
        # 插入到最前面 (索引0)
        self.contentLayout.insertWidget(0, oclp_card)

    def _add_compatibility_group(self, card, title, compat):
        compat_text, compat_color = self.format_compatibility(compat)
        self.ui_utils.add_group_with_indent(
            card,
            self.ui_utils.get_compatibility_icon(compat),
            title,
            compat_text,
            self.ui_utils.create_info_widget("", compat_color),
            indent_level=1
        )

    def _add_technical_details(self, card, details_dict):
        if not self.show_details:
            return
            
        details_text = []
        for k, v in details_dict.items():
            if v:
                details_text.append("{}: {}".format(k, v))
        
        if details_text:
            self.ui_utils.add_group_with_indent(
                card,
                self.ui_utils.colored_icon(FluentIcon.CODE, COLORS["info"]),
                "技术规格",
                " • ".join(details_text),
                indent_level=1
            )

    def _check_and_update_stats(self, compat, has_oclp=False):
        """辅助方法：更新不支持/OCLP计数"""
        is_supported = self._is_device_supported(compat)
        if not is_supported:
            self.found_unsupported = True
        if has_oclp:
            self.found_oclp = True
        return is_supported

    def _add_cpu_card(self, report):
        if "CPU" not in report: return 0
        cpu_info = report["CPU"]
        if not isinstance(cpu_info, dict): return 0
        
        compat = cpu_info.get("Compatibility", (None, None))
        is_supported = self._check_and_update_stats(compat)
        
        if not self.show_details and is_supported:
            return 0
        
        cpu_card = GroupHeaderCardWidget(self.scrollWidget)
        cpu_card.setTitle("处理器 (CPU)")
        
        name = cpu_info.get("Processor Name", "Unknown")
        self.ui_utils.add_group_with_indent(
            cpu_card,
            self.ui_utils.colored_icon(FluentIcon.TAG, COLORS["primary"]),
            "处理器型号",
            name,
            indent_level=0
        )

        self._add_compatibility_group(cpu_card, "macOS 兼容性", compat)

        self._add_technical_details(cpu_card, {
            "代号": cpu_info.get("Codename"),
            "核心数": cpu_info.get("Core Count"),
            "线程数": cpu_info.get("Thread Count"),
            "基础频率": cpu_info.get("Base Frequency")
        })

        self.contentLayout.addWidget(cpu_card)
        return 1

    def _add_gpu_card(self, report):
        if "GPU" not in report or not report["GPU"]: return 0
        
        visible_items = []
        for gpu_name, gpu_info in report["GPU"].items():
            compat = gpu_info.get("Compatibility", (None, None))
            has_oclp = "OCLP Compatibility" in gpu_info
            is_supported = self._check_and_update_stats(compat, has_oclp)
            
            # 显示条件：详细模式 OR 不原生支持 OR 需要 OCLP 补丁
            if self.show_details or not is_supported or has_oclp:
                visible_items.append((gpu_name, gpu_info, compat))
        
        if not visible_items:
            return 0
            
        gpu_card = GroupHeaderCardWidget(self.scrollWidget)
        gpu_card.setTitle("显卡 (Graphics)")

        for gpu_name, gpu_info, compat in visible_items:
            device_type = gpu_info.get("Device Type", "Unknown")
            self.ui_utils.add_group_with_indent(
                gpu_card,
                self.ui_utils.colored_icon(FluentIcon.PHOTO, COLORS["primary"]),
                gpu_name,
                "类型: {}".format(device_type),
                indent_level=0
            )

            self._add_compatibility_group(gpu_card, "macOS 兼容性", compat)

            if "OCLP Compatibility" in gpu_info:
                oclp_compat = gpu_info.get("OCLP Compatibility")
                oclp_text, oclp_color = self.format_compatibility(oclp_compat)
                info_text_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
                
                self.ui_utils.add_group_with_indent(
                    gpu_card,
                    self.ui_utils.colored_icon(FluentIcon.IOT, COLORS["primary"]),
                    "OCLP 兼容性",
                    oclp_text,
                    self.ui_utils.create_info_widget("通过 OCLP(-Mod) 提供扩展支持", info_text_color),
                    indent_level=1
                )

            if self.show_details:
                self._add_technical_details(gpu_card, {
                    "设备 ID": gpu_info.get("Device ID"),
                    "供应商": gpu_info.get("Manufacturer")
                })

                if "Monitor" in report:
                    self._add_monitor_info(gpu_card, gpu_name, gpu_info, report["Monitor"])

        self.contentLayout.addWidget(gpu_card)
        return 1

    def _add_monitor_info(self, gpu_card, gpu_name, gpu_info, monitors):
        connected_monitors = []
        for monitor_name, monitor_info in monitors.items():
            if monitor_info.get("Connected GPU") == gpu_name:
                connector = monitor_info.get("Connector Type", "Unknown")
                monitor_str = "{} ({})".format(monitor_name, connector)
                
                manufacturer = gpu_info.get("Manufacturer", "")
                raw_device_id = gpu_info.get("Device ID", "")
                device_id = raw_device_id[5:] if len(raw_device_id) > 5 else raw_device_id

                if "Intel" in manufacturer and device_id.startswith(("01", "04", "0A", "0C", "0D")):
                    if connector == "VGA":
                        monitor_str += " (不支持)"
                
                connected_monitors.append(monitor_str)

        if connected_monitors:
            self.ui_utils.add_group_with_indent(
                gpu_card,
                self.ui_utils.colored_icon(FluentIcon.VIEW, COLORS["info"]),
                "已连接显示器",
                ", ".join(connected_monitors),
                indent_level=1
            )

    def _add_sound_card(self, report):
        if "Sound" not in report or not report["Sound"]: return 0
        
        visible_items = []
        for audio_device, audio_props in report["Sound"].items():
            compat = audio_props.get("Compatibility", (None, None))
            is_supported = self._check_and_update_stats(compat)
            
            if self.show_details or not is_supported:
                visible_items.append((audio_device, audio_props, compat))
        
        if not visible_items:
            return 0
        
        sound_card = GroupHeaderCardWidget(self.scrollWidget)
        sound_card.setTitle("声卡 (Audio)")

        for audio_device, audio_props, compat in visible_items:
            self.ui_utils.add_group_with_indent(
                sound_card,
                self.ui_utils.colored_icon(FluentIcon.MUSIC, COLORS["primary"]),
                audio_device,
                "",
                indent_level=0
            )

            self._add_compatibility_group(sound_card, "macOS 兼容性", compat)

            if self.show_details:
                self._add_technical_details(sound_card, {
                    "设备 ID": audio_props.get("Device ID"),
                    "控制器 ID": audio_props.get("Controller Device ID")
                })
                
                endpoints = audio_props.get("Audio Endpoints", [])
                if endpoints:
                    self.ui_utils.add_group_with_indent(
                        sound_card,
                        self.ui_utils.colored_icon(FluentIcon.HEADPHONE, COLORS["info"]),
                        "音频接口",
                        ", ".join(endpoints),
                        indent_level=1
                    )

        self.contentLayout.addWidget(sound_card)
        return 1

    def _add_network_card(self, report):
        if "Network" not in report or not report["Network"]: return 0
        
        visible_items = []
        for device_name, device_props in report["Network"].items():
            compat = device_props.get("Compatibility", (None, None))
            has_oclp = "OCLP Compatibility" in device_props
            is_supported = self._check_and_update_stats(compat, has_oclp)
            
            if self.show_details or not is_supported or has_oclp:
                visible_items.append((device_name, device_props, compat))
        
        if not visible_items:
            return 0
        
        network_card = GroupHeaderCardWidget(self.scrollWidget)
        network_card.setTitle("网卡 (Network)")

        for device_name, device_props, compat in visible_items:
            self.ui_utils.add_group_with_indent(
                network_card,
                self.ui_utils.colored_icon(FluentIcon.WIFI, COLORS["primary"]),
                device_name,
                "",
                indent_level=0
            )

            self._add_compatibility_group(network_card, "macOS 兼容性", compat)

            if "OCLP Compatibility" in device_props:
                oclp_compat = device_props.get("OCLP Compatibility")
                oclp_text, oclp_color = self.format_compatibility(oclp_compat)
                info_text_color = "#d2d2d2" if isDarkTheme() else COLORS["text_secondary"]
                
                self.ui_utils.add_group_with_indent(
                    network_card,
                    self.ui_utils.colored_icon(FluentIcon.IOT, COLORS["primary"]),
                    "OCLP 兼容性",
                    oclp_text,
                    self.ui_utils.create_info_widget("通过 OCLP(-Mod) 提供扩展支持", info_text_color),
                    indent_level=1
                )

            self._add_continuity_info(network_card, device_props)
            
            if self.show_details:
                self._add_technical_details(network_card, {
                    "设备 ID": device_props.get("Device ID"),
                    "总线类型": device_props.get("Bus Type")
                })

        self.contentLayout.addWidget(network_card)
        return 1

    def _add_continuity_info(self, network_card, device_props):
        device_id = device_props.get("Device ID", "")
        if not device_id: return
        
        continuity_info = ""
        continuity_color = COLORS["text_secondary"]

        if device_id in pci_data.BroadcomWiFiIDs:
            continuity_info = "完整支持 (隔空投送, 接力, 通用剪贴板, 个人热点等)"
            continuity_color = COLORS["success"]
        elif device_id in pci_data.IntelWiFiIDs:
            continuity_info = "部分支持 (通过 AirportItlwm 实现接力与通用剪贴板) - 隔空投送, 个人热点等不可用"
            continuity_color = COLORS["warning"]
        elif device_id in pci_data.AtherosWiFiIDs:
            continuity_info = "有限支持 (无接力功能)。不推荐在 macOS 使用 Atheros 网卡。"
            continuity_color = COLORS["error"]

        if continuity_info and (self.show_details or continuity_color != COLORS["success"]):
            self.ui_utils.add_group_with_indent(
                network_card,
                self.ui_utils.colored_icon(FluentIcon.SYNC, continuity_color),
                "接力功能 (Continuity)",
                continuity_info,
                self.ui_utils.create_info_widget("", continuity_color),
                indent_level=1
            )

    def _add_storage_card(self, report):
        if "Storage Controllers" not in report or not report["Storage Controllers"]: return 0
        
        visible_items = []
        for controller_name, controller_props in report["Storage Controllers"].items():
            compat = controller_props.get("Compatibility", (None, None))
            is_supported = self._check_and_update_stats(compat)
            
            if self.show_details or not is_supported:
                visible_items.append((controller_name, controller_props, compat))
        
        if not visible_items:
            return 0
        
        storage_card = GroupHeaderCardWidget(self.scrollWidget)
        storage_card.setTitle("存储 (Storage)")

        for controller_name, controller_props, compat in visible_items:
            self.ui_utils.add_group_with_indent(
                storage_card,
                self.ui_utils.colored_icon(FluentIcon.FOLDER, COLORS["primary"]),
                controller_name,
                "",
                indent_level=0
            )

            self._add_compatibility_group(storage_card, "macOS 兼容性", compat)

            if self.show_details:
                self._add_technical_details(storage_card, {
                    "设备 ID": controller_props.get("Device ID"),
                    "供应商": controller_props.get("Manufacturer")
                })

                disk_drives = controller_props.get("Disk Drives", [])
                if disk_drives:
                    self.ui_utils.add_group_with_indent(
                        storage_card,
                        self.ui_utils.colored_icon(FluentIcon.FOLDER, COLORS["info"]),
                        "磁盘驱动器",
                        ", ".join(disk_drives),
                        indent_level=1
                    )

        self.contentLayout.addWidget(storage_card)
        return 1

    def _add_bluetooth_card(self, report):
        if "Bluetooth" not in report or not report["Bluetooth"]: return 0
        
        visible_items = []
        for bluetooth_name, bluetooth_props in report["Bluetooth"].items():
            compat = bluetooth_props.get("Compatibility", (None, None))
            is_supported = self._check_and_update_stats(compat)
            
            if self.show_details or not is_supported:
                visible_items.append((bluetooth_name, bluetooth_props, compat))
        
        if not visible_items:
            return 0
        
        bluetooth_card = GroupHeaderCardWidget(self.scrollWidget)
        bluetooth_card.setTitle("蓝牙 (Bluetooth)")

        for bluetooth_name, bluetooth_props, compat in visible_items:
            self.ui_utils.add_group_with_indent(
                bluetooth_card,
                self.ui_utils.colored_icon(FluentIcon.BLUETOOTH, COLORS["primary"]),
                bluetooth_name,
                "",
                indent_level=0
            )

            self._add_compatibility_group(bluetooth_card, "macOS 兼容性", compat)
            
            if self.show_details:
                self._add_technical_details(bluetooth_card, {
                    "设备 ID": bluetooth_props.get("Device ID"),
                    "供应商": bluetooth_props.get("Manufacturer")
                })

        self.contentLayout.addWidget(bluetooth_card)
        return 1

    def _add_biometric_card(self, report):
        if "Biometric" not in report or not report["Biometric"]: return 0
        
        # 生物识别全是不兼容的，必须更新 stats
        for bio_props in report["Biometric"].values():
            # 假设全不支持
            self.found_unsupported = True
        
        bio_card = GroupHeaderCardWidget(self.scrollWidget)
        bio_card.setTitle("生物识别 (Biometric)")

        self.ui_utils.add_group_with_indent(
            bio_card,
            self.ui_utils.colored_icon(FluentIcon.CLOSE, COLORS["warning"]),
            "硬件限制",
            "macOS 的生物识别验证需要 Apple T2 芯片，黑苹果系统无法支持。",
            self.ui_utils.create_info_widget("", COLORS["warning"]),
            indent_level=0
        )

        for bio_device, bio_props in report["Biometric"].items():
            self.ui_utils.add_group_with_indent(
                bio_card,
                self.ui_utils.colored_icon(FluentIcon.FINGERPRINT, COLORS["error"]),
                bio_device,
                "不支持",
                indent_level=0
            )
            
            if self.show_details:
                self._add_technical_details(bio_card, {
                    "设备 ID": bio_props.get("Device ID")
                })

        self.contentLayout.addWidget(bio_card)
        return 1

    def _add_sd_card(self, report):
        if "SD Controller" not in report or not report["SD Controller"]: return 0
        
        visible_items = []
        for controller_name, controller_props in report["SD Controller"].items():
            compat = controller_props.get("Compatibility", (None, None))
            is_supported = self._check_and_update_stats(compat)
            
            if self.show_details or not is_supported:
                visible_items.append((controller_name, controller_props, compat))
        
        if not visible_items:
            return 0
        
        sd_card = GroupHeaderCardWidget(self.scrollWidget)
        sd_card.setTitle("SD 控制器")

        for controller_name, controller_props, compat in visible_items:
            self.ui_utils.add_group_with_indent(
                sd_card,
                self.ui_utils.colored_icon(FluentIcon.SAVE, COLORS["primary"]),
                controller_name,
                "",
                indent_level=0
            )

            self._add_compatibility_group(sd_card, "macOS 兼容性", compat)
            
            if self.show_details:
                self._add_technical_details(sd_card, {
                    "设备 ID": controller_props.get("Device ID"),
                    "供应商": controller_props.get("Manufacturer")
                })

        self.contentLayout.addWidget(sd_card)
        return 1

    def refresh(self):
        self.update_display()