#!/usr/bin/env python

# this script takes ontology WS objects and creates tab-delimited import files for solr
import StringIO
import json
import sys
import re

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client
import biokbase.cdmi.client

wsname = 'KBasePublicOntologies'

# to create a string of values from an arbitrary structure:

def extractValues(d):
# would want to handle more types (e.g., int, float, list)
    values = [x for x in d.values() if type(x) in [ str, unicode ]  ]
#    print >> sys.stderr, values
    for x in d.values():
#        print >> sys.stderr, type(x)
        if type(x) == dict:
#            print >> sys.stderr, x
            subvalues = extractValues(x)
            values.extend(subvalues)
    return values


def export_ontology_from_ws():
    # production instance
    cdmi_api = biokbase.cdmi.client.CDMI_API()
    cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI()
    # private instance
    #cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
    #cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')

    genome_entities = cdmi_entity_api.all_entities_Genome(0,15000,['id','scientific_name','source_id'])

    #ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    all_keys = [ 'object_id','workspace_name','object_type','object_name', 'ontology_id', 'ontology_type', 'ontology_domain', 'ontology_description', 'ontology_description_sort', 'gene_list', 'evidence_codes' ]
    
    headerOutFile = open('ontologyToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(all_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()

    outFile = open('ontologyToSolr.tab', 'w')
    
    workspace_counter = 0
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        objects_list = ws_client.list_objects({"ids": [workspace_id]})
        if len(objects_list) > 0:
            print "\tWorkspace %s has %d objects" % (workspace_name, len(objects_list))
            object_counter = 0
    
            for x in objects_list:
                print "\t\tFinished checking %s, done with %s of all objects in %s" % (x[0], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
    
                if "Ontology" in x[2]:
    
                    done = False
    
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            wsobject = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    wsobject = wsobject[0]
                    
                    # make sure every column gets a value
                    search_values=dict()
                    for key in all_keys:
                        search_values[key] = ''
    
                    scalar_keys = [ 'ontology_id', 'ontology_type', 'ontology_domain', 'ontology_description' ]
    
                    for key in scalar_keys:
                        if wsobject['data'].has_key(key):
                            search_values[key] = wsobject['data'][key]
                        else:
                            search_values[key]=''
    
                    if wsobject['data'].has_key('ontology_description'):
                        search_values['ontology_description_sort'] = "_".join(wsobject['data']['ontology_description'].lower().split())

                    if wsobject['data'].has_key('evidence_codes'):
                        search_values['evidence_codes'] = ' '.join(wsobject['data']['evidence_codes'])
    
                    if wsobject['data'].has_key('gene_list'):
    #                    search_values['gene_list'] =' '.join(extractValues(wsobject['data']['gene_list']))
                        for key in wsobject['data']['gene_list']:
                            try:
                                search_values['gene_list'] += key + ' : ' + genome_entities[key]['scientific_name'] + ' : ' + ' '.join(wsobject['data']['gene_list'][key]) + ' '
                            except Exception, e:
                                print >> sys.stderr, e
                                print >> sys.stderr, 'perhaps genome ' + key + ' was not found'
    
                    search_values['object_id'] = 'kb|ws.' + str(workspace_id) + '.obj.' + str(wsobject['info'][0])
                    search_values['object_name'] = str(wsobject['info'][1])
                    search_values['workspace_name'] = workspace_name
                    search_values['object_type'] = x[2]
    
                    outBuffer = StringIO.StringIO()
    
                    try:
                        solr_strings = [ unicode(str(search_values[x])) for x in all_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n")
                    except Exception, e:
                        print str(e)
    #                    print search_values
                        print "Failed trying to write to string buffer."
    
    
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()
                else:
                    print '            skipping %s, is a %s' % (x[0], x[2])
                object_counter += 1
        workspace_counter += 1
    outFile.close()

if __name__ == "__main__":

    import argparse

    export_ontology_from_ws()
