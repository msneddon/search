#!/usr/bin/env python

import StringIO
import json
import sys
import random
import simplejson
import re
import time
import traceback

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

#wsinput = 'KBasePublicRichGenomesV3'
#wsoutput = 'KBasePublicGenomesV3LoadJul2014'
#wsoutput = 'kbasetest:home'

def copy_richGenome_to_genome(maxNumObjects,genome_list,wsinput,wsoutput,start_index,end_index,ws_source_client,ws_target_client):
    # gavin's dev instance
#    ws_prod_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    #ws_dev_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws/')

#    print "Start_index : " + str(start_index)
#    print "End_index : " + str(end_index)
    
    workspace_object = ws_source_client.get_workspace_info({'workspace':wsinput})
    
    workspace_id = workspace_object[0]
    workspace_name = workspace_object[1]
    
    print genome_list
    objects_list = list()
    if len(genome_list) > 0:
        names_list = list()
        for genome in genome_list:
            names_list.append({'workspace':wsinput,'name':genome})
        objects_list = [x['info'] for x in ws_source_client.get_objects(names_list)]
    else:
        # need to loop through to make sure we get all objects; limit of 5000 items returned by ws
#        objects_list = ws_source_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome"},limit:5000,skip:skipNum)
        object_count = 1
        skipNum = 0
        limitNum = 5000
        while object_count != 0:
            this_list = ws_source_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome","limit":limitNum,"skip":skipNum})
            object_count=len(this_list)
            skipNum += limitNum
            objects_list.extend(this_list)

#    print objects_list
#    print len(objects_list)
#    exit(0)

    objects_list.sort(key=lambda object: object[1])
#    print >> sys.stderr, objects_list


    if len(objects_list) > 0:
        print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
        object_counter = 0

        if maxNumObjects < 1000:
            objects_list = random.sample(objects_list,maxNumObjects)

        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = len(objects_list) - 1

        objects_list = objects_list[start_index:(end_index + 1)] 

#        print "Length of object list : " + str(len(objects_list))
#        sys.exit()

        for x in objects_list:
            print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
            
            if "Genome" in x[2]:

                try:
                    ws_source_client.get_object_info([{"workspace":wsoutput,"name":x[1]}],0)
                    object_counter += 1
                    if args.skip_existing == True:
                        print >> sys.stderr, 'object '  + x[1] + ' found in ws ' + wsoutput + ' , skipping'
                        continue
                    print >> sys.stderr, 'object '  + x[1] + ' found, replacing'
                except biokbase.workspace.client.ServerError, e:
                    print >> sys.stderr, 'object '  + x[1] + ' not found, adding to ws ' + wsoutput

                start = time.time()
                print >> sys.stderr, 'starting genome processing for ' + x[1]

                done = False
                while not done:
                    try:
                        genome = ws_source_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                        done = True
                    except Exception, e:
                        print str(e)
                        print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)

                end = time.time()
                print >> sys.stderr, "retrieved genome object for %s %s" % ( x[1], str(end - start))
                start = time.time()

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
                    fbaGenomeObject['contig_lengths'] = [ genome['data']['contig_lengths'][y] for y in genome['data']['contig_lengths'] ]
                    fbaGenomeObject['contig_ids'] = [ y for y in genome['data']['contig_lengths'] ]

                #Provenance
                genome_provenance = genome['provenance']

                end = time.time()
                print >> sys.stderr, "compiled genome object for %s %s" % ( x[1], str(end - start))
                start = time.time()

                if genome['data'].has_key('contigset_ref') and not args.skip_dna_sequences:
#                    contigs = ws_source_client.get_objects([{"wsid": str(workspace_id), "objid": genome['data']['contigset_ref']}])
#                    print >> sys.stderr, genome['data']['contigset_ref']
                    wsstuff = genome['data']['contigset_ref'].split('/')
#                    print >> sys.stderr, wsstuff
                    contigref = ws_source_client.get_objects([{"wsid": str(workspace_id), "objid": wsstuff[1]}])
#                    print >> sys.stderr, contigref
#                    print >> sys.stderr, contigref[0]['info']
                    contig = contigref[0]['data']
                    contig_provenance = contigref[0]['provenance']
                    fbaContig = dict()
                    fbaContig['contigs'] = list()
                    contig_keys = ["id","md5","source","source_id"]
                    for key in contig_keys:
                        if contig.has_key(key):
                            fbaContig[key] = contig[key]
                        else:
                            fbaContig[key] = ''
                    if contig.has_key('contigs'):
                        fbaContig['contigs'] = [ contig['contigs'][y] for y in contig['contigs']]

#                    print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

                end = time.time()
                print >> sys.stderr, "retrieved contigset object for %s %s" % ( x[1], str(end - start))
                start = time.time()

                fbaGenomeObject['features'] = list()

                featureset_info = ws_source_client.get_objects([{"ref": genome['data']['featureset_ref']}])
                end = time.time()
                print >> sys.stderr, "retrieved featureset object for %s %s" % ( x[1], str(end - start))
                start = time.time()

                features = featureset_info[0]['data']['features']

                for feature in features:

                    fbaFeature=dict()

                    # should check whether there is a ref here
                    f = features[feature]['data']

                    # these keys should have same name and structure in both object types
                    # fbagenome does not have roles
                    structure_keys = ['function','md5','protein_translation','protein_translation_length','dna_sequence_length','subsystems', 'protein_families', 'annotations','subsystem_data','regulon_data','atomic_regulons','coexpressed_fids','co_occurring_fids']
                    for key in structure_keys:
                        if f.has_key(key):
                            fbaFeature[key]=f[key]

# special keys
                    if f.has_key('feature_id'):
                        fbaFeature['id'] = f['feature_id']

                    if f.has_key('dna_sequence') and not args.skip_dna_sequences:
                        fbaFeature['dna_sequence'] = f['dna_sequence']

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

                end = time.time()
                print >> sys.stderr, "compiled features for %s %s" % ( x[1], str(end - start))
                start = time.time()

#                print >> sys.stderr, simplejson.dumps(fbaGenomeObject, sort_keys=True, indent=4 * ' ')

# would like a try block here
# if the save fails because subdata is too big, try to re-save as a genome-like object that doesn't
# have as many searchable fields
                contig_not_saved = True
                save_wait_time = 1
                while contig_not_saved:
                    try:
                        contig_info = ws_target_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"KBaseGenomes.ContigSet","data":fbaContig,"name": contigref[0]['info'][1],"provenance":contig_provenance}]})
                        contig_not_saved = False
                        fbaGenomeObject['contigset_ref'] = wsoutput + '/' + contigref[0]['info'][1]
                    except biokbase.workspace.client.ServerError as err:
                        rematch1 = re.search('504 Gateway Time-Out',str(err))
                        rematch2 = re.search('subdata size exceeds limit', str(err))
                        if rematch1 != None:
                            time.sleep(save_wait_time)
                            save_wait_time = save_wait_time * 2
                            print >> sys.stderr,contig_info
                            if save_wait_time > 500:
                                print "WS TIMEOUT Unable to save contigset for : " + fbaGenomeObject['id']
                                break
                        elif rematch2 != None:
                            print "Too many subobjects.  Unable to save contigset for : " + fbaGenomeObject['id']
                            print >> sys.stderr,fbaGenomeObject['id'] + ' is too large, skipping for now'
                            break                        
                        else:
                            print "Unable to save contigset for : " + fbaGenomeObject['id']
                            # print exception stack, any useful info
                            print traceback.format_exc()
                            break
                        
                genome_not_saved = True
                save_wait_time = 1
                while genome_not_saved:
                    try:
                        genome_info = ws_target_client.save_objects({"workspace":wsoutput,"objects":[ { "type":"KBaseGenomes.Genome","data":fbaGenomeObject,"name":fbaGenomeObject['id'],"provenance":genome_provenance}]})
                        genome_not_saved = False
                    except biokbase.workspace.client.ServerError as err:
                        rematch1 = re.search('504 Gateway Time-Out',str(err))
                        rematch2 = re.search('subdata size exceeds limit', str(err))
                        if rematch1 != None:
                            time.sleep(save_wait_time)
                            save_wait_time = save_wait_time * 2
                            print >> sys.stderr,genome_info
                            if save_wait_time > 500:
                                print "WS TIMEOUT Unable to save genome for : " + fbaGenomeObject['id']
                                break
                        elif rematch2 != None:
                            print "Too many subobjects.  Unable to save genome for : " + fbaGenomeObject['id']
                            print >> sys.stderr,fbaGenomeObject['id'] + ' is too large, skipping for now'
                            break                        
                        else:
                            print "Unable to save genome for : " + fbaGenomeObject['id']
                            # print exception stack, any useful info
                            print traceback.format_exc()

                end = time.time()
                print >> sys.stderr, "saved KBaseGenome.Genome objects for %s %s" % ( x[1], str(end - start))
                start = time.time()

            else:
                print '            skipping %s, is a %s' % (x[0], x[2])
            object_counter += 1
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('--wsinput', nargs="?", help='workspace name to load from', required=True)
    parser.add_argument('--wsoutput', nargs="?", help='workspace name to load to', required=True)
    parser.add_argument('--skip-existing',action='store_true',help='skip processing genomes which already exist in ws')
    parser.add_argument('--startindex',action='store',type=int, nargs="?", help='Number allows user to take a slice of total genomes in the WS.  Note start must be less end. Both start and end are required if used.  Indexing starts at zero.')
    parser.add_argument('--endindex', action="store",type=int, nargs="?",help='Number that the genome list slice goes up to (including).  If start index is not specified, this gets ignored.  If set to artificially high number it runs to the end of list.')
    parser.add_argument('--skip-dna-sequences',action='store_true',help='skip storing contigset object and feature DNA sequences')
    parser.add_argument('--source-wsinstance', dest="source_wsinstance",nargs="?",help='source workspace instance to use', required=False,action="store",default='https://kbase.us/services/ws/')
    parser.add_argument('--target-wsinstance', dest="target_wsinstance",nargs="?",help='source workspace instance to use', required=False,action="store",default='https://kbase.us/services/ws/')
    parser.add_argument('genomes', action="store", nargs='*')



    try:
        args = parser.parse_args()
    except Exception, e:
        print args
        raise
    print args

    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects

    start_index = None
    end_index = None

    if args.startindex is not None:
        try:
            start_index = int(args.startindex)
        except Exception, e:
            print "Unable to convert startindex to an integer"
            sys.exit(0)
        if args.endindex is not None:
            try:
                end_index = int(args.endindex)
            except Exception, e:
                print "Unable to convert endindex to an integer"
                sys.exit(0)
        else:
            print "ERROR : the start_index was set but there was no corresponding endindex."
            sys.exit()
        if start_index > end_index:
            print "ERROR : the startindex was larger than the endindex."
            sys.exit()
    
    print args.genomes
#    if source_wsinstance is None:
#        source_wsinstance = 'https://kbase.us/services/ws/'

#    if target_wsinstance is None:
#        target_wsinstance = 'https://kbase.us/services/ws/'

    ws_source_client = biokbase.workspace.client.Workspace(args.source_wsinstance)
    ws_target_client = biokbase.workspace.client.Workspace(args.target_wsinstance)

    if args.source_wsinstance == args.target_wsinstance :
        ws_source_client = ws_target_client

    try: 
        retval=ws_target_client.create_workspace({"workspace":args.wsoutput,"globalread":"n","description":"Public Genomes Workspace"})
        print 'created workspace ' + args.wsoutput + ' at ws url ' + ws_target_client.url 
        print retval 
    except biokbase.workspace.client.ServerError as err:
        rematch = re.search('Workspace name ' + args.wsoutput + ' is already in use',str(err))
        if rematch != None:
            #means WS already exists, now need to check on privelages.
            print 'workspace ' + args.wsoutput + ' at ws url ' + ws_target_client.url + ' may already exist, trying to use'
#            ws_target_client.get_permissions(
        else:  #Means another error
            print "E : " + str(e)
            print "x : " + str(x[0])
            raise
    except Exception, e:
        print "E : " + str(e)
        print "x : " + str(x[0])
        raise

#    sys.exit(0)
    copy_richGenome_to_genome(maxNumObjects,args.genomes,args.wsinput,args.wsoutput, start_index, end_index, ws_source_client,ws_target_client)
