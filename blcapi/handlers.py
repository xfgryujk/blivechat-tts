# -*- coding: utf-8 -*-
import logging
from typing import *

from . import client as cli
from . import models

__all__ = (
    'HandlerInterface',
    'BaseHandler',
)

logger = logging.getLogger('blivedm')

logged_unknown_cmds = set()
"""已打日志的未知cmd"""


class HandlerInterface:
    """直播消息处理器接口"""

    def handle(self, client: cli.BlivechatClient, command: dict):
        raise NotImplementedError

    def on_client_stopped(self, client: cli.BlivechatClient, exception: Exception | None):
        """当客户端停止时调用。可以在这里close或者重新start"""


def _make_msg_callback(method_name, message_cls):
    def callback(self: 'BaseHandler', client: cli.BlivechatClient, command: dict):
        method = getattr(self, method_name)
        return method(client, message_cls.from_command(command['data']))
    return callback


class BaseHandler(HandlerInterface):
    """一个简单的消息处理器实现，带消息分发和消息类型转换。继承并重写_on_xxx方法即可实现自己的处理器"""

    _CMD_CALLBACK_DICT: dict[
        int,
        Callable[
            ['BaseHandler', cli.BlivechatClient, dict],
            Any
        ] | None
    ] = {
        # 收到心跳包
        cli.Command.HEARTBEAT: _make_msg_callback('_on_heartbeat', models.HeartbeatMsg),
        # 收到弹幕
        cli.Command.ADD_TEXT: _make_msg_callback('_on_add_text', models.AddTextMsg),
        # 有人送礼
        cli.Command.ADD_GIFT: _make_msg_callback('_on_add_gift', models.AddGiftMsg),
        # 有人上舰
        cli.Command.ADD_MEMBER: _make_msg_callback('_on_add_member', models.AddMemberMsg),
        # 醒目留言
        cli.Command.ADD_SUPER_CHAT: _make_msg_callback('_on_add_super_chat', models.AddSuperChatMsg),
        # 删除醒目留言
        cli.Command.DEL_SUPER_CHAT: _make_msg_callback('_on_del_super_chat', models.DelSuperChatMsg),
        # 更新翻译
        cli.Command.UPDATE_TRANSLATION: _make_msg_callback('_on_update_translation', models.UpdateTranslationMsg),
        # 删除醒目留言
        cli.Command.FATAL_ERROR: _make_msg_callback('_on_fatal_error', models.FatalErrorMsg),
    }
    """cmd -> 处理回调"""

    def handle(self, client: cli.BlivechatClient, command: dict):
        cmd = command['cmd']
        if cmd not in self._CMD_CALLBACK_DICT:
            # 只有第一次遇到未知cmd时打日志
            if cmd not in logged_unknown_cmds:
                logger.warning('room=%s unknown cmd=%s, command=%s', client.room_key, cmd, command)
                logged_unknown_cmds.add(cmd)
            return

        callback = self._CMD_CALLBACK_DICT[cmd]
        if callback is not None:
            callback(self, client, command)

    def _on_heartbeat(self, client: cli.BlivechatClient, message: models.HeartbeatMsg):
        """收到心跳包"""

    def _on_add_text(self, client: cli.BlivechatClient, message: models.AddTextMsg):
        """收到弹幕"""

    def _on_add_gift(self, client: cli.BlivechatClient, message: models.AddGiftMsg):
        """有人送礼"""

    def _on_add_member(self, client: cli.BlivechatClient, message: models.AddMemberMsg):
        """有人上舰"""

    def _on_add_super_chat(self, client: cli.BlivechatClient, message: models.AddSuperChatMsg):
        """醒目留言"""

    def _on_del_super_chat(self, client: cli.BlivechatClient, message: models.DelSuperChatMsg):
        """删除醒目留言"""

    def _on_update_translation(self, client: cli.BlivechatClient, message: models.UpdateTranslationMsg):
        """更新翻译"""

    def _on_fatal_error(self, client: cli.BlivechatClient, message: models.FatalErrorMsg):
        """致命错误"""
