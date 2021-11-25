import json
from time import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from requests import Session as RequestSession
from .handlers import inline_query_handlers, chosen_inline_result_handlers, callback_query_handlers, message_handlers
from persianmeme import models
from LilSholex.exceptions import RequestInterruption


def webhook(request):
    update = json.loads(request.body.decode())
    match update:
        case {'chosen_inline_result': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'inline_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'callback_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'message': chat_id_result}:
            if (user_chat_id := chat_id_result['chat']['id']) < 0:
                return HttpResponse(status=200)
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
    match update:
        case {'chosen_inline_result': chosen_inline_result}:
            chosen_inline_result_handlers.handler(request, chosen_inline_result, user_chat_id)
        case {'inline_query': inline_query}:
            inline_query_handlers.handler(request, inline_query, user_chat_id)
        case {'callback_query': callback_query}:
            callback_query_handlers.handler(request, callback_query, user_chat_id)
        case {'message': message}:
            message_handlers.handler(request, message, user_chat_id)
    return HttpResponse(status=200)


def webhook_wrapper(request):
    request.http_session = RequestSession()
    try:
        return webhook(request)
    except RequestInterruption:
        return HttpResponse(status=200)
