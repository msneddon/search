#!/usr/bin/env python

import StringIO
import json
import sys
import random
import simplejson

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

wsinput = 'KBasePublicRichGenomes'
wsoutput = 'KBasePublicGenomes'
#wsoutput = '***REMOVED***:home'

def export_genomes_from_ws(maxNumObjects,genome_list):
    #ws_prod_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_prod_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws/')
#    ws_dev_client = biokbase.workspace.client.Workspace('https://140.221.84.209:7058/')
    #ws_dev_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws/')
    
    workspace_object = ws_prod_client.get_workspace_info({'workspace':wsinput})
    
    workspace_id = workspace_object[0]
    workspace_name = workspace_object[1]
    
    print genome_list
    objects_list = list()
    if len(genome_list) > 0:
        names_list = list()
        for genome in genome_list:
            names_list.append({'workspace':wsinput,'name':genome})
        objects_list = [x['info'] for x in ws_prod_client.get_objects(names_list)]
    else:
        objects_list = ws_prod_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome"})

    if len(objects_list) > 0:
        print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
        object_counter = 0

        if maxNumObjects < 1000:
            objects_list = random.sample(objects_list,maxNumObjects)

        for x in objects_list:
            print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)

            if "Genome" in x[2]:
                try:
                    ws_prod_client.get_object_info([{"workspace":wsoutput,"name":x[1]}],0)
                    print >> sys.stderr, 'object '  + x[1] + ' found, skipping'
                    continue
                except biokbase.workspace.client.ServerError, e:
                    print >> sys.stderr, 'object '  + x[1] + ' not found, adding to ws'

                done = False
                while not done:
                    try:
                        genome = ws_prod_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                        done = True
                    except Exception, e:
                        print str(e)
                        print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)

                #print json.dumps(genome['data'], sort_keys=True, indent=4, separators=(',',': '))
                genome = genome[0]
                #print genome['data'].keys()
                
                fbaGenomeObject = dict()

                scalar_keys = ['genetic_code','dna_size','md5','num_contigs','taxonomy','scientific_name','domain', 'complete', 'gc_content']
                for key in scalar_keys:
                    try:
                        fbaGenomeObject[key] = genome['data'][key]
                    except:
                        fbaGenomeObject[key] = ''

                # special keys
                if genome['data'].has_key('genome_id'):
                    fbaGenomeObject['id'] = genome['data']['genome_id']

                if genome['data'].has_key('genome_source'):
                    fbaGenomeObject['source'] = genome['data']['genome_source']

                if genome['data'].has_key('genome_source_id'):
                    fbaGenomeObject['source_id'] = genome['data']['genome_source_id']

                if genome['data'].has_key('genome_publications'):
                    fbaGenomeObject['publications'] = genome['data']['genome_publications']

                fbaGenomeObject['contig_lengths'] = list()
                fbaGenomeObject['contig_ids'] = list()
                if genome['data'].has_key('contig_lengths'):
                    fbaGenomeObject['contig_lengths'] = [ genome['data']['contig_lengths'][x] for x in genome['data']['contig_lengths'] ]
                    fbaGenomeObject['contig_ids'] = [ x for x in genome['data']['contig_lengths'] ]

                if genome['data'].has_key('contigset_ref'):
#                    contigs = ws_prod_client.get_objects([{"wsid": str(workspace_id), "objid": genome['data']['contigset_ref']}])
#                    print >> sys.stderr, genome['data']['contigset_ref']
                    wsstuff = genome['data']['contigset_ref'].split('/')
#                    print >> sys.stderr, wsstuff
                    contigref = ws_prod_client.get_objects([{"wsid": str(workspace_id), "objid": wsstuff[1]}])
#                    print >> sys.stderr, contigref
#                    print >> sys.stderr, contigref[0]['info']
                    contig = contigref[0]['data']
                    fbaContig = dict()
                    fbaContig['contigs'] = list()
                    contig_keys = ["id","md5","source","source_id"]
                    for key in contig_keys:
                        if contig.has_key(key):
                            fbaContig[key] = contig[key]
                        else:
                            fbaContig[key] = ''
                    if contig.has_key('contigs'):
                        fbaContig['contigs'] = [ contig['contigs'][x] for x in contig['contigs']]

                    contig_info = ws_prod_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"KBaseGenomes.ContigSet","data":fbaContig,"name": contigref[0]['info'][1]}]})
                    print >> sys.stderr, contig_info
#                    print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')



                fbaGenomeObject['features'] = list()

                featureset_info = ws_prod_client.get_objects([{"ref": genome['data']['featureset_ref']}])
                features = featureset_info[0]['data']['features']

                # dump out each feature in tab delimited format
                # need to batch these calls, super slow one at a time
                features_to_retrieve = list()
                features_to_process = list()
                for fid in features:
                    features_to_retrieve.append({"ref": workspace_name+'/'+fid})
                    if len(features_to_retrieve) > 99:
                        features_to_process.extend(ws_prod_client.get_objects(features_to_retrieve))
                        features_to_retrieve = list()
                        print >> sys.stderr, 'retrieved features so far: ' + str(len(features_to_process)) + ' of total features: ' + str(len(features))


                # final batch
                if len(features_to_retrieve) > 0:
                    features_to_process.extend(ws_prod_client.get_objects(features_to_retrieve))

#                print >> sys.stderr, len(features_to_process)
#                print >> sys.stderr, len(features)
                for feature in features_to_process:

                    fbaFeature=dict()

                    f = feature['data']

                    # these keys should have same name and structure in both object types
                    # fbagenome does not have roles
                    structure_keys = ['function','md5','protein_translation','dna_sequence','protein_translation_length','dna_sequence_length','subsystems', 'protein_families', 'aliases','annotations','subsystem_data','regulon_data','atomic_regulons','coexpressed_fids','co_occurring_fids']
                    for key in structure_keys:
                        if f.has_key(key):
                            fbaFeature[key]=f[key]

# special keys
                    if f.has_key('feature_id'):
                        fbaFeature['id'] = f['feature_id']

                    if f.has_key('feature_type'):
                        fbaFeature['type'] = f['feature_type']

                    if f.has_key('feature_publications'):
                        fbaFeature['publications'] = f['feature_publications']

                    # fba feature doesn't have ordinal
                    # ideally should sort locations by ordinal
                    if f.has_key('location'):
                        fbaFeature['location'] = list()
                        for loc in f['location']:
                            contig = loc[0]
                            begin = loc[1]
                            strand = loc[2]
                            length = loc[3]
                            ordinal = loc[4]
                            this_loc=[contig,begin,strand,length]
                            fbaFeature['location'].append(this_loc)


#                    print >> sys.stderr, simplejson.dumps(fbaFeature, sort_keys=True, indent=4 * ' ')

                    fbaGenomeObject['features'].append(fbaFeature)

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')
                genome_info = ws_prod_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"KBaseGenomes.Genome","data":fbaGenomeObject,"name":fbaGenomeObject['id']}]})
#                print >> sys.stderr,genome_info

            else:
                print '            skipping %s, is a %s' % (x[0], x[2])
            object_counter += 1
#    workspace_counter += 1
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('genomes', action="store", nargs='*')
    args = parser.parse_args()
    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    print args.genomes
    export_genomes_from_ws(maxNumObjects,args.genomes)
