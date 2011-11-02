#-*- coding:utf-8 -*-
import server
import ec2
import backup
from fabric.api import *
import getpass

@task
def localhost():
    user = getpass.getuser()
    env.hosts = [user + '@127.0.0.1']
    print "Running on " + unicode(env.hosts)


def print_path():
    import os
    print os.getcwd()

