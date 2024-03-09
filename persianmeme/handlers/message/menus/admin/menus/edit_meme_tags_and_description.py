from persianmeme.classes import User
from persianmeme.functions import create_description
from persianmeme.translations import admin_messages


def handler(user: User):
    user.edit_meme_tags()
    user.database.current_meme.description = create_description(user.database.current_meme.tags)
    user.database.current_meme.save(update_fields=('tags', 'description'))
    user.send_message(admin_messages['meme_tags_and_description_edited'].format(user.current_meme_translation))
    user.go_back()
