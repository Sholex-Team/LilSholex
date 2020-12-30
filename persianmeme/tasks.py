from .models import Voice
from background_task import background
from .functions import delete_vote_sync
from zoneinfo import ZoneInfo
from background_task.models import CompletedTask


@background(schedule=14400)
def check_voice(voice_id: int):
    CompletedTask.objects.all().delete()
    try:
        voice = Voice.objects.get(voice_id=voice_id, status='p')
    except Voice.DoesNotExist:
        return
    aware_date = voice.last_check.astimezone(ZoneInfo('Asia/Tehran'))
    if 0 < aware_date.hour < 8:
        voice.save()
        return check_voice(voice_id)
    accept_count = voice.accept_vote.count()
    deny_count = voice.deny_vote.count()
    if accept_count == deny_count == 0:
        return check_voice(voice_id)
    else:
        delete_vote_sync(voice)
        if accept_count >= deny_count:
            voice.accept()
        else:
            voice.deny()


@background(schedule=300)
def update_votes(voice_id: int):
    try:
        voice = Voice.objects.get(voice_id=voice_id)
    except Voice.DoesNotExist:
        return
    voice.edit_vote_count()
    update_votes(voice_id)
