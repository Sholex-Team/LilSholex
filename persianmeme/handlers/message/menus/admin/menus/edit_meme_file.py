from persianmeme.classes import User
from persianmeme.translations import admin_messages


def handler(message: dict, user: User):
    if user.edit_meme_file(message):
        user.send_message(admin_messages['meme_file_edited'].format(user.current_meme_translation))
        user.go_back()
