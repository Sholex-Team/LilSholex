from django.db import models


class User(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        banned = 'b', 'Banned'
        full_banned = 'f', 'Full Banned'

    class Rank(models.TextChoices):
        owner = 'o', 'Owner'
        user = 'u', 'User'
        admin = 'a', 'Admin'
        semi_admin = 's', 'Semi Admin'

    class VoiceOrder(models.TextChoices):
        votes = 'votes', 'Votes (Low to High)'
        voice_id = 'voice_id', 'Voice ID (Old to New)'
        high_votes = '-vote', 'Votes (High to Low)'
        new_voice_id = '-voice_id', 'Voice ID (New to Old)'

    user_id = models.AutoField(verbose_name='User ID', primary_key=True, unique=True)
    chat_id = models.BigIntegerField(verbose_name='User Chat ID', unique=True)
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.active,
        verbose_name='Current Status'
    )
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.user, verbose_name='User Rank')
    sent_message = models.BooleanField(verbose_name='Sent Message', default=False)
    username = models.CharField(max_length=255, verbose_name='Username', null=True, blank=True)
    sent_voice = models.BooleanField(verbose_name='Sent Voice', default=False)
    temp_voice_name = models.CharField(max_length=200, null=True)
    temp_user_id = models.BigIntegerField(null=True)
    last_date = models.BigIntegerField()
    count = models.IntegerField(default=1)
    last_usage_date = models.DateTimeField(auto_now=True, verbose_name='Last Usage Date')
    vote = models.BooleanField(verbose_name='Vote System', default=False)
    date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    voice_order = models.CharField(max_length=9, choices=VoiceOrder.choices, default=VoiceOrder.new_voice_id)
    delete_request = models.BooleanField(default=False, verbose_name='Delete Request')
    private_voices = models.ManyToManyField('Voice', 'private_voices', verbose_name='Private Voices')
    favorite_voices = models.ManyToManyField('Voice', 'favorite_voices', verbose_name='Favorite Voices')

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ['user_id']

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class Voice(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        pending = 'p', 'Pending'

    class Type(models.TextChoices):
        normal = 'n', 'Normal'
        private = 'p', 'Private'

    voice_id = models.AutoField(verbose_name='Voice ID', unique=True, primary_key=True)
    file_id = models.CharField(max_length=200, verbose_name='Voice File ID')
    file_unique_id = models.CharField(max_length=100, verbose_name='Voice Unique ID')
    name = models.CharField(max_length=200, verbose_name='Voice Name')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Voice Sender', related_name='senders')
    voters = models.ManyToManyField(User, verbose_name='Voters', related_name='voters', blank=True)
    votes = models.IntegerField(default=0, verbose_name='Up Votes')
    status = models.CharField(max_length=1, choices=Status.choices, verbose_name='Voice Status')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    voice_type = models.CharField(max_length=1, choices=Type.choices, default=Type.normal, verbose_name='Voice Type')

    class Meta:
        db_table = 'persianmeme_voices'
        ordering = ['-voice_id']

    def __str__(self):
        return f'{self.name}:{self.file_id}'


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True, verbose_name='Mass ID')
    chat_id = models.BigIntegerField(verbose_name='Chat ID')
    message_id = models.IntegerField(verbose_name='Message ID')
    seen = models.ManyToManyField(User, 'mass_seens', verbose_name='Seen By', blank=True)

    class Meta:
        db_table = 'persianmeme_ads'
        ordering = ['ad_id']

    def __str__(self):
        return str(self.ad_id)
