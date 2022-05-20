from typing import Any, Set, Union
from redis.commands.json.path import Path
from settings import get_redis_settings
import redis
import json


class RedisUtils:
    """Helper class for working with the Redis database"""

    transaction_step_data = "transaction_step_data"
    wallet_step_data      = "wallet_step_data"

    def __init__(self) -> None:
        config = get_redis_settings()
        self.__redis_db = redis.StrictRedis(host=config.host,
                                            port=config.port,
                                            password=config.password,
                                            decode_responses=True,
                                            charset="utf-8")
        self.__redis_json = self.__redis_db.json()

        if not self.__redis_json.get(self.transaction_step_data) and \
           not self.__redis_json.get(self.transaction_step_data):
           
            self.__redis_json.set(self.transaction_step_data, Path.root_path(), {})
            self.__redis_json.set(self.wallet_step_data, Path.root_path(), {})

    def delete_key(self, key: str) -> bool:
        return self.__redis_db.delete(key)

    def get_registered_users(self) -> Set[str]:
        """Get set of `registered_users`"""
        return self.__redis_db.smembers("registered_users")

    def is_registered_user(self, user_id: Union[str, int]) -> bool:
        """Check if user is in `registered_users`"""
        return self.__redis_db.sismember("registered_users", user_id)

    def add_new_users(self, value: Union[list, str, int]):
        if isinstance(value, (str, int)):
            self.__redis_db.sadd("registered_users", str(value))
        elif isinstance(value, list):
            self.__redis_db.sadd("registered_users", *value)

    def add_trasaction_step_data(
        self, 
        user_id: Union[str, int], 
        key: str, 
        value: Union[str, int]
    ) -> bool:
        if not self.__redis_json.type(self.transaction_step_data, Path(f".{user_id}")):
            self.__redis_json.set(self.transaction_step_data, Path(f".{user_id}"), {})
        return self.__redis_json.set(self.transaction_step_data, Path(f".{user_id}.{key}"), value)

    def get_transaction_step_data(self, user_id: Union[str, int]) -> dict:
        data = self.__redis_json.get(self.transaction_step_data, Path(f".{user_id}"))
        return data
