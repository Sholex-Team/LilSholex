from aiohttp import ClientSession
from urllib.parse import urlencode
from django.db.models import Model
from asgiref.sync import sync_to_async


def answer_callback_query(session: ClientSession, token: str):
    async def answer_query(query_id, text, show_alert):
        encoded = urlencode({'text': text})
        async with session.get(
            f'https://api.telegram.org/bot{token}/answerCallbackQuery?callback_query_id={query_id}&{encoded}&'
            f'show_alert={show_alert}'
        ) as _:
            return
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
def get_related_obj(queryset, **kwargs):
    return queryset.get(**kwargs)


@sync_to_async
def filter_by_ordering(model, order_type: str, count: int, **kwargs):
    return tuple(model.objects.filter(**kwargs).order_by(order_type)[:count])


@sync_to_async
def get_by_ordering(model, order_type: str, count: int):
    return tuple(model.objects.order_by(order_type)[:count])


@sync_to_async
def exists_obj(obj):
    return obj.exists()


@sync_to_async
def create_task(task_func, *args, **kwargs):
    task_func(*args, **kwargs)


def filter_object(queryset, first: bool, **kwargs):
    if (result := queryset.filter(**kwargs)).exists():
        return result.first() if first else tuple(result)
