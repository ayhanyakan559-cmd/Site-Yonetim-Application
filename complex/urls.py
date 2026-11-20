from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # manager
    path("manage/", views.overview, name="overview"),
    path("manage/site/", views.site_edit, name="site_edit"),
    path("manage/blocks/add/", views.block_add, name="block_add"),
    path("manage/units/add/", views.unit_add, name="unit_add"),
    path("manage/units/<int:pk>/", views.unit_detail, name="unit_detail"),
    path("manage/units/<int:pk>/residencies/add/", views.residency_add, name="residency_add"),
    path("manage/residencies/<int:pk>/end/", views.residency_end, name="residency_end"),
    path("manage/units/<int:pk>/charges/add/", views.charge_add, name="charge_add"),
    path("manage/charges/<int:pk>/pay/", views.payment_add, name="payment_add"),
    path("manage/people/", views.people, name="people"),
    path("manage/assignments/", views.assignments, name="assignments"),
    path("manage/assignments/<int:pk>/end/", views.assignment_end, name="assignment_end"),
    path("manage/debtors/", views.debtors, name="debtors"),
    path("manage/requests/", views.requests_list, name="requests"),
    path("manage/requests/<int:pk>/status/", views.request_status, name="request_status"),
    # shared
    path("announcements/", views.announcements, name="announcements"),
    # resident
    path("me/", views.my_home, name="my_home"),
    path("me/units/<int:unit_pk>/requests/", views.request_submit, name="request_submit"),
]
