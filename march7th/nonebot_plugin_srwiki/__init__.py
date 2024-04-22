from typing import List

from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot import require, on_regex, on_command
from nonebot.params import RegexDict, CommandArg, ArgPlainText

require("nonebot_plugin_saa")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Image, MessageFactory

try:
    from march7th.nonebot_plugin_srres import srres
    from march7th.nonebot_plugin_srres.model.achievements import AchievementType
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres
    from nonebot_plugin_srres.model.achievements import AchievementType

__plugin_meta__ = PluginMetadata(
    name="StarRailWiki",
    description="崩坏：星穹铁道百科",
    usage="""\
查询攻略图片: xxx(角色)(攻略)
查询成就详情: 查成就 xxx
隐藏成就列表: 查隐藏成就
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查攻略: [u]xxx[/u]角色攻略
（支持 角色攻略）
""",
    },
)

BASE_TYPE = "角色"
BASE_TYPE_RE = "(" + "|".join(BASE_TYPE) + ")"
WIKI_TYPE = ["图鉴", "攻略"]
WIKI_TYPE_RE = "(" + "|".join(WIKI_TYPE) + ")"

WIKI_RE = (
    rf"(?P<name>\w{{0,10}}?)(?P<type>{BASE_TYPE_RE}?{WIKI_TYPE_RE})(?P<res>\w{{0,10}})"
)

wiki_search = on_regex(WIKI_RE, priority=9, block=False)


@wiki_search.handle()
async def _(event: Event, matcher: Matcher, regex_dict: dict = RegexDict()):
    wiki_name: str = regex_dict["name"] or ""
    wiki_type: str = regex_dict.get("type") or ""
    res: str = regex_dict.get("res") or ""
    if wiki_name and res:
        await wiki_search.finish()
    if not wiki_name or not wiki_type:
        await wiki_search.finish()
    if not wiki_name and res:
        wiki_name = res
    if "角色" in wiki_type:
        wiki_type_1 = "character"
    else:
        wiki_type_1 = "all"
    pic_content = None
    if wiki_type_1 in {"all", "character"}:
        pic_content = await srres.get_character_overview(wiki_name)
    if (
        not pic_content
        and wiki_type_1 in {"all", "character"}
    ):
        pic_content = await srres.get_character_material(wiki_name)
    if pic_content:
        matcher.stop_propagation()
        msg_builder = MessageFactory([Image(pic_content)])
        await msg_builder.finish(at_sender=not event.is_tome())
    await wiki_search.finish()
