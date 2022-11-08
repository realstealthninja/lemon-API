import functools

from aioredis import Redis
from fastapi import HTTPException

client = Redis(host="redis")


async def limit(key: str = None, limit: int = 5, ttl: int = 60):
    """
    Used to limit the amount of calls to endpoints.
    :param key: the key to use to store the calls
    :param limit: the maximum amount of calls allowed during ttl
    :param ttl: the time to live of the calls
    :return: a dictionary with the following keys: call, ttl
    """
    req = await client.incr(key)
    if req == 1:
        await client.expire(key, 60)
        ttl = 60
    else:
        ttl = await client.ttl(key)
    if req > limit:
        return {"call": False, "ttl": ttl}
    else:
        return {"call": True, "ttl": ttl}


def limiter(*, max_calls: int = 5, ttl: int = 60):
    """
    NOTE: This decorator requires the decorated function to have fastAPI Request in the parameters.
    
    Decorator to limit the amount of calls to a specific endpoint.
    Limitation is based on IP address.
    :param max_calls: the maximum amount of calls allowed during ttl
    :param ttl: the time to live of the calls
    :return: HTTPException OR the function
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            client_ip = kwargs["request"].client.host
            res = await limit(client_ip, max_calls, ttl)
            if res["call"]:
                return await func(*args, **kwargs)
            else:
                raise HTTPException(
                    status_code=429,
                    detail=f"Ratelimited, too many requests. Try again in {res['ttl']} seconds.",
                    headers={"Retry-After": res["ttl"]},
                )

        return wrapper

    return decorator
