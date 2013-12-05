#!/usr/bin/env python

import pymongo
import gridfs
import bson

import json
import datetime
import base64
import cStringIO
import urllib2

def find_genome_updates_since(timestamp):
    mongoUpdates = list()

    mongoClient = pymongo.MongoClient(host='198.128.58.84',slaveOk=True)
    db = mongoClient.workspace_service
    collection = db.workspaceObjects
    # can also set read preference here i think
    #cursor=collection.find({"type":"Genome","moddate":{"$gt":"2013-11-05T18"}},{"id":1,"workspace":1})
    # want to use a date on the fly (python DateTime object?)
    cursor = collection.find({"moddate":{"$gt":timestamp}},{"uuid":1,"id":1,"workspace":1,"type":1})
    # returns a cursor object (can be used as array?)

    #print cursor.count()
    #print cursor[50]

    for c in cursor:
        if c['type'] != "Genome":
            continue
        else:
            mongoUpdates.append(c['_id'])

    cursor.close()
    mongoClient.close()

    return sorted(mongoUpdates)


def get_updated_object(id):
    mongoId = bson.objectid.ObjectId(id)

    mongoClient = pymongo.MongoClient('198.128.58.84', slaveOk=True)

    updatedObject = mongoClient.workspace_service.workspaceObjects.find_one({'_id': mongoId})

    dataBlob = mongoClient.workspace_service.fs.files.find_one({'chsum': updatedObject['chsum']})   
    gridFSClient = gridfs.GridFS(mongoClient.workspace_service)
    dataString = gridFSClient.get(dataBlob['_id']).read()

    mongoClient.close()

    return updatedObject, json.loads(dataString)


def flatten_genome_object(meta, data):
    mongoClient = pymongo.MongoClient('198.128.58.84', slaveOk=True)

    outBuffer = cStringIO.StringIO()

    outBuffer.write(unicode("object_id\tworkspace_id\tobject_type\tgid\tfid\tgenome_source_id\tfeature_sequence_length\t" + \
                 "feature_type\tfunction\talias\tpegs\trnas\tscientific_name\t" + \
                 "genome_dna_size\tcontigs\tdomain\ttaxonomy\tgenetic_code\tgc_content\n"))

    workspace_id = meta["workspace"]
    genome_id = meta["id"]

    num_contigs = "0"
    if "Contigs" in meta['refdeps'].values():
        contig_uuid = [x for x, y in meta['refdeps'].items() if y == "Contigs"][0]

        #fetch contigs and count them
        contigObject = mongoClient.workspace_service.workspaceObjects.find_one({'uuid': contig_uuid})
        contigBlob = mongoClient.workspace_service.fs.files.find_one({'chsum': contigObject['chsum']})   
        gridFSClient = gridfs.GridFS(mongoClient.workspace_service)
        contigs = json.loads(gridFSClient.get(contigBlob['_id']).read())['contigs']

        num_contigs = str(len(contigs))

        annotation_uuid = [x for x, y in meta['refdeps'].items() if y == "Annotation"][0]

        taxonomy = ""
        if annotation_uuid is not None:
            #fetch annotation and get taxonomy
            annotationObject = mongoClient.workspace_service.workspaceObjects.find_one({'uuid': annotation_uuid})
            annotationBlob = mongoClient.workspace_service.fs.files.find_one({'chsum': annotationObject['chsum']})   
            gridFSClient = gridfs.GridFS(mongoClient.workspace_service)
            annotation = json.loads(gridFSClient.get(annotationBlob['_id']).read())

            if annotation.has_key('genomes') and annotation['genomes'] is not None:
                taxonomy = annotation['genomes'][0]['taxonomy']

            try:
                domain = data['domain']
            except:
                domain = ""

            try:
                dna_size = str(data['size'])
            except:
                dna_size = "0"

            try:
                object_type = x[1]
            except:
                object_type = ""

            try:
                genome_scientific_name = data['scientific_name']
            except:
                genome_scientific_name = ""

            try:
                genome_id = str(data['id'])                
            except:
                genome_id = ""
                
            feature_list = data['features']

            try:
                gc_content = str(float(data['gc'])/int(dna_size) * 100.0)
            except:
                try:
                    gc_content = str(data['gc'])
                except:
                    gc_content = ""

            rnas = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and k['type'].find("rna") > -1) or (k['id'].find("rna") > -1)]))
            pegs = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and (k['type'].find("CDS") > -1 or k['type'].find("cds") > -1 or k['type'].find("peg") > -1 or k['type'].find("PEG") > -1))]))

            try:
                source_id = str(data['source_id'])
            except:
                source_id = ""

            feature_id = ""
            sequence_length = ""
            feature_type = ""
            feature_function = ""
            feature_alias = ""                

            try:
                genetic_code = str(data['genetic_code'])
            except:
                genetic_code = ""

            phenotype = ""
            complete = ""
            prokaryotic = ""
            md5 = ""

            object_id = workspace_id + "." + genome_id

            try:
                outBuffer.write(unicode(object_id + '\t' + workspace_id + '\t' +
                                        object_type + '\t' + genome_id + '\t' + feature_id + '\t' +
                                        source_id + '\t' + sequence_length + '\t' +
                                        feature_type + '\t' + feature_function + '\t' + 
                                        feature_alias + '\t' +
                                        pegs + '\t' + rnas + '\t' + genome_scientific_name + '\t' + 
                                        dna_size + '\t' +
                                        num_contigs + '\t' + domain + '\t' + taxonomy + '\t' + 
                                        genetic_code + '\t' + gc_content + "\n"))
            except Exception, e:
                print "Failed trying to write to string buffer."
                print "object_id:" + object_id
                print "workspace_id:" + workspace_id
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

                object_id = workspace_id + "." + feature_id
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
                    outBuffer.write(unicode(object_id + '\t' + workspace_id + '\t' +
                                            object_type + '\t' + genome_id + '\t' + feature_id + '\t' +
                                            source_id + '\t' + sequence_length + '\t' +
                                            feature_type + '\t' + feature_function + '\t' + 
                                            feature_alias + '\t' +
                                            pegs + '\t' + rnas + '\t' + genome_scientific_name + '\t' + 
                                            dna_size + '\t' +
                                            num_contigs + '\t' + domain + '\t' + taxonomy + '\t' + 
                                            genetic_code + '\t' + gc_content + "\n"))
                except Exception, e:
                    print "Failed trying to write to string buffer."
                    print "object_id:" + object_id
                    print "workspace_id:" + workspace_id
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

    return outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','')


def push_to_solr(data):    
    solr_url = "http://192.168.1.201:7077/search/wsGenomeFeatures/update?wt=json&separator=%09"

    commit_url = "http://192.168.1.201:7077/search/admin/cores?wt=json&action=RELOAD&core=wsGenomeFeatures"

    username = "admin"
    password = "***REMOVED***"

    outFile = open('testUpdate.tab', 'w')
    outFile.write(data)
    outFile.close()

    request = urllib2.Request(solr_url, data)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Content-type", "application/csv;charset=utf-8")

    response = urllib2.urlopen(request)

    request = urllib2.Request(commit_url, "")
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Content-type", "application/csv;charset=utf-8")
    
    response = urllib2.urlopen(request)
    return response


if __name__ == "__main__":
    import cProfile
    import pstats

    pr = cProfile.Profile()
    pr.enable()

    timestamp = datetime.datetime.now() - datetime.timedelta(days=30)

    findUpdatesStartTime = datetime.datetime.now()

    newObjects = find_genome_updates_since(timestamp.isoformat())

    findUpdatesEndTime = datetime.datetime.now()

    print findUpdatesEndTime - findUpdatesStartTime

    print len(newObjects)

    for x in newObjects:
        getUpdateStartTime = datetime.datetime.now()

        meta, data = get_updated_object(x)   

        getUpdateEndTime = datetime.datetime.now()

        print "grab updated object: " + str(getUpdateEndTime - getUpdateStartTime)

        #print meta
        #print json.dumps(data, indent=4, sort_keys=True)

        flattenStartTime = datetime.datetime.now()
        
        solrString = flatten_genome_object(meta, data)

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
