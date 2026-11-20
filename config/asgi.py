"""
Name(s) Surname(s) : Ayhan Yakan, Mustafa Ege Türker, Nazife Kaya
Student No(s)#     : 241805017, 241805034, 241805082
General Comments   : ASGI config for config project. Exposes the ASGI callable as ``application``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
