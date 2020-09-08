from .models import Voice
from background_task import background
from .functions import delete_vote
from asgiref.sync import sync_to_async


@background(schedule=28800)
def check_voice(voice_id: int):
    try:
        voice = Voice.objects.get(voice_id=voice_id, status='p')
    except Voice.DoesNotExist:
        return
    if (accept_count := voice.accept_vote.count()) == (deny_count := voice.deny_vote.count()) == 0:
        return check_voice(voice_id)
    else:
        delete_vote(voice)
        if accept_count >= deny_count:
            voice.accept()
        else:
            voice.deny()


@sync_to_async
def create_check_voice(voice_id: int):
    check_voice(voice_id)
