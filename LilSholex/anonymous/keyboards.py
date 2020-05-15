admin = {'keyboard': [
    ['Users', 'New Messages'],
    ['Ban User', 'Unban User'],
    ['NickName', 'Link'],
    ['Get User'],
    ['Get Recent Messages'],
    ['Get User Recent Messages'],
    ['Add Ad', 'Remove Ad']
], 'resize_keyboard': True}
en_back = {'keyboard': [
    ['Back']
], 'resize_keyboard': True}
support = {'keyboard': [
    ['Support']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['لینک  🔗', 'پیام های جدید'],
    ['تغییر نام ✍️', 'پیام های اخیر 🗳'],
    ['ارتباط با مدیریت 📬', 'لیست سیاه ☠️'],
    ['حمایت ❤️', 'راهنما 🔰']
], 'resize_keyboard': True}
fa_back = {'keyboard': [
    ['بازگشت 🔙']
], 'resize_keyboard': True}


def donate(price):
    return {'inline_keyboard': [[{'text': 'حمایت', 'url': f'https://idpay.ir/anonymoussholex/{price}'}]]}


def support_():
    return {'inline_keyboard': [[{'text': 'Support', 'url': f'http://t.me/SholexSupportbot'}]]}


def sholex():
    return {'inline_keyboard': [[{'text': 'Sholex', 'url': f'http://t.me/SholexTeam'}]]}


def message(token):
    return {'inline_keyboard': [[{'text': 'بلاک ‼️', 'callback_data': f'block:{token}'},
                                 {'text': 'جواب دادن 🔁', 'callback_data': f'answer:{token}'}]]}


def unblock(users):
    inline_keyboard = list()
    for nick_name, token in users:
        inline_keyboard.append([{'text': f'{nick_name} 🚫', 'callback_data': f'unblock:{token}'}])
    return {'inline_keyboard': inline_keyboard}
