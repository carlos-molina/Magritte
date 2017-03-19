#!/usr/bin/env python2.7
"""
title           : dockerctl.py
description     : control docker engine
source          :
author          : Adisorn Lertsinsrubtavee
date            : 19  Mar 2017
version         : 2.0
usage           :
notes           :
compile and run : % python segV2.py
python_version  : Python 2.7.0
====================================================
"""
import time
import putgetfunc
#import subprocess
#import thread
#import urllib
from docker import Client
import os
from docker.utils import create_host_config

client = Client(base_url='unix://var/run/docker.sock',version='auto')
#client = docker.from_env(assert_hostname=False)
pulling_flag = False
path = "SEG_repository"
info = {}
container_list = []
# pi_status= {
#     'PiID': '192.0.0.1',
#     'hardResources': {'cpu': 'A 1.2GHz 64-bit quad-core ARMv8 CPU', 'mem': '1', 'disk': '32'},
#     'softResources': {'OS': 'Linux'},
#     'resourceUsage': {'cpuUsage': '30', 'cpuLoad': '70'},
#     'containers':    []
#     }
def run_image(image_name, port_host, port_container):
    print time.strftime("%a, %d %b %Y %X +0000", time.gmtime())
    if has_image(image_name) == True:
        print 'Start running image'
        config = client.create_host_config(port_bindings={port_container:port_host})
        container = client.create_container(image=image_name, ports=[port_container], host_config=config)
        client.start(container=container.get('Id'))
        print 'running image'
        print time.strftime("%a, %d %b %Y %X +0000", time.gmtime())
        return is_image_running(image_name)
    print time.strftime("%a, %d %b %Y %X +0000", time.gmtime())
    return False

def has_image(image_name):
    local_images = client.images()
    for image in local_images:
        #print image["RepoTags"]
        if image_name in image["RepoTags"]:
            print "HAS image: %s" % image["RepoTags"]
            return True
    return False

def is_image_running(image_name):
    for container in client.containers():
        if container["Image"] == image_name:
            return True
    return False

def load_image(image_name):
    image_shortname = image_name[image_name.find("/") + 1:image_name.find(":")]
    print image_shortname
    f = open(path + '/'+ image_shortname + '.tar', 'r')
    client.load_image(f)
    pulling_flag = False
    print 'image loaded'

# def container_infoOld():
#     for container in client.containers():
#         #print container["Image"], container["Status"], container["Id"], container["Names"]
#         info['Id'] = container['Id']
#         info['Names'] = container["Names"]
#         info['Status'] = container["Status"]
#         info['Image'] = container["Image"]
#         container_list.append(info)
#     return container_list

def container_info(pi_status):
    for container in client.containers():
        with open('/sys/fs/cgroup/cpuacct/docker/' + container['Id'] + '/cpuacct.usage', 'r') as f:
            cpuUsage = f.readline()
        with open('/sys/fs/cgroup/memory/docker/' + container['Id'] + '/memory.usage_in_bytes', 'r') as f:
            memUsage = f.readline()
        putgetfunc.put_container(pi_status, container['Id'], cpuUsage, memUsage, container['Names'], container['Status'], container['Image'])
    return pi_status


# def container_memUsage(Id):
#     with open('/sys/fs/cgroup/memory/docker/' + Id + '/memory.usage_in_bytes', 'r') as f:
#         memUsage = f.readline()
#     return memUsage
#
# def container_cpuUsage(Id):
#     with open('/sys/fs/cgroup/cpuacct/docker/' + Id + '/cpuacct.usage', 'r') as f:
#         cpuUsage = f.readline()
#     return cpuUsage

