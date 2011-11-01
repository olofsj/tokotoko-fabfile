Tokotoko Fabfile
================

Tokotoko Fabfile contains [Fabric](http://www.fabfile.org) functions for
setting up and managing Django projects on Amazon EC2.

Features
--------

- Launching new EC2 instances
- Setting up Nginx, PostgreSQL and Gunicorn for running Django
- Optionally setting up Celery for background tasks
- Setting up and managing backups to Amazon S3

The django settings are read in from the Django settings file.

Requirements
------------

- Django
- Fabric
- Libcloud
- Git

