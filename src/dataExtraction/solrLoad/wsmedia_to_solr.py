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

solr_keys = ['object_id', 'object_type', 'object_workspace', 'object_name','media_id','media_name','media_source_id','media_source','protocol_link','is_defined','is_minimal','is_aerobic','media_type','pH_data','temperature','atmosphere','number_of_compounds','compound_ids','compound_names','compound_abbreviations']


def export_medias_from_ws(maxNumObjects, media_list, wsname):
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance 
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws') 
 
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})  
    all_workspaces = [ workspace_object ] 

    headerOutFile = open('MediasToSolr.tab.headers', 'w') 
    print >> headerOutFile, "\t".join(solr_keys) 
    #print >> headerOutFile, "\n"                                                                                                                
    headerOutFile.close() 

    outFile = open('MediasToSolr.tab', 'w')

    workspace_counter = 0
    for n in all_workspaces: 
        workspace_id = n[0]
        workspace_name = n[1] 
#Info Log 
        print media_list 
        objects_list = list() 
        if len(media_list) > 0: 
            names_list = list() 
            for media in media_list: 
                names_list.append({'workspace':wsname,'name':media}) 
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)] 
        else: 
# to do: need to make a few calls to list_objects to capture all of them
            object_count = 1 
            skipNum = 0 
            limitNum = 5000 
            while object_count != 0: 
                this_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseBiochem.Media","limit":limitNum,"skip":skipNum}) 
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
                if "Media" in x[2]:
                    done = False
                    while not done:
                        try: 
                            media = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}]) 
                            done = True 
                        except Exception, e: 
#Error Log                                                                                                               
                            print str(e) 
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id) 
                    media = media[0] 
#                    print media['data'].keys()                                                                            

                    media_object = dict()

                    media_object['object_id'] = 'kb|ws.' + str(media['info'][6]) + '.obj.' + str(media['info'][0]) 
                    media_object['object_workspace'] = media['info'][7] 
                    media_object['object_type'] = media['info'][2] 
                    media_object['object_name'] = media['info'][1] 

                    media_object["media_id"] = media['data']['id']

                    if media['data'].has_key('name'):
                        media_object["media_name"] = media['data']['name']

                    if media['data'].has_key('source_id'):
                        media_object["media_source_id"] = media['data']['source_id']
                    else:
                        media_object["media_source_id"] = ''

                    if media['data'].has_key('source'):
                        media_object["media_source"] = media['data']['source']
                    else:
                        media_object["media_source"] = ''

                    if media['data'].has_key('protocol_link'):
                        media_object["protocol_link"] = media['data']['protocol_link']
                    else:
                        media_object["protocol_link"] = ''

                    if media['data'].has_key('isDefined'):
                        media_object["is_defined"] = media['data']['isDefined']

                    if media['data'].has_key('isMinimal'):
                        media_object["is_minimal"] = media['data']['isMinimal']

                    if media['data'].has_key('isAerobic'):
                        media_object["is_aerobic"] = media['data']['isAerobic']
                    else:
                        media_object["is_aerobic"] = ''

                    if media['data'].has_key('type'):
                        media_object["media_type"] = media['data']['type']

                    if media['data'].has_key('pH_data'):
                        media_object["pH_data"] = media['data']['pH_data']
                    else:
                        media_object["pH_data"] = ''

                    if media['data'].has_key('temperature'):
                        media_object["temperature"] = media['data']['temperature']
                    else:
                        media_object["temperature"] = ''

                    if media['data'].has_key('atmosphere'):
                        media_object["atmosphere"] = media['data']['atmosphere']
                    else:
                        media_object["atmosphere"] = ''

                    if media['data'].has_key('mediacompounds'): 
                        compound_objects_set = set() #Example value from compound_ref in mediacompounds -  489/6/1/compounds/id/cpd00030
                                                       #Keys of dict is ws_id of biochemistry (first three values of ref),# values are the biochemistry object.
#                        compound_values_dict = dict() #Example value from compound_ref in mediacompounds -  489/6/1/compounds/id/cpd00030
#                                                      #Keys of dict is ws_id of biochemistry (first three values of ref), values are dict [compound_id][abbreviation and name as keys]
                        compound_ids_set = set()
                        compound_names_set = set()
                        compound_abbreviations_set = set()
                        

                        #get stubbed out dictionaries for media compounds (Minimizes the number ws_get operations on Biochem)
                        for media_compound in media['data']['mediacompounds']:
                            compound_ref_elements = media_compound["compound_ref"].split("/")
                            biochem_ws_id = "/".join(compound_ref_elements[0:3])
                            compound_id = compound_ref_elements[5]
                            compound_objects_set.add(biochem_ws_id)
                            compound_ids_set.add(compound_id)
#                            compound_values_dict[biochem_ws_id][compound_id]={"name":"","abbreviation":""}
                            
                        #Now go through the stubbed out compounds and populate them
                        for biochem_object_path in compound_objects_set:
                            [bws_id, bws_object_id, bws_object_ver] = biochem_object_path.split("/")
                            try: 
                                biochem = ws_client.get_objects([{"wsid": str(bws_id), "objid": str(bws_object_id), "ver": str(bws_object_ver)}])[0] 
                                for compound in biochem['data']['compounds']:
                                    if (compound['id'] in compound_ids_set):
                                        compound_names_set.add(compound['name'])
                                        compound_abbreviations_set.add(compound['abbreviation'])
                            except Exception, e: 
                                print "Can't get biochemistry at : " + biochem_object_path + ". Not indexing this media." 
                                print "ERROR: " + str(e) 
                                print("Unexpected error:", sys.exc_info()[0])
                                continue 
                        media_object["number_of_compounds"] = len(media['data']['mediacompounds'])
#                        media_object["number_of_compounds"] = len(compound_ids_set)
                        media_object["compound_ids"] =  " ".join(compound_ids_set)
                        media_object["compound_names"] =  " ".join(compound_names_set)
                        media_object["compound_abbreviations"] =  " ".join(compound_abbreviations_set)
                    else:
                        media_object["number_of_compounds"] = 0
                        media_object["compound_ids"] =  " "
                        media_object["compound_names"] =  " "
                        media_object["compound_abbreviations"] =  " "

                    counter = counter + 1
#                    sys.stdout.write("Counter: " + str(counter)  + " \r" )
                    sys.stdout.write("Counter Time : " + str(counter) + " : Media " + media_object["media_id"] + " : " + str(datetime.datetime.now()) + "\n")
                    sys.stdout.flush()

                    outBuffer = StringIO.StringIO()
                    try: 
                        solr_strings = [ unicode(str(media_object[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n") 
#                        print outBuffer.getvalue()
                    except Exception, e:
#Warning Log                                                                                                                                     
                        print "Exception : " + str(e)
                        print "Failed trying to write to string buffer for media " + media_object['media_id']
                        print("Unexpected error:", sys.exc_info()[0])
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close() 
    outFile.close() 
                            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('medias', action="store", nargs='*') 
    args = parser.parse_args() 
    maxNumObjects = sys.maxint 
    if args.maxNumObjects: 
        maxNumObjects = args.maxNumObjects 
 
    wsname = args.wsname[0] 
#Info Log                                                                                                                                                  
    print args.medias 
    sys.stdout.write("START TIME : " + str(datetime.datetime.now())+ "\n")
    export_medias_from_ws(maxNumObjects,args.medias,wsname) 
    sys.stdout.write("END TIME : " + str(datetime.datetime.now())+ "\n")


