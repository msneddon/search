#!/usr/bin/env python

import datetime
import sys
import simplejson
import time
import random
import MySQLdb

import biokbase.cdmi.client

cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')

kbase_sapling_db = MySQLdb.connect('192.168.1.85','kbase_sapselect','oiwn22&dmwWEe','kbase_sapling_v1')

# DvH, E.coli
# takes 4min (total) without dna_seqs, with coexpressed_fids
# takes 5min (total) with retrieving everything
#genomes = ['kb|g.3562','kb|g.0','kb|g.3899']
# arabidopsis--takes 50m with individual dna_seq calls (coexpressed_fids untested)
# takes much less time when cached
#genomes = ['kb|g.3899']
# two random genomes
#genomes = ['kb|g.9','kb|g.222']
#genomes = ['kb|g.3562','kb|g.1494','kb|g.423']
genome_entities = cdmi_entity_api.all_entities_Genome(1,15000,['id','scientific_name','source_id'])

genomes = random.sample(genome_entities,5)
genomes = ['kb|g.19762','kb|g.1976']

genomeObjects = dict()

for g in genomes:
    print >> sys.stderr, "processing genome " + g + ' ' + genome_entities[g]['scientific_name']
    genomeObjects[g] = dict()
    featureSet = dict()

    start = time.time()

    # maybe use get_entity_Genome to get additional fields, like source_id and domain?
    genome_data = cdmi_api.genomes_to_genome_data([g])[g]

    end = time.time()
    print >> sys.stderr, "querying genome_data " + str(end - start)

###############################################
    #fill in top level genome object properties
    genomeObjects[g]["id"] = g
    genomeObjects[g]["scientific_name"] = genome_data["scientific_name"]
    genomeObjects[g]["genetic_code"] = int(genome_data["genetic_code"])
    genomeObjects[g]["dna_size"] = int(genome_data["dna_size"])
    genomeObjects[g]["num_contigs"] = int(genome_data["contigs"])
    genomeObjects[g]["source"] = 'KBase Central Store'
    genomeObjects[g]["md5"] = genome_data["genome_md5"]
    if genomeObjects[g].has_key('taxonomy'):
        genomeObjects[g]["taxonomy"] = genome_data["taxonomy"]
        genomeObjects[g]["domain"] = genome_data['taxonomy'].split(';')[0]
    genomeObjects[g]["gc_content"] = float(genome_data["gc_content"])
    genomeObjects[g]["complete"] = int(genome_data["complete"])

    genomeObjects[g]["source_id"] = genome_entities[g]['source_id']

    genomeObjects[g]["contig_lengths"] = list()

    #genomeObjects[g]["contigset_ref"] = 
    #genomeObjects[g]["proteinset_ref"] = 
    #genomeObjects[g]["transcriptset_ref"] = 

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
    contigSet["md5"] = genomeObjects[g]["md5"]
#    contigSet["source_id"] = ""
    contigSet["source"] = "KBase Central Store"
    contigSet["type"] = "Organism"
#    contigSet["reads_ref"] = None
#    contigSet["fasta_ref"] = None
    contigSet["contigs"] = list()

    start = time.time()

    contig_ids = cdmi_api.genomes_to_contigs([g])[g]

    end = time.time()
    print  >> sys.stderr, "querying contig ids " + str(end - start)

    start = time.time()

    contig_sequences = cdmi_api.contigs_to_sequences(contig_ids)

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
        
        contigSet["contigs"].append(contig)
        
        # should this be a dict?
        genomeObjects[g]["contig_lengths"].append(int(contig_lengths[x]))


###########################
    # build Feature objects


    # collect all data needed for building Feature objects

    # feature ids
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    # locations need IsLocatedIn relationship
    isLocatedIn = cdmi_entity_api.get_relationship_IsLocatedIn(fids,[],['from_link','to_link','ordinal','begin','len','dir'],[])

    # feature annotations
    start = time.time()

    isAnnotatedBy = cdmi_entity_api.get_relationship_IsAnnotatedBy(fids,[],['from_link','to_link'],[])
    annotation_ids = [ x[1]['to_link'] for x in isAnnotatedBy ]
    cds_annotations = cdmi_entity_api.get_entity_Annotation(annotation_ids,['annotator','comment','annotation_time'])

    end = time.time()
    print  >> sys.stderr, "querying annotations " + str(end - start)


    # feature function, type, alias, source_id
    features = cdmi_entity_api.get_entity_Feature(fids,['id','feature-type','source-id','sequence-length','function','alias'])

    # feature protein families
    start = time.time()

    #[[{},{from_link:blah1,to_link:blaa2h},{}],...]
    # want protein_families[*][1]['from_link']
    isMemberOf = cdmi_entity_api.get_relationship_IsMemberOf(fids,[],['from_link','to_link'],[])
    family_ids = [ x[1]['to_link'] for x in isMemberOf ]
    families = cdmi_entity_api.get_entity_Family(family_ids,['id','type','release','family_function'])

    end = time.time()
    print  >> sys.stderr, "querying protein_families " + str(end - start)

    # feature proteins
    start = time.time()

#    proteins = cdmi_api.fids_to_proteins(fids)
    produces = cdmi_entity_api.get_relationship_Produces(fids,[],['from_link','to_link'],[])
    protein_list = [ x[1]['to_link'] for x in produces ]

    end = time.time()
    print  >> sys.stderr, "querying proteins " + str(end - start)

    # feature protein sequences
    start = time.time()

    protein_translations = cdmi_entity_api.get_entity_ProteinSequence(protein_list,['id','sequence'])
#    protein_translations = dict()
#    cursor = kbase_sapling_db.cursor()
#    placeholders = '%s,' * (len(protein_list)-1)
#    placeholders = placeholders + '%s'
#    cursor.execute ("EXPLAIN SELECT id,sequence FROM ProteinSequence WHERE id IN (" + placeholders + ")",protein_list)
#    out = cursor.fetchone()
#    print out
#    sys.exit(0)
#    result_set = cursor.fetchall()
#    for row in result_set:
        # let's make this structure exactly the same as what's returned by get_entity_ProteinSequence
#        protein_translations[row[0]] = dict()
#        protein_translations[row[0]]['sequence'] = row[1]
#        protein_translations[row[0]]['id'] = row[0]
#    print protein_translations

    end = time.time()
    print  >> sys.stderr, "querying protein seqs " + str(end - start)

    # feature dna sequences
    #dna_seqs = dict()

    #start = time.time()    
    # this is horribly slow
    #for x in xrange(len(fids)):
    #    dna_seqs[fids[x]] = cdmi_api.fids_to_dna_sequences([fids[x]])
    #
    #    end = time.time()
    #    print  >> sys.stderr, "feature #" + str(x) + " querying dna seqs, elapsed time " + str(end - start)

    # feature publications
    start = time.time()

    # literature might have to traverse proteins
    # (which we may need anyway)
    
    isATopicOf = cdmi_entity_api.get_relationship_IsATopicOf(protein_list,[],['from_link','to_link'],[])
    publication_ids = [ x[1]['to_link'] for x in isATopicOf ]
    publication_data = cdmi_entity_api.get_entity_Publication(publication_ids,['id','title','link','pubdate'])

    end = time.time()
    print  >> sys.stderr, "querying literature " + str(end - start)

    # feature roles
    hasFunctional = cdmi_entity_api.get_relationship_HasFunctional(fids,[],['from_link','to_link'],[])

    # subsystems may have to traverse a bunch of entities
    start = time.time()

    subsystems = cdmi_api.fids_to_subsystems(fids)

    end = time.time()
    print  >> sys.stderr, "querying subsystems " + str(end - start)

    # subsystem data
    # (what is difference between subsystems and subsystem data?)
    start = time.time()

    subsystem_data = cdmi_api.fids_to_subsystem_data(fids)

    end = time.time()
    print  >> sys.stderr, "querying subsystem_data " + str(end - start)

    # regulon data
    start = time.time()

    regulon_data = cdmi_api.fids_to_regulon_data(fids)

    end = time.time()
    print  >> sys.stderr, "querying regulon data " + str(end - start)

    # atomic regulons
    start = time.time()

    atomic_regulons = cdmi_api.fids_to_atomic_regulons(fids)
    # do we want to chase down the members of each regulon?

    end = time.time()
    print  >> sys.stderr, "querying atomic regulons " + str(end - start)

    # co-expressed fids, really slow for e.coli
    # want IsCoregulatedWith?  still horribly slow for e.coli, times out
    # probably need a better way to do this

    #start = time.time()

    #coexpressed = dict()
    #for x in fids:
    #    coe = cdmi_api.fids_to_coexpressed_fids([x])
    #
    #    if coe.has_key(x):
    #        if not coexpressed.has_key(x):
    #            coexpressed[x] = list()
    #        
    #        coexfids=dict()
    #        for coexfid in coe[x]:
    #            coexfids['scored_fid'] = coexfid[0]
    #            coexfids['score'] = coexfid[1]
    #        coexpressed[x].append(coexfids)
    #
    #    end = time.time()
    #    print  >> sys.stderr, "querying co-expressed, elapsed time " + str(end - start)

    # co-occurring fids needs to go to pairset for score
    start = time.time()

    co_occurring = cdmi_api.fids_to_co_occurring_fids(fids)

    end = time.time()
    print  >> sys.stderr, "querying co-occurring " + str(end - start)

    #copy the list of feature ids
    genomeObjects[g]["feature_ids"] = fids[:]


    #copy location info
    locations = dict()
    for x in isLocatedIn:
        fid = x[1]['from_link']

        if not locations.has_key(fid):
            locations[fid] = list()
        
        # it would be good to have these locations sorted by ordinal
        # (if they're not already)
        # need to convert locations to spec; do now or later?
        location = dict()
        location['contig_id'] = x[1]['to_link']
        location['begin'] = x[1]['begin']
        location['strand'] = x[1]['dir']
        location['length'] = x[1]['len']
        location['ordinal'] = x[1]['ordinal']
        locations[fid].append(location)

    #copy annotation info
    annotations = dict()
    for x in isAnnotatedBy:
        fid = x[1]['from_link']

        if not annotations.has_key(fid):
            annotations[fid] = list()
        
        current_cds_annotation = cds_annotations[x[1]['to_link']]
        
        object_annotation = dict()
        object_annotation['annotation_time'] = current_cds_annotation['annotation_time']
        object_annotation['annotator'] = current_cds_annotation['annotator']
        object_annotation['comment'] = current_cds_annotation['comment']
        annotations[fid].append(object_annotation)


    protein_families = dict()
    for x in isMemberOf:
        fid = x[1]['from_link']
        
        if not protein_families.has_key(fid):
            protein_families[fid] = list()
        
        # need to convert this structure to Feature spec
        # do here, or later?
        this_family = families[x[1]['to_link']]
        family = dict()
        family['id'] = this_family['id']
        family['subject_db'] = this_family['type']
        family['release_version'] = this_family['release']
        
        # why is family_function list? take just first for now
        if this_family.has_key('family_function'):
            family['subject_description'] = this_family['family_function'][0]
        protein_families[fid].append(family)


    protein_ids = dict()
    proteins = dict()
    for x in produces:
        proteins[x[1]['from_link']] = x[1]['to_link']
        protein_ids[x[1]['to_link']] = x[1]['from_link']

    publications = dict()
    for x in isATopicOf:
        protein_id = x[1]['from_link']
        fid = protein_ids[protein_id]
        
        if not publications.has_key(fid):
            publications[fid] = list()
        
        # need to convert this structure to Feature spec
        # do here, or later?
        this_pub = publication_data[x[1]['to_link']]
        pub = dict()
        pub['id'] = this_pub['id']
        pub['title'] = this_pub['title']
        pub['link'] = this_pub['link']
        pub['pubdate'] = this_pub['pubdate']
        publications[fid].append(pub)


    roles = dict()
    for x in hasFunctional:
        fid = x[1]['from_link']
        if not roles.has_key(fid):
            roles[fid] = list()
        roles[fid].append( x[1]['to_link'] )

    start = time.time()
    for x in fids:
        featureObject = dict()
        featureObject["id"] = x
        featureObject["genome_id"] = g
        featureObject["source"] = 'KBase Central Store'
        
        if locations.has_key(x):
            featureObject["location"] = locations[x]
        
        if features.has_key(x):
            featureObject["type"] = features[x]['feature_type']
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
            featureObject["publications"] = publications[x]
        
        if roles.has_key(x):
            featureObject["roles"] = roles[x]
        
        if subsystems.has_key(x):
            featureObject["subsystems"] = subsystems[x]
        
        if subsystem_data.has_key(x):
            featureObject["subsystem_data"] = [{'subsystem': s[0], 'variant': s[1], 'role': s[2]} for s in subsystem_data[x]]
        
        if regulon_data.has_key(x):
            featureObject["regulon_data"] = regulon_data[x]
        
        if atomic_regulons.has_key(x):
            featureObject["atomic_regulons"] = [{'atomic_regulon': ar[0], 'atomic_regulon_size': ar[1]} for ar in atomic_regulons[x]]
        
        if co_occurring.has_key(x):
            featureObject["co_occurring"] = [{'scored_fid': c[0], 'score': c[1]} for c in co_occurring[x]]

        # these are not populated yet
        # not sure of the types of these at the moment
        coexpressed = cdmi_api.fids_to_coexpressed_fids([x])

        if coexpressed.has_key(x):
            featureObject["coexpressed"] = coexpressed[x]

#        end = time.time()
#        print  >> sys.stderr, "feature #" + str(x) + " processing, querying dna seqs, coexpressed, elapsed time " + str(end - start)

# ultimately will insert these into workspace
# need to get workspace ref back to put into the Genome object
        # e.g.
        # featureObject = simplejson.dumps(featureObject)
        # ws.save_objects({'workspace': 'search_workspace',objects=[featureObject]})
        # (or can batch a list of featureObjects, but don't want to batch
        # too many or it'll bork)

#        print simplejson.dumps(featureObject,sort_keys=True,indent=4 * ' ')
        featureSet[x]=featureObject

#        import sys
#        sys.exit(0)

    end = time.time()
    print  >> sys.stderr, " processing features, queried coexpressed, elapsed time " + str(end - start)
    # insert into workspace, get path
    print simplejson.dumps(contigSet,sort_keys=True,indent=4 * ' ')
    # insert into workspace, get path
    print simplejson.dumps(featureSet,sort_keys=True,indent=4 * ' ')

    # these will reference a ContigSet and FeatureSet object
    genomeObjects[g]["featureset_ref"] = 'featuresetRef'
    genomeObjects[g]["contigset_ref"] = 'contigsetRef'

    #start = time.time()

    print simplejson.dumps(genomeObjects[g],sort_keys=True,indent=4 * ' ')

    #end = time.time()
    #print  >> sys.stderr, "printing json " + str(end - start)
