import os
import sys
import platform
from Scripts import utils


class Settings:
    def __init__(self, utils_instance=None):
        self.u = utils_instance if utils_instance else utils.Utils()
        self.defaults = {
            "build_output_directory": "",
            "include_beta_versions": False,
            "theme": "Auto", # 默认为跟随系统
            "auto_update_check": True,
            "enable_debug_logging": False,
            "window_geometry": None
        }

        self.settings_file = self._get_settings_file_path()
        self.settings = self.load_settings()

    def _get_settings_file_path(self):
        """
        获取设置文件的存储路径。
        - 开发环境：存放在项目根目录。
        - 打包环境：存放在系统的用户数据目录 (AppData / Application Support)，确保设置不丢失。
        """
        if getattr(sys, 'frozen', False):
            # === 打包环境 (PyInstaller) ===
            app_name = "SimpleKaruzi"
            
            if platform.system() == "Windows":
                base_dir = os.environ.get("APPDATA")
                if not base_dir:
                    base_dir = os.path.expanduser("~")
            elif platform.system() == "Darwin":
                base_dir = os.path.expanduser("~/Library/Application Support")
            else:
                # Linux / 其他
                base_dir = os.path.expanduser("~/.config")
            
            # 创建应用专属目录
            app_dir = os.path.join(base_dir, app_name)
            if not os.path.exists(app_dir):
                try:
                    os.makedirs(app_dir)
                except OSError:
                    app_dir = os.path.expanduser("~")
            
            return os.path.join(app_dir, "settings.json")
        else:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(script_dir, "settings.json")

    def load_settings(self):
        try:
            loaded_settings = self.u.read_file(self.settings_file)
            
            if loaded_settings is not None:
                final_settings = self.defaults.copy()
                final_settings.update(loaded_settings)
                return final_settings
        except Exception as e:
            print(f"Error loading settings: {e}")

        return self.defaults.copy()

    def save_settings(self):
        try:
            self.u.write_file(self.settings_file, self.settings)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, self.defaults.get(key, default))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def __getattr__(self, name):
        if name.startswith("get_"):
            key = name[4:]
            if key in self.defaults:
                return lambda: self.get(key)
        
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")