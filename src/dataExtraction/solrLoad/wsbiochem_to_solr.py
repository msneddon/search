#!/usr/bin/env python
 
import StringIO 
import simplejson 
import sys 
import random 
import re 
import pprint
import datetime
 
# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/    
reload(sys)
sys.setdefaultencoding("utf-8") 

import biokbase.workspace.client 

pp = pprint.PrettyPrinter(indent=4)

solr_keys = ['object_id', 'object_type', 'object_workspace', 'object_name','biochem_id','biochem_name','biochem_description', 'number_of_compartments','compartment_names','number_of_compounds','compound_ids','compound_names','compound_abbreviations','compound_aliases','number_of_reactions','reaction_ids','reaction_names','reaction_abbreviations','reaction_aliases','number_of_cues','cue_ids','cue_names','cue_abbreviations']

def export_biochems_from_ws(maxNumObjects, biochem_list, wsname):
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance 
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws') 
 
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})  
    all_workspaces = [ workspace_object ] 

    headerOutFile = open('BiochemsToSolr.tab.headers', 'w') 
    print >> headerOutFile, "\t".join(solr_keys) 
    #print >> headerOutFile, "\n"                                                                                                                
    headerOutFile.close() 

    outFile = open('BiochemsToSolr.tab', 'w')

    workspace_counter = 0
    for n in all_workspaces: 
        workspace_id = n[0]
        workspace_name = n[1] 
#Info Log 
        print biochem_list 
        objects_list = list() 
        if len(biochem_list) > 0: 
            names_list = list() 
            for biochem in biochem_list: 
                names_list.append({'workspace':wsname,'name':biochem}) 
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)] 
        else: 
# to do: need to make a few calls to list_objects to capture all of them
            object_count = 1 
            skipNum = 0 
            limitNum = 5000 
            while object_count != 0: 
                this_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseBiochem.Biochemistry","limit":limitNum,"skip":skipNum}) 
                object_count=len(this_list) 
                skipNum += limitNum 
                objects_list.extend(this_list) 
 
        objects_list.sort() 

        if len(objects_list) > 0:
#Info Log
            print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
            object_counter = 0
 
            if maxNumObjects < 1000: 
                objects_list = random.sample(objects_list,maxNumObjects) 
 
            counter = 0
            for x in objects_list: 
#Info log 
#                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name) 
                if "Biochemistry" in x[2]:
                    done = False
                    while not done:
                        try: 
                            biochem = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}]) 
                            done = True 
                        except Exception, e: 
#Error Log                                                                                                               
                            print str(e) 
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id) 
                    biochem = biochem[0] 
#                    print biochem['data'].keys()                                                                            

                    biochem_object = dict()

                    biochem_object['object_id'] = 'kb|ws.' + str(biochem['info'][6]) + '.obj.' + str(biochem['info'][0]) 
                    biochem_object['object_workspace'] = biochem['info'][7] 
                    biochem_object['object_type'] = biochem['info'][2] 
                    biochem_object['object_name'] = biochem['info'][1] 

                    biochem_object["biochem_id"] = biochem['data']['id']

                    if biochem['data'].has_key('name'):
                        biochem_object["biochem_name"] = biochem['data']['name']
                    else:
                        biochem_object["biochem_name"] = ''

                    if biochem['data'].has_key('description'):
                        biochem_object["biochem_description"] = biochem['data']['description']
                    else:
                        biochem_object["biochem_description"] = ''

                    if biochem['data'].has_key('compartments'): 
                        biochem_object["number_of_compartments"] = len(biochem['data']['compartments']) 
                        biochem_object["compartment_names"] = ' '.join([x['name'] for x in biochem['data']['compartments'] if x.has_key('name') ]) 
                    else: 
                        biochem_object["number_of_compartments"] = 0
                        biochem_object["compartment_names"] = ''

                    if biochem['data'].has_key('compounds'):
                        biochem_object["number_of_compounds"] = len(biochem['data']['compounds'])
                        biochem_object["compound_ids"] = ' '.join([x['name'] for x in biochem['data']['compounds'] if x.has_key('id') ]) 
                        biochem_object["compound_names"] = ' '.join([x['name'] for x in biochem['data']['compounds'] if x.has_key('name') ]) 
                        biochem_object["compound_abbreviations"] = ' '.join([x['name'] for x in biochem['data']['compounds'] if x.has_key('abbreviation')])
                    else:
                        biochem_object["number_of_compounds"] = 0
                        biochem_object["compound_ids"] = '' 
                        biochem_object["compound_names"] = '' 
                        biochem_object["compound_abbreviations"] = ''

                    if biochem['data'].has_key('compound_aliases'):
                        alias_dict = biochem['data']['compound_aliases']
                        aliases = set()
                        for compound_id in alias_dict.keys():
                            for alias_source in alias_dict[compound_id].keys():
                                for alias in alias_dict[compound_id][alias_source]:
                                    aliases.add(alias)
                        biochem_object["compound_aliases"] = " ".join(aliases)
                    else:
                        biochem_object["compound_aliases"] = ""

                    if biochem['data'].has_key('reactions'):
                        biochem_object["number_of_reactions"] = len(biochem['data']['reactions'])
                        biochem_object["reaction_ids"] = ' '.join([x['name'] for x in biochem['data']['reactions'] if x.has_key('id') ]) 
                        biochem_object["reaction_names"] = ' '.join([x['name'] for x in biochem['data']['reactions'] if x.has_key('name') ]) 
                        biochem_object["reaction_abbreviations"] = ' '.join([x['name'] for x in biochem['data']['reactions'] if x.has_key('abbreviation')])
                    else:
                        biochem_object["number_of_reactions"] = 0
                        biochem_object["reaction_ids"] = '' 
                        biochem_object["reaction_names"] = '' 
                        biochem_object["reaction_abbreviations"] = ''

                    if biochem['data'].has_key('reaction_aliases'):
                        alias_dict = biochem['data']['reaction_aliases']
                        aliases = set()
                        for reaction_id in alias_dict.keys():
                            for alias_source in alias_dict[reaction_id].keys():
                                for alias in alias_dict[reaction_id][alias_source]:
                                    aliases.add(alias)
                        biochem_object["reaction_aliases"] = " ".join(aliases)
                    else:
                        biochem_object["reaction_aliases"] = ""

                    if biochem['data'].has_key('cues'): 
                        biochem_object["number_of_cues"] = len(biochem['data']['cues'])
                        biochem_object["cue_ids"] = ' '.join([x['name'] for x in biochem['data']['cues'] if x.has_key('id') ])
                        biochem_object["cue_names"] = ' '.join([x['name'] for x in biochem['data']['cues'] if x.has_key('name') ])
                        biochem_object["cue_abbreviations"] = ' '.join([x['name'] for x in biochem['data']['cues'] if x.has_key('abbreviation')])
                    else:
                        biochem_object["number_of_cues"] = 0
                        biochem_object["cue_ids"] = ''
                        biochem_object["cue_names"] = ''
                        biochem_object["cue_abbreviations"] = ''

                    counter = counter + 1
#                    sys.stdout.write("Counter: " + str(counter)  + " \r" )
                    sys.stdout.write("Counter Time : " + str(counter) + " : Biochem " + biochem_object["biochem_id"] + " : " + str(datetime.datetime.now()) + "\n")
                    sys.stdout.flush()

                    outBuffer = StringIO.StringIO()
                    try: 
                        solr_strings = [ unicode(str(biochem_object[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n") 
#                        print outBuffer.getvalue()
                    except Exception, e:
#Warning Log                                                                                                                                     
                        print "Exception : " + str(e)
                        print "Failed trying to write to string buffer for biochem " + biochem_object['biochem_id']
                        print("Unexpected error:", sys.exc_info()[0])
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close() 
    outFile.close() 
                            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('biochems', action="store", nargs='*') 
    args = parser.parse_args() 
    maxNumObjects = sys.maxint 
    if args.maxNumObjects: 
        maxNumObjects = args.maxNumObjects 
 
    wsname = args.wsname[0] 
#Info Log                                                                                                                                                  
    print args.biochems 
    sys.stdout.write("START TIME : " + str(datetime.datetime.now())+ "\n")
    export_biochems_from_ws(maxNumObjects,args.biochems,wsname) 
    sys.stdout.write("END TIME : " + str(datetime.datetime.now())+ "\n")


