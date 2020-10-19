from django.core.management.base import BaseCommand
from persianmeme.models import Broadcast, User
from persianmeme.classes import User as UserClass
from time import sleep


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            broadcast = Broadcast.objects.filter(sent=False)
            if broadcast.exists():
                broadcast = broadcast.first()
                for user in User.objects.filter(started=True):
                    UserClass(instance=user).forward_message(broadcast.sender.chat_id, broadcast.message_id)
                broadcast.sent = True
                broadcast.save()
            sleep(15)
