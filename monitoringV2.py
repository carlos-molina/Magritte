#!/usr/bin/python
"""
title           : monitoring.py
description     : Collect monitoring data of raspberry pi
                  put collected to JSON file
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
import threading
import argparse
import traceback
import time
import os
import subprocess

from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn import InterestFilter
from pyndn.security import KeyChain
from pyndn import Interest
import dockerctl
from decision_engineV2 import DecisionEngine
import ndnMessageHandler

class Monitoring(object):
    def __init__(self):

        self.node = {}
        self.node.setdefault('A', []).append('SEG_1')
        self.node.setdefault('B', []).append('SEG_2')
        self.node.setdefault('B', []).append('SEG_3')
        self.node.setdefault('B', []).append('SEG_4')
        self.node.setdefault('ALL', []).append('SEG_1')
        self.node.setdefault('ALL', []).append('SEG_2')
        self.node.setdefault('ALL', []).append('SEG_3')
        self.node.setdefault('ALL', []).append('SEG_4')


        self.prefix_trigger = "/trigger/"
        #self.prefix_trigger = Name(prefix_trigger)

        self.prefix_serviceMonitoring = "/sm/service_monitoring"
        #self.prefix_serviceMonitoring = Name(prefix_serviceMonitoring)

        self.serviceName = "rpi-nano-httpd.tar"
        # Default configuration of NDN
        self.outstanding = dict()
        self.isDone = False
        self.keyChain = KeyChain()
        self.face = Face("127.0.0.1")

        self.face.setCommandSigningInfo(self.keyChain, \
                                        self.keyChain.getDefaultCertificateName())
        self.timer = 5.0

    def run(self):
        try:
            # send Interest message to retrieve data
            # self.sendNextInterest(self.prefix_serviceMigration)
            groupName = 'A'

            self.sendMonitoring_Interest(groupName)

            while not self.isDone:
                self.face.processEvents()
                time.sleep(0.01)


        except RuntimeError as e:
            print "ERROR: %s" % e

    def sendMonitoring_Interest(self, group):
        print "Send Interest: Monitoring to group: %s" %group
        for selectedNode in self.node[group]:
            print "node: %s " % selectedNode
            f = os.popen('date +%s')
            timestamp = f.read()
            print 'Timestamp %s' % timestamp
            name = Name(self.prefix_serviceMonitoring + '/' + selectedNode + '/' + timestamp)

            interest = Interest(name)
            uri = name.toUri()

            interest.setInterestLifetimeMilliseconds(4000)
            interest.setMustBeFresh(True)

            if uri not in self.outstanding:
                self.outstanding[uri] = 1

            self.face.expressInterest(interest, self.onMonitoringData, self.onTimeout)
            print "Sent Interest for %s" % uri
            ## create new thread to send Interest monitoring every X sec.
            monitoring = threading.Timer(self.timer, self.sendMonitoring_Interest, [group])
            monitoring.start()

    def onMonitoringData(self, interest, data):
        print "Receive monitoring data"
        payload = data.getContent()
        dataName = data.getName()
        dataName_size = dataName.size()
        data_name_components = dataName.toUri().split("/")

        if "service_monitoring" in data_name_components:
            nodeName = data_name_components[data_name_components.index("service_monitoring") + 1]
            timeStamp = data_name_components[data_name_components.index("service_monitoring") + 2]
            print 'Receive Data from %s' % nodeName
            print 'Timestamp %s' % timeStamp

            fileName = 'status'+'-'+nodeName+'.json'
            print fileName
            # Write the configuration script in the desired location in append mode
            path = "/home/pi/carlos/codeV2/SC_monitoring"
            #self.isDone = ndnMessageHandler.processingData(path, fileName, data)
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
                    ### Fix this
                    self.sendNextInterest_Monitoring(interestName)

                    # If segment number is available and what have recieved is the FINAL_BLOCK, then EXECUTE the configuration script

                ### Recieve all chunks of data --> Execute it here
                if lastSegmentNum == dataSegmentNum:
                    print "Received complete Data message: %s  " % fileName

            except RuntimeError as e:
                print "ERROR: %s" % e
                self.isDone = True

        else:
            print "this is not monitoring Data"

        currentInterestName = interest.getName()
        # Delete the Interest name from outstanding INTEREST dict as reply DATA has been received.
        del self.outstanding[currentInterestName.toUri()]

    def sendNextInterest_Monitoring(self, name):
        interest = Interest(name)
        uri = name.toUri()

        interest.setInterestLifetimeMilliseconds(4000)
        interest.setMustBeFresh(True)

        if uri not in self.outstanding:
            self.outstanding[uri] = 1

        self.face.expressInterest(interest, self.onMonitoringData, self.onTimeout)
        print "Sent Interest for %s" % uri

    def sendPushInterest(self, name):
        interest = Interest(name)
        uri = name.toUri()

        interest.setInterestLifetimeMilliseconds(4000)
        interest.setMustBeFresh(True)

        if uri not in self.outstanding:
            self.outstanding[uri] = 1

        # self.face.expressInterest(interest, self.onData, self._onTimeout)
        self.face.expressInterest(interest, None, None)  ## set None --> sent out only, don't wait for Data and Timeout
        print "Sent Push-Interest for %s" % uri

    def onTimeout(self, interest):
        name = interest.getName()
        uri = name.toUri()

        print "TIMEOUT #%d: %s" % (self.outstanding[uri], uri)
        self.outstanding[uri] += 1

        if self.outstanding[uri] <= 3:
            self.sendMonitoring_Interest(name)
        else:
            self.isDone = True


if __name__ == '__main__':

    #resetStatus = raw_input('Enter 1 if need to auto configure this new light, else Enter 0 ')
    try:

        Monitoring().run()

    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)