from persianmeme.keyboards import settings
from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
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
            user.send_message(user.translate('ordering_changed'), settings)
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
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
