en_user = {'keyboard': [['Group Guard', 'Anonymous Message'], ['Language 📖']], 'resize_keyboard': True}
fa_user = {'keyboard': [['مدیریت گروه', 'پیام ناشناس'], ['زبان 📖']], 'resize_keyboard': True}
admin = {'keyboard': [['Unanswered messages']], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
fa_back = {'keyboard': [['بازگشت 🔙']], 'resize_keyboard': True}
seen = {'inline_keyboard': [[{'text': 'Checked ✔', 'callback_data': 'seen'}]]}
en_type = {'keyboard': [['Suggestion 👌', 'Bug ☢'], ['Back 🔙']], 'resize_keyboard': True}
fa_type = {'keyboard': [['پیشنهادات 👌', 'باگ ☢'], ['بازگشت 🔙']], 'resize_keyboard': True}
en_lang = {'keyboard': [['فارسی 🇮🇷', 'English 🇺🇸'], ['Back 🔙']], 'resize_keyboard': True}
fa_lang = {'keyboard': [['فارسی 🇮🇷', 'English 🇺🇸'], ['بازگشت 🔙']], 'resize_keyboard': True}


def message(message_id):
    return {'inline_keyboard': [[
        {'text': 'Check ✔️', 'callback_data': f'{message_id}:read'},
        {'text': 'Answer ✍', 'callback_data': f'{message_id}:answer'},
        {'text': 'Ban ❌', 'callback_data': f'{message_id}:ban'}
    ]]}
