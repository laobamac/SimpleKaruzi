from Scripts.datasets import os_data
import random

class KextInfo:
    def __init__(self, name, description, category, required = False, min_darwin_version = (), max_darwin_version = (), requires_kexts = [], conflict_group_id = None, github_repo = {}, download_info = {}):
        self.name = name
        self.description = description
        self.category = category
        self.required = required
        self.min_darwin_version = min_darwin_version or os_data.get_lowest_darwin_version()
        self.max_darwin_version = max_darwin_version or os_data.get_latest_darwin_version()
        self.requires_kexts = requires_kexts
        self.conflict_group_id = conflict_group_id
        self.github_repo = github_repo
        self.download_info = download_info
        self.checked = required

kexts = [
    KextInfo(
        name = "Lilu", 
        description = "用于任意的内核扩展、库和程序修补",
        category = "Required",
        required = True,
        github_repo = {
            "owner": "acidanthera",
            "repo": "Lilu"
        }
    ),
    KextInfo(
        name = "VirtualSMC", 
        description = "内核中先进的Apple SMC模拟器",
        category = "Required",
        required = True,
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "SMCBatteryManager", 
        description = "管理、监控和报告电池状态",
        category = "VirtualSMC Plugins",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "SMCDellSensors", 
        description = "在戴尔计算机上启用风扇监控和控制",
        category = "VirtualSMC Plugins",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "SMCLightSensor", 
        description = "允许系统利用环境光传感器设备",
        category = "VirtualSMC Plugins",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "SMCProcessor", 
        description = "管理英特尔CPU温度传感器",
        category = "VirtualSMC Plugins",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "SMCRadeonSensors", 
        description = "为AMD GPU提供温度读数",
        category = "VirtualSMC Plugins",
        min_darwin_version = "18.0.0",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "ChefKissInc",
            "repo": "SMCRadeonSensors"
        },
        download_info = {
            "id": int("".join(random.choices('0123456789', k=9))), 
            "url": "https://nightly.link/ChefKissInc/SMCRadeonSensors/workflows/main/master/Artifacts.zip"
        }
    ),
    KextInfo(
        name = "SMCSuperIO", 
        description = "监控硬件传感器和控制风扇速度",
        category = "VirtualSMC Plugins",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "VirtualSMC"
        }
    ),
    KextInfo(
        name = "NootRX", 
        description = "支持rDNA 2独立显卡的补丁内核扩展",
        category = "Graphics",
        min_darwin_version = "20.5.0",
        requires_kexts = ["Lilu"],
        conflict_group_id = "GPU",
        github_repo = {
            "owner": "ChefKissInc",
            "repo": "NootRX"
        },
        download_info = {
            "id": int("".join(random.choices('0123456789', k=9))), 
            "url": "https://nightly.link/ChefKissInc/NootRX/workflows/main/master/Artifacts.zip"
        }
    ),
    KextInfo(
        name = "NootedRed", 
        description = "支持AMD Vega集成显卡的内核扩展",
        category = "Graphics",
        min_darwin_version = "19.0.0",
        requires_kexts = ["Lilu"],
        conflict_group_id = "GPU",
        github_repo = {
            "owner": "ChefKissInc",
            "repo": "NootedRed"
        },
        download_info = {
            "id": int("".join(random.choices('0123456789', k=9))), 
            "url": "https://nightly.link/ChefKissInc/NootedRed/workflows/main/master/Artifacts.zip"
        }
    ),
    KextInfo(
        name = "WhateverGreen", 
        description = "为GPU提供各种必要的预支持补丁",
        category = "Graphics",
        requires_kexts = ["Lilu"],
        conflict_group_id = "GPU",
        github_repo = {
            "owner": "acidanthera",
            "repo": "WhateverGreen"
        }
    ),
    KextInfo(
        name = "AppleALC", 
        description = "为非官方支持的编解码器提供原生macOS高清音频",
        category = "Audio",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "AppleALC"
        }
    ),
    KextInfo(
        name = "AirportBrcmFixup", 
        description = "为非原生博通Wi-Fi卡提供必要的补丁",
        category = "Wi-Fi",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "AirportBrcmFixup"
        }
    ),
    KextInfo(
        name = "AirportItlwm", 
        description = "英特尔Wi-Fi驱动程序，支持原生macOS Wi-Fi接口",
        category = "Wi-Fi",
        conflict_group_id = "IntelWiFi",
        github_repo = {
            "owner": "OpenIntelWireless",
            "repo": "itlwm"
        }
    ),
    KextInfo(
        name = "corecaptureElCap", 
        description = "启用旧的Qualcomm Atheros无线网卡",
        category = "Wi-Fi",
        min_darwin_version = "18.0.0",
        max_darwin_version = "24.99.99",
        requires_kexts = ["IO80211ElCap"],
        download_info = {
            "id": 348147192, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Wifi/corecaptureElCap-v1.0.2.zip"
        }
    ),
    KextInfo(
        name = "IO80211ElCap", 
        description = "启用旧的Qualcomm Atheros无线网卡",
        category = "Wi-Fi",
        min_darwin_version = "18.0.0",
        max_darwin_version = "24.99.99",
        requires_kexts = ["corecaptureElCap"],
        download_info = {
            "id": 128321732, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Wifi/IO80211ElCap-v2.0.1.zip"
        }
    ),
    KextInfo(
        name = "IO80211FamilyLegacy", 
        description = "启用旧的Apple无线适配器",
        category = "Wi-Fi",
        min_darwin_version = "23.0.0",
        requires_kexts = ["AMFIPass", "IOSkywalkFamily"],
        download_info = {
            "id": 817294638, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/main/payloads/Kexts/Wifi/IO80211FamilyLegacy-v1.0.0.zip"
        }
    ),
    KextInfo(
        name = "IOSkywalkFamily", 
        description = "启用旧的Apple无线适配器",
        category = "Wi-Fi",
        min_darwin_version = "23.0.0",
        requires_kexts = ["AMFIPass", "IO80211FamilyLegacy"],
        download_info = {
            "id": 926584761, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/main/payloads/Kexts/Wifi/IOSkywalkFamily-v1.2.0.zip"
        }
    ),
    KextInfo(
        name = "itlwm", 
        description = "英特尔Wi-Fi驱动程序，模拟为以太网并通过Heliport连接Wi-Fi",
        category = "Wi-Fi",
        conflict_group_id = "IntelWiFi",
        github_repo = {
            "owner": "OpenIntelWireless",
            "repo": "itlwm"
        }
    ),
    KextInfo(
        name = "Ath3kBT", 
        description = "上传固件以启用Atheros蓝牙支持",
        category = "Bluetooth",
        max_darwin_version = "20.99.99",
        requires_kexts = ["Ath3kBTInjector"],
        github_repo = {
            "owner": "zxystd",
            "repo": "AthBluetoothFirmware"
        }
    ),
    KextInfo(
        name = "Ath3kBTInjector", 
        description = "上传固件以启用Atheros蓝牙支持",
        category = "Bluetooth",
        max_darwin_version = "20.99.99",
        requires_kexts = ["Ath3kBT"],
        github_repo = {
            "owner": "zxystd",
            "repo": "AthBluetoothFirmware"
        }
    ),
    KextInfo(
        name = "BlueToolFixup", 
        description = "修补蓝牙堆栈以支持第三方网卡",
        category = "Bluetooth",
        min_darwin_version = "21.0.0",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrcmPatchRAM"
        }
    ),
    KextInfo(
        name = "BrcmBluetoothInjector", 
        description = "在旧版本上启用博通蓝牙开关",
        category = "Bluetooth",
        max_darwin_version = "20.99.99",
        requires_kexts = ["BrcmBluetoothInjector", "BrcmFirmwareData", "BrcmPatchRAM2", "BrcmPatchRAM3"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrcmPatchRAM"
        }
    ),
    KextInfo(
        name = "BrcmFirmwareData", 
        description = "为基于博通RAMUSB的设备应用PatchRAM更新",
        category = "Bluetooth",
        requires_kexts = ["BlueToolFixup", "BrcmBluetoothInjector", "BrcmPatchRAM2", "BrcmPatchRAM3"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrcmPatchRAM"
        }
    ),
    KextInfo(
        name = "BrcmPatchRAM2", 
        description = "为基于博通RAMUSB的设备应用PatchRAM更新",
        category = "Bluetooth",
        max_darwin_version = "18.99.99",
        requires_kexts = ["BlueToolFixup", "BrcmBluetoothInjector", "BrcmFirmwareData", "BrcmPatchRAM3"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrcmPatchRAM"
        }
    ),
    KextInfo(
        name = "BrcmPatchRAM3", 
        description = "为基于博通RAMUSB的设备应用PatchRAM更新",
        category = "Bluetooth",
        min_darwin_version = "19.0.0",
        requires_kexts = ["BlueToolFixup", "BrcmBluetoothInjector", "BrcmFirmwareData", "BrcmPatchRAM2"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrcmPatchRAM"
        }
    ),
    KextInfo(
        name = "IntelBluetoothFirmware", 
        description = "上传固件以启用英特尔蓝牙支持",
        category = "Bluetooth",
        requires_kexts = ["BlueToolFixup", "IntelBTPatcher", "IntelBluetoothInjector"],
        github_repo = {
            "owner": "lshbluesky",
            "repo": "IntelBluetoothFirmware"
        }
    ),
    KextInfo(
        name = "IntelBTPatcher", 
        description = "修复英特尔蓝牙错误以获得更好的连接性",
        category = "Bluetooth",
        requires_kexts = ["Lilu", "BlueToolFixup", "IntelBluetoothFirmware", "IntelBluetoothInjector"],
        github_repo = {
            "owner": "lshbluesky",
            "repo": "IntelBluetoothFirmware"
        }
    ),
    KextInfo(
        name = "IntelBluetoothInjector", 
        description = "在旧版本上启用英特尔蓝牙开关",
        category = "Bluetooth",
        max_darwin_version = "20.99.99",
        requires_kexts = ["BlueToolFixup", "IntelBluetoothFirmware", "IntelBTPatcher"],
        github_repo = {
            "owner": "lshbluesky",
            "repo": "IntelBluetoothFirmware"
        }
    ),
    KextInfo(
        name = "AppleIGB", 
        description = "为英特尔的IGB以太网控制器提供支持",
        category = "Ethernet",
        github_repo = {
            "owner": "donatengit",
            "repo": "AppleIGB"
        },
        download_info = {
            "id": 736194363, 
            "url": "https://github.com/lzhoang2801/lzhoang2801.github.io/raw/main/public/extra-files/AppleIGB-v5.11.4.zip"
        }
    ),
    KextInfo(
        name = "AppleIGC", 
        description = "为英特尔2.5G以太网(i225/i226)提供支持", 
        category = "Ethernet",
        github_repo = {
            "owner": "SongXiaoXi",
            "repo": "AppleIGC"
        }
    ),
    KextInfo(
        name = "SimpleGBE", 
        description = "macOS的i210/211以太网驱动程序",
        category = "Ethernet",
        github_repo = {
            "owner": "laobamac",
            "repo": "SimpleGBE"
        }
    ),
    KextInfo(
        name = "AtherosE2200Ethernet", 
        description = "为Atheros E2200系列提供支持", 
        category = "Ethernet",
        github_repo = {
            "owner": "Mieze",
            "repo": "AtherosE2200Ethernet"
        }
    ),
    KextInfo(
        name = "CatalinaBCM5701Ethernet", 
        description = "为博通BCM57XX以太网系列提供支持",
        category = "Ethernet",
        min_darwin_version = "20.0.0",
        download_info = {
            "id": 821327912,
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Ethernet/CatalinaBCM5701Ethernet-v1.0.2.zip"
        }
    ),
    KextInfo(
        name = "HoRNDIS", 
        description = "使用安卓手机的USB网络共享模式访问互联网",
        category = "Ethernet",
        github_repo = {
            "owner": "TomHeaven",
            "repo": "HoRNDIS"
        },
        download_info = {
            "id": 79378595,
            "url": "https://github.com/TomHeaven/HoRNDIS/releases/download/rel9.3_2/Release.zip"
        }
    ),
    KextInfo(
        name = "IntelLucy",
        description = "为英特尔X500系列提供支持",
        category = "Ethernet",
        github_repo = {
            "owner": "Mieze",
            "repo": "IntelLucy"
        }
    ),
    KextInfo(
        name = "IntelMausiEthernet", 
        description = "macOS的英特尔以太网LAN驱动程序",
        category = "Ethernet",
        github_repo = {
            "owner": "CloverHackyColor",
            "repo": "IntelMausiEthernet"
        }
    ),
    KextInfo(
        name = "LucyRTL8125Ethernet", 
        description = "为Realtek RTL8125系列提供支持", 
        category = "Ethernet",
        github_repo = {
            "owner": "Mieze",
            "repo": "LucyRTL8125Ethernet"
        }
    ),
    KextInfo(
        name = "NullEthernet", 
        description = "当没有支持的网络硬件时创建一个空以太网", 
        category = "Ethernet",
        github_repo = {
            "owner": "RehabMan",
            "repo": "os-x-null-ethernet"
        },
        download_info = {
            "id": 182736492, 
            "url": "https://bitbucket.org/RehabMan/os-x-null-ethernet/downloads/RehabMan-NullEthernet-2016-1220.zip"
        }
    ),
    KextInfo(
        name = "RealtekRTL8100", 
        description = "为Realtek RTL8100系列提供支持", 
        category = "Ethernet",
        github_repo = {
            "owner": "Mieze",
            "repo": "RealtekRTL8100"
        },
        download_info = {
            "id": 10460478, 
            "url": "https://github.com/lzhoang2801/lzhoang2801.github.io/raw/main/public/extra-files/RealtekRTL8100-v2.0.1.zip"
        }
    ),
    KextInfo(
        name = "RealtekRTL8111", 
        description = "为Realtek RTL8111/8168系列提供支持", 
        category = "Ethernet",
        github_repo = {
            "owner": "Mieze",
            "repo": "RTL8111_driver_for_OS_X"
        },
        download_info = {
            "id": 130015132, 
            "url": "https://github.com/Mieze/RTL8111_driver_for_OS_X/releases/download/2.4.2/RealtekRTL8111-V2.4.2.zip"
        }
    ),
    KextInfo(
        name = "GenericUSBXHCI", 
        description = "修复一些基于AMD APU的系统上发现的USB 3.0问题",
        category = "USB",
        github_repo = {
            "owner": "RattletraPM",
            "repo": "GUX-RyzenXHCIFix"
        }
    ),
    KextInfo(
        name = "USBToolBox", 
        description = "灵活的USB映射",
        category = "USB",
        github_repo = {
            "owner": "USBToolBox",
            "repo": "kext"
        }
    ),
    KextInfo(
        name = "UTBDefault", 
        description = "启用所有USB端口（假设没有端口限制）",
        category = "USB",
        requires_kexts = ["USBToolBox"],
        github_repo = {
            "owner": "USBToolBox",
            "repo": "kext"
        }
    ),
    KextInfo(
        name = "XHCI-unsupported", 
        description = "为不支持的xHCI控制器启用USB 3.0支持",
        category = "USB",
        github_repo = {
            "owner": "daliansky",
            "repo": "OS-X-USB-Inject-All"
        },
        download_info = {
            "id": 185465401, 
            "url": "https://github.com/daliansky/OS-X-USB-Inject-All/releases/download/v0.8.0/XHCI-unsupported.kext.zip"
        }
    ),
    KextInfo(
        name = "AlpsHID", 
        description = "为Alps I2C触摸板带来原生多点触控支持",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "blankmac",
            "repo": "AlpsHID"
        }
    ),
    KextInfo(
        name = "VoodooInput", 
        description = "为任意输入源提供Magic Trackpad 2软件模拟",
        category = "Input",
        github_repo = {
            "owner": "acidanthera",
            "repo": "VoodooInput"
        }
    ),
    KextInfo(
        name = "VoodooPS2Controller", 
        description = "为PS/2键盘、触摸板和鼠标提供支持",
        category = "Input",
        github_repo = {
            "owner": "acidanthera",
            "repo": "VoodooPS2"
        }
    ),
    KextInfo(
        name = "VoodooRMI", 
        description = "通过SMBus/I2C的Synaptic触摸板内核扩展",
        category = "Input",
        github_repo = {
            "owner": "VoodooSMBus",
            "repo": "VoodooRMI"
        }
    ),
    KextInfo(
        name = "VoodooSMBus", 
        description = "i2c-i801 + ELAN SMBus触摸板内核扩展",
        category = "Input",
        min_darwin_version = "18.0.0",
        github_repo = {
            "owner": "VoodooSMBus",
            "repo": "VoodooSMBus"
        }
    ),
    KextInfo(
        name = "VoodooI2C", 
        description = "英特尔I2C控制器和从设备驱动程序",
        category = "Input",
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "VoodooI2CAtmelMXT", 
        description = "用于Atmel MXT I2C触摸屏的卫星内核扩展",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "VoodooI2CELAN", 
        description = "用于ELAN I2C触摸板的卫星内核扩展",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "VoodooI2CFTE", 
        description = "用于基于FTE的触摸板的卫星内核扩展",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "VoodooI2CHID", 
        description = "用于HID I2C或ELAN1200+输入设备的卫星内核扩展",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "VoodooI2CSynaptics", 
        description = "用于Synaptics I2C触摸板的卫星内核扩展",
        category = "Input",
        requires_kexts = ["VoodooI2C"],
        github_repo = {
            "owner": "VoodooI2C",
            "repo": "VoodooI2C"
        }
    ),
    KextInfo(
        name = "AsusSMC", 
        description = "在华硕笔记本电脑上支持环境光传感器、键盘背光和Fn键",
        category = "Brand Specific",
        max_darwin_version = "23.99.99",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "hieplpvip",
            "repo": "AsusSMC"
        }
    ),
    KextInfo(
        name = "BigSurface", 
        description = "一个完全集成的内核扩展，支持所有Surface相关硬件",
        category = "Brand Specific",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "Xiashangning",
            "repo": "BigSurface"
        }
    ),
    KextInfo(
        name = "YogaSMC", 
        description = "支持同步SMC键、控制传感器和管理特定厂商功能",
        category = "Brand Specific",
        requires_kexts = ["Lilu", "VirtualSMC"],
        github_repo = {
            "owner": "zhen-zen",
            "repo": "YogaSMC"
        }
    ),
    KextInfo(
        name = "CtlnaAHCIPort", 
        description = "改进对某些SATA控制器的支持", 
        category = "Storage",
        min_darwin_version = "20.0.0",
        conflict_group_id = "SATA",
        download_info = {
            "id": 927362352,
            "url": "https://raw.githubusercontent.com/lzhoang2801/lzhoang2801.github.io/refs/heads/main/public/extra-files/CtlnaAHCIPort-v3.4.1.zip",
            "sha256": "c8cf54f8b98995d076f365765025068e3d612f6337e279774203441c06f1a474"
        }
    ),
    KextInfo(
        name = "SATA-unsupported", 
        description = "改进对某些SATA控制器的支持", 
        category = "Storage",
        max_darwin_version = "19.99.99",
        conflict_group_id = "SATA",
        download_info = {
            "id": 239471623,
            "url": "https://raw.githubusercontent.com/lzhoang2801/lzhoang2801.github.io/refs/heads/main/public/extra-files/SATA-unsupported-v0.9.2.zip",
            "sha256": "942395056afa1e1d0e06fb501ab7c0130bf687d00e08b02c271844769056a57c"
        }
    ),
    KextInfo(
        name = "NVMeFix", 
        description = "解决NVMe SSD的兼容性和性能问题", 
        category = "Storage",
        min_darwin_version = "18.0.0",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "NVMeFix"
        }
    ),
    KextInfo(
        name = "RealtekCardReader", 
        description = "Realtek PCIe/USB SD卡读卡器驱动程序", 
        category = "Card Reader",
        min_darwin_version = "18.0.0",
        max_darwin_version = "23.99.99",
        requires_kexts = ["RealtekCardReaderFriend"],
        conflict_group_id = "RealtekCardReader",
        github_repo = {
            "owner": "0xFireWolf",
            "repo": "RealtekCardReader"
        }
    ),
    KextInfo(
        name = "RealtekCardReaderFriend", 
        description = "让系统信息识别你的Realtek读卡器",
        category = "Card Reader",
        min_darwin_version = "18.0.0",
        max_darwin_version = "22.99.99",
        requires_kexts = ["Lilu", "RealtekCardReader"],
        github_repo = {
            "owner": "0xFireWolf",
            "repo": "RealtekCardReaderFriend"
        }
    ), 
    KextInfo(
        name = "Sinetek-rtsx", 
        description = "Realtek PCIe SD卡读卡器驱动程序",
        category = "Card Reader",
        conflict_group_id = "RealtekCardReader",
        github_repo = {
            "owner": "cholonam",
            "repo": "Sinetek-rtsx"
        }
    ),
    KextInfo(
        name = "AmdTscSync", 
        description = "适用于AMD CPU的VoodooTSCSync修改版本",
        category = "TSC Synchronization",
        conflict_group_id = "TSC",
        github_repo = {
            "owner": "naveenkrdy",
            "repo": "AmdTscSync"
        }
    ),
    KextInfo(
        name = "VoodooTSCSync", 
        description = "同步英特尔CPU上TSC的内核扩展",
        category = "TSC Synchronization",
        conflict_group_id = "TSC",
        github_repo = {
            "owner": "RehabMan",
            "repo": "VoodooTSCSync"
        },
        download_info = {
            "id": 823728912, 
            "url": "https://github.com/lzhoang2801/lzhoang2801.github.io/raw/refs/heads/main/public/extra-files/VoodooTSCSync-v1.1.zip"
        }
    ),
    KextInfo(
        name = "CpuTscSync", 
        description = "用于TSC同步和禁用英特尔CPU上xcpm_urgency的Lilu插件",
        category = "TSC Synchronization",
        requires_kexts = ["Lilu"],
        conflict_group_id = "TSC",
        github_repo = {
            "owner": "acidanthera",
            "repo": "CpuTscSync"
        }
    ),
    KextInfo(
        name = "ForgedInvariant", 
        description = "用于在AMD和英特尔上同步TSC的即插即用内核扩展",
        category = "TSC Synchronization",
        requires_kexts = ["Lilu"],
        conflict_group_id = "TSC",
        github_repo = {
            "owner": "ChefKissInc",
            "repo": "ForgedInvariant"
        },
        download_info = {
            "id": int("".join(random.choices('0123456789', k=9))), 
            "url": "https://nightly.link/ChefKissInc/ForgedInvariant/workflows/main/master/Artifacts.zip"
        }
    ),
    KextInfo(
        name = "AMFIPass", 
        description = "amfi=0x80启动参数的替代方案",
        category = "Extras",
        min_darwin_version = "20.0.0",
        requires_kexts = ["Lilu"],
        download_info = {
            "id": 926491527, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/main/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip"
        }
    ),
    KextInfo(
        name = "ASPP-Override", 
        description = "为英特尔Sandy Bridge CPU重新启用CPU电源管理",
        category = "Extras",
        min_darwin_version = "21.4.0",
        download_info = {
            "id": 913826421,
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Misc/ASPP-Override-v1.0.1.zip"
        }
    ),
    KextInfo(
        name = "AppleIntelCPUPowerManagement", 
        description = "在旧版英特尔CPU上重新启用CPU电源管理", 
        category = "Extras",
        min_darwin_version = "22.0.0",
        download_info = {
            "id": 736296452, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Misc/AppleIntelCPUPowerManagement-v1.0.0.zip"
        }
    ),
    KextInfo(
        name = "AppleIntelCPUPowerManagementClient", 
        description = "在旧版英特尔CPU上重新启用CPU电源管理", 
        category = "Extras",
        min_darwin_version = "22.0.0",
        download_info = {
            "id": 932639706, 
            "url": "https://github.com/dortania/OpenCore-Legacy-Patcher/raw/refs/heads/main/payloads/Kexts/Misc/AppleIntelCPUPowerManagementClient-v1.0.0.zip"
        }
    ),
    KextInfo(
        name = "AppleMCEReporterDisabler", 
        description = "禁用AppleMCEReporter.kext以防止内核恐慌", 
        category = "Extras",
        download_info = {
            "id": 738162736, 
            "url": "https://github.com/acidanthera/bugtracker/files/3703498/AppleMCEReporterDisabler.kext.zip"
        }
    ),
    KextInfo(
        name = "BrightnessKeys", 
        description = "无需DSDT补丁的亮度按键处理程序",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "BrightnessKeys"
        }
    ),
    KextInfo(
        name = "CPUFriend", 
        description = "动态电源管理数据注入（需要CPUFriendDataProvider）",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "CPUFriend"
        }
    ),
    KextInfo(
        name = "CpuTopologyRebuild", 
        description = "优化英特尔Alder Lake及以上CPU的核心配置",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "b00t0x",
            "repo": "CpuTopologyRebuild"
        }
    ),
    KextInfo(
        name = "CryptexFixup", 
        description = "各种用于安装Rosetta cryptex的补丁",
        category = "Extras",
        min_darwin_version = "22.0.0",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "CryptexFixup"
        }
    ),
    KextInfo(
        name = "ECEnabler", 
        description = "允许读取长度超过1字节的嵌入式控制器字段",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "1Revenger1",
            "repo": "ECEnabler"
        }
    ),
    KextInfo(
        name = "FeatureUnlock", 
        description = "在不受支持的硬件上启用额外功能",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "FeatureUnlock"
        }
    ),
    KextInfo(
        name = "HibernationFixup", 
        description = "修复休眠兼容性问题",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "HibernationFixup"
        }
    ),
    KextInfo(
        name = "NoTouchID", 
        description = "避免带有Touch ID传感器的板ID在认证对话框中出现延迟",
        category = "Extras",
        min_darwin_version = "17.5.0",
        max_darwin_version = "19.6.0",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "al3xtjames",
            "repo": "NoTouchID"
        }
    ),
    KextInfo(
        name = "RestrictEvents", 
        description = "阻止不需要的进程并解锁功能",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "RestrictEvents"
        }
    ),
    KextInfo(
        name = "RTCMemoryFixup", 
        description = "模拟CMOS（RTC）内存中的一些偏移量",
        category = "Extras",
        requires_kexts = ["Lilu"],
        github_repo = {
            "owner": "acidanthera",
            "repo": "RTCMemoryFixup"
        }
    )
]

kext_index_by_name = {kext.name: index for index, kext in enumerate(kexts)}