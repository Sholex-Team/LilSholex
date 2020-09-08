from typing import Callable
from aiohttp import ClientSession
from urllib.parse import urlencode
from asgiref.sync import sync_to_async
from django.db.models import Model


def answer_callback_query(token: str, session: ClientSession) -> Callable:
    async def answer_query(query_id, text, show_alert):
        encoded = urlencode({'text': text})
        async with session.get(
            f'https://api.telegram.org/bot{token}/answerCallbackQuery?callback_query_id={query_id}&{encoded}&'
            f'show_alert={show_alert}'
        ):
            pass
    return answer_query


@sync_to_async
def save_obj(obj: Model):
    obj.save()


@sync_to_async
def delete_obj(obj):
    obj.delete()


@sync_to_async
def get_obj(model, **kwargs):
    return model.objects.get(**kwargs)


@sync_to_async
def create_obj(model, **kwargs):
    return model.objects.create(**kwargs)


@sync_to_async
def filter_by_ordering(model, order_type, **kwargs):
    return list(model.objects.filter(**kwargs).order_by(order_type))


@sync_to_async
def get_by_ordering(model, order_type):
    return list(model.objects.order_by(order_type))


@sync_to_async
def exists_obj(obj):
    return obj.exists()
