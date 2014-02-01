#!/usr/bin/env python

# this script takes Gwas WS objects and creates a tab-delimited import file for solr
import StringIO
import json
import sys
import random

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

wsname = 'KBasePublicGwasData'

def export_gwas_from_ws(maxNumObjects):
    #ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    # ranjan's Gwas objects are currently in Gavin's dev workspace
#    ws_client = biokbase.workspace.client.Workspace('http://140.221.84.209:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    #print all_workspaces
    
    # the keys in the solr schema
    # print out a header file
    # data fields must be printed in same order
    solr_ws_keys = ['object_id','workspace_name','object_type', 'object_name']
    solr_keys = [ 'kbase_genome_name', 'kbase_genome_id', 'source_genome_name', 'source', 'GwasPopulation_description', 'ecotype_details', 'GwasPopulation_obj_id', 'filetype', 'comment', 'assay', 'originator', 'GwasPopulationVariation_parent_obj_id', 'trait_ontology_id', 'trait_name','unit_of_measure','protocol','num_population','GwasPopulationStructure_obj_id','GwasPopulationKinship_obj_id','pvaluecutoff', 'GwasTopVariations_obj_id','distance_cutoff','genes','genes_snp_list']
    headerOutFile = open('gwasToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(solr_ws_keys + solr_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()
    
    outFile = open('gwasToSolr.tab', 'w')
    
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        objects_list = ws_client.list_objects({"ids": [workspace_id]})
        if len(objects_list) > 0:
            print "\tWorkspace %s has %d objects" % (workspace_name, len(objects_list))
            object_counter = 0
    
            if maxNumObjects < 1000 :
                objects_list = random.sample(objects_list,maxNumObjects)
    
            for x in objects_list:
                print "\t\tFinished checking %s, done with %s of all objects in %s" % (x[0], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
    
                if "Gwas" in x[2]:
    
                    done = False
    
                    object_type = x[2]
                    object_name = x[1]
    
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            gwas = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    #print json.dumps(gwas['data'], sort_keys=True, indent=4, separators=(',',': '))
                    gwas = gwas[0]
                    #print gwas['info']
                    
    # [u'originator', u'comment', u'assay', u'GwasPopulation_obj_id', u'variation_file', u'filetype', u'genome', u'GwasPopulationVariation_obj_id']
    
                    object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(gwas['info'][0])
    
                    search_values=dict()
                    for key in solr_keys:
                        search_values[key] = ''
    
                    #scalar_keys = [ 'GwasPopulation_description', 'GwasPopulation_obj_id', 'filetype', 'comment', 'assay', 'originator', 'trait_ontology_id', 'trait_name','unit_of_measure','protocol']
                    scalar_keys = [ 'GwasPopulation_description', 'GwasPopulation_obj_id', 'filetype', 'comment', 'assay', 'originator', 'GwasPopulationVariation_parent_obj_id', 'trait_ontology_id', 'trait_name','unit_of_measure','protocol','num_population','GwasPopulationStructure_obj_id','GwasPopulationKinship_obj_id','pvaluecutoff', 'GwasTopVariations_obj_id','distance_cutoff']
    
                    # handle generic scalar keys
                    for key in scalar_keys:
                        if gwas['data'].has_key(key):
                            search_values[key] = gwas['data'][key]
                        else:
                            search_values[key]=''
    
                    # handle special keys
                    if gwas['data'].has_key('GwasPopulationVariation_obj_id'):
                        search_values['GwasPopulationVariation_parent_obj_id'] = gwas['data']['GwasPopulationVariation_obj_id']
    
                    if gwas['data'].has_key('genome'):
                        search_values['kbase_genome_name'] = gwas['data']['genome']['kbase_genome_name']
                        search_values['kbase_genome_id'] = gwas['data']['genome']['kbase_genome_id']
                        search_values['source_genome_name'] = gwas['data']['genome']['source_genome_name']
                        search_values['source'] = gwas['data']['genome']['source']
    
                    if gwas['data'].has_key('ecotype_details'):
                        for ed in gwas['data']['ecotype_details']:
    # there are some issues with character encoding here, not sure how to resolve
    # (not a showstopper)
                            search_values['ecotype_details']  += ' '.join(ed.values())
    #                        search_values['ecotype_details'] = search_values['ecotype_details'] + ecotype_details
    
                    if gwas['data'].has_key('genes'):
                        search_values['genes'] = ' '.join( [ gene[1] + ' ' + gene[2] + ' ' + gene[3] + ' '  for gene in gwas['data']['genes'] ] )
                    if gwas['data'].has_key('genes_snp_list'):
                        search_values['genes_snp_list'] = ' '.join([ gene[1] + ' ' + gene[2] + ' ' + gene[4] + ' '  for gene in gwas['data']['genes_snp_list'] ])
    
                   # need to embed GwasTopVariations data in the GwasGeneList object
                    if gwas['data'].has_key('GwasTopVariations_obj_id'):
                        gwasTopVariation = ws_client.get_objects([{"wsid": str(workspace_id), "name": gwas['data']['GwasTopVariations_obj_id']}])
                        # only retrieving one object
                        gwasTopVariation = gwasTopVariation[0]
                        topVariation_scalar_keys = [ 'comment', 'assay', 'originator', 'trait_ontology_id', 'trait_name','protocol']
                        for key in topVariation_scalar_keys:
                            if gwasTopVariation['data'].has_key(key):
                                search_values[key] = gwasTopVariation['data'][key]
    
                        if gwasTopVariation['data'].has_key('genome'):
                            search_values['kbase_genome_name'] = gwasTopVariation['data']['genome']['kbase_genome_name']
                            search_values['kbase_genome_id'] = gwasTopVariation['data']['genome']['kbase_genome_id']
                            search_values['source_genome_name'] = gwasTopVariation['data']['genome']['source_genome_name']
                            search_values['source'] = gwasTopVariation['data']['genome']['source']
    
                    outBuffer = StringIO.StringIO()
    
                    try:
                        solr_strings = [object_id,workspace_name,object_type,object_name]
                        solr_strings += [ unicode(str(search_values[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n")
    #                    outBuffer.write(unicode(str(object_id) + '\t' + str(workspace_name) + '\t' +
    #                                        str(object_type) + '\t' + str(search_values['kbase_genome_name']) + '\t' + str(search_values['kbase_genome_id']) + '\t' +
    #                                        str(search_values['source_genome_name']) + '\t' + str(search_values['source']) + '\t' +
    #                                        str(search_values['GwasPopulation_description']) + '\t' + str(search_values['ecotype_details']) + '\t' + str(search_values['GwasPopulation_obj_id']) + '\t' + str(search_values['filetype']) + '\t' +
    #                                        str(search_values['comment']) + '\t' + str(search_values['assay']) + '\t' +
    #                                        str(search_values['originator']) + '\t' + str(search_values['GwasPopulationVariation_obj_id']) + "\n"))
                    except Exception, e:
                        print str(e)
    #                    print search_values
                        print "Failed trying to write to string buffer."
    
    
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()
                else:
                    print '            skipping %s, is a %s' % (x[0], x[2])
                object_counter += 1
    outFile.close()
    
if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    args = parser.parse_args()

    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    export_gwas_from_ws(maxNumObjects)
