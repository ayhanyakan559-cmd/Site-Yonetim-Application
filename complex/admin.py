"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Django Admin registrations for the 10 residential complex domain models.
"""

from django.contrib import admin

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
)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(DuesCharge)
class DuesChargeAdmin(admin.ModelAdmin):
    list_display = ("unit", "billing_period", "amount", "due_date", "outstanding_amount", "current_status")
    list_filter = ("billing_period",)
    inlines = [PaymentInline]


@admin.register(Residency)
class ResidencyAdmin(admin.ModelAdmin):
    list_display = ("person", "unit", "start_date", "end_date")


@admin.register(ManagementAssignment)
class ManagementAssignmentAdmin(admin.ModelAdmin):
    list_display = ("person", "site", "start_date", "end_date")


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("subject", "unit", "submitted_by", "submission_date", "status")
    list_filter = ("status",)


admin.site.register([ResidentialSite, Block, Unit, Person, Payment, Announcement])
