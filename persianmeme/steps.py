from . import translations
from . import keyboards
from .models import User

admin_steps = {
    'main': {'menu': User.Menu.ADMIN_MAIN, 'message': translations.admin_messages['back'], 'keyboard': keyboards.admin},
    'voice_name': {
        'menu': User.Menu.ADMIN_MEME_NAME,
        'message': translations.admin_messages['meme_name'].format(translations.admin_messages['voice']),
        'before': 'meme_type'
    },
    'video_name': {
        'menu': User.Menu.ADMIN_MEME_NAME,
        'message': translations.admin_messages['meme_name'].format(translations.admin_messages['video']),
        'before': 'meme_type'
    },
    'voice_tags': {
        'menu': User.Menu.ADMIN_MEME_TAGS,
        'message': translations.admin_messages['send_meme_tags'].format(translations.admin_messages['voice']),
        'before': 'voice_name',
        'callback': 'clear_temp_meme_tags'
    },
    'video_tags': {
        'menu': User.Menu.ADMIN_MEME_TAGS,
        'message': translations.admin_messages['send_meme_tags'].format(translations.admin_messages['video']),
        'before': 'video_name',
        'callback': 'clear_temp_meme_tags'
    },
    'chat_id': {
        'menu': User.Menu.ADMIN_MESSAGE_USER_ID, 'message': translations.admin_messages['chat_id'], 'before': 'main'
    },
    'send_edit_meme': {
        'menu': User.Menu.ADMIN_SEND_EDIT_MEME,
        'message': translations.admin_messages['send_edit_meme'],
        'keyboard': keyboards.en_back,
        'before': 'main',
        'callback': 'clear_current_meme'
    },
    'edit_voice': {
        'menu': User.Menu.ADMIN_EDIT_MEME,
        'message': translations.admin_messages['edit_meme'].format(translations.admin_messages['voice']),
        'keyboard': keyboards.edit_meme,
        'before': 'send_edit_meme',
        'callback': 'clear_temp_meme_tags'
    },
    'edit_video': {
        'menu': User.Menu.ADMIN_EDIT_MEME,
        'message': translations.admin_messages['edit_meme'].format(translations.admin_messages['video']),
        'keyboard': keyboards.edit_meme,
        'before': 'send_edit_meme',
        'callback': 'clear_temp_meme_tags'
    },
    'meme_review_type': {
        'menu': User.Menu.ADMIN_MEME_REVIEW_TYPE,
        'message': translations.admin_messages['meme_type'],
        'keyboard': keyboards.meme_review_type,
        'before': 'main',
        'callback': 'clear_current_meme'
    },
    'meme_review': {
        'menu': User.Menu.ADMIN_MEME_REVIEW,
        'message': translations.admin_messages['review_the_meme'],
        'keyboard': keyboards.meme_review,
        'before': 'meme_review_type'
    },
    'meme_type': {
        'menu': User.Menu.ADMIN_MEME_TYPE,
        'message': translations.admin_messages['meme_type'],
        'keyboard': keyboards.en_meme_type,
        'before': 'main'
    }
}
user_steps = {
    'main': {'menu': User.Menu.USER_MAIN, 'message': translations.user_messages['back'], 'keyboard': keyboards.user},
    'manage_private_voices': {
        'menu': User.Menu.USER_PRIVATE_VOICES,
        'message': translations.user_messages['choose'],
        'keyboard': keyboards.manage_voice_list,
        'before': 'main',
        'callback': 'clear_current_meme'
    },
    'suggest_voice_name': {
        'menu': User.Menu.USER_SUGGEST_MEME_NAME,
        'message': translations.user_messages['meme_name'].format(translations.user_messages['voice']),
        'before': 'voice_suggestions'
    },
    'suggest_video_name': {
        'menu': User.Menu.USER_SUGGEST_MEME_NAME,
        'message': translations.user_messages['meme_name'].format(translations.user_messages['video']),
        'before': 'video_suggestions'
    },
    'suggest_voice_tags': {
        'menu': User.Menu.USER_SUGGEST_MEME_TAGS,
        'message': translations.user_messages['send_meme_tags'].format(translations.user_messages['voice']),
        'before': 'suggest_voice_name',
        'callback': 'clear_temp_meme_tags'
    },
    'suggest_video_tags': {
        'menu': User.Menu.USER_SUGGEST_MEME_TAGS,
        'message': translations.user_messages['send_meme_tags'].format(translations.user_messages['video']),
        'before': 'suggest_video_name',
        'callback': 'clear_temp_meme_tags'
    },
    'private_name': {
        'menu': User.Menu.USER_PRIVATE_VOICE_NAME,
        'message': translations.user_messages['meme_name'].format(translations.user_messages['voice']),
        'before': 'main'
    },
    'private_voice_tags': {
        'menu': User.Menu.USER_PRIVATE_VOICE_TAGS,
        'message': translations.user_messages['send_meme_tags'].format(translations.user_messages['voice']),
        'before': 'private_name',
        'callback': 'clear_temp_meme_tags'
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
        'callback': 'clear_current_meme'
    },
    'settings': {
        'menu': User.Menu.USER_SETTINGS,
        'message': translations.user_messages['settings'],
        'keyboard': keyboards.settings,
        'before': 'main'
    },
    'voice_suggestions': {
        'menu': User.Menu.USER_VOICE_SUGGESTIONS,
        'message': translations.user_messages['choose'],
        'keyboard': keyboards.voice_suggestions,
        'before': 'manage_voices',
        'callback': 'clear_current_meme'
    },
    'video_suggestions': {
        'menu': User.Menu.USER_VIDEO_SUGGESTIONS,
        'message': translations.user_messages['choose'],
        'keyboard': keyboards.video_suggestions,
        'before': 'main',
        'callback': 'clear_current_meme'
    },
    'manage_voices': {
        'menu': User.Menu.USER_MANAGE_VOICES,
        'message': translations.user_messages['choose'],
        'keyboard': keyboards.manage_voices,
        'before': 'main'
    }
}
