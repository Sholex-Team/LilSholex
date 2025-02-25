from persianmeme.models import MemeType
from persianmeme.functions import make_string_keyboard_list
from persianmeme.types import ObjectType
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    inliner = telegram_context.common.USER.get()
    match object_type := meme_context.callback_query.PAGE_TYPE.get():
        case ObjectType.PLAYLIST:
            objs, prev_page, next_page = await inliner.get_playlists()
        case ObjectType.PLAYLIST_VOICE:
            objs, prev_page, next_page = await inliner.get_playlist_voices()
        case ObjectType.SUGGESTED_VOICE:
            objs, prev_page, next_page = await inliner.get_suggestions(MemeType.VOICE)
        case ObjectType.SUGGESTED_VIDEO:
            objs, prev_page, next_page = await inliner.get_suggestions(MemeType.VIDEO)
        case ObjectType.PRIVATE_VOICE:
            objs, prev_page, next_page = await inliner.get_private_voices()
    await inliner.edit_message_text(*await make_string_keyboard_list(object_type, objs, prev_page, next_page))
