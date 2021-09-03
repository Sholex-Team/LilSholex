from django.core.management.base import BaseCommand
from background_task.models import Task


class Command(BaseCommand):
    def handle(self, *args, **options):
        Task.objects.update(locked_by=None, locked_at=None)
        self.stdout.write('All tasks have been cleared.')
