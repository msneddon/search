#!/usr/bin/env python
 
import StringIO 
import simplejson 
import sys 
import random 
import re 
import pprint
 
# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/    
reload(sys)
sys.setdefaultencoding("utf-8") 

import biokbase.workspace.client 

pp = pprint.PrettyPrinter(indent=4)

def export_fba_models_from_ws(maxNumObjects, fba_model_list, wsname):
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance 
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws') 
 
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})  
    all_workspaces = [ workspace_object ] 

    workspace_counter = 0
    for n in all_workspaces: 
        workspace_id = n[0]
        workspace_name = n[1] 
#Info Log 
        print fba_model_list 
        objects_list = list() 
        if len(fba_model_list) > 0: 
            names_list = list() 
            for fba_model in fba_model_list: 
                names_list.append({'workspace':wsname,'name':fba_model}) 
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)] 
        else: 
# to do: need to make a few calls to list_objects to capture all of them
            object_count = 1 
            skipNum = 0 
            limitNum = 5000 
            while object_count != 0: 
                this_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseFBA.FBAModel","limit":limitNum,"skip":skipNum}) 
                object_count=len(this_list) 
                skipNum += limitNum 
                objects_list.extend(this_list) 
 
        objects_list.sort() 

        if len(objects_list) > 0:
#Info Log
            print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
            object_counter = 0
 
#            type_dict = dict()

            if maxNumObjects < 1000: 
                objects_list = random.sample(objects_list,maxNumObjects) 
 
            counter = 0
            for x in objects_list: 
#Info log 
#                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name) 
                if "FBAModel" in x[2]:
#                    print "in x-2 spot : " + str(x[2])
                    done = False
                    while not done:
                        try: 
                            fba_model = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}]) 
                            done = True 
                        except Exception, e: 
#Error Log                                                                                                               
                            print str(e) 
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id) 
                    fba_model = fba_model[0] 
#                    print fba_model['data'].keys()                                                                            
                    #[u'gapfillings', u'name', u'source', u'modelcompounds', u'gapgens', u'biomasses', u'template_refs', u'modelcompartments', u'genome_ref', u'type', u'source_id', u'__VERSION__', u'template_ref', u'id', u'modelreactions']

#list (modelreactions) top level FBA Model->ModelReaction(list(modelReactionProteins))->
#ModelReactionProtein(list(ModelReactionProteinSubunit))->
#ModelReactionProteinSubunit(list(feature_refs))->KBaseGenomes.Genome.features.[*].ids



                    fba_model_object = dict()
                    feature_dict = dict()

                    fba_model_object["fba_model_id"] = fba_model['data']['id']

                    if fba_model['data'].has_key('name'):
                        fba_model_object["fba_model_name"] = fba_model['data']['name']

                    if fba_model['data'].has_key('type'):
                        fba_model_object["fba_model_type"] = fba_model['data']['type']

                    if fba_model['data'].has_key('gapfillings'):
                        fba_model_object["number_of_gapfillings"] = len(fba_model['data']['gapfillings'])
                    else:
                        fba_model_object["number_of_gapfillings"] = 0

                    if fba_model['data'].has_key('gapgens'):
                        fba_model_object["number_of_gapgens"] = len(fba_model['data']['gapgens'])
                    else:
                        fba_model_object["number_of_gapgens"] = 0

                    if fba_model['data'].has_key('biomasses'):
                        fba_model_object["number_of_biomasses"] = len(fba_model['data']['biomasses'])
                    else:
                        fba_model_object["number_of_biomasses"] = 0

                    if fba_model['data'].has_key('template_refs'):
                        fba_model_object["number_of_templates"] = len(fba_model['data']['template_refs'])
                    else:
                        fba_model_object["number_of_templates"] = 0

                    if fba_model['data'].has_key('modelcompartments'):
                        fba_model_object["number_of_compartments"] = len(fba_model['data']['modelcompartments'])
                    else:
                        fba_model_object["number_of_compartments"] = 0

                    if fba_model['data'].has_key('modelreactions'):
                        fba_model_object["number_of_reactions"] = len(fba_model['data']['modelreactions'])
                        fba_model_object["reaction_names"] = ' '.join([x['name'] for x in fba_model['data']['modelreactions'] if x.has_key('name') ])
                        fba_model_object["reaction_pathways"]= ' '.join([x['pathway'] for x in fba_model['data']['modelreactions'] if x.has_key('pathway')])
                        fba_model_object["reaction_aliases"] = ' '.join([y for y in x['aliases'] for x in fba_model['data']['modelreactions'] if x.has_key('aliases')])
#NEED TO GET FEATURES.  BUT REFERENCES GENOME SUBOBJECT
#                        if fba_model['data']['modelreactions'].has_key(['modelReactionProteins']):
                        for model_reaction in fba_model['data']['modelreactions']:
                            for model_reaction_protein in model_reaction['modelReactionProteins']:
                                for model_reaction_protein_subunit in model_reaction_protein['modelReactionProteinSubunits']:
                                    for feature_ref in model_reaction_protein_subunit['feature_refs']:
                                        feature_dict[feature_ref]=1                            
                        fba_model_object["number_of_features"] = len(feature_dict.keys())
                        print "NUM FEATURES : " + str(fba_model_object["number_of_features"])
#                            print "FEATURE REFS " + str(fba_model['data']['modelreactions']['modelReactionProteins']['modelReactionProteinSubunits']['feature_refs'])

                    else:
                        fba_model_object["number_of_reactions"] = 0
                        fba_model_object["reaction_names"] = ''
                        fba_model_object["reaction_pathway"] = ''
                        fba_model_object["reaction_aliases"] = ''


                    if fba_model['data'].has_key('modelcompounds'):
                        fba_model_object["number_of_compounds"] = len(fba_model['data']['modelcompounds'])
                        fba_model_object["compound_names"] = ' '.join([x['name'] for x in fba_model['data']['modelcompounds'] if x.has_key('name') ])
                        fba_model_object["compound_ids"] = ' '.join([x['id'] for x in fba_model['data']['modelcompounds'] if x.has_key('id') ])
                        fba_model_object["compound_aliases"] = ' '.join([y for y in x['aliases'] for x in fba_model['data']['modelcompounds'] if x.has_key('aliases')]) 
                    else: 
                        fba_model_object["number_of_compounds"] = 0
                        fba_model_object["compound_names"] = ''
                        fba_model_object["compound_ids"] = '' 
                        fba_model_object["compound_aliases"] = '' 
                    
                    if fba_model['data'].has_key('genome_ref'):
                        #FOLLOW THE REFERENCE
                        print "Genome ref : " + str(fba_model['data']['genome_ref'])
                        try:
                            fba_model = ws_client.get_referenced_objects(fba_model['data']['genome_ref'])
                        except:
                            print "Can't get genome at : " + fba_model['data']['genome_ref']
                    else:
                        #DO WE INDEX THE OBJECT?  DO WE DO THE METAGENOME
                        #ASSUME either genome_ref or metagenome_ref must exist?
                        print "IN ELSE"
                        



#                    pp.pprint("MODEL REACTIONS\n" + str(fba_model['data']['modelreactions']))
#                    pp.pprint("OBJECT\n" + str(fba_model_object))
                    pp.pprint("Feature refs\n" + str(feature_dict.keys()))

#                    if fba_model['data']['type']:
#                        if  type_dict.has_key(fba_model['data']['type']): 
#                            type_dict[fba_model['data']['type']] = type_dict[fba_model['data']['type']] + 1  
#                        else:
#                            type_dict[fba_model['data']['type']] = 1 
#                    else:
#                        if  type_dict.has_key("blank"): 
#                            type_dict["blank"] = type_dict["blank"] + 1  
#                        else:
#                            type_dict["blank"] = 1 
                    counter = counter + 1
                    sys.stdout.write("Counter: " + str(counter)  + " \r" )
                    sys.stdout.flush()
 #       pp.pprint(type_dict)
                            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('fba_models', action="store", nargs='*') 
    args = parser.parse_args() 
    maxNumObjects = sys.maxint 
    if args.maxNumObjects: 
        maxNumObjects = args.maxNumObjects 
 
    wsname = args.wsname[0] 
#Info Log                                                                                                                                                  
    print args.fba_models 
    export_fba_models_from_ws(maxNumObjects,args.fba_models,wsname) 


