#!/usr/bin/env python

import pymongo
import requests
import datetime
import numpy

shockURL = "http://localhost:7044/"

times = list()

try:    
    mc = pymongo.MongoClient()

    shockObjects = mc['workspace']['shock_nodeMap'].find()
    print "Grabbing " + str(shockObjects.count()) + " genomes"

    begin = datetime.datetime.now()

    total = 0

    done = False
    while not done:
        node = shockObjects.next()['node']

        start = datetime.datetime.now()

        r = requests.get(shockURL + "node/" + node + "?download", auth=(username, password))
        data = r.json        

        downloadTime = datetime.datetime.now() - start

        print "genome " + str(total) + "     " + shockURL + "node/" + node + "?download" + "     " + str(downloadTime)
        total += 1
        times.append(downloadTime.total_seconds())
except Exception, e:
    print str(e)
    print "DONE"

    ntimes = numpy.array(times)

    print "Total time: " + str(datetime.datetime.now() - begin)
    print "Max: " + str(numpy.max(ntimes))
    print "Min: " + str(numpy.min(ntimes))
    print "Average: " + str(numpy.mean(ntimes))
    print "Stddev: " + str(numpy.stddev(ntimes))
