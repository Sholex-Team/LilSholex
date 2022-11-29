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
from random import randint


def get_voice(file_unique_id: str, visibility=models.Meme.Visibility.NORMAL):
    if (target_voice := models.Meme.objects.filter(
        file_unique_id=file_unique_id,
        status=models.Meme.Status.ACTIVE,
        visibility=visibility
    )).exists():
        return target_voice.first()


def get_admin_voice(voice_id: int):
    try:
        return models.Meme.objects.get(id=voice_id)
    except (models.Meme.DoesNotExist, ValueError):
        return None


def count_memes():
    return f'All memes count : {models.Meme.objects.filter(status=models.Meme.Status.ACTIVE).count()}'


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


def check_voice(file_unique_id: str):
    target_voice = models.Meme.objects.filter(file_unique_id=file_unique_id, status=models.Meme.Status.PENDING)
    if target_voice.exists():
        return target_voice.first()


def answer_callback_query(session: RequestsSession):
    return answer_callback_query_closure(session, settings.MEME)


def get_delete(delete_id: int):
    try:
        return models.Delete.objects.get(id=delete_id)
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
            voice := models.Meme.objects.filter(file_unique_id=file_unique_id, status=models.Meme.Status.SEMI_ACTIVE)
    ).exists():
        voice = voice.first()
        voice.status = models.Meme.Status.ACTIVE
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
                        f'https://api.telegram.org/bot{settings.MEME}/copyMessage',
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


def make_result(meme: list):
    temp_result = {
        'id': meme[0],
        'title': meme[2]
    }
    if meme[3] == models.MemeType.VIDEO:
        temp_result['type'] = 'video'
        temp_result['video_file_id'] = meme[1]
        temp_result['description'] = meme[4]
    else:
        temp_result['type'] = 'voice'
        temp_result['voice_file_id'] = meme[1]
    return temp_result


def make_like_result(meme: list):
    temp_result = make_result(meme)
    temp_result['reply_markup'] = {'inline_keyboard': [[
        {'text': '👍', 'callback_data': f'up:{meme[0]}'}, {'text': '👎', 'callback_data': f'down:{meme[0]}'}
    ]]}
    return temp_result


def make_meme_result(meme: models.Meme):
    temp_result = {
        'id': meme.id,
        'title': meme.name
    }
    if meme.type == models.MemeType.VIDEO:
        temp_result['type'] = 'video'
        temp_result['video_file_id'] = meme.file_id
        temp_result['description'] = meme.description
    else:
        temp_result['type'] = 'voice'
        temp_result['voice_file_id'] = meme.file_id
    return temp_result


def make_meme_like_result(meme: models.Meme):
    temp_result = make_meme_result(meme)
    temp_result['reply_markup'] = {'inline_keyboard': [[
        {'text': '👍', 'callback_data': f'up:{meme.id}'}, {'text': '👎', 'callback_data': f'down:{meme.id}'}
    ]]}
    return temp_result


def make_list_string(object_type: ObjectType, objs):
    if objs.exists():
        return '\n\n'.join([
            f'{"🔴" if object_type is ObjectType.PLAYLIST else ("🔊" if obj.type == models.MemeType.VOICE else "📹")}'
            f' {index + 1} : {obj.name}' for index, obj in enumerate(objs)
        ])
    match object_type:
        case ObjectType.PLAYLIST:
            return user_messages['no_playlist']
        case ObjectType.PLAYLIST_VOICE | ObjectType.PRIVATE_VOICE | ObjectType.SUGGESTED_VOICE:
            return user_messages['no_voice']
        case ObjectType.SUGGESTED_VIDEO:
            return user_messages['no_video']
        case ObjectType.SUGGESTED_MEME:
            return user_messages['empty_list']


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


def check_for_voice(message: dict):
    return 'voice' in message and (
            'mime_type' not in message['voice'] or message['voice']['mime_type'] == 'audio/ogg'
    )


def check_for_video(message: dict, bypass_limits: bool):
    return 'video' in message and (
        'mime_type' not in (video := message['video']) or video['mime_type'] == 'video/mp4'
    ) and (bypass_limits or (video['file_size'] <= settings.VIDEO_SIZE_LIMIT and
                             video['duration'] <= settings.VIDEO_DURATION_LIMIT))


def create_description(tags):
    return ', '.join([meme_tag.tag for meme_tag in tags])


def fake_deny_vote(queryset):
    if (user_count := models.User.objects.count()) < settings.MIN_FAKE_VOTE:
        fake_min = user_count
        fake_max = user_count
    else:
        fake_min = settings.MIN_FAKE_VOTE
        if user_count < settings.MAX_FAKE_VOTE:
            fake_max = user_count
        else:
            fake_max = settings.MAX_FAKE_VOTE
    faked_count = 0
    for meme in queryset:
        if meme.status == meme.Status.PENDING and \
                meme.deny_vote.count() < (random_fake := randint(fake_min, fake_max)):
            faked_count += 1
            meme.deny_vote.set(models.User.objects.all()[:random_fake])
    return faked_count
