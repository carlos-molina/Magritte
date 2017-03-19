#!/usr/bin/python
import sys
import time
import traceback

from pyndn import Data
from pyndn import Face
from pyndn import Interest
from pyndn import Name
from pyndn.security import KeyChain
from enumerate_publisher import EnumeratePublisher


class ServiceController(object):
    def __init__(self):
        # Register all published name prefixes
        prefix_serviceDiscovery = "/sm/service_discovery"
        self.prefix_serviceDiscovery = Name(prefix_serviceDiscovery)

        prefix_serviceRegistration = "/sm/service_registration"
        self.prefix_serviceRegistration = Name(prefix_serviceRegistration)

        prefix_serviceMigration = "/sm/service_migration"
        self.prefix_serviceMigration = Name(prefix_serviceMigration)

        self.prefix_serviceMigrationPush = "/sm/service_migration/push/"

        prefix_trigger = "/trigger"
        self.prefix_trigger = Name(prefix_trigger)
        self.Path = "/home/pi/carlos/SC_repository/"
        self.serviceName = "rpi-nano-httpd.tar"
        self.serviceInfo = {
            'uhttpd.tar': {'image_name': 'fnichol/uhttpd:latest', 'port_host': 8080, 'port_container': 80,
                           'component': ['ubuntu.tar', 'python.tar', 'java.tar']},
            'httpd.tar': {'image_name': 'httpd:latest', 'port_host': 8081, 'port_container': 80,
                          'component': ['debian.tar', 'python.tar', 'java.tar']},
            'rpi-nano-httpd.tar':{'image_name': 'hypriot/rpi-nano-httpd:latest', 'port_host': 8082, 'port_container': 80,
                          'component': ['debian.tar', 'python.tar', 'java.tar']},
            'rpi-busybox-httpd.tar': {'image_name': 'hypriot/rpi-nano-httpd:latest', 'port_host': 8083,
                                      'port_container': 80,
                                      'component': ['debian.tar', 'python.tar', 'java.tar']}
            }


        # Create face to localhost, Default configuration from PyNDN
        self.outstanding = dict()
        self.isDone = False
        self.keyChain = KeyChain()
        self.face = Face("127.0.0.1")

        # Set the KeyChain and certificate name used to sign command interests (e.g. for registerPrefix).
        self.face.setCommandSigningInfo(self.keyChain, \
                                        self.keyChain.getDefaultCertificateName())
        # Register name prefixes to the face

        self.face.registerPrefix(self.prefix_serviceDiscovery, self.onInterest_serviceDiscovery, self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_serviceDiscovery.toUri()

        self.face.registerPrefix(self.prefix_serviceRegistration, self.onInterest_serviceRegistration, self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_serviceRegistration.toUri()

        self.face.registerPrefix(self.prefix_serviceMigration, self.onInterest_serviceMigration, self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_serviceMigration.toUri()

        self.face.registerPrefix(self.prefix_trigger, self.onInterest_trigger, self.onRegisterFailed)
        print "Registering prefix : " + self.prefix_trigger.toUri()

    def onInterest_trigger(self,prefix, interest, face, interestFilterId, filter):
        interestName = interest.getName()
        print "Received Interest name: %s" % interestName.toUri()
        interest_name_components = interestName.toUri().split("/")
        serviceName = interest_name_components[2]
        nodeName = interest_name_components[3]
        prefix_serviceMigrationPushtoNode = self.prefix_serviceMigrationPush + nodeName + '/' + serviceName
        print "Sent Push Interest for %s" % prefix_serviceMigrationPushtoNode
        self.prefix_serviceMigrationPushtoNode = Name(prefix_serviceMigrationPushtoNode)
        self.sendPushInterest(self.prefix_serviceMigrationPushtoNode)

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

    def onInterest_serviceDiscovery(self, prefix, interest, face, interestFilterId, filter):
        print "Processing Interest message:/SM/service_discovery"
        # send a list of available service

    def onInterest_serviceRegistration(self,prefix, interest, face, interestFilterId, filter):
        print "Processing Interest message:/SM/service_registration"
        # upload image file to repository
        # send ACK to service provider

    def onInterest_serviceMigration(self,prefix, interest, face, interestFilterId, filter):
        # Receive command from decision engine to migrate teh service to some specific location
        # Select image file from the repo
        # Send to the chosen SEG

        interestName = interest.getName()
        interestNameSize = interestName.size()
        print "Receive Interest message: %s , sending back DATA message" % interestName
        # try if the received INTEREST include a segment number. If include, extract the segment number and file requested.
        try:
            SegmentNum = (interestName.get(interestNameSize - 1)).toSegment()
            serviceName = (interestName.get(interestNameSize - 2)).toEscapedString()
            dataName = interestName.getSubName(0, interestNameSize - 1)

        # If no segment number is included in the INTEREST, set the segment number as 0 and set the file name to configuration script to be sent
        except RuntimeError as e:
            SegmentNum = 0
            #dataName = (interestName.append(Name("install")).append(Name(self.serviceName)))
            dataName = interestName

        # TO BE USED WITH WEB INTERFACE

        filePath = self.Path + self.serviceName
        print filePath
        # Test in terminal
        # self.filePath = "config_script_tobe_uploaded/" + serviceName

        # get the practical limit of the size of a network-layer packet : 8800 bytes
        maxNdnPacketSize = self.face.getMaxNdnPacketSize()

        # print 	'practical limit of the size of a network-layer packet :' + str(maxNdnPacketSize)

        try:
            # due to overhead of NDN name and other header values; NDN header overhead + Data packet content = < maxNdnPacketSize
            # So Here segment size is hard coded to 5000 KB.
            # Class Enumerate publisher is used to split large files into segments and get a required segment ( segment numbers started from 0)

            dataSegment, last_segment_num = EnumeratePublisher(filePath, 5000, SegmentNum).getFileSegment()

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

            face.send(data.wireEncode().toBuffer())
            print "Replied to Interest name: %s" % interestName.toUri()
            print "Replied with Data name: %s" % dataName.toUri()

            # If configuration manager has sent the last segment of the file, script can be stopped.
            #if SegmentNum == last_segment_num:
                #self.isDone = True


        except ValueError as err:
            print "ERROR: %s" % err

    def onRegisterFailed(self, prefix, interest, face, interestFilterId, filter):
        print "Register failed for prefix", prefix.toUri()
        self.isDone = True


    def run(self):
        try:

            while not self.isDone:
                self.face.processEvents()
                time.sleep(0.01)

        except RuntimeError as e:
            print "ERROR: %s" % e


if __name__ == '__main__':

    try:

        SC = ServiceController()
        SC.run()

    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
