from persianmeme.classes import User


def handler(file_unique_id: str, message_id: int, user: User):
    if user.add_voice_to_playlist(file_unique_id):
        user.send_message(user.translate('added_to_playlist'))
        user.go_back()
    else:
        user.send_message(
            user.translate('meme_is_not_yours', user.translate('voice')),
            reply_to_message_id=message_id
        )
