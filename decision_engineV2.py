#!/usr/bin/python
"""
title           : seg.py
description     : Decide where to migrate the service
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

class DecisionEngine(object):

    def __init__(self, nodeName, data):
        self.nodeName = nodeName
        #print data
        self.data = data.split('/')
        #print self.data
        self.monitoringData = {'memUsage': ' ', 'loadAvg': ' '}
        self.monitoringData['memUsage'] = self.data[0]
        self.monitoringData['loadAvg'] = self.data[1]
        print self.monitoringData
        print 'Memory Usage:', self.monitoringData['memUsage']
        print 'Load Average:', self.monitoringData['loadAvg']
        self.memUsage_threshold = 60
        self.loadAvg_threshold = 1

    def makeDecision(self):
        memUsage = float(self.monitoringData['memUsage'])
        loadAvg = float(self.monitoringData['loadAvg'])
        print "Processing monitoring Data with rules base "
        if memUsage > self.memUsage_threshold:
            print "memUsage is larger than threshold, cannot create service on %s" % self.nodeName
            return False
        else:
            print "memUsage is less than threshold, check CPU load"
            if loadAvg <  self.loadAvg_threshold:
                print 'CPU load is under threshold, migrate service to %s' %self.nodeName
                return True
            else:
                print 'memUsage is lower than threshold, but CPU is too high, CANNOT migrate the service to %s' %self.nodeName
                return False
