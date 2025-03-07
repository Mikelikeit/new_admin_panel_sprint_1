"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
from pathlib import Path
from dotenv import load_dotenv
from split_settings.tools import include

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOCALE_PATHS = ['movies/locale']

include('components/security.py', 'components/application.py', 'components/password_validation.py',
        'components/database.py', 'components/internationalization.py', 'components/static.py',
        'components/default_pk_field_type.py')
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
