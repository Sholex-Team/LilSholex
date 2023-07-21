from json import loads
from django.conf import settings
from persianmeme import keyboards
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.translations import user_messages


def handler(message: dict, text: str, message_id: int, user: UserClass):
    user.database.back_menu = 'main'
    match text:
        case 'راهنما 🔰':
            user.database.menu = User.Menu.USER_HELP
            user.send_message(
                user.translate('help'),
                keyboards.help_keyboard(list(loads(settings.MEME_HELP_MESSAGES).keys()))
            )
        case 'گزارش تخلف 🛑':
            user.database.menu = User.Menu.USER_REPORT_MEME
            user.send_message(user_messages['send_target_meme'], keyboards.per_back, message_id)
        case 'حمایت مالی 💸':
            user.send_message(user.translate('donate'), reply_to_message_id=message_id, parse_mode='Markdown')
        case 'کانال رای‌گیری 🗳':
            user.send_message(user.translate('voting_channel'), keyboards.voting_channel, message_id)
        case 'آخرین میم ها 🆕':
            user.send_ordered_meme_list(user.database.Ordering.new_meme_id)
        case 'ارتباط با مدیریت 📬':
            if user.sent_message:
                user.send_message(user.translate('pending_message'))
            else:
                user.database.menu = User.Menu.USER_CONTACT_ADMIN
                user.send_message(user.translate('send_message'), keyboards.per_back)
        case 'ویس ها 🔊':
            user.database.menu = User.Menu.USER_MANAGE_VOICES
            user.send_message(user.translate('choose'), keyboards.manage_voices)
        case 'ویدئو ها 📹':
            user.database.menu = User.Menu.USER_VIDEO_SUGGESTIONS
            user.send_message(user.translate('choose'), keyboards.video_suggestions)
        case 'میم های محبوب 👌':
            user.send_ordered_meme_list(user.database.Ordering.high_votes)
        case 'پر استفاده ها ⭐':
            user.send_ordered_meme_list(user.database.Ordering.high_usage)
        case 'درخواست حذف میم ✖':
            if user.database.delete_user.exists():
                user.send_message(user.translate('pending_request'))
            else:
                user.database.menu = User.Menu.USER_DELETE_REQUEST
                user.send_message(user.translate('meme'), keyboards.per_back)
        case 'تنظیمات ⚙':
            user.database.menu = User.Menu.USER_SETTINGS
            user.send_message(user.translate('settings'), keyboards.settings)
        case _:
            if (search_result := user.get_public_meme(message)) is False:
                user.send_message(user.translate('unknown_command'))
            elif search_result:
                user.send_message(
                    user.translate('meme_info', user.translate(search_result.type_string), search_result.name),
                    keyboards.use(search_result.id)
                )
