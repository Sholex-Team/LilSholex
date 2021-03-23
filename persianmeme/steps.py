from . import translations
from . import keyboards
from .models import User
admin_steps = {
    'main': {'menu': User.Menu.ADMIN_MAIN, 'message': translations.admin_messages['back'], 'keyboard': keyboards.owner},
    'voice_name': {
        'menu': User.Menu.ADMIN_VOICE_NAME, 'message': translations.admin_messages['voice_name'], 'before': 'main'
    },
    'voice_tags': {
        'menu': User.Menu.ADMIN_VOICE_TAGS,
        'message': translations.admin_messages['voice_tags'],
        'before': 'voice_name'
    },
    'chat_id': {
        'menu': User.Menu.ADMIN_MESSAGE_USER_ID, 'message': translations.admin_messages['chat_id'], 'before': 'main'
    },
    'edit_ad': {
        'menu': User.Menu.ADMIN_EDIT_AD_ID,
        'message': translations.admin_messages['edit_ad'],
        'keyboard': keyboards.en_back,
        'before': 'main'
    }
}
user_steps = {
    'main': {'menu': User.Menu.USER_MAIN, 'message': translations.user_messages['back'], 'keyboard': keyboards.user},
    'private': {
        'menu': User.Menu.USER_PRIVATE_VOICES,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.private,
        'before': 'main'
    },
    'favorite': {
        'menu': User.Menu.USER_FAVORITE_VOICES,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.private,
        'before': 'main'
    },
    'suggest_name': {
        'menu': User.Menu.USER_SUGGEST_VOICE_NAME,
        'message': translations.user_messages['voice_name'],
        'before': 'main'
    },
    'suggest_tags': {
        'menu': User.Menu.USER_SUGGEST_VOICE_TAGS,
        'message': translations.user_messages['voice_tags'],
        'before': 'suggest_name'
    },
    'private_name': {
        'menu': User.Menu.USER_PRIVATE_VOICE_NAME,
        'message': translations.user_messages['voice_name'],
        'before': 'main'
    },
    'manage_playlists': {
        'menu': User.Menu.USER_PLAYLISTS,
        'message': translations.user_messages['manage_playlists'],
        'keyboard': keyboards.manage_playlists,
        'before': 'main'
    },
    'manage_playlist': {
        'menu': User.Menu.USER_MANAGE_PLAYLIST,
        'message': translations.user_messages['manage_playlist'],
        'keyboard': keyboards.manage_playlist,
        'before': 'manage_playlists'
    }
}
