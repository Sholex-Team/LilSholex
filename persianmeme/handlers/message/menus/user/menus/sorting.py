from persianmeme.keyboards import settings
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match text := telegram_context.message.TEXT.get():
        case (
            'جدید به قدیم' |
            'قدیم به جدید' |
            'بهترین به بدترین' |
            'بدترین به بهترین' |
            'پر استفاده به کم استفاده' |
            'کم استفاده به پر استفاده'
        ):
            user.database.back_menu = 'main'
            user.database.menu = User.Menu.USER_SETTINGS
            await user.send_message(user.translate('ordering_changed'), settings)
            match text:
                case 'جدید به قدیم':
                    user.database.meme_ordering = user.database.Ordering.new_meme_id
                case 'قدیم به جدید':
                    user.database.meme_ordering = user.database.Ordering.meme_id
                case 'بهترین به بدترین':
                    user.database.meme_ordering = user.database.Ordering.high_votes
                case 'بدترین به بهترین':
                    user.database.meme_ordering = user.database.Ordering.votes
                case 'پر استفاده به کم استفاده':
                    user.database.meme_ordering = user.database.Ordering.high_usage
                case 'کم استفاده به پر استفاده':
                    user.database.meme_ordering = user.database.Ordering.low_usage
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
