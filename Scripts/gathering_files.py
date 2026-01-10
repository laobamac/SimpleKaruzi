from Scripts.custom_dialogs import show_info, show_confirmation, show_download_dialog
from Scripts import github
from Scripts import kext_maestro
from Scripts import integrity_checker
from Scripts import resource_fetcher
from Scripts import utils
import os
import shutil
import subprocess
import platform
import sys
import json
import time
import urllib.request

os_name = platform.system()

class gatheringFiles:
    def __init__(self, utils_instance=None, github_instance=None, kext_maestro_instance=None, integrity_checker_instance=None, resource_fetcher_instance=None):
        self.utils = utils_instance if utils_instance else utils.Utils()
        self.github = github_instance if github_instance else github.Github()
        self.kext = kext_maestro_instance if kext_maestro_instance else kext_maestro.KextMaestro()
        self.fetcher = resource_fetcher_instance if resource_fetcher_instance else resource_fetcher.ResourceFetcher()
        self.integrity_checker = integrity_checker_instance if integrity_checker_instance else integrity_checker.IntegrityChecker()
        
        self.dortania_builds_url = "https://gitapi.simplehac.top/https://raw.githubusercontent.com/dortania/build-repo/builds/latest.json"
        self.ocbinarydata_url = "https://gitapi.simplehac.top/https://github.com/acidanthera/OcBinaryData/archive/refs/heads/master.zip"
        self.sksp_manifest_url = "https://next.oclpapi.simplehac.cn/SKSP/manifest.json"
        
        self.amd_vanilla_patches_url = "https://gitapi.simplehac.top/https://raw.githubusercontent.com/AMD-OSX/AMD_Vanilla/beta/patches.plist"
        self.aquantia_macos_patches_url = "https://gitapi.simplehac.top/https://raw.githubusercontent.com/CaseySJ/Aquantia-macOS-Patches/refs/heads/main/CaseySJ-Aquantia-Patch-Sets-1-and-2.plist"
        self.hyper_threading_patches_url = "https://gitapi.simplehac.top/https://github.com/b00t0x/CpuTopologyRebuild/raw/refs/heads/master/patches_ht.plist"
        
        self.temporary_dir = self.utils.get_temporary_dir()
        
        # === 持久化存储路径设置 ===
        if getattr(sys, 'frozen', False):
            # 打包环境：使用系统用户数据目录
            app_name = "SimpleKaruzi"
            if platform.system() == "Windows":
                base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            elif platform.system() == "Darwin":
                base_dir = os.path.expanduser("~/Library/Application Support")
            else:
                base_dir = os.path.expanduser("~/.config")
            
            self.ock_files_dir = os.path.join(base_dir, app_name, "OCK_Files")
        else:
            # 开发环境：保持在项目目录
            self.ock_files_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "OCK_Files")
        # =======================
        
        self.download_history_file = os.path.join(self.ock_files_dir, "history.json")
        self.sksp_manifest_file = os.path.join(self.ock_files_dir, "manifest.json")

    def get_product_index(self, product_list, product_name_name):
        for index, product in enumerate(product_list):
            if product_name_name == product.get("product_name"):
                return index
        return None
        
    def update_download_database(self, kexts, download_history):
        download_database = download_history.copy()
        dortania_builds_data = self.fetcher.fetch_and_parse_content(self.dortania_builds_url, "json")
        seen_repos = set()

        def add_product_to_download_database(products):
            if isinstance(products, dict):
                products = [products]

            for product in products:
                if not product or not product.get("product_name"):
                    continue

                product_index = self.get_product_index(download_database, product.get("product_name"))

                if product_index is None:
                    download_database.append(product)
                else:
                    download_database[product_index].update(product)

        for kext in kexts:
            if not kext.checked:
                continue

            if kext.download_info:
                if not kext.download_info.get("sha256"):
                    kext.download_info["sha256"] = None
                add_product_to_download_database({"product_name": kext.name, **kext.download_info})
            elif kext.github_repo and kext.github_repo.get("repo") not in seen_repos:
                name = kext.github_repo.get("repo")
                seen_repos.add(name)
                if name != "IntelBluetoothFirmware" and name in dortania_builds_data:
                    add_product_to_download_database({
                        "product_name": name,
                        "id": dortania_builds_data[name]["versions"][0]["release"]["id"], 
                        "url": dortania_builds_data[name]["versions"][0]["links"]["release"],
                        "sha256": dortania_builds_data[name]["versions"][0]["hashes"]["release"]["sha256"]
                    })
                else:
                    latest_release = self.github.get_latest_release(kext.github_repo.get("owner"), kext.github_repo.get("repo")) or {}
                    add_product_to_download_database(latest_release.get("assets"))

        add_product_to_download_database({
            "product_name": "OpenCorePkg",
            "id": dortania_builds_data["OpenCorePkg"]["versions"][0]["release"]["id"], 
            "url": dortania_builds_data["OpenCorePkg"]["versions"][0]["links"]["release"],
            "sha256": dortania_builds_data["OpenCorePkg"]["versions"][0]["hashes"]["release"]["sha256"]
        })

        return sorted(download_database, key=lambda x:x["product_name"])
    
    def move_bootloader_kexts_to_product_directory(self, product_name):
        if not os.path.exists(self.temporary_dir):
            self.utils.log_message("[收集文件] 目录 {} 不存在。".format(self.temporary_dir), level="ERROR", to_build_log=True)
            raise FileNotFoundError("目录 {} 不存在。".format(self.temporary_dir))
        
        temp_product_dir = os.path.join(self.temporary_dir, product_name)
        
        if not "OpenCore" in product_name:
            kext_paths = self.utils.find_matching_paths(temp_product_dir, extension_filter=".kext")
            for kext_path, type in kext_paths:
                source_kext_path = os.path.join(self.temporary_dir, product_name, kext_path)
                destination_kext_path = os.path.join(self.ock_files_dir, product_name, os.path.basename(kext_path))
                
                if "debug" in kext_path.lower() or "Contents" in kext_path or not self.kext.process_kext(temp_product_dir, kext_path):
                    continue
                
                shutil.move(source_kext_path, destination_kext_path)
        else:
            source_bootloader_path = os.path.join(self.temporary_dir, product_name, "X64", "EFI")
            if os.path.exists(source_bootloader_path):
                destination_efi_path = os.path.join(self.ock_files_dir, product_name, os.path.basename(source_bootloader_path))
                shutil.move(source_bootloader_path, destination_efi_path)
                source_config_path = os.path.join(os.path.dirname(os.path.dirname(source_bootloader_path)), "Docs", "Sample.plist")
                destination_config_path = os.path.join(destination_efi_path, "OC", "config.plist")
                shutil.move(source_config_path, destination_config_path)

            ocbinarydata_dir = os.path.join(self.temporary_dir, "OcBinaryData", "OcBinaryData-master")
            if os.path.exists(ocbinarydata_dir):
                background_picker_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "datasets", "background_picker.icns")
                product_dir = os.path.join(self.ock_files_dir, product_name)
                efi_dirs = self.utils.find_matching_paths(product_dir, name_filter="EFI", type_filter="dir")

                for efi_dir, _ in efi_dirs:
                    for dir_name in os.listdir(ocbinarydata_dir):
                        source_dir = os.path.join(ocbinarydata_dir, dir_name)
                        destination_dir = os.path.join(destination_efi_path, "OC", dir_name)
                        if os.path.isdir(destination_dir):
                            shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)

                    resources_image_dir = os.path.join(product_dir, efi_dir, "OC", "Resources", "Image")
                    picker_variants = self.utils.find_matching_paths(resources_image_dir, type_filter="dir")
                    for picker_variant, _ in picker_variants:
                        if ".icns" in ", ".join(os.listdir(os.path.join(resources_image_dir, picker_variant))):
                            shutil.copy(background_picker_path, os.path.join(resources_image_dir, picker_variant, "Background.icns"))

            macserial_paths = self.utils.find_matching_paths(temp_product_dir, name_filter="macserial", type_filter="file")
            if macserial_paths:
                for macserial_path, _ in macserial_paths:
                    source_macserial_path = os.path.join(self.temporary_dir, product_name, macserial_path)
                    destination_macserial_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename(macserial_path))
                    shutil.move(source_macserial_path, destination_macserial_path)
                    if os.name != "nt":
                        subprocess.run(["chmod", "+x", destination_macserial_path])
        
        return True
    
    def gather_bootloader_kexts(self, kexts, macos_version):
        self.utils.log_message("[收集文件] 请稍候，正在下载 OpenCorePkg、Kexts 和 macserial...", level="INFO", to_build_log=True)

        download_history = self.utils.read_file(self.download_history_file)
        if not isinstance(download_history, list):
            download_history = []

        download_database = self.update_download_database(kexts, download_history)
        
        self.utils.create_folder(self.temporary_dir)

        seen_download_urls = set()

        for product in kexts + [{"Name": "OpenCorePkg"}]:
            if not isinstance(product, dict) and not product.checked:
                continue

            product_name = product.name if not isinstance(product, dict) else product.get("Name")
            
            if product_name == "AirportItlwm":
                version = macos_version[:2]
                if all((kexts[kext_maestro.kext_data.kext_index_by_name.get("IOSkywalkFamily")].checked, kexts[kext_maestro.kext_data.kext_index_by_name.get("IO80211FamilyLegacy")].checked)) or self.utils.parse_darwin_version("24.0.0") <= self.utils.parse_darwin_version(macos_version):
                    version = "22"
                elif self.utils.parse_darwin_version("23.4.0") <= self.utils.parse_darwin_version(macos_version):
                    version = "23.4"
                elif self.utils.parse_darwin_version("23.0.0") <= self.utils.parse_darwin_version(macos_version):
                    version = "23.0"
                product_name += version
            elif "VoodooPS2" in product_name:
                product_name = "VoodooPS2"
            elif product_name == "BlueToolFixup" or product_name.startswith("Brcm"):
                product_name = "BrcmPatchRAM"
            elif product_name.startswith("Ath3kBT"):
                product_name = "Ath3kBT"
            elif product_name.startswith("IntelB"):
                product_name = "IntelBluetoothFirmware"
            elif product_name.startswith("VoodooI2C"):
                product_name = "VoodooI2C"
            elif product_name == "UTBDefault":
                product_name = "USBToolBox"

            product_download_index = self.get_product_index(download_database, product_name)
            if product_download_index is None:
                if hasattr(product, 'github_repo') and product.github_repo:
                    product_download_index = self.get_product_index(download_database, product.github_repo.get("repo"))
            
            if product_download_index is None:
                self.utils.log_message("[收集文件] 无法找到 {} 的下载链接。".format(product_name), level="WARNING", to_build_log=True)
                continue

            product_info = download_database[product_download_index]
            product_id = product_info.get("id")
            product_download_url = product_info.get("url")
            sha256_hash = product_info.get("sha256")

            if product_download_url in seen_download_urls:
                continue
            seen_download_urls.add(product_download_url)

            product_history_index = self.get_product_index(download_history, product_name)
            asset_dir = os.path.join(self.ock_files_dir, product_name)
            manifest_path = os.path.join(asset_dir, "manifest.json")

            if product_history_index is not None:
                history_item = download_history[product_history_index]
                is_latest_id = (product_id == history_item.get("id"))
                folder_is_valid, _ = self.integrity_checker.verify_folder_integrity(asset_dir, manifest_path)
                
                if is_latest_id and folder_is_valid:
                    self.utils.log_message("[收集文件] {} 的最新版本已下载。".format(product_name), level="INFO", to_build_log=True)
                    continue

            self.utils.log_message("[收集文件] 正在更新 {}...".format(product_name), level="INFO", to_build_log=True)
            if product_download_url:
                self.utils.log_message("[收集文件] 正在从 {} 下载".format(product_download_url), level="INFO", to_build_log=True)
            else:
                self.utils.log_message("[收集文件] 无法找到 {} 的下载链接。".format(product_name), level="ERROR", to_build_log=True)
                shutil.rmtree(self.temporary_dir, ignore_errors=True)
                return False

            zip_path = os.path.join(self.temporary_dir, product_name) + ".zip"
            if not self.fetcher.download_and_save_file(product_download_url, zip_path, sha256_hash):
                folder_is_valid, _ = self.integrity_checker.verify_folder_integrity(asset_dir, manifest_path)
                if product_history_index is not None and folder_is_valid:
                    self.utils.log_message("[收集文件] 使用之前下载的 {} 版本。".format(product_name), level="INFO", to_build_log=True)
                    continue
                else:
                    self.utils.log_message("[收集文件] 暂时无法下载 {}。请稍后再试。".format(product_name), level="ERROR", to_build_log=True)
                    raise Exception("暂时无法下载 {}。请稍后再试。".format(product_name))
            
            self.utils.extract_zip_file(zip_path)
            self.utils.create_folder(asset_dir, remove_content=True)
            
            while True:
                nested_zip_files = self.utils.find_matching_paths(os.path.join(self.temporary_dir, product_name), extension_filter=".zip")
                if not nested_zip_files:
                    break
                for zip_file, _ in nested_zip_files:
                    full_zip_path = os.path.join(self.temporary_dir, product_name, zip_file)
                    self.utils.extract_zip_file(full_zip_path)
                    os.remove(full_zip_path)

            if "OpenCore" in product_name:
                oc_binary_data_zip_path = os.path.join(self.temporary_dir, "OcBinaryData.zip")
                self.utils.log_message("[收集文件] 请稍候，正在下载 OcBinaryData...", level="INFO", to_build_log=True)
                self.utils.log_message("[收集文件] 正在从 {} 下载".format(self.ocbinarydata_url), level="INFO", to_build_log=True)
                self.fetcher.download_and_save_file(self.ocbinarydata_url, oc_binary_data_zip_path)

                if not os.path.exists(oc_binary_data_zip_path):
                    self.utils.log_message("[收集文件] 暂时无法下载 OcBinaryData。请稍后再试。", level="ERROR", to_build_log=True)
                    shutil.rmtree(self.temporary_dir, ignore_errors=True)
                    return False
                
                self.utils.extract_zip_file(oc_binary_data_zip_path)

            if self.move_bootloader_kexts_to_product_directory(product_name):
                self.integrity_checker.generate_folder_manifest(asset_dir, manifest_path)
                self._update_download_history(download_history, product_name, product_id, product_download_url, sha256_hash)

        shutil.rmtree(self.temporary_dir, ignore_errors=True)
        return True
    
    def get_kernel_patches(self, patches_name, patches_url):
        try:
            response = self.fetcher.fetch_and_parse_content(patches_url, "plist")

            return response["Kernel"]["Patch"]
        except:
            self.utils.log_message("[收集文件] 暂时无法下载 {}".format(patches_name), level="WARNING", to_build_log=True)
            show_info("下载失败", "暂时无法下载 {}。请稍后再试或手动应用。".format(patches_name))
            return []
        
    def _update_download_history(self, download_history, product_name, product_id, product_url, sha256_hash):
        product_history_index = self.get_product_index(download_history, product_name)
        
        entry = {
            "product_name": product_name, 
            "id": product_id,
            "url": product_url,
            "sha256": sha256_hash
        }

        if product_history_index is None:
            download_history.append(entry)
        else:
            download_history[product_history_index].update(entry)
        
        self.utils.create_folder(os.path.dirname(self.download_history_file))
        self.utils.write_file(self.download_history_file, download_history)
        
    def gather_hardware_sniffer(self):
        if os_name != "Windows":
            return

        self.utils.log_message("[收集文件] 正在获取 Hardware Sniffer...", level="INFO")

        PRODUCT_NAME = "Hardware-Sniffer-CLI.exe"
        REPO_OWNER = "lzhoang2801"
        REPO_NAME = "Hardware-Sniffer"

        destination_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), PRODUCT_NAME)
        
        latest_release = self.github.get_latest_release(REPO_OWNER, REPO_NAME) or {}
        
        product_id = None
        product_download_url = None
        sha256_hash = None

        asset_name = PRODUCT_NAME.split('.')[0]
        for asset in latest_release.get("assets", []):
            if asset.get("product_name") == asset_name:
                product_id = asset.get("id")
                product_download_url = asset.get("url")
                sha256_hash = asset.get("sha256")
                break

        if not all([product_id, product_download_url, sha256_hash]):
            show_info("未找到发布信息", "无法找到 {} 的发布信息。请稍后再试。".format(PRODUCT_NAME))
            raise Exception("无法找到 {} 的发布信息。".format(PRODUCT_NAME))

        download_history = self.utils.read_file(self.download_history_file)
        if not isinstance(download_history, list):
            download_history = []

        product_history_index = self.get_product_index(download_history, PRODUCT_NAME)
        
        if product_history_index is not None:
            history_item = download_history[product_history_index]
            is_latest_id = (product_id == history_item.get("id"))
            
            file_is_valid = False
            if os.path.exists(destination_path):
                local_hash = self.integrity_checker.get_sha256(destination_path)
                file_is_valid = (sha256_hash == local_hash)

            if is_latest_id and file_is_valid:
                self.utils.log_message("[收集文件] {} 的最新版本已下载。".format(PRODUCT_NAME), level="INFO")
                return destination_path

        self.utils.log_message("[收集文件] {} {}...".format("正在更新" if product_history_index is not None else "请稍候，正在下载", PRODUCT_NAME), level="INFO")
        
        if not self.fetcher.download_and_save_file(product_download_url, destination_path, sha256_hash):
            manual_download_url = "https://github.com/{}/{}/releases/latest".format(REPO_OWNER, REPO_NAME)
            show_info("下载失败", "请前往 {} 手动下载 {}。".format(manual_download_url, PRODUCT_NAME))
            raise Exception("下载 {} 失败。".format(PRODUCT_NAME))

        self._update_download_history(download_history, PRODUCT_NAME, product_id, product_download_url, sha256_hash)
        
        return destination_path

    # === SKSP 功能 ===
    def get_local_sksp_info(self):
        """获取本地 SKSP manifest 信息"""
        if os.path.exists(self.sksp_manifest_file):
            return self.utils.read_file(self.sksp_manifest_file)
        return None

    def fetch_remote_sksp_info(self):
        """获取远程 SKSP manifest 信息"""
        return self.fetcher.fetch_and_parse_content(self.sksp_manifest_url, "json")

    def check_sksp_status(self):
        """检查 SKSP 状态，返回 (是否存在, 本地版本)"""
        exists = os.path.isdir(self.ock_files_dir) and len(os.listdir(self.ock_files_dir)) > 0
        info = self.get_local_sksp_info()
        version = info.get("version") if info else "未知"
        return exists, version

    def download_and_install_sksp(self, dialog=None):
        """下载并安装 SKSP"""
        remote_info = self.fetch_remote_sksp_info()
        if not remote_info:
            return False, "无法获取远程 SKSP 信息"

        download_url = remote_info.get("download_url")
        sha256 = remote_info.get("sha256")
        
        if not download_url:
            return False, "Manifest 中缺少下载链接"

        # 准备下载
        self.utils.create_folder(self.temporary_dir)
        temp_zip = os.path.join(self.temporary_dir, "SKSP.zip")
        
        try:
            if dialog:
                dialog.update_progress(0, "正在连接...")
                
            response = urllib.request.urlopen(download_url)
            total_size = int(response.info().get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 8192
            start_time = time.time()
            
            with open(temp_zip, 'wb') as out_file:
                while True:
                    if dialog and dialog.is_canceled():
                        response.close()
                        os.remove(temp_zip)
                        return False, "用户取消"
                    
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    out_file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if dialog:
                        # 计算进度和速度
                        progress = int(downloaded_size * 100 / total_size) if total_size > 0 else 0
                        elapsed = time.time() - start_time
                        speed = downloaded_size / (elapsed if elapsed > 0 else 1) / 1024 / 1024 # MB/s
                        dialog.update_progress(progress, "正在下载... {:.2f} MB/s".format(speed))
            
            # 校验
            if dialog: dialog.update_progress(95, "正在校验...")
            if sha256:
                local_sha = self.integrity_checker.get_sha256(temp_zip)
                if local_sha != sha256:
                    return False, "文件校验失败"
            
            # 解压
            if dialog: dialog.update_progress(98, "正在解压...")
            self.utils.extract_zip_file(temp_zip, self.temporary_dir)
            
            # 覆盖 OCK_Files
            # 假设 zip 结构中有一个 OCK_Files 文件夹
            extracted_ock = os.path.join(self.temporary_dir, "OCK_Files")
            if os.path.exists(extracted_ock):
                if os.path.exists(self.ock_files_dir):
                    shutil.rmtree(self.ock_files_dir)
                shutil.move(extracted_ock, self.ock_files_dir)
                
                # 保存新的 manifest (如果 zip 包里没带)
                if not os.path.exists(self.sksp_manifest_file):
                    self.utils.write_file(self.sksp_manifest_file, remote_info)
            else:
                return False, "压缩包结构不正确（未找到 OCK_Files 目录）"
                
            return True, "安装成功"
            
        except Exception as e:
            return False, str(e)
        finally:
            if os.path.exists(self.temporary_dir):
                shutil.rmtree(self.temporary_dir, ignore_errors=True)

    def check_sksp_on_startup(self):
        """启动时检查逻辑"""
        exists, _ = self.check_sksp_status()
        if exists:
            return # 存在则跳过
            
        content = (
            "检测到 <b>OCK_Files</b> (资源文件) 缺失或为空。<br><br>"
            "虽然程序会自动拉取最新版本的引导和驱动文件，但建议事先下载 <b>SKSP (SimpleKaruzi Support PKG)</b> 来快速输出 EFI。<br>"
            "生成时会检查更新，不必担心过时问题。<br><br>"
            "是否立即下载 SKSP？"
        )
        
        while True:
            if show_confirmation("缺失支持资源包", content, yes_text="下载并安装", no_text="跳过"):
                dialog = show_download_dialog()
                success, msg = self.download_and_install_sksp(dialog)
                dialog.close()
                if success:
                    show_info("完成", "SKSP 安装成功！")
                    return
                elif msg == "用户取消":
                    continue
                else:
                    show_info("错误", "下载失败: {}".format(msg))
            else:
                if show_confirmation("确认跳过？", "没有本地资源包，生成 EFI 时将需要下载大量文件，速度可能较慢。\n\n确定要跳过吗？", yes_text="确定跳过", no_text="返回下载"):
                    break