#!/usr/bin/env python

import StringIO
import simplejson
import sys
import random
import re

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import biokbase.workspace.client

solr_keys = ["object_id", "object_version", "object_workspace", "object_type", "object_name", "model_id", "model_source", "model_source_id", "model_name", "model_type", "model_genome_ref", "biomasses", "compartments" , 'reaction_name', 'reaction_id', 'reaction_ref', 'reaction_direction', 'reaction_pathway', 'reaction_features', 'compound_id', 'compound_name', 'compound_ref', 'compound_formula', 'modelcompartment_ref']
solr_model_keys = ["object_id", "object_version", "object_workspace", "object_type", "object_name", "model_id", "model_source", "model_source_id", "model_name", "model_type", "model_genome_ref", "biomasses", "compartments" ]
solr_reaction_keys = ['reaction_name', 'reaction_id', 'reaction_direction', 'reaction_pathway', 'reaction_ref', 'reaction_features', 'modelcompartment_ref']
solr_compound_keys = ['compound_id', 'compound_name', 'compound_ref', 'compound_formula', 'modelcompartment_ref']
#solr_keys = ["object_id" , "workspace_name" , "object_type" , 'object_name', "genome_id", "feature_id", "genome_source" , "genome_source_id" , "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids"]
#solr_genome_keys = ["genome_id", "genome_source" , "genome_source_id" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications"]
#solr_feature_keys = ["feature_id",  "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids"]


def export_models_from_ws(maxNumObjects,model_list,wsname):
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    headerOutFile = open('modelsToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(solr_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()

    outFile = open('modelsToSolr.tab', 'w')
    
    workspace_counter = 0
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        print model_list
        objects_list = list()
        if len(model_list) > 0:
            names_list = list()
            for model in model_list:
                names_list.append({'workspace':wsname,'name':model})
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)]
        else:
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
            print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
            object_counter = 0
    
            if maxNumObjects < 1000:
                objects_list = random.sample(objects_list,maxNumObjects)
    
            for x in objects_list:
                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
    
#                numeric_id = (x[1].split('.'))[1]
#                print >> sys.stderr, numeric_id
#                if numeric_id < 475:
#                    print >> sys.stderr, 'skipping ' + x[1] + ' for now'
#                    continue

                if "Model" in x[2]:
                    done = False
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            model = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    #print json.dumps(genome['data'], sort_keys=True, indent=4, separators=(',',': '))
                    model = model[0]
                    #print model['data'].keys()
                    
                    modelObject = dict()

                    for key in solr_reaction_keys:
                        modelObject[key] = ''
                    for key in solr_compound_keys:
                        modelObject[key] = ''

                    modelObject['object_id'] = 'kb|ws.' + str(model['info'][6]) + '.obj.' + str(model['info'][0])
                    modelObject['object_workspace'] = model['info'][7]
                    modelObject['object_type'] = model['info'][2]
                    modelObject['object_name'] = model['info'][1]
                    modelObject['object_version'] = model['info'][4]

                    model_scalar_keys = ['id', 'source', 'source_id', 'name', 'type', 'genome_ref']
                    for key in model_scalar_keys:
                        try:
                            modelObject['model_'+key] = str(model['data'][key])
                        except:
                            modelObject['model_'+key] = ''
    
                    # special keys

                    modelObject['biomasses']=''
                    modelObject['compartments']=''

                    # write to import file

                    outBuffer = StringIO.StringIO()

                    try:
                        solr_strings = [ unicode(str(modelObject[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n")
                    except Exception, e:
                        print str(e)
                        print "Failed trying to write to string buffer for model " + modelObject['object_id']
                
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()

                    # will probably loop over some substructures
                    # but not sure how yet

                    for index,reactionObj in enumerate(model['data']['modelreactions']):
                        reactionObject=dict()
                        reaction = reactionObj
    
                        for key in solr_model_keys:
                            reactionObject[key] = modelObject[key]
                        for key in solr_compound_keys:
                            reactionObject[key] = modelObject[key]

                        reactionObject['object_id'] = 'kb|ws.' + str(model['info'][6]) + '.obj.' + str(model['info'][0]) + '/modelreactions/' + str(index)
#                        reactionObject['object_workspace'] = model['info'][7]
#                        reactionObject['object_type'] = model['info'][2]
                        reactionObject['object_type'] = 'KBaseFBA.ModelReaction'
#                        reactionObject['object_name'] = model['info'][1]
#                        reactionObject['object_version'] = model['info'][4]

                        reaction_scalar_keys = ['name', 'id', 'direction', 'pathway']
                        for key in reaction_scalar_keys:
                            try:
                                reactionObject['reaction_'+key] = str(reaction[key])
                            except:
                                reactionObject['reaction_'+key] = ''
    
                        reaction_scalar_keys = ['reaction_ref', 'modelcompartment_ref']
                        for key in reaction_scalar_keys:
                            try:
                                reactionObject[key] = str(reaction[key])
                            except:
                                reactionObject[key] = ''
    
                        # special keys

                        reactionObject['reaction_features']=''
                        for protein in reaction['modelReactionProteins']:
                            for subunit in protein['modelReactionProteinSubunits']:
                                reactionObject['reaction_features'] += ';'.join(subunit['feature_refs'])

                        outBuffer = StringIO.StringIO()
                
                        try:
                            solr_strings = [ unicode(str(reactionObject[x])) for x in solr_keys ]
                            solr_line = "\t".join(solr_strings)
                            outBuffer.write(solr_line + "\n")
                        except Exception, e:
                            print str(e)
                            print "Failed trying to write to string buffer for reaction " + reaction['id']
                
#                        outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','\\"'))
                        outFile.write(outBuffer.getvalue().encode('utf8').replace('\'',''))
                        outBuffer.close()

                    for index,compoundObj in enumerate(model['data']['modelcompounds']):
                        compoundObject=dict()
                        compound = compoundObj
    
                        for key in solr_model_keys:
                            compoundObject[key] = modelObject[key]
                        for key in solr_reaction_keys:
                            compoundObject[key] = modelObject[key]

                        compoundObject['object_id'] = 'kb|ws.' + str(model['info'][6]) + '.obj.' + str(model['info'][0]) + '/modelcompounds/' + str(index)
#                        compoundObject['object_workspace'] = model['info'][7]
#                        compoundObject['object_type'] = model['info'][2]
                        compoundObject['object_type'] = 'KBaseFBA.ModelCompound'
#                        compoundObject['object_name'] = model['info'][1]
#                        compoundObject['object_version'] = model['info'][4]

                        compound_scalar_keys = ['name', 'id', 'formula']
                        for key in compound_scalar_keys:
                            try:
                                compoundObject['compound_'+key] = str(compound[key])
                            except:
                                compoundObject['compound_'+key] = ''
    
                        compound_scalar_keys = ['compound_ref', 'modelcompartment_ref']
                        for key in compound_scalar_keys:
                            try:
                                compoundObject[key] = str(compound[key])
                            except:
                                compoundObject[key] = ''
    
                        # special keys

                        outBuffer = StringIO.StringIO()
                
                        try:
                            solr_strings = [ unicode(str(compoundObject[x])) for x in solr_keys ]
                            solr_line = "\t".join(solr_strings)
                            outBuffer.write(solr_line + "\n")
                        except Exception, e:
                            print str(e)
                            print "Failed trying to write to string buffer for compound " + compound['id']
                
#                        outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','\\"'))
                        outFile.write(outBuffer.getvalue().encode('utf8').replace('\'',''))
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
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('models', action="store", nargs='*')
    args = parser.parse_args()

    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    wsname = args.wsname[0]

    print args.models
    export_models_from_ws(maxNumObjects,args.models,wsname)
