# scripts/flush_and_setup_data.py

import os
import sys

# Fix path issues so we can import project settings
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import Membership, Organization
from vendors.models import Vendor

User = get_user_model()


def run():
    print("🚨 Flushing database...")
    call_command("flush", interactive=True)

    print("✅ Creating default organization...")
    org = Organization.objects.create(
        name="VendorGuard Solo",
        domain="vendorguard.local",
        is_personal=True,
    )

    print("👤 Creating superuser...")
    if not User.objects.filter(email="rickyanand2@gmail.com").exists():
        user = User.objects.create_superuser(
            email="rickyanand2@gmail.com",
            password="123",
            first_name="Ricky",
            last_name="Anand",
            job_title="Admin",
            is_active=True,
            is_admin=True,
            is_superuser=True,
            is_verified_email=True,
        )

        # ✅ Link user to organization via Membership
        Membership.objects.create(user=user, organization=org, role="owner")

        print("✅ Superuser created and linked to organization.")
    else:
        print("⚠️ Superuser already exists.")

    print("🏢 Creating test vendors...")
    Vendor.objects.create(
        name="Test Vendor 1", description="Example vendor 1", organization=org
    )
    Vendor.objects.create(
        name="Test Vendor 2", description="Example vendor 2", organization=org
    )
    print("✅ Vendors created.")


if __name__ == "__main__":
    run()
