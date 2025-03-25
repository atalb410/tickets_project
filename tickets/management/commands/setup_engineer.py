from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib import messages

class Command(BaseCommand):
    help = 'Creates an engineer user and adds them to the Engineers group'

    def handle(self, *args, **kwargs):
        # Create Engineers group if it doesn't exist
        engineers_group, created = Group.objects.get_or_create(name='Engineers')
        if created:
            self.stdout.write(self.style.SUCCESS('Engineers group created successfully'))

        # Create engineer user if it doesn't exist
        if not User.objects.filter(username='engineer').exists():
            engineer = User.objects.create_user(
                username='engineer',
                password='engineer123',
                email='engineer@example.com'
            )
            engineer.groups.add(engineers_group)
            self.stdout.write(self.style.SUCCESS('Engineer user created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Engineer user already exists'))

        # Print login credentials
        self.stdout.write(self.style.SUCCESS('\nEngineer Login Credentials:'))
        self.stdout.write(self.style.SUCCESS('Username: engineer'))
        self.stdout.write(self.style.SUCCESS('Password: engineer123')) 