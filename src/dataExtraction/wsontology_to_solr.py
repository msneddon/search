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

#auth_token = biokbase.auth.Token(user_id='***REMOVED***', password='***REMOVED***')
#ws_client = biokbase.workspace.client.Workspace('http://localhost:7058', user_id='***REMOVED***', password='***REMOVED***')
ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')

progress = 0.0

all_workspaces = ws_client.list_workspace_info({})

print "There are %d visible workspaces." % len(all_workspaces)

#print all_workspaces

outFile = open('ontologyToSolr.tab', 'w')

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

workspace_counter = 0
#for n in all_workspaces:
for n in all_workspaces:
    print "Finished checking %s of all visible workspaces" % (str(100.0 * float(workspace_counter)/len(all_workspaces)) + " %")

    workspace_id = n[0]
    workspace_name = n[1]
# should just get pointer to workspace directly
    if (workspace_name != 'KBasePublicOntologies'):
        print "Skipping workspace %s" % workspace_name
        continue

    objects_list = ws_client.list_objects({"ids": [workspace_id]})
    if len(objects_list) > 0:
        print "\tWorkspace %s has %d objects" % (workspace_name, len(objects_list))
        object_counter = 0

        for x in objects_list:
            print "\t\tFinished checking %s, done with %s of all objects in %s" % (x[0], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)

            if "Ontology" in x[2]:

                done = False

                object_type = x[2]

#                sys.stderr.write(str(x)+"\n")
                while not done:
                    try:
                        wsobject = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                        done = True
                    except Exception, e:
                        print str(e)
                        print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)

                wsobject = wsobject[0]
                
                # these are the keys in the solr document
                # (not including the default keys)
                all_keys = [ 'ontology_id', 'ontology_type', 'ontology_domain', 'ontology_description', 'gene_list', 'evidence_codes' ]

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

                if wsobject['data'].has_key('evidence_codes'):
                    search_values['evidence_codes'] = ' '.join(wsobject['data']['evidence_codes'])

                if wsobject['data'].has_key('gene_list'):
#                    search_values['gene_list'] =' '.join(extractValues(wsobject['data']['gene_list']))
                    for key in wsobject['data']['gene_list']:
                        search_values['gene_list'] += key + ': ' + ' '.join(wsobject['data']['gene_list'][key]) + ' '

                object_id = 'kb|ws.' + str(workspace_id) + '.obj.' + str(wsobject['info'][0])

                outBuffer = StringIO.StringIO()

                try:
                    solr_strings = [object_id,workspace_name,object_type]
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


