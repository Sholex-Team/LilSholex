from json import JSONDecodeError
from aiohttp.client_exceptions import ClientError


def fix(func):
    async def check_exception(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except (ClientError, JSONDecodeError):
                continue
    return check_exception
