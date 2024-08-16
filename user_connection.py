from typing             import Awaitable
from uuid               import uuid4

from fastapi.websockets import WebSocketState, WebSocket
from loguru             import logger

from .event             import Event


class UserConnection:
    def __init__(self,
        pool      : 'UserConnectionPool',
        user_id   : int,
        websocket : WebSocket,
        on_event  : Awaitable
    ):
        self.socket: WebSocket = websocket
        self.on_event          = on_event
        self.pool              = pool
        self.user_id           = user_id
        self.id                = str(uuid4())

    async def listen(self):
        while True:
            data  = await self.socket.receive_json()
            event = Event(**data)
            await self.on_event(self.user_id, event)

    async def send(self, event: str):
        try:
            await self.socket.send_text(event)
        except Exception as e:
            logger.error(f'Error while sending event to websocket: {e}')

    async def disconnect(self) -> bool:
        if self.socket.client_state != WebSocketState.DISCONNECTED:
            try:
                await self.socket.close()
            except Exception as e:
                logger.error(f'Socket closing error: {e}')
        return await self.pool._disconnect(self.id) # return True when pool is empty


class UserConnectionPool:
    _pools: dict[int, 'UserConnectionPool'] = {} # user_id: UserConnectionPool

    @staticmethod
    def connect(
        user_id   : int,
        websocket : WebSocket,
        on_event  : Awaitable
    ) -> UserConnection:
        pool = UserConnectionPool.get_by_id(user_id)
        if not pool:
            pool = UserConnectionPool(user_id)
            UserConnectionPool._pools[user_id] = pool
        return pool._add_connection(websocket, on_event)

    @staticmethod
    def is_online(user_id: int) -> bool:
        pool = UserConnectionPool.get_by_id(user_id)
        return pool and pool._is_online

    @staticmethod
    def get_by_id(user_id: int) -> 'UserConnectionPool':
        return UserConnectionPool._pools.get(user_id)

    ########################################################

    def __init__(self, user_id: int):
        self.user_id                                = user_id
        self.connections: dict[str, UserConnection] = {} # connection_id: UserConnection

    def _add_connection(self,
        websocket : WebSocket,
        on_event  : Awaitable
    ) -> UserConnection:
        connection = UserConnection(self, self.user_id, websocket, on_event)
        self.connections[connection.id] = connection
        return connection

    async def _disconnect(self, connection_id: str) -> bool:
        del self.connections[connection_id]
        if not self._is_online:
            del UserConnectionPool._pools[self.user_id]
            return True
        return False

    @property
    def _is_online(self) -> bool:
        return bool(len(self.connections))

    async def send(self, event: str):
        for connection in self.connections.values():
            await connection.send(event)
