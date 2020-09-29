from .models import Voice, User, AdminVote
from .classes import User
from django.db.models import F
from background_task import background
from .functions import delete_vote, kick_admin


@background(schedule=28800)
def check_voice(voice_id: int):
    try:
        voice = Voice.objects.get(voice_id=voice_id, status='p')
    except Voice.DoesNotExist:
        return
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
    owner = User(instance=User.objects.filter(rank=User.Rank.owner).first())
    for admin in User.objects.filter(rank=User.Rank.khiar):
        vote, created = AdminVote.objects.get_or_create(admin=admin)
        if not (admin in voice.deny_vote.all() or admin in voice.accept_vote.all()):
            vote.count = F('count') + 1
            vote.save()
            if vote.count >= 10:
                admin.rank = User.Rank.user
                admin.save()
                kick_admin(admin.chat_id)
                owner.send_message(f'Admin {admin.chat_id} : {admin.username} has been demoted !')
                vote.delete()
        else:
            vote.count = 0
            vote.save()
