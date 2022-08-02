from pydub import AudioSegment
from LilSholex.persianmeme.models import Meme
from persianmeme.keyboards import user as user_keyboard, back as back_keyboard
from persianmeme.models import User
from persianmeme.classes import User as UserClass


def duration_to_milliseconds(durations: list):
    seconds = []
    for duration in durations:
        duration = reversed(duration)
        stemp = []
        for index, value in enumerate(duration):
            stemp.append(int(value) * (60 * index) if index else 1)
        seconds.append(sum(stemp) * 1000)
    return seconds


def handler(text: str, user: UserClass):
    file_path = user.database.last_meme_file
    if '-' in text and ':' in text:
        start, end = duration_to_milliseconds(list(map(
            lambda x: x.split(':'),
            text.split('-')
        )))
        audio_segment_ogg = AudioSegment.from_ogg(file_path)
        if len(audio_segment_ogg) >= start and len(audio_segment_ogg) <= end:
            result = audio_segment_ogg[start:end]
            result.export(file_path.replace('ogg', 'mp3'), format='mp3')
            result = user.send_voice(file_path.replace(
                'ogg', 'mp3'), "Trimmed !")['voice']
            # Maybe regex ? : re.search(r'downloads/(.*)\.ogg', file_path).group(1)
            old_file_id = file_path.replace('.ogg', '').replace('downloads/', '')
            Meme.objects.filter(file_id=old_file_id).update(
                file_id=result['file_id'],
                file_unique_id=result['file_unique_id'],
                message_id=result['message_id']
            )
            user.database.last_meme.send_vote(user.session)
            user.send_message(user.translate(
                'meme_added', user.temp_meme_translation), user_keyboard)

            user.database.last_meme = None
            user.database.last_meme_file = None
            user.database.menu = User.Menu.USER_MAIN
        else:
            user.send_message(user.translate('invalid_duration'))
