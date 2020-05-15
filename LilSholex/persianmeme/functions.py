from persianmeme import models
import faster_than_requests as fast_req
from urllib.parse import urlencode
from django.conf import settings
from groupguard.decorators import fix


def get_voice(file_unique_id, voice_type='n'):
    return models.Voice.objects.filter(file_unique_id=file_unique_id, status='a', voice_type=voice_type)


def get_owner():
    return models.User.objects.get(rank='o')


def add_voice(file_id, file_unique_id, name, sender, status):
    if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type='n').exists():
        models.Voice.objects.create(
            file_id=file_id, file_unique_id=file_unique_id, name=name, sender=sender, status=status
        )
        return True
    return False


def count_voices():
    voices_count = models.Voice.objects.filter(status='a').count()
    return f'All voices count : {voices_count}'


def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


def get_admins():
    return models.User.objects.filter(rank__in=['a', 'o'])


@fix
def answer_inline_query(inline_query_id, results, next_offset, cache_time):
    encoded = urlencode({'results': results})
    fast_req.get(f'https://api.telegram.org/bot{settings.MEME}/answerInlineQuery?inline_query_id={inline_query_id}&'
                 f'{encoded}&next_offset={next_offset}&cache_time={cache_time}&is_personal=True')


def delete_voice(file_unique_id):
    models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type='n', status='a').delete()


@fix
def answer_callback_query(query_id, text, show_alert):
    encoded = urlencode({'text': text})
    fast_req.get(
        f'https://api.telegram.org/bot{settings.MEME}/answerCallbackQuery?callback_query_id={query_id}&{encoded}&'
        f'show_alert={show_alert}'
    )
