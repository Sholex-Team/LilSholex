from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    match text:
        case 'حذف ویس ❌':
            if user.delete_private_voice():
                user.send_message(user.translate('meme_deleted', user.translate('voice')))
            else:
                user.send_message(
                    user.translate('meme_deleted_before', user.translate('voice'))
                )
            user.go_back()
        case 'گوش دادن به ویس 🎧':
            user.send_current_meme()
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
