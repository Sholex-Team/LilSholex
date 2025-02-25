from persianmeme.keyboards import en_back
from persianmeme.models import User, MemeType
from persianmeme.classes import User as UserClass
from persianmeme.translations import admin_messages
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match text := telegram_context.message.TEXT.get():
        case 'Edit File':
            user.database.back_menu = 'meme_review'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_FILE
            await user.send_message(admin_messages['edit_meme_file'].format(user.current_meme_translation), en_back)
        case 'Edit Name':
            user.database.back_menu = 'meme_review'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_NAME
            await user.send_message(admin_messages['edit_meme_name'].format(user.current_meme_translation), en_back)
        case 'Edit Tags':
            user.database.back_menu = 'meme_review'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS
            await user.send_message(admin_messages['edit_meme_tags'].format(user.current_meme_translation), en_back)
        case 'Edit Tags & Description' if user.database.current_meme.type == MemeType.VIDEO:
            user.database.back_menu = 'meme_review'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION
            await user.send_message(admin_messages['edit_meme_tags'].format(user.current_meme_translation), en_back)
        case 'Edit Description' if user.database.current_meme.type == MemeType.VIDEO:
            user.database.back_menu = 'meme_review'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_DESCRIPTION
            await user.send_message(
                admin_messages['edit_meme_description'].format(user.current_meme_translation), en_back
            )
        case 'Delete 🗑':
            await user.delete_current_meme()
            if not await user.assign_meme():
                await user.go_back()
        case 'Check the Meme':
            await user.database.current_meme.send_meme(
                user.database.chat_id,
                extra_text=user.database.current_meme.description_text
            )
        case 'Done ✔' | 'Done and Next ▶️':
            await user.review_current_meme()
            if text == 'Done ✔':
                await user.go_back()
            else:
                if not await user.assign_meme():
                    await user.go_back()
        case 'Skip ⏩':
            await user.revoke_current_review()
            if not await user.assign_meme():
                await user.go_back()
        case _:
            await user.send_message(
                admin_messages['unknown_command'], reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
