"""
title           : putgetfunc.py
description     : includes 
                  a) functions to manipulate a dictionary that representes 
                     the consumption of a Raspberry Pi resources
                  b) functions for creating a json file from the dictionary and 
                     reading it from the file and converting it back to the original 
                     dictionary
source          :  
author          : Carlos Molina Jimenez
date            : 15 Feb 2017
version         : 1.0
usage           : 
notes           :
compile and run : % python3 putgetfunc.py
python_version  : Python 3.6.0   
====================================================
"""

"""
pi_status:     describes the resource configuration of an idividual Pi
               and their current consumption.
hardResources: hardware configuration of the Pi
               cpu: cpu description
               mem: memory size of the Pi in Gbytes
               disk disk size of the Pi in Gbutes
softResources: software configuration of the Pi
               OS: operating system of the Pi
resourceUsage: current status of resource consuption of the Pi
               cpuUsage: current cpu usage of the Pi in percentage
               cpuLoad:  current cpu load of the Pi (sa number between 1 and 4)
containers:    a dynamically growing/shrinking list of the containers currently running in the Pi.
               id: identification number of the container
               cpuUsage: current cpu usage of the container identified by id
               cpuUsage: current mem usage of the container identified by id

pi_status= {
    'PiID': '192.0.0.1',
    'hardResources': {'cpu': 'A 1.2GHz 64-bit quad-core ARMv8 CPU', 'mem': '1', 'disk': '32'}, 
    'softResources': {'OS': 'Linux'},
    'resourceUsage': {'cpuUsage': '30', 'cpuLoad': '70', memUsage:'20'},
    'containers':    [{'id': '64c1f6e0e5c19f9da2', 'cpuUsage': '23', 'memUsage': '3636', 'name': 'web1','status': 'Up 39 second', 'image': 'hypriot/rpi-busybox-httpd:latest'}
                     ]
}
"""

import json



"""
Expects a dictionary that representes the resources of a Pi.
Returns the id of the Pi
"""
def get_PiID(pi_status):
    piID=pi_status['PiID']
    return piID


"""
Expects a dictionary that representes the resources of a Pi and
the id of the Pi. Records the id in the dictionary. 
"""
def put_PiID(pi_status,piID):
    pi_status['PiID']=piID


"""
Expects a dictionary that representes the resources of a Pi.
Returns a sub-dictionary that represents the hardware resources of the Pi.
"""
def get_hardResources(pi_status):
    hardRes=pi_status['hardResources']
    return hardRes 

"""
Expects a dictionary that representes the resources of a Pi.
Returns the type of the cpu the Pi. 
"""
def get_hardResources_cpu(pi_status):            
    cpu=pi_status['hardResources']['cpu']
    return cpu 

"""
Expects a dictionary that representes the resources of a Pi and
the type of the cpu of the Pi.
Records the cpu in dicionary.
"""
def put_hardResources_cpu(pi_status,cpu):  
    pi_status['hardResources']['cpu']=cpu

"""
Expects a dictionary that representes the resources of a Pi.
Returns the size of the memory of the Pi 
"""
def get_hardResources_mem(pi_status):            
    mem=pi_status['hardResources']['mem']
    return mem 

"""
Expects a dictionary that representes the resources of a Pi.
and the size of the memory of the Pi and records it in the
dictionary.
"""
def put_hardResources_mem(pi_status,mem):        
    pi_status['hardResources']['mem']=mem

"""
Expects a dictionary that representes the resources of a Pi.
Returns the size of the disk of the Pi 
"""
def get_hardResources_disk(pi_status):
    disk=pi_status['hardResources']['disk']
    return  disk 

"""
Expects a dictionary that representes the resources of a Pi and
the size of the disk of the Pi.
Records the size of the disk in dictionary.  
"""
def put_hardResources_disk(pi_status,disk):        
    pi_status['hardResources']['disk']=disk

"""
Expects a dictionary that representes the resource usage of a Pi
Records the cpu usage in dictionary.
"""
def put_resourceUsage_cpu(pi_status,cpu):
    pi_status['resourceUsage']['cpuUsage']=cpu

"""
Expects a dictionary that representes the resource usage of a Pi
Records the cpu load in dictionary.
"""
def put_resourceUsage_cpuLoad(pi_status,cpuLoad):
    pi_status['resourceUsage']['cpuLoad']=cpuLoad

"""
Expects a dictionary that representes the resource usage of a Pi
Records the memory usage in dictionary.
"""
def put_resourceUsage_mem(pi_status,mem):
    pi_status['resourceUsage']['memUsage']=mem

"""
Expects a dictionary that representes the resources of a Pi.
Returns a list of dictionaries where each dictionary represents
a container currently running in the Pi. 
"""
def get_containers(pi_status):
    containersLst=pi_status['containers']
    return containersLst 


"""
Expects a dictionary that representes the resources of a Pi.
Returns the number of containers currently running in the Pi 
"""
def get_numContainers(pi_status):
    containerLst=pi_status['containers']
    return len(containerLst) 

"""
Expects a dictionary that representes the resources of a Pi,
the id of a container and the resource of interest (cpu, mem or disk).
Returns the current status of the given resource
"""
def get_containerResource(pi_status, containerID,resource):
    containersLst=pi_status['containers']
    l= len(containersLst)
    if l==0:
       return "No containers"
    else:
       for i in range(l):
         if containersLst[i]['id']==containerID:
            return containersLst[i][resource] 
         else:
            return "containerID not found"

"""
Expects a dictionary that representes the resources of a Pi and
the id of a container.
Returns a tuple of the form (containerID, cpuUsage, memUsage) which
represents the current status of the container identified as containerID.
Returns ("0", "0", "0") if no container is found with containerID
"""
def get_containerResources(pi_status, containerID):
    containersLst=pi_status['containers']
    l= len(containersLst)
    for i in range(l):
      if containersLst[i]['id']==containerID:
         return (containersLst[i]['id'], containersLst[i]['cpuUsage'], containersLst[i]['memUsage']) 
      else:
         return ("0", "0", "0") 

"""
Expects a dictionary that representes the resources of a Pi and
a tuple of the form (containerID, cpuUsage, memUsage) which
represents the current status of the container identified as containerID,
produces a dictionary out of the tuple and appends it to tail of
the list of containers running in the Pi
"""
def put_container(pi_status, containerID, cpuUsage, memUsage, name,status,image):
    containersList=pi_status['containers']
    containersList.append({'id': containerID, 'cpuUsage': cpuUsage, 'memUsage': memUsage, 'name' : name, 'status': status, 'image': image})


"""
Expects a dictionary that representes the resources of a Pi.
Returns a list of tuples. Each tuple has the form (containerID, cpuUsage, memUsage) which
represents the current status of each container
"""
def get_allContainerResources(pi_status):
    containersLst=pi_status['containers']
    l= len(containersLst)
    lst_of_tuples=[]
    for i in range(l):
        lst_of_tuples.append( (containersLst[i]['id'], containersLst[i]['cpuUsage'], containersLst[i]['memUsage'], containersLst[i]['name'],containersLst[i]['status'],containersLst[i]['image']))
    return lst_of_tuples 



"""
Expects a dictionary that representes the resources of a Pi
and a fname.
1) Deletes fname if it already exists then
2) Creates a json file named fname. 
"""
def create_jsonFile(pi_status, fname):
  import os
  try:
    os.remove(fname)
  except OSError:
    pass
  json_pi_status = json.dumps(pi_status)
  with open(fname, 'w') as json_outfile:
       json.dump(pi_status, json_outfile, ensure_ascii=False)



"""
Expects a dictionary that representes the resources of a Pi
and a file name that stores a json record that represents
the resources of a Pi.
Reads the json file from disk and converts it into the original dictionary 
that represents the resources of the Pi
"""
def read_jsonFile(fname): 
    with open(fname) as json_infile:
         pi_status_loaded = json.load(json_infile)
    return pi_status_loaded


"""
Expects a dictionary before and after being loaded 
from a file where it was stored as a json object.
Compares the two versions and return true is they are
equal, false otherwise
"""
def test_json_retrieval(pi_status, pi_status_loaded):
    if (pi_status == pi_status_loaded):
       return "true"
    else:
       return "false"




"""
I might need this later
http://stackoverflow.com/questions/19773669/python-dictionary-replace-values
def replace_value_with_newValue(current_dict, key_to_find, newValue):
    for key in current_dict.keys():
        if key == key_to_find:
            current_dict[key] = newValue 
"""

