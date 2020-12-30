from django.core.management.base import BaseCommand
from persianmeme.models import Broadcast
from persianmeme.functions import perform_broadcast
from django import db
from time import sleep
import asyncio


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            db.close_old_connections()
            broadcast = Broadcast.objects.filter(sent=False)
            if broadcast.exists():
                broadcast = broadcast.first()
                asyncio.run(perform_broadcast(broadcast))
                broadcast.sent = True
                db.close_old_connections()
                broadcast.save()
            sleep(15)
