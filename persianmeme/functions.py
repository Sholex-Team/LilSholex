from django.conf import settings
from LilSholex import decorators
from LilSholex.functions import answer_callback_query as answer_callback_query_closure
from . import models
import requests
import json
from uuid import uuid4
from .models import Broadcast
from .translations import user_messages
from .keyboards import bot
from asgiref.sync import sync_to_async
from aiohttp import ClientSession, TCPConnector, ClientError
from django.core.paginator import Paginator
import asyncio
from django import db
from .keyboards import numbers
from .types import ObjectType


@sync_to_async
def get_vote(file_unique_id):
    target_voice = models.Voice.objects.filter(
        file_unique_id=file_unique_id,
        status=models.Voice.Status.PENDING
    )
    if target_voice.exists():
        return target_voice.first()


@sync_to_async
def get_voice(file_unique_id, voice_type=models.Voice.Type.NORMAL):
    target_voice = models.Voice.objects.filter(
        file_unique_id=file_unique_id,
        status__in=models.PUBLIC_STATUS,
        voice_type=voice_type
    )
    if target_voice.exists():
        return target_voice.first()


@sync_to_async
def get_admin_voice(voice_id: int):
    try:
        return models.Voice.objects.get(voice_id=voice_id)
    except (models.Voice.DoesNotExist, ValueError):
        return None


@sync_to_async
def get_owner():
    return models.User.objects.get(rank='o')


@sync_to_async
def add_voice(file_id, file_unique_id, name, sender, status):
    if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type=models.Voice.Type.NORMAL).exists():
        return models.Voice.objects.create(
            file_id=file_id, file_unique_id=file_unique_id, name=name, sender=sender, status=status
        )


@sync_to_async
def count_voices():
    voices_count = models.Voice.objects.filter(status__in=models.PUBLIC_STATUS).count()
    return f'All voices count : {voices_count}'


@sync_to_async
def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


@decorators.async_fix
async def answer_inline_query(
        inline_query_id: str,
        results: str,
        next_offset: str,
        cache_time: float,
        is_personal: bool,
        session: ClientSession
):
    async with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/answerInlineQuery',
        params={
            'results': results,
            'next_offset': next_offset,
            'cache_time': cache_time,
            'is_personal': str(is_personal),
            'inline_query_id': inline_query_id
        }
    ) as _:
        return


@decorators.sync_fix
def delete_vote_sync(voice: models.Voice):
    requests.get(
        f'https://api.telegram.org/bot{settings.MEME}/deleteMessage',
        params={'chat_id': settings.MEME_CHANNEL, 'message_id': voice.message_id}
    )


@decorators.async_fix
async def delete_vote_async(message_id: int, session: ClientSession):
    async with session.get(
        f'https://api.telegram.org/bot{settings.MEME}/deleteMessage',
        params={'chat_id': settings.MEME_CHANNEL, 'message_id': message_id}
    ) as _:
        return


@sync_to_async
def check_voice(file_unique_id: str):
    target_voice = models.Voice.objects.filter(file_unique_id=file_unique_id, status=models.Voice.Type.PRIVATE)
    if target_voice.exists():
        return target_voice.first()


def answer_callback_query(session: ClientSession):
    return answer_callback_query_closure(session, settings.MEME)


@sync_to_async
def get_delete(delete_id: int):
    try:
        return models.Delete.objects.get(delete_id=delete_id)
    except models.Delete.DoesNotExist:
        return None


@sync_to_async
def delete_target_voice(target_delete: models.Delete):
    target_delete.voice.delete()


@decorators.sync_fix
def send_message(chat_id: int, text: str):
    requests.get(
        f'https://api.telegram.org/bot{settings.MEME}/sendMessage',
        params={'chat_id': chat_id, 'text': text}
    )


@sync_to_async
def count_users():
    return models.User.objects.count()


@sync_to_async
def get_delete_requests():
    return tuple(models.Delete.objects.all())


def start_bot_first():
    return json.dumps([{
        'type': 'article',
        'id': 'error',
        'title': user_messages['start_bot_title'],
        'input_message_content': {'message_text': user_messages['start_bot']},
        'reply_markup': bot
    }])


@sync_to_async
def get_all_accepted():
    return tuple(models.Voice.objects.filter(status=models.Voice.Status.SEMI_ACTIVE))


@sync_to_async
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
    async with ClientSession(connector=TCPConnector(limit=settings.BROADCAST_CONNECTION_LIMIT)) as client:
        async def forwarder(chat_id: int):
            while True:
                try:
                    async with client.get(
                            f'https://api.telegram.org/bot{settings.MEME}/forwardMessage',
                            params={'from_chat_id': from_chat_id, 'chat_id': chat_id, 'message_id': message_id}
                    ) as request_result:
                        if request_result.status != 429:
                            break
                except ClientError:
                    pass
                await asyncio.sleep(1)
        while result := await get_page(broadcast):
            first_index = 0
            for last_index in range(settings.BROADCAST_LIMIT, settings.PAGINATION_LIMIT + 1, settings.BROADCAST_LIMIT):
                await asyncio.gather(*[forwarder(user.chat_id) for user in result[first_index:last_index]])
                first_index = last_index
                await asyncio.sleep(1)


def make_like_result(voices, offset: int, limit: int):
    return [{
        'type': 'voice',
        'id': str(uuid4()),
        'voice_file_id': voice.file_id,
        'title': voice.name,
        'reply_markup': {'inline_keyboard': [
            [{'text': '👍', 'callback_data': f'up:{voice.voice_id}'},
             {'text': '👎', 'callback_data': f'down:{voice.voice_id}'}]
        ]}
    } for voice in voices[offset:offset + limit]]


def make_result(voices, offset: int, limit: int):
    return [{
        'type': 'voice',
        'id': str(uuid4()),
        'voice_file_id': voice.file_id,
        'title': voice.name
    } for voice in voices[offset:offset + limit]]


def make_list_string(object_type: ObjectType, objs: tuple):
    if objs:
        return '\n\n'.join([f'{numbers[index]} {obj.name}' for index, obj in enumerate(objs)])
    return user_messages['no_playlist'] if object_type is ObjectType.PLAYLIST else user_messages['no_voice']


def paginate(objs, page: int):
    paginator = Paginator(objs, 9)
    if not paginator.num_pages:
        return (), None, None
    page = paginator.page(page)
    return (
        tuple(page.object_list),
        page.previous_page_number() if page.has_previous() else None,
        page.next_page_number() if page.has_next() else None
    )


@sync_to_async
def get_contact_admin_messages():
    return tuple(models.Message.objects.select_related('sender').filter(status=models.Message.Status.PENDING))


@sync_to_async
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
