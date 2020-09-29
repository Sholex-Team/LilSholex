import requests
from urllib.parse import urlencode
from django.db.models import Model


def answer_callback_query(token: str):
    def answer_query(query_id, text, show_alert):
        encoded = urlencode({'text': text})
        requests.get(
            f'https://api.telegram.org/bot{token}/answerCallbackQuery?callback_query_id={query_id}&{encoded}&'
            f'show_alert={show_alert}'
        )
    return answer_query


def save_obj(obj: Model):
    obj.save()


def delete_obj(obj):
    obj.delete()


def get_obj(model, **kwargs):
    return model.objects.get(**kwargs)


def create_obj(model, **kwargs):
    return model.objects.create(**kwargs)


def filter_by_ordering(model, order_type, **kwargs):
    return model.objects.filter(**kwargs).order_by(order_type)


def get_by_ordering(model, order_type):
    return model.objects.order_by(order_type)


def exists_obj(obj):
    return obj.exists()
