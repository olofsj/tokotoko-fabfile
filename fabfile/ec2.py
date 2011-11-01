#-*- coding:utf-8 -*-
import time
from libcloud.providers import get_driver
from libcloud.base import NodeImage, NodeSize
from fabric.api import *
from settings import *

Driver = get_driver(EC2_PROVIDER)
conn = Driver(EC2_ACCESS_ID, EC2_SECRET_KEY)

@task
def list_nodes():
    """List all running EC2 nodes"""
    nodes = conn.list_nodes()
    for node in nodes:
        if node.state == 0:
            env.hosts.append(node.public_ip[0])
    print "Running on EC2 nodes:", env.hosts


@task
def status():
    """Show status of all EC2 nodes"""
    nodes = conn.list_nodes()
    if len(nodes) == 0:
        print "There are no active nodes."
    else:
        for node in nodes:
            print 'Name:', node.name, 'IP:', node.public_ip[0], 'State:', node.state


@task
def initLocalS3cmd():
    """Set up s3cmd config on the local machine"""
    print "Setting up local s3cmd configuration."
    with hide('running', 'stdout'):
        local('echo "%s\n%s\n%s\n\n\n\ny\ny\n" | s3cmd --configure' %
                (EC2_ACCESS_ID, EC2_SECRET_KEY, S3CMD_ENC_PASS))


@task
def new_instance():
    """Provision a new EC2 instance"""
    name = raw_input("Name of new instance: ")
    image = NodeImage(id=EC2_AMI_NAME, name="", driver="")
    size = NodeSize(id=EC2_INSTANCE_SIZE, name="", ram=None, disk=None, bandwidth=None, price=None, driver="")
    node = conn.create_node(name=name, image=image, size=size,
            ex_keyname=EC2_KEYNAME, ex_securitygroup=EC2_SECURITY_GROUP)
    nodes = conn.list_nodes()
    print nodes
    while nodes[-1].state != 0:
        print nodes[-1]
        time.sleep(30)
        nodes = conn.list_nodes()
    print "ok"
    nodes = conn.list_nodes()

