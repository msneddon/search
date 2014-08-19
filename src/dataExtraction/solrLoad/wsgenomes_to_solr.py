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

solr_keys = ["object_id" , "workspace_name" , "object_type" , 'object_name', "genome_id", "feature_id", "genome_source" , "genome_source_id" , "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "num_cds", "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids" , "has_publications" , "has_protein_families" ]
solr_genome_keys = ["genome_id", "genome_source" , "genome_source_id" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "num_cds", "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications", "has_publications"]
solr_feature_keys = ["feature_id",  "feature_source_id" , "protein_translation_length" , "dna_sequence_length", "feature_type" , "function" , "gene_name", "aliases" , "feature_publications" , "location_contig", "location_begin", "location_end", "location_strand", "locations", "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "atomic_regulons", "coexpressed_fids" , "co_occurring_fids" , "has_protein_families" ]


def export_genomes_from_ws(maxNumObjects,genome_list,wsname):
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws')
    
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})
    
    all_workspaces = [ workspace_object ]
    
    headerOutFile = open('genomesToSolr.tab.headers', 'w')
    print >> headerOutFile, "\t".join(solr_keys)
    #print >> headerOutFile, "\n"
    headerOutFile.close()

    outFile = open('genomesToSolr.tab', 'w')
    
    # to add
    # genome_source, feature_source_id,genome_publications,
    # subsystems and/or subsystem_data, annotations, regulon_data
    # don't print header, use header file (so can split output)
    #outFile.write(unicode("object_id\tworkspace_name\tobject_type\tgenome_id\tfeature_id\tgenome_source_id\tprotein_translation_length\t" + \
    #                 "roles\tprotein_families\tcoexpressed_fids\tco_occurring_fids\t" + \
    #                 "feature_publications\tannotations\t" + \
    #                 "feature_type\tfunction\taliases\tscientific_name\t" + \
    #                 "genome_dna_size\tnum_contigs\tdomain\ttaxonomy\tgc_content\n").encode('utf8'))
    
    workspace_counter = 0
    #for n in all_workspaces:
    for n in all_workspaces:
    
        workspace_id = n[0]
        workspace_name = n[1]
    
        print genome_list
        objects_list = list()
        if len(genome_list) > 0:
            names_list = list()
            for genome in genome_list:
                names_list.append({'workspace':wsname,'name':genome})
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)]
        else:
# to do: need to make a few calls to list_objects to capture all of them
#            objects_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome"})
            object_count = 1
            skipNum = 0
            limitNum = 5000
            while object_count != 0:
                this_list = ws_client.list_objects({"ids": [workspace_id],"type":"KBaseSearch.Genome","limit":limitNum,"skip":skipNum})
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

                if "Genome" in x[2]:
                    done = False
    #                sys.stderr.write(str(x)+"\n")
                    while not done:
                        try:
                            genome = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                            done = True
                        except Exception, e:
                            print str(e)
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
    
                    #print json.dumps(genome['data'], sort_keys=True, indent=4, separators=(',',': '))
                    genome = genome[0]
                    #print genome['data'].keys()
                    
                    genomeObject = dict()

                    for key in solr_feature_keys:
                        genomeObject[key] = ''

                    genomeObject['object_id'] = 'kb|ws.' + str(genome['info'][6]) + '.obj.' + str(genome['info'][0])
                    genomeObject['workspace_name'] = genome['info'][7]
                    genomeObject['object_type'] = genome['info'][2]
                    genomeObject['object_name'] = genome['info'][1]

                    if genome['data'].has_key('num_cds'):
                        genomeObject['num_cds'] = str(genome['data']['num_cds'])
                    else:
                        genomeObject['num_cds'] = ''

    		# want this undefined unless there actually are contigs
                    genomeObject['num_contigs'] = ""
                    if genome['data'].has_key('num_contigs'):
                        genomeObject['num_contigs'] = genome['data']['num_contigs']
    #                    else:
    #                        print genome['metadata']
    #                        print genome['data']['contigs']
                    elif genome['data'].has_key('contigs_uuid'):
                        done = False
                        skip = False
                        while not done:
                            try:
                                genomeObject['contigs'] = ws_client.get_object_by_ref({"reference": genome['data']['contigs_uuid'], "asHash": True})
                                done = True
                            except:
                                print "Having trouble getting contigs_uuid " + genome['data']['contigs_uuid'] + " from workspace " + workspace_id
                                done = True
                                skip = True
    
                        if not skip and contigs['data'].has_key('contigs') and contigs['data']['contigs'] is not None:
                            genomeObject['num_contigs'] = str(len(contigs['data']['contigs']))
                        else:
                            num_contigs = "1"
                    else:
                        pass
    
# solr_genome_keys = ["genome_id", "genome_source" , "genome_source_id" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications"]

                    scalar_keys = ['genome_id','genome_source','genome_source_id','scientific_name', 'domain', 'gc_content']
                    for key in scalar_keys:
                        try:
                            genomeObject[key] = str(genome['data'][key])
                        except:
                            genomeObject[key] = ''
    
                    # special keys
                    # complete is uninformative in cdm
                    genomeObject['complete'] = ''

                    genomeObject['taxonomy'] = ''
                    if genome['data'].has_key('taxonomy'):
                        genomeObject['taxonomy'] = re.sub('; ',';',str(genome['data']['taxonomy']))
#                                re.sub('\n',' ',featureObject['annotations'])

                    genomeObject['scientific_name_sort'] = "_".join(genomeObject['scientific_name'].lower().split())

#                    genomeObject['cs_id'] = str(genome['data']['genome_id'])
                    genomeObject['genome_dna_size'] = str(genome['data']['dna_size'])
                    genomeObject['genome_publications'] = ''
                    genomeObject['has_publications'] = False

                    featureset_info = ws_client.get_objects([{"ref": genome['data']['featureset_ref']}])
                    features = featureset_info[0]['data']['features']
    
                    outBuffer = StringIO.StringIO()

                    try:
                        solr_strings = [ unicode(str(genomeObject[x])) for x in solr_keys ]
                        solr_line = "\t".join(solr_strings)
                        outBuffer.write(solr_line + "\n")
                    except Exception, e:
                        print str(e)
                        print "Failed trying to write to string buffer for genome " + genomeObject['object_id']
                
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"',''))
                    outBuffer.close()


                    # dump out each feature in tab delimited format
                    for feature in features:
    
                        featureObject=dict()
#solr_keys = ['cs_id', "object_id" , "workspace_name" , "object_type" , 'object_name', "genome_id", "feature_id", "genome_source" , "genome_source_id" , "feature_source_id" , "protein_translation_length" , "feature_type" , "function" , "aliases" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications" , "feature_publications" , "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "coexpressed_fids" , "co_occurring_fids"]
#solr_genome_keys = ["genome_id", "genome_source" , "genome_source_id" , "scientific_name" , "scientific_name_sort" , "genome_dna_size" , "num_contigs" , "complete" , "domain" , "taxonomy" , "gc_content" , "genome_publications"]
#solr_feature_keys = ["feature_id",  "feature_source_id" , "protein_translation_length" , "feature_type" , "function" , "aliases" , "feature_publications" , "roles" , "subsystems" , "subsystem_data" , "protein_families" , "annotations" , "regulon_data" , "coexpressed_fids" , "co_occurring_fids"]

                        # will want to add support for refs here
                        f = features[feature]['data']
    
                        for key in solr_genome_keys:
                            featureObject[key] = genomeObject[key]

                        scalar_keys = ['feature_id','feature_source_id','protein_translation_length','dna_sequence_length','feature_type','function']
                        for key in scalar_keys:
                            try:
                                featureObject[key] = str(f[key])
                            except:
                                featureObject[key] = ''
    
                         # this will likely change to reflect the ws naming convention
#                        featureObject['object_id'] = 'kb|ws.' + str(feature['info'][6]) + '.obj.' + str(feature['info'][0])
#                        featureObject['object_id'] = 'kb|ws.' + str(featureset_info[0]['info'][6]) + '.obj.' + str(featureset_info[0]['info'][0]) + '.sub.' + feature
                        featureObject['object_id'] = 'kb|ws.' + str(featureset_info[0]['info'][6]) + '.obj.' + str(featureset_info[0]['info'][0]) + '/features/' + feature
                        featureObject['workspace_name'] = featureset_info[0]['info'][7]
#                        featureObject['object_type'] = feature['info'][2]
                        featureObject['object_type'] = 'KBaseSearch.Feature'
                        featureObject['object_name'] = featureset_info[0]['info'][1] + '/features/' + feature
    
# special keys
#                        featureObject['cs_id'] = str(f['feature_id'])

                        prepopulate_keys = ['location_contig', 'location_begin', 'location_end', 'location_strand', 'locations', 'roles','annotations','subsystem_data','subsystems','feature_publications', 'atomic_regulons', 'regulon_data', 'coexpressed_fids', 'co_occurring_fids', 'protein_families', 'gene_name', 'aliases', 'has_protein_families']
                        for key in prepopulate_keys:
                            featureObject[key] = ''

                        # prefer an if here, so that errors inside
                        # don't get caught
                        if f.has_key('location') and len(f['location']) > 0:
                           featureObject['locations'] = simplejson.dumps(f['location'])
                           # determine strand (we hope all features have
                           # locations on same contig and strand)
                           # find loc[4] == 0 and loc[4] > all other locs
                           # set begin and end appropriately
                           featureObject['location_contig'] = f['location'][0][0]
                           featureObject['location_strand'] = f['location'][0][2]
                           firstLoc = list()
                           lastLoc = f['location'][0]
                           for loc in f['location']:
                              if loc[4] == 0:
                                  firstLoc = loc
                              if loc[4] > lastLoc[4]:
                                  lastLoc = loc
                           # not 100% sure about these
                           if featureObject['location_strand'] == '-':
#                               featureObject['location_begin'] = str(firstLoc[1])
                               featureObject['location_begin'] = str(lastLoc[1]-lastLoc[3]+1)
#                               featureObject['location_end'] = str(lastLoc[1]+lastLoc[3]-1)
                               featureObject['location_end'] = str(firstLoc[1])
                           else:
                               featureObject['location_begin'] = str(firstLoc[1])
                               featureObject['location_end'] = str(lastLoc[1]+lastLoc[3]-1)

                        if f.has_key('protein_families'):
                            featureObject['has_protein_families'] = True
                            for pf in f['protein_families']:
                                subj_desc = ''
                                if pf.has_key('subject_description'):
                                    subj_desc = pf['subject_description']
                                featureObject['protein_families'] += unicode(pf['id']) + ' : ' + unicode(subj_desc) + ' :: '
    
                        if f.has_key('aliases'):
                            featureObject['aliases'] = ' :: '.join([ (str(k) + ' : ' + ' '.join(f['aliases'][k]) ) for k in f["aliases"]])
                            if f['aliases'].has_key('genbank_gene'):
                                featureObject['gene_name'] = ' :: '.join(f['aliases']['genbank_gene'])
    
                        if f.has_key('feature_publications'):
                            # this boolean field is untested
                            featureObject['has_publications'] = True
                            for pub in f['feature_publications']:
                                featureObject['feature_publications'] += str(pub[0]) + ' ' + pub[2] + ' ' + pub[3] + ' ' + pub[5] + ' ' + pub[6] + ' '
    
                        if f.has_key('roles'):
                            featureObject['roles'] = ' , '.join([str(k) for k in f["roles"]])
    
#                        if f.has_key('annotations'):
#                            for anno in f['annotations']:
#                                featureObject['annotations'] += anno[0] + ' ' + anno[1] + ' '
#                                re.sub('\n',' ',featureObject['annotations'])
    
#                        if f.has_key('subsystem_data'):
#                            for ssdata in f['subsystem_data']:
#                                featureObject['subsystem_data'] += str(ssdata[0]) + ' ' + str(ssdata[2])
    
#                        if f.has_key('atomic_regulons'):
#                            for ar in f['atomic_regulons']:
#                                featureObject['atomic_regulons'] += ar[0] + ' '
    
#                        if f.has_key('regulon_data'):
#                            for reg in f['regulon_data']:
#                                featureObject['regulon_data'] += reg[0] + ' '
#                                featureObject['regulon_data'] += ' :: '
#                                for member in reg[1]:
#                                    featureObject['regulon_data'] += member + ' '
#                                featureObject['regulon_data'] += ' :: '
#                                for tfs in reg[2]:
#                                    featureObject['regulon_data'] += tfs + ' '
    
#                        if f.has_key('co_occurring_fids'):
#                            for coo in f['co_occurring_fids']:
#                                featureObject['co_occurring_fids'] += coo[0] + ' '
    
#                        if f.has_key('coexpressed_fids'):
#                            for coe in f['coexpressed_fids']:
#                                featureObject['coexpressed_fids'] += coe[0] + ' '
    
#                        if f.has_key('subsystems'):
#                            featureObject['subsystems'] = ' , '.join([str(k) for k in f["subsystems"]])
    
                        outBuffer = StringIO.StringIO()
                
                        try:
                            solr_strings = [ unicode(str(featureObject[x])) for x in solr_keys ]
                            solr_line = "\t".join(solr_strings)
                            outBuffer.write(solr_line + "\n")
                        except Exception, e:
                            print str(e)
                            print "Failed trying to write to string buffer for feature " + f['feature_id']
                
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
    parser.add_argument('genomes', action="store", nargs='*')
    args = parser.parse_args()
    maxNumObjects = sys.maxint
    if args.maxNumObjects:
        maxNumObjects = args.maxNumObjects
    
    wsname = args.wsname[0]

    print args.genomes
    export_genomes_from_ws(maxNumObjects,args.genomes,wsname)
