#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run tests for the Django LTI Tool PRovider
"""

import sys
from django.conf import settings
from django.core.management import execute_from_command_line

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    SITE_ID=1,
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django_lti_tool_provider'
    ],
    MIDDLEWARE_CLASSES=[
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    ROOT_URLCONF='django_lti_tool_provider.tests.urls',
    REDIRECT_AFTER_LTI='home',
    TEMPLATE_CONTEXT_PROCESSORS=(
        "django.contrib.auth.context_processors.auth"
    ),
    USE_TZ=True,
    SOUTH_TESTS_MIGRATE=True,
    LTI_CLIENT_KEY='lti_client_key',
    LTI_CLIENT_SECRET='lti_client_secret',
    SECRET_KEY='test_secret_key_not_need_to_look_like_actual_secret_key',
)

if __name__ == "__main__":
    args = sys.argv[1:]
    paths = [arg for arg in args if arg[0] != '-']
    if not paths:
        paths = ["django_lti_tool_provider/tests"]
    options = [arg for arg in args if arg not in paths]
    execute_from_command_line([sys.argv[0], "test"] + paths + options)