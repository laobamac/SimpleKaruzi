from Scripts import resource_fetcher
from Scripts import utils
import json

class Github:
    def __init__(self, utils_instance=None, resource_fetcher_instance=None):
        self.utils = utils_instance if utils_instance else utils.Utils()
        self.fetcher = resource_fetcher_instance if resource_fetcher_instance else resource_fetcher.ResourceFetcher()

    def get_commits(self, owner, repo, branch="main", per_page=1):
        """
        使用 GitHub API 获取提交信息
        API: GET /repos/{owner}/{repo}/commits
        """
        url = "https://api.github.com/repos/{}/{}/commits?sha={}&per_page={}".format(owner, repo, branch, per_page)
        
        response = self.fetcher.fetch_and_parse_content(url)

        if not response:
            raise ValueError("无法从 GitHub 获取提交信息。")

        try:
            # 兼容处理：fetcher 可能返回字符串或已经解析的 JSON 对象
            if isinstance(response, str):
                commits_data = json.loads(response)
            else:
                commits_data = response
            
            # API 返回提交列表
            if isinstance(commits_data, list) and len(commits_data) > 0:
                # 构造符合调用方预期的结构
                latest_commit = commits_data[0]
                return {
                    "currentCommit": {
                        "oid": latest_commit["sha"],
                        "message": latest_commit["commit"]["message"],
                        "date": latest_commit["commit"]["committer"]["date"]
                    },
                    "raw_data": commits_data
                }
            elif isinstance(commits_data, dict) and "message" in commits_data:
                # 处理 API 错误消息
                raise ValueError("GitHub API 错误: {}".format(commits_data["message"]))
                
        except Exception as e:
            raise ValueError("解析 GitHub 提交数据失败: {}".format(e))

        raise ValueError("在分支 {} 上找不到仓库 {} 的提交信息。".format(branch, repo))

    def get_latest_release(self, owner, repo):
        """
        使用 GitHub API 获取最新发布信息
        API: GET /repos/{owner}/{repo}/releases/latest
        """
        url = "https://api.github.com/repos/{}/{}/releases/latest".format(owner, repo)
        
        response = self.fetcher.fetch_and_parse_content(url)

        if not response:
            raise ValueError("无法从 GitHub 获取发布信息。")

        try:
            if isinstance(response, str):
                release_data = json.loads(response)
            else:
                release_data = response
            
            # 检查是否有 API 错误信息
            if "message" in release_data and "documentation_url" in release_data:
                raise ValueError("GitHub API 错误: {}".format(release_data["message"]))

        except json.JSONDecodeError:
             raise ValueError("无法解析来自 GitHub 的响应。")

        body = release_data.get("body", "")
        # 处理资产列表
        assets = self._process_api_assets(release_data.get("assets", []))

        return {
            "body": body,
            "assets": assets,
            "tag_name": release_data.get("tag_name", ""),
            "name": release_data.get("name", "")
        }

    def _process_api_assets(self, api_assets):
        """处理 API 返回的 assets 列表，应用过滤规则"""
        assets = []
        
        for asset in api_assets:
            download_url = asset.get("browser_download_url")
            file_name = asset.get("name")
            
            # 应用原有的过滤逻辑：
            # 排除文件名包含 DEBUG 但不包含 tlwm 的文件
            if not ("tlwm" in file_name or ("tlwm" not in file_name and "DEBUG" not in file_name.upper())):
                continue
            
            # GitHub API 的 assets 对象中通常不直接包含 SHA256
            # 这里设为 None，gathering_files.py 会处理这种情况（不校验或下载后计算）
            sha256 = None
            
            assets.append({
                "product_name": self.extract_asset_name(file_name),
                "id": asset.get("id"),
                "url": "https://gitapi.simplehac.top/" + download_url,
                "sha256": sha256
            })
            
        return assets

    def extract_asset_name(self, file_name):
        end_idx = len(file_name)
        if "-" in file_name:
            end_idx = min(file_name.index("-"), end_idx)
        if "_" in file_name:
            end_idx = min(file_name.index("_"), end_idx)
        if "." in file_name:
            end_idx = min(file_name.index("."), end_idx)
            if file_name[end_idx] == "." and file_name[end_idx - 1].isdigit():
                end_idx = end_idx - 1
        asset_name = file_name[:end_idx]

        if "Sniffer" in file_name:
            asset_name = file_name.split(".")[0]
        if asset_name == "IntelBluetooth":
            asset_name = "IntelBluetoothFirmware"
        if "unsupported" in file_name:
            asset_name += "-unsupported"
        elif "rtsx" in file_name:
            asset_name += "-rtsx"
        elif "itlwm" in file_name.lower():
            if "Sonoma14.4" in file_name:
                asset_name += "23.4"
            elif "Sonoma14.0" in file_name:
                asset_name += "23.0"
            elif "Ventura" in file_name:
                asset_name += "22"
            elif "Monterey" in file_name:
                asset_name += "21"
            elif "BigSur" in file_name:
                asset_name += "20"
            elif "Catalina" in file_name:
                asset_name += "19"
            elif "Mojave" in file_name:
                asset_name += "18"
            elif "HighSierra" in file_name:
                asset_name += "17"

        return asset_name