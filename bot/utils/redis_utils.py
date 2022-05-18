from typing import Set, Union
from settings import get_redis_settings
import redis


class RedisUtils:
    """Helper class for working with the Redis database"""
    def __init__(self) -> None:
        config = get_redis_settings()
        self.__redis_db = redis.StrictRedis(host=config.host,
                                port=config.port,
                                decode_responses=True,
                                charset="utf-8")

    def delete_key(self, key: str):
        return self.__redis_db.delete(key)

    def get_registered_users(self) -> Set[str]:
        return self.__redis_db.smembers("registered_users")

    def is_registered_user(self, user_id: Union[str, int]) -> bool:
        return self.__redis_db.sismember("registered_users", user_id)

    def add_new_users(self, value: Union[list, str, int]):
        if isinstance(value, (str, int)):
            self.__redis_db.sadd("registered_users", str(value))
        elif isinstance(value, list):
            self.__redis_db.sadd("registered_users", *value)
