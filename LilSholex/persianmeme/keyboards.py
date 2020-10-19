owner = {'keyboard': [
    ['Add Sound', 'Delete Sound', 'Voice Count', 'Member Count'],
    ['Ban a User'],
    ['Unban a User', 'Full Ban', 'Message User'],
    ['Get User', 'Broadcast'],
    ['Add Ad', 'Delete Ad', 'Delete Requests']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['راهنما 🔰', 'پیشنهاد ویس 🔥'],
    ['حذف ویس ❌', 'ویس های محبوب 👌'],
    ['امتیازدهی ⭐', 'ارتباط با مدیریت 📬'],
    ['آخرین ویس ها 🆕', 'مرتب سازی 🗂'],
    ['درخواست حذف ویس ✖'],
    ['ویس های شخصی 🔒', 'علاقه مندی ها ❤️']
], 'resize_keyboard': True}
per_back = {'keyboard': [['بازگشت 🔙']], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
toggle = {'keyboard': [['روشن 🔛', 'خاموش 🔴'], ['بازگشت 🔙']], 'resize_keyboard': True}
voice_order = {'keyboard': [
    ['قدیم به جدید', 'جدید به قدیم'],
    ['بهترین به بدترین ', 'بدترین به بهترین'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
next_page = {'keyboard': [['صفحه ی بعد ➡️'], ['بازگشت 🔙']], 'resize_keyboard': True}
private = {'keyboard': [['حذف 🗑', 'افزودن ⏬'], ['بازگشت 🔙']], 'resize_keyboard': True}
bot = {'inline_keyboard': [[{'text': 'Bot 🤖', 'url': 'https://t.me/Persian_Meme_Bot'}]]}


def voice(accept_count: int = 0, deny_count: int = 0):
    return {'inline_keyboard': [[
        {'text': f'Accept : {accept_count} ', 'callback_data': 'accept'},
        {'text': f'Deny : {deny_count}', 'callback_data': 'deny'}
    ]]}


def message(chat_id):
    return {'inline_keyboard': [
        [
            {'text': 'Read', 'callback_data': f'read:{chat_id}'},
            {'text': 'Ban', 'callback_data': f'ban:{chat_id}'}
        ],
        [{'text': 'Reply', 'callback_data': f'reply:{chat_id}'}]
    ]}


def delete_voice(delete_id):
    return {'inline_keyboard': [
        [{'text': 'Delete', 'callback_data': f'delete:{delete_id}'},
         {'text': 'Deny', 'callback_data': f'delete_deny:{delete_id}'}]
    ]}


def use(voice_name):
    return {'inline_keyboard': [[{'text': 'استفاده ✔️', 'switch_inline_query': voice_name}]]}
