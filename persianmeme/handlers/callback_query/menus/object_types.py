from persianmeme.classes import User as UserClass
from persianmeme.types import ObjectType
from persianmeme.models import User, MemeType, Meme
from persianmeme.keyboards import manage_voice, manage_video
from persianmeme.translations import user_messages
from LilSholex.exceptions import RequestInterruption


def handler(callback_type: ObjectType, meme_id: id, query_id: str, answer_query, inliner: UserClass):
    try:
        match callback_type:
            case ObjectType.PRIVATE_VOICE.value:
                inliner.database.current_meme = inliner.get_private_voice(meme_id)
                inliner.database.back_menu = 'manage_private_voices'
                inliner.database.menu = User.Menu.USER_MANAGE_PRIVATE_VOICE
            case ObjectType.SUGGESTED_VOICE.value:
                inliner.database.current_meme = inliner.get_suggested_meme(
                    meme_id, MemeType.VOICE
                )
                inliner.database.back_menu = 'voice_suggestions'
                inliner.database.menu = User.Menu.USER_MANAGE_VOICE_SUGGESTION
            case ObjectType.SUGGESTED_VIDEO.value:
                inliner.database.current_meme = inliner.get_suggested_meme(
                    meme_id, MemeType.VIDEO
                )
                inliner.database.back_menu = 'video_suggestions'
                inliner.database.menu = User.Menu.USER_MANAGE_VIDEO_SUGGESTION
            case ObjectType.PLAYLIST_VOICE.value:
                inliner.database.current_meme = inliner.database.current_playlist.voices.get(
                    id=meme_id
                )
                inliner.database.back_menu = 'manage_playlist'
                inliner.database.menu = User.Menu.USER_MANAGE_PLAYLIST_VOICE
    except Meme.DoesNotExist:
        inliner.database.save()
        raise RequestInterruption()
    temp_current_meme = inliner.database.current_meme
    inliner.menu_cleanup()
    inliner.database.current_meme = temp_current_meme
    inliner.database.menu_mode = inliner.database.MenuMode.USER
    if inliner.database.current_meme.type == MemeType.VOICE:
        meme_translation = user_messages['voice']
        meme_keyboard = manage_voice
    else:
        meme_translation = user_messages['video']
        meme_keyboard = manage_video
    answer_query(query_id, user_messages['manage_meme'].format(meme_translation), False)
    inliner.send_message(
        user_messages['managing_meme'].format(meme_translation), meme_keyboard
    )
