from typing import Optional

from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    github_proxy: Optional[str] = "https://mirror.ghproxy.com"
    sr_wiki_url: Optional[str] = (
        "https://github.com/dontdot/star-rail-atlas/blob/index"
    )
    sr_guide_url: Optional[str] = "https://raw.githubusercontent.com/Nwflower/star-rail-atlas/master"

plugin_config = get_plugin_config(Config)
