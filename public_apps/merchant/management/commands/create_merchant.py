from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from django.core.management.base import BaseCommand
from public_apps.merchant.models import Domain, Merchant

class Command(BaseCommand):
    help = 'Create a new merchant tenant with admin user'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)

    def handle(self, *args, **options):
        User = get_user_model()
        schema_name = options['name'].lower().replace(' ', '_')
        
        # Use schema_context for public schema operations
        with schema_context('public'):
            # Create merchant tenant
            merchant = Merchant.objects.create(
                name=options['name'],
                schema_name=schema_name,
                contact_email=options['email'],
                status='active'
            )
            
            Domain.objects.create(
                domain=options['domain'],
                tenant=merchant,
                is_primary=True
            )

        # Create tenant admin user in the new tenant's schema
        with schema_context(schema_name):
            admin_user = User.objects.create_superuser(
                email=options['email'],
                password=options['password'],
                role='tenant_admin',
                tenant=merchant,
                is_staff=True,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(f"""
                Successfully created merchant tenant:
                Name: {merchant.name}
                Schema: {merchant.schema_name}
                Domain: {options['domain']}
                Admin User: {admin_user.email} (username: {admin_user.username})
                Admin URL: http://{options['domain']}/admin/
                """)
            )