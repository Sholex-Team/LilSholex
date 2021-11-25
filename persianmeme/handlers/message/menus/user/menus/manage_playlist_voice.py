from persianmeme.classes import User


def handler(text: str, user: User):
    match text:
        case 'حذف ویس ❌':
            if user.remove_voice_from_playlist():
                user.send_message(user.translate('deleted_from_playlist'))
            else:
                user.send_message(user.translate('not_in_playlist'))
            user.go_back()
        case 'گوش دادن به ویس 🎧':
            user.send_current_meme()
        case _:
            user.send_message(user.translate('unknown_command'))
