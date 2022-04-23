import json
import requests
from django.conf import settings
from django.db import models
from LilSholex.decorators import sync_fix
from .keyboards import meme_recovery, suggestion_vote
from asgiref.sync import sync_to_async
from uuid import uuid4
from . import translations
from functools import cached_property
from LilSholex.exceptions import TooManyRequests
from LilSholex.celery import celery_app


class MemeType(models.IntegerChoices):
    VOICE = 0, 'Voice'
    VIDEO = 1, 'Video'


class MemeTag(models.Model):
    tag = models.CharField(max_length=20, verbose_name='Tag Content', primary_key=True)

    class Meta:
        ordering = ['tag']
        db_table = 'persianmeme_meme_tags'


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
        ADMIN_ADD_AD = 10, 'Admin Add Ad'
        ADMIN_DELETE_AD = 11, 'Admin Delete Ad'
        ADMIN_GET_USER = 12, 'Admin Get User'
        ADMIN_BROADCAST = 13, 'Admin Broadcast'
        ADMIN_EDIT_AD_ID = 14, 'Admin Edit Ad ID'
        ADMIN_EDIT_AD = 15, 'Admin Edit Ad'
        ADMIN_BAN_VOTE = 16, 'Admin Ban Vote'
        ADMIN_GET_MEME = 40, 'Admin Get Meme'
        ADMIN_MEME_TAGS = 42, 'Admin Meme Tags'
        ADMIN_SEND_EDIT_MEME = 44, 'Admin Send Edit Meme'
        ADMIN_EDIT_MEME = 45, 'Admin Edit Meme'
        ADMIN_EDIT_MEME_NAME = 46, 'Admin Edit Meme Name'
        ADMIN_EDIT_MEME_TAGS = 47, 'Admin Edit Meme Tags'
        ADMIN_FILE_ID = 48, 'Admin File ID'
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

    user_id = models.AutoField(verbose_name='User ID', primary_key=True, unique=True)
    chat_id = models.BigIntegerField(verbose_name='Chat ID', unique=True)
    menu = models.PositiveSmallIntegerField(verbose_name='Current Menu', choices=Menu.choices, default=Menu.USER_MAIN)
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.ACTIVE)
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.USER)
    username = models.CharField(max_length=35, null=True, blank=True)
    temp_meme_name = models.CharField(max_length=80, null=True, verbose_name='Temporary Meme Name', blank=True)
    temp_user_id = models.BigIntegerField(null=True, verbose_name='Temporary User ID', blank=True)
    temp_meme_tags = models.ManyToManyField(
        MemeTag, 'user_voice_tags', blank=True, verbose_name='Temporary Voice Tags'
    )
    last_usage_date = models.DateTimeField(auto_now=True)
    vote = models.BooleanField(verbose_name='Vote System', default=False)
    date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    meme_ordering = models.CharField(max_length=12, choices=Ordering.choices, default=Ordering.new_meme_id)
    back_menu = models.CharField(max_length=50, null=True, blank=True)
    started = models.BooleanField('Started', default=False)
    last_start = models.DateTimeField(null=True, blank=True)
    last_broadcast = models.ForeignKey('Broadcast', models.SET_NULL, 'user_broadcast', null=True, blank=True)
    playlists = models.ManyToManyField('Playlist', 'user_playlist', blank=True)
    current_playlist = models.ForeignKey(
        'Playlist',
        models.SET_NULL,
        'user_current_playlist',
        blank=True, null=True,
        verbose_name='Current Playlist',
        default=None
    )
    current_meme = models.ForeignKey('Meme', models.SET_NULL, 'user_voice', blank=True, null=True, default=None)
    current_ad = models.ForeignKey('Ad', models.SET_NULL, 'user_ad', null=True, blank=True)
    menu_mode = models.CharField(
        max_length=1, verbose_name='Menu Mode', choices=MenuMode.choices, default=MenuMode.USER
    )
    recent_memes = models.ManyToManyField(
        'Meme', 'recent_memes', blank=True, verbose_name='Recent Memes', through='RecentMeme'
    )
    use_recent_memes = models.BooleanField('Use Recent Memes', default=True)
    temp_meme_type = models.PositiveSmallIntegerField(
        'Temporary Meme Type', blank=True, null=True, choices=MemeType.choices
    )
    report_violation_count = models.PositiveSmallIntegerField(default=0)
    search_items = models.PositiveSmallIntegerField(choices=SearchItems.choices, default=SearchItems.BOTH)

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ['user_id']

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class Meme(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        PENDING = 'p', 'Pending'
        DELETED = 'd', 'Deleted'
        REPORTED = 'r', 'Reported'

    class Visibility(models.TextChoices):
        NORMAL = 'n', 'Normal'
        PRIVATE = 'p', 'Private'

    message_id = models.BigIntegerField(verbose_name='Message ID', null=True, blank=True)
    file_id = models.CharField(max_length=128, verbose_name='Meme File ID')
    file_unique_id = models.CharField(max_length=64, verbose_name='Meme Unique ID')
    name = models.CharField(max_length=256)
    sender = models.ForeignKey(User, models.CASCADE, related_name='senders')
    voters = models.ManyToManyField(User, related_name='voters', blank=True)
    votes = models.IntegerField(default=0, verbose_name='Up Votes')
    status = models.CharField(max_length=1, choices=Status.choices)
    previous_status = models.CharField(
        max_length=1, choices=Status.choices, null=True, blank=True, verbose_name='Status Before Reporting'
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    visibility = models.CharField(max_length=1, choices=Visibility.choices, default=Visibility.NORMAL)
    accept_vote = models.ManyToManyField(User, 'accept_vote_users', blank=True, verbose_name='Accept Votes')
    deny_vote = models.ManyToManyField(User, 'deny_vote_users', blank=True, verbose_name='Deny Votes')
    tags = models.ManyToManyField(MemeTag, 'meme_tags', blank=True)
    usage_count = models.PositiveIntegerField('Usage Count', default=0)
    assigned_admin = models.ForeignKey(
        User, models.SET_NULL, 'meme_admin', verbose_name='Assigned Admin', null=True, blank=True
    )
    reviewed = models.BooleanField('Is Reviewed', default=False)
    type = models.PositiveSmallIntegerField('Meme Type', choices=MemeType.choices, default=MemeType.VOICE)
    description = models.CharField(max_length=120, blank=True, null=True)
    task_id = models.CharField(max_length=36, blank=True, null=True)

    class Meta:
        db_table = 'persianmeme_memes'
        ordering = ['-id']

    def __str__(self):
        return f'{self.name}:{self.file_id}'

    def accept(self, session: requests.Session = requests.Session()):
        from .functions import send_message
        self.delete_vote(session)
        self.status = self.Status.ACTIVE
        self.save()
        self.accept_vote.clear()
        self.deny_vote.clear()
        send_message(self.sender.chat_id, translations.user_messages['meme_accepted'].format(
            translations.user_messages[self.type_string]
        ), session)

    def deny(self, session: requests.Session = requests.Session()):
        from .functions import send_message
        self.delete_vote(session)
        send_message(self.sender.chat_id, translations.user_messages['meme_denied'].format(
            translations.user_messages[self.type_string]
        ), session)
        self.delete()

    @property
    def description_text(self):
        return translations.admin_messages['description'].format(self.description) \
            if self.type == MemeType.VIDEO else str()

    @sync_fix
    def send_meme(
            self,
            chat_id: int,
            session: requests.Session = requests.Session(),
            meme_keyboard: dict = None,
            extra_text: str = ''
    ) -> int:
        tags_string = str()
        for tag in self.tags.all():
            tags_string += f'\n<code>{tag.tag}</code>'
        meme_dict = {
            'caption': f'{extra_text}<b>Meme Name</b>: <code>{self.name}</code>\n\n<b>Meme Tags 👇</b>{tags_string}',
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
        with session.get(
                f'https://api.telegram.org/bot{settings.MEME}/send{request_type}',
                params=meme_dict,
                timeout=settings.REQUESTS_TIMEOUT * 10
        ) as response:
            if response.status_code == 200:
                return response.json()['result']['message_id']
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @cached_property
    def type_string(self):
        return 'video' if self.type == MemeType.VIDEO else 'voice'

    def ban_sender(self, session: requests.Session = requests.Session()):
        self.sender.status = self.sender.Status.BANNED
        self.sender.save()
        self.deny(session)

    def delete(self, *args, **kwargs):
        if kwargs.get('log'):
            self.send_meme(
                settings.MEME_LOGS,
                kwargs.get('http_session', requests.Session()),
                meme_recovery(self.id),
                translations.admin_messages['deleted_by_admins'].format(
                    translations.admin_messages[self.type_string],
                    kwargs.pop('admin'),
                    self.file_id
                )
            )
            self.status = self.Status.DELETED
            return self.save()
        super().delete(*args, **kwargs)

    @sync_fix
    def delete_vote(self, session: requests.Session = requests.Session()):
        celery_app.control.revoke(self.task_id)
        with session.get(
                f'https://api.telegram.org/bot{settings.MEME}/deleteMessage',
                params={'chat_id': settings.MEME_CHANNEL, 'message_id': self.message_id},
                timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    def send_vote(self, session: requests.Session = requests.Session()):
        from persianmeme.tasks import check_meme

        self.message_id = self.send_meme(
            settings.MEME_CHANNEL,
            session,
            suggestion_vote(self.id)
        )
        self.save()
        self.task_id = check_meme.apply_async((self.id,), countdown=settings.CHECK_MEME_COUNTDOWN)
        self.save()


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True, verbose_name='Ad ID')
    chat_id = models.BigIntegerField(verbose_name='Chat ID')
    message_id = models.IntegerField(verbose_name='Message ID')
    seen = models.ManyToManyField(User, 'mass_seens', verbose_name='Seen By', blank=True)

    class Meta:
        db_table = 'persianmeme_ads'
        ordering = ['ad_id']

    def __str__(self):
        return str(self.ad_id)


class Delete(models.Model):
    meme = models.ForeignKey(Meme, models.CASCADE, 'delete_meme')
    user = models.ForeignKey(User, models.CASCADE, 'delete_user')

    class Meta:
        db_table = 'persianmeme_deletes'

    def __str__(self):
        return f'{self.id} : {self.meme.id}'


class Broadcast(models.Model):
    message_id = models.IntegerField('Message ID')
    sender = models.ForeignKey(User, models.CASCADE, 'broadcast_user', verbose_name='Sender Admin')
    sent = models.BooleanField('Is Sent', default=False)

    @property
    @sync_to_async
    def get_sender(self):
        return self.sender

    def __str__(self):
        return f'{self.id}:{self.message_id}'

    class Meta:
        db_table = 'persianmeme_broadcasts'
        ordering = ['id']


class Playlist(models.Model):
    invite_link = models.UUIDField('Invite ID', default=uuid4)
    name = models.CharField(max_length=60)
    voices = models.ManyToManyField(Meme, 'playlist_voice')
    creator = models.ForeignKey(User, models.CASCADE)
    date = models.DateTimeField('Creation Date', auto_now_add=True)

    def get_link(self):
        return f'https://t.me/Persian_Meme_Bot?start={self.invite_link}'

    class Meta:
        db_table = 'persianmeme_playlists'
        ordering = ['-date']

    def __str__(self):
        return f'{self.name}:{self.creator.chat_id}'


class Message(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, 'Pending'
        READ = 2, 'Read'

    sender = models.ForeignKey(User, models.CASCADE, 'message_user')
    message_id = models.PositiveBigIntegerField('Message ID')
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = 'persianmeme_messages'

    def __str__(self):
        return f'{self.id} : {self.sender.chat_id}'


class RecentMeme(models.Model):
    user = models.ForeignKey(User, models.CASCADE, 'recent_meme_user')
    meme = models.ForeignKey(Meme, models.CASCADE, 'recent_meme_meme')

    class Meta:
        ordering = ['-id']
        db_table = 'persianmeme_user_recent_memes'


class Report(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, 'Pending'
        REVIEWED = 1, 'Reviewed'

    meme = models.OneToOneField(
        Meme, models.CASCADE, related_name='report_meme', verbose_name='Reported Meme', primary_key=True
    )
    reporters = models.ManyToManyField(User, 'report_users', blank=False)
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)
    report_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'persianmeme_reports'


BOT_ADMINS = (User.Rank.ADMIN, User.Rank.OWNER)
