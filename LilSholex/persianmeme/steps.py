from . import translations
from . import keyboards

admin_steps = {
    'main': {'menu': 1, 'message': translations.admin_messages['back'], 'keyboard': keyboards.owner},
    'voice_name': {'menu': 2, 'message': translations.admin_messages['voice_name'], 'before': 'main'},
    'chat_id': {'menu': 8, 'message': translations.admin_messages['chat_id'], 'before': 'main'}
}
user_steps = {
    'main': {'menu': 1, 'message': translations.user_messages['back'], 'keyboard': keyboards.user},
    'private': {
        'menu': 11,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.private,
        'before': 'main'
    },
    'favorite': {
        'menu': 15,
        'message': translations.user_messages['choices'],
        'keyboard': keyboards.private,
        'before': 'main'
    },
    'suggest_name': {
        'menu': 3,
        'message': translations.user_messages['voice_name'],
        'before': 'main'
    },
    'private_name': {
        'menu': 12,
        'message': translations.user_messages['voice_name'],
        'before': 'main'
    }
}
