from persianmeme.classes import User
from persianmeme.translations import admin_messages


def handler(text: str, user: User):
    user.database.current_meme.name = text
    user.database.current_meme.save()
    user.send_message(admin_messages['meme_name_edited'].format(user.current_meme_translation))
    user.go_back()
