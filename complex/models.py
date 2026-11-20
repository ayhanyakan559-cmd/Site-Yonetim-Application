"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Domain model for Residential Complex Management.
    Each class maps 1:1 to a concept in the conceptual UML model (PDF section 4).
    Paragraph references (D01-D09) and business rules (BR01-BR14) point to the
    project documents.
"""

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


def today() -> date:
    return timezone.localdate()


def _overlaps(qs, start, end):
    """Filter qs (records with start_date/end_date) to those overlapping [start, end]."""
    qs = qs.filter(Q(end_date__isnull=True) | Q(end_date__gte=start))
    if end is not None:
        qs = qs.filter(start_date__lte=end)
    return qs


def active_q(on: date) -> Q:
    return Q(start_date__lte=on) & (Q(end_date__isnull=True) | Q(end_date__gte=on))


class DatedPeriod(models.Model):
    """Shared startDate / optional endDate behaviour (D04, D05, BR05)."""

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        abstract = True

    def state(self, on: date | None = None) -> str:
        on = on or today()
        if on < self.start_date:
            return "Upcoming"
        if self.end_date is not None and on > self.end_date:
            return "Ended"
        return "Active"

    @property
    def current_state(self) -> str:
        return self.state()

    def is_active_on(self, on: date | None = None) -> bool:
        return self.state(on) == "Active"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:  # BR05
            raise ValidationError({"end_date": "End date cannot precede start date."})


# --- D01 / D02 -------------------------------------------------------------


class ResidentialSite(models.Model):
    site_name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.site_name

    def active_assignment(self, on: date | None = None):
        return self.management_assignments.filter(active_q(on or today())).first()

    def active_manager(self, on: date | None = None):
        assignment = self.active_assignment(on)
        return assignment.person if assignment else None


class Block(models.Model):
    site = models.ForeignKey(ResidentialSite, on_delete=models.PROTECT, related_name="blocks")
    block_label = models.CharField(max_length=10)

    class Meta:
        ordering = ["block_label"]
        constraints = [  # BR08
            models.UniqueConstraint(fields=["site", "block_label"], name="unique_block_label_per_site"),
        ]

    def __str__(self):
        return f"Block {self.block_label}"

    def clean(self):
        super().clean()
        if self.site_id and self.block_label:  # BR08 (checked here too because forms exclude `site`)
            self.block_label = self.block_label.strip().upper()
            if Block.objects.filter(site_id=self.site_id, block_label=self.block_label).exclude(pk=self.pk).exists():
                raise ValidationError({"block_label": "This block label already exists in the site."})


class Unit(models.Model):
    block = models.ForeignKey(Block, on_delete=models.PROTECT, related_name="units")
    unit_number = models.PositiveIntegerField()
    floor_number = models.IntegerField()

    class Meta:
        ordering = ["block__block_label", "unit_number"]
        constraints = [  # BR08
            models.UniqueConstraint(fields=["block", "unit_number"], name="unique_unit_number_per_block"),
        ]

    def __str__(self):
        return f"{self.block.block_label}-{self.unit_number:02d}"

    def clean(self):
        super().clean()
        if self.block_id and self.unit_number is not None:  # BR08
            if Unit.objects.filter(block_id=self.block_id, unit_number=self.unit_number).exclude(pk=self.pk).exists():
                raise ValidationError({"unit_number": "This unit number already exists in the block."})

    @property
    def site(self):
        return self.block.site

    def active_residencies(self, on: date | None = None):
        return self.residencies.filter(active_q(on or today())).select_related("person")

    def is_occupied(self, on: date | None = None) -> bool:
        return self.active_residencies(on).exists()


# --- D03 ---------------------------------------------------------------------


class Person(models.Model):
    full_name = models.CharField(max_length=120)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    # Optional login account. Roles come from Residency / ManagementAssignment, not from the account.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="person"
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def active_residencies(self, on: date | None = None):
        return self.residencies.filter(active_q(on or today())).select_related("unit__block__site")

    def resides_in(self, unit, on: date | None = None) -> bool:
        return self.residencies.filter(active_q(on or today()), unit=unit).exists()

    def managed_sites(self, on: date | None = None):
        return ResidentialSite.objects.filter(
            management_assignments__in=self.management_assignments.filter(active_q(on or today()))
        ).distinct()

    def manages(self, site, on: date | None = None) -> bool:
        return self.management_assignments.filter(active_q(on or today()), site=site).exists()


# --- D04 ---------------------------------------------------------------------


class Residency(DatedPeriod):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="residencies")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="residencies")

    class Meta:
        ordering = ["-start_date"]
        verbose_name_plural = "residencies"
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=models.F("start_date")),
                name="residency_end_not_before_start",
            ),
        ]

    def __str__(self):
        return f"{self.person} in {self.unit}"

    def clean(self):
        super().clean()
        if self.person_id and self.unit_id and self.start_date:  # BR06
            clash = _overlaps(
                Residency.objects.filter(person_id=self.person_id, unit_id=self.unit_id).exclude(pk=self.pk),
                self.start_date,
                self.end_date,
            )
            if clash.exists():
                raise ValidationError("This person already has an overlapping residency in this unit.")


# --- D05 ---------------------------------------------------------------------


class ManagementAssignment(DatedPeriod):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="management_assignments")
    site = models.ForeignKey(ResidentialSite, on_delete=models.PROTECT, related_name="management_assignments")

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=models.F("start_date")),
                name="assignment_end_not_before_start",
            ),
        ]

    def __str__(self):
        return f"{self.person} manages {self.site}"

    def clean(self):
        super().clean()
        if self.site_id and self.start_date:  # BR13: one active manager at a time
            clash = _overlaps(
                ManagementAssignment.objects.filter(site_id=self.site_id).exclude(pk=self.pk),
                self.start_date,
                self.end_date,
            )
            if clash.exists():
                raise ValidationError(
                    "Another management assignment overlaps this period. End the current assignment first."
                )


# --- D06 / D07 ---------------------------------------------------------------


class DuesCharge(models.Model):
    UNPAID, PARTIAL, SETTLED, OVERDUE = "Unpaid", "Partially paid", "Settled", "Overdue"

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="dues_charges")
    billing_period = models.DateField(help_text="Stored as the first day of the billed month.")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()

    class Meta:
        ordering = ["-billing_period", "unit__block__block_label", "unit__unit_number"]
        constraints = [
            models.UniqueConstraint(fields=["unit", "billing_period"], name="one_charge_per_unit_period"),  # BR09
            models.CheckConstraint(condition=Q(amount__gt=0), name="charge_amount_positive"),  # BR01
        ]

    def __str__(self):
        return f"{self.unit} {self.period_label}"

    def save(self, *args, **kwargs):
        if self.billing_period:
            self.billing_period = self.billing_period.replace(day=1)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.billing_period:
            self.billing_period = self.billing_period.replace(day=1)
        if self.amount is not None and self.amount <= 0:  # BR01
            raise ValidationError({"amount": "Amount must be positive."})
        if self.unit_id and self.billing_period:  # BR09
            dup = DuesCharge.objects.filter(unit_id=self.unit_id, billing_period=self.billing_period)
            if dup.exclude(pk=self.pk).exists():
                raise ValidationError({"billing_period": "This unit already has a charge for that billing period."})

    @property
    def period_label(self) -> str:
        return self.billing_period.strftime("%B %Y")

    @property
    def paid_amount(self) -> Decimal:
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def outstanding_amount(self) -> Decimal:  # BR03 (derived, never entered)
        return self.amount - self.paid_amount

    def status(self, on: date | None = None) -> str:  # BR04
        on = on or today()
        outstanding = self.outstanding_amount
        if outstanding <= 0:
            return self.SETTLED
        if on > self.due_date:
            return self.OVERDUE
        return self.PARTIAL if outstanding < self.amount else self.UNPAID

    @property
    def current_status(self) -> str:
        return self.status()


class Payment(models.Model):
    METHOD_CHOICES = [
        ("Bank transfer", "Bank transfer"),
        ("Cash", "Cash"),
        ("Credit card", "Credit card"),
    ]

    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="payments")
    charge = models.ForeignKey(DuesCharge, on_delete=models.PROTECT, related_name="payments")  # BR14
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=30, choices=METHOD_CHOICES)
    reference_number = models.CharField(max_length=40)

    class Meta:
        ordering = ["payment_date", "pk"]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),  # BR01
        ]

    def __str__(self):
        return f"{self.reference_number} – TRY {self.amount}"

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:  # BR01
            raise ValidationError({"amount": "Payment amount must be positive."})
        if self.charge_id and self.amount is not None:  # BR02
            already_paid = (
                self.charge.payments.exclude(pk=self.pk).aggregate(total=Sum("amount"))["total"] or Decimal("0")
            )
            remaining = self.charge.amount - already_paid
            if self.amount > remaining:
                raise ValidationError(
                    {"amount": f"Payment of TRY {self.amount:,.2f} exceeds the outstanding amount of TRY {remaining:,.2f}."}
                )


# --- D08 ---------------------------------------------------------------------


class MaintenanceRequest(models.Model):
    OPEN, IN_PROGRESS, RESOLVED = "Open", "In Progress", "Resolved"
    STATUS_CHOICES = [(OPEN, OPEN), (IN_PROGRESS, IN_PROGRESS), (RESOLVED, RESOLVED)]  # BR11

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="maintenance_requests")
    submitted_by = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="maintenance_requests")
    subject = models.CharField(max_length=150)
    description = models.TextField()
    submission_date = models.DateField(default=today)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)

    class Meta:
        ordering = ["-submission_date", "-pk"]

    def __str__(self):
        return f"{self.subject} ({self.unit})"

    def clean(self):
        super().clean()
        if self.submitted_by_id and self.unit_id and self.submission_date:  # BR10
            if not self.submitted_by.resides_in(self.unit, self.submission_date):
                raise ValidationError("Only a person with an active residency in this unit can submit a request.")


# --- D09 ---------------------------------------------------------------------


class Announcement(models.Model):
    site = models.ForeignKey(ResidentialSite, on_delete=models.PROTECT, related_name="announcements")
    author = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="announcements")
    title = models.CharField(max_length=150)
    message = models.TextField()
    publication_date = models.DateField(default=today)

    class Meta:
        ordering = ["-publication_date", "-pk"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.author_id and self.site_id and self.publication_date:  # BR12
            if not self.author.manages(self.site, self.publication_date):
                raise ValidationError("Only the site's active manager can publish announcements.")
