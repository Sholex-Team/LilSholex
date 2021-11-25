from persianmeme.models import User, Playlist
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User as UserClass
from persianmeme.translations import user_messages
from persianmeme.keyboards import manage_playlist


def handler(playlist_id: int, query_id: str, answer_query, inliner: UserClass):
    try:
        inliner.database.current_playlist = Playlist.objects.get(
            id=playlist_id, creator=inliner.database
        )
    except (Playlist.DoesNotExist, ValueError):
        inliner.database.save()
        raise RequestInterruption()
    inliner.menu_cleanup()
    inliner.database.menu_mode = inliner.database.MenuMode.USER
    inliner.database.menu = User.Menu.USER_MANAGE_PLAYLIST
    inliner.database.back_menu = 'manage_playlists'
    answer_query(query_id, user_messages['managing_playlist'], False)
    inliner.send_message(user_messages['manage_playlist'], manage_playlist)
