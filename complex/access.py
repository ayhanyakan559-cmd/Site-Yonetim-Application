"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Role helpers and access-control decorators (US01, US02).
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Person, ResidentialSite


def person_for(user):
    if not user.is_authenticated:
        return None
    try:
        return user.person
    except Person.DoesNotExist:
        return None


def managed_site_for(person):
    """The site the person actively manages (demo: one site per installation)."""
    if person is None:
        return None
    return person.managed_sites().first()


def manager_required(view):
    """Server-side guard: the user must be the active manager of a site. Passes `site` to the view."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        person = person_for(request.user)
        site = managed_site_for(person)
        if site is None:
            raise PermissionDenied("Manager access required.")
        request.person = person
        request.site = site
        return view(request, *args, **kwargs)

    return wrapper


def person_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        person = person_for(request.user)
        if person is None:
            raise PermissionDenied("No person record is linked to this account.")
        request.person = person
        return view(request, *args, **kwargs)

    return wrapper


def get_site_or_none():
    return ResidentialSite.objects.first()
