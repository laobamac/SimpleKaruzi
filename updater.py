import os
import tempfile
import shutil
import sys

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

from Scripts import resource_fetcher
from Scripts import github
from Scripts import run
from Scripts import utils
from Scripts import integrity_checker
from Scripts.custom_dialogs import show_update_dialog, show_info, show_confirmation

class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(dict)
    check_failed = pyqtSignal(str)
    no_update = pyqtSignal()
    
    def __init__(self, updater_instance):
        super().__init__()
        self.updater = updater_instance
    
    def run(self):
        try:
            # 1. 获取远程清单
            remote_manifest = self.updater.get_remote_manifest()
            if not remote_manifest:
                self.check_failed.emit("无法从 GitHub 获取更新信息。\n\n请检查您的网络连接，稍后再试。")
                return
            
            # 2. 生成本地清单
            local_manifest = self.updater.get_local_manifest()
            if not local_manifest:
                self.check_failed.emit("无法生成本地文件清单。\n\n请稍后再试。")
                return
            
            # 3. 比较差异
            files_to_update = self.updater.compare_manifests(local_manifest, remote_manifest)
            if not files_to_update:
                self.no_update.emit()
            else:
                self.update_available.emit(files_to_update)
        except Exception as e:
            self.check_failed.emit("检查更新时发生错误：\n\n{}".format(str(e)))

class Updater(QObject):
    def __init__(self, utils_instance=None, github_instance=None, resource_fetcher_instance=None, run_instance=None, integrity_checker_instance=None):
        super().__init__()
        self.utils = utils_instance if utils_instance else utils.Utils()
        self.github = github_instance if github_instance else github.Github(utils_instance=self.utils)
        self.fetcher = resource_fetcher_instance if resource_fetcher_instance else resource_fetcher.ResourceFetcher(utils_instance=self.utils)
        self.run = run_instance.run if run_instance else run.Run().run
        self.integrity_checker = integrity_checker_instance if integrity_checker_instance else integrity_checker.IntegrityChecker(utils_instance=self.utils)
        
        # SimpleKaruzi 仓库地址
        self.remote_manifest_url = "https://nightly.link/laobamac/SimpleKaruzi/workflows/generate-manifest/main/manifest.json.zip"
        self.download_repo_url = "https://github.com/laobamac/SimpleKaruzi/archive/refs/heads/main.zip"
        
        self.temporary_dir = tempfile.mkdtemp()
        self.root_dir = os.path.dirname(os.path.realpath(__file__))

    def get_remote_manifest(self, dialog=None):
        if dialog:
            dialog.update_progress(10, "正在获取远程清单...")
        
        try:
            temp_manifest_zip_path = os.path.join(self.temporary_dir, "remote_manifest.json.zip")
            success = self.fetcher.download_and_save_file(self.remote_manifest_url, temp_manifest_zip_path)
            
            if not success or not os.path.exists(temp_manifest_zip_path):
                return None

            self.utils.extract_zip_file(temp_manifest_zip_path, self.temporary_dir)
            
            remote_manifest_path = os.path.join(self.temporary_dir, "manifest.json")
            manifest_data = self.utils.read_file(remote_manifest_path)
            
            if dialog:
                dialog.update_progress(20, "清单下载成功")
            
            return manifest_data
        except Exception as e:
            self.utils.log_message("[更新程序] 获取远程清单错误: {}".format(str(e)), level="ERROR")
            return None
    
    def get_local_manifest(self, dialog=None):
        if dialog:
            dialog.update_progress(40, "正在生成本地清单...")
        
        try:
            manifest_data = self.integrity_checker.generate_folder_manifest(self.root_dir, save_manifest=False)
            
            if dialog:
                dialog.update_progress(50, "本地清单已生成")
            
            return manifest_data
        except Exception as e:
            self.utils.log_message("[更新程序] 生成本地清单错误: {}".format(str(e)), level="ERROR")
            return None
    
    def compare_manifests(self, local_manifest, remote_manifest):
        if not local_manifest or not remote_manifest:
            return None
        
        files_to_update = {
            "modified": [],
            "missing": [],
            "new": []
        }
        
        local_files = set(local_manifest.keys())
        remote_files = set(remote_manifest.keys())
        
        for file_path in local_files & remote_files:
            if local_manifest[file_path] != remote_manifest[file_path]:
                files_to_update["modified"].append(file_path)
        
        files_to_update["missing"] = list(remote_files - local_files)
        # files_to_update["new"] = list(local_files - remote_files) # 忽略本地新增的文件
        
        total_changes = len(files_to_update["modified"]) + len(files_to_update["missing"])
        
        return files_to_update if total_changes > 0 else None
    
    def download_update(self, dialog=None):
        if dialog:
            dialog.update_progress(60, "正在创建临时目录...")
        
        try:
            self.utils.create_folder(self.temporary_dir)
            
            if dialog:
                dialog.update_progress(65, "正在下载更新包...")
            
            file_path = os.path.join(self.temporary_dir, "update.zip")
            success = self.fetcher.download_and_save_file(self.download_repo_url, file_path)
            
            if not success or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return False
            
            if dialog:
                dialog.update_progress(75, "正在解压文件...")
            
            self.utils.extract_zip_file(file_path, self.temporary_dir)
            
            if dialog:
                dialog.update_progress(80, "文件解压成功")
            
            return True
        except Exception as e:
            self.utils.log_message("[更新程序] 下载/解压期间出错: {}".format(str(e)), level="ERROR")
            return False
    
    def update_files(self, files_to_update, dialog=None):
        if not files_to_update:
            return True
        
        try:
            target_dir = os.path.join(self.temporary_dir, "SimpleKaruzi-main")

            if not os.path.exists(target_dir):
                # 兼容旧名称
                fallback_dir = os.path.join(self.temporary_dir, "OpCore-Simplify-main")
                if os.path.exists(fallback_dir):
                    target_dir = fallback_dir
                else:
                    self.utils.log_message("[更新程序] 未找到目标目录: {}".format(target_dir), level="ERROR")
                    return False
            
            all_files = files_to_update["modified"] + files_to_update["missing"]
            total_files = len(all_files)
            
            if dialog:
                dialog.update_progress(85, "正在更新 {} 个文件...".format(total_files))
            
            updated_count = 0
            for index, relative_path in enumerate(all_files, start=1):
                source = os.path.join(target_dir, relative_path)
                
                if not os.path.exists(source):
                    self.utils.log_message("[更新程序] 未找到源文件: {}".format(source), level="ERROR")
                    continue
                
                destination = os.path.join(self.root_dir, relative_path)
                
                self.utils.create_folder(os.path.dirname(destination))
                
                self.utils.log_message("[更新程序] 正在更新 [{}/{}]: {}".format(index, total_files, os.path.basename(relative_path)), level="INFO")
                if dialog:
                    progress = 85 + int((index / total_files) * 10)
                    dialog.update_progress(progress, "正在更新 [{}/{}]: {}".format(index, total_files, os.path.basename(relative_path)))
                
                try:
                    shutil.move(source, destination)
                    updated_count += 1
                    
                    if ".command" in os.path.splitext(relative_path)[-1] and os.name != "nt":
                        self.run({
                            "args": ["chmod", "+x", destination]
                        })
                except Exception as e:
                    self.utils.log_message("[更新程序] 更新失败 {}: {}".format(relative_path, str(e)), level="ERROR")
            
            if dialog:
                dialog.update_progress(95, "成功更新 {}/{} 个文件".format(updated_count, total_files))
            
            if os.path.exists(self.temporary_dir):
                shutil.rmtree(self.temporary_dir)
            
            if dialog:
                dialog.update_progress(100, "更新完成！")
            
            return True
        except Exception as e:
            self.utils.log_message("[更新程序] 更新文件期间出错: {}".format(str(e)), level="ERROR")
            return False
    
    def perform_update_process(self, files_to_update):
        """执行实际的更新流程（下载、替换、重启），通常在主线程调用"""
        if not show_confirmation("有新版本可用！", "您想要现在更新吗？", yes_text="更新", no_text="稍后"):
            return False
        
        dialog = show_update_dialog("正在更新", "正在启动更新进程...")
        dialog.show()
        
        try:
            if not self.download_update(dialog):
                dialog.close()
                show_info("更新失败", "无法下载或解压更新包。\n\n请检查您的网络连接并重试。")
                return
            
            if not self.update_files(files_to_update, dialog):
                dialog.close()
                show_info("更新失败", "无法更新文件。\n\n请稍后再试。")
                return
            
            dialog.close()
            show_info("更新完成", "更新已成功完成！\n\n程序需要重启以应用更新。")
            
            os.execv(sys.executable, ["python3"] + sys.argv)
        except Exception as e:
            dialog.close()
            self.utils.log_message("[更新程序] 更新期间出错: {}".format(str(e)), level="ERROR")
            show_info("更新错误", "更新过程中发生错误：\n\n{}".format(str(e)))
        finally:
            if os.path.exists(self.temporary_dir):
                try:
                    shutil.rmtree(self.temporary_dir)
                except:
                    pass

    def create_checker_thread(self):
        """创建一个检查线程，但不启动它。供外部调用者连接信号。"""
        return UpdateCheckerThread(self)

    def run_update(self):
        """自动更新入口点（启动时调用）"""
        self.auto_checker_thread = self.create_checker_thread()
        
        def on_update_available(files_to_update):
            self.auto_checker_thread.quit()
            self.auto_checker_thread.wait()
            self.perform_update_process(files_to_update)
        
        def on_check_failed(error_message):
            self.auto_checker_thread.quit()
            self.auto_checker_thread.wait()
            self.utils.log_message(f"[更新程序] 自动检查失败: {error_message}", level="WARNING")
        
        def on_no_update():
            self.auto_checker_thread.quit()
            self.auto_checker_thread.wait()
            # 自动检查无更新，静默退出
        
        self.auto_checker_thread.update_available.connect(on_update_available)
        self.auto_checker_thread.check_failed.connect(on_check_failed)
        self.auto_checker_thread.no_update.connect(on_no_update)
        
        self.auto_checker_thread.start()