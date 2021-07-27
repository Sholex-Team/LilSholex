from .types import ObjectType
from LilSholex.functions import emoji_number
owner = {'keyboard': [
    ['Add Sound', 'Delete Sound', 'Voice Count', 'Member Count'],
    ['Ban a User', 'Unban a User', 'Full Ban'],
    ['Broadcast', 'Message User'],
    ['Get Voice', 'Get User'],
    ['Add Ad', 'Delete Ad', 'Edit Ad'],
    ['Accept Voice', 'Ban Vote', 'Deny Voice'],
    ['Edit Voice', 'File ID'],
    ['Messages', 'Accepted', 'Delete Requests']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['راهنما 🔰'],
    ['گروه عمومی', 'دیسکورد', 'حمایت مالی 💸'],
    ['ویس های پیشنهادی ✔', 'لغو رای گیری ⏹'],
    ['درخواست حذف ویس ✖', 'ویس های شخصی 🔒'],
    ['پر استفاده ها ⭐', 'ویس های محبوب 👌'],
    ['علاقه مندی ها ❤️', 'پلی لیست ▶️'],
    ['ارتباط با مدیریت 📬', 'تنظیمات ⚙'],
    ['آخرین ویس ها 🆕', ]
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
    ['مرتب سازی 🗂', 'امتیازدهی ⭐'],
    ['ویس های اخیر ⏱'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
manage_voice_list = {'keyboard': [['افزودن ویس ⏬', 'مشاهده ی ویس ها 📝'], ['بازگشت 🔙']], 'resize_keyboard': True}
manage_suggestions = {'keyboard': [['پیشنهاد ویس 🔥', 'مشاهده ی ویس ها 📝'], ['بازگشت 🔙']], 'resize_keyboard': True}
discord = {'inline_keyboard': [[{'text': 'Discord 🎮', 'url': 'https://discord.gg/PersianMeme'}]]}
group = {'inline_keyboard': [[{'text': 'گروه عمومی 👥', 'url': 'https://t.me/persianmemeofficial'}]]}
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
edit_voice = {'keyboard': [['Edit Name', 'Edit Tags'], ['Back 🔙']], 'resize_keyboard': True}


def voice(accept_count: int = 0, deny_count: int = 0):
    return {'inline_keyboard': [[
        {'text': f'✅ : {accept_count} ', 'callback_data': 'accept'},
        {'text': f'❌ : {deny_count}', 'callback_data': 'deny'}
    ]]}


def message(chat_id):
    return {'inline_keyboard': [[{'text': f'From : {chat_id}', 'callback_data': 'none'}]]}


def manage_message(target_message):
    return {'inline_keyboard': [
        [{'text': f'From : {target_message.sender.chat_id}', 'callback_data': 'none'}],
        [
            {'text': 'Read', 'callback_data': f'read:{target_message.id}'},
            {'text': 'Ban', 'callback_data': f'ban:{target_message.id}'}
        ],
        [{'text': 'Reply', 'callback_data': f'reply:{target_message.id}'}]
    ]}


def delete_voice(delete_id):
    return {'inline_keyboard': [
        [{'text': 'Delete', 'callback_data': f'delete:{delete_id}'},
         {'text': 'Deny', 'callback_data': f'delete_deny:{delete_id}'}]
    ]}


def use(voice_id: int):
    return {'inline_keyboard': [[{'text': 'استفاده ✔️', 'switch_inline_query': f'id:{voice_id}'}]]}


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


def make_voice_list(voices):
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
