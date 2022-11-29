import json
from django.conf import settings
from LilSholex.decorators import sync_fix
from LilSholex.classes import Base
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
    create_description
)
from enum import Enum
from . import translations, models, steps
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
from .types import InvalidMemeTag, LongMemeTag, TooManyMemeTags
from string import punctuation
from itertools import combinations
from django.db.models import Q, Case, When, BooleanField
from .types import ObjectType, ReportResult
from requests import Session
from .tasks import revoke_review
from LilSholex.exceptions import TooManyRequests
from functools import cached_property


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

    def delete_current_meme(self):
        if self.database.current_meme:
            self.database.current_meme.delete(admin=self.database, log=True)
            self.send_message(translations.admin_messages['deleted'])
        else:
            self.send_message(translations.admin_messages['deleted_before'])

    def delete_meme(self, file_unique_id, meme_type: models.MemeType):
        if (result := models.Meme.objects.filter(
            file_unique_id=file_unique_id,
            visibility=models.Meme.Visibility.NORMAL,
            status=models.Meme.Status.ACTIVE,
            type=meme_type
        )).exists():
            target_meme = result.first()
            target_meme.assigned_admin = self.database
            target_meme.delete(admin=self.database, log=True)

    def cancel_voting(self, meme_type: models.MemeType):
        if not (pending_memes := models.Meme.objects.filter(
                sender=self.database, status=models.Meme.Status.PENDING, type=meme_type
        )).exists():
            self.send_message(translations.user_messages['no_voting'].format(
                translations.user_messages['any_video' if meme_type == models.MemeType.VIDEO else 'any_voice']
            ))
            return
        for pending_meme in pending_memes:
            pending_meme.delete_vote()
            pending_meme.delete()
        self.send_message(translations.user_messages['voting_canceled'].format(
            translations.user_messages['voice' if meme_type == models.MemeType.VOICE else 'video']
        ))

    @sync_fix
    def send_current_meme(self, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        params = {
            'caption': self.database.current_meme.name,
            'reply_markup': reply_markup,
            'reply_to_message_id': reply_to_message_id
        }
        if self.database.current_meme.type == models.MemeType.VOICE:
            meme_method = 'Voice'
            params['voice'] = self.database.current_meme.file_id
        else:
            meme_method = 'Video'
            params['video'] = self.database.current_meme.file_id
        with self.session.get(
            f'{self._BASE_URL}send{meme_method}',
            params={**self._BASE_PARAM, **params},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def delete_message(self, message_id: int):
        with self.session.get(
            f'{self._BASE_URL}deleteMessage', params={**self._BASE_PARAM, 'message_id': message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as _:
            return

    @sync_fix
    def copy_message(
            self,
            message_id: int,
            reply_markup: dict = '',
            from_chat_id: int = None,
            chat_id: int = None,
            protect_content: bool = False
    ):
        assert (chat_id and not from_chat_id) or (from_chat_id and not chat_id),\
            'You must use a chat_id or a from_chat_id !'
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        base_param = {'message_id': message_id, 'reply_markup': reply_markup, 'protect_content': protect_content}
        with self.session.get(
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

    @property
    def __search_items(self):
        match self.database.search_items:
            case models.User.SearchItems.VIDEOS:
                return Q(type=models.MemeType.VIDEO), Q(meme__type=models.MemeType.VIDEO)
            case models.User.SearchItems.VOICES:
                return Q(type=models.MemeType.VOICE), Q(meme__type=models.MemeType.VOICE)
            case models.User.SearchItems.BOTH:
                return Q(type__in=(types_tuple := (models.MemeType.VOICE, models.MemeType.VIDEO))), \
                       Q(meme__type__in=types_tuple)

    def get_memes(self, query: str, offset: str):
        if query.startswith('names:'):
            query = query[6:].strip()
            queries = Q(name__icontains=query)
            type_filter, recent_type_filter = self.__search_items
        elif query.startswith('id:') and (target_voice_id := query[3:].strip()).isdigit():
            result_maker = make_meme_like_result if self.database.vote else make_meme_result
            try:
                return ([result_maker(models.Meme.objects.get(
                    Q(id=target_voice_id) & ((
                                                     Q(visibility=models.Meme.Visibility.PRIVATE) &
                                                     Q(sender=self.database)
                                             ) | Q(visibility=models.Meme.Visibility.NORMAL)) & Q(
                        status=models.Meme.Status.ACTIVE)
                ))], str())
            except (models.Meme.DoesNotExist, ValueError):
                return list(), str()
        else:
            if is_tags := query.startswith('tags:'):
                query = query[5:].strip()
                type_filter, recent_type_filter = self.__search_items
            else:
                if query.startswith('voices:'):
                    query = query[7:].strip()
                    type_filter = Q(type=models.MemeType.VOICE)
                    recent_type_filter = Q(meme__type=models.MemeType.VOICE)
                elif query.startswith('videos:'):
                    query = query[7:].strip()
                    type_filter = Q(type=models.MemeType.VIDEO)
                    recent_type_filter = Q(meme__type=models.MemeType.VIDEO)
                else:
                    type_filter, recent_type_filter = self.__search_items
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
            lambda: models.RecentMeme.objects.filter(
                Q(user=self.database, meme__status=models.Meme.Status.ACTIVE) & recent_type_filter
            ).select_related('meme').values_list(
                'meme__id', 'meme__file_id', 'meme__name', 'meme__type', 'meme__description'
            ) if not query and self.database.use_recent_memes else tuple(),
            lambda: [
                voice for playlist in self.database.playlists.prefetch_related('voices')
                for voice in playlist.voices.values_list('id', 'file_id', 'name', 'type', 'description').filter(
                    queries & type_filter
                ).annotate(is_name=is_name).order_by('-is_name', self.database.meme_ordering).distinct()
            ],
            lambda: models.Meme.objects.values_list('id', 'file_id', 'name', 'type', 'description').filter(
                queries & (
                        (Q(status=models.Meme.Status.ACTIVE) & Q(visibility=models.Meme.Visibility.NORMAL)) |
                        (Q(sender=self.database) & Q(visibility=models.Meme.Visibility.PRIVATE))
                ) & type_filter
            ).annotate(is_name=is_name).order_by('-visibility', '-is_name', self.database.meme_ordering).distinct()
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
                temp_result = [result_maker(meme) for meme in current_result
                               if all(meme[0] != target_result['id'] for target_result in results)]
                if not (temp_len := len(temp_result)):
                    splinted_offset[current_offset] = 'e'
                else:
                    splinted_offset[current_offset] += len(current_result)
                results.extend(temp_result)
                remaining -= temp_len
                if not remaining:
                    break
        return results, ':'.join(map(lambda item: str(item), splinted_offset))

    def delete_request(self, meme: models.Meme):
        models.Delete.objects.create(meme=meme, user=self.database)

    @sync_fix
    def get_chat(self):
        with self.session.get(
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
            self.database.usernames.get_or_create(username=username.lower())

    def like_meme(self, target_voice: models.Meme):
        if self.database in target_voice.accept_vote.all():
            return False
        else:
            if self.database in target_voice.deny_vote.all():
                target_voice.deny_vote.remove(self.database)
            target_voice.accept_vote.add(self.database)
            target_voice.save()
        return True

    def dislike_meme(self, target_voice: models.Meme):
        if self.database in target_voice.deny_vote.all():
            return False
        else:
            if self.database in target_voice.accept_vote.all():
                target_voice.accept_vote.remove(self.database)
            target_voice.deny_vote.add(self.database)
            target_voice.save()
        return True

    def add_voter(self, voice: models.Meme):
        voice.voters.add(self.database)

    def remove_voter(self, voice: models.Meme):
        voice.voters.remove(self.database)

    @property
    def private_voices_count(self):
        return models.Meme.objects.filter(visibility=models.Meme.Visibility.PRIVATE, sender=self.database).count()

    def get_private_voice(self, voice_id: str):
        return models.Meme.objects.get(
            id=voice_id, visibility=models.Meme.Visibility.PRIVATE, sender=self.database, type=models.MemeType.VOICE
        )

    def get_suggested_meme(self, meme_id: str, meme_type: models.MemeType):
        return models.Meme.objects.get(
            id=meme_id,
            status=models.Meme.Status.ACTIVE,
            visibility=models.Meme.Visibility.NORMAL,
            sender=self.database,
            type=meme_type
        )

    def delete_private_voice(self):
        if self.database.current_meme.sender == self.database:
            self.database.current_meme.delete()
            self.database.current_meme = None
            return True
        return False

    def create_private_voice(self, message: dict):
        if models.Meme.objects.filter(Q(file_unique_id=message['voice']['file_unique_id']) & (
                Q(visibility=models.Meme.Visibility.NORMAL) |
                (Q(visibility=models.Meme.Visibility.PRIVATE) & Q(sender=self.database))
        )).exists():
            self.send_message(self.translate('meme_already_exists'), reply_to_message_id=message['message_id'])
            return False
        models.Meme.objects.create(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status=models.Meme.Status.ACTIVE,
            visibility=models.Meme.Visibility.PRIVATE,
            sender=self.database,
            name=self.database.temp_meme_name,
        ).tags.set(self.database.temp_meme_tags.all(), clear=True)
        self.database.temp_meme_tags.clear()
        return True

    def delete_suggested_meme(self):
        if self.database.current_meme.sender == self.database:
            self.database.current_meme.delete()
            return True
        return False

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
        with self.session.get(
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
        if check_for_voice(message):
            return True
        self.send_message(self.translate('send_a_meme', self.translate('voice')))

    def get_playlists(self, page: int):
        return paginate(models.Playlist.objects.filter(creator=self.database), page)

    def get_playlist_voices(self, page: int):
        return paginate(self.database.current_playlist.voices.all(), page)

    def get_private_voices(self, page: int):
        return paginate(models.Meme.objects.filter(
            sender=self.database, visibility=models.Meme.Visibility.PRIVATE), page
        )

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
        if (voice := models.Meme.objects.filter(
            file_unique_id=file_unique_id,
            sender=self.database,
            visibility=models.Meme.Visibility.PRIVATE,
            type=models.MemeType.VOICE
        )).exists() and (first_voice := voice.first()) not in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.add(first_voice)
            return True
        return False

    def remove_voice_from_playlist(self):
        if self.database.current_meme in self.database.current_playlist.voices.all():
            self.database.current_playlist.voices.remove(self.database.current_meme)
            return True
        return False

    def delete_playlist(self):
        self.database.current_playlist.delete()
        self.database.current_playlist = None

    def edit_current_ad(self, message_id: int):
        if self.database.current_ad:
            self.database.current_ad.message_id = message_id
            self.database.current_ad.save()
            return True
        return False

    def get_vote(self, message: dict):
        if matched := check_for_voice(message):
            target_vote = models.Meme.objects.filter(
                file_unique_id=message['voice']['file_unique_id'],
                status=models.Meme.Status.PENDING,
                type=models.MemeType.VOICE
            )
        elif matched := check_for_video(message, True):
            target_vote = models.Meme.objects.filter(
                file_unique_id=message['video']['file_unique_id'],
                status=models.Meme.Status.PENDING,
                type=models.MemeType.VIDEO
            )
        if matched and target_vote.exists():
            return target_vote.first()
        self.send_message(self.translate('unknown_meme'), reply_to_message_id=message['message_id'])

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

    def __check_meme_tags(self, tags: str):
        if 'tags:' in tags:
            raise InvalidMemeTag()
        if len(tags) >= len(punctuation):
            if any(char in tags for char in punctuation):
                raise InvalidMemeTag()
        else:
            if any(char in punctuation for char in tags):
                raise InvalidMemeTag()
        tags = tags.split('\n')
        if len(tags) > 6:
            raise TooManyMemeTags()
        if any(len(tag) > models.MemeTag._meta.get_field('tag').max_length for tag in tags):
            raise LongMemeTag()
        for tag in tags:
            self.database.temp_meme_tags.add(models.MemeTag.objects.get_or_create(tag=tag.strip())[0])

    def process_meme_tags(self, tags: str):
        if not tags:
            self.send_message(self.translate('send_meme_tags', self.temp_meme_translation))
            return False
        try:
            self.__check_meme_tags(tags)
        except ValueError as e:
            self.send_message(self.translate(str(e), self.temp_meme_translation))
            return False
        return True

    def clear_temp_meme_tags(self):
        self.database.temp_meme_tags.clear()

    def initial_meme_check(self, message: dict, meme_type: models.MemeType or int):
        if meme_type == models.MemeType.VOICE:
            if not self.voice_exists(message):
                return False
            initial_check_result = message['voice']['file_id'], message['voice']['file_unique_id']
        else:
            if not check_for_video(message, self.database.rank in models.BOT_ADMINS):
                self.send_message(self.translate('send_a_meme', self.translate('video')))
                return False
            initial_check_result = message['video']['file_id'], message['video']['file_unique_id']
        if models.Meme.objects.filter(
                file_unique_id=initial_check_result[1], visibility=models.Meme.Visibility.NORMAL
        ).exists():
            self.send_message(self.translate('meme_already_exists'))
            return False
        return initial_check_result

    def edit_meme_file(self, message: dict):
        if not (initial_check_result := self.initial_meme_check(message, self.database.current_meme.type)):
            return False
        self.database.current_meme.file_id, self.database.current_meme.file_unique_id = initial_check_result
        self.database.current_meme.save()
        return True

    def add_meme(self, message: dict, status: models.Meme.Status):
        if not (initial_check_result := self.initial_meme_check(message, self.database.temp_meme_type)):
            return False
        new_meme = models.Meme.objects.create(
            file_id=initial_check_result[0],
            file_unique_id=initial_check_result[1],
            name=self.database.temp_meme_name,
            sender=self.database,
            status=status,
            type=self.database.temp_meme_type,
            description=create_description(self.database.temp_meme_tags.all()) if
            self.database.temp_meme_type == models.MemeType.VIDEO else None
        )
        new_meme.tags.set(self.database.temp_meme_tags.all(), clear=True)
        self.database.temp_meme_tags.clear()
        return new_meme

    def validate_meme_name(self, message: dict, text: str, meme_type: models.MemeType or int):
        if not text or \
                message.get('entities') or len(text) > 80 or text.startswith('tags:') or \
                text.startswith('names:'):
            self.send_message(
                self.translate('invalid_meme_name', self.translate(
                    'voice' if meme_type == models.MemeType.VOICE else 'video'
                )),
                reply_to_message_id=message['message_id']
            )
            return False
        return True

    def validate_meme_description(self, text: str, message_id: int, meme_type: models.MemeType or int):
        if not text or len(text) > 120:
            self.send_message(self.translate(
                'invalid_meme_description', self.translate('voice' if meme_type == models.MemeType.VOICE else 'video')
            ), reply_to_message_id=message_id)
            return False
        return True

    def get_public_meme(self, message):
        if matched := check_for_video(message, True):
            file_unique_id = message['video']['file_unique_id']
            meme_type = models.MemeType.VIDEO
            meme_translation = self.translate('video')
        elif matched := check_for_voice(message):
            file_unique_id = message['voice']['file_unique_id']
            meme_type = models.MemeType.VOICE
            meme_translation = self.translate('voice')
        if matched:
            if (target_voice := models.Meme.objects.filter(
                    file_unique_id=file_unique_id,
                    type=meme_type,
                    status=models.Meme.Status.ACTIVE,
                    visibility=models.Meme.Visibility.NORMAL
            )).exists():
                return target_voice.first()
            self.send_message(self.translate('meme_not_found', meme_translation))
            return None
        return False

    def clear_current_playlist(self):
        self.database.current_playlist = None

    def clear_current_meme(self):
        self.database.current_meme = None

    def clear_current_ad(self):
        self.database.current_ad = None

    def menu_cleanup(self):
        self.__perform_back_callback(self.__back_menu.get('callback'))

    def add_recent_meme(self, voice: models.Meme):
        self.database.recent_memes.remove(voice)
        self.database.recent_memes.add(voice)
        if extra_voices := tuple(models.RecentMeme.objects.filter(
                user=self.database
        ).order_by('-id')[20:].values_list('id', flat=True)):
            models.RecentMeme.objects.filter(id__in=extra_voices).delete()

    def send_ordered_meme_list(self, ordering: models.User.Ordering):
        ordered_memes = models.Meme.objects.filter(
            status=models.Meme.Status.ACTIVE, visibility=models.Meme.Visibility.NORMAL
        ).order_by(ordering)[:12]
        return self.send_message(
            make_list_string(ObjectType.SUGGESTED_MEME, ordered_memes), make_meme_list(ordered_memes)
        )

    def clear_recent_memes(self):
        self.database.recent_memes.clear()

    def suggest_meme(self, meme_type: models.MemeType):
        if models.Meme.objects.filter(
                sender=self.database, status=models.Meme.Status.PENDING, type=meme_type
        ).exists():
            return self.send_message(self.translate('pending_meme', self.translate(
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
        return self.send_message(self.translate('meme_name', meme_translation), per_back)

    def get_suggestions(self, page: int, meme_type=models.MemeType):
        return paginate(models.Meme.objects.filter(
            sender=self.database, visibility=models.Meme.Visibility.NORMAL, type=meme_type
        ).exclude(status=models.Meme.Status.PENDING), page)

    def start(self):
        self.menu_cleanup()
        if self.database.rank == self.database.Rank.USER or self.database.menu_mode == self.database.MenuMode.USER:
            self.database.menu = self.database.Menu.USER_MAIN
            self.database.menu_mode = self.database.MenuMode.USER
            return self.send_message(self.translate('welcome'), user_keyboard)
        self.database.menu = self.database.Menu.ADMIN_MAIN
        return self.send_message(self.translate('welcome'), admin)

    def check_current_meme(self):
        if not self.database.current_meme:
            self.send_message(self.translate('meme_not_accessible'))
            self.go_back()
            return False
        return True

    def assign_meme(self):
        if (assigned_meme := models.Meme.objects.filter(
                assigned_admin=self.database,
                reviewed=False,
                visibility=models.Meme.Visibility.NORMAL,
                status=models.Meme.Status.ACTIVE
        )).exists():
            self.database.current_meme = assigned_meme.first()
        elif (new_meme := models.Meme.objects.filter(
                assigned_admin=None,
                reviewed=False,
                status=models.Meme.Status.ACTIVE,
                visibility=models.Meme.Visibility.NORMAL
        )).exists():
            self.database.current_meme = new_meme.first()
            self.database.current_meme.assigned_admin = self.database
            self.database.current_meme.save()
            revoke_review.apply_async((self.database.current_meme.id,), countdown=settings.REVOKE_REVIEW_COUNTDOWN)
        else:
            self.send_message(translations.admin_messages['no_meme_to_review'])
            return False
        self.send_message(
            translations.admin_messages['review_the_meme'],
            meme_review,
            self.database.current_meme.send_meme(
                self.database.chat_id,
                self.session,
                extra_text=self.database.current_meme.description_text
            )
        )
        return True

    @cached_property
    def current_meme_translation(self):
        return self.translate(self.database.current_meme.type_string)

    @cached_property
    def temp_meme_translation(self):
        return self.translate('voice' if self.database.temp_meme_type == models.MemeType.VOICE else 'video')

    def review_current_meme(self):
        self.database.current_meme.reviewed = True
        self.database.current_meme.save()
        self.send_message(self.translate('reviewed', self.current_meme_translation))

    def report_meme(self, meme: models.Meme):
        report, created = models.Report.objects.get_or_create(meme__id=meme.id, defaults={'meme': meme})
        if report.status == models.Report.Status.REVIEWED:
            return ReportResult.REPORT_FAILED
        if created or not report.reporters.filter(user_id=self.database.user_id).exists():
            if created:
                report.meme.send_meme(
                    settings.MEME_REPORTS_CHANNEL, self.session, report_keyboard(report.meme.id)
                )
            report.reporters.add(self.database)
            if report.reporters.count() == settings.VIOLATION_REPORT_LIMIT:
                if report.meme.status == models.Meme.Status.PENDING:
                    report.meme.delete_vote(self.session)
                report.meme.previous_status = report.meme.status
                report.meme.status = models.Meme.Status.REPORTED
                report.meme.save()
            return ReportResult.REPORTED
        return ReportResult.REPORTED_BEFORE

    def edit_meme_tags(self):
        self.database.current_meme.tags.set(self.database.temp_meme_tags.all(), clear=True)
        self.database.temp_meme_tags.clear()
