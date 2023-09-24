# -*- coding: utf-8 -*-
from typing import *

import blcapi

_config: Optional['AppConfig'] = None


def init():
    global _config
    _config = AppConfig()


def get_config():
    return _config


class AppConfig:
    def __init__(self):
        self.blc_ws_url = 'ws://localhost:12450/api/chat'
        self.room_key_type = blcapi.RoomKeyType.ROOM_ID
        # 房间ID
        self.room_key_value = 92384

        self.tts_voice_id: str | None = None
        self.tts_rate = 250
        self.tts_volume = 1.0

        self.max_tts_queue_size = 5
