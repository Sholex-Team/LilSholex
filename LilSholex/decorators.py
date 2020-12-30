from aiohttp import ClientError
from requests import RequestException
from asyncio import sleep


def async_fix(func):
    async def check_exception(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except ClientError:
                await sleep(0.4)

    return check_exception


def sync_fix(func):
    def check_exception(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except RequestException:
                continue

    return check_exception
