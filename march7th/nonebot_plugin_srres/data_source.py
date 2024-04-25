import json
import random
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict
import hashlib

import httpx
from nonebot.log import logger
from nonebot.compat import type_validate_python

from .config import plugin_config
from .model.characters import (
    CharacterIndex
)

plugin_data_dir = Path(__name__).parent.absolute() # NoneBot2 机器人根目录
data_path = plugin_data_dir / "data" / "nonebot_plugin_march7th" # NoneBot2 机器人插件数据目录
index_dir = data_path / "index"


ResFiles = {
    "files",
    "filesHash",
    "othername",
}

NicknameFile = "othername.json"
VersionFile = "filesHash.json"

class ResIndexType(TypedDict):
    characters: CharacterIndex


class StarRailRes:
    ResIndex: ResIndexType = {
        "characters": {}
    }
    Nickname: Dict[str, Any] = {}
    NicknameRev: Dict[str, Any] = {}

    def proxy_url(self, url: str) -> str:
        if plugin_config.github_proxy:
            github_proxy = plugin_config.github_proxy
            if github_proxy.endswith("/"):
                github_proxy = github_proxy[:-1]
            return f"{github_proxy}/{url}"
        return url

    async def download(self, url: str) -> Optional[bytes]:
        async with httpx.AsyncClient() as client:
            for i in range(3):
                try:
                    resp = await client.get(url, timeout=10)
                    if resp.status_code == 302:
                        url = resp.headers["location"]
                        continue
                    resp.raise_for_status()
                    return resp.content
                except Exception as e:
                    logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                    await asyncio.sleep(2)
            logger.error(f"Error downloading {url}, all attempts failed.")
            return None

    async def cache(self, file: str):
        status = True
        if not (data_path / file).exists():
            (data_path / file).parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Downloading {file}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_wiki_url}/{file}")
            )
            if not data:
                logger.error(f"Failed to download {file}.")
                status = False
            else:
                with open(data_path / file, "wb") as f:
                    f.write(data)
        return status
    
    async def img_cache(self, file: str, img_hash: str):
        status = True
        update = False
        if not (data_path / file).exists():
            (data_path / file).parent.mkdir(parents=True, exist_ok=True)
            update = True
        else:
            with open(data_path / file, 'rb') as f:
                    img_cachefile = f.read()
            img_cacheHash = hashlib.md5(img_cachefile).hexdigest()
            if not img_hash == img_cacheHash:
                update = True
        if update:
            logger.debug(f"Downloading {file}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_guide_url}/{file}")
            )
            if not data:
                logger.error(f"Failed to download {file}.")
                status = False
            else:
                with open(data_path / file, "wb") as f:
                    f.write(data)
        return status

    async def get_character_overview(self, name: str) -> Optional[Path]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            overview = self.ResIndex["characters"][id].path[1:]
            img_hash = self.ResIndex["characters"][id].hash
            if overview:
                # if isinstance(overview, list):
                #     overview = random.choice(overview)
                if await self.img_cache(overview, img_hash):
                    return data_path / overview
        return None

    def get_character_overview_url(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            overview = self.ResIndex["characters"][id].guide_overview
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    def get_data_folder(self) -> Path:
        return data_path

    def load_index_file(self, name: str, model=True) -> Dict[str, Any]:
        if name in ResFiles and (index_dir / f"{name}.json").exists():
            with open(index_dir / f"{name}.json", encoding="utf-8") as f:
                data = json.load(f)
            if not model:
                return data
            if name == 'files':
                return type_validate_python(ResIndexType.__annotations__['characters'], data['guide_overview'])
            else:
                return type_validate_python(ResIndexType.__annotations__[name], data)
        return {}

    def reload(self) -> None:
        for name in ResFiles:
            if name in {"files"}:
                self.ResIndex['characters'] = self.load_index_file(name)
                logger.debug(f'ResIndex:{self.ResIndex}')
                continue
            
        self.Nickname = self.load_index_file("othername", model=False)
        for type in {"characters"}:
            if type in self.Nickname.keys():
                for k, v in dict(self.Nickname[type]).items():
                    for v_item in list(v):
                        self.NicknameRev[v_item] = k

    async def update(self) -> bool:
        """
        更新索引文件
        """
        status: bool = True
        update_index: bool = False
        # 检查是否需要更新
        logger.debug(f"正在下载 {VersionFile}...")
        data = await self.download(
            self.proxy_url(f"{plugin_config.sr_wiki_url}/{VersionFile}")
        )
        if not data:
            logger.error(f"文件 {VersionFile} 下载失败")
            return False
        if not data_path.exists() or not (data_path / VersionFile).exists():
            data_path.mkdir(parents=True, exist_ok=True)
            # 版本文件不存在，更新索引
            update_index = True
        else:
            with open(data_path / VersionFile, encoding="utf-8") as f:
                current_version = json.load(f)
            if current_version["version"] != json.loads(data)["version"]:
                # 版本不一致，更新索引
                update_index = True
        # 更新版本文件
        with open(data_path / VersionFile, "w", encoding="utf-8") as f:
            f.write(data.decode("utf-8"))
        # 更新索引
        index_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("正在检查索引文件是否完整")
        # 下载索引文件
        for name in ResFiles:
            filename = f"{name}.json"
            if not (index_dir / filename).exists() or update_index:
                # 索引文件不存在或需要更新时下载
                logger.debug(f"正在下载索引 {filename}...")
                data = await self.download(
                    self.proxy_url(
                        f"{plugin_config.sr_wiki_url}/{filename}"
                    )
                )
                if not data:
                    logger.error(f"文件 {filename} 下载失败")
                    status = False
                    continue
                with open(index_dir / filename, "wb") as f:
                    f.write(data)
        logger.info("索引文件检查完毕")
        if status:
            self.reload()
        return status
