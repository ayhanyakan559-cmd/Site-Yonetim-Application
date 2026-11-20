"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Django forms for site structure, residencies, charges, payments, requests, and announcements.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

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

DATE = forms.DateInput(attrs={"type": "date"})


class SiteForm(forms.ModelForm):
    class Meta:
        model = ResidentialSite
        fields = ["site_name", "address"]


class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ["block_label"]


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["block", "unit_number", "floor_number"]

    def __init__(self, *args, site=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["block"].queryset = Block.objects.filter(site=site)


class PersonForm(forms.ModelForm):
    username = forms.CharField(required=False, help_text="Optional: create a login for this person.")
    password = forms.CharField(required=False, widget=forms.PasswordInput)

    class Meta:
        model = Person
        fields = ["full_name", "telephone", "email"]

    def clean(self):
        data = super().clean()
        username, password = data.get("username"), data.get("password")
        if username or password:
            if not (username and password):
                raise forms.ValidationError("Provide both username and password, or neither.")
            if get_user_model().objects.filter(username=username).exists():
                self.add_error("username", "This username is taken.")
            else:
                validate_password(password)
        return data

    def save(self, commit=True):
        person = super().save(commit=False)
        username = self.cleaned_data.get("username")
        if username:
            person.user = get_user_model().objects.create_user(
                username=username, password=self.cleaned_data["password"], email=person.email
            )
        if commit:
            person.save()
        return person


class ResidencyForm(forms.ModelForm):
    class Meta:
        model = Residency
        fields = ["person", "start_date", "end_date"]
        widgets = {"start_date": DATE, "end_date": DATE}


class EndPeriodForm(forms.Form):
    end_date = forms.DateField(widget=DATE)


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = ManagementAssignment
        fields = ["person", "start_date", "end_date"]
        widgets = {"start_date": DATE, "end_date": DATE}


class ChargeForm(forms.ModelForm):
    billing_period = forms.DateField(
        input_formats=["%Y-%m", "%Y-%m-%d"], widget=forms.DateInput(attrs={"type": "month"}, format="%Y-%m"),
        help_text="Month and year",
    )

    class Meta:
        model = DuesCharge
        fields = ["billing_period", "amount", "due_date"]
        widgets = {"due_date": DATE}


class PaymentForm(forms.Form):
    person = forms.ModelChoiceField(queryset=Person.objects.all(), label="Paying person")
    payment_date = forms.DateField(widget=DATE)
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    method = forms.ChoiceField(choices=Payment.METHOD_CHOICES)
    reference_number = forms.CharField(max_length=40)


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ["subject", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=MaintenanceRequest.STATUS_CHOICES)


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}
