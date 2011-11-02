#-*- coding:utf-8 -*-
from fabric.api import *
import getpass

try:
    import server
    import ec2
    import backup
except ImportError:
    pass


@task
def localhost():
    user = getpass.getuser()
    env.hosts = [user + '@127.0.0.1']
    print "Running on " + unicode(env.hosts)


def print_path():
    import os
    print os.path.dirname(__file__)

