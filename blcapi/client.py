# -*- coding: utf-8 -*-
import asyncio
import enum
import json
import logging
from typing import *

import aiohttp

from . import handlers

__all__ = (
    'RoomKeyType',
    'RoomKey',
    'Command',
    'BlivechatClient',
)

logger = logging.getLogger('blcapi')


class RoomKeyType(enum.IntEnum):
    ROOM_ID = 1
    AUTH_CODE = 2


class RoomKey(NamedTuple):
    """用来标识一个房间"""
    type: RoomKeyType
    value: int | str

    def __str__(self):
        res = str(self.value)
        if self.type == RoomKeyType.AUTH_CODE:
            # 身份码要脱敏
            res = '***' + res[-3:]
        return res
    __repr__ = __str__


class Command(enum.IntEnum):
    HEARTBEAT = 0
    JOIN_ROOM = 1
    ADD_TEXT = 2
    ADD_GIFT = 3
    ADD_MEMBER = 4
    ADD_SUPER_CHAT = 5
    DEL_SUPER_CHAT = 6
    UPDATE_TRANSLATION = 7
    FATAL_ERROR = 8


class FatalError(Exception):
    """致命错误，无法重连了"""
    def __init__(self, type_, msg):
        super().__init__(msg)
        self.type = type_


class BlivechatClient:
    """
    blivechat消息转发服务的客户端

    :param ws_url: blivechat消息转发服务WebSocket地址
    :param room_key: 要连接的房间
    :param session: 连接池
    :param heartbeat_interval: 发送心跳包的间隔时间（秒）
    """

    def __init__(
        self,
        ws_url: str,
        room_key: RoomKey,
        *,
        session: aiohttp.ClientSession | None = None,
        heartbeat_interval: float = 10,
    ):
        self._ws_url = ws_url
        self._room_key = room_key

        if session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            self._own_session = True
        else:
            self._session = session
            self._own_session = False
            assert self._session.loop is asyncio.get_event_loop()  # noqa

        self._heartbeat_interval = heartbeat_interval

        self._handler: handlers.HandlerInterface | None = None
        """消息处理器"""

        # 在运行时初始化的字段
        self._websocket: aiohttp.ClientWebSocketResponse | None = None
        """WebSocket连接"""
        self._network_future: asyncio.Future | None = None
        """网络协程的future"""
        self._heartbeat_timer_handle: asyncio.TimerHandle | None = None
        """发心跳包定时器的handle"""

    @property
    def is_running(self) -> bool:
        """本客户端正在运行，注意调用stop后还没完全停止也算正在运行"""
        return self._network_future is not None

    @property
    def room_key(self):
        """构造时传进来的room_key参数"""
        return self._room_key

    def set_handler(self, handler: Optional['handlers.HandlerInterface']):
        """
        设置消息处理器

        注意消息处理器和网络协程运行在同一个协程，如果处理消息耗时太长会阻塞接收消息。如果是CPU密集型的任务，建议将消息推到线程池处理；
        如果是IO密集型的任务，应该使用async函数，并且在handler里使用create_task创建新的协程

        :param handler: 消息处理器
        """
        self._handler = handler

    def start(self):
        """启动本客户端"""
        if self.is_running:
            logger.warning('room=%s client is running, cannot start() again', self._room_key)
            return

        self._network_future = asyncio.create_task(self._network_coroutine_wrapper())

    def stop(self):
        """停止本客户端"""
        if not self.is_running:
            logger.warning('room=%s client is stopped, cannot stop() again', self._room_key)
            return

        self._network_future.cancel()

    async def stop_and_close(self):
        """便利函数，停止本客户端并释放本客户端的资源，调用后本客户端将不可用"""
        if self.is_running:
            self.stop()
            await self.join()
        await self.close()

    async def join(self):
        """等待本客户端停止"""
        if not self.is_running:
            logger.warning('room=%s client is stopped, cannot join()', self._room_key)
            return

        await asyncio.shield(self._network_future)

    async def close(self):
        """释放本客户端的资源，调用后本客户端将不可用"""
        if self.is_running:
            logger.warning('room=%s is calling close(), but client is running', self._room_key)

        # 如果session是自己创建的则关闭session
        if self._own_session:
            await self._session.close()

    async def _send_cmd_data(self, cmd: Command, data: dict):
        """
        发送消息给服务器

        :param cmd: 消息类型，见Command
        :param data: 消息体JSON数据
        """
        if self._websocket is None or self._websocket.closed:
            raise ConnectionResetError('websocket is closed')

        body = {'cmd': cmd, 'data': data}
        await self._websocket.send_json(body)

    async def _network_coroutine_wrapper(self):
        """负责处理网络协程的异常，网络协程具体逻辑在_network_coroutine里"""
        exc = None
        try:
            await self._network_coroutine()
        except asyncio.CancelledError:
            # 正常停止
            pass
        except Exception as e:
            logger.exception('room=%s _network_coroutine() finished with exception:', self._room_key)
            exc = e
        finally:
            logger.debug('room=%s _network_coroutine() finished', self._room_key)
            self._network_future = None

        if self._handler is not None:
            self._handler.on_client_stopped(self, exc)

    async def _network_coroutine(self):
        """网络协程，负责连接服务器、接收消息、解包"""
        retry_count = 0
        while True:
            try:
                # 连接
                async with self._session.ws_connect(
                    self._ws_url,
                    receive_timeout=self._heartbeat_interval + 5,
                ) as websocket:
                    self._websocket = websocket
                    await self._on_ws_connect()

                    # 处理消息
                    message: aiohttp.WSMessage
                    async for message in websocket:
                        self._on_ws_message(message)
                        # 至少成功处理1条消息
                        retry_count = 0

            except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
                # 掉线重连
                pass
            except FatalError:
                raise
            finally:
                self._websocket = None
                await self._on_ws_close()

            # 准备重连
            retry_count += 1
            logger.warning('room=%s is reconnecting, retry_count=%d', self._room_key, retry_count)
            await asyncio.sleep(self._get_reconnect_interval(retry_count))

    @staticmethod
    def _get_reconnect_interval(retry_count: int):
        # 重连间隔时间不要太小，否则会消耗公共服务器资源
        return min(1 + (retry_count - 1) * 2, 10)

    async def _on_ws_connect(self):
        """WebSocket连接成功"""
        await self._send_join_room()
        self._heartbeat_timer_handle = asyncio.get_running_loop().call_later(
            self._heartbeat_interval, self._on_send_heartbeat
        )

    async def _on_ws_close(self):
        """WebSocket连接断开"""
        if self._heartbeat_timer_handle is not None:
            self._heartbeat_timer_handle.cancel()
            self._heartbeat_timer_handle = None

    async def _send_join_room(self):
        """发送加入房间消息"""
        await self._send_cmd_data(Command.JOIN_ROOM, {
            'roomKey': {
                'type': self._room_key.type,
                'value': self._room_key.value
            },
            # 'config': {
            #     'autoTranslate': False
            # }
        })

    def _on_send_heartbeat(self):
        """定时发送心跳包的回调"""
        if self._websocket is None or self._websocket.closed:
            self._heartbeat_timer_handle = None
            return

        self._heartbeat_timer_handle = asyncio.get_running_loop().call_later(
            self._heartbeat_interval, self._on_send_heartbeat
        )
        asyncio.create_task(self._send_heartbeat())

    async def _send_heartbeat(self):
        """发送心跳包"""
        try:
            await self._send_cmd_data(Command.HEARTBEAT, {})
        except (ConnectionResetError, aiohttp.ClientConnectionError) as e:
            logger.warning('room=%s _send_heartbeat() failed: %r', self._room_key, e)
        except Exception:  # noqa
            logger.exception('room=%s _send_heartbeat() failed:', self._room_key)

    def _on_ws_message(self, message: aiohttp.WSMessage):
        """
        收到WebSocket消息

        :param message: WebSocket消息
        """
        if message.type != aiohttp.WSMsgType.TEXT:
            logger.warning('room=%s unknown websocket message type=%s, data=%s', self._room_key,
                           message.type, message.data)
            return

        try:
            body = json.loads(message.data)
            self._handle_command(body)
        except Exception:
            logger.error('room=%s, body=%s', self._room_key, message.data)
            raise

    def _handle_command(self, command: dict):
        """
        处理业务消息

        :param command: 业务消息
        """
        if self._handler is not None:
            try:
                self._handler.handle(self, command)
            except Exception as e:
                logger.exception('room=%s _handle_command() failed, command=%s', self._room_key, command, exc_info=e)

        cmd = command['cmd']
        if cmd == Command.FATAL_ERROR:
            body = command['data']
            raise FatalError(body['type'], body['msg'])
