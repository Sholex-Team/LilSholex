from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    match text:
        case 'حذف ویدئو ❌' | 'حذف ویس ❌':
            if user.delete_suggested_meme():
                user.send_message(
                    user.translate('meme_deleted', user.current_meme_translation)
                )
                user.database.current_meme = None
            else:
                user.send_message(
                    user.translate('meme_is_not_yours', user.current_meme_translation)
                )
            user.go_back()
        case 'تماشای ویدئو 👁' | 'گوش دادن به ویس 🎧':
            user.send_current_meme()
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
