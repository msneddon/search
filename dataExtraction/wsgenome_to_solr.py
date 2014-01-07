#!/usr/bin/env python

import StringIO
import json
import sys

import biokbase.workspace.client

#auth_token = biokbase.auth.Token(user_id='***REMOVED***', password='***REMOVED***')
ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')


progress = 0.0

all_workspaces = ws_client.list_workspace_info({})

print "There are %d visible workspaces." % len(all_workspaces)

print all_workspaces

outFile = open('genomesToSolr.tab', 'w')

outFile.write(unicode("object_id\tworkspace_id\tobject_type\tgenome_id\tfeature_id\tgenome_source_id\tfeature_sequence_length\t" + \
                 "feature_type\tfunction\talias\tscientific_name\t" + \
                 "genome_dna_size\tnum_contigs\tdomain\ttaxonomy\tgenetic_code\tgc_content\n").encode('utf8'))

workspace_counter = 0
for n in all_workspaces:
    print "Finished checking %s of all visible workspaces" % (str(100.0 * float(workspace_counter)/len(all_workspaces)) + " %")

    workspace_id = n[0]

    objects_list = ws_client.list_objects({"ids": [workspace_id]})
    if len(objects_list) > 0:
        print "\tWorkspace %s has %d objects" % (workspace_id, len(objects_list))
        object_counter = 0

        for x in objects_list:
            print "\t\tFinished checking %s, done with %s of all objects in %s" % (x[0], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_id)

            if "KBase.Genome" in x[2]:
                done = False
#                sys.stderr.write(str(x)+"\n")
                while not done:
                    try:
                        genome = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                        done = True
                    except Exception, e:
                        print str(e)
                        print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)

                #print json.dumps(genome['data'], sort_keys=True, indent=4, separators=(',',': '))
                genome = genome[0]
                #print genome['data'].keys()
                
		# want this undefined unless there actually are contigs
                num_contigs = ""
                if genome['data'].has_key('num_contigs'):
                    num_contigs = genome['data']['num_contigs']
#                    else:
#                        print genome['metadata']
#                        print genome['data']['contigs']
                elif genome['data'].has_key('contigs_uuid'):
                    done = False
                    skip = False
                    while not done:
                        try:
                            contigs = ws_client.get_object_by_ref({"reference": genome['data']['contigs_uuid'], "asHash": True})
                            done = True
                        except:
                            print "Having trouble getting contigs_uuid " + genome['data']['contigs_uuid'] + " from workspace " + workspace_id
                            done = True
                            skip = True

                    if not skip and contigs['data'].has_key('contigs') and contigs['data']['contigs'] is not None:
                        num_contigs = str(len(contigs['data']['contigs']))
                    else:
                        num_contigs = "1"
                else:
                    pass

                taxonomy = ""
                if genome['data'].has_key("taxonomy"):
                    taxonomy = genome['data']['taxonomy']

                try:
#                    print genome['data']
                    domain = genome['data']['domain']
                except:
                    domain = ""

                try:
                    dna_size = str(genome['data']['dna_size'])
                except:
                    dna_size = ""

                try:
                    object_type = x[2]
                except:
                    object_type = ""

                try:
                    genome_scientific_name = genome['data']['scientific_name']
                except:
                    genome_scientific_name = ""

                try:
                    genome_id = str(genome['data']['genome_id'])
                except:
                    genome_id = ""
                
                featureset_info = ws_client.get_objects([{"ref": genome['data']['featureset_ref']}])
                features = featureset_info[0]['data']['features']

                try:
                    gc_content = str(genome['data']['gc_content'])
                except:
                    try:
                        gc_content = str(float(genome['data']['gc'])/int(dna_size) * 100.0)
                    except:
                        gc_content = ""

#                rnas = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and k['type'].find("rna") > -1) or (k['id'].find("rna") > -1)]))
#                pegs = str(sum([1 for k in feature_list if (k.has_key('type') and k['type'] is not None and (k['type'].find("CDS") > -1 or k['type'].find("cds") > -1 or k['type'].find("peg") > -1 or k['type'].find("PEG") > -1))]))

                try:
                    source_id = str(genome['data']['genome_source_id'])
                except:
                    source_id = ""

                feature_id = ""
                sequence_length = ""
                feature_type = ""
                feature_function = ""
                feature_alias = ""                

                try:
                    genetic_code = str(genome['data']['genetic_code'])
                except:
                    genetic_code = ""

                phenotype = ""
                complete = ""
                prokaryotic = ""
                md5 = ""

#                object_id = str(workspace_id) + "." + str(genome_id)
                object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(genome['info'][0])

                outBuffer = StringIO.StringIO()

                try:
                    outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_id) + '\t' +
                                        str(object_type) + '\t' + str(genome_id) + '\t' + str(feature_id) + '\t' +
                                        str(source_id) + '\t' + str(sequence_length) + '\t' +
                                        str(feature_type) + '\t' + str(feature_function) + '\t' + 
                                        str(feature_alias) + '\t' +
#                                        str(pegs) + '\t' + str(rnas) + '\t' + str(genome_scientific_name) + '\t' + 
                                        str(genome_scientific_name) + '\t' + 
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
#                    print "pegs:" + pegs
#                    print "rnas:" + rnas
                    print "genome_scientific_name:" + genome_scientific_name
                    print "dna_size:" + dna_size
                    print "num_contigs:" + str(num_contigs)
                    print "domain:" + domain
                    print "taxonomy:" + taxonomy
                    print "genetic_code:" + genetic_code
                    print "gc_content:" + gc_content

                #outBuffer.write(genomeSolrText.encode('utf8'))

                # dump out each feature in tab delimited format
                for fid in features:
#                    print fid
                    f = features[fid]
#                    print f

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

#                    object_id = str(workspace_id) + "." + str(feature_id)
# not sure how to generate a solr id for these documents
                    object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(genome['info'][0]) + '.feature.' + str(fid)
                    object_type = "KBase.Feature-1.0"
                    
                    if f.has_key('feature_type'):
                        feature_type = f['feature_type']
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
#                                            pegs + '\t' + rnas + '\t' + genome_scientific_name + '\t' + 
                                            genome_scientific_name + '\t' + 
                                            dna_size + '\t' +
                                            str(num_contigs) + '\t' + domain + '\t' + taxonomy + '\t' + 
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
#                        print "pegs:" + pegs
#                        print "rnas:" + rnas
                        print "genome_scientific_name:" + genome_scientific_name
                        print "dna_size:" + dna_size
                        print "num_contigs:" + str(num_contigs)
                        print "domain:" + domain
                        print "taxonomy:" + taxonomy
                        print "genetic_code:" + genetic_code
                        print "gc_content:" + gc_content

                outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                outBuffer.close()
            object_counter += 1
    workspace_counter += 1
outFile.close()

