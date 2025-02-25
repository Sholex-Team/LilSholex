from persianmeme.types import ObjectType
from persianmeme.models import User, MemeType, Meme
from persianmeme.keyboards import manage_voice, manage_video
from persianmeme.translations import user_messages
from LilSholex.exceptions import RequestInterruption
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    inliner = telegram_context.common.USER.get()
    new_attributes = dict()
    try:
        match meme_context.callback_query.CALLBACK_TYPE.get():
            case ObjectType.PRIVATE_VOICE.value:
                new_attributes['current_meme'] = await inliner.get_private_voice()
                new_attributes['back_menu'] = 'manage_private_voices'
                inliner.database.menu = User.Menu.USER_MANAGE_PRIVATE_VOICE
            case ObjectType.SUGGESTED_VOICE.value:
                new_attributes['current_meme'] = await inliner.get_suggested_meme(MemeType.VOICE)
                new_attributes['back_menu'] = 'voice_suggestions'
                inliner.database.menu = User.Menu.USER_MANAGE_VOICE_SUGGESTION
            case ObjectType.SUGGESTED_VIDEO.value:
                new_attributes['current_meme'] = await inliner.get_suggested_meme(MemeType.VIDEO)
                new_attributes['back_menu'] = 'video_suggestions'
                inliner.database.menu = User.Menu.USER_MANAGE_VIDEO_SUGGESTION
            case ObjectType.PLAYLIST_VOICE.value:
                if await inliner.check_current_playlist():
                    new_attributes['current_meme'] = await inliner.database.current_playlist.voices.aget(
                        id=meme_context.common.MEME_ID.get()
                    )
                    new_attributes['back_menu'] = 'manage_playlist'
                    new_attributes['current_playlist'] = inliner.database.current_playlist
                    inliner.database.menu = User.Menu.USER_MANAGE_PLAYLIST_VOICE
                else:
                    await inliner.database.asave()
                    raise RequestInterruption()
            case _:
                await inliner.database.asave()
                raise RequestInterruption()
    except Meme.DoesNotExist:
        await inliner.database.asave()
        raise RequestInterruption()
    inliner.menu_cleanup()
    for attr in new_attributes:
        setattr(inliner.database, attr, new_attributes[attr])
    inliner.database.menu_mode = inliner.database.MenuMode.USER
    if inliner.database.current_meme.type == MemeType.VOICE:
        meme_translation = user_messages['voice']
        meme_keyboard = manage_voice
    else:
        meme_translation = user_messages['video']
        meme_keyboard = manage_video
    async with TaskGroup() as tg:
        tg.create_task(answer_callback_query(user_messages['manage_meme'].format(meme_translation), False))
        tg.create_task(inliner.send_message(
            user_messages['managing_meme'].format(meme_translation), meme_keyboard
        ))
