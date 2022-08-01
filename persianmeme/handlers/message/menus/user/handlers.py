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
    trim_voice_yes_or_no,
    user_trim_duration
)


def handler(message: dict, text: str, message_id: int, user: UserClass):
    match user.database.menu:
        case User.Menu.USER_MAIN:
            main.handler(message, text, message_id, user)
        case User.Menu.USER_CONTACT_ADMIN:
            contact_admin.handler(message_id, user)
        case User.Menu.USER_SUGGEST_MEME_NAME if user.validate_meme_name(message, text, user.database.temp_meme_type):
            suggest_meme_name.handler(text, user)
        case User.Menu.USER_SETTINGS:
            settings_menu.handler(text, message_id, user)
        case User.Menu.USER_SUGGEST_MEME_TAGS if user.process_meme_tags(text):
            suggest_meme_tags.handler(user)
        case User.Menu.USER_SUGGEST_MEME if target_meme := user.add_meme(message, Meme.Status.PENDING):
            suggest_meme.handler(target_meme, user)
        case User.Menu.USER_RANKING:
            ranking.handler(text, message_id, user)
        case User.Menu.USER_SORTING:
            sorting.handler(text, message_id, user)
        case User.Menu.USER_RECENT_VOICES:
            recent_voices.handler(text, user)
        case User.Menu.USER_DELETE_REQUEST if target_meme := user.get_public_meme(message):
            delete_request.handler(message_id, target_meme, user)
        case User.Menu.USER_PRIVATE_VOICES:
            private_voices.handler(text, message_id, user)
        case User.Menu.USER_PRIVATE_VOICE_NAME if user.validate_meme_name(message, text, MemeType.VOICE):
            private_voice_name.handler(text, user)
        case User.Menu.USER_PRIVATE_VOICE_TAGS if user.process_meme_tags(text):
            private_voice_tags.handler(user)
        case User.Menu.USER_PRIVATE_VOICE if user.voice_exists(message) and user.create_private_voice(message):
            private_voice.handler(user)
        case User.Menu.USER_MANAGE_PRIVATE_VOICE if user.check_current_meme():
            manage_private_voice.handler(text, message_id, user)
        case User.Menu.USER_PLAYLISTS:
            playlists.handler(text, message_id, user)
        case User.Menu.USER_CREATE_PLAYLIST:
            create_playlist.handler(text, message_id, user)
        case User.Menu.USER_MANAGE_PLAYLIST if user.database.current_playlist:
            manage_playlist.handler(text, message_id, user)
        case User.Menu.USER_ADD_VOICE_PLAYLIST if user.voice_exists(message):
            add_voice_playlist.handler(message['voice']['file_unique_id'], message_id, user)
        case User.Menu.USER_MANAGE_PLAYLIST_VOICE if user.check_current_meme():
            manage_playlist_voice.handler(text, user)
        case User.Menu.USER_HELP:
            help.handler(text, message_id, user)
        case User.Menu.USER_VOICE_SUGGESTIONS:
            voice_suggestions.handler(text, message_id, user)
        case User.Menu.USER_VIDEO_SUGGESTIONS:
            video_suggestions.handler(text, message_id, user)
        case User.Menu.USER_MANAGE_VIDEO_SUGGESTION | \
                User.Menu.USER_MANAGE_VOICE_SUGGESTION if user.check_current_meme():
            manage_meme_suggestion.handler(text, message_id, user)
        case User.Menu.USER_MANAGE_VOICES:
            manage_voices.handler(text, message_id, user)
        case User.Menu.USER_SUGGEST_MEME_TYPE:
            suggest_meme_type.handler(text, message_id, user)
        case User.Menu.USER_REPORT_MEME:
            report_meme.handler(message, message_id, user)
        case User.Menu.USER_SEARCH_ITEMS:
            search_items.handler(text, message_id, user)
        case User.Menu.USER_TRIM_VOICE_YES_OR_NO:
            trim_voice_yes_or_no.handler(text, user)
        case User.Menu.USER_TRIM_DURATION:
            user_trim_duration.handler(text, user)