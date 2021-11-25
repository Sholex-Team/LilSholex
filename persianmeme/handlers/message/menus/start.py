from persianmeme import models, keyboards, translations
from django.forms import ValidationError


def handler(text, user, message_id):
    match text.split():
        case ('/start', ) | ('/start', 'new_user'):
            user.menu_cleanup()
            user.start()
        case ('/start', 'suggest_meme'):
            user.menu_cleanup()
            user.database.back_menu = 'main'
            if user.database.rank != models.User.Rank.USER and \
                    user.database.menu_mode == models.User.MenuMode.ADMIN:
                user.database.menu = models.User.Menu.ADMIN_MEME_TYPE
                target_keyboard = keyboards.en_meme_type
                translation = translations.admin_messages['meme_type']
            else:
                user.database.menu = models.User.Menu.USER_SUGGEST_MEME_TYPE
                target_keyboard = keyboards.per_meme_type
                translation = translations.user_messages['meme_type']
            user.send_message(translation, target_keyboard)
        case ('/start', playlist_id):
            user.menu_cleanup()
            user.database.menu = models.User.Menu.ADMIN_MAIN
            target_keyboard = keyboards.admin \
                if user.database.rank != models.User.Rank.USER or \
                user.database.menu_mode == models.User.MenuMode.ADMIN else keyboards.user
            try:
                if result := user.join_playlist(playlist_id):
                    user.send_message(
                        user.translate('joined_playlist', result.name), target_keyboard
                    )
                else:
                    user.send_message(
                        user.translate('already_joined_playlist'), target_keyboard
                    )
            except (models.Playlist.DoesNotExist, ValidationError):
                user.send_message(user.translate('invalid_playlist'), target_keyboard)
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)