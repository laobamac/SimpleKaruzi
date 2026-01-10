from Scripts import run
from Scripts import utils
from Scripts.custom_dialogs import ask_network_count, show_info, show_confirmation
import platform
import json

os_name = platform.system()

class WifiProfileExtractor:
    def __init__(self, run_instance=None, utils_instance=None):
        self.run = run_instance.run if run_instance else run.Run().run
        self.utils = utils_instance if utils_instance else utils.Utils()

    def get_authentication_type(self, authentication_type):
        authentication_type = authentication_type.lower()

        open_types = ("none", "owe", "open")
        for open_type in open_types:
            if open_type in authentication_type:
                return "open"

        if "wep" in authentication_type or "shared" in authentication_type:
            return "wep"
        
        if "wpa" in authentication_type or "sae" in authentication_type:
            return "wpa"
        
        return None

    def validate_wifi_password(self, authentication_type=None, password=None):
        if password is None:
            self.utils.log_message("[WiFi 配置文件提取器] 未找到密码", level="INFO")
            return None

        if authentication_type is None:
            self.utils.log_message("[WiFi 配置文件提取器] 未找到认证类型", level="INFO")
            return password

        self.utils.log_message("[WiFi 配置文件提取器] 正在验证 \"{}\" 的密码，认证类型为 {}".format(password, authentication_type), level="INFO")

        if authentication_type == "open":
            return ""

        try:
            password.encode('ascii')
        except UnicodeEncodeError:
            return None
            
        if 8 <= len(password) <= 63 and all(32 <= ord(c) <= 126 for c in password):
            return password
                
        return None

    def get_wifi_password_macos(self, ssid):
        output = self.run({
            "args": ["security", "find-generic-password", "-wa", ssid]
        })

        if output[-1] != 0:
            return None
                
        try:
            ssid_info = json.loads(output[0].strip())
            password = ssid_info.get("password")
        except:
            password = output[0].strip() if output[0].strip() else None
            
        return self.validate_wifi_password("wpa", password)
        
    def get_wifi_password_windows(self, ssid):
        output = self.run({
            "args": ["netsh", "wlan", "show", "profile", ssid, "key=clear"]
        })

        if output[-1] != 0:
            return None

        authentication_type = None
        password = None

        for line in output[0].splitlines():
            if authentication_type is None and "Authentication" in line:
                authentication_type = self.get_authentication_type(line.split(":")[1].strip())
            elif "Key Content" in line:
                password = line.split(":")[1].strip()

        return self.validate_wifi_password(authentication_type, password)

    def get_wifi_password_linux(self, ssid):
        output = self.run({
            "args": ["nmcli", "--show-secrets", "connection", "show", ssid]
        })

        if output[-1] != 0:
            return None
        
        authentication_type = None
        password = None

        for line in output[0].splitlines():
            if "802-11-wireless-security.key-mgmt:" in line:
                authentication_type = self.get_authentication_type(line.split(":")[1].strip())
            elif "802-11-wireless-security.psk:" in line:
                password = line.split(":")[1].strip()

        return self.validate_wifi_password(authentication_type, password)

    def ask_network_count(self, total_networks):
        if self.utils.gui_handler:
            result = ask_network_count(total_networks)
            if result == 'a':
                return total_networks
            return int(result)
        
        return 5
    
    def process_networks(self, ssid_list, max_networks, get_password_func):
        networks = []
        processed_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while len(networks) < max_networks and processed_count < len(ssid_list):
            ssid = ssid_list[processed_count]
            
            try:
                self.utils.log_message("[WiFi 配置文件提取器] 正在检索 \"{}\" 的密码 (第 {} 个，共 {})".format(ssid, processed_count + 1, len(ssid_list)), level="INFO", to_build_log=True)
                password = get_password_func(ssid)
                if password is not None:
                    if (ssid, password) not in networks:
                        consecutive_failures = 0
                        networks.append((ssid, password))
                        self.utils.log_message("[WiFi 配置文件提取器] 成功检索到 \"{}\" 的密码".format(ssid), level="INFO", to_build_log=True)
                        
                        if len(networks) == max_networks:
                            break
                else:
                    self.utils.log_message("[WiFi 配置文件提取器] 无法检索 \"{}\" 的密码".format(ssid), level="INFO", to_build_log=True)
                    consecutive_failures += 1 if os_name == "Darwin" else 0

                    if consecutive_failures >= max_consecutive_failures:
                        result = show_confirmation("WiFi 配置文件提取器", "无法检索密码。是否继续尝试？")
                        
                        if not result:
                            break

                        consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1 if os_name == "Darwin" else 0
                self.utils.log_message("[WiFi 配置文件提取器] 处理网络 \"{}\" 时出错: {}".format(ssid, str(e)), level="ERROR", to_build_log=True)

                if consecutive_failures >= max_consecutive_failures:
                    result = show_confirmation("WiFi 配置文件提取器", "无法检索密码。是否继续尝试？")
                        
                    if not result:
                        break

                    consecutive_failures = 0
            finally:
                processed_count += 1
            
            if processed_count >= max_networks and len(networks) < max_networks and processed_count < len(ssid_list):

                result = show_confirmation("WiFi 配置文件提取器", "仅检索到 {}/{} 个网络。是否尝试更多以达到目标数量？".format(len(networks), max_networks))
                        
                if not result:
                    break
        
        return networks

    def get_preferred_networks_macos(self, interface):
        output = self.run({
            "args": ["networksetup", "-listpreferredwirelessnetworks", interface]
        })

        if output[-1] != 0 or "Preferred networks on" not in output[0]:
            return []
        
        ssid_list = [network.strip() for network in output[0].splitlines()[1:] if network.strip()]
        
        if not ssid_list:
            return []
            
        max_networks = self.ask_network_count(len(ssid_list))
        
        if self.utils.gui_handler:
            content = (
                "为了从钥匙串中检索 WiFi 密码，macOS 将提示您<br>"
                "为每个 WiFi 网络输入管理员凭据。"
            )
            show_info("需要管理员验证", content)
        
        return self.process_networks(ssid_list, max_networks, self.get_wifi_password_macos)

    def get_preferred_networks_windows(self):
        output = self.run({
            "args": ["netsh", "wlan", "show", "profiles"]
        })

        if output[-1] != 0:
            return []
        
        ssid_list = []

        for line in output[0].splitlines():
            if "All User Profile" in line:
                try:
                    ssid = line.split(":")[1].strip()
                    if ssid:
                        ssid_list.append(ssid)
                except:
                    continue
        
        if not ssid_list:
            return []

        max_networks = len(ssid_list)
    
        self.utils.log_message("[WiFi 配置文件提取器] 正在检索 {} 个网络的密码".format(len(ssid_list)), level="INFO", to_build_log=True)
        
        return self.process_networks(ssid_list, max_networks, self.get_wifi_password_windows)

    def get_preferred_networks_linux(self):
        output = self.run({
            "args": ["nmcli", "-t", "-f", "NAME", "connection", "show"]
        })

        if output[-1] != 0:
            return []
        
        ssid_list = [network.strip() for network in output[0].splitlines() if network.strip()]
        
        if not ssid_list:
            return []
            
        max_networks = len(ssid_list)
    
        self.utils.log_message("[WiFi 配置文件提取器] 正在检索 {} 个网络的密码".format(len(ssid_list)), level="INFO", to_build_log=True)
        
        return self.process_networks(ssid_list, max_networks, self.get_wifi_password_linux)

    def get_wifi_interfaces(self):
        output = self.run({
            "args": ["networksetup", "-listallhardwareports"]
        })

        if output[-1] != 0:
            return []
        
        interfaces = []
        
        for interface_info in output[0].split("\n\n"):
            if "Device: en" in interface_info:
                try:
                    interface = "en{}".format(int(interface_info.split("Device: en")[1].split("\n")[0]))
                    
                    test_output = self.run({
                        "args": ["networksetup", "-listpreferredwirelessnetworks", interface]
                    })

                    if test_output[-1] == 0 and "Preferred networks on" in test_output[0]:
                        interfaces.append(interface)
                except:
                    continue

        return interfaces
    
    def get_profiles(self):
        content = (
            "<b>注意：</b><br>"
            "<ul>"
            "<li>当使用 itlwm kext 时，WiFi 在 macOS 中显示为以太网</li>"
            "<li>您需要 Heliport 应用程序来管理 macOS 中的 WiFi 连接</li>"
            "<li>此步骤将启用启动时自动连接 WiFi<br>"
            "对于通过恢复版 OS (Recovery OS) 安装 macOS 的用户非常有用</li>"
            "</ul><br>"
            "您想要扫描 WiFi 配置文件吗？"
        )
        if not show_confirmation("WiFi 配置文件提取器", content):
            return []
        
        profiles = []
        self.utils.log_message("[WiFi 配置文件提取器] 正在检测 WiFi 配置文件", level="INFO", to_build_log=True)
        
        if os_name == "Windows":
            profiles = self.get_preferred_networks_windows()
        elif os_name == "Linux":
            profiles = self.get_preferred_networks_linux()
        elif os_name == "Darwin":
            wifi_interfaces = self.get_wifi_interfaces()

            if wifi_interfaces:
                for interface in wifi_interfaces:
                    self.utils.log_message("[WiFi 配置文件提取器] 正在检查接口: {}".format(interface), level="INFO", to_build_log=True)
                    interface_profiles = self.get_preferred_networks_macos(interface)
                    if interface_profiles:
                        profiles = interface_profiles
                        break
            else:
                self.utils.log_message("[WiFi 配置文件提取器] 未检测到 WiFi 接口。", level="INFO", to_build_log=True)

        if not profiles:
            self.utils.log_message("[WiFi 配置文件提取器] 未找到带有保存密码的 WiFi 配置文件。", level="INFO", to_build_log=True)
        
        self.utils.log_message("[WiFi 配置文件提取器] 成功应用了 {} 个 WiFi 配置文件".format(len(profiles)), level="INFO", to_build_log=True)

        return profiles