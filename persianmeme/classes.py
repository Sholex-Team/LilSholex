import json
from django.conf import settings
from LilSholex.decorators import async_fix
from LilSholex.classes import Base
from asgiref.sync import sync_to_async
from aiohttp import ClientSession
from datetime import datetime, timedelta
from LilSholex.functions import filter_object
from persianmeme.functions import (
    make_like_result,
    make_result,
    paginate,
    get_vote,
    delete_vote_async,
    get_contact_admin_messages,
    get_voice
)
from enum import Enum
from . import translations, models, steps
from typing import Union
from .keyboards import message as message_keyboard, manage_message
from .types import InvalidVoiceTag, LongVoiceTag, TooManyVoiceTags
from string import punctuation
from itertools import combinations
from django.db.models import Q, Case, When, BooleanField
from asyncio import iscoroutinefunction


class User(Base):
    _BASE_URL = f'https://api.telegram.org/bot{settings.MEME}/'
    __ads: tuple
    __enforced_rank: Union[models.User.Rank, None]
    __is_inline: bool

    class Mode(Enum):
        NORMAL = 0
        SEND_AD = 1

    def __init__(
            self,
            session: ClientSession,
            mode: Mode,
            chat_id: int = None,
            instance: models.User = None,
            is_inline: bool = False
    ):
        self.__mode = mode
        self.__is_inline = is_inline
        super().__init__(settings.MEME, chat_id, instance, session)

    def __await__(self):
        yield from super().__await__()
        self.__enforced_rank = self.database.rank if self.__is_inline else None
        return self

    @sync_to_async
    def broadcast(self, message_id: int):
        models.Broadcast.objects.create(sender=self.database, message_id=message_id)

    @sync_to_async
    def get_user(self):
        result = models.User.objects.get_or_create(chat_id=self.chat_id)
        if self.__mode == self.Mode.SEND_AD:
            self.__ads = tuple(models.Ad.objects.exclude(seen=result[0]))
        return result

    @sync_to_async
    def delete_semi_active(self, file_unique_id: str):
        if result := filter_object(
            models.Voice.objects,
            True,
            file_unique_id=file_unique_id,
            status=models.Voice.Status.SEMI_ACTIVE
        ):
            result.delete(admin=self.database)
            return True
        return False

    @sync_to_async
    def delete_voice(self, file_unique_id):
        if result := filter_object(
            models.Voice.objects,
            True,
            file_unique_id=file_unique_id,
            voice_type=models.Voice.Type.NORMAL,
            status__in=models.PUBLIC_STATUS
        ):
            result.delete(admin=self.database)

    @sync_to_async
    def __delete_voting(self, file_unique_id: str):
        if result := filter_object(
            models.Voice.objects,
            True,
            file_unique_id=file_unique_id,
            voice_type=models.Voice.Type.NORMAL,
            status=models.Voice.Status.PENDING,
            sender=self.database
        ):
            result.delete(dont_send=True)
            return result.message_id

    @async_fix
    async def cancel_voting(self, file_unique_id: str):
        if message_id := await self.__delete_voting(file_unique_id):
            async with self._session.get(
                f'{self._BASE_URL}deleteMessage',
                params={'chat_id': settings.MEME_CHANNEL, 'message_id': message_id}
            ) as _:
                pass
            return True

    @async_fix
    async def send_voice(self, file_id: str, caption: str, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = {'caption': caption, 'reply_markup': reply_markup}
        async with self._session.get(
            f'{self._BASE_URL}sendVoice',
            params={**self._BASE_PARAM, **encoded, 'voice': file_id, 'reply_to_message_id': reply_to_message_id}
        ) as _:
            return

    async def delete_message(self, message_id: int):
        async with self._session.get(
                f'{self._BASE_URL}deleteMessage', params={**self._BASE_PARAM, 'message_id': message_id}
        ) as _:
            return

    @async_fix
    async def forward_message(self, from_chat_id: int, message_id: int):
        async with self._session.get(
            f'{self._BASE_URL}forwardMessage',
            params={**self._BASE_PARAM, 'from_chat_id': from_chat_id, 'message_id': message_id}
        ) as _:
            return

    @async_fix
    async def copy_message(
            self, message_id: int, reply_markup: dict = '', from_chat_id: int = None,  chat_id: int = None
    ):
        assert chat_id or from_chat_id, 'You must use a chat_id or a from_chat_id !'
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        base_param = {'message_id': message_id, 'reply_markup': reply_markup}
        async with self._session.get(
            f'{self._BASE_URL}copyMessage',
            params={
                'from_chat_id': self.database.chat_id,
                'chat_id': chat_id,
                **base_param
            } if not from_chat_id else {'from_chat_id': from_chat_id, 'chat_id': self.database.chat_id, **base_param}
        ) as result:
            if result.status == 200 and (result := await result.json())['ok']:
                return result['result']['message_id']
            return False

    @sync_to_async
    def __save_ad(self, ad: models.Ad):
        ad.seen.add(self.database)
        ad.save()

    async def send_ad(self):
        for ad in self.__ads:
            await self.forward_message(ad.chat_id, ad.message_id)
            await self.__save_ad(ad)

    @sync_to_async
    def get_voices(self, query: str, offset: str):
        if len(splinted_offset := offset.split(':')) != 4:
            splinted_offset = [0] * 4
        if query.startswith('names:'):
            query = query[6:].strip()
            queries = Q(name__icontains=query[6:].strip())
        else:
            if is_tags := query.startswith('tags:'):
                query = query[5:].strip()
            first_tags = query.split()
            second_tags = [
                ' '.join(first_tags[start:end + 1]) for start, end in combinations(range(len(first_tags)), 2)
                ]
            queries = (Q(tags__tag__iexact=first_tags.pop(0)) if first_tags else Q()) if is_tags else \
                Q(name__icontains=query)
            for tag in first_tags:
                queries |= Q(tags__tag__iexact=tag)
            for tag in second_tags:
                queries |= Q(tags__tag__iexact=tag)
        is_name = Case(When(name__icontains=query, then=True), default=False, output_field=BooleanField())
        result_sets = (
            lambda: [
                voice for playlist in self.database.playlists.prefetch_related('voices')
                for voice in playlist.voices.filter(
                    queries
                ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct()
            ],
            lambda: self.database.private_voices.all().filter(
                queries
            ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct(),
            lambda: self.database.favorite_voices.all().filter(
                queries & Q(status__in=models.PUBLIC_STATUS)
            ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct(),
            lambda: models.Voice.objects.filter(
                queries &
                Q(status__in=models.PUBLIC_STATUS) &
                Q(voice_type=models.Voice.Type.NORMAL)
            ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct()
        )
        results = []
        remaining = 50
        result_maker = make_like_result if self.database.vote else make_result
        for result, current_offset in zip(result_sets, range(4)):
            if splinted_offset[current_offset] != 'e':
                splinted_offset[current_offset] = int(splinted_offset[current_offset])
                temp_result = result_maker(result(), splinted_offset[current_offset], remaining)
                if not (temp_len := len(temp_result)):
                    splinted_offset[current_offset] = 'e'
                else:
                    splinted_offset[current_offset] += temp_len
                results.extend(temp_result)
                remaining = 50 - len(results)
                if not remaining:
                    break
        return results, ':'.join(map(lambda item: str(item), splinted_offset))

    @sync_to_async
    def delete_request(self, voice: models.Voice):
        models.Delete.objects.create(voice=voice, user=self.database)

    @async_fix
    async def get_chat(self):
        async with self._session.get(
                f'{self._BASE_URL}getChat', params=self._BASE_PARAM
        ) as response:
            response = await response.json()
            return response.get('result', {})

    async def set_username(self):
        username = (await self.get_chat()).get('username')
        if username:
            self.database.username = '@' + username

    @sync_to_async
    def like_voice(self, target_voice: models.Voice):
        if self.database in target_voice.accept_vote.all():
            return False
        else:
            if self.database in target_voice.deny_vote.all():
                target_voice.deny_vote.remove(self.database)
            target_voice.accept_vote.add(self.database)
        return True

    @sync_to_async
    def dislike_voice(self, target_voice: models.Voice):
        if self.database in target_voice.deny_vote.all():
            return False
        else:
            if self.database in target_voice.accept_vote.all():
                target_voice.accept_vote.remove(self.database)
            target_voice.deny_vote.add(self.database)
        return True

    @sync_to_async
    def add_voter(self, voice: models.Voice):
        voice.voters.add(self.database)

    @sync_to_async
    def remove_voter(self, voice: models.Voice):
        voice.voters.remove(self.database)

    @sync_to_async
    def private_user_count(self):
        return self.database.private_voices.count()

    @sync_to_async
    def delete_private_voice(self, voice: models.Voice):
        if voice in self.database.private_voices.all():
            voice.delete(dont_send=True)
            return True

    @sync_to_async
    def create_private_voice(self, message: dict):
        new_voice = self.database.private_voices.create(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status=models.Voice.Status.ACTIVE,
            voice_type=models.Voice.Type.PRIVATE,
            sender=self.database,
            name=self.database.temp_voice_name,
        )
        new_voice.tags.set(self.database.temp_voice_tags.all())
        self.database.temp_voice_tags.clear()

    @sync_to_async
    def add_favorite_voice(self, voice: models.Voice):
        if voice not in self.database.favorite_voices.all():
            self.database.favorite_voices.add(voice)
            return True

    @sync_to_async
    def delete_favorite_voice(self, voice: models.Voice):
        self.database.favorite_voices.remove(voice)

    @sync_to_async
    def count_favorite_voices(self):
        return self.database.favorite_voices.count()

    @sync_to_async
    def remove_voice(self, file_unique_id: str):
        target_voices = models.Voice.objects.filter(
            file_unique_id=file_unique_id,
            status__in=models.PUBLIC_STATUS,
            sender=self.database,
            voice_type=models.Voice.Type.NORMAL
        )
        if target_voices.exists():
            target_voices.first().delete(dont_send=True)
            return True

    async def send_help(self):
        async with self._session.get(
            f'{self._BASE_URL}sendAnimation',
            params={
                **self._BASE_PARAM, 'animation': settings.MEME_ANIM, 'caption': self.translate('help_gif')
            }
        ) as _:
            return

    @property
    def __back_menu(self):
        try:
            if self.database.menu_mode != self.database.MenuMode.USER:
                return steps.admin_steps[self.database.back_menu]
            return steps.user_steps[self.database.back_menu]
        except KeyError:
            if self.database.menu_mode != self.database.MenuMode.USER:
                return steps.admin_steps['main']
            return steps.user_steps['main']
    
    async def __perform_back_callback(self, callback: str):
        if callback:
            target_method = getattr(self, callback)
            if iscoroutinefunction(target_method):
                await target_method()
            else:
                target_method()

    async def go_back(self):
        step = self.__back_menu
        self.database.menu = step['menu']
        self.database.back_menu = step.get('before')
        await self.send_message(step['message'], step.get('keyboard', ''))
        await self.__perform_back_callback(step.get('callback'))
        await self.save()

    @async_fix
    async def record_audio(self):
        now = datetime.now()
        if self.database.started and self.database.last_start and \
                (now - self.database.last_start) <= timedelta(seconds=18000):
            return
        while True:
            async with self._session.get(
                    f'{self._BASE_URL}sendChatAction', params={**self._BASE_PARAM, 'action': 'record_audio'}
            ) as response:
                if response.status != 429:
                    self.database.started = response.status == 200
                    if self.database.started:
                        self.database.last_start = now
                    return

    @sync_to_async
    def has_pending_voice(self):
        return models.Voice.objects.filter(sender=self.database, status=models.Voice.Status.PENDING).exists()

    async def voice_exists(self, message: dict):
        if 'voice' in message and ('mime_type' not in message['voice'] or message['voice']['mime_type'] == 'audio/ogg'):
            return True
        if self.database.rank == models.User.Rank.USER:
            await self.send_message(self.translate('send_a_voice'))
        else:
            await self.send_message(self.translate('send_a_voice'))

    @sync_to_async
    def get_playlists(self, page: int):
        return paginate(models.Playlist.objects.filter(creator=self.database), page)

    @sync_to_async
    def get_playlist_voices(self, page: int):
        return paginate(self.database.current_playlist.voices.all(), page)

    @sync_to_async
    def create_playlist(self, name: str):
        return models.Playlist.objects.create(name=name, creator=self.database)

    @sync_to_async
    def join_playlist(self, playlist_id: str):
        if (playlist := models.Playlist.objects.get(
                invite_link=playlist_id
        )).creator != self.database and playlist not in self.database.playlists.all():
            self.database.playlists.add(playlist)
            return playlist
        return False

    @property
    @sync_to_async
    def playlist_name(self):
        return self.database.current_playlist.name

    @property
    @sync_to_async
    def playlist_link(self):
        return self.database.current_playlist.get_link()

    @sync_to_async
    def add_voice_to_playlist(self, file_unique_id: str):
        if (voice := filter_object(
            models.Voice.objects,
            True,
            file_unique_id=file_unique_id,
            sender=self.database,
            voice_type=models.Voice.Type.PRIVATE
        )) and voice not in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.add(voice)
            return True
        return False

    @property
    @sync_to_async
    def playlist_users(self):
        return self.database.current_playlist.user_playlist.count()

    @sync_to_async
    def remove_voice_from_playlist(self):
        if self.database.current_playlist and self.database.current_voice and \
                self.database.current_voice in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.remove(self.database.current_voice)
            return True
        return False

    @property
    @sync_to_async
    def playlist_voices(self):
        return self.database.current_playlist.voices.all()

    @property
    @sync_to_async
    def voice_info(self):
        return self.database.current_voice.file_id, self.database.current_voice.name

    @sync_to_async
    def delete_playlist(self):
        if self.database.current_playlist:
            self.database.current_playlist.delete()
            self.database.current_playlist = None

    @sync_to_async
    def set_current_ad(self, ad_id: int):
        self.database.current_ad = models.Ad.objects.get(ad_id=ad_id)

    @sync_to_async
    def edit_current_ad(self, message_id: int):
        if self.database.current_ad:
            self.database.current_ad.message_id = message_id
            self.database.current_ad.save()
            return True
        return False

    async def get_vote(self, file_unique_id: str):
        if not (target_voice := await get_vote(file_unique_id)):
            await self.send_message(self.translate('voice_not_found'))
        return target_voice

    async def accept_voice(self, voice: models.Voice):
        sender_user = await User(self._session, self.Mode.NORMAL, instance=await voice.async_accept())
        await sender_user.send_message(self.translate('voice_accepted'))
        await delete_vote_async(voice.message_id, self._session)

    async def deny_voice(self, voice: models.Voice):
        sender_user = await User(self._session, self.Mode.NORMAL, instance=await voice.async_deny())
        await sender_user.send_message(self.translate('voice_denied'))
        await delete_vote_async(voice.message_id, self._session)

    @property
    @sync_to_async
    def sent_message(self):
        return models.Message.objects.filter(sender=self.database, status=models.Message.Status.PENDING).exists()

    @sync_to_async
    def _create_message(self, message_id: int):
        models.Message.objects.create(sender=self.database, message_id=message_id)

    async def contact_admin(self, message_id: int):
        if new_message_id := await self.copy_message(
                message_id, message_keyboard(self.database.chat_id), chat_id=settings.MEME_MESSAGES
        ):
            await self._create_message(new_message_id)

    async def send_messages(self):
        if messages := await get_contact_admin_messages():
            for message in messages:
                await self.copy_message(
                    message.message_id, manage_message(message), from_chat_id=settings.MEME_MESSAGES
                )
            await self.send_message(self.translate('messages'))
            return
        await self.send_message(self.translate('no_message'))

    def translate(self, key: str, *formatting_args):
        return (translations.user_messages[key] if (
            (self.__enforced_rank == self.database.Rank.USER) or
            (self.__enforced_rank not in models.BOT_ADMINS and self.database.menu_mode == self.database.MenuMode.USER)
        ) else translations.admin_messages[key]).format(*formatting_args)

    @sync_to_async
    def __check_voice_tags(self, tags: str):
        if 'tags:' in tags:
            raise InvalidVoiceTag()
        if len(tags) >= len(punctuation):
            if any(char in tags for char in punctuation):
                raise InvalidVoiceTag()
        else:
            if any(char in punctuation for char in tags):
                raise InvalidVoiceTag()
        tags = tags.split('\n')
        if len(tags) > 6:
            raise TooManyVoiceTags()
        if any(len(tag) > 32 for tag in tags):
            raise LongVoiceTag()
        for tag in tags:
            self.database.temp_voice_tags.add(models.VoiceTag.objects.get_or_create(tag=tag)[0])
    
    async def process_voice_tags(self, tags: str):
        if not tags:
            await self.send_message(self.translate('voice_tags'))
            return False
        try:
            await self.__check_voice_tags(tags)
        except ValueError as e:
            await self.send_message(self.translate(str(e)))
            return False
        return True
    
    @sync_to_async
    def clear_temp_voice_tags(self):
        self.database.temp_voice_tags.clear()

    @sync_to_async
    def add_voice(self, file_id, file_unique_id, status):
        if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type=models.Voice.Type.NORMAL).exists():
            new_voice = models.Voice.objects.create(
                file_id=file_id,
                file_unique_id=file_unique_id,
                name=self.database.temp_voice_name,
                sender=self.database,
                status=status
            )
            new_voice.tags.set(self.database.temp_voice_tags.all())
            self.database.temp_voice_tags.clear()
            return new_voice
    
    @sync_to_async
    def edit_voice_name(self, new_name: str):
        self.database.current_voice.name = new_name
        self.database.current_voice.save()
    
    @sync_to_async
    def edit_voice_tags(self):
        self.database.current_voice.tags.set(self.database.temp_voice_tags.all())
        self.database.temp_voice_tags.clear()
    
    async def validate_voice_name(self, message: dict):
        if message.get('entities') or len(message['text']) > 50 or message['text'].startswith('tags:') or \
                message['text'].startswith('names:'):
            await self.send_message(
                self.translate('invalid_voice_name'), reply_to_message_id=message['message_id']
            )
            return False
        return True

    async def get_public_voice(self, message: dict):
        if target_voice := await get_voice(message['voice']['file_unique_id']):
            return target_voice
        await self.send_message(self.translate('voice_not_found'), reply_to_message_id=message['message_id'])
        return None
    
    def clear_current_playlist(self):
        self.database.current_playlist = None
    
    def clear_current_voice(self):
        self.database.current_voice = None
    
    def clear_current_ad(self):
        self.database.current_ad = None
    
    async def menu_cleanup(self):
        await self.__perform_back_callback(self.__back_menu.get('callback'))
