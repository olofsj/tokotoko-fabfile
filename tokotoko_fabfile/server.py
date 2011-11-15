#-*- coding:utf-8 -*-
import string
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, sed
from settings import *


@task
def bootstrap():
    """Initial setup of new server"""

    # Upgrade and install some needed packages
    with hide('stdout'):
        sudo('aptitude install -y update-notifier-common') # Shows if reboot needed
        sudo('add-apt-repository ppa:nginx/stable')
        sudo('add-apt-repository ppa:pitti/postgresql')
        sudo('aptitude update')
    sudo('aptitude full-upgrade -y')
    with hide('stdout'):
        sudo('aptitude install -y git')
    # Reboot if needed after upgrade
    if exists("/var/run/reboot-required"):
        reboot(40)

    # Install and set up PostgreSQL
    with hide('stdout'):
        sudo('aptitude install -y postgresql python-psycopg2')
    sed('/etc/postgresql/9.1/main/pg_hba.conf', 
            before='(local.*all.*all.*)peer',
            after='\\1md5',
            use_sudo=True)

    # Set up s3cmd
    print "Setting up s3cmd configuration."
    with hide('running', 'stdout'):
        run('echo "%s\n%s\n%s\n\n\n\ny\ny\n" | s3cmd --configure' %
                (EC2_ACCESS_ID, EC2_SECRET_KEY, S3CMD_ENC_PASS))


@task
def setup_project():
    """Initial setup of project on server"""

    # Set up log files for Gunicorn
    if USES_DJANGO:
        sudo('mkdir -p /var/log/gunicorn')
        sudo('touch /var/log/gunicorn/%s.log' % GUNICORN_SERVICE_NAME)
        sudo('chown www-data:adm /var/log/gunicorn')
        sudo('chown www-data:adm /var/log/gunicorn/%s.log' % GUNICORN_SERVICE_NAME)

    # Install and set up PIP and Virtualenv
    with hide('stdout'):
        sudo('aptitude install -y python-setuptools')
        sudo('easy_install pip')
        sudo('pip install virtualenv')
    if not exists("%s/env" % PROJECT_DIR):
        with cd(PROJECT_DIR):
            run('virtualenv env')
            run('echo "export DJANGO_SETTINGS=production" >> env/bin/activate')
            run('echo "export TOKOTOKO_FABFILE_PROJECT=%s/current" >> env/bin/activate' % PROJECT_DIR)

    # Set up Celery
    if USES_CELERY:
        setup_celery()

    # Set up database
    if USES_DJANGO:
        create_database()

    # Push local repo and update
    deploy()

    # Set up cron job for daily backups
    sudo('mkdir -p %s' % BACKUP_DIR)
    sudo('chmod a+rwx %s' % BACKUP_DIR)
    with hide('warnings'):
        with settings(warn_only=True):
            run('crontab -l > /tmp/crondump')
    cronjob = '00 19 * * * %s/current/cron.sh %s > %s/cron.log' % (PROJECT_DIR, os.path.join(PROJECT_DIR, 'env'), BACKUP_DIR)
    run('echo "%s" >> /tmp/crondump' % cronjob)
    run('crontab /tmp/crondump')


def setup_celery():
    """Set up log files and RabbitMQ for Celery"""
    sudo('mkdir -p /var/log/celery')
    sudo('chown www-data:adm /var/log/celery')
    sudo('mkdir -p /var/run/celery')
    sudo('chown www-data:adm /var/run/celery')
    with hide('stdout'):
        sudo('aptitude install -y rabbitmq-server')
    with settings(warn_only=True):
        sudo('rabbitmqctl add_user %s %s' % (django_settings.BROKER_USER,
            django_settings.BROKER_PASSWORD))
        sudo('rabbitmqctl add_vhost %s' % django_settings.BROKER_VHOST)
        sudo('rabbitmqctl set_permissions -p %s %s ".*" ".*" ".*"' %
                (django_settings.BROKER_VHOST, django_settings.BROKER_USER))


@task
def deploy():
    """Deploy code and reload services"""
    git_push_from_local()

    update_and_reload()


@task
def git_push_from_local():
    """Push local repo to remote machine"""
    if not exists("%s/repo" % PROJECT_DIR):
        # Set up bare Git repo to push to
        run('mkdir -p %s/repo' % PROJECT_DIR)
        with cd('%s/repo' % PROJECT_DIR):
            run('git init --bare')

    local('ssh-add %(key_filename)s' % env)
    local('git remote add ec2push ssh://ubuntu@%(host_string)s:22%(project_dir)s/repo' % env)
    with settings(warn_only=True):
        result = local('git push ec2push %(gitbranch)s' % env)
    local('git remote rm ec2push')
    if result.failed:
        abort("Git push failed.")


@task
def update_and_reload():
    """Update from pushed repo and reload services"""
    # Pull updates to checked out location
    if not exists("%s/current" % PROJECT_DIR):
        run('git clone -b %(gitbranch)s %(project_dir)s/repo current' % env)
    with cd('%(project_dir)s/current' % env):
        run('git pull')

    # Install requirements and run postinstall script
    with cd('%(project_dir)s/current' % env):
        sudo('aptitude install -y $(< requirements.packages)')
        run('../env/bin/pip install -r requirements.txt')
        sudo('cp -f -r config/* /')
        with prefix('source ~/env/bin/activate'):
            run('../current/postinstall')
        with hide('running', 'stdout'):
            output = run('ls config/etc/nginx/sites-available/')
        sites = output.split()

    # Activate all nginx sites
    for site in sites:
        if not exists("/etc/nginx/sites-enabled/%s" % site):
            sudo('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (site, site))

    reload()


@task
def system_upgrade():
    """Upgrade system (reboot if needed)"""
    # Upgrade and install some needed packages
    with hide('stdout'):
        sudo('aptitude update')
    sudo('aptitude full-upgrade -y')
    # Reboot if needed after upgrade
    if exists("/var/run/reboot-required") and confirm("Reboot required. Reboot now?"):
        reboot(40)


@task
def reload():
    """Restart services"""
    with hide('warnings'):
        with settings(warn_only=True):
            if USES_CELERY:
                sudo('service celeryd stop')
            if USES_DJANGO:
                sudo('service %s stop' % GUNICORN_SERVICE_NAME)
                sudo('service %s start' % GUNICORN_SERVICE_NAME)
            sudo('service nginx start')
            sudo('service nginx reload')
            if USES_CELERY:
                sudo('service celeryd start')


@task
def create_database():
    """Creates user and database from Django settings"""
    db_user = django_settings.DATABASES['default']['USER']
    db_pass = django_settings.DATABASES['default']['PASSWORD']
    db_name = django_settings.DATABASES['default']['NAME']
    with settings(warn_only=True):
        run('sudo -u postgres psql -c "CREATE USER %s WITH NOCREATEDB NOCREATEUSER \
               ENCRYPTED PASSWORD E\'%s\'"' % (db_user, db_pass))
        run('sudo -u postgres psql -c "CREATE DATABASE %s WITH OWNER %s"' %
                ( db_name, db_user))

