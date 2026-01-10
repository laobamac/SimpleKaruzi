import os
import sys
import shutil
import zipfile
import subprocess
import platform
import tempfile
import time
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from Scripts import resource_fetcher
from Scripts import github
from Scripts import run
from Scripts import utils
from Scripts import integrity_checker
from Scripts.custom_dialogs import show_update_dialog, show_info, show_confirmation

# === 版本号定义 ===
CURRENT_VERSION = "1.0.0"
# =================

REPO_OWNER = "laobamac"
REPO_NAME = "SimpleKaruzi"

class UpdateCheckerThread(QThread):
    # 信号定义保持原样，兼容原有逻辑
    update_available = pyqtSignal(dict) # 传递文件差异字典
    check_failed = pyqtSignal(str)
    no_update = pyqtSignal()
    
    def __init__(self, updater_instance):
        super().__init__()
        self.updater = updater_instance
    
    def run(self):
        try:
            # === 使用原来的 manifest 方式检测 ===
            # 1. 获取远程清单
            remote_manifest = self.updater.get_remote_manifest()
            if not remote_manifest:
                self.check_failed.emit("无法从 GitHub 获取更新信息。\n\n请检查您的网络连接，稍后再试。")
                return
            
            # 2. 生成本地清单
            local_manifest = self.updater.get_local_manifest()
            if not local_manifest:
                self.check_failed.emit("无法生成本地文件清单。")
                return
            
            # 3. 比较差异
            files_to_update = self.updater.compare_manifests(local_manifest, remote_manifest)
            if not files_to_update:
                self.no_update.emit()
            else:
                # 只要有差异，就认为需要更新
                self.update_available.emit(files_to_update)
        except Exception as e:
            self.check_failed.emit("检查更新时发生错误：\n\n{}".format(str(e)))

class Updater(QObject):
    def __init__(self, utils_instance=None, github_instance=None, resource_fetcher_instance=None, run_instance=None, integrity_checker_instance=None):
        super().__init__()
        self.utils = utils_instance if utils_instance else utils.Utils()
        self.github = github_instance if github_instance else github.Github(utils_instance=self.utils)
        self.fetcher = resource_fetcher_instance if resource_fetcher_instance else resource_fetcher.ResourceFetcher(utils_instance=self.utils)
        self.run_inst = run_instance if run_instance else run.Run()
        self.integrity_checker = integrity_checker_instance if integrity_checker_instance else integrity_checker.IntegrityChecker(utils_instance=self.utils)
        
        # Manifest URL (保持原样)
        self.remote_manifest_url = "https://nightly.link/laobamac/SimpleKaruzi/workflows/generate-manifest/main/manifest.json.zip"
        
        self.temporary_dir = tempfile.mkdtemp()
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # 确定程序根目录
        if self.is_frozen:
            self.app_path = sys.executable
            self.root_dir = os.path.dirname(sys.executable)
        else:
            self.app_path = sys.argv[0]
            self.root_dir = os.path.dirname(os.path.realpath(__file__))

    # ================= 原有的 Manifest 检测逻辑 =================
    def get_remote_manifest(self, dialog=None):
        if dialog: dialog.update_progress(10, "正在获取远程清单...")
        try:
            temp_zip = os.path.join(self.temporary_dir, "remote_manifest.json.zip")
            if not self.fetcher.download_and_save_file(self.remote_manifest_url, temp_zip):
                return None
            self.utils.extract_zip_file(temp_zip, self.temporary_dir)
            manifest_path = os.path.join(self.temporary_dir, "manifest.json")
            return self.utils.read_file(manifest_path)
        except Exception as e:
            self.utils.log_message(f"[更新] 获取远程清单错误: {e}", level="ERROR")
            return None
    
    def get_local_manifest(self, dialog=None):
        if dialog: dialog.update_progress(40, "正在生成本地清单...")
        try:
            # 注意：如果是打包后的exe，生成清单可能会很慢或不准确，
            # 但既然您要求用原来的方法，我们继续沿用。
            return self.integrity_checker.generate_folder_manifest(self.root_dir, save_manifest=False)
        except Exception as e:
            self.utils.log_message(f"[更新] 生成本地清单错误: {e}", level="ERROR")
            return None
    
    def compare_manifests(self, local, remote):
        if not local or not remote: return None
        local_files = set(local.keys())
        remote_files = set(remote.keys())
        
        modified = [f for f in local_files & remote_files if local[f] != remote[f]]
        missing = list(remote_files - local_files)
        
        if len(modified) + len(missing) > 0:
            return {"modified": modified, "missing": missing}
        return None

    # ================= 新的更新执行逻辑 (Release ZIP 替换) =================
    
    def fetch_release_asset_url(self):
        """获取对应平台的 Release Asset 下载链接"""
        try:
            release = self.github.get_latest_release(REPO_OWNER, REPO_NAME)
            if not release: return None
            
            system = platform.system()
            os_keyword = "Win" if system == "Windows" else "macOS"
            ext = ".zip"
            
            for asset in release.get("assets", []):
                name = asset.get("name", "")
                # 匹配 SimpleKaruzi-Win.zip 或 SimpleKaruzi-macOS.zip
                if os_keyword in name and name.endswith(ext):
                    return asset.get("browser_download_url")
            return None
        except:
            return None

    def perform_update_process(self, _ignored_manifest_data=None):
        """
        覆盖原有逻辑：虽然是 Manifest 检测出的更新，但我们执行的是 Release 包下载替换
        """
        # 1. 获取下载链接
        self.utils.log_message("[更新] 正在查找适合当前系统的 Release 包...", level="INFO")
        download_url = self.fetch_release_asset_url()
        
        if not download_url:
            show_info("更新失败", "检测到文件变更，但在 GitHub Release 中未找到适合当前系统的安装包 (SimpleKaruzi-Win/macOS.zip)。")
            return

        # 2. 确认更新
        if not show_confirmation("有新版本可用", "检测到新版本，准备下载并自动安装。\n\n程序将在下载完成后自动重启。\n是否继续？", yes_text="立即更新", no_text="稍后"):
            return

        # 3. 准备下载
        dialog = show_update_dialog("正在更新", "正在连接服务器...")
        dialog.show()
        
        temp_dir = os.path.join(self.temporary_dir, "UpdatePkg")
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        self.utils.create_folder(temp_dir)
        
        zip_path = os.path.join(temp_dir, "update.zip")
        
        # 4. 下载
        dialog.update_progress(10, "正在下载更新包...")
        if not self.fetcher.download_and_save_file(download_url, zip_path):
            dialog.close()
            show_info("下载失败", "无法下载更新包，请检查网络。")
            return

        # 5. 解压
        dialog.update_progress(50, "正在解压...")
        try:
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
        except Exception as e:
            dialog.close()
            show_info("解压失败", f"错误: {e}")
            return

        # 6. 查找新文件
        new_app_path = self._find_new_executable(extract_dir)
        if not new_app_path:
            dialog.close()
            show_info("更新错误", "下载的包中未找到可执行文件。")
            return

        dialog.update_progress(90, "准备重启安装...")
        time.sleep(1)
        dialog.close()
        
        # 7. 执行替换脚本
        self._execute_replacement_script(new_app_path)

    def _find_new_executable(self, extract_dir):
        system = platform.system()
        target = "SimpleKaruzi.exe" if system == "Windows" else "SimpleKaruzi.app"
        for root, dirs, files in os.walk(extract_dir):
            if system == "Windows" and target in files:
                return os.path.join(root, target)
            if system == "Darwin" and target in dirs:
                return os.path.join(root, target)
        return None

    def _execute_replacement_script(self, new_file):
        if platform.system() == "Windows":
            self._win_script(new_file)
        elif platform.system() == "Darwin":
            self._mac_script(new_file)

    def _win_script(self, new_exe):
        if not self.is_frozen:
            self.utils.open_folder(os.path.dirname(new_exe))
            return
        
        bat_path = os.path.join(os.path.dirname(self.app_path), "updater.bat")
        content = f"""
@echo off
timeout /t 3 /nobreak > NUL
echo Updating...
move /y "{new_exe}" "{self.app_path}"
start "" "{self.app_path}"
del "%~f0"
"""
        try:
            with open(bat_path, "w", encoding="gbk") as f: f.write(content)
            subprocess.Popen([bat_path], shell=True)
            sys.exit(0)
        except Exception as e:
            self.utils.log_message(f"Script error: {e}", level="ERROR")

    def _mac_script(self, new_app):
        if not self.is_frozen:
            self.utils.open_folder(os.path.dirname(new_app))
            return

        sh_path = os.path.join(tempfile.gettempdir(), "sk_update.sh")
        # 回溯 .app 路径
        app_bundle = self.app_path
        while "/Contents/MacOS" in app_bundle:
            app_bundle = os.path.dirname(app_bundle)
        if app_bundle.endswith("/Contents"):
            app_bundle = os.path.dirname(app_bundle)

        content = f"""#!/bin/bash
sleep 2
rm -rf "{app_bundle}"
mv "{new_app}" "{app_bundle}"
xattr -cr "{app_bundle}"
open "{app_bundle}"
rm "$0"
"""
        try:
            with open(sh_path, "w") as f: f.write(content)
            os.chmod(sh_path, 0o755)
            subprocess.Popen(["/bin/bash", sh_path])
            sys.exit(0)
        except Exception as e:
            self.utils.log_message(f"Script error: {e}", level="ERROR")

    def create_checker_thread(self):
        return UpdateCheckerThread(self)