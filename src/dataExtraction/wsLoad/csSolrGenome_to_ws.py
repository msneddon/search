#!/usr/bin/env python

# use this script to take genomes and features from CS (features via solr prep cores)
# and create WS objects
# use the ws-url command-line tool to set the active workspace service URL
# use kbase-login to set the appropriate auth token

import datetime
import sys
import simplejson
import time
import random
import requests

import biokbase.workspace.client
import biokbase.cdmi.client

# production instance
cdmi_api = biokbase.cdmi.client.CDMI_API()
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI()
ws = biokbase.workspace.client.Workspace()
# private instance
#cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
#cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')
#ws = biokbase.workspace.client.Workspace("http://localhost:7058", user_id='***REMOVED***', password='***REMOVED***')
# v3 instance
#cdmi_api = biokbase.cdmi.client.CDMI_API('http://140.221.84.182:7032')
#cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://140.221.84.182:7032')

solr_url_base = 'http://localhost:9077/search'
solr_admin_cores = '/admin/cores?wt=json'

solr_req = requests.get(solr_url_base+solr_admin_cores)
solr_cores = simplejson.loads(solr_req.text)

wsname = 'KBasePublicRichGenomes'

# set up a try block here?
try:
    retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":"Search CS workspace"})
# want this to catch only workspace exists errors
except biokbase.workspace.client.ServerError, e:
    pass
#    print >> sys.stderr, e

#kbase_sapling_db = MySQLdb.connect('192.168.1.85','kbase_sapselect','oiwn22&dmwWEe','kbase_sapling_v1')

# want to try to go in order to avoid repeats
genome_entities = cdmi_entity_api.all_entities_Genome(0,15000,['id','scientific_name','source_id'])
#genome_entities = cdmi_entity_api.all_entities_Genome(0,500,['id','scientific_name','source_id'])
#genome_entities = cdmi_entity_api.all_entities_Genome(60,500,['id','scientific_name','source_id'])
#genome_entities = cdmi_entity_api.all_entities_Genome(40,500,['id','scientific_name','source_id'])
genomes = genome_entities
#genomes = random.sample(genome_entities,500)

#genomes = sys.argv[1:]

# DvH, E.coli
# takes 4min (total) without dna_seqs, with coexpressed_fids
# takes 5min (total) with retrieving everything
#genomes = ['kb|g.3562','kb|g.0']
# arabidopsis--takes 50m with individual dna_seq calls (coexpressed_fids untested)
# takes much less time when cached
#genomes = ['kb|g.3899']
# poplar is only in the v3 instance right now
#genomes = ['kb|g.3907']
# more static sets
#genomes = ['kb|g.9','kb|g.222']
#genomes = ['kb|g.3562','kb|g.1494','kb|g.423']
#genomes = ['kb|g.19762','kb|g.1976']
#genomes = ['kb|g.0']
#genomes = ['kb|g.3562']
#genomes = ['kb|g.3562','kb|g.0']
# DvH, e.coli, multiple versions of arabidopsis
# what other genomes are essential?
#genomes = ['kb|g.3562','kb|g.0','kb|g.1105','kb|g.1103','kb|g.26509','kb|g.1104']
# kb|g.1103 has at least one feature with a bad location
#genomes = ['kb|g.3562','kb|g.0','kb|g.3899','kb|g.1105','kb|g.26509','kb|g.1104']
# chicken
#genomes = ['kb|g.3643']
#genomes = ['kb|g.26509']
# pseudomonas stutzeri (for microbes demo)
#genomes = ['kb|g.27073']

#genomeObjects = dict()


def insert_features(gid,fids):

    fids_to_insert = list()

    feature_list = 'feature_id%3A"' + '"+feature_id%3A"'.join(fids) + '"'
    # ws.save_objects(feature_objects)
    # return...mapping?

    core_data = dict()
    for core in solr_cores['status']:
        req = requests.get(solr_url_base + '/' + core + '/select?wt=json&rows=1000000&q=' + feature_list)
        core_data[core] = dict()
        data = simplejson.loads(req.text)
#        print >> sys.stderr, data
        for doc in data['response']['docs']:
            if not core_data[core].has_key(doc['feature_id']):
                core_data[core][doc['feature_id']] = list()
#            print >> sys.stderr, doc['feature_id']
            core_data[core][doc['feature_id']].extend([doc])
#    print >> sys.stderr, core_data

    for feature_id in fids:
        featureObject = dict()
        featureObject["feature_id"] = feature_id
        featureObject["genome_id"] = g
        featureObject["source"] = 'KBase Central Store'
        
        if core_data['Feature'].has_key(feature_id):
            this_feature=core_data['Feature'][feature_id][0]
            if this_feature.has_key('feature_type'):
                featureObject["feature_type"] = this_feature['feature_type']
            if this_feature.has_key('function'):
                featureObject["function"] = this_feature['function']
            if this_feature.has_key('sequence_length'):
                featureObject["dna_sequence_length"] = this_feature['sequence_length']
            if this_feature.has_key('source_id'):
                featureObject["feature_source_id"] = this_feature['source_id']

        if core_data['ProteinSeq'].has_key(feature_id):
            this_feature=core_data['ProteinSeq'][feature_id][0]
            if this_feature.has_key('md5'):
                featureObject["md5"] = this_feature['md5']
            if this_feature.has_key('sequence'):
                featureObject["protein_translation"] = this_feature['sequence']
                featureObject["protein_translation_length"] = len(this_feature['sequence'])

        if core_data['FeatureAlias'].has_key(feature_id):
            this_feature=core_data['FeatureAlias'][feature_id]
            featureObject["aliases"] = [ x['alias'] for x in this_feature ]

        if core_data['Location'].has_key(feature_id):
            this_feature=core_data['Location'][feature_id]
            locs = list()
            for loc in this_feature:
                this_loc = [ loc['contig_id'], loc['begin'], loc['dir'], loc['len'], loc['ordinal'] ] 
                locs.append(this_loc)
#            print >> sys.stderr, core_data['Location'][feature_id]
            featureObject["location"] = locs

        if core_data['Families'].has_key(feature_id):
            this_feature=core_data['Families'][feature_id]
            fams = list()
            for fam in this_feature:
                this_fam = dict()
                this_fam['id'] = fam['family_id']
                this_fam['release_version'] = fam['release']
                this_fam['subject_db'] = fam['type']
                if this_fam.has_key('family_function'):
                    this_fam['subject_description'] = fam['family_function']
                fams.append(this_fam)
#            print >> sys.stderr, core_data['Location'][feature_id]
            featureObject["protein_families"] = fams

        if core_data['Annotations'].has_key(feature_id):
            this_feature=core_data['Annotations'][feature_id]
            annos = list()
            for anno in this_feature:
                if anno.has_key('comment'):
                    this_anno = [ anno['comment'], anno['annotator'], anno['annotation_time'] ] 
                    annos.append(this_anno)
#            print >> sys.stderr, core_data['Location'][feature_id]
            featureObject["annotations"] = annos

        if core_data['Publications'].has_key(feature_id):
            this_feature=core_data['Publications'][feature_id]
            pubs = list()
            for pub in this_feature:
                this_pub = [ int(pub['pubmed_id']), 'PubMed', pub['article_title'], pub['pubmed_url'], pub['pubdate'], pub['authors'], pub['journal_title'] ] 
                pubs.append(this_pub)
#            print >> sys.stderr, core_data['Location'][feature_id]
            featureObject["feature_publications"] = pubs

        if core_data['Roles'].has_key(feature_id):
            this_feature=core_data['Roles'][feature_id]
            featureObject["roles"] = list()
            for x in this_feature:
#                featureObject["roles"] = [ x['role'] for x in this_feature ]
                if x.has_key('role'):
                    featureObject["roles"].append( x['role'] )
        if core_data['Subsystems'].has_key(feature_id):
            this_feature=core_data['Subsystems'][feature_id]
            featureObject["subsystems"] = [ x['subsystem'] for x in this_feature ]

        if core_data['SubsystemData'].has_key(feature_id):
            this_feature=core_data['SubsystemData'][feature_id]
#            print >> sys.stderr,this_feature
            subsystems = list()
            for subsys in this_feature:
                this_sys = [ subsys['subsystem'], subsys['variant'], subsys['role'] ] 
                subsystems.append(this_sys)
#            print >> sys.stderr, core_data['Location'][feature_id]
            featureObject["subsystem_data"] = subsystems

        if core_data['AtomicRegulons'].has_key(feature_id):
            this_feature=core_data['AtomicRegulons'][feature_id]
            ars = list()
            for ar in this_feature:
                this_ar = [ ar['atomic_regulon_id'], ar['atomic_regulon_size'] ] 
                ars.append(this_ar)
            featureObject["atomic_regulons"] = ars

        if core_data['CoOccurringFids'].has_key(feature_id):
            this_feature=core_data['CoOccurringFids'][feature_id]
            coos = list()
            for coo in this_feature:
                this_coo = [ coo['co_occurring_fid'], coo['score'] ] 
                coos.append(this_coo)
            featureObject["co_occurring_fids"] = coos

        if core_data['CoExpressedFids'].has_key(feature_id):
            this_feature=core_data['CoExpressedFids'][feature_id]
            coes = list()
            for coe in this_feature:
                this_coe = [ coe['co_expressed_fid'], coe['score'] ] 
                coes.append(this_coe)
            featureObject["coexpressed_fids"] = coes

        if core_data['RegulonData'].has_key(feature_id):
            this_feature=core_data['RegulonData'][feature_id]
            regulons = list()
            for reg in this_feature:
                regulon_set = reg['regulon_set'].split(',')
                tfs = list()
                if reg.has_key('tfs'):
                    tfs = reg['tfs'].split(',')
                this_reg = [ reg['regulon_id'], regulon_set, tfs ] 
                regulons.append(this_reg)
            featureObject["regulon_data"] = regulons

        fids_to_insert.append( { "type":"KBaseSearch.Feature","data":featureObject,"name":feature_id } )

#        print >> sys.stderr, simplejson.dumps(featureObject,sort_keys=True,indent=4 * ' ')
        
    feature_info = ws.save_objects({"workspace":wsname,"objects": fids_to_insert })

    return feature_info


for g in genomes:
    start = time.time()

    # maybe use get_entity_Genome to get additional fields, like source_id and domain?
    genome_data = cdmi_api.genomes_to_genome_data([g])[g]

    end = time.time()
    print >> sys.stderr, "querying genome_data " + str(end - start)

    if 'Pseudomonas' not in genome_data['scientific_name']:
        print >> sys.stderr, "skipping genome " + g + ' ' + genome_entities[g]['scientific_name']
        continue
    print >> sys.stderr, "processing genome " + g + ' ' + genome_entities[g]['scientific_name']

    try:
        ws.get_object_info([{"workspace":wsname,"name":g}],0)
#        print >> sys.stderr, 'genome '  + g + ' found, updating'
        print >> sys.stderr, 'genome '  + g + ' found, skipping'
        continue
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'genome '  + g + ' not found, adding to ws'

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
    if genome_data.has_key('taxonomy'):
        genomeObject["taxonomy"] = genome_data["taxonomy"]
        genomeObject["domain"] = genome_data['taxonomy'].split(';')[0]
    genomeObject["gc_content"] = float(genome_data["gc_content"])
    genomeObject["complete"] = int(genome_data["complete"])

    genomeObject["genome_source_id"] = genome_entities[g]['source_id']

    genomeObject["contig_lengths"] = dict()

    #genomeObject["contigset_ref"] = 
    #genomeObject["proteinset_ref"] = 
    #genomeObject["transcriptset_ref"] = 

    #start = time.time()

    #taxonomy = cdmi_api.genomes_to_taxonomies([g])[g]

    #end = time.time()
    #print >> sys.stderr, "querying taxonomies " + str(end - start)

##########################
    # build ContigSet and Contig objects
    # ultimately we will want to build ContigSet independent of
    # the Genome object, insert it first, get its workspace path,
    # then use that to populate contigset_ref in the Genome object

    contigSet = dict()

    contigSet["id"] = g+".contigset.0"
    contigSet["name"] = "contigset for " + g
    contigSet["md5"] = genomeObject["md5"]
#    contigSet["source_id"] = ""
    contigSet["source"] = "KBase Central Store"
    contigSet["type"] = "Organism"
#    contigSet["reads_ref"] = None
#    contigSet["fasta_ref"] = None
    contigSet["contigs"] = dict()

    start = time.time()

    contig_ids = cdmi_api.genomes_to_contigs([g])[g]

    genomeObject['contig_ids'] = contig_ids

    end = time.time()
    print  >> sys.stderr, "querying contig ids " + str(end - start)

    start = time.time()

    # retrieving all with one call died on kb|g.3907, kb|g.3643 Gallus gallus, kb|g.41 Mouse
    # looping over each contig_id still seems slow on chicken
    contig_sequences = dict()
    for contig_id in contig_ids:
        contig_seq = cdmi_api.contigs_to_sequences([contig_id])
        contig_sequences[contig_id] = contig_seq[contig_id]

    end = time.time()
    print  >> sys.stderr, "querying contig seqs " + str(end - start)

    start = time.time()

    contig_lengths = cdmi_api.contigs_to_lengths(contig_ids)

    end = time.time()
    print  >> sys.stderr, "querying contig lengths " + str(end - start)

    start = time.time()

    contig_md5s = cdmi_api.contigs_to_md5s(contig_ids)

    end = time.time()
    print  >> sys.stderr, "querying contig md5s " + str(end - start)

    for x in contig_ids:
        contig = dict()
        contig["id"] = x
        contig["length"] = int(contig_lengths[x])
        contig["md5"] = contig_md5s[x]
        contig["sequence"] = contig_sequences[x]
        
        contigSet["contigs"][x]=contig
        
        genomeObject["contig_lengths"][x]=int(contig_lengths[x])

    # will need to insert the ContigSet object here, in order to
    # be able to use the ref in Feature.location
    # will also need to build a mapping of contig_ids to contigrefs
    # put in existing contigSet?  might get confusing

    start = time.time()

# first see if object already exists
    try:
        contigset_info=ws.get_object_info([{"workspace":wsname,"name":contigSet['id']}],0)
#        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' found, updating'
        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' found, skipping'
#        continue
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'contigset '  + contigSet['id'] + ' not found, adding to ws'
        # this will reference a ContigSet object
        #print simplejson.dumps(contigSet,sort_keys=True,indent=4 * ' ')
        # another try block here?
        contigset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.ContigSet","data":contigSet,"name":contigSet['id']}]})

    end = time.time()
    print >> sys.stderr, "inserting contigset into ws " + str(end - start)
    print >> sys.stderr, contigset_info

    contigset_ref = wsname + '/' + contigSet['id']
    genomeObject["contigset_ref"] = contigset_ref

###########################
    # build Feature objects

    # feature ids
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    start = time.time()
    fids_to_insert = list()

    for x in fids:
        fids_to_insert.append( x )
        if len(fids_to_insert) > 99:

             feature_info = insert_features(g,fids_to_insert)
             for ws_feature in feature_info:
                 print >> sys.stderr, ws_feature
                 if not featureSet['features'].has_key(ws_feature[1]):
                     featureSet['features'][ws_feature[1]] = dict()
                 featureSet['features'][ws_feature[1]] = ws_feature[7] + '/' + ws_feature[1]

             fids_to_insert = list()

    # final fids to insert (batching code)
    if len(fids_to_insert) > 0:
         feature_info = insert_features(g,fids_to_insert)
         for ws_feature in feature_info:
             print >> sys.stderr, ws_feature
             if not featureSet['features'].has_key(ws_feature[1]):
                 featureSet['features'][ws_feature[1]] = dict()
             featureSet['features'][ws_feature[1]] = ws_feature[7] + '/' + ws_feature[1]

    end = time.time()
    print  >> sys.stderr, " processing features, elapsed time " + str(end - start)

    # insert into workspace, get path
#    print simplejson.dumps(featureSet,sort_keys=True,indent=4 * ' ')
    # another try block here?
    featureset_id = genomeObject['genome_id'] + '.featureset'
    featureset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.FeatureSet","data":featureSet,"name":featureset_id}]})
    print >> sys.stderr, featureset_info

    featureset_ref = wsname + '/' + featureset_id
    genomeObject['featureset_ref'] = featureset_ref
    start = time.time()

#    print simplejson.dumps(genomeObject,sort_keys=True,indent=4 * ' ')
    genome_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.Genome","data":genomeObject,"name":genomeObject['genome_id']}]})
    print >> sys.stderr, genome_info

    end = time.time()
    print  >> sys.stderr, "insert genome into ws " + str(end - start)
