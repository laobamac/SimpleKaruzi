from Scripts.datasets import cpu_data
from Scripts.datasets import kext_data
from Scripts.datasets import os_data
from Scripts.datasets import pci_data
from Scripts.datasets import codec_layouts
from Scripts import utils
import os
import shutil
import random
import platform
import sys
from qfluentwidgets import isDarkTheme

try:
    long
    unicode
except NameError:
    long = int
    unicode = str

from Scripts.custom_dialogs import show_options_dialog, show_info, show_confirmation, show_checklist_dialog

class KextMaestro:
    def __init__(self, utils_instance=None):
        self.utils = utils_instance if utils_instance else utils.Utils()
        self.matching_keys = [
            "IOPCIMatch", 
            "IONameMatch", 
            "IOPCIPrimaryMatch", 
            "idProduct", 
            "idVendor", 
            "HDAConfigDefault"
        ]
        if getattr(sys, 'frozen', False):
            app_name = "SimpleKaruzi"
            if platform.system() == "Windows":
                base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            elif platform.system() == "Darwin":
                base_dir = os.path.expanduser("~/Library/Application Support")
            else:
                base_dir = os.path.expanduser("~/.config")
            
            self.ock_files_dir = os.path.join(base_dir, app_name, "OCK_Files")
        else:
            self.ock_files_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "OCK_Files")
        self.kexts = kext_data.kexts
    
    def _get_highlight_color(self):
        """获取用于强调文本的颜色（适配亮/暗模式）"""
        return "#FF99A4" if isDarkTheme() else "red"
        
    def extract_pci_id(self, kext_path):
        if not os.path.exists(kext_path):
            return []

        plist_path = os.path.join(kext_path, "Contents", "Info.plist")
        plist_data = self.utils.read_file(plist_path)

        pci_ids = []

        for personality_name, properties in plist_data.get("IOKitPersonalities", {}).items():
            matching_keys = [key for key in self.matching_keys if key in properties]
            
            if not matching_keys:
                continue
            
            match_key = matching_keys[0]

            if match_key in ["IOPCIMatch", "IOPCIPrimaryMatch"]:
                pci_list = properties[match_key].split(" ")
                for pci_id in pci_list:
                    vendor_id = pci_id[-4:]
                    device_id = pci_id[2:6]
                    pci_ids.append("{}-{}".format(vendor_id, device_id).upper())
            elif match_key == "IONameMatch":
                for pci_id in properties[match_key]:
                    vendor_id = pci_id[3:7]
                    device_id = pci_id.split(",")[1].zfill(4)
                    pci_ids.append("{}-{}".format(vendor_id, device_id).upper())
            elif match_key == "idProduct":
                vendor_id = self.utils.int_to_hex(properties["idVendor"]).zfill(4)
                device_id = self.utils.int_to_hex(properties["idProduct"]).zfill(4)
                pci_ids.append("{}-{}".format(vendor_id, device_id).upper())
            elif match_key == "HDAConfigDefault":
                for codec_layout in properties[match_key]:
                    codec_id = self.utils.int_to_hex(codec_layout.get("CodecID")).zfill(8)
                    pci_ids.append("{}-{}".format(codec_id[:4], codec_id[-4:]))
                pci_ids = sorted(list(set(pci_ids)))

        return pci_ids

    def is_intel_hedt_cpu(self, processor_name, cpu_codename):
        if cpu_codename in cpu_data.IntelCPUGenerations[45:66]:
            return cpu_codename.endswith(("-X", "-P", "-W", "-E", "-EP", "-EX"))
        
        if cpu_codename in cpu_data.IntelCPUGenerations[66:]:
            return "Xeon" in processor_name
        
        return False

    def _select_audio_codec_layout(self, hardware_report, default_layout_id=None):
        codec_id = None
        audio_controller_properties = None

        for codec_properties in hardware_report.get("Sound", {}).values():
            if codec_properties.get("Device ID") in codec_layouts.data:
                codec_id = codec_properties.get("Device ID")

                if codec_properties.get("Controller Device ID"):
                    for device_name, device_properties in hardware_report.get("System Devices", {}).items():
                        if device_properties.get("Device ID") == codec_properties.get("Controller Device ID"):
                            audio_controller_properties = device_properties
                            break
                break

        available_layouts = codec_layouts.data.get(codec_id)
        
        if not available_layouts:
            return None, None

        options = []
        default_index = 0
        
        if default_layout_id is None:
            recommended_authors = ("Mirone", "InsanelyDeepak", "Toleda", "DalianSky")
            recommended_layouts = [layout for layout in available_layouts if self.utils.contains_any(recommended_authors, layout.comment)]
            default_layout_id = random.choice(recommended_layouts or available_layouts).id
            
        for i, layout in enumerate(available_layouts):
            options.append("{} - {}".format(layout.id, layout.comment))
            if layout.id == default_layout_id:
                default_index = i

        while True:
            content = "为了获得最佳音质，请在安装后尝试多个布局，以确定最适合您硬件的布局。"

            selected_index = show_options_dialog(
                title="选择音频布局 ID (Codec Layout ID)",
                content=content,
                options=options,
                default_index=default_index
            )

            if selected_index is not None:
                return available_layouts[selected_index].id, audio_controller_properties

    def check_kext(self, index, target_darwin_version, allow_unsupported_kexts=False):
        kext = self.kexts[index]

        if kext.checked or not (allow_unsupported_kexts or self.utils.parse_darwin_version(kext.min_darwin_version) <= self.utils.parse_darwin_version(target_darwin_version) <= self.utils.parse_darwin_version(kext.max_darwin_version)):
            return

        kext.checked = True

        for requires_kext_name in kext.requires_kexts:
            requires_kext_index = kext_data.kext_index_by_name.get(requires_kext_name)
            if requires_kext_index:
                self.check_kext(requires_kext_index, target_darwin_version, allow_unsupported_kexts)

        if kext.conflict_group_id:
            for other_kext in self.kexts:
                if other_kext.conflict_group_id == kext.conflict_group_id and other_kext.name != kext.name:
                    other_kext.checked = False

    def select_required_kexts(self, hardware_report, macos_version, needs_oclp, acpi_patches):
        self.utils.log_message("[KEXT MAESTRO] 正在检查所需的内核扩展...", level="INFO")

        for kext in self.kexts:
            kext.checked = kext.required

        selected_kexts = ["UTBDefault"]

        if "Intel" in hardware_report.get("CPU").get("Manufacturer"):
            selected_kexts.extend(("SMCProcessor", "SMCSuperIO"))

        if "Laptop" in hardware_report.get("Motherboard").get("Platform") and not "SURFACE" in hardware_report.get("Motherboard").get("Name"):
            selected_kexts.append("SMCBatteryManager")
            if "DELL" in hardware_report.get("Motherboard").get("Name"):
                selected_kexts.append("SMCDellSensors")
            selected_kexts.append("SMCLightSensor")

        if  not (" Core" in hardware_report.get("CPU").get("Processor Name") and \
                 hardware_report.get("CPU").get("Codename") in cpu_data.IntelCPUGenerations[28:]) or \
            self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("23.0.0"):
            selected_kexts.append("RestrictEvents")

        for codec_properties in hardware_report.get("Sound", {}).values():
            if codec_properties.get("Device ID") in codec_layouts.data:
                if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("25.0.0"):
                    content = (
                        "自 macOS Tahoe 26 DP2 起，Apple 移除了 AppleHDA 并使用 Apple T2 芯片进行音频管理。<br>"
                        "因此，AppleALC 将不再起作用，直到您回滚 AppleHDA。"
                    )
                    options = [
                        "<b>AppleALC</b> - 需要使用 <b>安装补丁</b> 回滚 AppleHDA",
                        "<b>VoodooHDA</b> - 音质低于 AppleHDA，Kext 注入到 <b>/Library/Extensions</b>"
                    ]
                    result = show_options_dialog("音频 Kext 选择", content, options, default_index=0)
                    if result == 0:
                        needs_oclp = True
                        selected_kexts.append("AppleALC")
                else:
                    selected_kexts.append("AppleALC")

        if "AppleALC" in selected_kexts:
            audio_layout_id, audio_controller_properties = self._select_audio_codec_layout(hardware_report)
        else:
            audio_layout_id = None
            audio_controller_properties = None
        
        if "AMD" in hardware_report.get("CPU").get("Manufacturer") and self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("21.4.0") or \
            int(hardware_report.get("CPU").get("CPU Count")) > 1 and self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("19.0.0"):
            selected_kexts.append("AppleMCEReporterDisabler")

        if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("22.0.0") and not "AVX2" in hardware_report.get("CPU").get("SIMD Features"):
            selected_kexts.append("CryptexFixup")

        if  "Lunar Lake" not in hardware_report.get("CPU").get("Codename") and \
            "Meteor Lake" not in hardware_report.get("CPU").get("Codename") and \
            hardware_report.get("CPU").get("Codename") in cpu_data.IntelCPUGenerations[:20] and \
            int(hardware_report.get("CPU").get("Core Count")) > 6:
            selected_kexts.append("CpuTopologyRebuild")

        for gpu_name, gpu_props in hardware_report.get("GPU", {}).items():
            if "Integrated GPU" in gpu_props.get("Device Type"):
                if "AMD" in gpu_props.get("Manufacturer"):
                    selected_kexts.append("NootedRed")
                else:
                    selected_kexts.append("WhateverGreen")
            else:
                if "Navi 22" in gpu_props.get("Codename"):
                    selected_kexts.append("NootRX")
                    break

                if gpu_props.get("Codename") in {"Navi 21", "Navi 23"}:
                    hl_color = self._get_highlight_color()
                    content = (
                        "<span style='color:{color}; font-weight:bold'>重要：黑屏修复</span><br>"
                        "如果您在详细模式（Verbose）后遇到黑屏：<br>"
                        "1. 使用 ProperTree 打开 config.plist<br>"
                        "2. 导航至 NVRAM -> Add -> 7C436110-AB2A-4BBB-A880-FE41995C9F82 -> boot-args<br>"
                        "3. 从 boot-args 中移除 \"-v debug=0x100 keepsyms=1\"<br><br>"
                    ).format(color=hl_color)

                    options = [
                        "<b>NootRX</b> - 使用最新的 GPU 固件",
                        "<b>WhateverGreen</b> - 使用原始 Apple 固件",
                    ]

                    if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("25.0.0"):
                        content += (
                            "自 macOS Tahoe 26 起，WhateverGreen 在 AMD {} 显卡上存在已知的接口修补问题。<br>"
                            "为避免此问题，您可以使用 <a href='https://wxcznb.lanzouw.com/iRoL43fsdmre'>laobamac/WhateverGreen</a> 或 NootRX 或选择不安装显卡 Kext。"
                        ).format(gpu_props.get("Codename"))
                        options.append("<b>不使用任何 Kext</b>")
                        recommended_option = 0
                    else:
                        content += (
                            "AMD {} 显卡有两个可用的 Kext 选项：<br>"
                            "您可以在安装后尝试不同的 Kext，以找到最适合您系统的选项。"
                        ).format(gpu_props.get("Codename"))
                        recommended_option = 1

                    if any(other_gpu_props.get("Manufacturer") == "Intel" for other_gpu_props in hardware_report.get("GPU", {}).values()):
                        show_info("NootRX Kext 警告", "NootRX Kext 不兼容 Intel 显卡。<br>由于存在 Intel 显卡，已自动选择 WhateverGreen Kext。")
                        selected_kexts.append("WhateverGreen")
                        continue

                    result = show_options_dialog("AMD 显卡驱动扩展选择", content, options, default_index=recommended_option)
                    
                    if result == 0:
                        selected_kexts.append("NootRX")
                    elif result == 1:
                        selected_kexts.append("WhateverGreen")

                    continue

                if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("25.0.0"):
                    content = (
                        "自 macOS Tahoe 26 起，原版 WhateverGreen 在 AMD 显卡上存在已知的接口修补问题。<br>"
                        "已默认不添加WhateverGreen，但为了更稳定的Hackintosh建议您手动下载下方驱动并添加启用↓<br>"
                        "使用 laobamac/WhateverGreen 作为优秀的替代方案。<a href='https://wxcznb.lanzouw.com/iRoL43fsdmre'>点击此处下载</a><br>"
                    )
                    show_info("警告", content)
                    break

                selected_kexts.append("WhateverGreen")

        if "Laptop" in hardware_report.get("Motherboard").get("Platform") and ("ASUS" in hardware_report.get("Motherboard").get("Name") or "NootedRed" in selected_kexts):
            selected_kexts.append("ForgedInvariant")

        if self.is_intel_hedt_cpu(hardware_report.get("CPU").get("Processor Name"), hardware_report.get("CPU").get("Codename")):
            selected_kexts.append("CpuTscSync")

        if needs_oclp:
            selected_kexts.extend(("AMFIPass", "RestrictEvents"))

        for network_name, network_props in hardware_report.get("Network", {}).items():
            device_id = network_props.get("Device ID")

            if device_id in pci_data.BroadcomWiFiIDs and self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("23.0.0"):
                selected_kexts.append("IOSkywalkFamily")

            if device_id in pci_data.BroadcomWiFiIDs[:15]:
                selected_kexts.append("AirportBrcmFixup")
            elif device_id == pci_data.BroadcomWiFiIDs[15] and self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("19.0.0"):
                selected_kexts.append("AirportBrcmFixup")
            elif device_id in pci_data.BroadcomWiFiIDs[16:18] and self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("20.0.0"):
                selected_kexts.append("AirportBrcmFixup")
            elif device_id in pci_data.IntelWiFiIDs:
                hl_color = self._get_highlight_color()
                airport_itlwm_content = (
                    "<b>AirportItlwm</b> - 使用原生 WiFi 设置菜单<br>"
                    "• 提供接力 (Handoff)、通用剪贴板、定位服务、个人热点支持<br>"
                    "• 支持企业级安全<br>"
                )

                if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("24.0.0"):
                    airport_itlwm_content += "• <span style='color:{}'>自 macOS Sequoia 15 起</span>：可以配合 OCLP 根补丁使用，但可能会导致问题".format(hl_color)
                elif self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("23.0.0"):
                    airport_itlwm_content += "• <span style='color:{}'>在 macOS Sonoma 14 上</span>：除非使用 OCLP 根补丁，否则 iServices 无法工作".format(hl_color)

                itlwm_content = (
                    "<b>itlwm</b> - 总体更稳定<br>"
                    "• 配合 <b>HeliPort</b> 应用使用，而非原生 WiFi 设置菜单<br>"
                    "• 无 Apple 接力功能和企业级安全性<br>"
                    "• 可连接隐藏网络"
                )

                recommended_option = 1 if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("23.0.0") else 0
                options = [airport_itlwm_content, itlwm_content]

                if "Beta" in os_data.get_macos_name_by_darwin(macos_version):
                    show_info("Intel 网卡 Kext 选择", "对于 macOS 测试版 (Beta)，仅支持 itlwm kext。")
                    selected_option = 1
                else:
                    result = show_options_dialog("Intel 网卡 Kext 选择", "Intel 无线网卡有两个可用的 Kext 选项：", options, default_index=recommended_option)
                    selected_option = result if result is not None else recommended_option

                if selected_option == 1:
                    selected_kexts.append("itlwm")
                else:
                    selected_kexts.append("AirportItlwm")
                    
                    if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("24.0.0"):
                        selected_kexts.append("IOSkywalkFamily")
                    elif self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("23.0.0"):
                        content = (
                            "自 macOS Sonoma 14 起，如果不打补丁，AirportItlwm 无法使用 iServices。<br><br>"
                            "应用 OCLP 根补丁以修复 iServices？"
                        )
                        if show_confirmation("需要安装补丁", content):
                            selected_kexts.append("IOSkywalkFamily")
            elif device_id in pci_data.AtherosWiFiIDs[:8]:
                selected_kexts.append("corecaptureElCap")
                if self.utils.parse_darwin_version(macos_version) > self.utils.parse_darwin_version("20.99.99"):
                    selected_kexts.append("AMFIPass")
            elif device_id in pci_data.IntelI22XIDs:
                selected_kexts.append("AppleIGC")
            elif device_id in pci_data.AtherosE2200IDs:
                selected_kexts.append("AtherosE2200Ethernet")
            elif device_id in pci_data.IntelMausiIDs:
                selected_kexts.append("IntelMausiEthernet")
            elif device_id in pci_data.RealtekRTL8125IDs:
                selected_kexts.append("LucyRTL8125Ethernet")
            elif device_id in pci_data.RealtekRTL8100IDs:
                selected_kexts.append("RealtekRTL8100")
            elif device_id in pci_data.RealtekRTL8111IDs:
                selected_kexts.append("RealtekRTL8111")
            elif device_id in pci_data.AppleIGBIDs:
                selected_kexts.append("AppleIGB")
            elif device_id in pci_data.BroadcomBCM57XXIDs:
                selected_kexts.append("CatalinaBCM5701Ethernet")
            elif device_id in pci_data.IntelX500IDs:
                selected_kexts.append("IntelLucy")

        if all(network_props.get("Bus Type") == "USB" for network_props in hardware_report.get("Network", {}).values()):
            selected_kexts.append("NullEthernet")

        for bluetooth_name, bluetooth_props in hardware_report.get("Bluetooth", {}).items():
            usb_id = bluetooth_props.get("Device ID")

            if usb_id in pci_data.AtherosBluetoothIDs:
                selected_kexts.extend(("Ath3kBT", "Ath3kBTInjector"))
            elif usb_id in pci_data.BroadcomBluetoothIDs:               
                selected_kexts.append("BrcmFirmwareData")
            elif usb_id in pci_data.IntelBluetoothIDs:
                selected_kexts.append("IntelBluetoothFirmware")
            elif usb_id in pci_data.BluetoothIDs[-1]:
                selected_kexts.append("BlueToolFixup")

        if "Laptop" in hardware_report.get("Motherboard").get("Platform"):
            if "SURFACE" in hardware_report.get("Motherboard").get("Name"):
                selected_kexts.append("BigSurface")
            else:
                if "ASUS" in hardware_report.get("Motherboard").get("Name"):
                    selected_kexts.append("AsusSMC")
                selected_kexts.append("BrightnessKeys")

                for device_name, device_props in hardware_report.get("Input").items():
                    if not device_props.get("Device"):
                        continue

                    device_id = device_props.get("Device")
                    idx = None
                    if device_id in pci_data.InputIDs:
                        idx = pci_data.InputIDs.index(device_id)

                    if "PS/2" in device_props.get("Device Type", "None"):
                        selected_kexts.append("VoodooPS2Controller")
                        if device_id.startswith("SYN"):
                            selected_kexts.append("VoodooRMI")
                        elif idx and 75 < idx < 79:
                            selected_kexts.append("VoodooSMBus")
                    if "I2C" in device_props.get("Device Type", "None"):
                        selected_kexts.append("VoodooI2CHID")
                        if idx:
                            if idx < 76:
                                selected_kexts.append("AlpsHID")
                            elif 78 < idx:
                                selected_kexts.append("VoodooRMI")
        
        for device_name, device_info in hardware_report.get("System Devices", {}).items():
            if device_info.get("Bus Type") == "ACPI" and device_info.get("Device") in pci_data.YogaHIDs:
                selected_kexts.append("YogaSMC")

        if any(patch.checked for patch in acpi_patches if patch.name == "BATP"):
            selected_kexts.append("ECEnabler")

        for controller_name, controller_props in hardware_report.get("SD Controller", {}).items():
            if controller_props.get("Device ID") in pci_data.RealtekCardReaderIDs:
                if controller_props.get("Device ID") in pci_data.RealtekCardReaderIDs[5:]:
                    selected_kexts.append("Sinetek-rtsx")
                else:
                    selected_kexts.append("RealtekCardReader")
        
        for controller_name, controller_props in hardware_report.get("Storage Controllers", {}).items():
            if "NVMe" in controller_name or "NVM Express" in controller_name:
                selected_kexts.append("NVMeFix")
            elif not "AHCI" in controller_name or "AMD" in hardware_report.get("CPU").get("Manufacturer"):
                if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("20.0.0"):
                    if controller_props.get("Device ID") in pci_data.UnsupportedSATAControllerIDs:
                        selected_kexts.append("CtlnaAHCIPort")
                else:
                    if controller_props.get("Device ID") in pci_data.UnsupportedSATAControllerIDs[15:]:
                        selected_kexts.append("SATA-unsupported")

        for controller_name, controller_props in hardware_report.get("USB Controllers").items():
            device_id = controller_props.get("Device ID")
            if device_id in pci_data.UnsupportedUSBControllerIDs:
                idx = pci_data.UnsupportedUSBControllerIDs.index(device_id)
                if idx == 0:
                    if "Laptop" in hardware_report.get("Motherboard").get("Platform"):
                        selected_kexts.append("GenericUSBXHCI")
                else:
                    selected_kexts.append("XHCI-unsupported")

        if "Sandy Bridge" in hardware_report.get("CPU").get("Codename"):
            selected_kexts.append("ASPP-Override")

        if "Sandy Bridge" in hardware_report.get("CPU").get("Codename") or "Ivy Bridge" in hardware_report.get("CPU").get("Codename"):
            selected_kexts.extend(("AppleIntelCPUPowerManagement", "AppleIntelCPUPowerManagementClient"))

        allow_unsupported_kexts = self.verify_kext_compatibility(selected_kexts, macos_version)

        for name in selected_kexts:
            self.check_kext(kext_data.kext_index_by_name.get(name), macos_version, allow_unsupported_kexts)

        return needs_oclp, audio_layout_id, audio_controller_properties

    def install_kexts_to_efi(self, macos_version, kexts_directory):
        for kext in self.kexts:
            if kext.checked:
                try:
                    source_kext_path = destination_kext_path = None

                    kext_paths = self.utils.find_matching_paths(self.ock_files_dir, extension_filter=".kext", name_filter=kext.name)
                    for kext_path, type in kext_paths:
                        if "AirportItlwm" == kext.name:
                            version = macos_version[:2]
                            if all((self.kexts[kext_data.kext_index_by_name.get("IOSkywalkFamily")].checked, self.kexts[kext_data.kext_index_by_name.get("IO80211FamilyLegacy")].checked)) or self.utils.parse_darwin_version("24.0.0") <= self.utils.parse_darwin_version(macos_version):
                                version = "22"
                            elif self.utils.parse_darwin_version("23.4.0") <= self.utils.parse_darwin_version(macos_version):
                                version = "23.4"
                            elif self.utils.parse_darwin_version("23.0.0") <= self.utils.parse_darwin_version(macos_version):
                                version = "23.0"
                            
                            if version in kext_path:
                                source_kext_path = os.path.join(self.ock_files_dir, kext_path)
                                destination_kext_path = os.path.join(kexts_directory, os.path.basename(kext_path))
                                break
                        else:
                            main_kext = kext_path.split("/")[0]
                            main_kext_index = kext_data.kext_index_by_name.get(main_kext)
                            if not main_kext_index or self.kexts[main_kext_index].checked:
                                if os.path.splitext(os.path.basename(kext_path))[0] in kext.name:
                                    source_kext_path = os.path.join(self.ock_files_dir, kext_path)
                                    destination_kext_path = os.path.join(kexts_directory, os.path.basename(kext_path))
                    
                    if os.path.exists(source_kext_path):
                        shutil.copytree(source_kext_path, destination_kext_path, dirs_exist_ok=True)
                except:
                    continue

    def process_kext(self, kexts_directory, kext_path):
        try:
            plist_path = self.utils.find_matching_paths(os.path.join(kexts_directory, kext_path), extension_filter=".plist", name_filter="Info")[0][0]
            bundle_info = self.utils.read_file(os.path.join(kexts_directory, kext_path, plist_path))

            if isinstance(bundle_info.get("CFBundleIdentifier", None), (str, unicode)):
                pass
        except:
            return None

        executable_path = os.path.join("Contents", "MacOS", bundle_info.get("CFBundleExecutable", "None"))
        if not os.path.exists(os.path.join(kexts_directory, kext_path, executable_path)):
            executable_path = ""
        
        return {
            "BundlePath": kext_path.replace("\\", "/").lstrip("/"),
            "Enabled": True,
            "ExecutablePath": executable_path.replace("\\", "/").lstrip("/"),
            "PlistPath": plist_path.replace("\\", "/").lstrip("/"),
            "BundleIdentifier": bundle_info.get("CFBundleIdentifier"),
            "BundleVersion": bundle_info.get("CFBundleVersion"),
            "BundleLibraries": {
                bundle_identifier: bundle_version
                for bundle_identifier, bundle_version in bundle_info.get("OSBundleLibraries", {}).items() 
            }
        }

    def modify_kexts(self, plist_path, hardware_report, macos_version):
        try:
            bundle_info = self.utils.read_file(plist_path)

            if bundle_info.get("IOKitPersonalities").get("itlwm").get("WiFiConfig"):
                from Scripts import wifi_profile_extractor
                
                wifi_profiles = wifi_profile_extractor.WifiProfileExtractor().get_profiles()

                if wifi_profiles:
                    bundle_info["IOKitPersonalities"]["itlwm"]["WiFiConfig"] = {
                        "WiFi_{}".format(index): {
                            "password": profile[1],
                            "ssid": profile[0]
                        }
                        for index, profile in enumerate(wifi_profiles, start=1)
                    }
            elif bundle_info.get("IOKitPersonalities").get("VoodooTSCSync"):
                bundle_info["IOKitPersonalities"]["VoodooTSCSync"]["IOPropertyMatch"]["IOCPUNumber"] = 0 if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("21.0.0") else int(hardware_report["CPU"]["Core Count"]) - 1
            elif bundle_info.get("IOKitPersonalities").get("AmdTscSync"):
                bundle_info["IOKitPersonalities"]["AmdTscSync"]["IOPropertyMatch"]["IOCPUNumber"] = 0 if self.utils.parse_darwin_version(macos_version) >= self.utils.parse_darwin_version("21.0.0") else int(hardware_report["CPU"]["Core Count"]) - 1
            else:
                return
            
            self.utils.write_file(plist_path, bundle_info)
        except:
            return            
        
    def load_kexts(self, hardware_report, macos_version, kexts_directory):
        kernel_add = []
        unload_kext = []

        if self.kexts[kext_data.kext_index_by_name.get("IO80211ElCap")].checked:
            unload_kext.extend((
                "AirPortBrcm4331",
                "AppleAirPortBrcm43224"
            ))
        elif self.kexts[kext_data.kext_index_by_name.get("VoodooSMBus")].checked:
            unload_kext.append("VoodooPS2Mouse")
        elif self.kexts[kext_data.kext_index_by_name.get("VoodooRMI")].checked:
            if not self.kexts[kext_data.kext_index_by_name.get("VoodooI2C")].checked:
                unload_kext.append("RMII2C")
            else:
                unload_kext.extend((
                    "VoodooSMBus",
                    "RMISMBus",
                    "VoodooI2CHID"
                ))

        kext_paths = self.utils.find_matching_paths(kexts_directory, extension_filter=".kext")
        bundle_list = []

        for kext_path, type in kext_paths:
            bundle_info = self.process_kext(kexts_directory, kext_path)

            if bundle_info:
                self.modify_kexts(os.path.join(kexts_directory, kext_path, bundle_info.get("PlistPath")), hardware_report, macos_version)

                bundle_list.append(bundle_info)

        bundle_dict = {bundle["BundleIdentifier"]: bundle for bundle in bundle_list}

        sorted_bundles = []
        
        visited = set()
        seen_identifier = set()

        def visit(bundle):
            if os.path.splitext(os.path.basename(bundle.get("BundlePath")))[0] in unload_kext or (bundle.get("BundlePath"), bundle.get("BundleIdentifier")) in visited:
                return
                        
            bundle["MaxKernel"] = os_data.get_latest_darwin_version()
            bundle["MinKernel"] = os_data.get_lowest_darwin_version()

            kext_index = kext_data.kext_index_by_name.get(os.path.splitext(os.path.basename(bundle.get("BundlePath")))[0])

            if kext_index:
                bundle["MaxKernel"] = self.kexts[kext_index].max_darwin_version
                bundle["MinKernel"] = self.kexts[kext_index].min_darwin_version
            
            for dep_identifier in bundle.get("BundleLibraries"):
                if dep_identifier in bundle_dict:
                    visit(bundle_dict[dep_identifier])
                    
                    bundle["MaxKernel"] = bundle["MaxKernel"] if self.utils.parse_darwin_version(bundle["MaxKernel"]) < self.utils.parse_darwin_version(bundle_dict[dep_identifier].get("MaxKernel", "99.99.99")) else bundle_dict[dep_identifier]["MaxKernel"]
                    bundle["MinKernel"] = bundle["MinKernel"] if self.utils.parse_darwin_version(bundle["MinKernel"]) > self.utils.parse_darwin_version(bundle_dict[dep_identifier].get("MinKernel", "0.0.0")) else bundle_dict[dep_identifier]["MinKernel"]

            if os.path.splitext(os.path.basename(bundle.get("BundlePath")))[0] == "AirPortBrcm4360_Injector":
                bundle["MaxKernel"] = "19.99.99"
            elif os.path.splitext(os.path.basename(bundle.get("BundlePath")))[0] == "AirportItlwm":
                bundle["MaxKernel"] = macos_version[:2] + bundle["MaxKernel"][2:]
                bundle["MinKernel"] = macos_version[:2] + bundle["MinKernel"][2:]

            visited.add((bundle.get("BundlePath"), bundle.get("BundleIdentifier")))

            if bundle.get("BundleIdentifier") in seen_identifier:
                bundle["Enabled"] = False
            else:
                seen_identifier.add(bundle.get("BundleIdentifier"))

            sorted_bundles.append(bundle)

        for bundle in bundle_list:
            visit(bundle)

        latest_darwin_version = (os_data.get_latest_darwin_version(), os_data.get_latest_darwin_version(include_beta=False))
        lowest_darwin_version = os_data.get_lowest_darwin_version()

        for bundle in sorted_bundles:
            kernel_add.append({
                "Arch": "x86_64",
                "BundlePath": bundle.get("BundlePath"),
                "Comment": " | SimpleKaruzi",
                "Enabled": bundle.get("Enabled"),
                "ExecutablePath": bundle.get("ExecutablePath"),
                "MaxKernel": "" if bundle.get("MaxKernel") in latest_darwin_version else bundle.get("MaxKernel"),
                "MinKernel": "" if bundle.get("MinKernel") == lowest_darwin_version else bundle.get("MinKernel"),
                "PlistPath": bundle.get("PlistPath")
            })

        return kernel_add

    def uncheck_kext(self, index):
        kext = self.kexts[index]
        kext.checked = False

        for other_kext in self.kexts:
            if other_kext.name in kext.requires_kexts and not other_kext.required:
                other_kext.checked = False

    def verify_kext_compatibility(self, selected_kexts, target_darwin_version):
        incompatible_kexts = []
        try:
            incompatible_kexts = [
                (self.kexts[index].name, "Lilu" in self.kexts[index].requires_kexts)
                for index in selected_kexts
                if not self.utils.parse_darwin_version(self.kexts[index].min_darwin_version)
                <= self.utils.parse_darwin_version(target_darwin_version)
                <= self.utils.parse_darwin_version(self.kexts[index].max_darwin_version)
            ]
        except:
            incompatible_kexts = [
                (self.kexts[kext_data.kext_index_by_name.get(kext_name)].name, "Lilu" in self.kexts[kext_data.kext_index_by_name.get(kext_name)].requires_kexts)
                for kext_name in selected_kexts
                if not self.utils.parse_darwin_version(self.kexts[kext_data.kext_index_by_name.get(kext_name)].min_darwin_version)
                <= self.utils.parse_darwin_version(target_darwin_version)
                <= self.utils.parse_darwin_version(self.kexts[kext_data.kext_index_by_name.get(kext_name)].max_darwin_version)
            ]

        if not incompatible_kexts:
            return False
        
        hl_color = self._get_highlight_color()
        content = (
            "当前 macOS 版本 ({}) 的不兼容 Kext 列表：<br>"
            "<ul>"
        ).format(target_darwin_version)
        
        for index, (kext_name, is_lilu_dependent) in enumerate(incompatible_kexts):
            content += "<li><b>{}. {}</b>".format(index + 1, kext_name)
            if is_lilu_dependent:
                content += " - Lilu 插件"
            content += "</li>"
        
        content += (
            "</ul><br>"
            "<b>注意：</b><br>"
            "• 对于 Lilu 插件，使用 \"-lilubetaall\" 启动参数将强制加载它们。<br>"
            "• 强制加载不支持的 Kext 可能会导致系统不稳定。 <b><span style='color:{}'>请谨慎操作。</span></b><br><br>"
            "您要在不支持的 macOS 版本上强制加载{}吗？"
        ).format(hl_color, "这些 Kext" if len(incompatible_kexts) > 1 else "此 Kext")
        
        return show_confirmation("不兼容的 Kext", content, yes_text="是", no_text="否")

    def kext_configuration_menu(self, macos_version):
        content = (
            "为您的系统选择内核扩展 (Kexts)。<br>"
            "灰色项目不支持当前的 macOS 版本 ({})。<br><br>"
            "<b>注意：</b><br>"
            "• 当选中某个 Kext 的插件时，整个 Kext 将自动被选中。"
        ).format(macos_version)
        
        checklist_items = []
        
        for kext in self.kexts:
            is_supported = self.utils.parse_darwin_version(kext.min_darwin_version) <= self.utils.parse_darwin_version(macos_version) <= self.utils.parse_darwin_version(kext.max_darwin_version)
            
            display_text = "{} - {}".format(kext.name, kext.description)
            if not is_supported:
                display_text += " (不支持)"
            
            checklist_items.append({
                "label": display_text,
                "category": kext.category if kext.category else "未分类",
                "supported": is_supported
            })
        
        checked_indices = [i for i, kext in enumerate(self.kexts) if kext.checked]
        
        selected_indices = show_checklist_dialog("配置内核扩展", content, checklist_items, checked_indices)
        
        self.utils.log_message("[KEXT MAESTRO] 已选 Kext 索引: {}".format(selected_indices), level="INFO")
        if selected_indices is None:
            return

        newly_checked = [i for i in selected_indices if i not in checked_indices]
        
        allow_unsupported_kexts = self.verify_kext_compatibility(newly_checked, macos_version)
        
        for i, kext in enumerate(self.kexts):
            if i not in selected_indices and kext.checked and not kext.required:
                self.uncheck_kext(i)
        
        for i in selected_indices:
            self.check_kext(i, macos_version, allow_unsupported_kexts)