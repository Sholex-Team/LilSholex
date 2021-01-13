from .types import ObjectType
numbers = {
    0: '1️⃣',
    1: '2️⃣',
    2: '3️⃣',
    3: '4️⃣',
    4: '5️⃣',
    5: '6️⃣',
    6: '7️⃣',
    7: '8️⃣',
    8: '9️⃣'
}
owner = {'keyboard': [
    ['Add Sound', 'Delete Sound', 'Voice Count', 'Member Count'],
    ['Ban a User', 'Edit Ad', 'Ban Vote'],
    ['Unban a User', 'Full Ban', 'Message User'],
    ['Get User', 'Broadcast', 'Accepted'],
    ['Add Ad', 'Delete Ad', 'Delete Requests']
], 'resize_keyboard': True}
user = {'keyboard': [
    ['لغو رای گیری ⏹'],
    ['گروه عمومی', 'دیسکورد', 'حمایت مالی 💸'],
    ['راهنما 🔰', 'پیشنهاد ویس 🔥'],
    ['حذف ویس ❌', 'ویس های محبوب 👌'],
    ['امتیازدهی ⭐', 'ارتباط با مدیریت 📬'],
    ['آخرین ویس ها 🆕', 'مرتب سازی 🗂'],
    ['درخواست حذف ویس ✖'],
    ['ویس های شخصی 🔒', 'علاقه مندی ها ❤️'],
    ['پلی لیست ▶️']
], 'resize_keyboard': True}
per_back = {'keyboard': [['بازگشت 🔙']], 'resize_keyboard': True}
en_back = {'keyboard': [['Back 🔙']], 'resize_keyboard': True}
toggle = {'keyboard': [['روشن 🔛', 'خاموش 🔴'], ['بازگشت 🔙']], 'resize_keyboard': True}
voice_order = {'keyboard': [
    ['قدیم به جدید', 'جدید به قدیم'],
    ['بهترین به بدترین ', 'بدترین به بهترین'],
    ['بازگشت 🔙']
], 'resize_keyboard': True}
private = {'keyboard': [['حذف 🗑', 'افزودن ⏬'], ['بازگشت 🔙']], 'resize_keyboard': True}
bot = {'inline_keyboard': [[{'text': 'Bot 🤖', 'url': 'https://t.me/Persian_Meme_Bot'}]]}
discord = {'inline_keyboard': [[{'text': 'Discord 🎮', 'url': 'https://discord.gg/PTK4Vbg'}]]}
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


def voice(accept_count: int = 0, deny_count: int = 0):
    return {'inline_keyboard': [[
        {'text': f'✅ : {accept_count} ', 'callback_data': 'accept'},
        {'text': f'❌ : {deny_count}', 'callback_data': 'deny'}
    ]]}


def message(chat_id):
    return {'inline_keyboard': [
        [{'text': f'From : {chat_id}', 'callback_data': 'none'}],
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


def create_list_keyboard(objs: tuple, object_type: ObjectType, start: int):
    return [{
        'text': numbers[start + index],
        'callback_data': f'{object_type.value}:{obj.id if object_type == ObjectType.PLAYLIST else obj.voice_id}'
    } for index, obj in enumerate(objs)]


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
