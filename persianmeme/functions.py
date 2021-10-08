from django.conf import settings
from LilSholex import decorators
from LilSholex.functions import answer_callback_query as answer_callback_query_closure
from . import models
from requests import Session as RequestsSession
from .models import Broadcast
from .translations import user_messages
from asgiref.sync import sync_to_async
from aiohttp import ClientSession, TCPConnector, ClientError
from django.core.paginator import Paginator
import asyncio
from django import db
from .types import ObjectType
import json
from LilSholex.exceptions import TooManyRequests


def get_vote(file_unique_id):
    if (target_voice := models.Voice.objects.filter(
        file_unique_id=file_unique_id,
        status=models.Voice.Status.PENDING
    )).exists():
        return target_voice.first()


def get_voice(file_unique_id: str, voice_type=models.Voice.Type.NORMAL):
    if (target_voice := models.Voice.objects.filter(
        file_unique_id=file_unique_id,
        status=models.Voice.Status.ACTIVE,
        voice_type=voice_type
    )).exists():
        return target_voice.first()


def get_admin_voice(voice_id: int):
    try:
        return models.Voice.objects.get(id=voice_id)
    except (models.Voice.DoesNotExist, ValueError):
        return None


def count_voices():
    voices_count = models.Voice.objects.filter(status=models.Voice.Status.ACTIVE).count()
    return f'All voices count : {voices_count}'


def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


@decorators.sync_fix
def answer_inline_query(
        inline_query_id: str,
        results: str,
        next_offset: str,
        switch_pm_text: str,
        switch_pm_parameter: str,
        session: RequestsSession
):
    with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/answerInlineQuery',
        params={
            'results': results,
            'next_offset': next_offset,
            'switch_pm_text': switch_pm_text,
            'switch_pm_parameter': switch_pm_parameter,
            'inline_query_id': inline_query_id,
            'cache_time': 0
        },
        timeout=settings.REQUESTS_TIMEOUT
    ) as response:
        if response.status_code != 429:
            return
        raise TooManyRequests(response.json()['parameters']['retry_after'])


@decorators.sync_fix
def delete_vote_sync(message_id: int, session: RequestsSession = RequestsSession()):
    with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/deleteMessage',
        params={'chat_id': settings.MEME_CHANNEL, 'message_id': message_id},
        timeout=settings.REQUESTS_TIMEOUT
    ) as _:
        return


def check_voice(file_unique_id: str):
    target_voice = models.Voice.objects.filter(file_unique_id=file_unique_id, status=models.Voice.Status.PENDING)
    if target_voice.exists():
        return target_voice.first()


def answer_callback_query(session: RequestsSession):
    return answer_callback_query_closure(session, settings.MEME)


def get_delete(delete_id: int):
    try:
        return models.Delete.objects.get(delete_id=delete_id)
    except models.Delete.DoesNotExist:
        return None


@decorators.sync_fix
def send_message(chat_id: int, text: str, session: RequestsSession = RequestsSession()):
    with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/sendMessage',
        params={'chat_id': chat_id, 'text': text}
    ) as response:
        if response.status_code != 429:
            return
        raise TooManyRequests(response.json()['parameters']['retry_after'])


def accept_voice(file_unique_id: str):
    if (
            voice := models.Voice.objects.filter(file_unique_id=file_unique_id, status=models.Voice.Status.SEMI_ACTIVE)
    ).exists():
        voice = voice.first()
        voice.status = models.Voice.Status.ACTIVE
        voice.save()
        return True


@sync_to_async
def get_page(broadcast: models.Broadcast):
    db.close_old_connections()
    result = tuple(models.User.objects.filter(started=True).exclude(
        last_broadcast=broadcast
    )[:settings.PAGINATION_LIMIT])
    if result:
        models.User.objects.filter(
            user_id__gte=result[0].user_id, user_id__lte=result[-1].user_id, started=True
        ).update(last_broadcast=broadcast)
    return result


async def perform_broadcast(broadcast: Broadcast):
    from_chat_id = (await broadcast.get_sender).chat_id
    message_id = broadcast.message_id
    async with ClientSession(connector=TCPConnector(
            limit=settings.BROADCAST_CONNECTION_LIMIT
    )) as client:
        async def forwarder(chat_id: int):
            while True:
                try:
                    async with client.get(
                        f'https://api.telegram.org/bot{settings.MEME}/forwardMessage',
                        params={'from_chat_id': from_chat_id, 'chat_id': chat_id, 'message_id': message_id}
                    ) as request_result:
                        if request_result.status != 429:
                            break
                        await asyncio.sleep((await request_result.json())['parameters']['retry_after'])
                except (ClientError, asyncio.TimeoutError):
                    pass
        while result := await get_page(broadcast):
            first_index = 0
            for last_index in range(settings.BROADCAST_LIMIT, settings.PAGINATION_LIMIT + 1, settings.BROADCAST_LIMIT):
                await asyncio.gather(*[forwarder(user.chat_id) for user in result[first_index:last_index]])
                first_index = last_index
                await asyncio.sleep(0.7)


def make_like_result(voice):
    return {
        'type': 'voice',
        'id': voice[0],
        'voice_file_id': voice[1],
        'title': voice[2],
        'reply_markup': {'inline_keyboard': [
            [{'text': '👍', 'callback_data': f'up:{voice[0]}'},
             {'text': '👎', 'callback_data': f'down:{voice[0]}'}]
        ]}
    }


def make_result(voice):
    return {
        'type': 'voice',
        'id': voice[0],
        'voice_file_id': voice[1],
        'title': voice[2]
    }


def make_voice_result(voice: models.Voice):
    return {
        'type': 'voice',
        'id': voice.id,
        'voice_file_id': voice.file_id,
        'title': voice.name,
        'reply_markup': {'inline_keyboard': [
            [{'text': '👍', 'callback_data': f'up:{voice.id}'},
             {'text': '👎', 'callback_data': f'down:{voice.id}'}]
        ]}
    }


def make_voice_like_result(voice: models.Voice):
    return {
        'type': 'voice',
        'id': voice.id,
        'voice_file_id': voice.file_id,
        'title': voice.name
    }


def make_list_string(object_type: ObjectType, objs):
    if objs.exists():
        return '\n\n'.join([f'🔴 {index + 1} : {obj.name}' for index, obj in enumerate(objs)])
    return user_messages['no_playlist'] if object_type is ObjectType.PLAYLIST else user_messages['no_voice']


def paginate(objs, page: int):
    paginator = Paginator(objs, 9)
    if not paginator.num_pages:
        return (), None, None
    page = paginator.page(page) if page <= paginator.num_pages else paginator.page(paginator.num_pages)
    return (
        page.object_list,
        page.previous_page_number() if page.has_previous() else None,
        page.next_page_number() if page.has_next() else None
    )


def get_message(message_id: int):
    try:
        target_message = models.Message.objects.select_related('sender').get(
            id=message_id, status=models.Message.Status.PENDING
        )
    except models.Message.DoesNotExist:
        return False
    target_message.status = models.Message.Status.READ
    target_message.save()
    return target_message


def create_voice_list(voices: tuple):
    voices_str = str()
    for voice in voices:
        voices_str += f'⭕ {voice.name}\n'
    return voices_str


@decorators.sync_fix
def edit_message_reply_markup(
        chat_id: int,
        new_reply_markup: dict,
        message_id: int = None,
        inline_message_id: int = None,
        session: RequestsSession = RequestsSession()
):
    assert message_id is not None or inline_message_id is not None,\
        'You must at least provide message_id or inline_message_id !'
    params = {'chat_id': chat_id, 'reply_markup': json.dumps(new_reply_markup)}
    if message_id:
        params['message_id'] = message_id
    else:
        params['inline_message_id'] = inline_message_id
    with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/editMessageReplyMarkup',
        timeout=(settings.REQUESTS_TIMEOUT * 20),
        params=params
    ) as response:
        if response.status_code != 429:
            return
        raise TooManyRequests(response.json()['parameters']['retry_after'])
