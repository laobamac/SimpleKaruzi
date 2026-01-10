class PatchInfo:
    def __init__(self, name, description, function_name):
        self.name = name
        self.description = description
        self.function_name = function_name
        self.checked = False

patches = [
    PatchInfo(
        name = "ALS",
        description = "虚拟或启用环境光传感器设备，用于存储当前亮度/自动亮度级别",
        function_name = "ambient_light_sensor"
    ),
    PatchInfo(
        name = "APIC",
        description = "通过将第一个CPU条目指向HEDT系统上的活动CPU来避免内核恐慌",
        function_name = "fix_apic_processor_id"
    ),
    PatchInfo(
        name = "BATP",
        description = "在笔记本电脑上启用电池百分比显示",
        function_name = "battery_status_patch"
    ),
    PatchInfo(
        name = "BUS0",
        description = "添加系统管理总线设备以修复AppleSMBus问题",
        function_name = "add_system_management_bus_device"
    ),
    PatchInfo(
        name = "Disable Devices",
        description = "禁用不支持的PCI设备，例如GPU、Wi-Fi网卡和SD卡读卡器",
        function_name = "disable_unsupported_device"
    ),
    PatchInfo(
        name = "FakeEC",
        description = "操作系统感知的虚拟EC（由CorpNewt开发）",
        function_name = "fake_embedded_controller"
    ),
    PatchInfo(
        name = "RCSP",
        description = "移除有条件的ACPI作用域声明",
        function_name = "remove_conditional_scope"
    ),
    PatchInfo(
        name = "CMOS",
        description = "修复HP实时时钟电源丢失（005）开机错误",
        function_name = "fix_hp_005_post_error"
    ),
    PatchInfo(
        name = "FixHPET",
        description = "修补IRQ冲突（由CorpNewt开发）",
        function_name = "fix_irq_conflicts"
    ),
    PatchInfo(
        name = "GPI0",
        description = "启用GPIO设备以使I2C触摸板正常工作",
        function_name = "enable_gpio_device"
    ),
    PatchInfo(
        name = "IMEI",
        description = "创建虚拟IMEI设备以确保Intel集成显卡加速功能正常工作",
        function_name = "add_intel_management_engine"
    ),
    PatchInfo(
        name = "MCHC",
        description = "添加内存控制器集线器控制器设备以修复AppleSMBus",
        function_name = "add_memory_controller_device"
    ),
    PatchInfo(
        name = "PMC",
        description = "添加PMCR设备以在300系列主板上启用NVRAM支持",
        function_name = "enable_nvram_support"
    ),
    PatchInfo(
        name = "PM (Legacy)",
        description = "阻止CpuPm和Cpu0Ist ACPI表，以避免在Intel Ivy Bridge及更旧CPU上出现内核恐慌",
        function_name = "drop_cpu_tables"
    ),
    PatchInfo(
        name = "PLUG",
        description = "将CPU对象重新定义为处理器并设置plugin-type = 1（由CorpNewt开发）",
        function_name = "enable_cpu_power_management"
    ),
    PatchInfo(
        name = "PNLF",
        description = "定义PNLF设备以在笔记本电脑上启用背光控制",
        function_name = "enable_backlight_controls"
    ),
    PatchInfo(
        name = "RMNE",
        description = "创建空以太网设备以允许macOS系统访问iServices",
        function_name = "add_null_ethernet_device"
    ),
    PatchInfo(
        name = "RTC0",
        description = "创建新的RTC设备以解决HEDT系统上的PCI配置问题",
        function_name = "fix_system_clock_hedt"
    ),
    PatchInfo(
        name = "RTCAWAC",
        description = "上下文感知的AWAC禁用和RTC启用/虚拟/范围修复（由CorpNewt开发）",
        function_name = "fix_system_clock_awac"
    ),
    PatchInfo(
        name = "PRW",
        description = "修复_PRW方法中的睡眠状态值，以防止在macOS中立即唤醒",
        function_name = "instant_wake_fix"
    ),
    PatchInfo(
        name = "Surface Patch",
        description = "适用于所有Surface Pro / Book / Laptop硬件的特殊补丁",
        function_name = "surface_laptop_special_patch"
    ),
    PatchInfo(
        name = "UNC",
        description = "禁用未使用的非核心桥以防止HEDT系统上的内核恐慌",
        function_name = "fix_uncore_bridge"
    ),
    PatchInfo(
        name = "USB Reset",
        description = "禁用USB集线器设备以手动重建端口",
        function_name = "disable_usb_hub_devices"
    ),
    PatchInfo(
        name = "USBX",
        description = "创建USBX设备以注入USB电源属性",
        function_name = "add_usb_power_properties"
    ),
    PatchInfo(
        name = "WMIS",
        description = "某些型号忘记从ThermalZone返回结果",
        function_name = "return_thermal_zone"
    ),
    PatchInfo(
        name = "XOSI",
        description = "将操作系统伪装成Windows，以在macOS上启用被非Windows系统锁定的设备",
        function_name = "operating_system_patch"
    )
]