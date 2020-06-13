from django.db import models
from uuid import uuid4


class Word(models.Model):
    text = models.CharField(max_length=50, primary_key=True, verbose_name='Word')

    class Meta:
        db_table = 'words'

    def __str__(self):
        return self.text


class User(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        banned = 'b', 'Banned'

    class Rank(models.TextChoices):
        admin = 'a', 'Admin'
        user = 'u', 'User'

    class Lang(models.TextChoices):
        persian = 'fa', 'Persian'
        english = 'en', 'English'

    chat_id = models.BigIntegerField(primary_key=True, verbose_name='Chat ID')
    username = models.CharField(max_length=64, verbose_name='Username', null=True, blank=True)
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    status = models.CharField(max_length=1, verbose_name='User Status', choices=Status.choices, default=Status.active)
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.user, verbose_name='User Rank')
    register_date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    last_activity = models.DateTimeField(verbose_name='Last Message Date', auto_now=True)
    lang = models.CharField(max_length=2, verbose_name='Language', choices=Lang.choices, default=Lang.persian)
    phone_number = models.BigIntegerField(null=True, blank=True, verbose_name='Phone Number')
    mutes = models.ManyToManyField('Group', 'user_mutes', verbose_name='Muted In', blank=True)
    number_pass = models.ManyToManyField('Group', 'users_number_passes', verbose_name='Number Pass', blank=True)

    class Meta:
        db_table = 'users'
        ordering = ['chat_id']

    def __str__(self):
        return f'{self.chat_id} : {self.username}'


class Group(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'فعال'
        ads = 'w', 'فعال با تبلیغات'
        banned = 'b', 'بن شده'
        deactive = 'd', 'غیرفعال'

    class ViolationPunish(models.TextChoices):
        warn = 'w', 'اخطار'
        mute = 'm', 'سکوت'
        ban = 'b', 'اخراج'
        nothing = 'n', 'هیچ'

    class Punish(models.TextChoices):
        ban = 'b', 'اخراج'
        mute = 'm', 'سکوت'

    class Lang(models.TextChoices):
        Persian = 'fa', 'فارسی'
        English = 'en', 'English'

    # Information
    chat_id = models.BigIntegerField(primary_key=True, verbose_name='Group ID')
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.active)
    register_date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    owner = models.ForeignKey(User, models.CASCADE, 'owner', verbose_name='Group Owner')
    channel = models.CharField(
        max_length=75, verbose_name='Locked Channel', null=True, blank=True, help_text='Locked channel @username'
    )
    rules = models.TextField(null=True, blank=True, verbose_name='Rules')
    last_permissions = models.CharField(max_length=300, verbose_name='Last Permissions', blank=True, null=True)
    promoted = models.BooleanField(default=False, verbose_name='Promoted')
    # Locks
    id_lock = models.BooleanField(verbose_name='ID Lock', default=False)
    link_lock = models.BooleanField(verbose_name='Link Lock', default=False)
    curse_lock = models.BooleanField(verbose_name='Curse Lock', default=True)
    sharp_lock = models.BooleanField(verbose_name='Sharp Lock', default=False)
    text_lock = models.BooleanField(verbose_name='Text Lock', default=False)
    forward_lock = models.BooleanField(verbose_name='Forward Message Lock', default=True)
    image_lock = models.BooleanField(verbose_name='Image Lock', default=False)
    video_lock = models.BooleanField(verbose_name='Video Lock', default=False)
    document_lock = models.BooleanField(verbose_name='Document Lock', default=False)
    sticker_lock = models.BooleanField(verbose_name='Sticker Lock', default=False)
    location_lock = models.BooleanField(verbose_name='Location Lock', default=True)
    phone_number_lock = models.BooleanField(verbose_name='Phone Number Lock', default=True)
    voice_message_lock = models.BooleanField(verbose_name='Voice Message Lock', default=False)
    video_message_lock = models.BooleanField(verbose_name='Video Message Lock', default=False)
    gif_lock = models.BooleanField(verbose_name='Gif Message Lock', default=False)
    poll_lock = models.BooleanField(verbose_name='Poll Message Lock', default=False)
    game_lock = models.BooleanField(verbose_name='Game Lock', default=True)
    english_lock = models.BooleanField(verbose_name='English Text Lock', default=False)
    persian_lock = models.BooleanField(verbose_name='Persian Or Arabic Text Lock', default=False)
    contact_lock = models.BooleanField(verbose_name='Contact Lock', default=False)
    bot_lock = models.BooleanField(verbose_name='Bot Lock', default=True)
    services_lock = models.BooleanField(verbose_name='Services Lock', default=True)
    inline_keyboard_lock = models.BooleanField(default=False, verbose_name='Inline Keyboard')
    # White List
    white_list = models.ManyToManyField(User, related_name='white_list', verbose_name='White Listed', blank=True)
    # Punishing
    punish = models.CharField(
        max_length=1,
        verbose_name='Punish',
        default=ViolationPunish.nothing,
        choices=ViolationPunish.choices
    )
    max_warn = models.IntegerField(default=5, verbose_name='Max Warnings')
    clear_days = models.IntegerField(default=7, verbose_name='Clear warns after (days)')
    max_warn_punish = models.CharField(
        max_length=1,
        choices=Punish.choices,
        default=Punish.ban,
        verbose_name='Max Warn Punish'
    )
    # Anti Spam
    anti_spam = models.BooleanField(default=True, verbose_name='Anti Spam')
    max_messages = models.IntegerField(default=10, verbose_name='Max Messages')
    spam_punish = models.CharField(max_length=1, choices=Punish.choices, default=Punish.ban, verbose_name='Spam Punish')
    spam_time = models.IntegerField(verbose_name='Clear After', default=10, help_text='in seconds')
    # Filters
    words = models.ManyToManyField(Word, 'words', verbose_name='Filtered Words', blank=True)
    # Welcome Message
    is_welcome_message = models.BooleanField(verbose_name='Welcome Message', default=True)
    welcome_message = models.TextField(
        verbose_name='Welcome message text',
        default='Hi "first_name"\nWelcome to "group_name" !',
        help_text='Use "first_name" for user first name and "group_name" for group title .'
    )
    # Reporting
    reporting = models.BooleanField(verbose_name='Reporting', default=False)
    max_reports = models.IntegerField(verbose_name='Max Reports', default=5)
    # Language
    lang = models.CharField(max_length=2, choices=Lang.choices, default=Lang.Persian, verbose_name='Language')
    # Bot Messages
    delete_time = models.IntegerField(verbose_name='Delete Messages After', help_text='in seconds', default=5)
    deleting = models.BooleanField(default=True, verbose_name='Delete Bot Messages')
    # Anti Tabchi
    anti_tabchi = models.BooleanField(default=False, verbose_name='Anti Tabchi')
    tabchi_time = models.IntegerField(default=120, verbose_name='Verify Until', help_text='in seconds')
    number_range = models.IntegerField(verbose_name='Phone Number Range', null=True, blank=True)
    # Forced Adding
    force_count = models.IntegerField(verbose_name='Forced Add count', null=True, blank=True)
    # Auto Lockdown
    auto_lock = models.BooleanField('Auto Lock', default=False)
    auto_lock_on = models.TimeField('Group Lock on', null=True, blank=True, help_text='Turning on time')
    auto_lock_off = models.TimeField('Group Unlock on', null=True, blank=True, help_text='Turning off time')
    is_checking = models.BooleanField('Is Checking', default=False)

    class Meta:
        db_table = 'groups'
        ordering = ['chat_id']

    def __str__(self):
        return f'{self.chat_id} : {self.status}'

    def save(self, *args, **kwargs):
        if self.auto_lock and not self.is_checking:
            from groupguard.tasks import check_lock
            self.is_checking = True
            check_lock(self.chat_id)
        super().save(*args, **kwargs)


class Warn(models.Model):
    warn_id = models.AutoField(primary_key=True, verbose_name='Warn ID')
    user = models.ForeignKey(User, models.CASCADE, verbose_name='User', related_name='warn_user')
    group = models.ForeignKey(Group, models.CASCADE, verbose_name='Group', related_name='warn_group')
    count = models.IntegerField(verbose_name='Warns Count', default=0)
    last_edit = models.DateTimeField(auto_now=True, verbose_name='Last Warn')

    class Meta:
        db_table = 'warns'
        ordering = ['warn_id']

    def __str__(self):
        return f'{self.warn_id} : {self.count}'


class Login(models.Model):
    login_token = models.UUIDField(default=uuid4, verbose_name='Login UUID', primary_key=True)
    user = models.ForeignKey(User, models.CASCADE, 'login_user', verbose_name='Login User')
    group = models.ForeignKey(Group, models.CASCADE, 'login_group', verbose_name='Login Group')
    login_date = models.DateTimeField(null=True, verbose_name='Login Date', blank=True)
    ip = models.GenericIPAddressField(verbose_name='Last IP Address', null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')

    class Meta:
        ordering = ['login_date']
        db_table = 'logins'

    def __str__(self):
        return f'{self.user} : {self.ip}'


class Message(models.Model):
    message_id = models.AutoField(primary_key=True, verbose_name='Message ID')
    message_unique_id = models.BigIntegerField(verbose_name='Message Unique ID')
    reports = models.IntegerField(default=0, verbose_name='Message\'s Reports')
    reporters = models.ManyToManyField(User, 'reports_users', verbose_name='Reporters')
    group = models.ForeignKey(Group, models.CASCADE, 'messages_group')
    user = models.ForeignKey(User, models.CASCADE, 'messages_user')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')

    class Meta:
        db_table = 'messages'
        ordering = ['-message_id']

    def __str__(self):
        return f'{self.message_id} : {self.message_unique_id}'


class Activity(models.Model):
    activity_id = models.AutoField(primary_key=True, verbose_name='Activity ID')
    user = models.ForeignKey(User, models.CASCADE, 'activity_user', verbose_name='User')
    count = models.IntegerField(verbose_name='Messages Count', default=0)
    group = models.ForeignKey(Group, models.CASCADE, 'activity_group', verbose_name='Group')
    messages = models.ManyToManyField(Message, 'activity_messages', verbose_name='Messages')
    restricted = models.BooleanField(verbose_name='Restricted', default=False)
    last_message = models.DateTimeField(verbose_name='Last Message Date', null=True, blank=True)

    class Meta:
        db_table = 'activities'
        ordering = ['activity_id']
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f'{self.activity_id} : {self.user}'


class Command(models.Model):
    class Rules(models.TextChoices):
        creator = 'c', 'Creator'
        admin = 'a', 'Administrator'
        member = 'm', 'Member'

    command_id = models.AutoField(primary_key=True, verbose_name='Command ID')
    cmd = models.CharField(max_length=50, verbose_name='Command')
    group = models.ForeignKey(Group, models.CASCADE, 'commands_group', verbose_name='Group')
    permission = models.CharField(max_length=1, choices=Rules.choices, verbose_name='Permission')
    answer = models.TextField(verbose_name='Command Answer')

    class Meta:
        db_table = 'commands'
        ordering = ['command_id']

    def __str__(self):
        return f'{self.command_id} : {self.cmd}'


class Curse(models.Model):
    curse_id = models.AutoField(primary_key=True, verbose_name='Curse ID')
    word = models.CharField(max_length=100, verbose_name='Curse Word', unique=True)

    class Meta:
        db_table = 'curses'
        ordering = ['curse_id']

    def __str__(self):
        return f'{self.curse_id} : {self.word}'


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True, verbose_name='Ad ID')
    chat_id = models.BigIntegerField(verbose_name='Ad Chat ID')
    message_id = models.IntegerField(verbose_name='Ad Message ID')
    seen = models.ManyToManyField(Group, 'ad_groups', verbose_name='Seen By')

    class Meta:
        db_table = 'ads'
        ordering = ['ad_id']

    def __str__(self):
        return f'{self.ad_id} : {self.chat_id}'


class Verify(models.Model):
    verify_id = models.AutoField(primary_key=True, verbose_name='Verify ID')
    user = models.ForeignKey(User, models.CASCADE, 'verifies_user', verbose_name='User')
    group = models.ForeignKey(Group, models.CASCADE, 'verifies_group', verbose_name='Group')
    validated = models.BooleanField(default=False, verbose_name='Validated')
    valid_until = models.DateTimeField(verbose_name='Valid Until')

    class Meta:
        ordering = ['verify_id']
        db_table = 'groupguard_verifies'
        verbose_name_plural = 'Verifies'

    def __str__(self):
        return str(self.verify_id)


class ForcedAdd(models.Model):
    add_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.CASCADE, 'added_user', verbose_name='User')
    group = models.ForeignKey(Group, models.CASCADE, 'added_group', verbose_name='Group')
    added_number = models.IntegerField(verbose_name='Adds Count', default=0)
    promoted = models.BooleanField(verbose_name='Promoted', default=False)

    class Meta:
        ordering = ['add_id']
        db_table = 'forced_adds'

    def __str__(self):
        return str(self.add_id)
