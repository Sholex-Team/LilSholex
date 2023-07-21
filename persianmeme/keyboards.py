from .types import ObjectType
from LilSholex.functions import emoji_number
admin = {'keyboard': [
    ['Add Meme', 'Delete Meme', 'Meme Count'],
    ['Ban a User', 'Unban a User', 'Full Ban'],
    ['Broadcast', 'Message User'],
    ['Get User', 'Started Count'],
    ['Add Ad', 'Delete Ad', 'Edit Ad'],
    ['Ban Vote', 'God Mode'],
    ['Edit Meme', 'File ID', 'Meme Review'],
    ['Messages', 'Delete Requests'],
    ['Broadcast Status', 'Member Count']
], 'resize_keyboard': True}
en_meme_type = {'keyboard': [['Video', 'Voice'], ['Back 🔙']], 'resize_keyboard': True}
per_meme_type = {'keyboard': [['ویس 🔊', 'ویدئو 📹'], ['بازگشت 🔙']], 'resize_keyboard': True}
search_items = {'keyboard': [
    ['ویس ها 🔊', 'ویدئو ها 📹'], ['ویس ها 🔊 و ویدئو ها 📹'], ['بازگشت 🔙']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['راهنما 🔰', 'گزارش تخلف 🛑'],
    ['درخواست حذف میم ✖', 'حمایت مالی 💸'],
    ['ویس ها 🔊', 'کانال رای‌گیری 🗳', 'ویدئو ها 📹'],
    ['پر استفاده ها ⭐', 'آخرین میم ها 🆕', 'میم های محبوب 👌'],
    ['ارتباط با مدیریت 📬', 'تنظیمات ⚙']
], 'resize_keyboard': True}
manage_voices = {'keyboard': [
    ['ویس های پیشنهادی ✔', 'ویس های شخصی 🔒'], ['پلی لیست ها ▶️'], ['بازگشت 🔙']
], 'resize_keyboard': True}
video_suggestions = {'keyboard': [
    ['پیشنهاد ویدئو 🔥', 'مشاهده ی ویدئو ها 📝'], ['لغو رای گیری ⏹'], ['بازگشت 🔙']
], 'resize_keyboard': True}
per_back = {'keyboard': [['بازگشت 🔙']], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
toggle = {'keyboard': [['روشن 🔛', 'خاموش 🔴'], ['بازگشت 🔙']], 'resize_keyboard': True}
voice_order = {'keyboard': [
    ['قدیم به جدید', 'جدید به قدیم'],
    ['بهترین به بدترین ', 'بدترین به بهترین'],
    ['پر استفاده به کم استفاده'],
    ['کم استفاده به پر استفاده'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
settings = {'keyboard': [
    ['مرتب سازی 🗂', 'ویس های اخیر ⏱'],
    ['آیتم های جستجو 🔍', 'امتیازدهی ⭐'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
manage_voice_list = {'keyboard': [['افزودن ویس ⏬', 'مشاهده ی ویس ها 📝'], ['بازگشت 🔙']], 'resize_keyboard': True}
voice_suggestions = {'keyboard': [
    ['پیشنهاد ویس 🔥', 'مشاهده ی ویس ها 📝'], ['لغو رای گیری ⏹'], ['بازگشت 🔙']
], 'resize_keyboard': True}
voting_channel = {'inline_keyboard': [[{'text': 'کانال رای‌گیری 🗳', 'url': 'https://t.me/persianmemeofficial'}]]}
admin_message = {'inline_keyboard': [[{'text': 'پیام از طرف مدیریت 👆', 'callback_data': 'none'}]]}
manage_playlists = {'keyboard': [
    ['ایجاد پلی لیست 🆕'], ['مشاهده پلی لیست ها 📝'], ['بازگشت 🔙']
], 'resize_keyboard': True}
manage_playlist = {'keyboard': [
    ['افزودن ویس ⏬', 'مشاهده ی ویس ها 📝'],
    ['حذف پلی لیست ❌', 'لینک دعوت 🔗'],
    ['مشترکین پلی لیست 👥'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
manage_voice = {'keyboard': [['حذف ویس ❌', 'گوش دادن به ویس 🎧'], ['بازگشت 🔙']], 'resize_keyboard': True}
manage_video = {'keyboard': [['حذف ویدئو ❌', 'تماشای ویدئو 👁'], ['بازگشت 🔙']], 'resize_keyboard': True}
edit_meme = {'keyboard': [
    ['Edit Name', 'Edit Tags', 'Check the Meme'],
    ['Edit File', 'Edit Tags & Description'],
    ['Edit Description'],
    ['Done ✔'],
    ['Back 🔙']
], 'resize_keyboard': True}
meme_review = {'keyboard': [
    ['Edit File', 'Edit Name', 'Edit Tags'],
    ['Edit Tags & Description'],
    ['Edit Description'],
    ['Delete 🗑', 'Check the Meme'],
    ['Done ✔', 'Done and Next ⏭'], ['Back 🔙']
], 'resize_keyboard': True}
deleted = {'inline_keyboard': [[{'text': 'Deleted 🗑', 'callback_data': 'none'}]]}
recovered = {'inline_keyboard': [[{'text': 'Recovered ♻', 'callback_data': 'none'}]]}
dismissed = {'inline_keyboard': [[{'text': 'Dismissed ✔', 'callback_data': 'none'}]]}
processed = {'inline_keyboard': [[{'text': 'Processed ✔', 'callback_data': 'none'}]]}


def suggestion_vote(meme_id: int):
    return {'inline_keyboard': [[
        {'text': '✅', 'callback_data': f'a:{meme_id}'},
        {'text': '❌', 'callback_data': f'd:{meme_id}'}
    ], [
        {'text': 'نتایج 📊', 'callback_data': f're:{meme_id}'},
        {'text': 'گزارش ⚠', 'callback_data': f'rep:{meme_id}'}
    ]]}


def meme_recovery(meme_id: int):
    return {'inline_keyboard': [[
        {'text': 'Recover', 'callback_data': f'r:{meme_id}'},
        {'text': 'Delete', 'callback_data': f'rd:{meme_id}'}
    ]]}


def message(chat_id):
    return {'inline_keyboard': [[{'text': f'From : {chat_id}', 'callback_data': f'p:{chat_id}'}]]}


def manage_message(target_message):
    return {'inline_keyboard': [
        [{'text': f'From : {target_message.sender.chat_id}', 'callback_data': f'p:{target_message.sender.chat_id}'}],
        [
            {'text': 'Read', 'callback_data': f'read:{target_message.id}'},
            {'text': 'Ban', 'callback_data': f'ban:{target_message.id}'}
        ],
        [{'text': 'Reply', 'callback_data': f'reply:{target_message.id}'}]
    ]}


def delete_voice(delete_id):
    return {'inline_keyboard': [[
        {'text': 'Delete', 'callback_data': f'delete:{delete_id}'},
        {'text': 'Deny', 'callback_data': f'delete_deny:{delete_id}'}
    ]]}


def use(meme_id: int):
    return {'inline_keyboard': [[{'text': 'استفاده ✔️', 'switch_inline_query': f'id:{meme_id}'}]]}


def create_voice_list_keyboard(voices, start: int):
    return [{
        'text': emoji_number(str(index + start + 1)),
        'switch_inline_query': f'id:{obj.id}'
    } for index, obj in enumerate(voices)]


def create_list_keyboard(objs: tuple, object_type: ObjectType, start: int):
    return [{
        'text': emoji_number(str(start + index + 1)),
        'callback_data': f'{object_type.value}:{obj.id}'
    } for index, obj in enumerate(objs)]


def make_meme_list(voices):
    return {'inline_keyboard': [
        create_voice_list_keyboard(
            voices[start:index], start
        ) for index in range(3, 15, 3) if voices[(start := index - 3):index]
    ]}


def make_list(obj_type: ObjectType, objs, prev_page: int, next_page: int):
    temp_keyboard = {'inline_keyboard': [
        create_list_keyboard(
            objs[start:index], obj_type, start
        ) for index in range(3, 12, 3) if objs[(start := index - 3):index]
    ]}
    temp_keyboard['inline_keyboard'].append(list())
    if prev_page is not None:
        temp_keyboard['inline_keyboard'][-1].insert(0, {
            'text': '◀️',
            'callback_data': f'{obj_type.value}page:{prev_page}'
        })
    if next_page is not None:
        temp_keyboard['inline_keyboard'][-1].insert(1, {
            'text': '▶️',
            'callback_data': f'{obj_type.value}page:{next_page}'
        })
    return temp_keyboard


def help_keyboard(messages):
    temp_keyboard = {'keyboard': [messages[i:i + 2] for i in range(0, len(messages), 2)], 'resize_keyboard': True}
    temp_keyboard['keyboard'].insert(0, per_back['keyboard'][0])
    return temp_keyboard


def report(meme_id: int):
    return {'inline_keyboard': [[
        {'text': 'Delete', 'callback_data': f'rep_accept:{meme_id}'},
        {'text': 'Dismiss', 'callback_data': f'rep_dismiss:{meme_id}'}
    ]]}
