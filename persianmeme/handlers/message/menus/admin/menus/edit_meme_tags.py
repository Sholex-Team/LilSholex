from persianmeme.classes import User


def handler(user: User):
    user.edit_meme_tags()
    user.database.current_meme.save(update_fields=('tags',))
    user.send_message(user.translate('meme_tags_edited', user.current_meme_translation))
    user.go_back()
