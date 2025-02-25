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
            broadcast = Broadcast.objects.filter(sent=False).select_related('sender')
            if broadcast.exists():
                self.stdout.write('Processing a broadcast.')
                broadcast = broadcast.first()
                asyncio.run(perform_broadcast(broadcast))
                broadcast.sent = True
                db.close_old_connections()
                broadcast.save()
                self.stdout.write('Broadcast has been processed.')
                return sleep(15)
            self.stdout.write('There isn\'t any broadcast to process !')
            sleep(15)
