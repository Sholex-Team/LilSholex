import json
from django.conf import settings
from django.db import models
from LilSholex.decorators import async_fix
from .keyboards import meme_recovery, suggestion_vote
from asgiref.sync import sync_to_async
from uuid import uuid4
from . import translations
from functools import cached_property
from LilSholex.exceptions import TooManyRequests
from LilSholex.celery import celery_app
from django.utils.html import escape
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


class MemeType(models.IntegerChoices):
    VOICE = 0, 'Voice'
    VIDEO = 1, 'Video'


class User(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        BANNED = 'b', 'Banned'
        FULL_BANNED = 'f', 'Full Banned'

    class Rank(models.TextChoices):
        OWNER = 'o', 'Owner'
        USER = 'u', 'User'
        ADMIN = 'a', 'Admin'
        KHIAR = 'k', 'Khiar'

    class Ordering(models.TextChoices):
        votes = 'votes', 'Votes (Low to High)'
        meme_id = 'id', 'Meme ID (Old to New)'
        high_votes = '-votes', 'Votes (High to Low)'
        new_meme_id = '-id', 'Meme ID (New to Old)'
        high_usage = '-usage_count', 'Usage Count (High to Low)'
        low_usage = 'usage_count', 'Usage Count (Low to High)'

    class MenuMode(models.TextChoices):
        ADMIN = 'a', 'Admin'
        USER = 'u', 'User'

    class SearchItems(models.IntegerChoices):
        VOICES = 0, 'Voices'
        VIDEOS = 1, 'Videos'
        BOTH = 2, 'Voices & Videos'

    class Menu(models.IntegerChoices):
        ADMIN_MAIN = 1, 'Admin Main Menu'
        ADMIN_MEME_NAME = 2, 'Admin Meme Name',
        ADMIN_NEW_MEME = 3, 'Admin New Meme'
        ADMIN_DELETE_MEME = 4, 'Admin Delete Meme'
        ADMIN_BAN_USER = 5, 'Admin Ban User'
        ADMIN_UNBAN_USER = 6, 'Admin Unban User'
        ADMIN_FULL_BAN_USER = 7, 'Admin Full Ban User'
        ADMIN_MESSAGE_USER_ID = 8, 'Admin Message User ID'
        ADMIN_MESSAGE_USER = 9, 'Admin Message User'
        ADMIN_GET_USER = 12, 'Admin Get User'
        ADMIN_BROADCAST = 13, 'Admin Broadcast'
        ADMIN_BAN_VOTE = 16, 'Admin Ban Vote'
        ADMIN_GET_MEME = 40, 'Admin Get Meme'
        ADMIN_MEME_TAGS = 42, 'Admin Meme Tags'
        ADMIN_SEND_EDIT_MEME = 44, 'Admin Send Edit Meme'
        ADMIN_EDIT_MEME = 45, 'Admin Edit Meme'
        ADMIN_EDIT_MEME_NAME = 46, 'Admin Edit Meme Name'
        ADMIN_EDIT_MEME_TAGS = 47, 'Admin Edit Meme Tags'
        ADMIN_EDIT_MEME_FILE = 66, 'Admin Edit Meme File'
        ADMIN_FILE_ID = 48, 'Admin File ID'
        ADMIN_MEME_REVIEW_TYPE = 67, 'Admin Meme Review Type'
        ADMIN_MEME_REVIEW = 54, 'Admin Meme Review'
        ADMIN_BROADCAST_STATUS = 55, 'Admin Broadcast Status'
        ADMIN_MEME_TYPE = 57, 'Admin Meme Type'
        ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION = 62, 'Admin Edit Meme Tags and Description'
        ADMIN_EDIT_MEME_DESCRIPTION = 63, 'Admin Edit Meme Description'
        ADMIN_GOD_MODE = 65, 'Admin God Mode'
        USER_MAIN = 19, 'User Main'
        USER_CONTACT_ADMIN = 20, 'User Contact Admin'
        USER_SUGGEST_MEME_NAME = 21, 'User Suggest Meme Name'
        USER_SUGGEST_MEME = 22, 'User Suggest Meme'
        USER_RANKING = 24, 'User Ranking'
        USER_SORTING = 25, 'User Sorting'
        USER_DELETE_REQUEST = 26, 'User Delete Request'
        USER_PRIVATE_VOICES = 27, 'User Private Voices'
        USER_PRIVATE_VOICE_NAME = 28, 'User Private Voice Name'
        USER_MANAGE_PRIVATE_VOICE = 29, 'User Manage Private Voice'
        USER_PRIVATE_VOICE = 30, 'User Private Voice'
        USER_PLAYLISTS = 35, 'User Playlists'
        USER_CREATE_PLAYLIST = 36, 'User Create Playlist'
        USER_MANAGE_PLAYLIST = 37, 'User Manage Playlist'
        USER_ADD_VOICE_PLAYLIST = 38, 'User Add Voice To Playlist'
        USER_MANAGE_PLAYLIST_VOICE = 39, 'User Manager Playlist Voice'
        USER_SUGGEST_MEME_TAGS = 41, 'User Suggest Meme Tags'
        USER_PRIVATE_VOICE_TAGS = 43, 'User Private Voice Tags'
        USER_HELP = 49, 'User Help'
        USER_SETTINGS = 50, 'User Settings'
        USER_RECENT_VOICES = 51, 'User Recent Voices'
        USER_VOICE_SUGGESTIONS = 52, 'User Voice Suggestions'
        USER_MANAGE_VOICE_SUGGESTION = 53, 'User Manage Voice Suggestion'
        USER_VIDEO_SUGGESTIONS = 60, 'User Video Suggestions'
        USER_MANAGE_VOICES = 56, 'User Manage Voices'
        USER_MANAGE_VIDEO_SUGGESTION = 61, 'User Manager Video Suggestion'
        USER_SUGGEST_MEME_TYPE = 58, 'User Suggest Meme Type'
        USER_REPORT_MEME = 59, 'User Report Meme'
        USER_SEARCH_ITEMS = 64, 'User Search Items'
        USER_CANCEL_VOTING = 68, 'User Cancel Voting'

    user_id = models.AutoField(primary_key=True, unique=True)
    chat_id = models.BigIntegerField(unique=True)
    menu = models.PositiveSmallIntegerField(choices=Menu, default=Menu.USER_MAIN)
    status = models.CharField(max_length=1, choices=Status, default=Status.ACTIVE)
    rank = models.CharField(max_length=1, choices=Rank, default=Rank.USER)
    temp_meme_name = models.CharField(max_length=80, null=True, blank=True)
    temp_user_id = models.BigIntegerField(null=True, blank=True)
    temp_meme_tags = models.TextField(blank=True, null=True, max_length=125)
    last_usage_date = models.DateTimeField(auto_now=True)
    vote = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    meme_ordering = models.CharField(max_length=12, choices=Ordering, default=Ordering.new_meme_id)
    back_menu = models.CharField(max_length=50, null=True, blank=True)
    started = models.BooleanField(default=False)
    last_start = models.DateTimeField(null=True, blank=True)
    last_broadcast = models.ForeignKey('Broadcast', models.SET_NULL, 'user_broadcast', null=True, blank=True)
    playlists = models.ManyToManyField('Playlist', 'users', blank=True)
    current_playlist = models.ForeignKey(
        'Playlist',
        models.SET_NULL,
        'user_current_playlist',
        blank=True,
        null=True,
        default=None
    )
    current_meme = models.ForeignKey(
        'Meme', models.SET_NULL, 'user_current_memes', blank=True, null=True
    )
    menu_mode = models.CharField(max_length=1, choices=MenuMode, default=MenuMode.USER)
    recent_memes = models.ManyToManyField('NewMeme', 'recent_memes', blank=True, through='RecentMeme')
    use_recent_memes = models.BooleanField(default=True)
    temp_meme_type = models.PositiveSmallIntegerField(blank=True, null=True, choices=MemeType)
    report_violation_count = models.PositiveSmallIntegerField(default=0)
    search_items = models.PositiveSmallIntegerField(choices=SearchItems, default=SearchItems.BOTH)

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ('user_id',)
        indexes = (models.Index(fields=('chat_id',)),)

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class NewMeme(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        PENDING = 'p', 'Pending'
        DELETED = 'd', 'Deleted'
        REPORTED = 'r', 'Reported'

    class Visibility(models.TextChoices):
        NORMAL = 'n', 'Normal'
        PRIVATE = 'p', 'Private'

    file_id = models.CharField(max_length=128)
    file_unique_id = models.CharField(max_length=64)
    name = models.CharField(max_length=256)
    sender = models.ForeignKey(User, models.CASCADE, related_name='sent_memes')
    status = models.CharField(max_length=1, choices=Status)
    visibility = models.CharField(max_length=1, choices=Visibility, default=Visibility.NORMAL)
    tags = models.CharField(max_length=125, blank=True, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    type = models.PositiveSmallIntegerField(choices=MemeType, default=MemeType.VOICE)
    description = models.CharField(max_length=120, blank=True, null=True)
    votes = models.IntegerField(default=0)
    playlist_voice = models.ForeignKey('PlaylistVoice', models.CASCADE, 'memes', blank=True, null=True)
    last_applied_change = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ('-id',)
        constraints = (
            models.UniqueConstraint(fields=('file_unique_id', 'sender'), name='unique_sender_meme'),
            models.UniqueConstraint(
                fields=('file_unique_id',), condition=models.Q(visibility='n'), name='unique_public_meme'
            ),
            models.UniqueConstraint(
                fields=('sender', 'type'), condition=models.Q(status__in=('p', 'r')), name='unique_pending_meme'
            )
        )
        indexes = (
            models.Index(
                fields=('status', 'type'), include=('id', 'file_id', 'name', 'description'), name='memes_index_1'
            ),
            models.Index(
                fields=('id',), include=('file_id', 'name', 'type', 'description'), name='memes_index_2'
            ),
            models.Index(
                fields=('status', 'visibility'),
                include=('id', 'file_id', 'name', 'type', 'description'),
                name='memes_index_3'
            ),
            models.Index(
                fields=('sender', 'visibility'),
                include=('id', 'file_id', 'name', 'type', 'description'),
                name='memes_index_4'
            ),
            models.Index(
                fields=('status', 'visibility', 'type'),
                include=('id', 'file_id', 'name', 'description'),
                name='memes_index_5'
            ),
            models.Index(
                fields=('sender', 'visibility', 'type'),
                include=('id', 'file_id', 'name', 'description'),
                name='memes_index_6'
            )
        )

    def __str__(self):
        return f'{self.name}:{self.file_id}'


class Meme(NewMeme):
    message_id = models.BigIntegerField(null=True, blank=True)
    task_id = models.CharField(max_length=36, blank=True, null=True)
    review_admin = models.ForeignKey(User, models.SET_NULL, 'reviewed_memes', null=True, blank=True)
    reviewed = models.BooleanField(default=False)
    accept_vote = models.ManyToManyField(User, 'accepted_memes', blank=True)
    deny_vote = models.ManyToManyField(User, 'denied_memes', blank=True)
    voters = models.ManyToManyField(User, related_name='voters', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    previous_status = models.CharField(max_length=1, choices=NewMeme.Status, null=True, blank=True)

    @async_fix
    async def send_meme(
            self,
            chat_id: int,
            meme_keyboard: dict = None,
            extra_text: str = ''
    ) -> int:
        tags_string = str()
        if self.tags:
            for tag in self.tags.split('\n'):
                tags_string += f'\n<code>{escape(tag)}</code>'
        meme_dict = {
            'caption': f'{extra_text}<b>Meme Name</b>: <code>{escape(self.name)}</code>'
                       f'\n\n<b>Meme Tags 👇</b>{tags_string}',
            'parse_mode': 'HTML',
            'chat_id': chat_id
        }
        if meme_keyboard:
            meme_dict['reply_markup'] = json.dumps(meme_keyboard)
        if self.type == MemeType.VOICE:
            meme_dict['voice'] = self.file_id
            request_type = 'Voice'
        else:
            meme_dict['video'] = self.file_id
            request_type = 'Video'
        async with telegram_context.common.HTTP_SESSION.get().get(
            f'https://api.telegram.org/bot{settings.MEME_TOKEN}/send{request_type}',
            params=meme_dict,
            timeout=settings.REQUESTS_TIMEOUT * 10
        ) as response:
            if response.status == 200:
                return (await response.json())['result']['message_id']
            elif response.status == 429:
                raise TooManyRequests((await response.json())['parameters']['retry_after'])
            return 0

    @cached_property
    def type_string(self):
        return 'video' if self.type == MemeType.VIDEO else 'voice'

    async def adelete(self, *args, **kwargs):
        if kwargs.get('log'):
            self.status = self.Status.DELETED
            async with TaskGroup() as tg:
                tg.create_task(self.send_meme(
                    settings.MEME_LOGS,
                    meme_recovery(self.id),
                    translations.admin_messages['deleted_by_admins'].format(
                        translations.admin_messages[self.type_string],
                        kwargs.pop('admin'),
                        self.file_id
                    )
                ))
                tg.create_task(self.asave(update_fields=('status',)))
        else:
            return await super().adelete(*args, **kwargs)

    @async_fix
    async def delete_vote(self):
        from .functions import delete_vote

        if self.task_id:
            celery_app.control.revoke(self.task_id)
        if self.message_id:
            await delete_vote(self.message_id)

    async def send_vote(self):
        from persianmeme.tasks import check_meme

        if message_id := await self.send_meme(settings.MEME_CHANNEL, suggestion_vote(self.id)):
            self.message_id = message_id
            await self.asave(update_fields=('message_id',))
        self.task_id = check_meme.apply_async((self.id,), countdown=settings.CHECK_MEME_COUNTDOWN)

    async def accept(self):
        from .functions import send_message

        self.status = self.Status.ACTIVE
        async with TaskGroup() as tg:
            tg.create_task(self.delete_vote())
            tg.create_task(self.asave(update_fields=('status',)))
            tg.create_task(sync_to_async(self.accept_vote.clear)())
            tg.create_task(sync_to_async(self.deny_vote.clear)())
            tg.create_task(send_message(self.sender.chat_id, translations.user_messages['meme_accepted'].format(
                translations.user_messages[self.type_string]
            )))

    async def deny(self):
        from .functions import send_message

        async with TaskGroup() as tg:
            tg.create_task(self.delete_vote())
            tg.create_task(send_message(self.sender.chat_id, translations.user_messages['meme_denied'].format(
                translations.user_messages[self.type_string]
            )))
            tg.create_task(self.adelete())

    @property
    def description_text(self):
        return translations.admin_messages['description'].format(escape(self.description)) \
            if self.type == MemeType.VIDEO else str()

    class Meta:
        ordering = ('-id',)


class Delete(models.Model):
    meme = models.ForeignKey(Meme, models.CASCADE, 'delete_requests')
    user = models.ForeignKey(User, models.CASCADE, 'delete_user')

    class Meta:
        ordering = ('id',)
        db_table = 'persianmeme_deletes'

    def __str__(self):
        return f'{self.id} : {self.meme.id}'


class Broadcast(models.Model):
    message_id = models.IntegerField('Message ID')
    sender = models.ForeignKey(User, models.CASCADE, 'broadcast_user')
    sent = models.BooleanField('Is Sent', default=False)

    def __str__(self):
        return f'{self.id}:{self.message_id}'

    class Meta:
        db_table = 'persianmeme_broadcasts'
        ordering = ('id',)


class PlaylistVoice(models.Model):
    playlist = models.ForeignKey('Playlist', models.CASCADE, 'playlist_voices')
    voice = models.ForeignKey('Meme', models.CASCADE, 'playlist_voices')
    last_change = models.UUIDField(default=uuid4)

    class Meta:
        ordering = ('-id',)
        constraints = (models.UniqueConstraint(fields=('playlist', 'voice'), name='unique_playlist_voice'),)


class Playlist(models.Model):
    invite_link = models.UUIDField('Invite ID', default=uuid4)
    name = models.CharField(max_length=60)
    creator = models.ForeignKey(User, models.CASCADE)
    voices = models.ManyToManyField('Meme', 'playlists', through=PlaylistVoice, blank=True)

    def get_link(self):
        return f'https://t.me/Persian_Meme_Bot?start={self.invite_link}'

    class Meta:
        db_table = 'persianmeme_playlists'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.name}:{self.creator.chat_id}'


class Message(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, 'Pending'
        READ = 2, 'Read'

    sender = models.ForeignKey(User, models.CASCADE, 'message_user')
    message_id = models.PositiveBigIntegerField('Message ID')
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.PENDING)

    class Meta:
        ordering = ('id',)
        db_table = 'persianmeme_messages'

    def __str__(self):
        return f'{self.id} : {self.sender.chat_id}'


class RecentMeme(models.Model):
    user = models.ForeignKey(User, models.CASCADE, 'recent_meme_user')
    meme = models.ForeignKey(NewMeme, models.CASCADE, 'recent_meme_meme')

    class Meta:
        ordering = ('-id',)
        indexes = (
            models.Index(fields=('user',), include=('id', 'meme'), name='recent_memes_index_1'),
            models.Index(fields=('user', 'meme'), name='recent_memes_index_2')
        )
        constraints = (models.UniqueConstraint(fields=('user', 'meme'), name='unique_recent_meme'),)
        db_table = 'persianmeme_user_recent_memes'


class Report(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, 'Pending'
        REVIEWED = 1, 'Reviewed'

    meme = models.OneToOneField(
        Meme, models.CASCADE, related_name='report_meme', primary_key=True
    )
    reporters = models.ManyToManyField(User, 'report_users', blank=False)
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.PENDING)
    reviewer = models.ForeignKey(User, models.SET_NULL, 'reviewed_reports', blank=True, null=True)
    report_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'persianmeme_reports'
        ordering = ('report_date',)


class Username(models.Model):
    user = models.ForeignKey(User, models.CASCADE, 'usernames')
    username = models.CharField(max_length=35)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id',)
        constraints = (models.UniqueConstraint(fields=('user', 'username'), name='unique_usernames'),)
        indexes = (models.Index(fields=('username', 'id')),)

    def __str__(self):
        return f'{self.user.chat_id} : {self.username}'


ADMINS = (User.Rank.ADMIN, User.Rank.KHIAR, User.Rank.OWNER)
HIGH_LEVEL_ADMINS = (User.Rank.ADMIN, User.Rank.OWNER)
