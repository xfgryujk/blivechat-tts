# -*- coding: utf-8 -*-
import dataclasses
import enum


@dataclasses.dataclass
class HeartbeatMsg:
    """心跳消息"""

    @classmethod
    def from_command(cls, data: dict):  # noqa
        return cls()


class AuthorType(enum.IntEnum):
    NORMAL = 0
    GUARD = 1
    """舰队"""
    ADMIN = 2
    """房管"""
    ROOM_OWNER = 3
    """主播"""


class GuardLevel(enum.IntEnum):
    """舰队等级"""

    NONE = 0
    LV3 = 1
    """总督"""
    LV2 = 2
    """提督"""
    LV1 = 3
    """舰长"""


class ContentType(enum.IntEnum):
    TEXT = 0
    EMOTICON = 1


@dataclasses.dataclass
class AddTextMsg:
    """弹幕消息"""

    avatar_url: str = ''
    """用户头像URL"""
    timestamp: int = 0
    """时间戳（秒）"""
    author_name: str = ''
    """用户名"""
    author_type: int = AuthorType.NORMAL.value
    """用户类型，见AuthorType"""
    content: str = ''
    """弹幕内容"""
    privilege_type: int = GuardLevel.NONE.value
    """舰队等级，见GuardLevel"""
    is_gift_danmaku: bool = False
    """是否礼物弹幕"""
    author_level: int = 1
    """用户等级"""
    is_newbie: bool = False
    """是否正式会员"""
    is_mobile_verified: bool = True
    """是否绑定手机"""
    medal_level: int = 0
    """勋章等级，如果没戴当前房间勋章则为0"""
    id: str = ''
    """消息ID"""
    translation: str = ''
    """弹幕内容翻译"""
    content_type: int = ContentType.TEXT.value
    """内容类型，见ContentType"""
    content_type_params: dict | list = dataclasses.field(default_factory=dict)
    """跟内容类型相关的参数"""

    @classmethod
    def from_command(cls, data: list):
        content_type = data[13]
        content_type_params = data[14]
        if content_type == ContentType.EMOTICON:
            content_type_params = {'url': content_type_params[0]}

        return cls(
            avatar_url=data[0],
            timestamp=data[1],
            author_name=data[2],
            author_type=data[3],
            content=data[4],
            privilege_type=data[5],
            is_gift_danmaku=bool(data[6]),
            author_level=data[7],
            is_newbie=bool(data[8]),
            is_mobile_verified=bool(data[9]),
            medal_level=data[10],
            id=data[11],
            translation=data[12],
            content_type=content_type,
            content_type_params=content_type_params,
        )


@dataclasses.dataclass
class AddGiftMsg:
    """礼物消息"""

    id: str = ''
    """消息ID"""
    avatar_url: str = ''
    """用户头像URL"""
    timestamp: int = 0
    """时间戳（秒）"""
    author_name: str = ''
    """用户名"""
    total_coin: int = 0
    """总价瓜子数，1000金瓜子 = 1元"""
    gift_name: str = ''
    """礼物名"""
    num: int = 0
    """数量"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            id=data['id'],
            avatar_url=data['avatarUrl'],
            timestamp=data['timestamp'],
            author_name=data['authorName'],
            total_coin=data['totalCoin'],
            gift_name=data['giftName'],
            num=data['num'],
        )


@dataclasses.dataclass
class AddMemberMsg:
    """上舰消息"""

    id: str = ''
    """消息ID"""
    avatar_url: str = ''
    """用户头像URL"""
    timestamp: int = 0
    """时间戳（秒）"""
    author_name: str = ''
    """用户名"""
    privilege_type: int = GuardLevel.NONE.value
    """舰队等级，见GuardLevel"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            id=data['id'],
            avatar_url=data['avatarUrl'],
            timestamp=data['timestamp'],
            author_name=data['authorName'],
            privilege_type=data['privilegeType'],
        )


@dataclasses.dataclass
class AddSuperChatMsg:
    """醒目留言消息"""

    id: str = ''
    """消息ID"""
    avatar_url: str = ''
    """用户头像URL"""
    timestamp: int = 0
    """时间戳（秒）"""
    author_name: str = ''
    """用户名"""
    price: int = 0
    """价格（元）"""
    content: str = ''
    """内容"""
    translation: str = ''
    """内容翻译"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            id=data['id'],
            avatar_url=data['avatarUrl'],
            timestamp=data['timestamp'],
            author_name=data['authorName'],
            price=data['price'],
            content=data['content'],
            translation=data['translation'],
        )


@dataclasses.dataclass
class DelSuperChatMsg:
    """删除醒目留言消息"""

    ids: list[str] = dataclasses.field(default_factory=list)
    """醒目留言ID数组"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            ids=data['ids'],
        )


@dataclasses.dataclass
class UpdateTranslationMsg:
    """更新内容翻译消息"""

    id: str = ''
    """消息ID"""
    translation: str = ''
    """内容翻译"""

    @classmethod
    def from_command(cls, data: list):
        return cls(
            id=data[0],
            translation=data[1],
        )


class FatalErrorType(enum.IntEnum):
    AUTH_CODE_ERROR = 1


@dataclasses.dataclass
class FatalErrorMsg:
    """致命错误消息"""

    type: int = FatalErrorType.AUTH_CODE_ERROR.value
    """类型，见FatalErrorType"""
    msg: str = ''
    """描述信息"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            type=data['type'],
            msg=data['msg'],
        )
