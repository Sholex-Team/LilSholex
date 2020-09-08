from typing import Callable
from urllib.parse import urlencode
import requests
from aiohttp import ClientSession
from asgiref.sync import sync_to_async
from django.conf import settings
from LilSholex.decorators import fix
from LilSholex.functions import answer_callback_query as answer_callback_query_closure
from . import models


@sync_to_async
def get_voice(file_unique_id, voice_type='n'):
    target_voice = models.Voice.objects.filter(file_unique_id=file_unique_id, status='a', voice_type=voice_type)
    if target_voice.exists():
        return target_voice.first()


@sync_to_async
def get_owner():
    return models.User.objects.get(rank='o')


@sync_to_async
def add_voice(file_id, file_unique_id, name, sender, status):
    if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type='n').exists():
        return models.Voice.objects.create(
            file_id=file_id, file_unique_id=file_unique_id, name=name, sender=sender, status=status
        )


@sync_to_async
def count_voices():
    voices_count = models.Voice.objects.filter(status='a').count()
    return f'All voices count : {voices_count}'


@sync_to_async
def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


@fix
async def answer_inline_query(inline_query_id, results, next_offset, cache_time, session: ClientSession, /):
    encoded = urlencode({'results': results})
    async with session.get(
            f'https://api.telegram.org/bot{settings.MEME}/answerInlineQuery?inline_query_id={inline_query_id}&'
            f'{encoded}&next_offset={next_offset}&cache_time={cache_time}&is_personal=True'
    ) as _:
        pass


@sync_to_async
def delete_voice(file_unique_id):
    models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type='n', status='a').delete()


def delete_vote(voice: models.Voice):
    requests.get(
            f'https://api.telegram.org/bot{settings.MEME}/deleteMessage?chat_id={settings.MEME_CHANNEL}'
            f'&message_id={voice.message_id}'
    )


@sync_to_async
def check_voice(file_unique_id: str):
    if (target_voice := models.Voice.objects.filter(file_unique_id=file_unique_id, status='p')).exists():
        return target_voice.first()


def answer_callback_query(session: ClientSession) -> Callable:
    return answer_callback_query_closure(settings.MEME, session)


@sync_to_async
def get_delete(delete_id: int):
    try:
        return models.Delete.objects.get(delete_id=delete_id)
    except models.Delete.DoesNotExist:
        return None


@sync_to_async
def delete_target_voice(target_delete: models.Delete):
    target_delete.voice.delete()


def send_message(chat_id: int, text: str):
    encoded = urlencode({'chat_id': chat_id, 'text': text})
    requests.get(f'https://api.telegram.org/bot{settings.MEME}/sendMessage?{encoded}')


@sync_to_async
def count_users():
    return models.User.objects.count()


@sync_to_async
def get_delete_requests():
    return list(models.Delete.objects.all())
