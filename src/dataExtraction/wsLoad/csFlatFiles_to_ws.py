#!/usr/bin/env python

# use this script to take genomes and features from CS (via flat files
# generated from SQL dumps)
# and create WS objects
# use the ws-url command-line tool to set the active workspace service URL
# use kbase-login to set the appropriate auth token

import datetime
import sys
import simplejson
import time
import random
import requests
import pprint
import codecs
import Bio.SeqIO
import Bio.SeqFeature

import biokbase.workspace.client
import biokbase.cdmi.client

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
    newFeatureLocations = list()
    lastLoc = list()
    for index,loc in enumerate(featureLocations):
#        print >> sys.stderr, 'start loop'
#        print >> sys.stderr, lastLoc
#        print >> sys.stderr, loc
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
#        print >> sys.stderr, 'end loop'
#        print >> sys.stderr, lastLoc
    # append the last location
    newFeatureLocations.append(lastLoc)
    return newFeatureLocations

def create_feature_objects(gid,genetic_code,featureData,contigSeqObjects):

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
        print >> sys.stderr, 'too many lines of coexpressedfids for ' + genome_id + ', skipping'
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
    for location_line in featureData['Locations']:
        location_line=location_line.rstrip()
        [fid,contig,begin,strand,length,ordinal]=location_line.split("\t")
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
#        print >> sys.stderr, featureLocations[fid]
        featureObjects[fid]['location'] = join_contiguous_locations(featureLocations[fid])
#        print >> sys.stderr, featureObjects[fid]['location']
        if len(featureObjects[fid]['location']) > 0:
#            print >> sys.stderr, 'making feature_dna for ' + fid + ' on contig ' + featureObjects[fid]['location'][0][0]
            if not featureObjects[fid].has_key('dna_sequence'):
                featureObjects[fid]['dna_sequence'] = ''

            locations = featureObjects[fid]['location']
            # some genomes have the list of locations in reverse order
            # jkbaumohl is researching
            # if featureObjects[fid]['location'][0][2] == '-':
            #     locations = reversed(featureObjects[fid]['location'])

            for loc in locations:
#                if loc[3] > 100000 and (featureObjects[fid]['feature_type'] != 'CDS' or len(featureObjects[fid]['protein_sequence']) < 30000 ) :
                if loc[3] > 100000 and len(featureObjects[fid]['protein_translation']) < 30000 :
                    print >> sys.stderr, 'warning: dna sequence for feature ' + fid + ' is much too long (compared to CS protein sequence if a CDS), skipping'
                    featureObjects[fid]['dna_sequence'] = ''
                    break
                if loc[2] == '-':
                    featSeqFeature = Bio.SeqFeature.SeqFeature(Bio.SeqFeature.FeatureLocation( loc[1] - loc[3], loc[1], strand=-1 ), id=fid+'/data/location/'+str(loc[4]))
                else: # assume + strand
                    featSeqFeature = Bio.SeqFeature.SeqFeature(Bio.SeqFeature.FeatureLocation( (loc[1]-1), (loc[1]-1) + loc[3], strand=+1 ), id=fid+'/data/location/'+str(loc[4]))
#                    print >> sys.stderr, featSeqFeature
#                    print >> sys.stderr, featSeqFeature.extract( contigSeqObjects[loc[0]])
                if contigSeqObjects.has_key(loc[0]):
                    featureObjects[fid]['dna_sequence'] += str(featSeqFeature.extract( contigSeqObjects[loc[0]]).seq)

#            print >> sys.stderr, 'genetic_code is ' + str(genetic_code)
#            print >> sys.stderr, fid

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

#            print >> sys.stderr, genetic_code
#            print >> sys.stderr, fid

            try:
                if featureObjects[fid]['feature_type'] == 'CDS' and (featureObjects[fid]['protein_translation'] + stop_codon != Bio.Seq.translate( featureObjects[fid]['dna_sequence'], cds=complete_cds,table=genetic_code) ) :
                    print >> sys.stderr, 'warning: computed translation does not match translation in db for ' + fid
                    if featureObjects[fid]['protein_translation'].find('X'):
                        print >> sys.stderr, 'X found in CS translation, not worrying about'
                    else:
                        print >> sys.stderr, featureObjects[fid]['protein_translation'] + stop_codon
                        print >> sys.stderr, cdmi_api.fids_to_dna_sequences([fid])
                        print >> sys.stderr, cdmi_api.fids_to_locations([fid])
                        print >> sys.stderr, featureObjects[fid]['location']
                        print >> sys.stderr, Bio.Seq.translate( featureObjects[fid]['dna_sequence'], cds=complete_cds,table=genetic_code)
                        print >> sys.stderr, featureObjects[fid]['dna_sequence']
#                        print >> sys.stderr, str(featSeqFeature.extract( contigSeqObjects[loc[0]]).seq.translate(table=genetic_code, cds=complete_cds) )
            except Bio.Data.CodonTable.TranslationError, e:
                print >> sys.stderr, 'possible problem with translation of fid ' + fid
                print >> sys.stderr, str(e)
                print >> sys.stderr, featureObjects[fid]['function']

        else:
            print >> sys.stderr, 'no locations for ' + fid + ', not making feature_dna'

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
#            regulon_id = fids2regulons[fid]
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
            print >> sys.stderr, 'missing data found in Role line'
            print >> sys.stderr, e
            print >> sys.stderr, roles_line
            print >> sys.stderr, 'skipping line'
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
    if not all_taxonomy_data.has_key(taxonomy_id):
        return ''
    if int(all_taxonomy_data[taxonomy_id]['domain']) == 1:
        return all_taxonomy_data[taxonomy_id]['description']

    if int(all_taxonomy_data[taxonomy_id]['hidden']) == 0:
        return '; '.join([ compute_taxonomy_lineage(all_taxonomy_data[taxonomy_id]['parent_taxonomy_id']) , all_taxonomy_data[taxonomy_id]['description'] ])
    else:
        return compute_taxonomy_lineage(all_taxonomy_data[taxonomy_id]['parent_taxonomy_id'])

def insert_genome(g,ws,wsname,featureData):

    start = time.time()

    numericGid = int(g.split('.')[1])
    print >> sys.stderr, g
    print >> sys.stderr, numericGid
    
    try:
        ws.get_object_info([{"workspace":wsname,"name":g}],0)
        if skipExistingGenomes == True:
            print >> sys.stderr, 'genome '  + g + ' found, skipping'
            return
        print >> sys.stderr, 'genome '  + g + ' found, replacing'
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'genome '  + g + ' not found, adding to ws'

#    all_genome_data = cdmi_api.genomes_to_genome_data([g])
    genome_data = dict()
    if all_genome_data.has_key(g):
        genome_data = all_genome_data[g]
    else:
        print >> sys.stderr, 'genome ' + g + ' has no entry in genome data, skipping'
        return

    end = time.time()
    print >> sys.stderr, "querying genome_data " + str(end - start)

#    if 'P' not in genome_data['scientific_name']:
    # sloppy hack to pick up where it crashed
#    if numericGid < 2207:
#    if numericGid < 28878:
#        print >> sys.stderr, "skipping genome " + g + ' ' + genome_data['scientific_name']
#        return
    print >> sys.stderr, "processing genome " + g + ' ' + genome_data['scientific_name']

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

    print  >> sys.stderr, "start querying contig seqs"

    # retrieving all with one call died on kb|g.3907, kb|g.3643 Gallus gallus, kb|g.41 Mouse
    # looping over each contig_id still seems slow on chicken
    # these sequences are too big for ws (250MB), need to refactor

    contig_sequences = dict()
    contigSeqObjects = dict()

    if contigseq_file_dir == '':
        print >> sys.stderr, 'no contig path defined, using CDMI'

        # loop over contigs method
        for contig_id in genomeObject['contig_ids']:
#            contig_seq = cdmi_api.contigs_to_sequences([contig_id])
#            contig_sequences[contig_id] = contig_seq[contig_id]
            # for debugging, don't get contig seqs
            contig_sequences[contig_id] = ''

        # all in one call (has been working so far)
        contig_sequences = cdmi_api.contigs_to_sequences(genomeObject['contig_ids'])

    else:
        print >> sys.stderr, 'contig path defined, attempting to read file in ' + contigseq_file_dir
        try:
            contig_handle = open (contigseq_file_dir + '/' + g + '.fa', 'rU')
            contigSeqObjects = Bio.SeqIO.to_dict( Bio.SeqIO.parse(contig_handle,'fasta') )
            for contigseq in contigSeqObjects:
#                print >> sys.stderr, contigseq
                contig_sequences[contigseq] = str(contigSeqObjects[contigseq].seq)
            contig_handle.close()
            print >> sys.stderr, 'reading contig file succeeded'
        except Exception, e:
            print >> sys.stderr, 'problem reading contig file for ' + g
            print >> sys.stderr, e
            print >> sys.stderr, 'attempting to use CDMI instead'
            contig_sequences = cdmi_api.contigs_to_sequences(genomeObject['contig_ids'])
            # need to make contigSeqObjects here


    end = time.time()
    print  >> sys.stderr, "done querying contig seqs " + str(end - start)

    for x in contigs:
        contig = dict()
        contig["id"] = x['id']
        contig["length"] = int(x['length'])
        contig["md5"] = x['contig_md5']
        if contig_sequences.has_key(x['id']):
            contig["sequence"] = contig_sequences[x['id']]
        else:
            print >> sys.stderr, 'contig ' + x['id'] + ' does not have sequence defined, setting to empty'
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
        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' found, replacing'
#        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' found, skipping'
#        continue
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' not found, adding to ws'
        # this will reference a ContigSet object
        #print simplejson.dumps(contigSet,sort_keys=True,indent=4 * ' ')
        # another try block here?

    try:
        contigset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.ContigSet","data":contigSet,"name":contigSet['id']}]})
        print >> sys.stderr, contigset_info
    except biokbase.workspace.client.ServerError, e:
        print >> sys.stderr, e

    end = time.time()
    print >> sys.stderr, "inserting contigset into ws " + str(end - start)
#    print >> sys.stderr, contigset_info

    contigset_ref = wsname + '/' + contigSet['id']
    genomeObject["contigset_ref"] = contigset_ref

###########################
    # build Feature objects

    start  = time.time()

    # with any luck this can be used directly when saving a FeatureSet
    featureObjects = create_feature_objects(gid,genomeObject['genetic_code'],featureData,contigSeqObjects)

    
    featureSet['features'] = dict()
    for feature in featureObjects:
        #print >> sys.stderr, feature 
        #print >> sys.stderr, featureObjects[feature]
        individualFeature = dict()
        individualFeature['data'] = featureObjects[feature]
        featureSet['features'][feature] = individualFeature
        
#    pp.pprint(featureObjects)

    end = time.time()
    print  >> sys.stderr, " processing features, elapsed time " + str(end - start)

    # for debugging
#    return 

    # insert into workspace, get path
#    print simplejson.dumps(featureSet,sort_keys=True,indent=4 * ' ')
    # another try block here?
    featureset_id = genomeObject['genome_id'] + '.featureset'

    start  = time.time()

#    print >> sys.stderr, simplejson.dumps(featureSet)

    featureSetType='KBaseSearch.SearchFeatureSet'
    if args.debug:
        featureSetType='KBaseSearch.FeatureSet'
    featureset_info = ws.save_objects({"workspace": wsname,
#                                       "objects":[{"type": "KBaseSearch.FeatureSet",
#                                       "objects":[{"type": "KBaseSearch.SearchFeatureSet",
                                       "objects":[{"type": featureSetType,
                                                   "data": featureSet,
                                                   "name": featureset_id}]
                                     })
    end = time.time()
    print  >> sys.stderr, " saving featureset to ws, elapsed time " + str(end - start)
    print >> sys.stderr, featureset_info

    featureset_ref = wsname + '/' + featureset_id
    genomeObject['featureset_ref'] = featureset_ref
    start = time.time()

#    print simplejson.dumps(genomeObject,sort_keys=True,indent=4 * ' ')
    genome_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.Genome","data":genomeObject,"name":genomeObject['genome_id']}]})
    print >> sys.stderr, genome_info

    end = time.time()
    print  >> sys.stderr, "insert genome into ws " + str(end - start)

if __name__ == "__main__":
    import argparse
    import os.path

    parser = argparse.ArgumentParser(description='Create solr tab-delimited import files from flat file dumps from CS.')
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('--sorted-file-dir', nargs=1, help='path to sorted dump files to be parsed (default .)')
    parser.add_argument('--contigseq-file-dir', nargs=1, help='path to FASTA contig sequence files (filenames must correspond to KBase genome ids e.g., kb|g.0.fa) (default: use CDMI to get sequences)')
    parser.add_argument('--skip-existing',action='store_true',help='skip processing genomes which already exist in ws')
    parser.add_argument('--debug',action='store_true',help='debugging')
    parser.add_argument('--skip-last',action='store_true',help='skip processing last genome (in case input is incomplete)')

    args = parser.parse_args()

    wsname = args.wsname[0]

    sorted_file_dir = '.'
    if args.sorted_file_dir:
        sorted_file_dir = args.sorted_file_dir[0]
    if args.skip_existing:
        skipExistingGenomes = True
    if args.contigseq_file_dir:
        contigseq_file_dir = args.contigseq_file_dir[0]

    # ws public instance
    ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")
    # ws team dev instance
    if args.debug:
#        ws = biokbase.workspace.client.Workspace("http://140.221.84.209:7058", user_id='***REMOVED***', password='***REMOVED***')
        ws = biokbase.workspace.client.Workspace("http://dev04:7058", user_id='***REMOVED***', password='***REMOVED***')

    print >> sys.stderr, wsname
    try:
        retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":"Search CS workspace"})
        print >> sys.stderr, 'created workspace ' + wsname + ' at ws url ' + ws.url
        print >> sys.stderr, retval
    # want this to catch only workspace exists errors
    except biokbase.workspace.client.ServerError, e:
        print >> sys.stderr, 'workspace ' + wsname + ' at ws url ' + ws.url + ' may already exist, trying to use'

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

    print >> sys.stderr, 'loading contig data into memory'
    contigDataHandle = open ('ContigSequence.tab','r')
    for line in contigDataHandle:
        line=line.rstrip()
        thisContig = dict()
        columns = line.split("\t")
        [ thisContig['genome_id'] , thisContig['id'] , thisContig['contig_md5'] , thisContig['length'] ] = columns
        if (not all_contig_data.has_key(thisContig['genome_id'])):
            all_contig_data[thisContig['genome_id']] = list()
        all_contig_data[thisContig['genome_id']].append(thisContig)
    print >> sys.stderr, 'done loading contig data into memory'

    print >> sys.stderr, 'loading taxonomy data into memory'
    taxonomyDataHandle = open ('TaxonomicGrouping.tab','r')
    for line in taxonomyDataHandle:
        line=line.rstrip()
        thisTaxonomy = dict()
        columns = line.split("\t")
        [ thisTaxonomy['taxonomy_id'] , thisTaxonomy['description'] , thisTaxonomy['parent_taxonomy_id'] , thisTaxonomy['hidden'], thisTaxonomy['domain'], thisTaxonomy['type'] ] = columns
        all_taxonomy_data[thisTaxonomy['taxonomy_id']] = thisTaxonomy
    print >> sys.stderr, 'done loading taxonomy data into memory'

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

    fileHandle = dict()
    featureData = dict()
    currentLine = dict()
    currentNumericGid = -1
    currentGid = ''

    fileList = ['Annotation','AtomicRegulons','CoexpressedFids','CoOccurringFids','Feature','fids2pubs','HasAliasAssertedFrom','Locations','ProteinFamilies','regulonData.members','regulonData.tfs','Roles','Subsystems','SubsystemData']
    attributeList = ['Annotation','AtomicRegulons','CoexpressedFids','CoOccurringFids','fids2pubs','HasAliasAssertedFrom','Locations','ProteinFamilies','regulonData.members','regulonData.tfs','Roles','Subsystems','SubsystemData']

    for file in fileList:
        fileName = sorted_file_dir + '/' + file + '.tab.sorted'
# want to follow up why this was needed
        fileHandle[file] = codecs.open ( fileName, mode='r', encoding='ISO-8859-1')
#        fileHandle[file] = open ( fileName, 'r')
        # seed the first line
        currentLine[file] = fileHandle[file].readline()

    while currentLine['Feature']:
#        print >> sys.stderr, "currentLine['Feature'] ", unicode(currentLine['Feature'])

        [fid,cs_id,gid,restOfLine] = currentLine['Feature'].split("\t",3)
        #print >> sys.stderr, [fid, cs_id, gid]

        [prefix,numericGid] = gid.split('.')
        numericGid = int(numericGid)

        if (currentNumericGid == -1):
            currentGid = gid
            currentNumericGid = numericGid
        if (numericGid > currentNumericGid):
            print >> sys.stderr, 'gid is ' + gid
            print >> sys.stderr, 'numericGid is ' + str(numericGid)
            print >> sys.stderr, 'currentNumericGid is ' + str(currentNumericGid)
            
            # read other files and populate featureData
            for attribute in attributeList:
                featureData[attribute] = list()
                while currentLine[attribute]:
                    if len(currentLine[attribute].split('\t', 1)) == 2:                    
                        [attrFid,attrRestOfLine] = currentLine[attribute].split("\t",1)
                    else:
                        print >> sys.stderr, 'suspect line : ' + currentLine[attribute]
                        print >> sys.stderr, currentLine[attribute].split(' ', 1)

                        if len(currentLine[attribute].strip()) == 0:
                            print >> sys.stderr, attribute                      
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
#                    print >> sys.stderr, 'attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)
                    if (attrGidNumericId == currentNumericGid):
                        featureData[attribute].append(currentLine[attribute])
                    if (attrGidNumericId < currentNumericGid):
                        print >> sys.stderr, attribute + ' file may have extra data, skipping'
                        print >> sys.stderr, ' '.join([attrGid, str(currentNumericGid)])
                    if (attrGidNumericId > currentNumericGid):
                        print >> sys.stderr, 'Should be the last feature for this genome: attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)
                        break
                    currentLine[attribute] = fileHandle[attribute].readline()
#            pp.pprint(featureData)
            # pass featureData to a sub that creates appropriate subobjects
            insert_genome(currentGid,ws,wsname,featureData)

            # make sure Python does gc right away
            featureData = None
            featureData = dict()
            featureData['Feature'] = list()
            featureData['Feature'].append(currentLine['Feature'])
            currentNumericGid = numericGid
            currentGid = gid
        if (numericGid == currentNumericGid):
            if not featureData.has_key('Feature'):
                featureData['Feature'] = list()
            featureData['Feature'].append(currentLine['Feature'])
        if (numericGid < currentNumericGid):
            print >> sys.stderr, 'There is a big problem! Feature file may not be sorted properly.'
            print >> sys.stderr, ' '.join([numericGid, currentNumericGid])
            print >> sys.stderr, currentLine['Feature']
            exit(5)
        currentLine['Feature'] = fileHandle['Feature'].readline()

    # process remaining features if not debugging
    # (need to skip if not parsing complete data set, since
    # if just taking a subset of export data, some files may
    # be incomplete, and you get key errors)
    if args.skip_last:
        print >> sys.stderr, 'skipping last genome ' + gid
        exit(0)

    print >> sys.stderr, 'gid is ' + gid
    print >> sys.stderr, 'numericGid is ' + str(numericGid)
    print >> sys.stderr, 'currentNumericGid is ' + str(currentNumericGid)
    # read other files and populate featureData
    for attribute in attributeList:
        featureData[attribute] = list()
        while currentLine[attribute]:
            [attrFid,attrRestOfLine]=currentLine[attribute].split("\t",1)
            [attrGidPrefix,attrGidNumericId,rest] = attrFid.split('.',2)
            attrGid=attrGidPrefix+'.'+attrGidNumericId
            attrGidNumericId=int(attrGidNumericId)
#            print >> sys.stderr, 'attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)
            if (attrGidNumericId == currentNumericGid):
                featureData[attribute].append(currentLine[attribute])
            if (attrGidNumericId < currentNumericGid):
                print >> sys.stderr, attribute + ' file may have extra data, skipping'
                print >> sys.stderr, ' '.join([attrGid, currentNumericGid])
            if (attrGidNumericId > currentNumericGid):
                print >> sys.stderr, 'need to skip to next attribute here: attrGid for ' + attribute + ' is ' + attrGid + ' for currentNumericGid ' + str(currentNumericGid)
                break
            currentLine[attribute] = fileHandle[attribute].readline()
#    pp.pprint(featureData)
    # pass featureData to a sub that creates appropriate subobjects
    insert_genome(currentGid,ws,wsname,featureData)

    
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
