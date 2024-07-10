import asyncio

from redis.asyncio.client import PubSub, Redis
from loguru               import logger

from .user_connection     import UserConnectionPool

redis_connection: Redis # must be initiated externally

class RedisReader:
    channels: dict[int: 'RedisReader'] = {} # 'user_id' : RedisReader

    @staticmethod
    def connect(user_id: int) -> 'RedisReader':
        channel = RedisReader.channels.get(user_id)
        if not channel:
            global redis_connection
            pubsub  = redis_connection.pubsub()
            channel = RedisReader(user_id, pubsub)
            RedisReader.channels[user_id] = channel
        return channel

    ########################################################

    def __init__(self, user_id: int, pubsub: PubSub):
        self.user_id      = user_id
        self.pubsub       = pubsub
        self.is_listening = False
        self.task         = None

    async def _listen(self):
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                event  = str(message['data'])
                if pool := UserConnectionPool.get_by_id(self.user_id):
                    await pool.send(event)
            await asyncio.sleep(0.01)

    ########################################################
    
    async def listen(self):
        if not self.is_listening:
            await self.pubsub.subscribe(str(self.user_id))
            self.task         = asyncio.create_task(self._listen())
            self.is_listening = True

    async def disconnect(self):
        del RedisReader.channels[self.user_id]
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
