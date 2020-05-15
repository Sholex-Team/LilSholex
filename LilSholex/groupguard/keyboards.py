admin = {'keyboard': [
    ['Users', 'Groups'],
    ['Ban Group', 'Ban User'],
    ['Unban Group', 'Unban User'],
    ['Add Ad', 'Delete Ad']
], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
en_user = {
    'keyboard': [['Add to Group', 'Support'], ['Help 🆘', 'Language 📖'], ['Validation 🔐']], 'resize_keyboard': True
}
fa_user = {
    'keyboard': [['اضافه کردن به گروه ⏬', 'پشتیبانی 👨‍💻'], ['راهنما 📕', 'زبان 📖'], ['احراز هویت 🔐']], 'resize_keyboard': True
}
en_lang = {'keyboard': [['فارسی 🇮🇷', 'English 🇺🇸'], ['Back 🔙']], 'resize_keyboard': True}
fa_lang = {'keyboard': [['فارسی 🇮🇷', 'English 🇺🇸'], ['بازگشت 🔙']], 'resize_keyboard': True}
en_number = {'keyboard': [[{'text': 'Share ☎️', 'request_contact': True}], ['Back 🔙']], 'resize_keyboard': True}
fa_number = {'keyboard': [[{'text': 'اشتراک ☎️', 'request_contact': True}], ['بازگشت 🔙']], 'resize_keyboard': True}
verify_number = {'inline_keyboard': [[{'text': 'Verify ☎️', 'url': 't.me/SholexBot'}]]}
fa_help = {'keyboard': [['دستورات کلی 👨', 'دستورات ادمین 💂‍♀️'], ['دستورات سازنده 👨‍💻'], ['بازگشت 🔙']], 'resize_keyboard': True}
en_help = {'keyboard': [['General 👨', 'Admin 💂‍♀️'], ['Creator 👨‍💻'], ['Back 🔙']], 'resize_keyboard': True}
fa_login = {'inline_keyboard': [[{'text': 'چت خصوصی 💬', 'url': 't.me/SholexBot'}]]}
en_login = {'inline_keyboard': [[{'text': 'Private Chat 💬', 'url': 't.me/SholexBot'}]]}


def invite(link):
    return {'inline_keyboard': [[{'text': 'Join ⏬', 'url': link}]]}


def support(link):
    return {'inline_keyboard': [[{'text': 'Support Bot ⏬', 'url': link}]]}


def verify(verify_id):
    return {'inline_keyboard': [[{'text': 'Verify ☑️', 'callback_data': str(verify_id)}]]}
