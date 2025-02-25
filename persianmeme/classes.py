import json
from asyncio import TaskGroup
from django.conf import settings
from LilSholex.decorators import async_fix
from datetime import datetime, timedelta
from .functions import (
    make_like_result,
    make_result,
    make_meme_result,
    make_meme_like_result,
    paginate,
    make_list_string,
    check_for_voice,
    check_for_video,
    create_description,
    clean_query,
    handle_message_params
)
from . import translations, models, steps, context as meme_context
from .keyboards import (
    report as report_keyboard,
    message as message_keyboard,
    manage_message,
    make_meme_list,
    per_back,
    admin,
    user as user_keyboard,
    meme_review
)
from .types import InvalidMemeTag, LongMemeTag, TooManyMemeTags, SearchType
from string import punctuation
from django.db.models import Q
from .types import ObjectType, ReportResult
from aiohttp import ClientSession
from .tasks import revoke_review
from LilSholex.exceptions import TooManyRequests
from typing import Any
from LilSholex.celery import celery_app
from LilSholex.functions import handle_request_exception
from asgiref.sync import sync_to_async
from django.db import transaction
from LilSholex.context import telegram as telegram_context


class User:
    __slots__ = ('_token', 'chat_id', 'session', '_base_params', 'database')
    _token: str
    session: ClientSession
    _base_params: dict[str, Any]
    database: models.User

    def __init__(self, instance: models.User = None):
        self._token = settings.MEME_TOKEN
        self.session = telegram_context.common.HTTP_SESSION.get()
        if instance:
            self.   database = instance
            self._set_base_params()

    def _set_base_params(self):
        self._base_params = {'chat_id': self.database.chat_id}

    async def set_database_instance(self):
        self.database = (await models.User.objects.aget_or_create(
            chat_id=telegram_context.common.USER_CHAT_ID.get()
        ))[0]
        self._set_base_params()

    @async_fix
    async def send_message(
            self,
            text: str,
            reply_markup: dict = None,
            reply_to_message_id: int | None = None,
            parse_mode: str | None = None,
            disable_web_page_preview: bool = True,
    ) -> int:
        message = {
            **self._base_params,
            'text': text,
            'disable_web_page_preview': str(disable_web_page_preview)
        }
        handle_message_params(message, reply_markup, reply_to_message_id, parse_mode)
        async with self.session.get(f'{settings.MEME_BASE_URL}sendMessage', params=message) as response:
            if response.status == 200:
                if (result := await response.json())['ok']:
                    return result['result']['message_id']
            elif response.status == 429:
                raise TooManyRequests((await response.json())['parameters']['retry_after'])
            return 0

    @async_fix
    async def delete_message(self) -> None:
        async with self.session.get(
            f'{settings.MEME_BASE_URL}deleteMessage',
            params={**self._base_params, 'message_id': telegram_context.common.MESSAGE_ID.get()}
        ) as response:
            return await handle_request_exception(response)

    @async_fix
    async def edit_message_text(self, text: str, inline_keyboard: dict = str()):
        if inline_keyboard:
            inline_keyboard = json.dumps(inline_keyboard)
        async with self.session.get(
            f'{settings.MEME_BASE_URL}editMessageText',
            params={
                **self._base_params,
                'message_id': telegram_context.common.MESSAGE_ID.get(),
                'text': text,
                'reply_markup': inline_keyboard
            }
        ) as response:
            return await handle_request_exception(response)

    @async_fix
    async def send_animation(
            self,
            animation: str,
            caption: str = str(),
            reply_markup: dict | None = None,
            reply_to_message_id: int | None = None,
            parse_mode: str | None = None
    ):
        message = {**self._base_params, 'animation': animation, 'caption': caption}
        handle_message_params(message, reply_markup, reply_to_message_id, parse_mode)
        async with self.session.get(f'{settings.MEME_BASE_URL}sendAnimation', params=message) as response:
            return await handle_request_exception(response)

    @async_fix
    async def pin_chat_message(self, chat_id: int, message_id: int):
        async with self.session.get(
            f'{settings.MEME_BASE_URL}pinChatMessage',
            params={'chat_id': chat_id, 'message_id': message_id}
        ) as response:
            return await handle_request_exception(response)

    @async_fix
    async def unpin_chat_message(self, chat_id: int):
        async with self.session.get(
            f'{settings.MEME_BASE_URL}unpinChatMessage',
            params={'chat_id': chat_id, 'message_id': telegram_context.common.MESSAGE_ID.get()}
        ) as response:
            return await handle_request_exception(response)

    async def broadcast(self, message_id: int):
        return (await models.Broadcast.objects.acreate(sender=self.database, message_id=message_id)).id

    async def delete_current_meme(self):
        async with TaskGroup() as tg:
            tg.create_task(self.send_message(translations.admin_messages['deleted']))
            tg.create_task(self.database.current_meme.adelete(admin=self.database, log=True))

    async def delete_meme(self, file_unique_id, meme_type: models.MemeType):
        if await (result := models.Meme.objects.filter(
            file_unique_id=file_unique_id,
            visibility=models.Meme.Visibility.NORMAL,
            status=models.Meme.Status.ACTIVE,
            type=meme_type
        )).aexists():
            target_meme = await result.afirst()
            target_meme.review_admin = self.database
            await target_meme.adelete(admin=self.database, log=True)

    async def cancel_voting(self, meme_type: models.MemeType):
        if not await (pending_memes := models.Meme.objects.filter(
                sender=self.database, status=models.Meme.Status.PENDING, type=meme_type
        )).aexists():
            await self.send_message(translations.user_messages['no_voting'].format(
                translations.user_messages['any_video' if meme_type == models.MemeType.VIDEO else 'any_voice']
            ))
            return
        async with TaskGroup() as tg:
            async for pending_meme in pending_memes:
                tg.create_task(pending_meme.delete_vote())
                tg.create_task(pending_meme.adelete())
            tg.create_task(self.send_message(translations.user_messages['voting_canceled'].format(
                translations.user_messages['voice' if meme_type == models.MemeType.VOICE else 'video']
            )))

    @async_fix
    async def send_current_meme(self, reply_markup: dict | None = None, reply_to_message_id: int | None = None):
        message = {'caption': self.database.current_meme.name}
        handle_message_params(message, reply_markup, reply_to_message_id)
        if self.database.current_meme.type == models.MemeType.VOICE:
            meme_method = 'Voice'
            message['voice'] = self.database.current_meme.file_id
        else:
            meme_method = 'Video'
            message['video'] = self.database.current_meme.file_id
        async with self.session.get(
            f'{settings.MEME_BASE_URL}send{meme_method}',
            params={**self._base_params, **message}
        ) as response:
            return await handle_request_exception(response)

    @async_fix
    async def copy_message(
            self,
            message_id: int,
            reply_markup: dict | None = None,
            from_chat_id: int = None,
            chat_id: int = None,
            protect_content: bool = False
    ):
        assert (chat_id and not from_chat_id) or (from_chat_id and not chat_id), \
            'You must use a chat_id or a from_chat_id !'
        base_param = {'message_id': message_id, 'protect_content': str(protect_content)}
        if reply_markup:
            base_param['reply_markup'] = json.dumps(reply_markup)
        async with self.session.get(
            f'{settings.MEME_BASE_URL}copyMessage',
            params={
                'from_chat_id': self.database.chat_id,
                'chat_id': chat_id,
                **base_param
            } if not from_chat_id else {'from_chat_id': from_chat_id, 'chat_id': self.database.chat_id, **base_param}
        ) as response:
            if response.status == 200:
                if (result := await response.json())['ok']:
                    return result['result']['message_id']
            elif response.status == 429:
                raise TooManyRequests((await response.json())['parameters']['retry_after'])
            return False


    def _get_recent_memes(self, meme_type: models.User.SearchItems):
        query = Q(user=self.database, meme__status=models.Meme.Status.ACTIVE)
        if meme_type != models.User.SearchItems.BOTH:
            query &= Q(meme__type=meme_type)
        return models.RecentMeme.objects.filter(query).select_related('meme').values_list(
            'meme__id', 'meme__file_id', 'meme__name', 'meme__type', 'meme__description'
        )

    def _search_memes(
            self, search_type: SearchType, meme_type: models.User.SearchItems, query: str, begin: int, remaining: int
    ):
        base_query = ('SELECT id, file_id, name, type, description FROM persianmeme_newmeme WHERE '
                      '((status=%s AND visibility=%s) OR (sender_id=%s AND visibility=%s)) AND ')
        params = [
            models.NewMeme.Status.ACTIVE.value,
            models.NewMeme.Visibility.NORMAL.value,
            self.database.user_id,
            models.NewMeme.Visibility.PRIVATE.value
        ]
        if meme_type != models.User.SearchItems.BOTH:
            base_query += 'type=%s AND '
            params.append(meme_type.value)
        match search_type:
            case SearchType.NAMES:
                base_query += '(MATCH (name) AGAINST (%s IN BOOLEAN MODE)) '
                params.append('+' + ' +'.join(query.split()) + '*')
            case SearchType.TAGS:
                base_query += '(MATCH (tags) AGAINST (%s IN BOOLEAN MODE)) '
                params.append('* '.join(query.split()) + '*')
            case _:
                base_query += ('(MATCH (name) AGAINST (%s IN BOOLEAN MODE) OR '
                               'MATCH (tags) AGAINST (%s IN BOOLEAN MODE)) ')
                params.append(param := '+' + ' +'.join(query.split()) + '*')
                params.append(param)
        base_query += 'LIMIT %s OFFSET %s'
        params.append(remaining)
        params.append(begin)
        return models.NewMeme.objects.raw(base_query, params)

    async def get_memes(self, query: str, offset: str, caption: str | None):
        if query.startswith(settings.ID_KEY) and (target_voice_id := query[3:].strip()).isdigit():
            result_maker = make_meme_like_result if self.database.vote else make_meme_result
            try:
                return ([result_maker(await models.NewMeme.objects.aget(
                    Q(id=target_voice_id) & ((Q(visibility=models.NewMeme.Visibility.PRIVATE)
                                              & Q(sender=self.database))
                                             | Q(visibility=models.NewMeme.Visibility.NORMAL)) &
                    Q(status=models.NewMeme.Status.ACTIVE)), caption)], str())
            except (models.NewMeme.DoesNotExist, ValueError):
                return list(), str()
        if query.startswith(settings.NAMES_KEY):
            query = query[len(settings.NAMES_KEY):]
            search_type = SearchType.NAMES
        elif query.startswith(settings.TAGS_KEY):
            query = query[len(settings.TAGS_KEY):]
            search_type = SearchType.TAGS
        else:
            search_type = SearchType.ALL
        if query.startswith(settings.VIDEOS_KEY):
            query = query[len(settings.VIDEOS_KEY):]
            meme_type = models.User.SearchItems.VIDEOS
        elif query.startswith(settings.VOICES_KEY):
            query = query[len(settings.VOICES_KEY):]
            meme_type = models.User.SearchItems.VOICES
        else:
            meme_type = models.User.SearchItems(self.database.search_items)
        query = clean_query(query)
        result_sets = (
            lambda begin, remaining_memes: (
                self._get_recent_memes(meme_type)[begin:begin + remaining_memes]
                if not query and self.database.use_recent_memes else None
            ),
            lambda begin, remaining_memes: (
                models.NewMeme.objects.values_list('id', 'file_id', 'name', 'type', 'description').filter(
                    ((Q(status=models.NewMeme.Status.ACTIVE) & Q(visibility=models.NewMeme.Visibility.NORMAL)) |
                     (Q(sender=self.database) & Q(visibility=models.NewMeme.Visibility.PRIVATE))) &
                    (Q(type=meme_type) if meme_type != models.User.SearchItems.BOTH else Q())
                ).order_by(self.database.meme_ordering)[begin:begin + remaining_memes]
                if not query else self._search_memes(search_type, meme_type, query, begin, remaining_memes)
            )
        )
        if len(splinted_offset := offset.split(':')) != len(result_sets):
            splinted_offset = [0] * len(result_sets)
        results = []
        results_set = set()
        remaining = 50
        for result, current_offset in zip(result_sets, range(len(result_sets))):
            if (offset_value := splinted_offset[current_offset]) == 'e':
                continue
            splinted_offset[current_offset] = offset_value = int(offset_value)
            if (current_result := result(offset_value, remaining)) is None:
                splinted_offset[current_offset] = 'e'
                continue
            new_results = 0
            if query:
                result_maker = make_meme_like_result if self.database.vote else make_meme_result
                async for meme in current_result:
                    results_set.add(meme.id)
                    results.append(result_maker(meme, caption))
                    new_results += 1
            else:
                result_maker = make_like_result if self.database.vote else make_result
                async for meme in current_result:
                    if meme[0] in results_set:
                        continue
                    results_set.add(meme[0])
                    results.append(result_maker(meme, caption))
                    new_results += 1
            if not new_results:
                splinted_offset[current_offset] = 'e'
            else:
                splinted_offset[current_offset] += len(current_result)
            remaining -= new_results
            if not remaining:
                break
        return results, ':'.join(map(lambda item: str(item), splinted_offset))

    async def delete_request(self):
        await models.Delete.objects.acreate(meme=meme_context.common.MEME.get(), user=self.database)

    @async_fix
    async def get_chat(self):
        async with self.session.get( f'{settings.MEME_BASE_URL}getChat', params=self._base_params) as response:
            if response.status == 200:
                return (await response.json()).get('result')
            elif response.status == 429:
                raise TooManyRequests((await response.json())['parameters']['retry_after'])
            return {}

    async def set_username(self):
        if username := (await self.get_chat()).get('username'):
            await self.database.usernames.aget_or_create(username=username.lower())

    @sync_to_async
    def _like_meme(self, target_meme: models.Meme):
        with transaction.atomic():
            target_meme.deny_vote.remove(self.database)
            target_meme.accept_vote.add(self.database)

    async def like_meme(self, target_meme: models.Meme):
        if await target_meme.accept_vote.acontains(self.database):
            return False
        await self._like_meme(target_meme)
        return True

    @sync_to_async
    def _dislike_meme(self, target_meme: models.Meme):
        with transaction.atomic():
            target_meme.accept_vote.remove(self.database)
            target_meme.deny_vote.add(self.database)

    async def dislike_meme(self, target_meme: models.Meme):
        if await target_meme.deny_vote.acontains(self.database):
            return False
        await self._dislike_meme(target_meme)
        return True

    @sync_to_async
    def add_voter(self, meme: models.Meme):
        meme.voters.add(self.database)

    @sync_to_async
    def remove_voter(self, meme: models.Meme):
        meme.voters.remove(self.database)

    @property
    async def private_voices_count(self):
        return await models.Meme.objects.filter(
            visibility=models.Meme.Visibility.PRIVATE, sender=self.database
        ).acount()

    async def get_private_voice(self):
        return await models.Meme.objects.aget(
            id=meme_context.common.MEME_ID.get(),
            visibility=models.Meme.Visibility.PRIVATE,
            sender=self.database,
            type=models.MemeType.VOICE
        )

    async def get_suggested_meme(self, meme_type: models.MemeType):
        return await models.Meme.objects.aget(
            id=meme_context.common.MEME_ID.get(),
            status=models.Meme.Status.ACTIVE,
            visibility=models.Meme.Visibility.NORMAL,
            sender=self.database,
            type=meme_type
        )

    async def delete_owned_meme(self):
        if self.database.current_meme.sender_id == self.database.user_id:
            await self.database.current_meme.adelete()
            return True
        return False

    async def _check_meme_existence(self, file_unique_id: str):
        return await models.Meme.objects.filter(
            Q(visibility=models.Meme.Visibility.NORMAL) |
            (Q(visibility=models.Meme.Visibility.PRIVATE) & Q(sender=self.database)),
            file_unique_id=file_unique_id
        ).aexists()

    async def create_private_voice(self):
        message: dict = telegram_context.message.MESSAGE.get()
        if await self._check_meme_existence(message['voice']['file_unique_id']):
            await self.send_message(
                self.translate('meme_already_exists'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
            return False
        await models.Meme.objects.acreate(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status=models.Meme.Status.ACTIVE,
            visibility=models.Meme.Visibility.PRIVATE,
            sender=self.database,
            name=self.database.temp_meme_name,
            tags=self.database.temp_meme_tags
        )
        self.database.temp_meme_tags = None
        return True

    @property
    def _back_menu(self):
        try:
            if self.database.menu_mode != self.database.MenuMode.USER:
                return steps.admin_steps[self.database.back_menu]
            return steps.user_steps[self.database.back_menu]
        except KeyError:
            if self.database.menu_mode != self.database.MenuMode.USER:
                return steps.admin_steps['main']
            return steps.user_steps['main']

    def __perform_back_callback(self, callback: str):
        if callback:
            return getattr(self, callback)()

    async def go_back(self):
        step = self._back_menu
        self.database.menu = step['menu']
        self.database.back_menu = step.get('before')
        self.__perform_back_callback(step.get('callback'))
        async with TaskGroup() as tg:
            tg.create_task(self.database.asave())
            tg.create_task(self.send_message(step['message'], step.get('keyboard')))

    @async_fix
    async def upload_voice(self):
        now = datetime.now()
        if self.database.started and self.database.last_start and \
                (now - self.database.last_start) <= timedelta(seconds=18000):
            return
        async with self.session.get(
            f'{settings.MEME_BASE_URL}sendChatAction', params={**self._base_params, 'action': 'upload_voice'}
        ) as response:
            if response.status == 429:
                raise TooManyRequests((await response.json())['parameters']['retry_after'])
            self.database.started = response.status == 200
            if self.database.started:
                self.database.last_start = now
            return

    async def voice_exists(self):
        if check_for_voice():
            return True
        await self.send_message(self.translate('send_a_meme', self.translate('voice')))

    @sync_to_async
    def get_playlists(self):
        return paginate(models.Playlist.objects.filter(creator=self.database))

    @sync_to_async
    def get_playlist_voices(self):
        return paginate(self.database.current_playlist.voices.all())

    @sync_to_async
    def get_private_voices(self):
        return paginate(models.Meme.objects.filter(sender=self.database, visibility=models.Meme.Visibility.PRIVATE))

    async def create_playlist(self):
        return await models.Playlist.objects.acreate(name=telegram_context.message.TEXT.get(), creator=self.database)

    @sync_to_async
    def join_playlist(self, playlist_id: str):
        try:
            playlist = models.Playlist.objects.get(invite_link=playlist_id)
        except models.Playlist.DoesNotExist:
            return False
        if playlist.creator == self.database or self.database.playlists.contains(playlist):
            return False
        self.database.playlists.add(playlist)
        return playlist

    @sync_to_async
    def add_voice_to_playlist(self):
        if (first_voice := models.Meme.objects.filter(
            file_unique_id=telegram_context.message.MESSAGE.get()['voice']['file_unique_id'],
            sender=self.database,
            visibility=models.Meme.Visibility.PRIVATE,
            type=models.MemeType.VOICE
        ).first()) and not self.database.current_playlist.voices.contains(first_voice):
            self.database.current_playlist.voices.add(first_voice)
            return True
        return False

    @sync_to_async
    def remove_voice_from_playlist(self):
        if self.database.current_playlist.voices.contains(self.database.current_meme):
            self.database.current_playlist.voices.remove(self.database.current_meme)
            return True
        return False

    async def get_vote(self):
        message: dict = telegram_context.message.MESSAGE.get()
        if matched := check_for_voice():
            target_vote = models.Meme.objects.filter(
                file_unique_id=message['voice']['file_unique_id'],
                status=models.Meme.Status.PENDING,
                type=models.MemeType.VOICE
            )
        elif matched := check_for_video(True):
            target_vote = models.Meme.objects.filter(
                file_unique_id=message['video']['file_unique_id'],
                status=models.Meme.Status.PENDING,
                type=models.MemeType.VIDEO
            )
        if matched and (first_vote := await target_vote.select_related('sender').afirst()):
            return first_vote
        await self.send_message(
            self.translate('unknown_meme'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )

    @property
    async def sent_message(self):
        return await models.Message.objects.filter(sender=self.database, status=models.Message.Status.PENDING).aexists()

    async def contact_admin(self):
        if new_message_id := await self.copy_message(
            telegram_context.common.MESSAGE_ID.get(),
            message_keyboard(self.database.chat_id),
            chat_id=settings.MEME_MESSAGES
        ):
            await models.Message.objects.acreate(sender=self.database, message_id=new_message_id)

    async def send_messages(self):
        if await (
            messages := models.Message.objects.select_related('sender').filter(status=models.Message.Status.PENDING)
        ).aexists():
            async for message in messages:
                await self.copy_message(
                    message.message_id, manage_message(message), from_chat_id=settings.MEME_MESSAGES
                )
            await self.send_message(self.translate('messages'))
            return
        await self.send_message(self.translate('no_message'))

    def translate(self, key: str, *formatting_args):
        return translations.user_messages[key].format(*formatting_args) \
            if self.database.rank == self.database.Rank.USER or \
            self.database.menu_mode == self.database.MenuMode.USER else \
            translations.admin_messages[key].format(*formatting_args)

    async def process_meme_tags(self):
        if not (tags := telegram_context.message.TEXT.get()):
            await self.send_message(self.translate('send_meme_tags', self.temp_meme_translation))
            return False
        try:
            if 'tags:' in tags:
                raise InvalidMemeTag()
            if len(tags) >= len(punctuation):
                if any(char in tags for char in punctuation):
                    raise InvalidMemeTag()
            else:
                if any(char in punctuation for char in tags):
                    raise InvalidMemeTag()
            split_tags = list()
            for tag in tags.split('\n'):
                if not (stripped_tag := tag.strip()):
                    continue
                if len(stripped_tag) > settings.MAX_TAG_LENGTH:
                    raise LongMemeTag()
                split_tags.append(stripped_tag)
            if not split_tags or len(split_tags) > 6:
                raise TooManyMemeTags()
            self.database.temp_meme_tags = '\n'.join(split_tags)
        except ValueError as e:
            await self.send_message(self.translate(str(e), self.temp_meme_translation))
            return False
        return True

    def clear_temp_meme_tags(self):
        self.database.temp_meme_tags = None

    def clear_temp_meme_type(self):
        self.database.temp_meme_type = None

    async def initial_meme_check(self, meme_type: models.MemeType or int):
        message: dict = telegram_context.message.MESSAGE.get()
        if meme_type == models.MemeType.VOICE:
            if not await self.voice_exists():
                return False
            initial_check_result = message['voice']['file_id'], message['voice']['file_unique_id']
        else:
            if not check_for_video(self.database.rank in models.HIGH_LEVEL_ADMINS):
                await self.send_message(self.translate('send_a_meme', self.translate('video')))
                return False
            initial_check_result = message['video']['file_id'], message['video']['file_unique_id']
        if await self._check_meme_existence(initial_check_result[1]):
            await self.send_message(self.translate('meme_already_exists'))
            return False
        return initial_check_result

    async def edit_meme_file(self):
        if not (initial_check_result := await self.initial_meme_check(self.database.current_meme.type)):
            return False
        current_meme = await self.get_current_meme()
        current_meme.file_id, current_meme.file_unique_id = initial_check_result
        await current_meme.asave(update_fields=('file_id', 'file_unique_id'))
        return True

    async def add_meme(self, status: models.Meme.Status):
        if not (initial_check_result := await self.initial_meme_check(self.database.temp_meme_type)):
            return False
        new_meme = await models.Meme.objects.acreate(
            file_id=initial_check_result[0],
            file_unique_id=initial_check_result[1],
            name=self.database.temp_meme_name,
            sender=self.database,
            status=status,
            type=self.database.temp_meme_type,
            tags=self.database.temp_meme_tags,
            description=create_description(self.database.temp_meme_tags) if
            self.database.temp_meme_type == models.MemeType.VIDEO and self.database.temp_meme_tags else None
        )
        self.database.temp_meme_tags = None
        return new_meme

    async def validate_meme_name(self, meme_type: models.MemeType or int):
        message: dict = telegram_context.message.MESSAGE.get()
        text: str = telegram_context.message.TEXT.get()
        if (not text or
                message.get('entities') or len(text) > 80 or
                any(text.startswith(word) for word in settings.SENSITIVE_WORDS)):
            await self.send_message(
                self.translate('invalid_meme_name', self.translate(
                    'voice' if meme_type == models.MemeType.VOICE else 'video'
                )),
                reply_to_message_id=message['message_id']
            )
            return False
        return True

    async def validate_meme_description(self):
        if not (text := telegram_context.message.TEXT.get()) or len(text) > 120:
            await self.send_message(self.translate(
                'invalid_meme_description',
                self.translate('voice' if self.database.current_meme.type == models.MemeType.VOICE else 'video')
            ), reply_to_message_id=telegram_context.common.MESSAGE_ID.get())
            return False
        return True

    async def get_public_meme(self):
        message: dict = telegram_context.message.MESSAGE.get()
        if matched := check_for_video(True):
            file_unique_id = message['video']['file_unique_id']
            meme_type = models.MemeType.VIDEO
            meme_translation = self.translate('video')
        elif matched := check_for_voice():
            file_unique_id = message['voice']['file_unique_id']
            meme_type = models.MemeType.VOICE
            meme_translation = self.translate('voice')
        if matched:
            if target_voice := await models.Meme.objects.filter(
                file_unique_id=file_unique_id,
                type=meme_type,
                status=models.Meme.Status.ACTIVE,
                visibility=models.Meme.Visibility.NORMAL
            ).afirst():
                return target_voice
            await self.send_message(self.translate('meme_not_found', meme_translation))
            return None
        return False

    def clear_current_playlist(self):
        self.database.current_playlist = None

    def clear_current_meme(self):
        self.database.current_meme = None

    def menu_cleanup(self):
        self.__perform_back_callback(self._back_menu.get('callback'))

    @sync_to_async
    def add_recent_meme(self, meme: models.Meme):
        self.database.recent_memes.remove(meme)
        self.database.recent_memes.add(meme)
        if extra_memes := tuple(models.RecentMeme.objects.filter(
            user=self.database
        ).order_by('-id')[20:].values_list('id', flat=True)):
            models.RecentMeme.objects.filter(id__in=extra_memes).delete()

    async def send_ordered_meme_list(self, ordering: models.User.Ordering):
        ordered_memes = models.Meme.objects.filter(
            status=models.Meme.Status.ACTIVE, visibility=models.Meme.Visibility.NORMAL
        ).order_by(ordering)[:12]
        async with TaskGroup() as tg:
            string_list = tg.create_task(make_list_string(ObjectType.SUGGESTED_MEME, ordered_memes))
            keyboard_list = tg.create_task(make_meme_list(ordered_memes))
        return await self.send_message(string_list.result(), keyboard_list.result())

    @sync_to_async
    def clear_recent_memes(self):
        self.database.recent_memes.clear()

    async def suggest_meme(self, meme_type: models.MemeType):
        if await models.Meme.objects.filter(
            Q(status=models.Meme.Status.PENDING) |
            Q(status=models.Meme.Status.REPORTED, report_meme__status=models.Report.Status.PENDING),
            sender=self.database,
            type=meme_type
        ).aexists():
            return await self.send_message(self.translate('pending_meme', self.translate(
                'voice' if meme_type == models.MemeType.VOICE else 'video'
            )))
        if meme_type == models.MemeType.VOICE:
            self.database.back_menu = 'voice_suggestions'
            meme_translation = self.translate('voice')
        else:
            self.database.back_menu = 'video_suggestions'
            meme_translation = self.translate('video')
        self.database.menu = self.database.Menu.USER_SUGGEST_MEME_NAME
        self.database.temp_meme_type = meme_type
        return await self.send_message(self.translate('meme_name', meme_translation), per_back)

    @sync_to_async
    def get_suggestions(self, meme_type: models.MemeType):
        return paginate(models.Meme.objects.filter(
            sender=self.database, visibility=models.Meme.Visibility.NORMAL, type=meme_type
        ).exclude(status=models.Meme.Status.PENDING))

    async def start(self):
        self.menu_cleanup()
        if self.database.rank == self.database.Rank.USER or self.database.menu_mode == self.database.MenuMode.USER:
            self.database.menu = self.database.Menu.USER_MAIN
            self.database.menu_mode = self.database.MenuMode.USER
            return await self.send_message(self.translate('welcome'), user_keyboard)
        self.database.menu = self.database.Menu.ADMIN_MAIN
        return await self.send_message(self.translate('welcome'), admin)

    async def check_current_meme(self):
        if not await self.get_current_meme():
            async with TaskGroup() as tg:
                tg.create_task(self.send_message(self.translate('meme_not_accessible')))
                tg.create_task(self.go_back())
            return False
        return True

    async def check_current_playlist(self):
        if not await self.get_current_playlist():
            async with TaskGroup() as tg:
                tg.create_task(self.send_message(self.translate('playlist_not_accessible')))
                tg.create_task(self.go_back())
            return False
        return True

    async def assign_meme(self):
        meme_query = Q(reviewed=False, visibility=models.Meme.Visibility.NORMAL, status=models.Meme.Status.ACTIVE)
        if self.database.current_meme_id:
            meme_query &= Q(id__gt=self.database.current_meme_id)
        if self.database.temp_meme_type is not None:
            meme_query &= Q(type=self.database.temp_meme_type)
        if assigned_meme := await models.Meme.objects.filter(
            meme_query, review_admin=self.database
        ).order_by('id').afirst():
            self.database.current_meme = assigned_meme
        elif new_meme := await models.Meme.objects.filter(meme_query, review_admin=None).order_by('id').afirst():
            self.database.current_meme = new_meme
            self.database.current_meme.review_admin = self.database
            self.database.current_meme.task_id = revoke_review.apply_async(
                (self.database.current_meme.id,), countdown=settings.REVOKE_REVIEW_COUNTDOWN
            )
            await self.database.current_meme.asave(update_fields=('review_admin', 'task_id'))
        else:
            await self.send_message(translations.admin_messages['no_meme_to_review'])
            return False
        await self.send_message(
            translations.admin_messages['review_the_meme'],
            meme_review,
            await self.database.current_meme.send_meme(
                self.database.chat_id,
                extra_text=self.database.current_meme.description_text
            )
        )
        return True

    @property
    def current_meme_translation(self):
        return self.translate(self.database.current_meme.type_string)

    @property
    def temp_meme_translation(self):
        return self.translate('voice' if self.database.temp_meme_type == models.MemeType.VOICE else 'video')

    async def review_current_meme(self):
        self.database.current_meme.reviewed = True
        async with TaskGroup() as tg:
            tg.create_task(self.database.current_meme.asave(update_fields=('reviewed',)))
            tg.create_task(
                self.send_message(self.translate('reviewed', self.current_meme_translation))
            )

    async def report_meme(self, meme: models.Meme):
        report, created = await models.Report.objects.select_related('meme').aget_or_create(
            meme__id=meme.id, defaults={'meme': meme}
        )
        if report.status == models.Report.Status.REVIEWED:
            return ReportResult.REPORT_FAILED
        if created or not await report.reporters.filter(user_id=self.database.user_id).aexists():
            async with TaskGroup() as tg:
                tg.create_task(sync_to_async(report.reporters.add)(self.database))
                if created:
                    if message_id := await report.meme.send_meme(
                        settings.MEME_REPORTS_CHANNEL, report_keyboard(report.meme.id)
                    ):
                        tg.create_task(self.pin_chat_message(settings.MEME_REPORTS_CHANNEL, message_id))
            if await report.reporters.acount() == settings.VIOLATION_REPORT_LIMIT:
                async with TaskGroup() as tg:
                    if report.meme.status == models.Meme.Status.PENDING:
                        tg.create_task(report.meme.delete_vote())
                    report.meme.previous_status = report.meme.status
                    report.meme.status = models.Meme.Status.REPORTED
                    tg.create_task(report.meme.asave(update_fields=('previous_status', 'status')))
            return ReportResult.REPORTED
        return ReportResult.REPORTED_BEFORE

    @sync_to_async
    def edit_meme_tags(self):
        self.database.current_meme.tags = self.database.temp_meme_tags
        self.database.temp_meme_tags = None

    @property
    async def unreviewed_memes_count(self) -> tuple[int, int, int]:
        base_query = Q(visibility=models.Meme.Visibility.NORMAL, status=models.Meme.Status.ACTIVE, reviewed=False)
        async with TaskGroup() as tg:
            total_count = tg.create_task(models.Meme.objects.filter(base_query).acount())
            video_count = tg.create_task(
                models.Meme.objects.filter(base_query, type=models.MemeType.VIDEO).acount()
            )
            voice_count = tg.create_task(
                models.Meme.objects.filter(base_query, type=models.MemeType.VOICE).acount()
            )
        return total_count.result(), video_count.result(), voice_count.result()

    async def revoke_current_review(self):
        celery_app.control.revoke(self.database.current_meme.task_id)
        self.database.current_meme.review_admin = None
        await self.database.current_meme.asave(update_fields=('review_admin',))

    @sync_to_async
    def get_current_playlist(self):
        return self.database.current_playlist

    @sync_to_async
    def get_current_meme(self):
        return self.database.current_meme

    @sync_to_async
    def get_playlist_member_count(self):
        return self.database.current_playlist.users.count()
