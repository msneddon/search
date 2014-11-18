#!/usr/bin/env python

# use this script to take genomes and features from CS (via flat files
# generated from SQL dumps)
# and create WS objects
# use the ws-url command-line tool to set the active workspace service URL
# use kbase-login to set the appropriate auth token

from datetime import datetime
import sys
import simplejson
import time
import random
import requests
import pprint
import codecs
import TextFileDecoder
import os
import Bio.SeqIO
import Bio.SeqFeature
import urllib2
import logging
import warnings
import re

import biokbase.workspace.client
import biokbase.cdmi.client


logger = None
pp = pprint.PrettyPrinter(indent=4)

# this will be used to store the pub info from PubMed
# use that with the fids2pubs mapping to stuff pub info into a feature
publications = dict()

# this will store the moral equivalent of genomes_to_genome_data
all_genome_data = dict()
all_contig_data = dict()
all_taxonomy_data = dict()

skipExistingGenomes = False
contigseq_file_dir = ''

# production CDMI instance
cdmi_api = biokbase.cdmi.client.CDMI_API()
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI()

# mimic the CDMI FormatLocations function:
# check that consecutive Locations are on same contig and strand
# check that end of N is same as begin of N+1
# if so, join them up (properly)
def join_contiguous_locations(featureLocations):
    #Appears to order the locations in the proper order (depending on + or - strand)
    newFeatureLocations = list()
    lastLoc = list()
    for index,loc in enumerate(featureLocations):
#Debug Log
#        logger.debug('start loop')
#        logger.debug(lastLoc)
#        logger.debug(loc)
        if len(lastLoc) > 0 and lastLoc[0] == loc[0] and lastLoc[2] == loc[2]:
            if loc[2] == '-':
                if (lastLoc[1] - lastLoc[3]) == loc[1]:
                    lastLoc[3] += loc[3]
                else:
                    newFeatureLocations.append(lastLoc)
                    lastLoc=loc
            else:
            # assume + strand
                if (lastLoc[1] + lastLoc[3]) == loc[1]:
                    lastLoc[3] += loc[3]
                else:
                    newFeatureLocations.append(lastLoc)
                    lastLoc=loc
        else:
            if len(lastLoc) > 0:
                newFeatureLocations.append(lastLoc)
            lastLoc=loc
#Debug Log
#        logger.debug('end loop')
#        logger.debug(lastLoc)
    # append the last location
    newFeatureLocations.append(lastLoc)
    return newFeatureLocations

def cleanup_filehandles(filehandles):
    #Closes all the attribute and feature open file_handles.
    for fileName in filehandles:
        filehandles[fileName].close()

def find_genome_first_line(fp, looking_for, begin, end):
    found_it = False 
    counter = 0 
    while (begin < end): 
        mid_point = (end + begin) / 2 
        line_start = fp.rfind("\n",mid_point) 
        if line_start == -1 : 
            line_start = 0 
        fp.seek(line_start) 
        line_to_check = fp.readline() 
        first_element = line_to_check.split("\t")[0]
        record_number = int(first_element.split(".")[1])
#        print "Next binary search iteration - Begin : " + str(begin) + "  End : " + str(end)
        if record_number == looking_for: 
            found_it = True 
            break 
            # found what you wanted                                                                                                           
        elif record_number > looking_for:
            end = line_start
        else: 
            begin = fp.tell() 
        counter = counter + 1 
#    print "Found it ? " + str(looking_for) + " " + str(found_it)
    logger.debug("Binary Search Result - Looking for " + str(looking_for) + "  Found? " + str(found_it))
    if found_it: 
        #Now find the first line of the file that has the genome of interest   
        scan_chunk_size = 100000
        found_first_line = False
        while (not found_first_line):
            scan_point = fp.tell() - scan_chunk_size 
            if scan_point < 0: 
                scan_point = 0 
            fp.seek(scan_point,0) 
            file_chunk = fp.read(scan_chunk_size)
            file_lines = file_chunk.split('\n',)
            while (len(file_lines) == 1) and (scan_point > 0): 
                #dont have a full line.  Double the scan chunk size until you get a new line.  
                scan_chunk_size = scan_chunk_size * 2 
                scan_point = fp.tell - scan_chunk_size 
                if scan_point < 0: 
                    scan_point = 0 
                fp.seek(scan_point,0)
            #first line is partial                                     
            fp.seek(scan_point,0)
            if scan_point != 0 :
                fp.readline()
            first_full_line = fp.readline()
            #split line and compare first element   
            first_element = first_full_line.split("\t")[0] 
            record_number = int(first_full_line.split(".")[1]) 
            if (record_number == looking_for) and (scan_point == 0):
                return_result = [found_it,0]
#                print "First Full line : " + first_full_line 
                return return_result 
            elif record_number < looking_for: 
                #if not the id looking for keep looping through readline until you find it. 
                previous_line_start = fp.tell()
                check_line = fp.readline()
                while (not found_first_line):
                    first_element = check_line.split("\t")[0]
                    record_number = int(check_line.split(".")[1])
                    if record_number == looking_for:
                        #found the first_line 
                        begin = previous_line_start 
                        return_result = [found_it,begin] 
#                        print "First line : " + check_line 
                        return return_result 
                    elif record_number < looking_for: 
                        #keep looping  
                        previous_line_start = fp.tell() 
                        check_line = fp.readline() 
                    else: 
                        #ERROR FILE NOT SORTED  
#                        print "ERROR the file is not properly sorted" 
                        logger.error("Binary Search : File not properly sorted")
                        fp.close() 
                        exit(0) 
            elif record_number == looking_for: 
                #elif id you are looking for and need to go back further. 
                fp.seek(scan_point,0) 
            else: 
                #ERROR FILE NOT SORTED 
#                print "ERROR the file is not properly sorted" 
                logger.error("Binary Search : File not properly sorted")
                fp.close() 
                exit(0) 
    else: 
        fp.seek(begin,0) 
        #next two lines are just for debugging  
#        stop_line = fp.read(1000) 
#        print "DID NOT FIND - The area stopped at : \n" + stop_line
        return_result = [found_it,begin] 
        return return_result 


def create_feature_objects(gid,genetic_code,featureData,contigSeqObjects):
    #Creates a hash/dict of feature objects
    featureObjects = dict()

    for feature_line in featureData['Feature']:
        feature_line=feature_line.rstrip()
        [fid,cs_id,genome_id,dna_sequence_length,feature_type,feature_source_id,function,md5,protein_translation_length,protein_translation]=feature_line.split("\t")
        featureObjects[fid]=dict()
        featureObjects[fid]["source"] = 'KBase Central Store'
        featureObjects[fid]['feature_id']=fid
        featureObjects[fid]['genome_id']=genome_id
        featureObjects[fid]['dna_sequence_length']=int(dna_sequence_length)
        featureObjects[fid]['feature_type']=feature_type
        featureObjects[fid]['feature_source_id']=feature_source_id
        if function != 'NULL':
            featureObjects[fid]['function']=function
        if md5 != 'NULL':
            featureObjects[fid]['md5']=md5
        if protein_translation_length != 'NULL':
            featureObjects[fid]['protein_translation_length']=int(protein_translation_length)
        # make sure to initialize
        if feature_type=='CDS':
            featureObjects[fid]['protein_translation']=''
        if protein_translation != 'NULL':
            featureObjects[fid]['protein_translation']=protein_translation
        # all features need a location
        featureObjects[fid]['location']=list()
#        pp.pprint(featureObjects[fid])

    for annotation_line in featureData['Annotation']:
        annotation_line=annotation_line.rstrip()
        [fid,comment,annotator,annotation_time]=annotation_line.split("\t")
        if not featureObjects[fid].has_key("annotations"):
            featureObjects[fid]['annotations']=list()
        annotation = [comment,annotator,int(annotation_time)]
        featureObjects[fid]['annotations'].append(annotation)

    for atomic_regulon_line in featureData['AtomicRegulons']:
        atomic_regulon_line=atomic_regulon_line.rstrip()
        [fid,atomic_regulon,count]=atomic_regulon_line.split("\t")
        if not featureObjects[fid].has_key("atomic_regulons"):
            featureObjects[fid]['atomic_regulons']=list()
        atomic_regulon = [atomic_regulon,int(count)]
        featureObjects[fid]['atomic_regulons'].append(atomic_regulon)

    # huge amount of coexpressed data for this genome makes
    # the featureset object too big
    # skip for now, try to figure out how to handle later
    if len(featureData['CoexpressedFids']) > 2000000:
        logger.warning('too many lines of coexpressedfids for ' + genome_id + ', skipping')
    else:
        for coexpressed_fid_line in featureData['CoexpressedFids']:
            coexpressed_fid_line=coexpressed_fid_line.rstrip()
            [fid,coexpressed_fid,score]=coexpressed_fid_line.split("\t")
            if not featureObjects[fid].has_key("coexpressed_fids"):
                featureObjects[fid]['coexpressed_fids']=list()
            coexpressed_fid = [coexpressed_fid,float(score)]
            featureObjects[fid]['coexpressed_fids'].append(coexpressed_fid)

    # not working right?
    # it's fine, db is missing some entries (see KBASE-640)
    for co_occurring_fid_line in featureData['CoOccurringFids']:
        co_occurring_fid_line=co_occurring_fid_line.rstrip()
        [fid,co_occurring_fid,score]=co_occurring_fid_line.split("\t")
        if not featureObjects[fid].has_key("co_occurring_fids"):
            featureObjects[fid]['co_occurring_fids']=list()
        # is score an int or float here? not sure
        co_occurring_fid = [co_occurring_fid,float(score)]
        featureObjects[fid]['co_occurring_fids'].append(co_occurring_fid)

    for fids2pubs_line in featureData['fids2pubs']:
        fids2pubs_line=fids2pubs_line.rstrip()
        [fid,id]=fids2pubs_line.split("\t")
        if not featureObjects[fid].has_key("feature_publications"):
            featureObjects[fid]['feature_publications']=list()
        fids2pubs = [int(id),'PubMed',publications[id]['article_title'],publications[id]['link'],publications[id]['pubdate'],publications[id]['authors'],publications[id]['journal_name'] ]
        featureObjects[fid]['feature_publications'].append(fids2pubs)

#    for alias_line in featureData['FeatureAlias']:
#        alias_line=alias_line.rstrip()
#        [fid,alias]=alias_line.split("\t")
#        if not featureObjects[fid].has_key("aliases"):
#            featureObjects[fid]['aliases']=list()
#        featureObjects[fid]['aliases'].append(alias)

    for hasalias_line in featureData['HasAliasAssertedFrom']:
        hasalias_line=hasalias_line.rstrip()
        [fid,alias,source_db]=hasalias_line.split("\t")
        if not featureObjects[fid].has_key("aliases"):
            featureObjects[fid]['aliases']=dict()
        if not featureObjects[fid]["aliases"].has_key(source_db):
            featureObjects[fid]['aliases'][source_db]=list()
        featureObjects[fid]['aliases'][source_db].append(alias)

    featureLocations = dict()
#    logger.debug("Number of rows in feature locations : " + str(len(featureData['Locations'])))
    for location_line in featureData['Locations']:
        location_line=location_line.rstrip()
        [fid,contig,begin,strand,length,ordinal]=location_line.split("\t")
#        logger.debug("FID : " + fid + " -- contig : " + contig + " -- begin : " + begin + " -- strand : "+strand+ " -- length : " + length + " -- ordinal : " + ordinal)
        if not featureLocations.has_key(fid):
            featureLocations[fid] = list()
        if strand == '-':
            start = int(begin) + int(length) - 1
            location = [contig,int(start),strand,int(length),int(ordinal)]
            featureLocations[fid].append(location)
        else:
            location = [contig,int(begin),strand,int(length),int(ordinal)]
            featureLocations[fid].append(location)
        # force the location list to be sorted by ordinal
        featureLocations[fid].sort( key = lambda loc: loc[4] )

    for fid in featureLocations:
#        logger.debug(featureLocations[fid])
#        logger.debug("Has locations " + fid)
        featureObjects[fid]['location'] = join_contiguous_locations(featureLocations[fid])
#       logger.debug(featureObjects[fid]['location'])
        if len(featureObjects[fid]['location']) > 0:
#           logger.debug('making feature_dna for ' + fid + ' on contig ' + featureObjects[fid]['location'][0][0])
            if not featureObjects[fid].has_key('dna_sequence'):
                featureObjects[fid]['dna_sequence'] = ''
            locations = featureObjects[fid]['location']
            for loc in locations:
#                if loc[3] > 100000 and (featureObjects[fid]['feature_type'] != 'CDS' or len(featureObjects[fid]['protein_sequence']) < 30000 ) :
                if loc[3] > 100000 and (featureObjects[fid]['feature_type'] != 'CDS' or len(featureObjects[fid]['protein_translation']) < 30000) :
                    logger.warning('dna sequence for feature ' + fid + ' is much too long (compared to CS protein sequence if a CDS), skipping')
                    featureObjects[fid]['dna_sequence'] = ''
                    break
                if loc[2] == '-':
                    featSeqFeature = Bio.SeqFeature.SeqFeature(Bio.SeqFeature.FeatureLocation( loc[1] - loc[3], loc[1], strand=-1 ), id=fid+'/data/location/'+str(loc[4]))
                else: # assume + strand
                    featSeqFeature = Bio.SeqFeature.SeqFeature(Bio.SeqFeature.FeatureLocation( (loc[1]-1), (loc[1]-1) + loc[3], strand=+1 ), id=fid+'/data/location/'+str(loc[4]))
#                    logger.debug(featSeqFeature)
#                    logger.debug(featSeqFeature.extract( contigSeqObjects[loc[0]]))
                if contigSeqObjects.has_key(loc[0]):
#                     logger.debug(featSeqFeature)
                     featureObjects[fid]['dna_sequence'] += str(featSeqFeature.extract( contigSeqObjects[loc[0]]).seq)
#            logger.debug('genetic_code is ' + str(genetic_code))
#            logger.debug(fid)

            # to override problems in the biopython start codons in the
            # standard table: the ensembl plants annotation of Arabidopsis
            # has at least one CDS with GUG as start codon
            # drawback is that translate() won't use M as first amino acid,
            # so there will be some false positives
            # (use bacterial table instead?)
            # there are also issues with frameshifts and other
            # modifications, which no check can verify
            complete_cds = False
            stop_codon = '*'
            if genetic_code in [4,11]:
                complete_cds = True
                stop_codon = ''
#            logger.debug(genetic_code)
#            logger.debug(fid)

            try:
                if featureObjects[fid]['feature_type'] == 'CDS' and (featureObjects[fid]['protein_translation'] + stop_codon != Bio.Seq.translate( featureObjects[fid]['dna_sequence'], cds=complete_cds,table=genetic_code) ) :
                    logger.warning('warning: computed translation does not match translation in db for ' + fid)
                    if featureObjects[fid]['protein_translation'].find('X'):
                        logger.warning('X found in CS translation, not worrying about for feature ' + fid)
                    else:
                        logger.debug("IN ELSE BIOPYTHON TRANSLATE:")
                        logger.debug(featureObjects[fid]['protein_translation'] + stop_codon)
                        logger.debug(cdmi_api.fids_to_dna_sequences([fid]))
                        logger.debug(cdmi_api.fids_to_locations([fid]))
                        logger.debug(featureObjects[fid]['location'])
                        logger.debug(Bio.Seq.translate( featureObjects[fid]['dna_sequence'], cds=complete_cds,table=genetic_code))
                        logger.debug(featureObjects[fid]['dna_sequence'])
            #                        print >> sys.stderr, str(featSeqFeature.extract( contigSeqObjects[loc[0]]).seq.translate(table=genetic_code, cds=complete_cds) )
#            except Warning, w:
                #CANT GET IT TO CATCH THIS WARNING
#                /usr/local/lib/python2.7/dist-packages/Bio/Seq.py:1976: BiopythonWarning: Partial codon, len(sequence) not a multiple of three. Explicitly trim the sequence or add trailing N before translation. This may become an error in future. BiopythonWarning)
                #NOT huge deal, but annoying
#                logger.warning('Feature ID Warning' + fid + ' : ' + w)
            except Bio.Data.CodonTable.TranslationError, e:
                logger.warning('possible problem with translation of fid ' + fid)
                logger.warning(str(e))
                logger.warning(featureObjects[fid]['function'])
#            except Exception, e:
#                #WARNING Still does not get caught here.
#                logger.warning('FINAL EXCPETION CATCH : ' + e)
        else:
            logger.warning('no locations for ' + fid + ', not making feature_dna')

    for protein_families_line in featureData['ProteinFamilies']:
        protein_families_line=protein_families_line.rstrip()
        [fid,id,release_version,subject_db,subject_description]=protein_families_line.split("\t")
        if not featureObjects[fid].has_key("protein_families"):
            featureObjects[fid]['protein_families']=list()
        protein_families = { 'id':id, 'release_version':release_version, 'subject_db':subject_db, 'subject_description':subject_description }
        featureObjects[fid]['protein_families'].append(protein_families)

    # RegulonData
    # (uses two featureData keys, need to track by reg)
    regulons2fids = dict()
    regulons2tfs = dict()
    fids2regulons = dict()
    for regulon_line in featureData['regulonData.members']:
        regulon_line=regulon_line.rstrip()
        [fid,reg]=regulon_line.split("\t")
        if not fids2regulons.has_key(fid):
            fids2regulons[fid]=list()
        fids2regulons[fid].append(reg)
        if not regulons2fids.has_key(reg):
            regulons2fids[reg]=list()
        regulons2fids[reg].append(fid)
    for tfs_line in featureData['regulonData.tfs']:
        tfs_line=tfs_line.rstrip()
        [fid,reg]=tfs_line.split("\t")
        if not regulons2tfs.has_key(reg):
            regulons2tfs[reg]=list()
        regulons2tfs[reg].append(fid)
    for fid in fids2regulons:
        for regulon_id in fids2regulons[fid]:
            regulon_set = regulons2fids[regulon_id]
            tfs = list()
            if regulons2tfs.has_key(regulon_id):
                tfs = regulons2tfs[regulon_id]
            regulon_data = [ regulon_id, regulon_set, tfs ]
            if not featureObjects[fid].has_key("regulon_data"):
                featureObjects[fid]['regulon_data']=list()
            featureObjects[fid]['regulon_data'].append(regulon_data)

    for roles_line in featureData['Roles']:
        roles_line=roles_line.rstrip()
        # some lines have an empty role (grr)
        try:
            [fid,role]=roles_line.split("\t")
        except Exception, e:
            logger.warning('missing data found in Role line')
            logger.warning(e)
            logger.warning(roles_line)
            logger.warning('skipping line')
            continue
        if not featureObjects[fid].has_key("roles"):
            featureObjects[fid]['roles']=list()
        featureObjects[fid]['roles'].append(role)

    for subsystems_line in featureData['Subsystems']:
        subsystems_line=subsystems_line.rstrip()
        [fid,subsystems]=subsystems_line.split("\t")
        if not featureObjects[fid].has_key("subsystems"):
            featureObjects[fid]['subsystems']=list()
        featureObjects[fid]['subsystems'].append(subsystems)

    for ssdata_line in featureData['SubsystemData']:
        ssdata_line=ssdata_line.rstrip()
        [fid,subsystem,variant,role]=ssdata_line.split("\t")
        if not featureObjects[fid].has_key("subsystem_data"):
            featureObjects[fid]['subsystem_data']=list()
        ssdata = [subsystem,variant,role]
        featureObjects[fid]['subsystem_data'].append(ssdata)

    return featureObjects

def compute_taxonomy_lineage(taxonomy_id):
    #recursive function that will retrieve the taxonomy lineage.
    if not all_taxonomy_data.has_key(taxonomy_id):
        return ''
    if int(all_taxonomy_data[taxonomy_id]['domain']) == 1:
        return all_taxonomy_data[taxonomy_id]['description']

    if int(all_taxonomy_data[taxonomy_id]['hidden']) == 0:
        return '; '.join([ compute_taxonomy_lineage(all_taxonomy_data[taxonomy_id]['parent_taxonomy_id']) , all_taxonomy_data[taxonomy_id]['description'] ])
    else:
        return compute_taxonomy_lineage(all_taxonomy_data[taxonomy_id]['parent_taxonomy_id'])

def insert_genome(g,ws,wsname,featureData,provenance_description,provenance_time_string):
    #This inserts the genome objects (Genome, ContigSet and FeatureSet) into the WS
    start = time.time()

    numericGid = int(g.split('.')[1])
    logger.info(g)
    logger.info(numericGid)
    
    #IF do not want to replace existing genomes in the WS
    try:
        ws.get_object_info([{"workspace":wsname,"name":g}],0)
        if skipExistingGenomes == True:
            logger.info('genome '  + g + ' found, skipping')
            return
        logger.info('genome '  + g + ' found, replacing')
    except biokbase.workspace.client.ServerError:
        logger.info('genome '  + g + ' not found, adding to ws')

#    all_genome_data = cdmi_api.genomes_to_genome_data([g])
    genome_data = dict()
    if all_genome_data.has_key(g):
        genome_data = all_genome_data[g]
    else:
        logger.info('genome ' + g + ' has no entry in genome data, skipping')
        logger.warning('genome ' + g + ' has no entry in genome data, skipping')
        return

    end = time.time()
    logger.info("querying genome_data " + str(end - start))
#    if 'P' not in genome_data['scientific_name']:
    # sloppy hack to pick up where it crashed
#    if numericGid < 2207:
#    if numericGid < 28878:
#        print >> sys.stderr, "skipping genome " + g + ' ' + genome_data['scientific_name']
#        return
    logger.info("processing genome " + g + ' ' + genome_data['scientific_name'])
    genomeObject = dict()
    featureSet = dict()
    featureSet['features'] = dict()

    ###############################################
    #fill in top level genome object properties
    genomeObject["genome_id"] = g
    genomeObject["scientific_name"] = genome_data["scientific_name"]
    genomeObject["genetic_code"] = int(genome_data["genetic_code"])
    genomeObject["dna_size"] = int(genome_data["dna_size"])
    genomeObject["num_contigs"] = int(genome_data["contigs"])
    genomeObject["genome_source"] = 'KBase Central Store'
    genomeObject["md5"] = genome_data["genome_md5"]
    genomeObject["domain"] = genome_data["domain"]
    genomeObject["gc_content"] = float(genome_data["gc_content"])
    genomeObject["complete"] = int(genome_data["complete"])
    genomeObject["num_cds"] = int(genome_data["pegs"])

    genomeObject["genome_source_id"] = genome_data['source_id']

    genomeObject["contig_lengths"] = dict()

    if genome_data.has_key('taxonomy_id') and all_taxonomy_data.has_key(genome_data['taxonomy_id']):
        genomeObject["taxonomy"] = '; '.join( [ compute_taxonomy_lineage(genome_data["taxonomy_id"]) , all_taxonomy_data[genome_data['taxonomy_id']]['description'] ] )

    # this is a temporary measure
#    if genomeObject.has_key('taxonomy') and 'Eukaryota' in genomeObject['taxonomy'] and 'Viridiplantae' not in genomeObject['taxonomy']:
#    if genomeObject.has_key('taxonomy') and 'Eukaryota' in genomeObject['taxonomy']:
#    if g == 'kb|g.2646':
#        print >> sys.stderr, 'skipping Eukaryota genome ' + g
#        return

    #genomeObject["contigset_ref"] = 
    #genomeObject["proteinset_ref"] = 
    #genomeObject["transcriptset_ref"] = 

    ##########################
    # build ContigSet and Contig objects
    # ultimately we will want to build ContigSet independent of
    # the Genome object, insert it first, get its workspace path,
    # then use that to populate contigset_ref in the Genome object

    contigSet = dict()

    contigSet["id"] = g+".contigset"
    contigSet["name"] = "contigset for " + g
    contigSet["md5"] = genomeObject["md5"]
#    contigSet["source_id"] = ""
    contigSet["source"] = "KBase Central Store"
    contigSet["type"] = "Organism"
#    contigSet["reads_ref"] = None
#    contigSet["fasta_ref"] = None
    contigSet["contigs"] = dict()

    contigs = all_contig_data[g]

    genomeObject['contig_ids'] = [ x['id'] for x in contigs ]

    start = time.time()
    logger.info("start querying contig seqs")

    # retrieving all with one call died on kb|g.3907, kb|g.3643 Gallus gallus, kb|g.41 Mouse
    # looping over each contig_id still seems slow on chicken
    # these sequences are too big for ws (250MB), need to refactor

    contig_sequences = dict()
    contigSeqObjects = dict()
    contig_set_made_flag = True

    ##########################################################
    #IF CONTIG FILE DIRECTORY DOES NOT EXIST USE CDMI
    if contigseq_file_dir == '':
        logger.info('no contig path defined, using CDMI')

        # loop over contigs method
        for contig_id in genomeObject['contig_ids']:
#            contig_seq = cdmi_api.contigs_to_sequences([contig_id])
#            contig_sequences[contig_id] = contig_seq[contig_id]
            # for debugging, don't get contig seqs
            contig_sequences[contig_id] = ''

        # all in one call (has been working so far)
        contig_sequences = cdmi_api.contigs_to_sequences(genomeObject['contig_ids'])
        # need to make contigSeqObjects here to pass to create_feature_objects

    else:
        ######################################################
        #CONTIG DIR EXISTS USE FILE if the file exists.
        logger.info('contig path defined, attempting to read file in ' + contigseq_file_dir)
        try:
            contig_filename = contigseq_file_dir + '/' + g + '.fa'
            contig_filesize = os.stat(contig_filename).st_size
            if contig_filesize > 1000000000:
#                Contigs file too large.  Can't save to WS but need to make objects so can do the dna sequence in the feature set.
                logger.info('contig file ' + contig_filename + ' may be too big, contigset will not be made for genome ' + g)
                logger.warning('contig file ' + contig_filename + ' may be too big, contigset will not be made for genome ' + g)
                contig_set_made_flag = False
            if genomeObject["num_contigs"] > 125000:
#                There are too many contigs for this genome.  The resulting contigset would be too large.  
                logger.info('contig file ' + contig_filename + '.  There are too many contigs for genome ' + g + '.  The resulting contigset would be too large')
                logger.warning('contig file ' + contig_filename + '.  There are too many contigs for genome ' + g + '.  The resulting contigset would be too large')
                contig_set_made_flag = False
            contig_handle = open (contig_filename, 'rU')
            contigSeqObjects = Bio.SeqIO.to_dict( Bio.SeqIO.parse(contig_handle,'fasta') )
            for contigseq in contigSeqObjects:
#                logger.debug(contigseq + ":::" + str(contigSeqObjects[contigseq].seq) )
                contig_sequences[contigseq] = str(contigSeqObjects[contigseq].seq)
            contig_handle.close()
            logger.info('reading contig file ' + contig_filename + ' succeeded')
        except Exception, e:
            logger.warning('problem reading contig file ' + contig_filename + ' for ' + g)
            logger.warning(e)
            logger.warning('attempting to use CDMI instead')
            contig_sequences = cdmi_api.contigs_to_sequences(genomeObject['contig_ids'])
            # need to make contigSeqObjects here to pass to create_feature_objects

### to do: measure the contig sequences
### if too large, skip genome (with warning to stderr)

    end = time.time()
    logger.info("done querying contig seqs " + str(end - start))

    if len(contig_sequences.keys()) != len(contigs):
        logger.warning('The number of CS contigs (' + str(len(contigs)) + ') is not equal to the number of contig sequences retrieved (' + str(len(contig_sequences.keys())) + ') for genome ' + g)
        logger.info('The number of CS contigs (' + str(len(contigs)) + ') is not equal to the number of contig sequences retrieved (' + str(len(contig_sequences.keys())) + ') for genome ' + g)

    for x in contigs:
        contig = dict()
        contig["id"] = x['id']
        contig["length"] = int(x['length'])
        contig["md5"] = x['contig_md5']
        if contig_sequences.has_key(x['id']):
            contig["sequence"] = contig_sequences[x['id']]
        else:
            logger.warning('contig ' + x['id'] + ' does not have sequence defined, setting to empty')
            contig["sequence"] = ''
        
        contigSet["contigs"][x['id']]=contig
        
        genomeObject["contig_lengths"][x['id']]=int(x['length'])

    # will need to insert the ContigSet object here, in order to
    # be able to use the ref in Feature.location
    # will also need to build a mapping of contig_ids to contigrefs
    # put in existing contigSet?  might get confusing

    start = time.time()

# first see if object already exists
    try:
        contigset_info=ws.get_object_info([{"workspace":wsname,"name":contigSet['id']}],0)
        logger.info('contigset '  + contigSet['id'] + ' found, replacing')
    except biokbase.workspace.client.ServerError:
        logger.info('contigset '  + contigSet['id'] + ' not found, adding to ws')

    # this will reference a ContigSet object
    #print simplejson.dumps(contigSet,sort_keys=True,indent=4 * ' ')

    if contig_set_made_flag:
        try:
            contigset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.ContigSet","data":contigSet,"name":contigSet['id'],"provenance":[{"time":provenance_time_string,"service": "KBase Search","description":provenance_description}]}]})
            logger.info(contigset_info)
        except biokbase.workspace.client.ServerError, e:
            logger.warning('possible error loading contigset for ' + g)
            logger.warning(e)
            logger.warning('contigset was unable to be created in the WS (likely too large) for ' + g)
            contig_set_made_flag = False
        # this is completely untested
        except urllib2.URLError, e:
            logger.warning(e)
            logger.warning('urllib2.URLError - possible problem with genome ' + g + ' contigset may be too large, not making contigset')
            contig_set_made_flag = False
        # want to check for urllib2.URLError: <urlopen error [Errno 5] _ssl.c:1242: Some I/O error occurred>
        # skip genome and warn if it occurs

    end = time.time()
    logger.info("inserting contigset into ws " + str(end - start))
#    logger.debug(contigset_info)

    #contigset reference is optional.  If could not make contig set it will be empty
    if contig_set_made_flag:
        contigset_ref = wsname + '/' + contigSet['id']
        genomeObject["contigset_ref"] = contigset_ref

###########################
    # build Feature objects

    start  = time.time()

    # with any luck this can be used directly when saving a FeatureSet
    featureObjects = create_feature_objects(gid,genomeObject['genetic_code'],featureData,contigSeqObjects)
    
    featureSet['features'] = dict()
    for feature in featureObjects:
        #logger.debug(feature) 
        #logger.debug(featureObjects[feature])
        individualFeature = dict()
        individualFeature['data'] = featureObjects[feature]
        featureSet['features'][feature] = individualFeature
        
#    pp.pprint(featureObjects)

    end = time.time()
    logger.info("processing features, elapsed time " + str(end - start))

    # for debugging
#    return 

    # insert into workspace, get path
#   logger.debug(simplejson.dumps(featureSet,sort_keys=True,indent=4 * ' '))
    # another try block here?
    featureset_id = genomeObject['genome_id'] + '.featureset'

    start  = time.time()
#    logger.debug(simplejson.dumps(featureSet))

    featureSetType='KBaseSearch.SearchFeatureSet'
    if args.debug:
        featureSetType='KBaseSearch.FeatureSet'
    try:
        featureset_info = ws.save_objects({"workspace": wsname,
#                                       "objects":[{"type": "KBaseSearch.FeatureSet",
#                                       "objects":[{"type": "KBaseSearch.SearchFeatureSet",
                                       "objects":[{"type": featureSetType,
                                                   "data": featureSet,
                                                   "name": featureset_id,
                                                   "provenance":[{"time":provenance_time_string,"service": "KBase Search","description":provenance_description}]}]
                                     })
        logger.info(featureset_info)
    except biokbase.workspace.client.ServerError, e:
        logger.warning('possible error loading featureset into the WS for ' + g)
        logger.warning(e)
    # this is completely untested
    except urllib2.URLError, e:
        logger.warning(e)
        logger.warning('possible problem with genome ' + g + ' featureset may be too large, skipping')
        return
    # want to check for urllib2.URLError: <urlopen error [Errno 5] _ssl.c:1242: Some I/O error occurred>
    # skip genome and warn if it occurs

    end = time.time()
    logger.info("saving featureset for genome " + g + " to ws, elapsed time " + str(end - start))

    featureset_ref = wsname + '/' + featureset_id
    genomeObject['featureset_ref'] = featureset_ref
    start = time.time()

#    print simplejson.dumps(genomeObject,sort_keys=True,indent=4 * ' ')
    genome_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.Genome","data":genomeObject,"name":genomeObject['genome_id'],"provenance":[{"time":provenance_time_string,"service": "KBase Search","description":provenance_description}]}]})
    logger.info(genome_info)

    end = time.time()
    logger.info("insert genome into ws " + str(end - start))

if __name__ == "__main__":
    import argparse
    import os.path

    parser = argparse.ArgumentParser(description='Create KBasePublicRichGenome ws objects from flat file dumps from CS.')
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('--sorted-file-dir', nargs=1, help='path to sorted dump files to be parsed (default .)')
    parser.add_argument('--contigseq-file-dir', nargs=1, help='path to FASTA contig sequence files (filenames must correspond to KBase genome ids e.g., kb|g.0.fa) (default: use CDMI to get sequences)')
    parser.add_argument('--logging-file-dir', nargs=1, help='path to the directory to write the logging file (default .)')
    parser.add_argument('--skip-existing',action='store_true',help='skip processing genomes which already exist in ws')
    parser.add_argument('--debug',action='store_true',help='debugging')
    parser.add_argument('--skip-last',action='store_true',help='skip processing last genome (in case input is incomplete)')
    parser.add_argument('--database_version', nargs=1,help='This is the version of the central store database that was used to generate the datbase dump files.  Ex: \'V5\'')
    parser.add_argument('--search_version', nargs=1,help='This is the version of search used to populate the workspace.  Ex: \'V0.4\'')
    parser.add_argument('--genomes', action="store", nargs='*', help='list of genomes to do only')
#    parser.add_argument('--skip-till', nargs=1, help='skip genomes with numeric gid < SKIP_TILL (genome must exist)')

    args = parser.parse_args()

    wsname = args.wsname[0]

    logging_file_dir = '.'
    if args.logging_file_dir: 
        logging_file_dir = args.logging_file_dir[0]

    logging.basicConfig(filename=logging_file_dir + '/csFlatFiles_to_ws_'+ datetime.utcnow().isoformat() + '.log', format='%(name)s - %(asctime)s - %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

    logger = logging.getLogger('csFlatFiles_to_ws')
#    logger.debug("THIS IS A TEST")

    process_all_genomes = True
    ordered_selected_genomes_list = []
    max_genome_number = None
    if (args.genomes): 
        if (len(args.genomes) > 0):
            g_regex = re.compile('kb\|g.\d+$')
            process_all_genomes = False
            genomes_list = args.genomes
            genomes_dict = dict()
            for genome in genomes_list:
                g_match = g_regex.match(genome)
                if (not g_match):
                #genome string is not in expected format.
                    print "Entered Genome : " + genome + " is not in valid format. Exiting program."
                    logger.error("Entered Genome : " + genome + " is not in valid format.  Exiting program.")
                    sys.exit(0)
                selectedGidNumber = genome.split('.')[1]
                genomes_dict[genome] = int(selectedGidNumber)
            ordered_selected_genomes_list = sorted(genomes_dict.values())
#            logger.debug("Genome Numeric IDS entered : " + str(ordered_selected_genomes_list))
            max_genome_number = ordered_selected_genomes_list[-1]
        else:
            logger.error("program was run with the genomes argument.  However no genomes were passed.")
            print "program was run with the genomes argument.  However no genomes were passed."
            sys.exit(0)
    sorted_file_dir = '.'
    if args.sorted_file_dir:
        sorted_file_dir = args.sorted_file_dir[0]
    if args.skip_existing:
        skipExistingGenomes = True
    if args.contigseq_file_dir:
        contigseq_file_dir = args.contigseq_file_dir[0]
        if (not os.path.isdir(contigseq_file_dir)):
            logger.error("Contig directory " + contigseq_file_dir + " does not exist. Fix path in call.  Exiting program")
            print "Contig directory " + contigseq_file_dir + " does not exist.  Exiting program."
            sys.exit(0)

    database_version = None
    if args.database_version:
        database_version = args.database_version[0]

    search_version = None
    if args.search_version:
        search_version = args.search_version[0]

    # ws public instance
    ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")
    # ws team dev instance
    if args.debug:
#        ws = biokbase.workspace.client.Workspace("http://140.221.84.209:7058")
        ws = biokbase.workspace.client.Workspace("http://dev04:7058")
    logger.info('WS = ' + wsname)
    try:
        retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":"Search CS workspace"})
        logger.info('created workspace ' + wsname + ' at ws url ' + ws.url)
        logger.info(retval)
    # want this to catch only workspace exists errors
    except biokbase.workspace.client.ServerError, e:
        logger.info('workspace ' + wsname + ' at ws url ' + ws.url + ' may already exist, trying to use')

    genomeDataHandle = open ('Genome.tab','r')
    for line in genomeDataHandle:
        line=line.rstrip()
        thisGenome = dict()
        columns = line.split("\t")
        if len(columns) == 12:
            [ thisGenome['id'] , thisGenome['complete'] , thisGenome['contigs'] , thisGenome['dna_size'] , thisGenome['gc_content'] , thisGenome['genetic_code'] , thisGenome['pegs'] , thisGenome['rnas'], thisGenome['domain'], thisGenome['genome_md5'], thisGenome['scientific_name'], thisGenome['source_id']  ] = columns
        if len(columns) == 13:
            [ thisGenome['id'] , thisGenome['complete'] , thisGenome['contigs'] , thisGenome['dna_size'] , thisGenome['gc_content'] , thisGenome['genetic_code'] , thisGenome['pegs'] , thisGenome['rnas'], thisGenome['domain'], thisGenome['genome_md5'], thisGenome['scientific_name'], thisGenome['source_id'] ,thisGenome['taxonomy_id'] ] = columns
        all_genome_data[thisGenome['id']] = thisGenome
    genomeDataHandle.close()    

    logger.info('loading contig data into memory')
    contigDataHandle = open ('ContigSequence.tab','r')
    for line in contigDataHandle:
        line=line.rstrip()
        thisContig = dict()
        columns = line.split("\t")
        [ thisContig['genome_id'] , thisContig['id'] , thisContig['contig_md5'] , thisContig['length'] ] = columns
        if (not all_contig_data.has_key(thisContig['genome_id'])):
            all_contig_data[thisContig['genome_id']] = list()
        all_contig_data[thisContig['genome_id']].append(thisContig)
    contigDataHandle.close()
    logger.info('done loading contig data into memory')

    logger.info('loading taxonomy data into memory')
    taxonomyDataHandle = open ('TaxonomicGrouping.tab','r')
    for line in taxonomyDataHandle:
        line=line.rstrip()
        thisTaxonomy = dict()
        columns = line.split("\t")
        [ thisTaxonomy['taxonomy_id'] , thisTaxonomy['description'] , thisTaxonomy['parent_taxonomy_id'] , thisTaxonomy['hidden'], thisTaxonomy['domain'], thisTaxonomy['type'] ] = columns
        all_taxonomy_data[thisTaxonomy['taxonomy_id']] = thisTaxonomy
    taxonomyDataHandle.close()
    logger.info('done loading taxonomy data into memory')

    pubHandle = open ( 'publications.tab.sorted', 'r')
    for line in pubHandle:
        line=line.rstrip()
        thisPub = dict()
        columns = line.split("\t")
        if len(columns) == 7:
            [ thisPub['id'] , thisPub['link'] , thisPub['pubdate'] , thisPub['journal_name'] , thisPub['article_title'] , thisPub['article_title_sort'] , thisPub['authors'] , ] = columns
        if len(columns) == 8:
            # abstract is not in the typed object yet, but we could add
            # it in the future, so let's just save it
            [ thisPub['id'] , thisPub['link'] , thisPub['pubdate'] , thisPub['journal_name'] , thisPub['article_title'] , thisPub['article_title_sort'] , thisPub['authors'] , thisPub['abstract'] ] = columns
        publications[thisPub['id']] = thisPub
    pubHandle.close()

    fileHandle = dict()
    featureData = dict()
    currentLine = dict()
    currentNumericGid = -1
    currentGid = ''
#    if args.skip_till:
#        currentNumericGid = int(args.skip_till[0])
#        currentGid = 'kb|g.' + str(currentNumericGid)
#        print >> sys.stderr, 'skipping all genomes less than ' + str(currentNumericGid)

    fileList = ['Annotation','AtomicRegulons','CoexpressedFids','CoOccurringFids','Feature','fids2pubs','HasAliasAssertedFrom','Locations','ProteinFamilies','regulonData.members','regulonData.tfs','Roles','Subsystems','SubsystemData']
    attributeList = ['Annotation','AtomicRegulons','CoexpressedFids','CoOccurringFids','fids2pubs','HasAliasAssertedFrom','Locations','ProteinFamilies','regulonData.members','regulonData.tfs','Roles','Subsystems','SubsystemData']
    fileBegins = dict()
    fileEnds = dict()
    max_file_time = 0.0
    provenance_time_string = None

    for file in fileList:
#        fileName = sorted_file_dir + '/' + file + '.tab.sorted'
        fileName = file + '.tab.sorted'
        original_dump_fileName = file + '.tab'
# want to follow up why this was needed
#        fileHandle[file] = codecs.open( fileName, mode='r', encoding='ISO-8859-1')
#        fileHandle[file] = open ( fileName, 'r')
#        fileHandle[file] = open(os.path.join(sorted_file_dir, fileName), 'r')
        fileHandle[file] = TextFileDecoder.open_textdecoder(os.path.join(sorted_file_dir, fileName), 'ISO-8859-1')

        current_file_time = os.stat(fileName).st_mtime 
        if current_file_time > max_file_time : 
            max_file_time = current_file_time 
        if not process_all_genomes:
            #initialize begins to zero
            fileBegins[file] = 0 
            #initialize ends to last byte of files
            fileHandle[file].seek(0,2)
            fileEnds[file] =  fileHandle[file].tell()
            fileHandle[file].seek(0,0)
        # seed the first line
        currentLine[file] = fileHandle[file].readline()

    provenance_time_string = datetime.utcfromtimestamp(max_file_time).isoformat().split(".")[0] + "Z"

    #Provenance Description                                              
    provenance_description = "Data from Central Store "
    if database_version : 
        provenance_description = provenance_description + str(database_version) + " "   
    provenance_description = provenance_description + "at " + provenance_time_string + " using KBase Search"   
    if search_version : 
        provenance_description = provenance_description + " " + search_version   

### to do: allow user to specify --first-genome
### scan through all files till get to the target genome
### then continue as normal

    select_genome_counter = 0
    processing_new_genome = True
    
    while currentLine['Feature']: 
#        logger.debug("currentLine['Feature'] ", unicode(currentLine['Feature']))  
        [fid,cs_id,gid,restOfLine] = currentLine['Feature'].split("\t",3) 
#        logger.debug('FID: ' + fid + ',  CSID: ' + cs_id + ',  GID: ' + gid) 
        [prefix,numericGid] = gid.split('.') 
        numericGid = int(numericGid) 
#    print "starting new loop -- Processing new genome : " + str(processing_new_genome) 
        if (not process_all_genomes) and (processing_new_genome) :
            found_genome = False
            count = 0
            while (not found_genome) :
#                print "fg " + str(found_genome) + " " + str(type(found_genome))
                count += 1
                if count > 10:
                    sys.exit(1)
#                print "ORDERED SELECTED GENOMES_LIST : " + ('\t'.join(map(str,ordered_selected_genomes_list)))
                numericGid = ordered_selected_genomes_list[select_genome_counter]
                currentNumericGid = -1
                logger.info("Binary search for Feature")
                (found_genome,fileBegins['Feature']) = find_genome_first_line(fileHandle['Feature'], numericGid, fileBegins['Feature'], fileEnds['Feature'])
                #print "Genome : " + str(numericGid) + " -- Found Genome Feature : " + str(found_genome) + " -- File Begin : " + str(fileBegins['Feature']) 
                if (not found_genome):
                    select_genome_counter = select_genome_counter + 1
                else:
                    processing_new_genome = False
                if (select_genome_counter >= len(ordered_selected_genomes_list)):
                    break            
                    #or sys.exit(0)?
            fileHandle['Feature'].seek(fileBegins['Feature'],0)
            currentLine['Feature'] = fileHandle['Feature'].readline()
            [fid,cs_id,gid,restOfLine] = currentLine['Feature'].split("\t",3)                                                                          
        if (currentNumericGid == -1): 
            currentGid = gid 
            currentNumericGid = numericGid 
        if (numericGid > currentNumericGid): 
#            if (currentGid in genomes_dict.keys()) or process_all_genomes: 
            logger.info('gid is ' + gid) 
            logger.info('numericGid is ' + str(numericGid)) 
            logger.info('currentNumericGid is ' + str(currentNumericGid)) 
            # read other files and populate featureData
            for attribute in attributeList: 
                featureData[attribute] = list() 
#                processing_attribute = True
                if (not process_all_genomes): 
                    attribute_found_genome = False 
#                    print "ATTRIBUTE " + attribute
#                    print "INPUTS looking_for " + str(currentNumericGid) + "  Begin " + str(fileBegins[attribute]) + "  End " + str(fileEnds[attribute])
                    logger.info("Binary search for " + attribute)
                    (attribute_found_genome,fileBegins[attribute]) = find_genome_first_line(fileHandle[attribute], currentNumericGid, fileBegins[attribute], fileEnds[attribute]) 
                    logger.debug("Genome : " + str(currentNumericGid) + " -- Attribute " + attribute + " -- Found Genome ATTR : " + str(attribute_found_genome) + " -- File Begin : " + str(fileBegins[attribute]) + "   File Ends : " +  str(fileEnds[attribute]))  
                    fileHandle[attribute].seek(fileBegins[attribute],0) 
                    if (fileBegins[attribute] <  fileEnds[attribute]):
                        currentLine[attribute] = fileHandle[attribute].readline()
#                    if (attribute_found_genome):
#                        processing_attribute = False
                    if (not attribute_found_genome):
                        #genome is not in that attribute
#                        print "Did not find attribute for genome, moving to next attribute \n" 
                        logger.info("Did not find attribute for genome, moving to next attribute") 
                        continue
                while currentLine[attribute]: 
                    if len(currentLine[attribute].split('\t', 1)) == 2: 
                        [attrFid,attrRestOfLine] = currentLine[attribute].split("\t",1) 
                    else: 
                        logger.warning('suspect line : ' + currentLine[attribute]) 
                        logger.warning(currentLine[attribute].split(' ', 1)) 
                        if len(currentLine[attribute].strip()) == 0: 
                            logger.warning(attribute) 
                            #[attrFid, attrRestOfLine] = [,""]
                            #sys.exit(0)
                            #print >> sys.stderr, "skipping"
                            #continue
                        else: 
                            [attrFid,attrRestOfLine] = currentLine[attribute].split(" ",1) 
                            # this makes a huge amount of output 
                            #                    print >> sys.stderr, 'currentFid is ' + str(attrFid)
                            #                    print >> sys.stderr, 'attribute is ' + str(attribute)
                            #                    print >> sys.stderr, currentLine[attribute]
                    [attrGidPrefix,attrGidNumericId,rest] = attrFid.split('.',2) 
                    attrGid = attrGidPrefix + '.' + attrGidNumericId 
                    attrGidNumericId = int(attrGidNumericId) 
                    #IF genome of interest or processing all genomes :: aka a genome that will be processed 
                    if process_all_genomes or (attrGid in genomes_dict.keys()): 
                        if (attrGidNumericId == currentNumericGid): 
                            featureData[attribute].append(currentLine[attribute]) 
                    #If processing all genomes and you find unexpected data from a previous genome number 
                    if (attrGidNumericId < currentNumericGid) and process_all_genomes: 
                        logger.warning(attribute + ' file may have extra data, skipping') 
                        logger.warning(' '.join(str(x) for x in [attrGid, str(currentNumericGid)]))
                        break
                    #If the attribute genome number is higher than the current genome of interest, you know you have all the atrributes of this type for this genome
                    elif (attrGidNumericId > currentNumericGid): 
                        #IF genome of interest or processing all genomes :: aka a genome that will be processed
                        if process_all_genomes or (attrGid in genomes_dict.keys()): 
                            logger.info('Should be the last feature for this genome: attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)) 
                        break 
                    currentLine[attribute] = fileHandle[attribute].readline() 
            #            pp.pprint(featureData)
            # pass featureData to a sub that creates appropriate subobjects
#             if (currentGid in genomes_dict.keys()) or process_all_genomes:
            insert_genome(currentGid,ws,wsname,featureData,provenance_description,provenance_time_string) 
            
 
            # make sure Python does gc right away  
            featureData = None 
            featureData = dict()
            featureData['Feature'] = list()
            featureData['Feature'].append(currentLine['Feature'])
            currentNumericGid = numericGid 
            currentGid = gid 
            processing_new_genome = True
            logger.info('Current Genome : ' + currentGid) 

            if not process_all_genomes:
                select_genome_counter = select_genome_counter+1 
                if (select_genome_counter >= len(ordered_selected_genomes_list)):
                    break
#                if  (max_genome_number == numericGid):
#                    break
 
        elif (numericGid == currentNumericGid): 
            if not featureData.has_key('Feature'):
                featureData['Feature'] = list() 
            featureData['Feature'].append(currentLine['Feature']) 
 
#        if (numericGid < currentNumericGid and not args.skip_till):
        elif (numericGid < currentNumericGid): 
            logger.error('There is a big problem! Feature file may not be sorted properly.')
            logger.error(' '.join([str(numericGid), str(currentNumericGid)]))
            logger.error(currentLine['Feature']) 
            exit(5) 
 
#        if (numericGid < currentNumericGid and args.skip_till):
#            print >> sys.stderr, 'Skipping line'
#            print >> sys.stderr, ' '.join([str(numericGid), str(currentNumericGid)]) 
        if (not process_all_genomes) and (numericGid > max_genome_number):
            cleanup_filehandles(fileHandle) 
            sys.exit(0) 
        currentLine['Feature'] = fileHandle['Feature'].readline()
#END WHILE LOOP

    # process remaining features if not debugging
    # (need to skip if not parsing complete data set, since
    # if just taking a subset of export data, some files may
    # be incomplete, and you get key errors)
    if args.skip_last:
        logger.info('skipping last genome ' + gid)
        cleanup_filehandles(fileHandle.keys())
        exit(0)

    if process_all_genomes or (currentGid in genomes_dict.keys()): 
        logger.info('gid is ' + gid)
        logger.info('numericGid is ' + str(numericGid))
        logger.info('currentNumericGid is ' + str(currentNumericGid))
        # read other files and populate featureData
        for attribute in attributeList:
            featureData[attribute] = list()
            if (not process_all_genomes): 
                attribute_found_genome = False 
#               print "ATTRIBUTE " + attribute                                                                                                                    
#               print "INPUTS looking_for " + str(currentNumericGid) + "  Begin " + str(fileBegins[attribute]) + "  End " + str(fileEnds[attribute])              
                logger.info("Binary search for " + attribute) 
                (attribute_found_genome,fileBegins[attribute]) = find_genome_first_line(fileHandle[attribute], currentNumericGid, fileBegins[attribute], fileEnds[attribute]) 
                logger.debug("Genome : " + str(currentNumericGid) + " -- Attribute " + attribute + " -- Found Genome ATTR : " + str(attribute_found_genome) + " -- File Begin : " + str(fileBegins[attribute]) + "   File Ends : " +  str(fileEnds[attribute])) 
                fileHandle[attribute].seek(fileBegins[attribute],0) 
                if (fileBegins[attribute] <  fileEnds[attribute]): 
                    currentLine[attribute] = fileHandle[attribute].readline() 
#                if (attribute_found_genome):                                                                                                                      
#                    processing_attribute = False                                                                                                                  
                if (not attribute_found_genome): 
                    #genome is not in that attribute                                                                                                               
#                   print "Did not find attribute for genome, moving to next attribute \n"                                                                        
                    logger.info("Did not find attribute for genome, moving to next attribute") 
                    continue 
            while currentLine[attribute]:
                [attrFid,attrRestOfLine]=currentLine[attribute].split("\t",1)
                [attrGidPrefix,attrGidNumericId,rest] = attrFid.split('.',2)
                attrGid=attrGidPrefix+'.'+attrGidNumericId
                attrGidNumericId=int(attrGidNumericId)
                if process_all_genomes or (attrGid in genomes_dict.keys()): 
                    if (attrGidNumericId == currentNumericGid): 
                        featureData[attribute].append(currentLine[attribute]) 
                #If processing all genomes and you find unexpected data from a previous genome number 
                if (attrGidNumericId < currentNumericGid) and process_all_genomes: 
                    logger.warning(attribute + ' file may have extra data, skipping') 
                    logger.warning(' '.join(str(x) for x in [attrGid, str(currentNumericGid)])) 
                    break 
                #If the attribute genome number is higher than the current genome of interest, you know you have all the atrributes of this type for this genome   
                elif (attrGidNumericId > currentNumericGid): 
                    #IF genome of interest or processing all genomes :: aka a genome that will be processed                                                        
                    if process_all_genomes or (attrGid in genomes_dict.keys()): 
                        logger.info('Should be the last feature for this genome: attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)) 
                    break 
                currentLine[attribute] = fileHandle[attribute].readline() 
    # pass featureData to a sub that creates appropriate subobjects
        insert_genome(currentGid,ws,wsname,featureData,provenance_description,provenance_time_string)
        cleanup_filehandles(fileHandle)
    else:
        cleanup_filehandles(fileHandle)
        exit(0)
        
    
# general arch:
# open publications file
# read into structure
# close pubs
# open other files
# read from Features until gid is new, saving lines in structure
# read in other files and save to structures
# pass features structure and filehandles or structures to import_features
# create and return feature subobjects (in python)
# pass gid and feature subobjects to import_genome
# create FeatureSet object in ws
# create Genome object in ws
