import json
from time import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .handlers import *
from persianmeme import models
from LilSholex.exceptions import RequestInterruption
from LilSholex.context import telegram as telegram_context


@require_POST
async def webhook(request):
    if not request.is_from_telegram:
        return HttpResponseForbidden()
    update = json.loads(request.body.decode())
    match update:
        case {'inline_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'chosen_inline_result': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'callback_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'message': chat_id_result}:
            if (user_chat_id := chat_id_result['chat']['id']) < 0:
                return HttpResponse(status=200)
        case {'channel_post': chat_id_result}:
            user_chat_id = chat_id_result['chat']['id']
    now = time()
    if (cache_value := cache.get_or_set(user_chat_id, (
            now + settings.SPAM_TIME, 0
    ), settings.SPAM_TIME)) == models.User.Status.BANNED:
        return HttpResponse(status=200)
    if cache_value[0] > now:
        if cache_value[1] > settings.SPAM_COUNT:
            cache.set(user_chat_id, models.User.Status.BANNED, settings.SPAM_PENALTY)
            return HttpResponse(status=200)
        cache.set(user_chat_id, (cache_value[0], cache_value[1] + 1), cache_value[0] - now)
    telegram_context.common.BOT_TOKEN.set(settings.MEME_TOKEN)
    telegram_context.common.USER_CHAT_ID.set(user_chat_id)
    match update:
        case {'inline_query': inline_query}:
            telegram_context.inline_query.INLINE_QUERY.set(inline_query)
            await inline_query_handlers.handler()
        case {'chosen_inline_result': chosen_inline_result}:
            telegram_context.chosen_inline_result.CHOSEN_INLINE_RESULT.set(chosen_inline_result)
            await chosen_inline_result_handlers.handler()
        case {'callback_query': callback_query}:
            telegram_context.callback_query.CALLBACK_QUERY.set(callback_query)
            await callback_query_handlers.handler()
        case {'message': message}:
            telegram_context.message.MESSAGE.set(message)
            await message_handlers.handler()
        case {'channel_post': message}:
            telegram_context.message.MESSAGE.set(message)
            await channel_post_handlers.handler()
    return HttpResponse(status=200)


async def webhook_wrapper(request):
    try:
        return await webhook(request)
    except RequestInterruption:
        return HttpResponse(status=200)
