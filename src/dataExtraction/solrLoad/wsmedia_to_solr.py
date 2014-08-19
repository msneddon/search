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

solr_keys = ["object_id", "object_version", "object_workspace", "object_type", "object_name", "media_id", "media_source_id", "media_name", "media_type", "media_isDefined", "media_isMinimal" , 'compound_ref', 'compound_minFlux', 'compound_maxFlux', 'compound_concentration', ]
solr_media_keys = ["object_id", "object_version", "object_workspace", "object_type", "object_name", "media_id", "media_source_id", "media_name", "media_type", "media_isDefined", "media_isMinimal" ]
solr_compound_keys = ['compound_ref', 'compound_minFlux', 'compound_maxFlux', 'compound_concentration', ]
#solr_keys = ["object_id" , "workspace_name" , "object_type" , 'object_name', "genome_id", "feature_id", "genome_source" , "genome_source_id" , "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids"]
#solr_genome_keys = ["genome_id", "genome_source" , "genome_source_id" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications"]
#solr_feature_keys = ["feature_id",  "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids"]


def export_media_from_ws(maxNumObjects,media_list,wsname):
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    headerOutFile = open('mediaToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(solr_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()

    outFile = open('mediaToSolr.tab', 'w')
    
    workspace_counter = 0
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        print media_list
        objects_list = list()
        if len(media_list) > 0:
            names_list = list()
            for media in media_list:
                names_list.append({'workspace':wsname,'name':media})
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)]
        else:
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

                if "Media" in x[2]:
                    done = False
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            media = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    #print json.dumps(genome['data'], sort_keys=True, indent=4, separators=(',',': '))
                    media = media[0]
                    #print media['data'].keys()
                    
                    mediaObject = dict()

                    for key in solr_compound_keys:
                        mediaObject[key] = ''

                    mediaObject['object_id'] = 'kb|ws.' + str(media['info'][6]) + '.obj.' + str(media['info'][0])
                    mediaObject['object_workspace'] = media['info'][7]
                    mediaObject['object_type'] = media['info'][2]
                    mediaObject['object_name'] = media['info'][1]
                    mediaObject['object_version'] = media['info'][4]

                    media_scalar_keys = ['id', 'source_id', 'name', 'type', 'isDefined', 'isMinimal']
                    for key in media_scalar_keys:
                        try:
                            mediaObject['media_'+key] = str(media['data'][key])
                        except:
                            mediaObject['media_'+key] = ''
    
                    # write to import file

                    outBuffer = StringIO.StringIO()

                    try:
                        solr_strings = [ unicode(str(mediaObject[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n")
                    except Exception, e:
                        print str(e)
                        print "Failed trying to write to string buffer for media " + mediaObject['object_id']
                
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()

                    # will probably loop over some substructures
                    # but not sure how yet

                    for index,compoundObj in enumerate(media['data']['mediacompounds']):
                        compoundObject=dict()
                        compound = compoundObj
    
                        for key in solr_media_keys:
                            compoundObject[key] = mediaObject[key]

                        compoundObject['object_id'] = 'kb|ws.' + str(media['info'][6]) + '.obj.' + str(media['info'][0]) + '/mediacompounds/' + str(index)
                        compoundObject['object_type'] = 'KBaseBiochem.MediaCompound'

                        compound_scalar_keys = ['minFlux', 'maxFlux', 'concentration']
                        for key in compound_scalar_keys:
                            try:
                                compoundObject['compound_'+key] = str(compound[key])
                            except:
                                compoundObject['compound_'+key] = ''
    
                        # want to chase down this ref and include metadata (e.g., id, name, formula, abbreviation, mass)
                        # this structure is unfortunately an array, so will need to manipulate it to get the right mapping
                        compound_scalar_keys = ['compound_ref']
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
                            print "Failed trying to write to string buffer for compound " + compound['compound_ref']
                
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
    parser.add_argument('media', action="store", nargs='*')
    args = parser.parse_args()

    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    wsname = args.wsname[0]

    print args.media
    export_media_from_ws(maxNumObjects,args.media,wsname)
