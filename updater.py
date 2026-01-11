import os
import sys
import shutil
import zipfile
import subprocess
import platform
import tempfile
import time
import json
import urllib.request
import ssl
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from Scripts.custom_dialogs import show_update_dialog, show_info, show_confirmation

CURRENT_VERSION = "1.0.1"
UPDATE_JSON_URL = "https://next.oclpapi.simplehac.cn/SKSP/update.json"

def version_compare(remote_ver, local_ver):
    try:
        v1 = [int(x) for x in remote_ver.strip().lstrip("v").split(".")]
        v2 = [int(x) for x in local_ver.strip().lstrip("v").split(".")]
        return v1 > v2
    except:
        return remote_ver > local_ver

class Updater(QObject):
    def __init__(self, utils_instance, github_instance, resource_fetcher_instance, run_instance=None, integrity_checker_instance=None):
        super().__init__()
        self.u = utils_instance
        self.github = github_instance
        self.fetcher = resource_fetcher_instance
        
        self.is_frozen = getattr(sys, 'frozen', False)
        self.app_path = self._get_app_path()
        
        self.auto_check_thread = None

    def _get_app_path(self):
        if self.is_frozen:
            return sys.executable
        return sys.argv[0]

    def create_checker_thread(self):
        return UpdateCheckerThread(self)

    def fetch_update_info(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(UPDATE_JSON_URL, headers={'User-Agent': 'SimpleKaruzi-Updater'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except Exception as e:
            self.u.log_message(f"[更新] 获取更新信息失败: {e}", level="ERROR")
            return None

    def _fix_permissions(self, path):
        if platform.system() == "Darwin" or platform.system() == "Linux":
            try:
                subprocess.run(['chmod', '-R', '755', path], check=False)
            except Exception as e:
                pass

    def perform_update_process(self, download_info, progress_callback=None, cancel_callback=None):
        def report(percent, message):
            if progress_callback:
                progress_callback(percent, message)
            if percent % 10 == 0:
                self.u.log_message(f"[更新] {message}", level="INFO")

        url = download_info.get("url")
        if not url:
            raise Exception("下载地址无效")

        temp_dir = os.path.join(tempfile.gettempdir(), "SimpleKaruzi_Update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        zip_path = os.path.join(temp_dir, "update_pkg.zip")
        
        # 1. 下载
        report(0, "准备下载...")
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={'User-Agent': 'SimpleKaruzi-Updater'})
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded_size = 0
                chunk_size = 8192 * 4
                start_time = time.time()
                
                with open(zip_path, 'wb') as out_file:
                    while True:
                        if cancel_callback and cancel_callback():
                            raise Exception("用户取消")

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        percent = int(downloaded_size * 100 / total_size) if total_size > 0 else 0
                        elapsed = time.time() - start_time
                        speed = downloaded_size / (elapsed if elapsed > 0 else 1) / 1024 / 1024
                        
                        report(percent, f"下载中... {speed:.2f} MB/s")
        except Exception as e:
            raise e

        # 2. 解压
        if cancel_callback and cancel_callback():
            raise Exception("用户取消")
            
        report(95, "正在解压...")
        extract_dir = os.path.join(temp_dir, "extracted")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            raise Exception(f"解压失败: {e}")
        
        # 3. 查找文件
        new_app_path = self._find_new_executable(extract_dir)
        if not new_app_path:
            raise Exception("未找到 SimpleKaruzi.app 或 .exe")

        self._fix_permissions(new_app_path)
        report(100, "准备就绪")
        
        return new_app_path

    def finalize_update(self, new_app_path):
        self.u.log_message(f"[更新] 正在执行最终替换流程: {new_app_path}", level="INFO")
        self._execute_replacement_script(new_app_path)

    def _find_new_executable(self, extract_dir):
        system = platform.system()
        target_name_lower = "simplekaruzi.exe" if system == "Windows" else "simplekaruzi.app"
        
        for root, dirs, files in os.walk(extract_dir):
            if "__MACOSX" in root: continue
            if system == "Windows":
                for f in files:
                    if f.lower() == target_name_lower: return os.path.join(root, f)
            elif system == "Darwin":
                for d in dirs:
                    if d.lower() == target_name_lower: return os.path.join(root, d)
        return None

    def _execute_replacement_script(self, new_file_path):
        current_platform = platform.system()
        if current_platform == "Windows":
            self._windows_update_script(new_file_path)
        elif current_platform == "Darwin":
            self._macos_update_script(new_file_path)

    def _windows_update_script(self, new_exe):
        if not self.is_frozen:
            self.u.open_folder(os.path.dirname(new_exe))
            return
        script_path = os.path.join(os.path.dirname(self.app_path), "updater.bat")
        batch_content = f"""@echo off
timeout /t 3 /nobreak > NUL
echo Updating SimpleKaruzi...
copy /y "{new_exe}" "{self.app_path}"
start "" "{self.app_path}"
del "%~f0"
"""
        with open(script_path, "w", encoding="gbk") as f: f.write(batch_content)
        subprocess.Popen([script_path], shell=True)
        os._exit(0)

    def _macos_update_script(self, new_app):
        if not self.is_frozen:
            self.u.open_folder(os.path.dirname(new_app))
            return
        
        script_path = os.path.join(tempfile.gettempdir(), "sk_update.sh")
        current_app_bundle = self.app_path
        
        while len(current_app_bundle) > 1 and not current_app_bundle.endswith(".app"):
            current_app_bundle = os.path.dirname(current_app_bundle)
            
        # [修复重点] 获取当前 GUI 用户，确保以用户身份运行 open，而不是 Root
        sh_content = f"""#!/bin/bash
# 等待主程序退出
sleep 2

# 替换文件
rm -rf "{current_app_bundle}"
mv "{new_app}" "{current_app_bundle}"

# 修复权限和隔离属性
chmod -R 755 "{current_app_bundle}"
xattr -cr "{current_app_bundle}"

# 获取当前登录的 GUI 用户名 (Console Owner)
REAL_USER=$(stat -f%Su /dev/console)

# 稍微等待文件系统刷新
sleep 1

# 以当前用户身份打开新 App
sudo -u "$REAL_USER" open "{current_app_bundle}"

# 删除脚本自身
rm "$0"
"""
        try:
            with open(script_path, "w") as f: f.write(sh_content)
            os.chmod(script_path, 0o755)
            
            # 后台运行，避免阻塞主程序退出
            apple_script = f'do shell script "bash \\"{script_path}\\" &> /dev/null &" with administrator privileges'
            
            subprocess.Popen(
                ['osascript', '-e', apple_script], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(0.5)
            os._exit(0)
        except Exception as e:
            self.u.log_message(f"[更新] 启动脚本失败: {e}", level="ERROR")

    def run_update(self):
        if self.auto_check_thread is not None and self.auto_check_thread.isRunning(): return
        self.auto_check_thread = self.create_checker_thread()
        self.auto_check_thread.update_available.connect(self._on_auto_update_available)
        self.auto_check_thread.check_failed.connect(lambda e: self._cleanup_auto_check())
        self.auto_check_thread.no_update.connect(lambda: self._cleanup_auto_check())
        self.auto_check_thread.finished.connect(self._cleanup_auto_check)
        self.auto_check_thread.start()

    def _cleanup_auto_check(self):
        if self.auto_check_thread:
            self.auto_check_thread.deleteLater()
            self.auto_check_thread = None

    def _on_auto_update_available(self, info):
        msg = f"发现新版本 v{info['version']}。\n请前往【设置 -> 软件更新】进行下载。"
        if show_confirmation("发现更新", msg, yes_text="知道了", no_text="关闭"): pass

class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(dict)
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)

    def __init__(self, updater_instance):
        super().__init__()
        self.updater = updater_instance

    def run(self):
        try:
            data = self.updater.fetch_update_info()
            if not data:
                self.check_failed.emit("无法连接到服务器")
                return
            remote_version = data.get("version", "0.0.0")
            if version_compare(remote_version, CURRENT_VERSION):
                downloads = data.get("downloads", {})
                sys_key = "win" if platform.system() == "Windows" else "mac"
                url = downloads.get(sys_key)
                if url:
                    self.update_available.emit({
                        "version": remote_version,
                        "url": url,
                        "date": data.get("date", "未知"),
                        "changelog": data.get("changelog", "无日志")
                    })
                else:
                    self.check_failed.emit("未找到当前系统的下载链接")
            else:
                self.no_update.emit()
        except Exception as e:
            self.check_failed.emit(str(e))