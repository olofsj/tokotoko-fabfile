#-*- coding:utf-8 -*-
import os
import datetime
from time import gmtime, strftime
from fabric.api import *
from fabric.contrib.files import exists
from settings import *

env.backupfiles = []

@task
def backup_local_folders():
    """Backup all folders to local directory"""

    for location in DIRS_TO_BACKUP:
        # Construct filename for backed up content
        timestamp = strftime("%Y-%m-%d", gmtime())
        dirname, name = os.path.split(location.rstrip('/'))
        backupname = name + '_' + timestamp

        print "Backing up %s..." % location

        # Do the backup by tar'ing the directory/file
        backupfile = '%s/%s.tar.gz' % (BACKUP_DIR, backupname)
        with hide('running', 'stdout'):
            local('cd %s && tar pzcf %s %s' % (dirname, backupfile, name))

        # Keep track of all created files
        env.backupfiles.append(backupfile)


@task
def backup_postgresql():
    """Backup PostgreSQL database to local directory"""

    # Construct filename for backed up content
    timestamp = strftime("%Y-%m-%d", gmtime())
    backupfile = '%s/pgdump_%s.gz' % (BACKUP_DIR, timestamp)
    db_name = django_settings.DATABASES['default']['NAME']

    print "Backing up PostgreSQL db %s..." % db_name
    with hide('running', 'stdout'):
        local('sudo -u postgres pg_dump %s | gzip > %s' % 
                (db_name, backupfile))

    # Keep track of all created files
    env.backupfiles.append(backupfile)


@task
def backup_all():
    """Backup everything to local directory"""

    backup_local_folders()

    backup_postgresql()


@task
def upload_to_s3():
    """Copy all backed up files to Amazon S3"""
    timestamp = strftime("%Y-%m-%d", gmtime())
    bucket = S3_BUCKET_ROOT + '-backup-' + timestamp
    local('s3cmd mb %s' % bucket)
    for localfile in env.backupfiles:
        local('s3cmd put %s %s' % (localfile, bucket))
    env.backupfiles = []


@task
def full_backup():
    """Do a full backup and upload to Amazon S3"""
    backup_all()

    upload_to_s3()

def get_s3_buckets():
    with hide('running'):
        output = local('s3cmd ls', capture=True)
    buckets = [l.split('  ', 1)[1] for l in output.splitlines()]
    return buckets

def get_latest_backup():
    buckets = get_s3_buckets()
    backups = [b for b in buckets if 'backup' in b]
    backups.sort(reverse=True)
    return backups[0]

@task
def clean_s3():
    """Remove unneeded backup versions"""
    # Keep daily backups for a week, and keep weekly updates

    buckets = get_s3_buckets()

    print "Processed the following backup buckets:"
    for bucket in buckets:
        if 'backup' in bucket:
            # Convert timestamp into a datetime object
            t = [int(i) for i in bucket.rsplit('-', 3)[1:4]]
            d = datetime.datetime(t[0], t[1], t[2])

            # If more than 7 days ago, delete if not on Monday
            if (d < datetime.datetime.now() - datetime.timedelta(days=7)
                    ) and (d.weekday() != 0):
                with hide('running', 'stdout'):
                    local('s3cmd del %s/*' % bucket)
                    local('s3cmd rb %s' % bucket)
                print '    %s deleted' % bucket
            else:
                print '    %s keeping' % bucket


@task
def daily_backup():
    """Do a full backup and clean S3. Should run daily."""

    full_backup()

    clean_s3()


@task
def ls():
    """List all backups uploaded to S3"""
    buckets = get_s3_buckets()
    for bucket in buckets:
        if 'backup' in bucket:
            with hide('running'):
                output = local('s3cmd du %s' % bucket, capture=True)
            disk_usage = int(output.split(' ', 1)[0])
            disk_usage = float(disk_usage)/1024/1024
            print '%s    %.2fM' % (bucket, disk_usage)


@task
def restore_postgresql(bucket=None):
    """Restore PostgreSQL backup"""

    if bucket is None:
        bucket = get_latest_backup()

    timestamp = bucket[-10:]
    filename = 'pgdump_%s.gz' % timestamp

    # Download from S3
    print "Fetching backup from %s" % bucket
    with hide('running'):
        run('s3cmd get %s/%s' % (bucket, filename))
        run('gunzip %s' % filename)
        filename = filename[:-3]

    # Load into PostgreSQL
    db_name = django_settings.DATABASES['default']['NAME']
    print "Loading data into database %s" % db_name
    with hide('running'):
        run('sudo -u postgres psql -d %s -f %s' % (db_name, filename))

    # Clean up
    with hide('running'):
        run('rm %s' % filename)


@task
def restore_directories(bucket=None):
    """Restore backed up directories"""

    if bucket is None:
        bucket = get_latest_backup()

    timestamp = bucket[-10:]

    for location in DIRS_TO_BACKUP:
        if exists(location):
            abort("%s exists, can't restore backup" % location)

        dirname, name = os.path.split(location.rstrip('/'))
        filename = name + '_' + timestamp + '.tar.gz'

        # Download from S3
        print "Fetching backup from %s" % bucket
        with hide('running'):
            run('s3cmd get %s/%s' % (bucket, filename))
            run('mkdir -p %s' % dirname)
            run('mv %s %s' % (filename, dirname))
            run('cd %s && tar pzxf %s' % (dirname, filename))
            run('cd %s && rm %s' % (dirname, filename))


@task
def restore(bucket=None):
    """Restore backup"""

    restore_directories(bucket)

    restore_postgresql(bucket)

