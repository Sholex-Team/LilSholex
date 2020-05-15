from django.forms import ModelForm, ValidationError, widgets
from groupguard.functions import get_chat_member
from groupguard import models, translators


class Group(ModelForm):
    class Meta:
        model = models.Group
        exclude = ['white_list', 'default_welcome_message', 'words', 'owner', 'last_permissions', 'is_checking']
        widgets = {
            'auto_lock_on': widgets.TimeInput({'type': 'time'}, '%H:%M'),
            'auto_lock_off': widgets.TimeInput({'type': 'time'}, '%H:%M')
        }

    def __init__(self, perms: dict, lang: str, /, **kwargs):
        super().__init__(**kwargs)
        self.user_id = perms['user']['id']
        self.first_name = perms['user']['first_name']
        self.lang = lang
        if perms['status'] != 'creator' and not perms['can_restrict_members']:
            for field in (
                    'id_lock',
                    'link_lock',
                    'curse_lock',
                    'sharp_lock',
                    'text_lock',
                    'forward_lock',
                    'image_lock',
                    'video_lock',
                    'document_lock',
                    'sticker_lock',
                    'location_lock',
                    'phone_number_lock',
                    'voice_message_lock',
                    'video_message_lock',
                    'gif_lock',
                    'game_lock',
                    'english_lock',
                    'persian_lock',
                    'contact_lock',
                    'services_lock',
                    'bot_lock',
                    'punish',
                    'max_warn',
                    'clear_days',
                    'max_warn_punish',
                    'anti_spam',
                    'max_messages',
                    'spam_punish',
                    'spam_time',
                    'rules',
                    'channel',
                    'anti_tabchi',
                    'tabchi_time',
                    'inline_keyboard_lock',
                    'poll_lock',
                    'auto_lock',
                    'auto_lock_on',
                    'auto_lock_off'
            ):
                self.fields[field].disabled = True
                self.fields[field].required = False
        if perms['status'] != 'creator' and not perms['can_change_info']:
            for field in ('is_welcome_message', 'welcome_message', 'rules', 'channel', 'lang'):
                self.fields[field].disabled = True
                self.fields[field].required = False
        for field in ('chat_id', 'status', 'promoted'):
            self.fields[field].disabled = True
            self.fields[field].required = False
        if lang == 'fa':
            for field in self.fields:
                labels = {
                    'chat_id': 'آیدی عددی',
                    'status': 'وضعیت',
                    'channel': 'کانال',
                    'rules': 'قوانین',
                    'lang': 'زبان',
                    'promoted': 'ویژه',
                    'punish': 'جریمه',
                    'clear_days': 'پاک کردن بعد از (روز)',
                    'max_warn': 'حداکثر اخطار ها',
                    'max_warn_punish': 'جریمه',
                    'id_lock': 'آیدی',
                    'curse_lock': 'توهین',
                    'link_lock': 'لینک',
                    'sharp_lock': 'هشتگ',
                    'text_lock': 'متن',
                    'forward_lock': 'فوروارد',
                    'image_lock': 'تصویر',
                    'video_lock': 'ویدیو',
                    'document_lock': 'فایل',
                    'sticker_lock': 'استیکر',
                    'location_lock': 'موقعیت مکانی',
                    'phone_number_lock': 'شماره تلفن',
                    'voice_message_lock': 'ویس',
                    'video_message_lock': 'ویدیو مسیج',
                    'gif_lock': 'گیف',
                    'poll_lock': 'رای گیری',
                    'game_lock': 'بازی',
                    'english_lock': 'متن انگلیسی',
                    'persian_lock': 'متن فارسی',
                    'contact_lock': 'مخاطب',
                    'bot_lock': 'ربات',
                    'services_lock': 'پیام های سرویس',
                    'inline_keyboard_lock': 'کیبورد شیشه ای',
                    'anti_spam': 'آنتی اسپم',
                    'max_messages': 'تعداد پیام مجاز',
                    'spam_punish': 'جریمه',
                    'spam_time': 'زمان اسپم',
                    'is_welcome_message': 'پیام خوش آمد',
                    'welcome_message': 'متن پیام',
                    'reporting': 'گزارش پیام',
                    'max_reports': 'حداکثر گزارش مجاز',
                    'anti_tabchi': 'ضد تبچی',
                    'tabchi_time': 'زمان تایید',
                    'number_range': 'پیش شماره',
                    'deleting': 'حذف پیام های ربات',
                    'delete_time': 'حذف پس از',
                    'force_count': 'تعداد اد',
                    'auto_lock': 'قفل خودکار',
                    'auto_lock_on': 'روشن کردن قفل خودکار',
                    'auto_lock_off': 'خاموش کردن قفل خودکار'
                }
                helps = {
                    'delete_time': 'به ثانیه',
                    'tabchi_time': 'به ثانیه',
                    'welcome_message': 'برای نام کاربر از "first_name" و برای نام گروه از "group_name" استفاده کنید !',
                    'spam_time': 'به ثانیه',
                    'channel': '@آیدی کانال قفل شده',
                    'auto_lock_on': 'ساعت روشن شدن قفل',
                    'auto_lock_off': 'ساعت خاموش شدن قفل'
                }
                try:
                    self.fields[field].label = labels[field]
                    self.fields[field].help_text = helps[field]
                except KeyError:
                    pass

    def clean_channel(self):
        if channel := self.cleaned_data.get('channel', None):
            if channel.startswith('@'):
                if get_chat_member(channel, self.user_id):
                    return channel
                raise ValidationError('Bot is not an admin in this channel !')
            raise ValidationError('Username must start with @ .')

    def clean(self):
        super().clean()
        if self.cleaned_data['auto_lock']:
            if not self.cleaned_data.get('auto_lock_on'):
                self.add_error('auto_lock_on', translators.commands['auto_lock'][self.lang])
            if not self.cleaned_data.get('auto_lock_off'):
                self.add_error('auto_lock_off', translators.commands['auto_lock'][self.lang])
