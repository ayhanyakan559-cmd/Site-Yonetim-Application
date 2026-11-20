"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Template context processor exposing active manager and resident roles.
"""

from .access import managed_site_for, person_for


def roles(request):
    person = person_for(getattr(request, "user", None)) if hasattr(request, "user") else None
    if person is None:
        return {"current_person": None, "is_manager": False, "is_resident": False}
    return {
        "current_person": person,
        "is_manager": managed_site_for(person) is not None,
        "is_resident": person.active_residencies().exists(),
    }
