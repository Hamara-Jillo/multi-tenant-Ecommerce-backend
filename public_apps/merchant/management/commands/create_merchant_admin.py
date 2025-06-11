from django.core.management.base import BaseCommand
from django.core.management import call_command
from public_apps.merchant.models import Merchant, Domain
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates the admin merchant and superuser'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True)
        parser.add_argument('--domain', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--schema', type=str, required=True)

    def handle(self, *args, **options):
        User = get_user_model()
        
        logger.info("Starting admin merchant creation...")
        
        # Drop and recreate database schemas
        with connection.cursor() as cursor:
            logger.debug("Dropping existing schemas...")
            cursor.execute('DROP SCHEMA IF EXISTS public CASCADE')
            cursor.execute('CREATE SCHEMA public')
            
        # Apply initial migrations
        logger.info("Applying migrations...")
        call_command('migrate_schemas', '--shared')
        
        # Create admin tenant
        with schema_context('public'):
            try:
                logger.debug("Creating merchant...")
                # Create merchant tenant first, but don't create user automatically
                merchant = Merchant.objects.create(
                    name=options['name'],
                    schema_name=options['schema'],
                    contact_email=options['email'],
                    domain_url=options['domain'],
                    status='active',
                    is_verified=True,
                    auto_create_admin=False  # Prevent automatic user creation
                )

                logger.debug("Creating superuser...")
                # Create single superuser
                user = User.objects.create_superuser(
                    email=options['email'],
                    password=options['password'],
                    is_staff=True,
                    is_superuser=True,
                    is_platform_admin=True,  # Link user to merchant
                )

                self.stdout.write(
                    self.style.SUCCESS(f'''
                    Successfully created admin merchant:
                    Name: {merchant.name}
                    Schema: {merchant.schema_name}
                    Domain: {merchant.domain_url}
                    Admin Email: {user.email}
                    Admin URL: http://{merchant.domain_url}/admin/
                    ''')
                )
            except Exception as e:
                logger.error(f"Error creating admin merchant: {str(e)}")
                logger.exception("Full error details:")
                raise e