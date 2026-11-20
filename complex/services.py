"""Use-case operations that enforce business rules across several objects."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Announcement, DuesCharge, MaintenanceRequest, Payment, Person, today


@transaction.atomic
def record_payment(*, charge: DuesCharge, person: Person, amount: Decimal, payment_date, method, reference_number):
    """Record a confirmed payment toward exactly one charge (D07, BR01, BR02, BR14)."""
    # Lock the charge row (no-op on SQLite, effective on server databases) so concurrent payments
    # cannot both pass the outstanding check.
    charge = DuesCharge.objects.select_for_update().get(pk=charge.pk)
    amount = Decimal(amount)
    if amount <= 0:
        raise ValidationError({"amount": "Payment amount must be positive."})
    outstanding = charge.outstanding_amount
    if amount > outstanding:
        raise ValidationError(
            {"amount": f"Payment of TRY {amount:,.2f} exceeds the outstanding amount of TRY {outstanding:,.2f}."}
        )
    payment = Payment(
        charge=charge,
        person=person,
        amount=amount,
        payment_date=payment_date,
        method=method,
        reference_number=reference_number,
    )
    payment.full_clean()
    payment.save()
    return payment


def update_request_status(*, request_obj: MaintenanceRequest, actor: Person, new_status: str):
    """Only the site's active manager may change status, and only to a permitted value (D08, BR11)."""
    if not actor.manages(request_obj.unit.site):
        raise PermissionDenied("Only the site's active manager can update request status.")
    if new_status not in dict(MaintenanceRequest.STATUS_CHOICES):
        raise ValidationError({"status": "Invalid status."})
    request_obj.status = new_status
    request_obj.save(update_fields=["status"])
    return request_obj


def submit_request(*, unit, person: Person, subject: str, description: str):
    req = MaintenanceRequest(unit=unit, submitted_by=person, subject=subject, description=description,
                             submission_date=today())
    req.full_clean()  # BR10
    req.save()
    return req


def publish_announcement(*, site, author: Person, title: str, message: str):
    ann = Announcement(site=site, author=author, title=title, message=message, publication_date=today())
    ann.full_clean()  # BR12
    ann.save()
    return ann
