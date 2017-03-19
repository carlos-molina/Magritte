#!/usr/bin/python
"""
title           : segV2.py
description     : operates the umobile hotspot which supports NFD,DTN and Docker
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



import sys
import argparse
import traceback
import time
import os
import random
import subprocess

from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn import InterestFilter
from pyndn.security import KeyChain
from pyndn import Interest
import dockerctl
from enumerate_publisher import EnumeratePublisher
import putgetfunc
import picheck

class SEG(object):
    def __init__(self, node_id):

        self.node_id = str(node_id)
        print "Node-name: %s" % self.node_id
        prefix_serviceMigrationPush = "/sm/service_migration/push/" + self.node_id
        self.prefix_serviceMigrationPush = Name(prefix_serviceMigrationPush)

        prefix_serviceMigration = "/sm/service_migration"
        self.prefix_serviceMigration = Name(prefix_serviceMigration)

        prefix_serviceMonitoring = "/sm/service_monitoring" + '/' + self.node_id
        self.prefix_serviceMonitoring = Name(prefix_serviceMonitoring)

        self.serviceInfo = {
            'uhttpd.tar': {'image_name': 'fnichol/uhttpd:latest', 'port_host': 8080, 'port_container': 80,
                           'component': ['ubuntu.tar', 'python.tar', 'java.tar']},
            'httpd.tar': {'image_name': 'httpd:latest', 'port_host': 8081, 'port_container': 80,
                          'component': ['debian.tar', 'python.tar', 'java.tar']},
            'rpi-nano-httpd.tar': {'image_name': 'hypriot/rpi-nano-httpd:latest', 'port_host': 8082,
                                   'port_container': 80,
                                   'component': ['debian.tar', 'python.tar', 'java.tar']},
            'rpi-busybox-httpd.tar': {'image_name': 'hypriot/rpi-nano-httpd:latest', 'port_host': 8083,
                                   'port_container': 80,
                                   'component': ['debian.tar', 'python.tar', 'java.tar']}
        }

        self.pi_status = {
            'PiID': '',
            'hardResources': {},
            'softResources': {'OS': 'Linux'},
            'resourceUsage': {},
            'containers': []
        }

        # Default configuration of NDN
        self.outstanding = dict()
        self.isDone = False
        self.keyChain = KeyChain()
        self.face = Face("127.0.0.1")

        self.face.setCommandSigningInfo(self.keyChain, \
                                        self.keyChain.getDefaultCertificateName())
        self.face.registerPrefix(self.prefix_serviceMigrationPush, self.onInterest_serviceMigrationPush, self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_serviceMigrationPush.toUri()

        self.face.registerPrefix(self.prefix_serviceMonitoring, self.onInterest_serviceMonitoring,
                                 self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_serviceMonitoring.toUri()


    def run(self):

        try:
            # Run the event loop forever. Use a short sleep to prevent the Producer from using 100% of the CPU.
            while not self.isDone:
                self.face.processEvents()
                time.sleep(0.01)

        except RuntimeError as e:
            print "ERROR: %s" % e

    def onInterest_serviceMonitoring(self, prefix, interest, face, interestFilterId, filter):
        interestName = interest.getName()
        interestNameSize = interestName.size()
        interest_name_components = interestName.toUri().split("/")
        timeStamp = interest_name_components[interest_name_components.index("service_monitoring") + 2]
        print "Receive Interest message name: %s" % interestName

        ##### V2 Data message is JSON file
        try:
            SegmentNum = (interestName.get(interestNameSize - 1)).toSegment()
            dataName = interestName.getSubName(0, interestNameSize - 1)

        # If no segment number is included in the INTEREST, set the segment number as 0 and set the file name to configuration script to be sent
        except RuntimeError as e:
            SegmentNum = 0
            dataName = interestName

        # Put JSON file to the Data message

        jsonfileName = 'status'+'-'+self.node_id+'.json'
        print 'Monitoring FileName %s' %jsonfileName
        putgetfunc.put_PiID(self.pi_status, self.node_id)
        putgetfunc.put_hardResources_cpu(self.pi_status, "A 1.2GHz 64-bit quad-core ARMv8 CPU")
        putgetfunc.put_hardResources_mem(self.pi_status, "1GB")
        putgetfunc.put_hardResources_disk(self.pi_status, "16GB")
        putgetfunc.put_resourceUsage_cpu(self.pi_status, picheck.pi_cpuUsage())
        putgetfunc.put_resourceUsage_cpuLoad(self.pi_status, picheck.pi_cpuLoad())
        putgetfunc.put_resourceUsage_mem(self.pi_status, picheck.pi_memUsage())
        self.pi_status = dockerctl.container_info(self.pi_status)
        putgetfunc.put_PiID(self.pi_status, self.node_id)
        putgetfunc.create_jsonFile(self.pi_status, jsonfileName)

        # get the practical limit of the size of a network-layer packet : 8800 bytes
        maxNdnPacketSize = self.face.getMaxNdnPacketSize()

        #print 'practical limit of the size of a network-layer packet :' + str(maxNdnPacketSize)

        try:
            # due to overhead of NDN name and other header values; NDN header overhead + Data packet content = < maxNdnPacketSize
            # So Here segment size is hard coded to 5000 KB.
            # Class Enumerate publisher is used to split large files into segments and get a required segment ( segment numbers started from 0)

            dataSegment, last_segment_num = EnumeratePublisher(jsonfileName, 8000, SegmentNum).getFileSegment()

            # create the DATA name appending the segment number
            dataName = dataName.appendSegment(SegmentNum)

            data = Data(dataName)
            data.setContent(dataSegment)

            # set the final block ID to the last segment number
            last_segment = (Name.Component()).fromNumber(last_segment_num)
            data.getMetaInfo().setFinalBlockId(last_segment)
            hourMilliseconds = 600 * 1000
            data.getMetaInfo().setFreshnessPeriod(hourMilliseconds)

            # currently Data is signed from the Default Identitiy certificate
            self.keyChain.sign(data, self.keyChain.getDefaultCertificateName())
            # Sending Data message
            face.send(data.wireEncode().toBuffer())
            print "Replied to Interest name: %s" % interestName.toUri()
            print "Replied with Data name: %s" % dataName.toUri()

            # If configuration manager has sent the last segment of the file, script can be stopped.
            # if SegmentNum == last_segment_num:
            # self.isDone = True

        except ValueError as err:
            print "ERROR: %s" % err



    def onInterest_serviceMigrationPush(self, prefix, interest, face, interestFilterId, filter):
        # receive Push Interest from SC, send another Interest to start service migration
        interestName = interest.getName()
        #interestNameSize = interestName.size()
        print "Receive Interest message name: %s" % interestName
        interest_name_components = interestName.toUri().split("/")


        if "push" in interest_name_components:
            fileName = interest_name_components[interest_name_components.index("push") + 2]
            print fileName

        ## check image is running or not
        #Ger info from serviceInfo
        docker_image_name = self.serviceInfo[fileName]['image_name']
        docker_port_host = self.serviceInfo[fileName]['port_host']
        docker_port_container = self.serviceInfo[fileName]['port_container']

        print 'Check docker Image Name: %s ' % docker_image_name
        print 'Port Host: %d' % docker_port_host
        print 'Port Container %d' % docker_port_container
        if dockerctl.is_image_running(docker_image_name) == True:
            print 'Image: %s is already running' % docker_image_name
        else:
            ##image is not running
            ##check docker client has this image or not
            print 'Image: %s is NOT running' % docker_image_name
            if dockerctl.has_image(docker_image_name) == True:
                ## has image but image is not running
                print 'Image: %s is already stored' % docker_image_name
                if dockerctl.run_image(docker_image_name, docker_port_host, docker_port_container) == True:
                    print 'Running docker image %s ...' % docker_image_name
                else:
                    print 'Error: Cannot run image %s' % docker_image_name
            else:
                print 'Image: %s is not stored, pull from SC' % docker_image_name
                ### Call sendNextInterest to SC
                prefix.requestService = (self.prefix_serviceMigration.append(Name(fileName)))
                print 'Sending Interest message: %s' % prefix.requestService
                self.sendNextInterest(prefix.requestService)


    def sendNextInterest(self, name):
        interest = Interest(name)
        uri = name.toUri()

        interest.setInterestLifetimeMilliseconds(4000)
        interest.setMustBeFresh(True)

        if uri not in self.outstanding:
            self.outstanding[uri] = 1

        self.face.expressInterest(interest, self.onData, self.onTimeout)
        print "Sent Interest for %s" % uri

    def onData(self, interest, data):
        # payload = data.getContent()
        # name = data.getName()

        # print "Received data: ", payload.toRawStr()
        # del self.outstanding[name.toUri()]

        # self.isDone = Truepayload = data.getContent()
        payload = data.getContent()
        dataName = data.getName()
        dataName_size = dataName.size()

        print "Received data name: ", dataName.toUri()
        data_name_components = dataName.toUri().split("/")

        # Check any Configuration script is in the Data...If so Data name include "install" Keyword and name component next to "install" is the configuration script name
        #if "install" in data_name_components:
        if "service_migration" in data_name_components:
            #fileName = data_name_components[data_name_components.index("install") + 1]
            fileName = data_name_components[data_name_components.index("service_migration") + 1]

            # Write the configuration script in the desired location in append mode
            path = "/home/pi/SM_NDN/SEG_repository"

            if not os.path.exists(path):
                os.makedirs(path)

            with open(os.path.join(path, fileName), 'ab') as temp_file:
                temp_file.write(payload.toRawStr())

                # if recieved Data is a segment of the configuration script, then need to fetch remaing segments
                # try if segment number is existed in Data Name

            try:
                dataSegmentNum = (dataName.get(dataName_size - 1)).toSegment()
                lastSegmentNum = (data.getMetaInfo().getFinalBlockId()).toNumber()
                print "dataSegmentNum" + str(dataSegmentNum)
                print "lastSegmentNum" + str(lastSegmentNum)

                # If segment number is available and what have recieved is not the FINAL_BLOCK, then fetch the NEXT segment
                if lastSegmentNum != dataSegmentNum:
                    interestName = dataName.getSubName(0, dataName_size - 1)
                    interestName = interestName.appendSegment(dataSegmentNum + 1)
                    self.sendNextInterest(interestName)

                    # If segment number is available and what have recieved is the FINAL_BLOCK, then EXECUTE the configuration script

                ### Recieve all chunks of data --> Execute it here
                if lastSegmentNum == dataSegmentNum:
                    print "Received complete image: %s, EXECUTED !!!!" % fileName

                    #subprocess.call("python " + path + "/" + fileName, shell=True)
                    docker_image_name = self.serviceInfo[fileName]['image_name']
                    docker_port_host = self.serviceInfo[fileName]['port_host']
                    docker_port_container = self.serviceInfo[fileName]['port_container']

                    dockerctl.load_image(docker_image_name)
                    if dockerctl.run_image(docker_image_name, docker_port_host, docker_port_container) == True:
                        print 'Running docker image %s ...' % docker_image_name
                    else:
                        print 'Error: Cannot run image %s' % docker_image_name
                        # forward_request(webserver, port, s, data)
                    self.isDone = True

                    # If Configuration Manager has sent a file with 'install' key word, but no segment number is available, that DATA packet is invalid. Then just do nothing and exist the program
            except RuntimeError as e:
                print "ERROR: %s" % e
                self.isDone = True

        currentInterestName = interest.getName()

        # Delete the Interest name from outstanding INTEREST dict as reply DATA has been received.
        del self.outstanding[currentInterestName.toUri()]


    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()
        self.isDone = True

    def onTimeout(self, interest):
        name = interest.getName()
        uri = name.toUri()

        print "TIMEOUT #%d: %s" % (self.outstanding[uri], uri)
        self.outstanding[uri] += 1

        if self.outstanding[uri] <= 3:
            self.sendNextInterest(name)
        else:
            self.isDone = True

if __name__ == '__main__':

    node_id = raw_input('Enter SEG-ID (e.g., SEG_1) ')
    try:

        SEG(node_id).run()

    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
