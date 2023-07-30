"""
Under development, this file has no usage yet, please don't even try to use it.
"""

import typing

from aioredis import Redis


class API:
    """A helper class for interacting with redis and moderating users."""

    def __init__(self):
        self.debug = False
        self.redis = Redis(host="redis", port=6379, decode_responses=True)

        self.req = typing.Optional[str]

    async def ban_user(self, duration: int = 120):
        """Bans a user from using the API temporally, by default using 120 seconds."""
        self.redis.set(self.req, "banned", duration)

    async def unban_user(self):
        """When user gets unbanned they will have access to the API again."""
        self.redis.delete(self.req)

    async def key_exists(self, key: str) -> bool:
        """
        Check if the given key exists in the redis database.
        Function to check if a key exists already in the redis database.
        :param key: The key to be used in the redis database.
        :return: boolean.
        """

        exists = await self.redis.exists(key)
        return exists
