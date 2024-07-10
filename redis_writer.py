from redis.asyncio.client import Redis

from .event import Event

redis_connection: Redis # must be initiated externally

class RedisWriter:
    @staticmethod
    async def push(channel: str, event: Event):
        global redis_connection
        await redis_connection.publish(channel, event.model_dump_json())
