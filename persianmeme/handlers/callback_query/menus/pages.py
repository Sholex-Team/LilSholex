from persianmeme.classes import User
from persianmeme.models import MemeType
from persianmeme.functions import make_list_string
from persianmeme.keyboards import make_list
from persianmeme.types import ObjectType


def handler(object_type: ObjectType, page: int, message_id: int, inliner: User):
    match object_type:
        case ObjectType.PLAYLIST:
            objs, prev_page, next_page = inliner.get_playlists(page)
        case ObjectType.PLAYLIST_VOICE:
            objs, prev_page, next_page = inliner.get_playlist_voices(page)
        case ObjectType.SUGGESTED_VOICE:
            objs, prev_page, next_page = inliner.get_suggestions(page, MemeType.VOICE)
        case ObjectType.SUGGESTED_VIDEO:
            objs, prev_page, next_page = inliner.get_suggestions(page, MemeType.VIDEO)
        case ObjectType.PRIVATE_VOICE:
            objs, prev_page, next_page = inliner.get_private_voices(page)
    inliner.edit_message_text(
        message_id,
        make_list_string(object_type, objs),
        make_list(object_type, objs, prev_page, next_page)
    )
