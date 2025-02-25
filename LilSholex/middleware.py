from django.conf import settings
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from django.utils.decorators import async_only_middleware
import asyncio
from LilSholex.context import telegram as telegram_context

AIOHTTP_SESSION = ClientSession(
    timeout=ClientTimeout(settings.REQUESTS_TIMEOUT),
    connector=TCPConnector(limit=settings.MAX_REQUEST_COUNT, ttl_dns_cache=settings.DNS_CACHE_TIME)
)


@async_only_middleware
def telegram_middleware(get_response):
    set_factory = True

    async def middleware(request):
        nonlocal set_factory
        if set_factory:
            asyncio.get_running_loop().set_task_factory(asyncio.eager_task_factory)
            set_factory = False
        request.is_from_telegram = request.META.get(settings.TELEGRAM_HEADER_NAME) == settings.WEBHOOK_TOKEN
        if request.is_from_telegram:
            telegram_context.common.HTTP_SESSION.set(AIOHTTP_SESSION)
        return await get_response(request)

    return middleware
