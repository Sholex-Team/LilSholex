owner = {'keyboard': [
        ['Add Sound', 'Delete Sound', 'Voice Count', 'Member Count'],
        ['Ban a User'],
        ['Unban a User', 'Full Ban', 'Message User'],
        ['Unchecked Voices', 'Get User'],
        ['Add Ad', 'Delete Ad']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['راهنما 🔰', 'پیشنهاد ویس 🔥'],
    ['حذف ویس ❌', 'ویس های محبوب 👌'],
    ['امتیازدهی ⭐', 'ارتباط با مدیریت 📬'],
    ['آخرین ویس ها 🆕', 'مرتب سازی 🗂'],
    ['درخواست حذف ویس ✖'],
    ['حمایت مالی 💸', 'ویس های شخصی 🔒'],
    ['علاقه مندی ها ❤️']
], 'resize_keyboard': True}
per_back = {'keyboard': [['بازگشت 🔙']], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
voice = {'inline_keyboard': [[
    {'text': 'Accept', 'callback_data': 'accept'},
    {'text': 'Deny', 'callback_data': 'deny'}
]]}
toggle = {'keyboard': [['روشن 🔛', 'خاموش 🔴'], ['بازگشت 🔙']], 'resize_keyboard': True}
voice_order = {'keyboard': [
    ['قدیم به جدید', 'جدید به قدیم'],
    ['بهترین به بدترین ', 'بدترین به بهترین'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
next_page = {'keyboard': [['صفحه ی بعد ➡️'], ['بازگشت 🔙']], 'resize_keyboard': True}
private = {'keyboard': [['حذف 🗑', 'افزودن ⏬'], ['بازگشت 🔙']], 'resize_keyboard': True}


def message(chat_id):
    return {'inline_keyboard': [[{'text': 'Read', 'callback_data': f'read:{chat_id}'}, {'text': 'Ban', 'callback_data': f'ban:{chat_id}'}], [{'text': 'Reply', 'callback_data': f'reply:{chat_id}'}]]}


def delete_voice(chat_id):
    return {'inline_keyboard': [[{'text': 'Delete', 'callback_data': f'delete:{chat_id}'}, {'text': 'Deny', 'callback_data': f'delete_deny:{chat_id}'}]]}


def donate(price):
    return {'inline_keyboard': [[{'text': 'حمایت', 'url': f'https://payping.ir/PersianMeme/{price}'}]]}


def use(voice_name):
    return {'inline_keyboard': [[{'text': 'استفاده ✔️', 'switch_inline_query': voice_name}]]}
