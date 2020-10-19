from .models import Voice
from background_task import background
from .functions import delete_vote
import pytz


@background(schedule=28800)
def check_voice(voice_id: int):
    try:
        voice = Voice.objects.get(voice_id=voice_id, status='p')
    except Voice.DoesNotExist:
        return
    aware_date = pytz.timezone('Asia/Tehran').localize(voice.last_check)
    if 0 < aware_date.hour < 8:
        voice.save()
        return check_voice(voice_id, schedule=21600)
    accept_count = voice.accept_vote.count()
    deny_count = voice.deny_vote.count()
    if accept_count == deny_count == 0:
        return check_voice(voice_id)
    else:
        delete_vote(voice)
        if accept_count >= deny_count:
            voice.accept()
        else:
            voice.deny()
