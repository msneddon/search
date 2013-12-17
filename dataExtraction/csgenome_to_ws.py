#!/usr/bin/env python

import datetime
import sys
import simplejson
import time

import biokbase.cdmi.client

cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')

# DvH, E.coli
# takes 4min (total) without dna_seqs, with coexpressed_fids
# takes 5min (total) with retrieving everything
genomes = ['kb|g.3562','kb|g.0','kb|g.3899']
# arabidopsis--takes 50m with individual dna_seq calls (coexpressed_fids untested)
# takes much less time when cached
#genomes = ['kb|g.3899']
# two random genomes
#genomes = ['kb|g.9','kb|g.222']

genomeObjects = dict()

for g in genomes:
    genomeObjects[g] = dict()

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
    genomeObjects[g]["taxonomy"] = genome_data["taxonomy"]
    genomeObjects[g]["gc_content"] = float(genome_data["gc_content"])
    genomeObjects[g]["complete"] = int(genome_data["complete"])

    #genomeObjects[g]["domain"] = genome_data['taxonomy'][0]
    #genomeObjects[g]["source_id"] = g

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

    genomeObjects[g]["ContigSet"] = dict()

    # what is this supposed to be?
    genomeObjects[g]["ContigSet"]["id"] = ""
    genomeObjects[g]["ContigSet"]["name"] = ""
    genomeObjects[g]["ContigSet"]["md5"] = ""
    genomeObjects[g]["ContigSet"]["source_id"] = ""
    genomeObjects[g]["ContigSet"]["source"] = "KBase Central Store"
    genomeObjects[g]["ContigSet"]["type"] = "Organism"
    genomeObjects[g]["ContigSet"]["reads_ref"] = None
    genomeObjects[g]["ContigSet"]["fasta_ref"] = None
    genomeObjects[g]["ContigSet"]["contigs"] = list()

    start = time.time()

    contig_ids = cdmi_api.genomes_to_contigs([g])[g]
    #genomeObjects[g]["contig_ids"] = contig_ids[g]

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
        # if we don't have this information, let's not add a key for them
#        contig["name"] = ""
#        contig["description"] = ""        
        genomeObjects[g]["ContigSet"]["contigs"].append(contig)
        # should this be a dict?
        genomeObjects[g]["contig_lengths"].append(int(contig_lengths[x]))


###########################
    # build Feature objects


    # collect all data needed for building Feature objects

    # feature ids
    start = time.time()
    
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    end = time.time()
    print  >> sys.stderr, "querying genome features " + str(end - start)

    # locations need IsLocatedIn relationship
    start = time.time()

    isLocatedIn = cdmi_entity_api.get_relationship_IsLocatedIn(fids,[],['from_link','to_link','ordinal','begin','len','dir'],[])

    end = time.time()
    print  >> sys.stderr, "querying locations " + str(end - start)


    # feature annotations
    start = time.time()

    isAnnotatedBy = cdmi_entity_api.get_relationship_IsAnnotatedBy(fids,[],['from_link','to_link'],[])
    annotation_ids = [ x[1]['to_link'] for x in isAnnotatedBy ]
    cds_annotations = cdmi_entity_api.get_entity_Annotation(annotation_ids,['annotator','comment','annotation_time'])

    end = time.time()
    print  >> sys.stderr, "querying annotations " + str(end - start)


    # feature function, type, alias, source_id
    start = time.time()

    features = cdmi_entity_api.get_entity_Feature(fids,['id','feature-type','source-id','sequence-length','function','alias'])

    end = time.time()
    print  >> sys.stderr, "querying feature entity for functions " + str(end - start)

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

    proteins = cdmi_api.fids_to_proteins(fids)

    end = time.time()
    print  >> sys.stderr, "querying proteins " + str(end - start)

    # feature protein sequences
    start = time.time()

    protein_translations = cdmi_entity_api.get_entity_ProteinSequence(proteins.values(),['id','sequence'])

    end = time.time()
    print  >> sys.stderr, "querying protein seqs " + str(end - start)

    # feature dna sequences
    dna_seqs = dict()

    start = time.time()    
    # this is horribly slow
    for x in xrange(len(fids)):
        dna_seqs[fids[x]] = cdmi_api.fids_to_dna_sequences([fids[x]])

        end = time.time()
        print  >> sys.stderr, "feature #" + str(x) + " querying dna seqs, elapsed time " + str(end - start)

    # feature publications
    start = time.time()

    # literature might have to traverse proteins
    # (which we may need anyway)
    
    isATopicOf = cdmi_entity_api.get_relationship_IsATopicOf(proteins.values(),[],['from_link','to_link'],[])
    publication_ids = [ x[1]['to_link'] for x in isATopicOf ]
    publication_data = cdmi_entity_api.get_entity_Publication(publication_ids,['id','title','link','pubdate'])

    end = time.time()
    print  >> sys.stderr, "querying literature " + str(end - start)

    # feature roles
    start = time.time()

    hasFunctional = cdmi_entity_api.get_relationship_HasFunctional(fids,[],['from_link','to_link'],[])

    end = time.time()
    print  >> sys.stderr, "querying roles " + str(end - start)

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

    start = time.time()

    coexpressed = dict()
    for x in fids:
        coe = cdmi_api.fids_to_coexpressed_fids([x])

        if coe.has_key(x):
            if not coexpressed.has_key(x):
                coexpressed[x] = list()
            
            coexfids=dict()
            for coexfid in coe[x]:
                coexfids['scored_fid'] = coexfid[0]
                coexfids['score'] = coexfid[1]
            coexpressed[x].append(coexfids)

        end = time.time()
        print  >> sys.stderr, "querying co-expressed, elapsed time " + str(end - start)

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
    for x in proteins.keys():
        #genomeObjects[g]["features"][x]["protein"] = proteins[x]
        protein_ids[proteins[x]] = x	

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



    # this will be a list of workspace paths that reference
    # the loaded Feature objects
    genomeObjects[g]["feature_refs"] = list()

    for x in fids:
        featureObject = dict()
        featureObject["id"] = x
        featureObject["genome_id"] = g
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
                    featureObject["protein_translation_length"] = len(protein_translations[proteins[x]]['sequence'])
        if dna_seqs.has_key(x):
            featureObject["dna_sequence"] = dna_seqs[x]
            featureObject["dna_sequence_length"] = len(dna_seqs[x])
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
            featureObject["subsystem_data"] = list()
            for ss in subsystem_data[x]:
                this_ss = dict()
                this_ss['subsystem'] = ss[0]
                this_ss['variant'] = ss[1]
                this_ss['role'] = ss[2]
                featureObject['subsystem_data'].append(this_ss)
        if regulon_data.has_key(x):
#            featureObject["regulon_data"] = list()
            featureObject["regulon_data"] = regulon_data[x]
        if atomic_regulons.has_key(x):
            featureObject["atomic_regulons"] = list()
            for ar in atomic_regulons[x]:
                this_ar = dict()
                this_ar['atomic_regulon'] = ar[0]
                this_ar['atomic_regulon_size'] = ar[1]
                featureObject["atomic_regulons"].append(this_ar)
        if co_occurring.has_key(x):
            featureObject["co_occurring"] = list()
            for coo in co_occurring[x]:
                this_coo = dict()
                this_coo['scored_fid'] = coo[0]
                this_coo['score'] = coo[1]
                featureObject["co_occurring"].append(this_coo)
# these are not populated yet
# not sure of the types of these at the moment
        if coexpressed.has_key(x):
#            featureObject["coexpressed"] = list()
            featureObject["coexpressed"] = coexpressed[x]

# ultimately will insert these into workspace
# need to get workspace ref back to put into the Genome object
        #print simplejson.dumps(featureObject,sort_keys=True,indent=4 * ' ')

# print out json
    #start = time.time()

    #print simplejson.dumps(genomeObjects[g],sort_keys=True,indent=4 * ' ')

    #end = time.time()
    #print  >> sys.stderr, "printing json " + str(end - start)
