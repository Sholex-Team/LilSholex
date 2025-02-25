from .models import Meme
from zoneinfo import ZoneInfo
from datetime import datetime
from LilSholex import celery_app
from django.conf import settings
from asgiref.sync import async_to_sync
from aiohttp import ClientSession, ClientTimeout
from LilSholex.context import telegram as telegram_context


@async_to_sync
async def async_to_sync_request(request_func):
    async with ClientSession(timeout=ClientTimeout(settings.REQUESTS_TIMEOUT)) as session:
        telegram_context.common.HTTP_SESSION.set(session)
        await request_func()


@celery_app.task
def revoke_review(meme_id: int):
    Meme.objects.filter(id=meme_id, reviewed=False, status=Meme.Status.ACTIVE).update(review_admin=None)


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
            async_to_sync_request(meme.accept)
        else:
            async_to_sync_request(meme.deny)
