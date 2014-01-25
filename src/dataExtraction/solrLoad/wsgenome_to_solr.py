#!/usr/bin/env python

import StringIO
import json
import sys
import random

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

wsname = 'KBasePublicRichGenomes'

def export_genomes_from_ws(maxNumObjects):
    #ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    outFile = open('genomesToSolr.tab', 'w')
    
    # to add
    # genome_source, feature_source_id,genome_publications,
    # subsystems and/or subsystem_data, annotations, regulon_data
    # don't print header, use header file (so can split output)
    #outFile.write(unicode("object_id\tworkspace_name\tobject_type\tgenome_id\tfeature_id\tgenome_source_id\tprotein_translation_length\t" + \
    #                 "roles\tprotein_families\tcoexpressed_fids\tco_occurring_fids\t" + \
    #                 "feature_publications\tannotations\t" + \
    #                 "feature_type\tfunction\taliases\tscientific_name\t" + \
    #                 "genome_dna_size\tnum_contigs\tdomain\ttaxonomy\tgc_content\n").encode('utf8'))
    
    workspace_counter = 0
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        objects_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome"})
    
        if len(objects_list) > 0:
            print "\tWorkspace %s has %d objects" % (workspace_name, len(objects_list))
            object_counter = 0
    
            if maxNumObjects < 1000:
                objects_list = random.sample(objects_list,maxNumObjects)
    
            for x in objects_list:
                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
    
                if "Genome" in x[2]:
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
                    roles = ''
                    protein_families = ''
                    coexpressed_fids = ''
                    co_occurring_fids = ''
                    feature_publications = ''
                    annotations = ''
    
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
                        outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_name) + '\t' +
                                            str(object_type) + '\t' + str(genome_id) + '\t' + str(feature_id) + '\t' +
                                            str(source_id) + '\t' + str(sequence_length) + '\t' +
                                            str(roles) + '\t' + str(protein_families) + '\t' + str(coexpressed_fids) + '\t' + str(co_occurring_fids) + '\t' +
                                            str(feature_publications) + '\t' + str(annotations) + '\t' +
                                            str(feature_type) + '\t' + str(feature_function) + '\t' + 
                                            str(feature_alias) + '\t' +
    #                                        str(pegs) + '\t' + str(rnas) + '\t' + str(genome_scientific_name) + '\t' + 
                                            str(genome_scientific_name) + '\t' + 
                                            str(dna_size) + '\t' +
                                            str(num_contigs) + '\t' + str(domain) + '\t' + str(taxonomy) + '\t' + 
                                            str(gc_content) + "\n"))
                    except Exception, e:
                        print str(e)
    
                        print "Failed trying to write to string buffer."
                        print "object_id:" + str(object_id)
                        print "workspace_name:" + str(workspace_name)
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
    #                    print "genetic_code:" + genetic_code
                        print "gc_content:" + gc_content
    
                    #outBuffer.write(genomeSolrText.encode('utf8'))
    
                    # dump out each feature in tab delimited format
                    # need to batch these calls, super slow one at a time
                    features_to_retrieve = list()
                    features_to_process = list()
                    for fid in features:
                        features_to_retrieve.append({"ref": workspace_name+'/'+fid})
                        if len(features_to_retrieve) > 99:
                            features_to_process.extend(ws_client.get_objects(features_to_retrieve))
                            features_to_retrieve = list()
                            print >> sys.stderr, 'retrieved features so far: ' + str(len(features_to_process)) + ' of total features: ' + str(len(features))
                    # final batch
                    if len(features_to_retrieve) > 0:
                        features_to_process.extend(ws_client.get_objects(features_to_retrieve))
    
    #                print >> sys.stderr, len(features_to_process)
    #                print >> sys.stderr, len(features)
                    for feature in features_to_process:
    
                        object_type = feature['info'][2]
                        object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(feature['info'][0])
    
                        f = feature['data']
    
                        try:
                            for role in f['roles']:
                                roles += unicode(role) + ' '
                        except:
                            roles = ""
    
                        try:
                            for anno in f['annotations']:
                                annotations += anno[0] + ' ' + anno[1] + ' '
                                re.sub('\n',' ',annotations)
    #                            annotations = ''
                        except:
                            annotations = ""
    
                        try:
                            for pub in f['feature_publications']:
    #                            print pub
                                feature_publications += str(pub[0]) + ' ' + pub[2] + ' ' + pub[3] + ' ' + pub[5] + ' ' + pub[6] + ' '
    #                            print 'feature_publications is ' + feature_publications
                        except Exception, e:
    #                        print e
                            feature_publications = ""
    
                        try:
                            for coo in f['co_occurring_fids']:
                                co_occurring_fids += coo[0] + ' '
                        except:
                            co_occurring_fids = ""
    
                        try:
                            for coe in f['coexpressed_fids']:
                                coexpressed_fids += coe[0] + ' '
    #                            coexpressed_fids = ""
                        except:
                            coexpressed_fids = ""
    
                        try:
                            for ss in f['subsystems']:
                                subsystems += unicode(ss) + ' '
                        except:
                            subsystems = ""
    
                        try:
    #                        protein_families = unicode(f["protein_families"][0]['id'] + f['protein_families'][0]['subject_description'])
                            for pf in f['protein_families']:
                                protein_families += unicode(pf['id']) + ' : ' + unicode(pf['subject_description']) + ' :: '
    #                        protein_families = unicode(f["protein_families"])
                        except:
                            protein_families = ""
    
                        try:
                            feature_function = unicode(f["function"])
                        except:
                            feature_function = ""
    
                        try:
                            feature_id = fid
                        except:
                            feature_id = ""
    
                        try:
                            # want something like this for roles, subsystems
                            feature_alias = ','.join([str(k) for k in f["aliases"]])
                        except:
                            feature_alias = ""
    
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
                            outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_name) + '\t' +
                                                object_type + '\t' + str(genome_id) + '\t' + str(feature_id) + '\t' +
                                                str(source_id) + '\t' + sequence_length + '\t' +
                                                str(roles) + '\t' + str(protein_families) + '\t' + str(coexpressed_fids) + '\t' + str(co_occurring_fids) + '\t' +
                                                str(feature_publications) + '\t' + str(annotations) + '\t' +
                                                feature_type + '\t' + feature_function + '\t' + 
                                                feature_alias + '\t' +
    #                                            pegs + '\t' + rnas + '\t' + genome_scientific_name + '\t' + 
                                                genome_scientific_name + '\t' + 
                                                dna_size + '\t' +
                                                str(num_contigs) + '\t' + domain + '\t' + taxonomy + '\t' + 
                                                gc_content + "\n"))
                        except Exception, e:
                            print "Failed trying to write to string buffer."
                            print e
                            print "object_id:" + object_id
                            print "workspace_name:" + str(workspace_name)
                            print "object_type:" + object_type
                            print "genome_id:" + genome_id
                            print "feature_id:" + feature_id
                            print "source_id:" + source_id
                            print "sequence_length:" + sequence_length
                            print "feature_type:" + feature_type
                            print "feature_function:" + feature_function
                            print "feature_alias:" + feature_alias
                            print "roles:" + roles
                            print "subsystems:" + subsystems
                            print "protein_families:" + protein_families
    #                        print "pegs:" + pegs
    #                        print "rnas:" + rnas
                            print "genome_scientific_name:" + genome_scientific_name
                            print "dna_size:" + dna_size
                            print "num_contigs:" + str(num_contigs)
                            print "domain:" + domain
                            print "taxonomy:" + taxonomy
    #                        print "genetic_code:" + genetic_code
                            print "gc_content:" + gc_content
    
                        # this died:
    #Traceback (most recent call last):
    #  File "/homes/chicago/kkeller/dev_container/modules/search/dataExtraction/wsgenome_to_solr.py", line 343, in <module>
    #    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
    #MemoryError
    
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()
                else:
                    print '            skipping %s, is a %s' % (x[0], x[2])
                object_counter += 1
        workspace_counter += 1
    outFile.close()
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    args = parser.parse_args()
    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    export_genomes_from_ws(maxNumObjects)
