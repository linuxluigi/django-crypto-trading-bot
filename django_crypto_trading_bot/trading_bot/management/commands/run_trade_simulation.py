from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Start the simulation'

    def handle(self, *args, **options):
        print("cooming soon...")
