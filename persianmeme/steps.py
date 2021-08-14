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
        'before': 'voice_name',
        'callback': 'clear_temp_voice_tags'
    },
    'chat_id': {
        'menu': User.Menu.ADMIN_MESSAGE_USER_ID, 'message': translations.admin_messages['chat_id'], 'before': 'main'
    },
    'edit_ad': {
        'menu': User.Menu.ADMIN_EDIT_AD_ID,
        'message': translations.admin_messages['edit_ad'],
        'keyboard': keyboards.en_back,
        'before': 'main',
        'callback': 'clear_current_ad'
    },
    'send_edit_voice': {
        'menu': User.Menu.ADMIN_SEND_EDIT_VOICE,
        'message': translations.admin_messages['send_edit_voice'],
        'keyboard': keyboards.en_back,
        'before': 'main',
        'callback': 'clear_current_voice'
    },
    'edit_voice': {
        'menu': User.Menu.ADMIN_EDIT_VOICE,
        'message': translations.admin_messages['edit_voice'],
        'keyboard': keyboards.edit_voice,
        'before': 'send_edit_voice',
        'callback': 'clear_temp_voice_tags'
    },
    'voice_review': {
        'menu': User.Menu.ADMIN_VOICE_REVIEW,
        'message': translations.admin_messages['review_the_voice'],
        'keyboard': keyboards.voice_review,
        'before': 'main',
        'callback': 'clear_current_voice'
    }
}
user_steps = {
    'main': {'menu': User.Menu.USER_MAIN, 'message': translations.user_messages['back'], 'keyboard': keyboards.user},
    'manage_private_voices': {
        'menu': User.Menu.USER_PRIVATE_VOICES,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.manage_voice_list,
        'before': 'main'
    },
    'manage_favorite_voices': {
        'menu': User.Menu.USER_FAVORITE_VOICES,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.manage_voice_list,
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
        'before': 'suggest_name',
        'callback': 'clear_temp_voice_tags'
    },
    'private_name': {
        'menu': User.Menu.USER_PRIVATE_VOICE_NAME,
        'message': translations.user_messages['voice_name'],
        'before': 'main'
    },
    'private_voice_tags': {
        'menu': User.Menu.USER_PRIVATE_VOICE_TAGS,
        'message': translations.user_messages['voice_tags'],
        'before': 'private_name',
        'callback': 'clear_temp_voice_tags'
    },
    'manage_playlists': {
        'menu': User.Menu.USER_PLAYLISTS,
        'message': translations.user_messages['manage_playlists'],
        'keyboard': keyboards.manage_playlists,
        'before': 'main',
        'callback': 'clear_current_playlist'
    },
    'manage_playlist': {
        'menu': User.Menu.USER_MANAGE_PLAYLIST,
        'message': translations.user_messages['manage_playlist'],
        'keyboard': keyboards.manage_playlist,
        'before': 'manage_playlists',
        'callback': 'clear_current_voice'
    },
    'settings': {
        'menu': User.Menu.USER_SETTINGS,
        'message': translations.user_messages['settings'],
        'keyboard': keyboards.settings,
        'before': 'main'
    },
    'manage_suggestions': {
        'menu': User.Menu.USER_SUGGESTIONS,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.manage_suggestions,
        'before': 'main'
    }
}
