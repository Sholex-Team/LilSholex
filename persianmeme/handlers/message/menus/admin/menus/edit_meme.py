from persianmeme.keyboards import en_back, admin
from persianmeme.models import MemeType, User
from persianmeme.translations import admin_messages
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'Edit File':
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_FILE
            await user.send_message(user.translate('edit_meme_file', user.current_meme_translation), en_back)
        case 'Edit Name':
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_NAME
            await user.send_message(user.translate(
                'edit_meme_name', user.current_meme_translation
            ), en_back)
        case 'Edit Tags':
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS
            await user.send_message(user.translate(
                'edit_meme_tags', user.current_meme_translation
            ), en_back)
        case 'Edit Tags & Description':
            if user.database.current_meme.type == MemeType.VIDEO:
                user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                          == MemeType.VOICE else 'edit_video'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION
                await user.send_message(user.translate(
                    'edit_meme_tags', user.current_meme_translation
                ), en_back)
        case 'Edit Description':
            if user.database.current_meme.type == MemeType.VIDEO:
                user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                          == MemeType.VOICE else 'edit_video'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_DESCRIPTION
                await user.send_message(user.translate(
                    'edit_meme_description', user.current_meme_translation
                ), en_back)
        case 'Check the Meme':
            await user.database.current_meme.send_meme(
                user.database.chat_id,
                extra_text=user.database.current_meme.description_text
            )
        case 'Done ✔':
            user.database.menu = User.Menu.ADMIN_MAIN
            await user.send_message(
                admin_messages['meme_edited'].format(user.current_meme_translation),
                admin,
                telegram_context.common.MESSAGE_ID.get()
            )
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
