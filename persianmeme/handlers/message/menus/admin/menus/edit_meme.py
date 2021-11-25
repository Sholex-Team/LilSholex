from persianmeme.keyboards import en_back, admin
from persianmeme.models import MemeType, User
from persianmeme.translations import admin_messages
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'Edit Name':
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_NAME
            user.send_message(user.translate(
                'edit_meme_name', user.current_meme_translation
            ), en_back)
        case 'Edit Tags':
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS
            user.send_message(user.translate(
                'edit_meme_tags', user.current_meme_translation
            ), en_back)
        case 'Edit Tags & Description' if user.database.current_meme.type == MemeType.VIDEO:
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION
            user.send_message(user.translate(
                'edit_meme_tags', user.current_meme_translation
            ), en_back)
        case 'Edit Description' if user.database.current_meme.type == MemeType.VIDEO:
            user.database.back_menu = 'edit_voice' if user.database.current_meme.type \
                                                      == MemeType.VOICE else 'edit_video'
            user.database.menu = User.Menu.ADMIN_EDIT_MEME_DESCRIPTION
            user.send_message(user.translate(
                'edit_meme_description', user.current_meme_translation
            ), en_back)
        case 'Check the Meme':
            user.database.current_meme.send_meme(
                user.database.chat_id,
                user.session,
                extra_text=user.database.current_meme.description_text
            )
        case 'Done ✔':
            user.database.menu = User.Menu.ADMIN_MAIN
            user.send_message(
                admin_messages['meme_edited'].format(user.current_meme_translation), admin, message_id
            )
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
