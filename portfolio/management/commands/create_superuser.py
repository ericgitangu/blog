from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a superuser non-interactively'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username for the superuser')
        parser.add_argument('--email', required=True, help='Email for the superuser')
        parser.add_argument('--password', required=True, help='Password for the superuser')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
            return

        User.objects.create_superuser(
            username=options['username'],
            email=options['email'],
            password=options['password']
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully'))
