from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import toggle, voice_order, search_items


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'مرتب سازی 🗂':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_SORTING
            user.send_message(user.translate('select_order'), voice_order)
        case 'امتیازدهی ⭐':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_RANKING
            user.send_message(user.translate('choose'), toggle)
        case 'ویس های اخیر ⏱':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_RECENT_VOICES
            user.send_message(user.translate('choose'), toggle)
        case 'آیتم های جستجو 🔍':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_SEARCH_ITEMS
            user.send_message(user.translate('select_search_items'), search_items)
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
