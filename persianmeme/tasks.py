from .models import Meme
from background_task import background
from zoneinfo import ZoneInfo
from datetime import datetime
from background_task.models import CompletedTask


@background(schedule=3600)
def revoke_review(meme_id: int):
    try:
        target_meme = Meme.objects.get(id=meme_id, reviewed=False, status=Meme.Status.ACTIVE)
    except Meme.DoesNotExist:
        return
    target_meme.assigned_admin = None
    target_meme.save()


@background(schedule=21600)
def check_meme(meme_id: int):
    CompletedTask.objects.all().delete()
    try:
        meme = Meme.objects.get(id=meme_id, status=Meme.Status.PENDING)
    except Meme.DoesNotExist:
        return
    if datetime.now(ZoneInfo('Asia/Tehran')).hour < 8:
        return check_meme(meme_id)
    accept_count = meme.accept_vote.count()
    deny_count = meme.deny_vote.count()
    if accept_count == deny_count == 0:
        return check_meme(meme_id)
    else:
        meme.delete_vote()
        if accept_count >= deny_count:
            meme.accept()
        else:
            meme.deny()
