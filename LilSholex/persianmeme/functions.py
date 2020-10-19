from urllib.parse import urlencode
from django.conf import settings
from LilSholex.decorators import fix
from LilSholex.functions import answer_callback_query as answer_callback_query_closure
from . import models
import requests
import json
from .translations import user_messages
from .keyboards import bot


def get_voice(file_unique_id, voice_type='n'):
    target_voice = models.Voice.objects.filter(file_unique_id=file_unique_id, status='a', voice_type=voice_type)
    if target_voice.exists():
        return target_voice.first()


def get_owner():
    return models.User.objects.get(rank='o')


def add_voice(file_id, file_unique_id, name, sender, status):
    if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type='n').exists():
        return models.Voice.objects.create(
            file_id=file_id, file_unique_id=file_unique_id, name=name, sender=sender, status=status
        )


def count_voices():
    voices_count = models.Voice.objects.filter(status='a').count()
    return f'All voices count : {voices_count}'


def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


@fix
def answer_inline_query(inline_query_id: str, results: str, next_offset: str, cache_time: float):
    encoded = urlencode({'results': results})
    requests.get(
        f'https://api.telegram.org/bot{settings.MEME}/answerInlineQuery?inline_query_id={inline_query_id}&'
        f'{encoded}&next_offset={next_offset}&cache_time={cache_time}&is_personal=True'
    )


def delete_vote(voice: models.Voice):
    requests.get(
            f'https://api.telegram.org/bot{settings.MEME}/deleteMessage?chat_id={settings.MEME_CHANNEL}'
            f'&message_id={voice.message_id}'
    )


def check_voice(file_unique_id: str):
    target_voice = models.Voice.objects.filter(file_unique_id=file_unique_id, status='p')
    if target_voice.exists():
        return target_voice.first()


def answer_callback_query():
    return answer_callback_query_closure(settings.MEME)


def get_delete(delete_id: int):
    try:
        return models.Delete.objects.get(delete_id=delete_id)
    except models.Delete.DoesNotExist:
        return None


def delete_target_voice(target_delete: models.Delete):
    target_delete.voice.delete()


def send_message(chat_id: int, text: str):
    encoded = urlencode({'chat_id': chat_id, 'text': text})
    requests.get(f'https://api.telegram.org/bot{settings.MEME}/sendMessage?{encoded}')


def count_users():
    return models.User.objects.count()


def get_delete_requests():
    return models.Delete.objects.all()


def start_bot_first():
    return json.dumps([{
        'type': 'article',
        'id': 'error',
        'title': user_messages['start_bot_title'],
        'input_message_content': {'message_text': user_messages['start_bot']},
        'reply_markup': bot
    }])
