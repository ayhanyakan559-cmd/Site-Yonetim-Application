"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : Root URL configuration wiring admin, login/logout, and complex routes.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="complex/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("complex.urls")),
]
