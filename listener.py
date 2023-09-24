# -*- coding: utf-8 -*-
import logging
import sys
from typing import *

import blcapi
import blcapi.client as blc_client
import blcapi.models as blc_models
import config
import tts

logger = logging.getLogger(__name__)

_live_client: blc_client.BlivechatClient | None = None
_live_msg_handler: Optional['LiveMsgHandler'] = None


def init():
    global _live_client, _live_msg_handler
    _live_msg_handler = LiveMsgHandler()

    cfg = config.get_config()
    _live_client = blcapi.BlivechatClient(
        ws_url=cfg.blc_ws_url,
        room_key=blcapi.RoomKey(type=cfg.room_key_type, value=cfg.room_key_value),
    )
    _live_client.set_handler(_live_msg_handler)
    _live_client.start()


class LiveMsgHandler(blcapi.BaseHandler):
    def on_client_stopped(self, client: blcapi.BlivechatClient, exception: Exception | None):
        if isinstance(exception, blc_client.FatalError):
            sys.exit(1)
        else:
            client.start()

    def _on_add_text(self, client: blcapi.BlivechatClient, message: blc_models.AddTextMsg):
        tts.say(f'{message.author_name} 说：{message.content}')

    def _on_add_gift(self, client: blcapi.BlivechatClient, message: blc_models.AddGiftMsg):
        tts.say(f'{message.author_name} 赠送了{message.num}个{message.gift_name}')

    def _on_add_member(self, client: blcapi.BlivechatClient, message: blc_models.AddMemberMsg):
        if message.privilege_type == blc_models.GuardLevel.LV1:
            guard_name = '舰长'
        elif message.privilege_type == blc_models.GuardLevel.LV2:
            guard_name = '提督'
        elif message.privilege_type == blc_models.GuardLevel.LV3:
            guard_name = '总督'
        else:
            guard_name = '未知舰队等级'
        tts.say(f'{message.author_name} 购买了{guard_name}')

    def _on_add_super_chat(self, client: blcapi.BlivechatClient, message: blc_models.AddSuperChatMsg):
        tts.say(f'{message.author_name} 打赏{message.price}元，说：{message.content}')
