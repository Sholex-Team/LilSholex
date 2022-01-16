from aiohttp import ClientError
from requests import RequestException
from asyncio import sleep as async_sleep
from time import sleep as sync_sleep
from .exceptions import TooManyRequests


def async_fix(func):
    async def check_exception(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except ClientError:
                await async_sleep(0.4)

    return check_exception


def sync_fix(func):
    def check_exception(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except TooManyRequests as e:
                sync_sleep(e.retry_after)
            except RequestException:
                continue

    return check_exception
