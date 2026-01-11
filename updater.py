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

CURRENT_VERSION = "1.0.0"
UPDATE_JSON_URL = "https://next.oclpapi.simplehac.cn/SKSP/update.json"

def version_compare(remote_ver, local_ver):
    """
    比较版本号
    返回 True 如果 remote > local
    """
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
        """获取当前运行的程序路径"""
        if self.is_frozen:
            return sys.executable
        return sys.argv[0]

    def create_checker_thread(self):
        """创建检查更新的线程"""
        return UpdateCheckerThread(self)

    def fetch_update_info(self):
        """获取并解析远程 update.json"""
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

    def perform_update_process(self, download_info):
        """
        主更新流程：下载 -> 解压 -> 生成脚本 -> 退出并替换
        """
        url = download_info.get("url")
        if not url:
            self.u.log_message("[更新] 错误：下载地址无效", level="ERROR")
            return

        temp_dir = os.path.join(tempfile.gettempdir(), "SimpleKaruzi_Update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        zip_path = os.path.join(temp_dir, "update_pkg.zip")
        
        dialog = show_update_dialog("正在更新", "正在连接服务器...")
        dialog.show()
        
        self.u.log_message(f"[更新] 开始下载: {url}", level="INFO")
        dialog.update_progress(10, "正在下载更新包...")
        
        if not self.fetcher.download_and_save_file(url, zip_path):
            dialog.close()
            self.u.log_message("[更新] 下载失败，请检查网络。", level="ERROR")
            show_info("更新失败", "下载失败，请检查网络连接。")
            return

        dialog.update_progress(50, "正在解压...")
        extract_dir = os.path.join(temp_dir, "extracted")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            dialog.close()
            self.u.log_message(f"[更新] 解压失败: {e}", level="ERROR")
            show_info("更新失败", f"解压失败: {e}")
            return
        
        new_app_path = self._find_new_executable(extract_dir)
        if not new_app_path:
            dialog.close()
            self.u.log_message("[更新] 错误：在更新包中未找到可执行文件。", level="ERROR")
            show_info("更新失败", "更新包内容异常：未找到可执行文件。")
            return

        dialog.update_progress(90, "准备重启安装...")
        self.u.log_message(f"[更新] 准备安装新版本: {new_app_path}", level="INFO")
        
        time.sleep(1)
        dialog.close()

        self._execute_replacement_script(new_app_path)

    def _find_new_executable(self, extract_dir):
        system = platform.system()
        target_name = "SimpleKaruzi.exe" if system == "Windows" else "SimpleKaruzi.app"
        
        for root, dirs, files in os.walk(extract_dir):
            if system == "Windows" and target_name in files:
                return os.path.join(root, target_name)
            if system == "Darwin" and target_name in dirs:
                return os.path.join(root, target_name)
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
        batch_content = f"""
@echo off
timeout /t 3 /nobreak > NUL
echo Updating SimpleKaruzi...
move /y "{new_exe}" "{self.app_path}"
if %errorlevel% neq 0 (
    echo Update failed.
    pause
    exit
)
start "" "{self.app_path}"
del "%~f0"
"""
        try:
            with open(script_path, "w", encoding="gbk") as f:
                f.write(batch_content)
            subprocess.Popen([script_path], shell=True)
            sys.exit(0)
        except Exception as e:
            self.u.log_message(f"[更新] 无法创建更新脚本: {e}", level="ERROR")

    def _macos_update_script(self, new_app):
        if not self.is_frozen:
            self.u.open_folder(os.path.dirname(new_app))
            return

        script_path = os.path.join(tempfile.gettempdir(), "sk_update.sh")
        current_app_bundle = self.app_path
        while "/Contents/MacOS" in current_app_bundle:
            current_app_bundle = os.path.dirname(current_app_bundle)
        if current_app_bundle.endswith("/Contents"):
            current_app_bundle = os.path.dirname(current_app_bundle)
            
        sh_content = f"""#!/bin/bash
sleep 2
rm -rf "{current_app_bundle}"
mv "{new_app}" "{current_app_bundle}"
xattr -cr "{current_app_bundle}"
open "{current_app_bundle}"
rm "$0"
"""
        try:
            with open(script_path, "w") as f:
                f.write(sh_content)
            os.chmod(script_path, 0o755)
            subprocess.Popen(["/bin/bash", script_path])
            sys.exit(0)
        except Exception as e:
            self.u.log_message(f"[更新] 无法创建更新脚本: {e}", level="ERROR")

    def run_update(self):
        """
        启动时自动检查更新的入口方法。
        修复了崩溃问题：将线程保存在 self.auto_check_thread 中。
        """
        if self.auto_check_thread is not None and self.auto_check_thread.isRunning():
            return

        self.auto_check_thread = self.create_checker_thread()
        
        # 连接信号
        self.auto_check_thread.update_available.connect(self._on_auto_update_available)
        self.auto_check_thread.check_failed.connect(self._on_auto_check_finished)
        self.auto_check_thread.no_update.connect(self._on_auto_check_finished)
        self.auto_check_thread.finished.connect(self._cleanup_auto_thread)
        
        self.auto_check_thread.start()

    def _on_auto_update_available(self, info):
        # 自动检查发现更新，弹出提示
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
            self.perform_update_process(info)

    def _on_auto_check_finished(self, msg=None):
        if msg:
            self.u.log_message(f"[自动更新] 检查结束: {msg}", level="INFO")

    def _cleanup_auto_thread(self):
        if self.auto_check_thread:
            self.auto_check_thread.deleteLater()
            self.auto_check_thread = None


class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(dict) # {version, url, notes, date}
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)

    def __init__(self, updater_instance):
        super().__init__()
        self.updater = updater_instance

    def run(self):
        try:
            data = self.updater.fetch_update_info()
            
            if not data:
                self.check_failed.emit("无法连接到服务器获取更新信息")
                return

            remote_version = data.get("version", "0.0.0")

            if version_compare(remote_version, CURRENT_VERSION):
                downloads = data.get("downloads", {})
                system = platform.system()
                
                target_url = None
                if system == "Windows":
                    target_url = downloads.get("win")
                elif system == "Darwin":
                    target_url = downloads.get("mac")
                
                if target_url:
                    self.update_available.emit({
                        "version": remote_version,
                        "url": target_url,
                        "date": data.get("date", "Unknown"),
                        "changelog": data.get("changelog", "无更新日志")
                    })
                else:
                    self.check_failed.emit(f"发现新版本 {remote_version}，但未找到适用于 {system} 的下载链接。")
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.check_failed.emit(str(e))