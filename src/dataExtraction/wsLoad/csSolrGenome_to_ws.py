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

#for core in solr_cores['status']:
#    print core + ': ' + str(solr_cores['status'][core]['index']['numDocs'])


wsname = 'KBasePublicRichGenomes'

# set up a try block here?
try:
    retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":"Search CS workspace"})
# want this to catch only workspace exists errors
except biokbase.workspace.client.ServerError, e:
    pass
#    print >> sys.stderr, e

#kbase_sapling_db = MySQLdb.connect('192.168.1.85','kbase_sapselect','oiwn22&dmwWEe','kbase_sapling_v1')

genome_entities = cdmi_entity_api.all_entities_Genome(0,15000,['id','scientific_name','source_id'])
genomes = random.sample(genome_entities,500)

#genomes = sys.argv[1:]

# DvH, E.coli
# takes 4min (total) without dna_seqs, with coexpressed_fids
# takes 5min (total) with retrieving everything
#genomes = ['kb|g.3562','kb|g.0']
# arabidopsis--takes 50m with individual dna_seq calls (coexpressed_fids untested)
# takes much less time when cached
#genomes = ['kb|g.3899']
# poplar is only in the v3 instance right now
genomes = ['kb|g.3907']
# more static sets
#genomes = ['kb|g.9','kb|g.222']
#genomes = ['kb|g.3562','kb|g.1494','kb|g.423']
#genomes = ['kb|g.19762','kb|g.1976']
#genomes = ['kb|g.0']
genomes = ['kb|g.3562']
#genomes = ['kb|g.3562','kb|g.0']
# DvH, e.coli, multiple versions of arabidopsis
# what other genomes are essential?
#genomes = ['kb|g.3562','kb|g.0','kb|g.1105','kb|g.1103','kb|g.26509','kb|g.1104']
# kb|g.1103 has at least one feature with a bad location
#genomes = ['kb|g.3562','kb|g.0','kb|g.3899','kb|g.1105','kb|g.26509','kb|g.1104']
# chicken
#genomes = ['kb|g.3643']

#genomeObjects = dict()


def insert_features(fids):

    feature_list = 'feature_id%3A"' + '"+feature_id%3A"'.join(fids) + '"'
    # for each core, make a request
    # use results to populate feature objects
    # ws.save_objects(feature_objects)
    # return...mapping?
    feature_req = requests.get(solr_url_base + '/Feature/select?wt=json&rows=100&q=' + feature_list)
    print >> sys.stderr, feature_req.text
    return

    featureObject = dict()
    featureObject["feature_id"] = x
    featureObject["genome_id"] = g
    featureObject["source"] = 'KBase Central Store'
    
    if locations.has_key(x):
        featureObject["location"] = locations[x]
    
    if features.has_key(x):
        featureObject["feature_type"] = features[x]['feature_type']
        featureObject["function"] = features[x]['function']
        
        if features[x].has_key('alias'):
            featureObject["aliases"] = features[x]['alias']
    
    if proteins.has_key(x):
        featureObject["md5"] = proteins[x]

        if protein_translations.has_key(proteins[x]):
            featureObject["protein_translation"] = protein_translations[proteins[x]]['sequence']
            featureObject["protein_translation_length"] = len(featureObject["protein_translation"])

    # we are not going to retrieve dna sequence, see if it saves time
#        featureObject["dna_sequence"] = cdmi_api.fids_to_dna_sequences([x])
#        featureObject["dna_sequence_length"] = len(featureObject["dna_sequence"])

    if protein_families.has_key(x):
        featureObject["protein_families"] = protein_families[x]
    
    if annotations.has_key(x):
        featureObject["annotations"] = annotations[x]
    
    if publications.has_key(x):
        featureObject["feature_publications"] = publications[x]
    
    if roles.has_key(x):
        featureObject["roles"] = roles[x]
    
    if subsystems.has_key(x):
        featureObject["subsystems"] = subsystems[x]
    
    if subsystem_data.has_key(x):
        featureObject["subsystem_data"] = subsystem_data[x]
    
    if regulon_data.has_key(x):
        x_reg=list()
        for reg in regulon_data[x]:
            this_reg=list()
            this_reg.append(reg['regulon_id'])
            this_reg.append(reg['regulon_set'])
            this_reg.append(reg['tfs'])
            x_reg.append(this_reg)
        featureObject["regulon_data"] = x_reg
    
    if atomic_regulons.has_key(x):
        featureObject["atomic_regulons"] = atomic_regulons[x]
    
    if co_occurring.has_key(x):
        featureObject["co_occurring_fids"] = list()
        for co_occur in co_occurring[x]:
            this_co_occur = [ co_occur[0], float(co_occur[1]) ]
            featureObject["co_occurring_fids"].append(this_co_occur)

    # these are not populated yet
    # not sure of the types of these at the moment
    # this times out even with one fid?!?
    coexpressed = dict()
    try:
        coexpressed = cdmi_api.fids_to_coexpressed_fids([x])
    except Exception, e:
        print >> sys.stderr, 'failed coexpressed_fids on ' + x
        print >> sys.stderr, e

    if coexpressed.has_key(x):
        featureObject["coexpressed_fids"] = list()
        for coexpress in coexpressed[x]:
            this_coexpressed = [ coexpress[0], float(coexpress[1]) ]
            featureObject["coexpressed_fids"].append(this_coexpressed)

#        end = time.time()
#        print  >> sys.stderr, "feature #" + str(x) + " processing, querying dna seqs, coexpressed, elapsed time " + str(end - start)

# ultimately will insert these into workspace
# need to get workspace ref back to put into the Genome object
    # e.g.
    # featureObject = simplejson.dumps(featureObject)
    # ws.save_objects({'workspace': 'search_workspace',objects=[featureObject]})
    # (or can batch a list of featureObjects, but don't want to batch
    # too many or it'll bork)
    feature_id = featureObject['feature_id']

    # test batching saves
#        fids_to_insert.append( { "type":"KBaseSearch.Feature","data":featureObject,"name":feature_id } )
#        if len(fids_to_insert) > 100:
#            feature_info = ws.save_objects({"workspace":wsname,"objects": fids_to_insert })
#            print >> sys.stderr, feature_info
        

    # original code, one save at a time
#        feature_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.Feature","data":featureObject,"name":feature_id}]})

#        print >> sys.stderr, feature_info

# need to figure out what to return
# dict of fid->feature_ref?
    feature_ref = wsname + '/' + feature_id
#        print simplejson.dumps(featureObject,sort_keys=True,indent=4 * ' ')
#    if not featureSet['features'].has_key(featureObject['feature_id']):
#        featureSet['features'][featureObject['feature_id']] = dict()
#    featureSet['features'][featureObject['feature_id']] = feature_ref


for g in genomes:
    print >> sys.stderr, "processing genome " + g + ' ' + genome_entities[g]['scientific_name']

    try:
        ws.get_object_info([{"workspace":wsname,"name":g}],0)
        print >> sys.stderr, 'genome '  + g + ' found, updating'
#        print >> sys.stderr, 'genome '  + g + ' found, skipping'
#        continue
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'genome '  + g + ' not found, adding to ws'

    genomeObject = dict()
    featureSet = dict()
    featureSet['features'] = dict()

    start = time.time()

    # maybe use get_entity_Genome to get additional fields, like source_id and domain?
    genome_data = cdmi_api.genomes_to_genome_data([g])[g]

    end = time.time()
    print >> sys.stderr, "querying genome_data " + str(end - start)

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

    # this died on kb|g.3907, kb|g.3643 Gallus gallus, kb|g.41 Mouse
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

             new_features = insert_features(fids_to_insert)
             fids_to_insert = list()

    # final fids to insert (batching code)
    if len(fids_to_insert) > 0:
         insert_features(fids_to_insert)

    end = time.time()
    print  >> sys.stderr, " processing features, elapsed time " + str(end - start)

    # insert into workspace, get path
#    print simplejson.dumps(featureSet,sort_keys=True,indent=4 * ' ')
    # another try block here?
    featureset_id = genomeObject['genome_id'] + '.featureset'
#    featureset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.FeatureSet","data":featureSet,"name":featureset_id}]})
#    print >> sys.stderr, featureset_info

    featureset_ref = wsname + '/' + featureset_id
    genomeObject['featureset_ref'] = featureset_ref
    start = time.time()

#    print simplejson.dumps(genomeObject,sort_keys=True,indent=4 * ' ')
#    genome_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.Genome","data":genomeObject,"name":genomeObject['genome_id']}]})
#    print >> sys.stderr, genome_info

    end = time.time()
    print  >> sys.stderr, "insert genome into ws " + str(end - start)
