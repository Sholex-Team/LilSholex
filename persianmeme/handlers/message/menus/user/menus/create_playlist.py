from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    if text and len(text) <= 60:
        user.send_message(
            user.translate('playlist_created', (user.create_playlist(text)).get_link())
        )
        user.go_back()
    else:
        user.send_message(
            user.translate('invalid_playlist_name'), reply_to_message_id=message_id
        )
