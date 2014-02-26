#!/usr/bin/env python

import StringIO
import json
import sys
import re
import random

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

wsname = 'KBasePublicMetagenomes'

def export_comm_from_ws(maxNumObjects):
    #ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    solr_ws_keys = ['object_id','workspace_name','object_name', 'object_type']
    # these are the keys in the solr document
    all_keys = [ 'metagenome_id', 'metagenome_name', 'metagenome_name_sort', 'library_id', 'metagenome_metadata', 'sequence_type', 'seq_method', 'metagenome_created', 'project_id', 'project_name', 'project_name_sort', 'project_description', 'project_created', 'PI_info', 'tech_contact', 'funding_source', 'ncbi_id', 'qiime_id', 'vamps_id', 'greengenes_id', 'sample_id', 'sample_name', 'sample_name_sort', 'sample_created', 'collection_date', 'env_package_type', 'feature', 'biome', 'material', 'location', 'country', 'latitude', 'longitude']
    headerOutFile = open('mgToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(solr_ws_keys + all_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()

    
    outFile = open('mgToSolr.tab', 'w')
    
    # to create a string of values from an arbitrary structure:
    
    def extractValues(d):
    # would want to handle more types (e.g., int, float, list)
        values = [x for x in d.values() if type(x) == unicode ]
    #    print >> sys.stderr, values
        for x in d.values():
    #        print >> sys.stderr, type(x)
            if type(x) == dict:
    #            print >> sys.stderr, x
                subvalues = extractValues(x)
                values.extend(subvalues)
        return values
    
    workspace_counter = 0
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
    
                if "Metagenome" in x[2]:
    
                    done = False
    
                    object_type = x[2]
    
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            mg = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    #print json.dumps(mg['data'], sort_keys=True, indent=4, separators=(',',': '))
                    mg = mg[0]
                    #print mg['data'].keys()
                    
                    search_values=dict()
                    for key in all_keys:
                        search_values[key] = ''
    
                    mg_scalar_keys = [ 'metagenome_id', 'metagenome_name', 'library_id', 'sequence_type', 'seq_method' ]
    
                    for key in mg_scalar_keys:
                        if mg['data'].has_key(key):
                            search_values[key] = mg['data'][key]
                        else:
                            search_values[key]=''
    
                    search_values['metagenome_created'] = mg['data']['created']
                    search_values['project_created'] = ''
                    if mg['data']['project'].has_key('created'):
                        search_values['project_created'] = mg['data']['project']['created']
                    search_values['sample_created'] = mg['data']['sample']['created']
    
                    pat = re.compile(r'\s+')
    
                    sample_scalar_keys = [ 'sample_id', 'sample_name', 'collection_date', 'env_package_type', 'feature', 'biome', 'material', 'location', 'country', 'latitude', 'longitude' ]
    
                    for key in sample_scalar_keys:
                        if mg['data']['sample'].has_key(key):
                            search_values[key] = pat.sub(' ',str(mg['data']['sample'][key]))
                        else:
                            search_values[key]=''
    
    #print pat.sub('', s)
                    project_scalar_keys = [ 'project_id', 'project_name',  'project_description', 'funding_source', 'ncbi_id', 'qiime_id', 'vamps_id', 'greengenes_id' ]
    
                    for key in project_scalar_keys:
                        if mg['data']['project'].has_key(key):
                            search_values[key] = pat.sub(' ',mg['data']['project'][key])
                        else:
                            search_values[key]=''
    
                    if mg['data'].has_key('metadata'):
    #                    search_values['metagenome_metadata']  = str(mg['data']['metadata'])
                        search_values['metagenome_metadata']  = pat.sub(' ',' '.join(extractValues(mg['data']['metadata'])))
    
                    if mg['data']['project'].has_key('PI_info'):
                        search_values['PI_info']  = pat.sub(' ',str(' '.join(mg['data']['project']['PI_info'].values())))
                    if mg['data']['project'].has_key('tech_contact'):
                        search_values['tech_contact']  = pat.sub(' ',str(' '.join(mg['data']['project']['tech_contact'].values())))
    
                    object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(mg['info'][0])
                    object_name = str(mg['info'][1])

                    search_values['metagenome_name_sort'] = "_".join(search_values['metagenome_name'].lower().split())
                    search_values['project_name_sort'] = "_".join(search_values['project_name'].lower().split())
                    search_values['sample_name_sort'] = "_".join(search_values['sample_name'].lower().split())

                    outBuffer = StringIO.StringIO()
    
                    try:
                        solr_strings = [object_id,workspace_name,object_name,object_type]
                        solr_strings += [ unicode(str(search_values[x])) for x in all_keys ]
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
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    args = parser.parse_args()
    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects

    export_comm_from_ws(maxNumObjects)
