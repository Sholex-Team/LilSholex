from persianmeme.models import User
from persianmeme.keyboards import edit_meme
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.current_meme = meme_context.common.MEME.get()
    user.database.back_menu = 'send_edit_meme'
    user.database.menu = User.Menu.ADMIN_EDIT_MEME
    await user.send_message(user.translate('edit_meme', user.current_meme_translation), edit_meme)
