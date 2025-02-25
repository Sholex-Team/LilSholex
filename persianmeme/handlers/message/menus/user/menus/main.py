from django.conf import settings
from persianmeme import keyboards
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.translations import user_messages
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.back_menu = 'main'
    match telegram_context.message.TEXT.get():
        case 'لغو رای‌گیری 🗳':
            user.database.menu = User.Menu.USER_CANCEL_VOTING
            await user.send_message(
                user_messages['meme_type'], keyboards.per_meme_type, telegram_context.common.MESSAGE_ID.get()
            )
        case 'راهنما 🔰':
            user.database.menu = User.Menu.USER_HELP
            await user.send_message(
                user.translate('help'),
                keyboards.help_keyboard(list(settings.MEME_HELP_MESSAGES.keys()))
            )
        case 'گزارش تخلف 🛑':
            user.database.menu = User.Menu.USER_REPORT_MEME
            await user.send_message(
                user_messages['send_target_meme'], keyboards.per_back, telegram_context.common.MESSAGE_ID.get()
            )
        case 'حمایت مالی 💸':
            await user.send_message(
                user.translate('donate'),
                reply_to_message_id=telegram_context.common.MESSAGE_ID.get(),
                parse_mode='Markdown'
            )
        case 'کانال رای‌گیری 🗳':
            await user.send_message(
                user.translate('voting_channel'), keyboards.voting_channel, telegram_context.common.MESSAGE_ID.get()
            )
        case 'آخرین میم ها 🆕':
            await user.send_ordered_meme_list(user.database.Ordering.new_meme_id)
        case 'ارتباط با مدیریت 📬':
            if await user.sent_message:
                await user.send_message(user.translate('pending_message'))
            else:
                user.database.menu = User.Menu.USER_CONTACT_ADMIN
                await user.send_message(user.translate('send_message'), keyboards.per_back)
        case 'ویس ها 🔊':
            user.database.menu = User.Menu.USER_MANAGE_VOICES
            await user.send_message(user.translate('choose'), keyboards.manage_voices)
        case 'ویدئو ها 📹':
            user.database.menu = User.Menu.USER_VIDEO_SUGGESTIONS
            await user.send_message(user.translate('choose'), keyboards.video_suggestions)
        case 'میم های محبوب 👌':
            await user.send_ordered_meme_list(user.database.Ordering.high_votes)
        case 'پر استفاده ها ⭐':
            await user.send_ordered_meme_list(user.database.Ordering.high_usage)
        case 'درخواست حذف میم ✖':
            if await user.database.delete_user.aexists():
                await user.send_message(user.translate('pending_request'))
            else:
                user.database.menu = User.Menu.USER_DELETE_REQUEST
                await user.send_message(user.translate('meme'), keyboards.per_back)
        case 'تنظیمات ⚙':
            user.database.menu = User.Menu.USER_SETTINGS
            await user.send_message(user.translate('settings'), keyboards.settings)
        case _:
            if (search_result := await user.get_public_meme()) is False:
                await user.send_message(user.translate('unknown_command'))
            elif search_result:
                await user.send_message(
                    user.translate('meme_info', user.translate(search_result.type_string), search_result.name),
                    keyboards.use(search_result.newmeme_ptr_id),
                    telegram_context.common.MESSAGE_ID.get()
                )
