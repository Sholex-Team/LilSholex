from persianmeme.models import User, Playlist
from LilSholex.exceptions import RequestInterruption
from persianmeme.translations import user_messages
from persianmeme.keyboards import manage_playlist
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    inliner = telegram_context.common.USER.get()
    try:
        inliner.database.current_playlist = await Playlist.objects.aget(
            id=meme_context.common.PLAYLIST_ID.get(),
            creator=inliner.database
        )
    except (Playlist.DoesNotExist, ValueError):
        await inliner.database.asave()
        raise RequestInterruption()
    inliner.menu_cleanup()
    inliner.database.menu_mode = inliner.database.MenuMode.USER
    inliner.database.menu = User.Menu.USER_MANAGE_PLAYLIST
    inliner.database.back_menu = 'manage_playlists'
    async with TaskGroup() as tg:
        tg.create_task(answer_callback_query(user_messages['managing_playlist'], False))
        tg.create_task(inliner.send_message(user_messages['manage_playlist'], manage_playlist))
