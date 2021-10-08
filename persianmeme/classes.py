import json
from django.conf import settings
from LilSholex.decorators import sync_fix
from LilSholex.classes import Base
from datetime import datetime, timedelta
from persianmeme.functions import (
    make_like_result,
    make_result,
    make_voice_result,
    make_voice_like_result,
    paginate,
    get_vote,
    delete_vote_sync,
    get_voice,
    make_list_string
)
from enum import Enum
from . import translations, models, steps
from .keyboards import (
    message as message_keyboard,
    manage_message,
    make_voice_list,
    per_back,
    en_back,
    owner,
    user as user_keyboard,
    manage_suggestions,
    voice_review
)
from .types import InvalidVoiceTag, LongVoiceTag, TooManyVoiceTags
from string import punctuation
from itertools import combinations
from django.db.models import Q, Case, When, BooleanField
from .types import ObjectType
from requests import Session
from .tasks import revoke_review
from LilSholex.exceptions import TooManyRequests


class User(Base):
    _BASE_URL = f'https://api.telegram.org/bot{settings.MEME}/'
    __ads: tuple

    class Mode(Enum):
        NORMAL = 0
        SEND_AD = 1

    def __init__(
            self,
            session: Session,
            mode: Mode,
            chat_id: int = None,
            instance: models.User = None
    ):
        self.__mode = mode
        super().__init__(settings.MEME, chat_id, instance, session)

    def broadcast(self, message_id: int):
        return models.Broadcast.objects.create(sender=self.database, message_id=message_id).id

    def get_user(self):
        user = models.User.objects.get_or_create(chat_id=self.chat_id)[0]
        if self.__mode == self.Mode.SEND_AD:
            self.__ads = models.Ad.objects.exclude(seen=user)
        return user

    def delete_current_voice(self):
        if self.database.current_voice:
            self.database.current_voice.delete(admin=self.database, log=True)
            self.send_message(translations.admin_messages['deleted'])
        else:
            self.send_message(translations.admin_messages['deleted_before'])

    def delete_voice(self, file_unique_id):
        if (result := models.Voice.objects.filter(
                file_unique_id=file_unique_id, voice_type=models.Voice.Type.NORMAL, status=models.Voice.Status.ACTIVE
        )).exists():
            result.first().delete(admin=self.database, log=True)

    @sync_fix
    def __delete_voting(self, message_id: int):
        with self._session.get(
            f'{self._BASE_URL}deleteMessage',
            params={'chat_id': settings.MEME_CHANNEL, 'message_id': message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @property
    def __pending_voices(self):
        pending_voices = models.Voice.objects.filter(sender=self.database, status=models.Voice.Status.PENDING)
        if pending_voices.exists():
            message_ids = [voice.message_id for voice in pending_voices]
            pending_voices.delete()
            return message_ids
        return None

    def cancel_voting(self):
        if pending_voices := self.__pending_voices:
            for voice in pending_voices:
                self.__delete_voting(voice)
            return True
        return False

    @sync_fix
    def send_voice(self, file_id: str, caption: str, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = {'caption': caption, 'reply_markup': reply_markup}
        with self._session.get(
            f'{self._BASE_URL}sendVoice',
            params={**self._BASE_PARAM, **encoded, 'voice': file_id, 'reply_to_message_id': reply_to_message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def delete_message(self, message_id: int):
        with self._session.get(
            f'{self._BASE_URL}deleteMessage', params={**self._BASE_PARAM, 'message_id': message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as _:
            return

    @sync_fix
    def forward_message(self, from_chat_id: int, message_id: int):
        with self._session.get(
            f'{self._BASE_URL}forwardMessage',
            params={**self._BASE_PARAM, 'from_chat_id': from_chat_id, 'message_id': message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def copy_message(
            self, message_id: int, reply_markup: dict = '', from_chat_id: int = None,  chat_id: int = None
    ):
        assert (chat_id and not from_chat_id) or (from_chat_id and not chat_id),\
            'You must use a chat_id or a from_chat_id !'
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        base_param = {'message_id': message_id, 'reply_markup': reply_markup}
        with self._session.get(
            f'{self._BASE_URL}copyMessage',
            params={
                'from_chat_id': self.database.chat_id,
                'chat_id': chat_id,
                **base_param
            } if not from_chat_id else {'from_chat_id': from_chat_id, 'chat_id': self.database.chat_id, **base_param},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                if (result := response.json())['ok']:
                    return result['result']['message_id']
            elif response.status_code != 429:
                return False
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def __save_ad(self, ad: models.Ad):
        ad.seen.add(self.database)
        ad.save()

    def send_ad(self):
        for ad in self.__ads:
            self.copy_message(ad.message_id, from_chat_id=ad.chat_id)
            self.__save_ad(ad)

    def get_voices(self, query: str, offset: str):
        if query.startswith('names:'):
            query = query[6:].strip()
            queries = Q(name__icontains=query)
        elif query.startswith('id:') and (target_voice_id := query[3:].strip()).isdigit():
            result_maker = make_voice_like_result if self.database.vote else make_voice_result
            try:
                return ([result_maker(models.Voice.objects.get(
                    Q(id=target_voice_id) & ((
                            Q(voice_type=models.Voice.Type.PRIVATE) &
                            Q(sender=self.database)
                    ) | Q(voice_type=models.Voice.Type.NORMAL)) & Q(status=models.Voice.Status.ACTIVE)
                ))], str())
            except (models.Voice.DoesNotExist, ValueError):
                return list(), str()
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
            lambda:  models.RecentVoice.objects.filter(user=self.database).select_related('voice').values_list(
                'voice__id', 'voice__file_id', 'voice__name'
            ) if not query and self.database.use_recent_voices else tuple(),
            lambda: [
                voice for playlist in self.database.playlists.prefetch_related('voices')
                for voice in playlist.voices.values_list('id', 'file_id', 'name').filter(
                    queries
                ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct()
            ],
            lambda: self.database.favorite_voices.values_list('id', 'file_id', 'name').filter(
                queries & Q(status=models.Voice.Status.ACTIVE)
            ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct(),
            lambda: models.Voice.objects.values_list('id', 'file_id', 'name').filter(
                queries & (
                    (Q(status=models.Voice.Status.ACTIVE) & Q(voice_type=models.Voice.Type.NORMAL)) |
                    (Q(sender=self.database) & Q(voice_type=models.Voice.Type.PRIVATE))
                )
            ).annotate(is_name=is_name).order_by('-is_name', self.database.voice_order).distinct()
        )
        if len(splinted_offset := offset.split(':')) != len(result_sets):
            splinted_offset = [0] * len(result_sets)
        results = []
        remaining = 50
        result_maker = make_like_result if self.database.vote else make_result
        for result, current_offset in zip(result_sets, range(len(result_sets))):
            if splinted_offset[current_offset] != 'e':
                splinted_offset[current_offset] = int(splinted_offset[current_offset])
                current_result = result()[splinted_offset[current_offset]:splinted_offset[current_offset] + remaining]
                temp_result = [result_maker(voice) for voice in current_result
                               if all(voice[0] != target_result['id'] for target_result in results)]
                if not (temp_len := len(temp_result)):
                    splinted_offset[current_offset] = 'e'
                else:
                    splinted_offset[current_offset] += len(current_result)
                results.extend(temp_result)
                remaining -= temp_len
                if not remaining:
                    break
        return results, ':'.join(map(lambda item: str(item), splinted_offset))

    def delete_request(self, voice: models.Voice):
        models.Delete.objects.create(voice=voice, user=self.database)

    @sync_fix
    def get_chat(self):
        with self._session.get(
            f'{self._BASE_URL}getChat', params=self._BASE_PARAM,
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                return response.json().get('result')
            elif response.status_code != 429:
                return {}
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def set_username(self):
        username = self.get_chat().get('username')
        if username:
            self.database.username = '@' + username

    def like_voice(self, target_voice: models.Voice):
        if self.database in target_voice.accept_vote.all():
            return False
        else:
            if self.database in target_voice.deny_vote.all():
                target_voice.deny_vote.remove(self.database)
            target_voice.accept_vote.add(self.database)
            target_voice.save()
        return True

    def dislike_voice(self, target_voice: models.Voice):
        if self.database in target_voice.deny_vote.all():
            return False
        else:
            if self.database in target_voice.accept_vote.all():
                target_voice.accept_vote.remove(self.database)
            target_voice.deny_vote.add(self.database)
            target_voice.save()
        return True

    def add_voter(self, voice: models.Voice):
        voice.voters.add(self.database)

    def remove_voter(self, voice: models.Voice):
        voice.voters.remove(self.database)

    @property
    def private_voices_count(self):
        return models.Voice.objects.filter(voice_type=models.Voice.Type.PRIVATE, sender=self.database).count()

    def get_private_voice(self, voice_id: str):
        return models.Voice.objects.get(id=voice_id, voice_type=models.Voice.Type.PRIVATE, sender=self.database)

    def get_favorite_voice(self, voice_id: str):
        return self.database.favorite_voices.get(id=voice_id, voice_type=models.Voice.Type.NORMAL)

    def get_suggested_voice(self, voice_id: str):
        return models.Voice.objects.get(
            id=voice_id, status=models.Voice.Status.ACTIVE, voice_type=models.Voice.Type.NORMAL, sender=self.database
        )

    def delete_private_voice(self):
        if self.database.current_voice.sender == self.database:
            self.database.current_voice.delete()
            self.database.current_voice = None
            return True
        return False

    def create_private_voice(self, message: dict):
        if models.Voice.objects.filter(Q(file_unique_id=message['voice']['file_unique_id']) & (
                Q(voice_type=models.Voice.Type.NORMAL) |
                (Q(voice_type=models.Voice.Type.PRIVATE) & Q(sender=self.database))
        )).exists():
            return False
        models.Voice.objects.create(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status=models.Voice.Status.ACTIVE,
            voice_type=models.Voice.Type.PRIVATE,
            sender=self.database,
            name=self.database.temp_voice_name,
        ).tags.set(self.database.temp_voice_tags.all(), clear=True)
        self.database.temp_voice_tags.clear()
        return True

    def add_favorite_voice(self, voice: models.Voice):
        if voice not in self.database.favorite_voices.all():
            self.database.favorite_voices.add(voice)
            return True

    def delete_favorite_voice(self):
        if self.database.favorite_voices.filter(id=self.database.current_voice.id).exists():
            self.database.favorite_voices.remove(self.database.current_voice)
            self.database.current_voice = None
            return True
        return False

    def delete_suggested_voice(self):
        if self.database.current_voice.sender == self.database:
            self.database.current_voice.delete()
            self.database.current_voice = None
            return True
        return False

    def count_favorite_voices(self):
        return self.database.favorite_voices.count()

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
    
    def __perform_back_callback(self, callback: str):
        if callback:
            return getattr(self, callback)()

    def go_back(self):
        step = self.__back_menu
        self.database.menu = step['menu']
        self.database.back_menu = step.get('before')
        self.send_message(step['message'], step.get('keyboard', ''))
        self.__perform_back_callback(step.get('callback'))
        self.database.save()

    @sync_fix
    def upload_voice(self):
        now = datetime.now()
        if self.database.started and self.database.last_start and \
                (now - self.database.last_start) <= timedelta(seconds=18000):
            return
        with self._session.get(
            f'{self._BASE_URL}sendChatAction', params={**self._BASE_PARAM, 'action': 'upload_voice'},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                self.database.started = response.status_code == 200
                if self.database.started:
                    self.database.last_start = now
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def voice_exists(self, message: dict):
        if 'voice' in message and ('mime_type' not in message['voice'] or message['voice']['mime_type'] == 'audio/ogg'):
            return True
        self.send_message(self.translate('send_a_voice'))

    def get_playlists(self, page: int):
        return paginate(models.Playlist.objects.filter(creator=self.database), page)

    def get_playlist_voices(self, page: int):
        return paginate(self.database.current_playlist.voices.all(), page)

    def get_private_voices(self, page: int):
        return paginate(models.Voice.objects.filter(sender=self.database, voice_type=models.Voice.Type.PRIVATE), page)

    def get_favorite_voices(self, page: int):
        return paginate(self.database.favorite_voices.all(), page)

    def create_playlist(self, name: str):
        return models.Playlist.objects.create(name=name, creator=self.database)

    def join_playlist(self, playlist_id: str):
        if (playlist := models.Playlist.objects.get(
                invite_link=playlist_id
        )).creator != self.database and playlist not in self.database.playlists.all():
            self.database.playlists.add(playlist)
            return playlist
        return False

    def add_voice_to_playlist(self, file_unique_id: str):
        if (voice := models.Voice.objects.filter(
                file_unique_id=file_unique_id, sender=self.database, voice_type=models.Voice.Type.PRIVATE
        )).exists() and (first_voice := voice.first()) not in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.add(first_voice)
            return True
        return False

    def remove_voice_from_playlist(self):
        if self.database.current_playlist and \
                self.database.current_voice in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.remove(self.database.current_voice)
            return True
        return False

    def delete_playlist(self):
        if self.database.current_playlist:
            self.database.current_playlist.delete()
            self.database.current_playlist = None

    def set_current_ad(self, ad_id: int):
        self.database.current_ad = models.Ad.objects.get(ad_id=ad_id)

    def edit_current_ad(self, message_id: int):
        if self.database.current_ad:
            self.database.current_ad.message_id = message_id
            self.database.current_ad.save()
            return True
        return False

    def get_vote(self, file_unique_id: str):
        if not (target_voice := get_vote(file_unique_id)):
            self.send_message(self.translate('voice_not_found'))
        return target_voice

    def accept_voice(self, voice: models.Voice):
        sender_user = User(self._session, self.Mode.NORMAL, instance=voice.user_accept())
        sender_user.send_message(sender_user.translate('voice_accepted'))
        delete_vote_sync(voice.message_id, self._session)

    def deny_voice(self, voice: models.Voice):
        sender_user = User(self._session, self.Mode.NORMAL, instance=voice.user_deny())
        sender_user.send_message(self.translate('voice_denied'))
        delete_vote_sync(voice.message_id, self._session)

    @property
    def sent_message(self):
        return models.Message.objects.filter(sender=self.database, status=models.Message.Status.PENDING).exists()

    def contact_admin(self, message_id: int):
        if new_message_id := self.copy_message(
                message_id, message_keyboard(self.database.chat_id), chat_id=settings.MEME_MESSAGES
        ):
            models.Message.objects.create(sender=self.database, message_id=new_message_id)

    def send_messages(self):
        if (
                messages := models.Message.objects.select_related('sender').filter(status=models.Message.Status.PENDING)
        ).exists():
            for message in messages:
                self.copy_message(
                    message.message_id, manage_message(message), from_chat_id=settings.MEME_MESSAGES
                )
            self.send_message(self.translate('messages'))
            return
        self.send_message(self.translate('no_message'))

    def translate(self, key: str, *formatting_args):
        return translations.user_messages[key].format(*formatting_args) \
            if self.database.rank == self.database.Rank.USER or \
            self.database.menu_mode == self.database.MenuMode.USER else \
            translations.admin_messages[key].format(*formatting_args)

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
    
    def process_voice_tags(self, tags: str):
        if not tags:
            self.send_message(self.translate('voice_tags'))
            return False
        try:
            self.__check_voice_tags(tags)
        except ValueError as e:
            self.send_message(self.translate(str(e)))
            return False
        return True

    def clear_temp_voice_tags(self):
        self.database.temp_voice_tags.clear()

    def add_voice(self, file_id, file_unique_id, status):
        if not models.Voice.objects.filter(file_unique_id=file_unique_id, voice_type=models.Voice.Type.NORMAL).exists():
            new_voice = models.Voice.objects.create(
                file_id=file_id,
                file_unique_id=file_unique_id,
                name=self.database.temp_voice_name,
                sender=self.database,
                status=status
            )
            new_voice.tags.set(self.database.temp_voice_tags.all(), clear=True)
            self.database.temp_voice_tags.clear()
            return new_voice

    def edit_voice_name(self, new_name: str):
        self.database.current_voice.name = new_name
        self.database.current_voice.save()

    def edit_voice_tags(self):
        self.database.current_voice.tags.set(self.database.temp_voice_tags.all(), clear=True)
        self.database.temp_voice_tags.clear()
    
    def validate_voice_name(self, message: dict):
        if not message.get('text') or\
                message.get('entities') or len(message['text']) > 50 or message['text'].startswith('tags:') or\
                message['text'].startswith('names:'):
            self.send_message(
                self.translate('invalid_voice_name'), reply_to_message_id=message['message_id']
            )
            return False
        return True

    def get_public_voice(self, message: dict):
        if target_voice := get_voice(message['voice']['file_unique_id']):
            return target_voice
        self.send_message(self.translate('voice_not_found'), reply_to_message_id=message['message_id'])
        return None
    
    def clear_current_playlist(self):
        self.database.current_playlist = None
    
    def clear_current_voice(self):
        self.database.current_voice = None
    
    def clear_current_ad(self):
        self.database.current_ad = None
    
    def menu_cleanup(self):
        self.__perform_back_callback(self.__back_menu.get('callback'))

    def add_recent_voice(self, voice: models.Voice):
        self.database.recent_voices.remove(voice)
        self.database.recent_voices.add(voice)
        if extra_voices := tuple(models.RecentVoice.objects.filter(
            user=self.database
        ).order_by('-id')[15:].values_list('id', flat=True)):
            models.RecentVoice.objects.filter(id__in=extra_voices).delete()

    def send_ordered_voice_list(self, ordering: models.User.VoiceOrder):
        ordered_voices = models.Voice.objects.filter(
            status=models.Voice.Status.ACTIVE, voice_type='n'
        ).order_by(ordering)[:12]
        return self.send_message(
            make_list_string(ObjectType.PLAYLIST_VOICE, ordered_voices), make_voice_list(ordered_voices)
        )

    def clear_recent_voices(self):
        self.database.recent_voices.clear()

    def add_sound(self):
        if self.database.rank == self.database.Rank.USER or self.database.menu_mode == self.database.MenuMode.USER:
            if models.Voice.objects.filter(sender=self.database, status=models.Voice.Status.PENDING).exists():
                self.database.menu = self.database.Menu.USER_SUGGESTIONS
                return self.send_message(self.translate('pending_voice'), manage_suggestions)
            self.database.back_menu = 'manage_suggestions'
            self.database.menu = self.database.Menu.USER_SUGGEST_VOICE_NAME
            return self.send_message(self.translate('voice_name'), per_back)
        self.database.menu = self.database.Menu.ADMIN_VOICE_NAME
        return self.send_message(self.translate('voice_name'), en_back)

    def get_suggested_voices(self, page: int):
        return paginate(models.Voice.objects.filter(
            sender=self.database, voice_type=models.Voice.Type.NORMAL
        ).exclude(status=models.Voice.Status.PENDING), page)

    def start(self):
        self.menu_cleanup()
        if self.database.rank == self.database.Rank.USER or self.database.menu_mode == self.database.MenuMode.USER:
            self.database.menu = self.database.Menu.USER_MAIN
            self.database.menu_mode = self.database.MenuMode.USER
            return self.send_message(self.translate('welcome'), user_keyboard)
        self.database.menu = self.database.Menu.ADMIN_MAIN
        return self.send_message(self.translate('welcome'), owner)

    def check_current_voice(self):
        if not self.database.current_voice:
            self.send_message(self.translate('voice_not_accessible'))
            self.go_back()
            return False
        return True

    def assign_voice(self):
        if (assigned_voice := models.Voice.objects.filter(
            assigned_admin=self.database,
            reviewed=False,
            voice_type=models.Voice.Type.NORMAL,
            status=models.Voice.Status.ACTIVE
        )).exists():
            self.database.current_voice = assigned_voice.first()
        elif (new_voice := models.Voice.objects.filter(
                assigned_admin=None,
                reviewed=False,
                status=models.Voice.Status.ACTIVE,
                voice_type=models.Voice.Type.NORMAL
        )).exists():
            self.database.current_voice = new_voice.first()
            self.database.current_voice.assigned_admin = self.database
            self.database.current_voice.save()
            revoke_review(self.database.current_voice.id)
        else:
            self.send_message(translations.admin_messages['no_voice_to_review'])
            return False
        self.send_message(
            translations.admin_messages['review_the_voice'],
            voice_review,
            self.database.current_voice.send_voice(self.database.chat_id, self._session)
        )
        return True
