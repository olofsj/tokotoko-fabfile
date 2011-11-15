#-*- coding:utf-8 -*-
import os
import sys
from fabric.api import *
from fabric.contrib import django
from libcloud.types import Provider
import libcloud.security

# This file contains module wide settings that you need to override for your
# project

PROJECT_NAME = 'your-project-name'

# Amazon EC2 connection settings
EC2_ACCESS_ID = 'your-ec2-access-id'
EC2_SECRET_KEY = 'your-ec2-secret-key'
EC2_PROVIDER = Provider.EC2_AP_NORTHEAST
S3CMD_ENC_PASS = 'choose-a-random-password'
S3_BUCKET_ROOT = 's3://example.com'

# Amazon EC2 AMI settings
EC2_KEYNAME = "your-keyname"
EC2_AMI_NAME = "ami-dab812db"
EC2_INSTANCE_SIZE = "t1.micro"
EC2_SECURITY_GROUP = "web"

# Libcloud settings
libcloud.security.VERIFY_SSL_CERT = True
libcloud.security.CA_CERTS_PATH.append(os.path.join(os.getenv('HOME'),
".ec2/cert-XXXX.pem"))

# Various settings
env.hosts = []
env.user = 'ubuntu'
env.key_filename = os.path.join(os.getenv('HOME'), '.ec2', EC2_KEYNAME + '.pem')
env.gitbranch = 'master'
env.psql_user_password = 'your-password' # FIXME: Handle this better?

# Backup settings
BACKUP_DIR = "/var/backups/your-domain"
DIRS_TO_BACKUP = []

# Gunicorn service name
GUNICORN_SERVICE_NAME = 'your-service'

# Django project settings
django.settings_module('djangosite.settings')
os.environ['DJANGO_SETTINGS'] = 'production'
try:
    from django.conf import settings as django_settings
    DIRS_TO_BACKUP.append(django_settings.MEDIA_ROOT)
    USES_CELERY = hasattr(django_settings, 'BROKER_USER')
    USES_DJANGO = True
except:
    USES_DJANGO = False
    USES_CELERY = False

# Override with project settings if found
try:
    from fabfile_settings import *
except ImportError:
    pass

