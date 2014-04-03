#!/usr/bin/env python

import StringIO
import json
import sys
import random
import simplejson
import re

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

wsinput = 'KBasePublicRichGenomesLoad'
wsoutput = 'KBasePublicGenomesLoad'
#wsoutput = '***REMOVED***:home'

def export_genomes_from_ws(maxNumObjects,genome_list):
    #ws_prod_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_prod_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws/')
    # gavin's dev instance
#    ws_prod_client = biokbase.workspace.client.Workspace('http://140.221.84.209:7058/')
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
        # need to loop through to make sure we get all objects; limit of 5000 items returned by ws
#        objects_list = ws_prod_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome"},limit:5000,skip:skipNum)
        object_count = 1
        skipNum = 0
        limitNum = 5000
        while object_count != 0:
            this_list = ws_prod_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome","limit":limitNum,"skip":skipNum})
            object_count=len(this_list)
            skipNum += limitNum
            objects_list.extend(this_list)

#    print objects_list
#    print len(objects_list)
#    exit(0)

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
#                    print >> sys.stderr, 'object '  + x[1] + ' found, replacing'
                    print >> sys.stderr, 'object '  + x[1] + ' found in ws ' + wsoutput + ' , skipping'
                    continue
                except biokbase.workspace.client.ServerError, e:
                    print >> sys.stderr, 'object '  + x[1] + ' not found, adding to ws ' + wsoutput

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

                # sometimes genomes are problematic
                # can hard-code list of genomes to skip
#                if genome['data'].has_key('genome_id'):
#                    if genome['data']['genome_id'] in ['kb|g.23167']:
#                        print >> sys.stderr, 'skipping ' + genome['data']['genome_id'] + ' , possible problem with RichGenome object'
#                        continue
#                    if genome['data']['genome_id'] in ['kb|g.3907','kb|g.140106','kb|g.140085','kb|g.166828','kb|g.166814','kb|g.3899']:
#                        print >> sys.stderr, 'skipping ' + genome['data']['genome_id'] + ' , searchable data too big'
#                        continue

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
#                    print >> sys.stderr, contig_info
#                    print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')



                fbaGenomeObject['features'] = list()

                featureset_info = ws_prod_client.get_objects([{"ref": genome['data']['featureset_ref']}])
                features = featureset_info[0]['data']['features']

                for feature in features:

                    fbaFeature=dict()

                    # should check whether there is a ref here
                    f = features[feature]['data']

                    # these keys should have same name and structure in both object types
                    # fbagenome does not have roles
                    structure_keys = ['function','md5','protein_translation','dna_sequence','protein_translation_length','dna_sequence_length','subsystems', 'protein_families', 'annotations','subsystem_data','regulon_data','atomic_regulons','coexpressed_fids','co_occurring_fids']
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

                    # aliases do not have the same structure
                    # not sure how to handle the source_db, ignoring for now
                    if f.has_key('aliases'):
                        fbaFeature['aliases'] = list()
                        for alias in f['aliases']:
                            fbaFeature['aliases'].extend(f['aliases'][alias])

#                    print >> sys.stderr, simplejson.dumps(fbaFeature, sort_keys=True, indent=4 * ' ')

                    fbaGenomeObject['features'].append(fbaFeature)

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

# would like a try block here
# if the save fails because subdata is too big, try to re-save as a genome-like object that doesn't
# have as many searchable fields
                try:
                    genome_info = ws_prod_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"KBaseGenomes.Genome","data":fbaGenomeObject,"name":fbaGenomeObject['id']}]})
                except biokbase.workspace.client.ServerError as err:
                    rematch = re.search('subdata size \d+ exceeds limit', str(err))
                    if rematch != None:
                        print >> sys.stderr,fbaGenomeObject['id'] + ' is too large, skipping for now'
                        continue
#                        print >> sys.stderr,fbaGenomeObject['id'] + ' is too large, trying to save as BasicGenome object'
#                        genome_info = ws_prod_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"kkellerKBaseGenomes.BasicGenome","data":fbaGenomeObject,"name":fbaGenomeObject['id']}]})
                    else:
                        raise
                print >> sys.stderr,genome_info

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
