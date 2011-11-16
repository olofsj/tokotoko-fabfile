#-*- coding:utf-8 -*-
from fabric.api import *
import getpass
import os
import sys


ENV_VAR = 'TOKOTOKO_FABFILE_PROJECT'

def find_project_dir():
    name = 'fabfile_settings.py'

    # Check if env variable set
    if os.getenv(ENV_VAR):
        # Use environment variable setting
        path = os.getenv(ENV_VAR)
        joined = os.path.join(path, name)
        if os.path.exists(joined):
            return os.path.abspath(path)

    # Otherwise, start in cwd and work downwards towards filesystem root
    path = '.'
    # Stop before falling off root of filesystem (should be platform
    # agnostic)
    while os.path.split(os.path.abspath(path))[1]:
        joined = os.path.join(path, name)
        if os.path.exists(joined):
            return os.path.abspath(path)
        path = os.path.join('..', path)

    print "No project settings found."
    sys.exit()

# Add project dir to path to be able to load fabfile and Django settings
project_dir = find_project_dir()
sys.path.append(project_dir)

# Load all modules
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

