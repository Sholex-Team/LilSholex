from .models import Meme
from zoneinfo import ZoneInfo
from datetime import datetime
from LilSholex import celery_app
from django.conf import settings


@celery_app.task
def revoke_review(meme_id: int):
    try:
        target_meme = Meme.objects.get(id=meme_id, reviewed=False, status=Meme.Status.ACTIVE)
    except Meme.DoesNotExist:
        return
    target_meme.assigned_admin = None
    target_meme.save()


@celery_app.task
def check_meme(meme_id: int):
    try:
        meme = Meme.objects.get(id=meme_id, status=Meme.Status.PENDING)
    except Meme.DoesNotExist:
        return
    if datetime.now(ZoneInfo('Asia/Tehran')).hour < 8:
        meme.task_id = check_meme.apply_async((meme_id,), countdown=settings.CHECK_MEME_COUNTDOWN)
        meme.save()
        return
    accept_count = meme.accept_vote.count()
    deny_count = meme.deny_vote.count()
    if accept_count == deny_count == 0:
        meme.task_id = check_meme.apply_async((meme_id,), countdown=settings.CHECK_MEME_COUNTDOWN)
        meme.save()
    else:
        if accept_count >= deny_count:
            meme.accept()
        else:
            meme.deny()
