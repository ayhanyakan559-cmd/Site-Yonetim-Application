"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Automated tests covering business rules BR01-BR14, role access control, workflows, and seed_demo.
"""

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import (
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
    today,
)

User = get_user_model()


class ComplexTestMixin:
    def create_base_fixture(self):
        d = today()
        self.site = ResidentialSite.objects.create(
            site_name="Test Complex",
            address="Test Address, Aydin",
        )
        self.block_a = Block.objects.create(site=self.site, block_label="A")
        self.block_b = Block.objects.create(site=self.site, block_label="B")
        self.unit_a12 = Unit.objects.create(block=self.block_a, unit_number=12, floor_number=3)
        self.unit_b05 = Unit.objects.create(block=self.block_b, unit_number=5, floor_number=2)

        self.manager_user = User.objects.create_user("manager", password="Password123!")
        self.manager = Person.objects.create(
            full_name="Deniz Aras", email="deniz@example.test", telephone="555-0001", user=self.manager_user
        )
        self.assignment = ManagementAssignment.objects.create(
            person=self.manager, site=self.site, start_date=d - timedelta(days=60)
        )

        self.resident_user = User.objects.create_user("ayse", password="Password123!")
        self.resident = Person.objects.create(
            full_name="Ayse Kaya", email="ayse@example.test", telephone="555-0002", user=self.resident_user
        )
        self.residency = Residency.objects.create(
            person=self.resident, unit=self.unit_a12, start_date=d - timedelta(days=30)
        )

        self.other_user = User.objects.create_user("mehmet", password="Password123!")
        self.other_resident = Person.objects.create(
            full_name="Mehmet Demir", email="mehmet@example.test", telephone="555-0003", user=self.other_user
        )
        self.other_residency = Residency.objects.create(
            person=self.other_resident, unit=self.unit_b05, start_date=d - timedelta(days=30)
        )


class BusinessRulesTests(ComplexTestMixin, TestCase):
    def setUp(self):
        self.create_base_fixture()

    def test_br01_charge_and_payment_must_be_positive(self):
        d = today()
        for bad in (Decimal("0"), Decimal("-50.00")):
            charge = DuesCharge(
                unit=self.unit_a12,
                billing_period=date(2026, 11, 1),
                amount=bad,
                due_date=d + timedelta(days=10),
            )
            with self.assertRaises(ValidationError):
                charge.full_clean()

        valid_charge = DuesCharge.objects.create(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 1),
            amount=Decimal("1000.00"),
            due_date=d + timedelta(days=10),
        )
        for bad in (Decimal("0"), Decimal("-10.00")):
            with self.assertRaises(ValidationError):
                services.record_payment(
                    charge=valid_charge,
                    person=self.resident,
                    amount=bad,
                    payment_date=d,
                    method="Bank transfer",
                    reference_number="BAD1",
                )
            p = Payment(
                charge=valid_charge,
                person=self.resident,
                amount=bad,
                payment_date=d,
                method="Bank transfer",
                reference_number="BAD2",
            )
            with self.assertRaises(ValidationError):
                p.full_clean()

    def test_br02_br03_br14_partial_payments_derived_outstanding_and_no_overpayment(self):
        d = today()
        charge = DuesCharge.objects.create(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 1),
            amount=Decimal("1000.00"),
            due_date=d + timedelta(days=10),
        )
        self.assertEqual(charge.outstanding_amount, Decimal("1000.00"))
        self.assertEqual(charge.status(d), DuesCharge.UNPAID)

        p1 = services.record_payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("400.00"),
            payment_date=d,
            method="Bank transfer",
            reference_number="P001",
        )
        self.assertEqual(p1.charge_id, charge.pk)  # BR14: single charge per payment
        self.assertEqual(charge.outstanding_amount, Decimal("600.00"))
        self.assertEqual(charge.status(d), DuesCharge.PARTIAL)

        # Overpayment rejected by service AND by model.full_clean()
        with self.assertRaises(ValidationError):
            services.record_payment(
                charge=charge,
                person=self.resident,
                amount=Decimal("700.00"),
                payment_date=d,
                method="Bank transfer",
                reference_number="P_OVER",
            )
        bad_payment = Payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("600.01"),
            payment_date=d,
            method="Cash",
            reference_number="P_OVER_MODEL",
        )
        with self.assertRaises(ValidationError):
            bad_payment.full_clean()

        p2 = services.record_payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("600.00"),
            payment_date=d,
            method="Bank transfer",
            reference_number="P002",
        )
        self.assertEqual(p2.charge_id, charge.pk)
        self.assertEqual(charge.outstanding_amount, Decimal("0.00"))
        self.assertEqual(charge.status(d), DuesCharge.SETTLED)

    def test_br04_charge_status_transitions_including_overdue(self):
        charge = DuesCharge.objects.create(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 1),
            amount=Decimal("1000.00"),
            due_date=date(2026, 11, 10),
        )
        self.assertEqual(charge.status(date(2026, 11, 10)), DuesCharge.UNPAID)
        self.assertEqual(charge.status(date(2026, 11, 11)), DuesCharge.OVERDUE)

        services.record_payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("400.00"),
            payment_date=date(2026, 11, 11),
            method="Bank transfer",
            reference_number="P1",
        )
        self.assertEqual(charge.status(date(2026, 11, 10)), DuesCharge.PARTIAL)
        self.assertEqual(charge.status(date(2026, 11, 11)), DuesCharge.OVERDUE)

        services.record_payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("600.00"),
            payment_date=date(2026, 11, 12),
            method="Bank transfer",
            reference_number="P2",
        )
        self.assertEqual(charge.status(date(2026, 11, 12)), DuesCharge.SETTLED)

    def test_br05_end_date_cannot_precede_start_date(self):
        r = Residency(
            person=self.other_resident,
            unit=self.unit_a12,
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 9),
        )
        with self.assertRaises(ValidationError):
            r.full_clean()

        # Same start and end date is allowed
        r_same = Residency(
            person=self.other_resident,
            unit=self.unit_a12,
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 10),
        )
        r_same.full_clean()

        ma = ManagementAssignment(
            person=self.other_resident,
            site=self.site,
            start_date=date(2024, 5, 10),
            end_date=date(2024, 5, 9),
        )
        with self.assertRaises(ValidationError):
            ma.full_clean()

    def test_br06_overlapping_residency_rejected_and_co_residents_allowed(self):
        # Overlapping residency for the same person + unit is rejected
        dup = Residency(
            person=self.resident,
            unit=self.unit_a12,
            start_date=self.residency.start_date + timedelta(days=5),
        )
        with self.assertRaises(ValidationError):
            dup.full_clean()

        # Different person living in the same unit at the same time is allowed
        roommate = Residency(
            person=self.other_resident,
            unit=self.unit_a12,
            start_date=self.residency.start_date,
        )
        roommate.full_clean()
        roommate.save()

        # Non-overlapping residency for the same person + unit is allowed after end_date
        d = today()
        self.residency.end_date = d - timedelta(days=5)
        self.residency.full_clean()
        self.residency.save()
        returned = Residency(person=self.resident, unit=self.unit_a12, start_date=d - timedelta(days=4))
        returned.full_clean()

    def test_br07_history_kept_after_move_and_dual_roles_independent(self):
        d = today()
        charge = DuesCharge.objects.create(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 1),
            amount=Decimal("1000.00"),
            due_date=d + timedelta(days=5),
        )
        services.record_payment(
            charge=charge,
            person=self.resident,
            amount=Decimal("400.00"),
            payment_date=d,
            method="Bank transfer",
            reference_number="P001",
        )
        req = services.submit_request(
            unit=self.unit_a12, person=self.resident, subject="Leaking tap", description="Drips"
        )

        # Resident moves out yesterday
        self.residency.end_date = d - timedelta(days=1)
        self.residency.full_clean()
        self.residency.save()

        self.assertFalse(self.unit_a12.is_occupied(d))
        self.assertEqual(self.unit_a12.dues_charges.count(), 1)
        self.assertEqual(charge.payments.count(), 1)
        self.assertEqual(self.unit_a12.maintenance_requests.count(), 1)
        self.assertEqual(req.submitted_by, self.resident)

        # Dual role: manager can also hold an active residency without conflict
        dual = Residency.objects.create(person=self.manager, unit=self.unit_a12, start_date=d)
        dual.full_clean()
        self.assertTrue(self.manager.manages(self.site, d))
        self.assertTrue(self.manager.resides_in(self.unit_a12, d))

    def test_br08_block_and_unit_uniqueness(self):
        dup_block = Block(site=self.site, block_label="a")  # normalized to A
        with self.assertRaises(ValidationError):
            dup_block.full_clean()

        dup_unit = Unit(block=self.block_a, unit_number=12, floor_number=3)
        with self.assertRaises(ValidationError):
            dup_unit.full_clean()

        # Same unit number in a different block is allowed
        other_block_unit = Unit(block=self.block_b, unit_number=12, floor_number=3)
        other_block_unit.full_clean()

    def test_br09_one_charge_per_unit_per_billing_period(self):
        DuesCharge.objects.create(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 15),  # normalized to day=1
            amount=Decimal("1000.00"),
            due_date=date(2026, 11, 30),
        )
        second = DuesCharge(
            unit=self.unit_a12,
            billing_period=date(2026, 11, 28),
            amount=Decimal("1200.00"),
            due_date=date(2026, 11, 30),
        )
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_br10_maintenance_request_requires_active_residency(self):
        d = today()
        req = services.submit_request(
            unit=self.unit_a12, person=self.resident, subject="Tap", description="Leaking"
        )
        self.assertEqual(req.status, MaintenanceRequest.OPEN)

        # Non-resident of unit A-12 rejected
        with self.assertRaises(ValidationError):
            services.submit_request(
                unit=self.unit_a12, person=self.other_resident, subject="Tap", description="Not mine"
            )

        # Former resident rejected
        self.residency.end_date = d - timedelta(days=1)
        self.residency.save()
        with self.assertRaises(ValidationError):
            services.submit_request(
                unit=self.unit_a12, person=self.resident, subject="Tap", description="After move-out"
            )

    def test_br11_request_status_transitions_and_active_manager_only(self):
        req = services.submit_request(
            unit=self.unit_a12, person=self.resident, subject="Tap", description="Leaking"
        )
        services.update_request_status(request_obj=req, actor=self.manager, new_status=MaintenanceRequest.IN_PROGRESS)
        req.refresh_from_db()
        self.assertEqual(req.status, MaintenanceRequest.IN_PROGRESS)

        services.update_request_status(request_obj=req, actor=self.manager, new_status=MaintenanceRequest.RESOLVED)
        req.refresh_from_db()
        self.assertEqual(req.status, MaintenanceRequest.RESOLVED)

        with self.assertRaises(ValidationError):
            services.update_request_status(request_obj=req, actor=self.manager, new_status="Closed")

        with self.assertRaises(PermissionDenied):
            services.update_request_status(request_obj=req, actor=self.resident, new_status=MaintenanceRequest.OPEN)

    def test_br12_announcement_requires_active_manager(self):
        ann = services.publish_announcement(site=self.site, author=self.manager, title="Notice", message="Body")
        self.assertEqual(ann.site, self.site)

        with self.assertRaises(ValidationError):
            services.publish_announcement(site=self.site, author=self.resident, title="Illegal", message="Body")

    def test_br13_single_active_management_assignment_and_sequential_history(self):
        d = today()
        overlap = ManagementAssignment(person=self.other_resident, site=self.site, start_date=d)
        with self.assertRaises(ValidationError):
            overlap.full_clean()

        self.assignment.end_date = d - timedelta(days=1)
        self.assignment.full_clean()
        self.assignment.save()

        next_mgr = ManagementAssignment(person=self.other_resident, site=self.site, start_date=d)
        next_mgr.full_clean()
        next_mgr.save()
        self.assertEqual(self.site.active_manager(d), self.other_resident)
        self.assertEqual(self.site.management_assignments.count(), 2)


class AccessControlTests(ComplexTestMixin, TestCase):
    def setUp(self):
        self.create_base_fixture()

    def test_anonymous_redirects_to_login(self):
        for name in ("home", "overview", "people", "debtors", "requests", "assignments", "announcements", "my_home"):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/login/", resp["Location"])

    def test_resident_cannot_access_manager_routes_or_submit_for_other_unit(self):
        self.client.force_login(self.resident_user)
        manager_urls = [
            reverse("overview"),
            reverse("unit_detail", args=[self.unit_a12.pk]),
            reverse("debtors"),
            reverse("requests"),
            reverse("people"),
            reverse("assignments"),
        ]
        for url in manager_urls:
            self.assertEqual(self.client.get(url).status_code, 403, msg=f"Expected 403 on {url}")

        # IDOR: Ayse cannot submit a maintenance request for Mehmet's unit B-05
        resp = self.client.post(
            reverse("request_submit", args=[self.unit_b05.pk]),
            {"subject": "Other unit", "description": "Trying IDOR"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(MaintenanceRequest.objects.filter(unit=self.unit_b05, submitted_by=self.resident).exists())

        # Resident cannot publish announcements
        resp = self.client.post(reverse("announcements"), {"title": "Hack", "message": "Nope"})
        self.assertEqual(resp.status_code, 403)

    def test_resident_my_home_shows_only_own_unit_charges(self):
        d = today()
        DuesCharge.objects.create(
            unit=self.unit_a12, billing_period=date(2026, 11, 1), amount=Decimal("1000.00"), due_date=d
        )
        DuesCharge.objects.create(
            unit=self.unit_b05, billing_period=date(2026, 11, 1), amount=Decimal("2500.00"), due_date=d
        )

        self.client.force_login(self.resident_user)
        resp = self.client.get(reverse("my_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A-12")
        self.assertContains(resp, "1,000.00")
        self.assertNotContains(resp, "B-05")
        self.assertNotContains(resp, "2,500.00")

    def test_dual_role_user_can_access_both_manager_and_resident_views(self):
        Residency.objects.create(person=self.manager, unit=self.unit_a12, start_date=today())
        self.client.force_login(self.manager_user)
        self.assertEqual(self.client.get(reverse("overview")).status_code, 200)
        self.assertEqual(self.client.get(reverse("my_home")).status_code, 200)


class ManagerWorkflowAndSeedTests(ComplexTestMixin, TestCase):
    def setUp(self):
        self.create_base_fixture()

    def test_end_to_end_manager_and_resident_workflows(self):
        d = today()
        self.client.force_login(self.manager_user)

        # Edit site, add block & unit, register person
        self.assertEqual(
            self.client.post(
                reverse("site_edit"), {"site_name": "Updated Complex", "address": "New Addr"}, follow=True
            ).status_code,
            200,
        )
        self.site.refresh_from_db()
        self.assertEqual(self.site.site_name, "Updated Complex")

        self.client.post(reverse("block_add"), {"block_label": "c"})
        self.assertTrue(Block.objects.filter(site=self.site, block_label="C").exists())
        block_c = Block.objects.get(site=self.site, block_label="C")

        self.client.post(reverse("unit_add"), {"block": block_c.pk, "unit_number": 1, "floor_number": 1})
        unit_c1 = Unit.objects.get(block=block_c, unit_number=1)

        self.client.post(
            reverse("people"),
            {"full_name": "New Resident", "telephone": "555-1111", "email": "new@example.test"},
        )
        new_person = Person.objects.get(full_name="New Resident")

        # Assign residency & end residency
        self.client.post(
            reverse("residency_add", args=[unit_c1.pk]),
            {"person": new_person.pk, "start_date": (d - timedelta(days=10)).isoformat(), "end_date": ""},
        )
        res = Residency.objects.get(person=new_person, unit=unit_c1)
        self.assertTrue(unit_c1.is_occupied(d))

        self.client.post(
            reverse("residency_end", args=[res.pk]),
            {"end_date": (d - timedelta(days=1)).isoformat()},
        )
        self.assertFalse(unit_c1.is_occupied(d))

        # Add charge and record partial + final payment
        self.client.post(
            reverse("charge_add", args=[self.unit_a12.pk]),
            {"billing_period": "2026-11", "amount": "1000.00", "due_date": (d - timedelta(days=5)).isoformat()},
        )
        charge = DuesCharge.objects.get(unit=self.unit_a12, billing_period=date(2026, 11, 1))

        # Debtors list includes overdue A-12
        debtors_resp = self.client.get(reverse("debtors"), {"block": "A", "period": "2026-11"})
        self.assertEqual(debtors_resp.status_code, 200)
        self.assertContains(debtors_resp, "A-12")

        # Overpayment via form shows error and does not save
        over_resp = self.client.post(
            reverse("payment_add", args=[charge.pk]),
            {
                "person": self.resident.pk,
                "payment_date": d.isoformat(),
                "amount": "1001.00",
                "method": "Bank transfer",
                "reference_number": "P_BAD",
            },
        )
        self.assertEqual(over_resp.status_code, 200)
        self.assertFalse(Payment.objects.filter(reference_number="P_BAD").exists())

        # Valid payment settles charge
        self.client.post(
            reverse("payment_add", args=[charge.pk]),
            {
                "person": self.resident.pk,
                "payment_date": d.isoformat(),
                "amount": "1000.00",
                "method": "Bank transfer",
                "reference_number": "P_OK",
            },
        )
        self.assertEqual(charge.outstanding_amount, Decimal("0.00"))

        # Publish announcement
        self.client.post(reverse("announcements"), {"title": "Elevator Check", "message": "Tomorrow at 10:00."})
        self.assertTrue(Announcement.objects.filter(title="Elevator Check").exists())

        # Resident submits request and manager updates status
        self.client.force_login(self.resident_user)
        self.client.post(
            reverse("request_submit", args=[self.unit_a12.pk]),
            {"subject": "Hall light", "description": "Flickering bulb"},
        )
        req = MaintenanceRequest.objects.get(subject="Hall light")

        self.client.force_login(self.manager_user)
        self.client.post(reverse("request_status", args=[req.pk]), {"status": MaintenanceRequest.RESOLVED})
        req.refresh_from_db()
        self.assertEqual(req.status, MaintenanceRequest.RESOLVED)

        # End current assignment today (remains active until end of day) and appoint successor from tomorrow
        self.client.post(reverse("assignment_end", args=[self.assignment.pk]), {"end_date": d.isoformat()})
        tomorrow = d + timedelta(days=1)
        resp = self.client.post(
            reverse("assignments"),
            {"person": self.other_resident.pk, "start_date": tomorrow.isoformat(), "end_date": ""},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.site.active_manager(d), self.manager)
        self.assertEqual(self.site.active_manager(tomorrow), self.other_resident)

    def test_seed_demo_command_matches_pdf_example(self):
        out = StringIO()
        call_command("seed_demo", reset=True, stdout=out)

        self.assertEqual(ResidentialSite.objects.count(), 1)
        self.assertEqual(Block.objects.count(), 3)
        self.assertEqual(Unit.objects.count(), 60)

        a12 = Unit.objects.get(block__block_label="A", unit_number=12)
        self.assertEqual(a12.floor_number, 3)

        nov_charge = DuesCharge.objects.get(unit=a12, billing_period=date(2026, 11, 1))
        self.assertEqual(nov_charge.amount, Decimal("1000.00"))
        self.assertEqual(nov_charge.paid_amount, Decimal("1000.00"))
        self.assertEqual(nov_charge.outstanding_amount, Decimal("0.00"))
        self.assertEqual(nov_charge.current_status, DuesCharge.SETTLED)
        self.assertEqual(list(nov_charge.payments.values_list("reference_number", flat=True)), ["P001", "P002"])

        self.assertTrue(MaintenanceRequest.objects.filter(unit=a12, subject="Leaking tap", status="Open").exists())
        self.assertTrue(Announcement.objects.filter(title="Water Maintenance").exists())

        # Debtors view as Deniz lists B-05 (1000) above C-03 (700)
        self.assertTrue(self.client.login(username="deniz", password="demo-pass-2026"))
        debtors_resp = self.client.get(reverse("debtors"))
        self.assertEqual(debtors_resp.status_code, 200)
        rows = debtors_resp.context["rows"]
        self.assertEqual([str(r["unit"]) for r in rows], ["B-05", "C-03"])
        self.assertEqual([r["total"] for r in rows], [Decimal("1000.00"), Decimal("700.00")])
