from persianmeme.keyboards import en_back
from persianmeme.models import User, MemeType
from persianmeme.classes import User as UserClass
from persianmeme.translations import admin_messages


def handler(text: str, message_id: int, user: UserClass):
    if user.check_current_meme():
        match text:
            case 'Edit File':
                user.database.back_menu = 'meme_review'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_FILE
                user.send_message(admin_messages['edit_meme_file'].format(user.current_meme_translation), en_back)
            case 'Edit Name':
                user.database.back_menu = 'meme_review'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_NAME
                user.send_message(admin_messages['edit_meme_name'].format(user.current_meme_translation), en_back)
            case 'Edit Tags':
                user.database.back_menu = 'meme_review'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS
                user.send_message(admin_messages['edit_meme_tags'].format(user.current_meme_translation), en_back)
            case 'Edit Tags &amp; Description' if user.database.current_meme.type == MemeType.VIDEO:
                user.database.back_menu = 'meme_review'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION
                user.send_message(admin_messages['edit_meme_tags'].format(user.current_meme_translation), en_back)
            case 'Edit Description' if user.database.current_meme.type == MemeType.VIDEO:
                user.database.back_menu = 'meme_review'
                user.database.menu = User.Menu.ADMIN_EDIT_MEME_DESCRIPTION
                user.send_message(
                    admin_messages['edit_meme_description'].format(user.current_meme_translation), en_back
                )
            case 'Delete 🗑':
                user.delete_current_meme()
                if not user.assign_meme():
                    user.go_back()
            case 'Check the Meme':
                user.database.current_meme.send_meme(
                    user.database.chat_id,
                    user.session,
                    extra_text=user.database.current_meme.description_text
                )
            case 'Done ✔' | 'Done and Next ⏭':
                user.review_current_meme()
                if text == 'Done ✔':
                    user.go_back()
                else:
                    if not user.assign_meme():
                        user.go_back()
            case _:
                user.send_message(admin_messages['unknown_command'], reply_to_message_id=message_id)
