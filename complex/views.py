from collections import OrderedDict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import services
from .access import manager_required, managed_site_for, person_for, person_required
from .forms import (
    AnnouncementForm,
    AssignmentForm,
    BlockForm,
    ChargeForm,
    EndPeriodForm,
    MaintenanceRequestForm,
    PaymentForm,
    PersonForm,
    ResidencyForm,
    SiteForm,
    StatusForm,
    UnitForm,
)
from .models import (
    Announcement,
    Block,
    DuesCharge,
    MaintenanceRequest,
    ManagementAssignment,
    Person,
    Residency,
    ResidentialSite,
    Unit,
    active_q,
    today,
)


def _flash_validation_error(request, exc: ValidationError):
    for msg in exc.messages:
        messages.error(request, msg)


@login_required
def home(request):
    person = person_for(request.user)
    if managed_site_for(person):
        return redirect("overview")
    if person and person.active_residencies().exists():
        return redirect("my_home")
    return render(request, "complex/no_role.html", {"has_site": ResidentialSite.objects.exists()})


# --------------------------------------------------------------------------- manager: structure


@manager_required
def overview(request):  # US03, US04, US05, US06
    site = request.site
    on = today()
    active_res = Residency.objects.filter(active_q(on)).select_related("person")
    blocks = site.blocks.prefetch_related(
        Prefetch("units", queryset=Unit.objects.prefetch_related(Prefetch("residencies", queryset=active_res,
                                                                          to_attr="current")))
    )
    total_units = Unit.objects.filter(block__site=site).count()
    occupied = Unit.objects.filter(block__site=site, residencies__in=active_res).distinct().count()
    overdue_count = sum(
        1 for c in DuesCharge.objects.filter(unit__block__site=site, due_date__lt=on) if c.outstanding_amount > 0
    )
    context = {
        "site": site,
        "blocks": blocks,
        "total_units": total_units,
        "occupied": occupied,
        "vacant": total_units - occupied,
        "overdue_count": overdue_count,
        "open_requests": MaintenanceRequest.objects.filter(unit__block__site=site).exclude(
            status=MaintenanceRequest.RESOLVED).count(),
        "site_form": SiteForm(instance=site),
        "block_form": BlockForm(),
        "unit_form": UnitForm(site=site),
    }
    return render(request, "complex/overview.html", context)


@manager_required
@require_POST
def site_edit(request):
    form = SiteForm(request.POST, instance=request.site)
    if form.is_valid():
        form.save()
        messages.success(request, "Site details saved.")
    else:
        messages.error(request, "Site name and address are required.")
    return redirect("overview")


@manager_required
@require_POST
def block_add(request):
    form = BlockForm(request.POST, instance=Block(site=request.site))
    if form.is_valid():
        form.save()
        messages.success(request, f"Block {form.instance.block_label} added.")
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect("overview")


@manager_required
@require_POST
def unit_add(request):
    form = UnitForm(request.POST, site=request.site)
    if form.is_valid():
        unit = form.save()
        messages.success(request, f"Unit {unit} added.")
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect("overview")


def _manager_unit(request, pk):
    return get_object_or_404(Unit.objects.select_related("block__site"), pk=pk, block__site=request.site)


@manager_required
def unit_detail(request, pk):  # US06, US10-US13, US15, US16
    unit = _manager_unit(request, pk)
    charges = unit.dues_charges.prefetch_related("payments__person")
    context = {
        "unit": unit,
        "active_residencies": unit.active_residencies(),
        "all_residencies": unit.residencies.select_related("person"),
        "charges": charges,
        "requests": unit.maintenance_requests.select_related("submitted_by"),
        "residency_form": ResidencyForm(initial={"start_date": today()}),
        "charge_form": ChargeForm(),
        "end_form": EndPeriodForm(initial={"end_date": today()}),
    }
    return render(request, "complex/unit_detail.html", context)


@manager_required
@require_POST
def residency_add(request, pk):  # US10
    unit = _manager_unit(request, pk)
    form = ResidencyForm(request.POST, instance=Residency(unit=unit))
    if form.is_valid():
        form.save()
        messages.success(request, f"Residency recorded for {form.instance.person} in {unit}.")
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect("unit_detail", pk=unit.pk)


@manager_required
@require_POST
def residency_end(request, pk):  # US11
    residency = get_object_or_404(Residency, pk=pk, unit__block__site=request.site)
    form = EndPeriodForm(request.POST)
    if form.is_valid():
        residency.end_date = form.cleaned_data["end_date"]
        try:
            residency.full_clean()
            residency.save()
            messages.success(request, f"Residency of {residency.person} ended on {residency.end_date}.")
        except ValidationError as exc:
            _flash_validation_error(request, exc)
    return redirect("unit_detail", pk=residency.unit_id)


@manager_required
@require_POST
def charge_add(request, pk):  # US13
    unit = _manager_unit(request, pk)
    form = ChargeForm(request.POST, instance=DuesCharge(unit=unit))
    if form.is_valid():
        form.save()
        messages.success(request, f"Charge for {form.instance.period_label} created.")
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect("unit_detail", pk=unit.pk)


@manager_required
def payment_add(request, pk):  # US16
    charge = get_object_or_404(DuesCharge.objects.select_related("unit__block__site"), pk=pk,
                               unit__block__site=request.site)
    if charge.outstanding_amount <= 0:
        messages.info(request, "This charge is already settled.")
        return redirect("unit_detail", pk=charge.unit_id)
    residents = Person.objects.filter(residencies__unit=charge.unit).distinct()
    initial = {"payment_date": today(), "amount": charge.outstanding_amount}
    if residents.count() == 1:
        initial["person"] = residents.first()
    form = PaymentForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.record_payment(charge=charge, **form.cleaned_data)
            messages.success(request, f"Payment {form.cleaned_data['reference_number']} recorded.")
            return redirect("unit_detail", pk=charge.unit_id)
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, errs in exc.message_dict.items():
                    for e in errs:
                        form.add_error(field if field in form.fields else None, e)
            else:
                form.add_error(None, exc)
    return render(request, "complex/payment_form.html", {"charge": charge, "form": form})


# --------------------------------------------------------------------------- manager: people & roles


@manager_required
def people(request):  # US07
    form = PersonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        person = form.save()
        messages.success(request, f"{person} registered.")
        return redirect("people")
    on = today()
    persons = Person.objects.select_related("user").prefetch_related(
        "residencies__unit__block", "management_assignments"
    )
    rows = []
    for p in persons:
        rows.append({
            "person": p,
            "units": [r.unit for r in p.residencies.all() if r.is_active_on(on)],
            "is_manager": any(a.is_active_on(on) and a.site_id == request.site.pk for a in p.management_assignments.all()),
        })
    return render(request, "complex/people.html", {"rows": rows, "form": form})


@manager_required
def assignments(request):  # US08
    site = request.site
    form = AssignmentForm(request.POST or None, instance=ManagementAssignment(site=site),
                          initial={"start_date": today()})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Management assignment recorded.")
        return redirect("assignments")
    return render(request, "complex/assignments.html", {
        "assignments": site.management_assignments.select_related("person"),
        "form": form,
        "end_form": EndPeriodForm(initial={"end_date": today()}),
    })


@manager_required
@require_POST
def assignment_end(request, pk):
    assignment = get_object_or_404(ManagementAssignment, pk=pk, site=request.site)
    form = EndPeriodForm(request.POST)
    if form.is_valid():
        assignment.end_date = form.cleaned_data["end_date"]
        try:
            assignment.full_clean()
            assignment.save()
            messages.success(request, f"Assignment of {assignment.person} ended on {assignment.end_date}.")
        except ValidationError as exc:
            _flash_validation_error(request, exc)
    return redirect("assignments")


# --------------------------------------------------------------------------- manager: finance & requests


@manager_required
def debtors(request):  # US18
    site = request.site
    on = today()
    block_filter = request.GET.get("block", "")
    period_filter = request.GET.get("period", "")
    charges = DuesCharge.objects.filter(unit__block__site=site, due_date__lt=on).select_related("unit__block")
    if block_filter:
        charges = charges.filter(unit__block__block_label=block_filter)
    if period_filter:
        try:
            y, m = (int(x) for x in period_filter.split("-"))
            charges = charges.filter(billing_period__year=y, billing_period__month=m)
        except ValueError:
            messages.error(request, "Invalid period filter.")
    per_unit = OrderedDict()
    for c in charges.prefetch_related("payments"):
        out = c.outstanding_amount
        if out <= 0:
            continue
        entry = per_unit.setdefault(c.unit_id, {"unit": c.unit, "charges": [], "total": Decimal("0")})
        entry["charges"].append(c)
        entry["total"] += out
    rows = sorted(per_unit.values(), key=lambda r: r["total"], reverse=True)
    return render(request, "complex/debtors.html", {
        "rows": rows,
        "grand_total": sum((r["total"] for r in rows), Decimal("0")),
        "blocks": site.blocks.all(),
        "block_filter": block_filter,
        "period_filter": period_filter,
    })


@manager_required
def requests_list(request):  # US21
    status = request.GET.get("status", "")
    block = request.GET.get("block", "")
    qs = MaintenanceRequest.objects.filter(unit__block__site=request.site).select_related("unit__block",
                                                                                       "submitted_by")
    if status:
        qs = qs.filter(status=status)
    if block:
        qs = qs.filter(unit__block__block_label=block)
    return render(request, "complex/requests.html", {
        "requests": qs,
        "statuses": [s for s, _ in MaintenanceRequest.STATUS_CHOICES],
        "blocks": request.site.blocks.all(),
        "status_filter": status,
        "block_filter": block,
    })


@manager_required
@require_POST
def request_status(request, pk):  # US22
    req = get_object_or_404(MaintenanceRequest, pk=pk, unit__block__site=request.site)
    form = StatusForm(request.POST)
    if form.is_valid():
        try:
            services.update_request_status(request_obj=req, actor=request.person,
                                           new_status=form.cleaned_data["status"])
            messages.success(request, f"“{req.subject}” is now {req.status}.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    else:
        messages.error(request, "Invalid status.")
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                    require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("requests")


# --------------------------------------------------------------------------- announcements (both roles)


@person_required
def announcements(request):  # US24, US25
    person = request.person
    site = managed_site_for(person)
    is_manager = site is not None
    if not is_manager:
        sites = {r.unit.site for r in person.active_residencies()}
        if not sites:
            raise PermissionDenied("Announcements are available to current residents and the active manager.")
        site = next(iter(sites))
    form = AnnouncementForm(request.POST or None) if is_manager else None
    if request.method == "POST":
        if not is_manager:
            raise PermissionDenied("Only the site's active manager can publish announcements.")
        if form.is_valid():
            try:
                services.publish_announcement(site=site, author=person, **form.cleaned_data)
                messages.success(request, "Announcement published.")
                return redirect("announcements")
            except ValidationError as exc:
                _flash_validation_error(request, exc)
    return render(request, "complex/announcements.html", {
        "site": site,
        "announcements": Announcement.objects.filter(site=site).select_related("author"),
        "form": form,
    })


# --------------------------------------------------------------------------- resident


@person_required
def my_home(request):  # US17, US23
    person = request.person
    residencies = person.active_residencies()
    if not residencies:
        raise PermissionDenied("You have no active residency.")
    units = []
    for r in residencies:
        unit = r.unit
        units.append({
            "unit": unit,
            "since": r.start_date,
            "charges": unit.dues_charges.prefetch_related("payments__person"),
            "outstanding": sum((c.outstanding_amount for c in unit.dues_charges.all()), Decimal("0")),
        })
    return render(request, "complex/my_home.html", {
        "units": units,
        "my_requests": person.maintenance_requests.select_related("unit__block"),
        "request_form": MaintenanceRequestForm(),
        "latest_announcements": Announcement.objects.filter(
            site__in={u["unit"].site for u in units}).select_related("author")[:3],
    })


@person_required
@require_POST
def request_submit(request, unit_pk):  # US20
    unit = get_object_or_404(Unit, pk=unit_pk)
    if not request.person.resides_in(unit):  # BR10, also prevents submitting for another unit (IDOR)
        raise PermissionDenied("You can only report problems in a unit you currently live in.")
    form = MaintenanceRequestForm(request.POST)
    if form.is_valid():
        try:
            services.submit_request(unit=unit, person=request.person, **form.cleaned_data)
            messages.success(request, "Maintenance request submitted.")
        except ValidationError as exc:
            _flash_validation_error(request, exc)
    else:
        messages.error(request, "Subject and description are required.")
    return redirect("my_home")
