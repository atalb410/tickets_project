from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tickets.models import QuotationRequest, QuoteAttachment, ActivityLog, Comment, QuoteChangeRequest, InspectionRequest

class Command(BaseCommand):
    help = 'Sets up user groups and creates a superuser'

    def handle(self, *args, **kwargs):
        # Create groups if they don't exist
        engineers_group, created = Group.objects.get_or_create(name='Engineers')
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} Engineers group'))

        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser "admin" with password "admin123"'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser "admin" already exists'))

        # Add admin to Engineers group
        admin_user = User.objects.get(username='admin')
        admin_user.groups.add(engineers_group)
        self.stdout.write(self.style.SUCCESS('Added admin user to Engineers group'))

        # Create a test agent user if it doesn't exist
        if not User.objects.filter(username='agent').exists():
            agent_user = User.objects.create_user('agent', 'agent@example.com', 'agent123')
            self.stdout.write(self.style.SUCCESS('Created agent user "agent" with password "agent123"'))
        else:
            self.stdout.write(self.style.SUCCESS('Agent user "agent" already exists'))

        self.stdout.write(self.style.SUCCESS('Setup completed successfully')) 