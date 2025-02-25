from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import toggle, voice_order, search_items
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'مرتب سازی 🗂':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_SORTING
            await user.send_message(user.translate('select_order'), voice_order)
        case 'امتیازدهی ⭐':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_RANKING
            await user.send_message(user.translate('choose'), toggle)
        case 'ویس های اخیر ⏱':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_RECENT_VOICES
            await user.send_message(user.translate('choose'), toggle)
        case 'آیتم های جستجو 🔍':
            user.database.back_menu = 'settings'
            user.database.menu = User.Menu.USER_SEARCH_ITEMS
            await user.send_message(user.translate('select_search_items'), search_items)
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
