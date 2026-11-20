"""Seed fictional demo data from PDF section 6 (US26)."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from complex import services
from complex.models import (
    Announcement,
    Block,
    DuesCharge,
    MaintenanceRequest,
    ManagementAssignment,
    Payment,
    Person,
    Residency,
    ResidentialSite,
    Unit,
)

DEMO_PASSWORD = "demo-pass-2026"
DEMO_USERNAMES = ("deniz", "ayse", "mehmet", "selin", "kemal", "canan")


def _validated_save(obj):
    obj.full_clean()
    obj.save()
    return obj


class Command(BaseCommand):
    help = "Load fictional Residential Complex Management demo data (PDF section 6)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing complex data and demo user accounts before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()

        if options["reset"]:
            Payment.objects.all().delete()
            DuesCharge.objects.all().delete()
            MaintenanceRequest.objects.all().delete()
            Announcement.objects.all().delete()
            Residency.objects.all().delete()
            ManagementAssignment.objects.all().delete()
            Unit.objects.all().delete()
            Block.objects.all().delete()
            ResidentialSite.objects.all().delete()
            Person.objects.all().delete()
            user_model.objects.filter(username__in=DEMO_USERNAMES).delete()
        elif ResidentialSite.objects.exists() or Person.objects.exists():
            self.stdout.write(
                self.style.WARNING("Demo data already exists. Re-run with --reset to reload cleanly.")
            )
            return

        site = _validated_save(
            ResidentialSite(
                site_name="Example Residential Complex",
                address="Cumhuriyet Mah. Örnek Sok. No: 12, Efeler, Aydın",
            )
        )

        blocks = {}
        units = {}
        for label in ("A", "B", "C"):
            block = _validated_save(Block(site=site, block_label=label))
            blocks[label] = block
            for num in range(1, 21):
                unit = _validated_save(
                    Unit(
                        block=block,
                        unit_number=num,
                        floor_number=((num - 1) // 4) + 1,  # A-12 is on floor 3 (PDF §6)
                    )
                )
                units[(label, num)] = unit

        def make_person(username, full_name, email, phone):
            user = user_model.objects.create_user(username=username, password=DEMO_PASSWORD, email=email)
            return _validated_save(Person(full_name=full_name, email=email, telephone=phone, user=user))

        deniz = make_person("deniz", "Deniz Aras", "deniz@example.test", "+90 555 000 0001")
        canan = make_person("canan", "Canan Öztürk", "canan@example.test", "+90 555 000 0005")
        ayse = make_person("ayse", "Ayşe Kaya", "ayse@example.test", "+90 555 000 0002")
        kemal = make_person("kemal", "Kemal Aydın", "kemal@example.test", "+90 555 000 0006")
        mehmet = make_person("mehmet", "Mehmet Demir", "mehmet@example.test", "+90 555 000 0003")
        selin = make_person("selin", "Selin Yılmaz", "selin@example.test", "+90 555 000 0004")

        # Management history (D05, BR13): Canan preceded Deniz
        _validated_save(
            ManagementAssignment(
                person=canan, site=site, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
            )
        )
        _validated_save(
            ManagementAssignment(person=deniz, site=site, start_date=date(2026, 1, 1), end_date=None)
        )

        # Residencies (D04, PDF §6): Kemal preceded Ayşe in A-12
        _validated_save(
            Residency(
                person=kemal, unit=units[("A", 12)], start_date=date(2025, 1, 1), end_date=date(2026, 8, 31)
            )
        )
        _validated_save(
            Residency(person=ayse, unit=units[("A", 12)], start_date=date(2026, 9, 1), end_date=None)
        )
        _validated_save(
            Residency(person=mehmet, unit=units[("B", 5)], start_date=date(2026, 2, 1), end_date=None)
        )
        _validated_save(
            Residency(person=selin, unit=units[("C", 3)], start_date=date(2026, 3, 1), end_date=None)
        )

        # Dues charges & confirmed payments (D06, D07, PDF §6)
        a12_nov = _validated_save(
            DuesCharge(
                unit=units[("A", 12)],
                billing_period=date(2026, 11, 1),
                amount=Decimal("1000.00"),
                due_date=date(2026, 11, 10),
            )
        )
        services.record_payment(
            charge=a12_nov,
            person=ayse,
            amount=Decimal("400.00"),
            payment_date=date(2026, 11, 3),
            method="Bank transfer",
            reference_number="P001",
        )
        services.record_payment(
            charge=a12_nov,
            person=ayse,
            amount=Decimal("600.00"),
            payment_date=date(2026, 11, 6),
            method="Bank transfer",
            reference_number="P002",
        )

        # Unpaid Dec 2026 charge on A-12 for live partial-payment / overpayment demo
        _validated_save(
            DuesCharge(
                unit=units[("A", 12)],
                billing_period=date(2026, 12, 1),
                amount=Decimal("1000.00"),
                due_date=date(2026, 12, 10),
            )
        )

        # Overdue charges for debtors list demo (B-05: 1000, C-03: 700)
        _validated_save(
            DuesCharge(
                unit=units[("B", 5)],
                billing_period=date(2026, 11, 1),
                amount=Decimal("1000.00"),
                due_date=date(2026, 11, 10),
            )
        )
        c03_nov = _validated_save(
            DuesCharge(
                unit=units[("C", 3)],
                billing_period=date(2026, 11, 1),
                amount=Decimal("1000.00"),
                due_date=date(2026, 11, 10),
            )
        )
        services.record_payment(
            charge=c03_nov,
            person=selin,
            amount=Decimal("300.00"),
            payment_date=date(2026, 11, 5),
            method="Bank transfer",
            reference_number="P003",
        )

        # Maintenance requests (D08)
        _validated_save(
            MaintenanceRequest(
                unit=units[("A", 12)],
                submitted_by=ayse,
                subject="Leaking tap",
                description="Kitchen sink tap has been dripping steadily since this morning.",
                submission_date=date(2026, 11, 4),
                status=MaintenanceRequest.OPEN,
            )
        )
        _validated_save(
            MaintenanceRequest(
                unit=units[("B", 5)],
                submitted_by=mehmet,
                subject="Intercom buzzer issue",
                description="Entrance buzzer does not ring inside the apartment.",
                submission_date=date(2026, 11, 12),
                status=MaintenanceRequest.IN_PROGRESS,
            )
        )

        # Announcements (D09)
        _validated_save(
            Announcement(
                site=site,
                author=deniz,
                title="Water Maintenance",
                message="Water supply will be interrupted on 5 November between 10:00 and 14:00 for pipe maintenance.",
                publication_date=date(2026, 11, 2),
            )
        )
        _validated_save(
            Announcement(
                site=site,
                author=deniz,
                title="Winter Heating Schedule",
                message="Central heating will operate daily from 06:30 to 23:00 starting this week.",
                publication_date=date(2026, 11, 15),
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded '{site.site_name}': {Block.objects.count()} blocks, "
                f"{Unit.objects.count()} units, {Person.objects.count()} people, "
                f"{DuesCharge.objects.count()} charges, {Payment.objects.count()} payments, "
                f"{MaintenanceRequest.objects.count()} requests, {Announcement.objects.count()} announcements."
            )
        )
