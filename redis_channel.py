import asyncio

from redis.asyncio.client import Redis
from loguru               import logger

from .event               import Event
from .user_connection     import UserConnectionPool


class RedisChannel:
    channels   : dict[int: 'RedisChannel'] = {} # 'user_id' : RedisChannel
    connection : Redis 

    @staticmethod
    async def setup_connection(**kwargs):
        RedisChannel.connection = Redis(**kwargs)
        await RedisChannel.connection.ping()

    @staticmethod
    def get(user_id: int) -> 'RedisChannel':
        channel = RedisChannel.channels.get(user_id)
        if not channel:
            channel = RedisChannel(user_id)
            RedisChannel.channels[user_id] = channel
        return channel

    ########################################################
    
    def __init__(self, user_id: int):
        self.user_id    = user_id
        self.pubsub     = None
        self.is_reading = False
        self.task       = None

    async def _read(self):
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                event  = str(message['data'])
                if pool := UserConnectionPool.get_by_id(self.user_id):
                    await pool.send(event)
            await asyncio.sleep(0.01)

    ########################################################
    
    async def read(self):
        if not self.is_reading:
            self.pubsub = RedisChannel.connection.pubsub()
            await self.pubsub.subscribe(str(self.user_id))
            self.task       = asyncio.create_task(self._read())
            self.is_reading = True

    async def write(self, event: Event):
        await RedisChannel.connection.publish(str(self.user_id), event.model_dump_json())

    async def close(self):
        del RedisChannel.channels[self.user_id]
        try:
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        except Exception as e:
            logger.error(f'An error occurred while redis disconnect: {e}')
