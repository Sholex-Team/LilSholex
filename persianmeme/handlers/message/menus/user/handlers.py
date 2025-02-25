from persianmeme.models import User, MemeType, Meme
from persianmeme.classes import User as UserClass
from .menus import (
    main,
    settings as settings_menu,
    ranking,
    sorting,
    suggest_meme_name,
    suggest_meme,
    recent_voices,
    delete_request,
    private_voices,
    manage_playlist,
    manage_private_voice,
    playlists,
    manage_playlist_voice,
    voice_suggestions,
    video_suggestions,
    manage_meme_suggestion,
    manage_voices,
    suggest_meme_type,
    contact_admin,
    suggest_meme_tags,
    private_voice_name,
    private_voice_tags,
    private_voice,
    create_playlist,
    add_voice_playlist,
    help,
    report_meme,
    search_items,
    cancel_voting
)
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match user.database.menu:
        case User.Menu.USER_MAIN:
            await main.handler()
        case User.Menu.USER_CONTACT_ADMIN:
            await contact_admin.handler()
        case User.Menu.USER_SUGGEST_MEME_NAME:
            if await user.validate_meme_name(user.database.temp_meme_type):
                await suggest_meme_name.handler()
        case User.Menu.USER_SETTINGS:
            await settings_menu.handler()
        case User.Menu.USER_SUGGEST_MEME_TAGS:
            if await user.process_meme_tags():
                await suggest_meme_tags.handler()
        case User.Menu.USER_SUGGEST_MEME:
            if target_meme := await user.add_meme(Meme.Status.PENDING):
                meme_context.common.MEME.set(target_meme)
                await suggest_meme.handler()
        case User.Menu.USER_RANKING:
            await ranking.handler()
        case User.Menu.USER_SORTING:
            await sorting.handler()
        case User.Menu.USER_RECENT_VOICES:
            await recent_voices.handler()
        case User.Menu.USER_DELETE_REQUEST:
            if target_meme := await user.get_public_meme():
                meme_context.common.MEME.set(target_meme)
                await delete_request.handler()
        case User.Menu.USER_PRIVATE_VOICES:
            await private_voices.handler()
        case User.Menu.USER_PRIVATE_VOICE_NAME:
            if await user.validate_meme_name(MemeType.VOICE):
                await private_voice_name.handler()
        case User.Menu.USER_PRIVATE_VOICE_TAGS:
            if await user.process_meme_tags():
                await private_voice_tags.handler()
        case User.Menu.USER_PRIVATE_VOICE:
            if await user.voice_exists() and await user.create_private_voice():
                await private_voice.handler()
        case User.Menu.USER_MANAGE_PRIVATE_VOICE:
            if await user.check_current_meme():
                await manage_private_voice.handler()
        case User.Menu.USER_PLAYLISTS:
            await playlists.handler()
        case User.Menu.USER_CREATE_PLAYLIST:
            await create_playlist.handler()
        case User.Menu.USER_MANAGE_PLAYLIST:
            if await user.check_current_playlist():
                await manage_playlist.handler()
        case User.Menu.USER_ADD_VOICE_PLAYLIST:
            if await user.voice_exists():
                await add_voice_playlist.handler()
        case User.Menu.USER_MANAGE_PLAYLIST_VOICE:
            if await user.check_current_meme() and await user.check_current_playlist():
                await manage_playlist_voice.handler()
        case User.Menu.USER_HELP:
            await help.handler()
        case User.Menu.USER_VOICE_SUGGESTIONS:
            await voice_suggestions.handler()
        case User.Menu.USER_VIDEO_SUGGESTIONS:
            await video_suggestions.handler()
        case User.Menu.USER_MANAGE_VIDEO_SUGGESTION | User.Menu.USER_MANAGE_VOICE_SUGGESTION:
            if await user.check_current_meme():
                await manage_meme_suggestion.handler()
        case User.Menu.USER_MANAGE_VOICES:
            await manage_voices.handler()
        case User.Menu.USER_SUGGEST_MEME_TYPE:
            await suggest_meme_type.handler()
        case User.Menu.USER_REPORT_MEME:
            await report_meme.handler()
        case User.Menu.USER_SEARCH_ITEMS:
            await search_items.handler()
        case User.Menu.USER_CANCEL_VOTING:
            await cancel_voting.handler()
