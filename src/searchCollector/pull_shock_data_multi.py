#!/usr/bin/env python

import pymongo
import requests
import datetime
import numpy
import multiprocessing
import gc
import simplejson

shockURL = "http://localhost:7044/"

def fetch_data(node):
    start = datetime.datetime.now()

    r = requests.get(shockURL + "node/" + node + "?download", auth=(username, password))
    data = simplejson.loads(r.content)

    downloadTime = datetime.datetime.now() - start

    print shockURL + "node/" + node + "?download" + "     " + str(downloadTime) + "     " + r.headers['content-length']

    r = None
    data = None
    start = None

    gc.collect()
    
    return downloadTime.total_seconds()



times = list()
chunkSize = 1

try:    
    gc.enable()

    mc = pymongo.MongoClient()
    shockObjects = mc['workspace']['shock_nodeMap'].find()

    nodes = list()

    try:
        done = False
        while not done:
            nodes.append(shockObjects.next()['node'])
    except:
        pass

    nodes = nodes[:1000]

    pool = multiprocessing.Pool(processes=chunkSize)

    print "Grabbing " + str(len(nodes)) + " genomes"

    begin = datetime.datetime.now()
    results = pool.imap_unordered(fetch_data,nodes,chunkSize)
    pool.close()
    pool.join()

    print "DONE"

    times = list()

    try:
        while True:
            times.append(results.next())
    except:
        pass    

    ntimes = numpy.array(times)

    #print "Total data: " + str()
    print "Total time: " + str(datetime.datetime.now() - begin)
    print "Max: " + str(numpy.max(ntimes))
    print "Min: " + str(numpy.min(ntimes))
    print "Average: " + str(numpy.mean(ntimes))
    print "Stddev: " + str(numpy.std(ntimes))
except Exception, e:
    print str(e)
