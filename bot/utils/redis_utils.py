from typing import Set, Union
import redis
from settings import get_redis_settings


config = get_redis_settings()
redis_db = redis.StrictRedis(host=config.host,
                             port=config.port,
                             decode_responses=True,
                             charset="utf-8")

def delete_key(key: str):
    return redis_db.delete(key)

def get_registered_users() -> Set[str]:
    return redis_db.smembers("registered_users")

def is_registered_user(user_id: Union[str, int]) -> bool:
    return redis_db.sismember("registered_users", user_id)

def add_new_users(value: Union[list, str, int]):
    if isinstance(value, (str, int)):
        redis_db.sadd("registered_users", str(value))
    elif isinstance(value, list):
        redis_db.sadd("registered_users", *value)
