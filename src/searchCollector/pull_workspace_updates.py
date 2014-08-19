#!/usr/bin/env python

import pymongo
import gridfs
import bson
import json
import datetime
import cStringIO
import requests


def find_genome_updates_since(mongoClient, timestamp):
    #connect to the Mongo server and find out which objects were saved after a certain datetime
    cursor = self.mongoClient['workspace']['workspaceObjVersions'].find({"savedate" : {"$gt" : timestamp}})

    #filter out only Genome objects
    mongoUpdates = [c for c in cursor if "KBGA.Genome" in c['type']]

    #close the mongo cursor
    cursor.close()

    #return the objects in chronological order
    return sorted(mongoUpdates)


def get_updated_object(mongoClient, mongoObject):
    #use the checksum from this mongo workspace object to find the associated shock node
    shockNode = mongoClient['workspace']['shock_nodeMap'].find_one({'chsum': mongoObject['chksum']})   

    return shockNode['node']


def flatten_genome_object(meta,nodeid):

    req = requests.get(shockBaseURL + "/node/" + nodeid + "?download", auth=('***REMOVED***', '***REMOVED***'))

    object = json.loads(req.content)

    outBuffer = cStringIO.StringIO()

    outBuffer.write(unicode("object_id\tworkspace_id\tobject_type\tgid\tfid\tgenome_source_id\tfeature_sequence_length\t" + \
                 "feature_type\tfunction\talias\tpegs\trnas\tscientific_name\t" + \
                 "genome_dna_size\tcontigs\tdomain\ttaxonomy\tgenetic_code\tgc_content\n"))


### magic done happens ###

# future: want to be able to detect any type of object we know about
    genome = object

    # hard-code for now; will need to be able to retrieve from meta
    workspace_id = 12345
    genome['info'] = list()
    genome['info'].append(54321)

    num_contigs = "0"
    if genome.has_key('contigs'):
        if len(genome['contigs']) == 0:
            num_contigs = "1"
        else:
            print genome['metadata']
            print genome['contigs']
    elif genome.has_key('contigs_uuid'):
        done = False
        skip = False
        while not done:
            try:
# will need to modify this code for wsv2
                contigs = ws_client.get_object_by_ref({"reference": genome['contigs_uuid'], "asHash": True})
                done = True
            except:
                print "Having trouble getting contigs_uuid " + genome['contigs_uuid'] + " from workspace " + workspace_id
                done = True
                skip = True

        if not skip and contigs.has_key('contigs') and contigs['data']['contigs'] is not None:
            num_contigs = str(len(contigs['contigs']))
        else:
            num_contigs = "1"
    else:
        pass

    taxonomy = ""
    if genome.has_key("annotation_uuid"):
        done = False
        skip = False
        while not done:
            try:
                annotation = ws_client.get_object_by_ref({"reference": genome['annotation_uuid'], "asHash": True})
                done = True
            except:
                print "Having trouble getting annotation_uuid " + genome['annotation_uuid'] + " from workspace " + workspace_id
                done = True
                skip = True
                
        if not skip and annotation.has_key('genomes') and annotation['data']['genomes'] is not None:
            #print json.dumps(annotation, sort_keys=True, indent=4, separators=(',',': '))
            taxonomy = annotation['genomes'][0]['taxonomy']
    else:
        pass
#        print genome.keys()

    try:
        domain = genome['domain']
    except:
        domain = ""

    try:
        dna_size = str(genome['size'])
    except:
        dna_size = "0"

    try:
        object_type = x[1]
    except:
        object_type = ""

    try:
        genome_scientific_name = genome['scientific_name']
    except:
        genome_scientific_name = ""

    try:
        genome_id = str(genome['id'])                
    except:
        genome_id = ""
    
    feature_list = genome['features']

    try:
        gc_content = str(float(genome['gc'])/int(dna_size) * 100.0)
    except:
        try:
            gc_content = str(genome['gc'])
        except:
            gc_content = ""

    rnas = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and k['type'].find("rna") > -1) or (k['id'].find("rna") > -1)]))
    pegs = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and (k['type'].find("CDS") > -1 or k['type'].find("cds") > -1 or k['type'].find("peg") > -1 or k['type'].find("PEG") > -1))]))

    try:
        source_id = str(genome['source_id'])
    except:
        source_id = ""

    feature_id = ""
    sequence_length = ""
    feature_type = ""
    feature_function = ""
    feature_alias = ""                

    try:
        genetic_code = str(genome['genetic_code'])
    except:
        genetic_code = ""

    phenotype = ""
    complete = ""
    prokaryotic = ""
    md5 = ""

#    object_id = str(workspace_id) + "." + str(genome_id)
    object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(genome['info'][0])

    try:
        outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_id) + '\t' +
                            str(object_type) + '\t' + str(genome_id) + '\t' + str(feature_id) + '\t' +
                            str(source_id) + '\t' + str(sequence_length) + '\t' +
                            str(feature_type) + '\t' + str(feature_function) + '\t' + 
                            str(feature_alias) + '\t' +
                            str(pegs) + '\t' + str(rnas) + '\t' + str(genome_scientific_name) + '\t' + 
                            str(dna_size) + '\t' +
                            str(num_contigs) + '\t' + str(domain) + '\t' + str(taxonomy) + '\t' + 
                            str(genetic_code) + '\t' + str(gc_content) + "\n"))
    except Exception, e:
        print str(e)

        print "Failed trying to write to string buffer."
        print "object_id:" + str(object_id)
        print "workspace_id:" + str(workspace_id)
        print "object_type:" + object_type
        print "genome_id:" + str(genome_id)
        print "feature_id:" + str(feature_id)
        print "source_id:" + str(source_id)
        print "sequence_length:" + sequence_length
        print "feature_type:" + feature_type
        print "feature_function:" + feature_function
        print "feature_alias:" + feature_alias
        print "pegs:" + pegs
        print "rnas:" + rnas
        print "genome_scientific_name:" + genome_scientific_name
        print "dna_size:" + dna_size
        print "num_contigs:" + num_contigs
        print "domain:" + domain
        print "taxonomy:" + taxonomy
        print "genetic_code:" + genetic_code
        print "gc_content:" + gc_content

    #outBuffer.write(genomeSolrText.encode('utf8'))

    # dump out each feature in tab delimited format
    for f in feature_list:
        #print f

        try:
            feature_function = unicode(f["function"])
        except:
            feature_function = ""

        try:
            feature_id = unicode(f["id"])
        except:
            feature_id = ""

        try:
            feature_alias = ','.join([str(k) for k in f["aliases"]])
        except:
            feature_alias = ""

#        object_id = str(workspace_id) + "." + str(feature_id)
        object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(genome['info'][0]) + '.feature.' + str(feature_id)
        object_type = "Feature"
        
        if f.has_key('type'):
            feature_type = f['type']
        else:
            try:
                feature_type = f['id'].split('.')[-2]
            except:
                feature_type = ""

        try:
            sequence_length = str( sum( [int(f['location'][i][3]) for i in range(len(f['location']))] ) )
        except:
            sequence_length = "0"

        try:
            outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_id) + '\t' +
                                object_type + '\t' + str(genome_id) + '\t' + str(feature_id) + '\t' +
                                str(source_id) + '\t' + sequence_length + '\t' +
                                feature_type + '\t' + feature_function + '\t' + 
                                feature_alias + '\t' +
                                pegs + '\t' + rnas + '\t' + genome_scientific_name + '\t' + 
                                dna_size + '\t' +
                                num_contigs + '\t' + domain + '\t' + taxonomy + '\t' + 
                                genetic_code + '\t' + gc_content + "\n"))
        except Exception, e:
            print "Failed trying to write to string buffer."
            print "object_id:" + object_id
            print "workspace_id:" + str(workspace_id)
            print "object_type:" + object_type
            print "genome_id:" + genome_id
            print "feature_id:" + feature_id
            print "source_id:" + source_id
            print "sequence_length:" + sequence_length
            print "feature_type:" + feature_type
            print "feature_function:" + feature_function
            print "feature_alias:" + feature_alias
            print "pegs:" + pegs
            print "rnas:" + rnas
            print "genome_scientific_name:" + genome_scientific_name
            print "dna_size:" + dna_size
            print "num_contigs:" + num_contigs
            print "domain:" + domain
            print "taxonomy:" + taxonomy
            print "genetic_code:" + genetic_code
            print "gc_content:" + gc_content


### magic done happens ###

    return outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','')


def push_to_solr(data):    
    solr_url = "http://localhost:7077/search/wsGenomeFeatures/update?wt=json&separator=%09"
    commit_url = "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=wsGenomeFeatures"

    outFile = open('testUpdate.tab', 'w')
    outFile.write(data)
    outFile.close()

    response = requests.post(solr_url, data=data, auth=(username, password))

    #base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    #request.add_header("Authorization", "Basic %s" % base64string)
    #request.add_header("Content-type", "application/csv;charset=utf-8")
    
    response = requests.post(commit_url, data="", auth=(username, password))
    return response


if __name__ == "__main__":
    import cProfile
    import pstats

    pr = cProfile.Profile()
    pr.enable()

    mongoServer = 'localhost'
    
    mongoClient = pymongo.MongoClient(host=mongoServer,slaveOk=True)

    timestamp = datetime.datetime.now() - datetime.timedelta(days=30)

    findUpdatesStartTime = datetime.datetime.now()

    newObjects = find_genome_updates_since(mongoClient, timestamp.isoformat())

    findUpdatesEndTime = datetime.datetime.now()

    print findUpdatesEndTime - findUpdatesStartTime

    print len(newObjects)

    for x in newObjects:
        getUpdateStartTime = datetime.datetime.now()

        id = get_updated_object(x)   

        getUpdateEndTime = datetime.datetime.now()

        print "grab updated object: " + str(getUpdateEndTime - getUpdateStartTime)

        #print meta
        #print json.dumps(data, indent=4, sort_keys=True)

        flattenStartTime = datetime.datetime.now()
        
        solrString = flatten_genome_object(id)

        flattenEndTime = datetime.datetime.now()
                
        print "flatten object: " + str(flattenEndTime - flattenStartTime)

        pushStartTime = datetime.datetime.now()

        result = push_to_solr(solrString).read()

        pushEndTime = datetime.datetime.now()

        print "push to solr: " + str(pushEndTime - pushStartTime)

        print result
        break

    pr.disable()

    s = cStringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print s.getvalue()

    print "DONE"
