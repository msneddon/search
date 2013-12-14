#!/usr/bin/env python

import datetime
import sys
import simplejson

import biokbase.cdmi.client

cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')

genomes = ['kb|g.3562','kb|g.0']
#genomes = ['kb|g.9','kb|g.222']

genomeObjects = dict()

for g in genomes:
    genomeObjects[g] = dict()

    start = datetime.datetime.now()

    genome_data = cdmi_api.genomes_to_genome_data([g])[g]

    end = datetime.datetime.now()
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

    #genomeObjects[g]["domain"] = 
    #genomeObjects[g]["source_id"] = 

    genomeObjects[g]["contig_lengths"] = list()

    #genomeObjects[g]["contigset_ref"] = 
    #genomeObjects[g]["proteinset_ref"] = 
    #genomeObjects[g]["transcriptset_ref"] = 

    #start = datetime.datetime.now()

    #taxonomy = cdmi_api.genomes_to_taxonomies([g])[g]

    #end = datetime.datetime.now()
    #print >> sys.stderr, "querying taxonomies " + str(end - start)

##########################
    # build ContigSet and Contig objects
    # ultimately we will want to build ContigSet independent of
    # the Genome object, insert it first, get its workspace path,
    # then use that to populate contigset_ref in the Genome object

    genomeObjects[g]["ContigSet"] = dict()

    genomeObjects[g]["ContigSet"]["id"] = ""
    genomeObjects[g]["ContigSet"]["name"] = ""
    genomeObjects[g]["ContigSet"]["md5"] = ""
    genomeObjects[g]["ContigSet"]["source_id"] = ""
    genomeObjects[g]["ContigSet"]["source"] = ""
    genomeObjects[g]["ContigSet"]["type"] = ""
    genomeObjects[g]["ContigSet"]["reads_ref"] = None
    genomeObjects[g]["ContigSet"]["fasta_ref"] = None
    genomeObjects[g]["ContigSet"]["contigs"] = list()

    start = datetime.datetime.now()

    contig_ids = cdmi_api.genomes_to_contigs([g])[g]
    #genomeObjects[g]["contig_ids"] = contig_ids[g]

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig ids " + str(end - start)

    start = datetime.datetime.now()

    contig_sequences = cdmi_api.contigs_to_sequences(contig_ids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig seqs " + str(end - start)

    start = datetime.datetime.now()

    contig_lengths = cdmi_api.contigs_to_lengths(contig_ids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig lengths " + str(end - start)

    start = datetime.datetime.now()

    contig_md5s = cdmi_api.contigs_to_md5s(contig_ids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig md5s " + str(end - start)

    for x in contig_ids:
        contig = dict()
        contig["id"] = x
        contig["length"] = int(contig_lengths[x])
        contig["md5"] = contig_md5s[x]
        contig["sequence"] = contig_sequences[x]
        contig["name"] = ""
        contig["description"] = ""        
        genomeObjects[g]["ContigSet"]["contigs"].append(contig)
        genomeObjects[g]["contig_lengths"].append(int(contig_lengths[x]))


###########################
    # build Feature objects


    # collect all data needed for building Feature objects

    # feature ids
    start = datetime.datetime.now()
    
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying genome features " + str(end - start)


    # feature annotations
    start = datetime.datetime.now()

    #annotations = cdmi_api.fids_to_annotations(fids)
    #annotations = cdmi_entity_api.get_entity_Annotation(fids,[])
    isAnnotatedBy = cdmi_entity_api.get_relationship_IsAnnotatedBy(fids,[],['from_link','to_link'],[])

    annotation_ids = [ x[1]['to_link'] for x in isAnnotatedBy ]

    annots = cdmi_entity_api.get_entity_Annotation(annotation_ids,['annotator','comment','annotation_time'])
    annotations = dict()
    for x in isAnnotatedBy:
        fid = x[1]['from_link']
        if not annotations.has_key(fid):
            annotations[fid] = list()
        this_annotation=annots[x[1]['to_link']]
        annotation = dict()
        annotation['annotation_time'] = this_annotation['annotation_time']
        annotation['annotator'] = this_annotation['annotator']
        annotation['comment'] = this_annotation['comment']
        annotations[fid].append(annotation)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying annotations " + str(end - start)


    # feature function, type, alias, source_id
    start = datetime.datetime.now()

    features = cdmi_entity_api.get_entity_Feature(fids,['id','feature-type','source-id','sequence-length','function','alias'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying feature entity for functions " + str(end - start)

    # feature protein families
    start = datetime.datetime.now()

    isMemberOf = cdmi_entity_api.get_relationship_IsMemberOf(fids,[],['from_link','to_link'],[])

    #[[{},{from_link:blah1,to_link:blaa2h},{}],...]
    # want protein_families[*][1]['from_link']
    family_ids = [ x[1]['to_link'] for x in isMemberOf ]
#    print >> sys.stderr, family_ids
    families = cdmi_entity_api.get_entity_Family(family_ids,['id','type','release','family_function'])

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
# why is family_function list? take just first for now
        if this_family.has_key('family_function'):
            family['subject_description'] = this_family['family_function'][0]
        protein_families[fid].append(family)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying protein_families " + str(end - start)

    # feature proteins
    start = datetime.datetime.now()

    proteins = cdmi_api.fids_to_proteins(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying proteins " + str(end - start)

#    start = datetime.datetime.now()
#    protein_ids = dict()
#    for x in proteins.keys():
#        genomeObjects[g]["features"][x]["protein"] = proteins[x]
#        protein_ids[proteins[x]] = x	
#    end = datetime.datetime.now()
#    print  >> sys.stderr, "copying proteins " + str(end - start)

    # feature protein sequences
    start = datetime.datetime.now()

    protein_translations = cdmi_entity_api.get_entity_ProteinSequence(proteins.values(),['id','sequence'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying protein seqs " + str(end - start)

#    print >> sys.stderr, features
#    start = datetime.datetime.now()
#    for x in protein_seqs.keys():
#        genomeObjects[g]["features"][protein_ids[x]]["protein_seq"]=protein_seqs[x]['sequence']
#    end = datetime.datetime.now()
#    print >> sys.stderr, "copying feature entity for functions " + str(end - start)

    # feature dna sequences
    start = datetime.datetime.now()

    dna_seqs = cdmi_api.fids_to_dna_sequences(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying dna seqs " + str(end - start)

#    start = datetime.datetime.now()
#    for x in dna_seqs.keys():
#        genomeObjects[g]["features"][x]["dna_seqs"] = dna_seqs[x]
#    end = datetime.datetime.now()
#    print  >> sys.stderr, "copying dna seqs " + str(end - start)

    # feature publications
    start = datetime.datetime.now()

    # literature might have to traverse proteins
    # (which we may need anyway)
    
    publications = cdmi_entity_api.get_relationship_IsATopicOf(proteins.values(),[],['from_link','to_link'],[])
#    print >> sys.stderr, publications

    publication_ids = [ x[1]['to_link'] for x in publications ]
    publication_data = cdmi_entity_api.get_entity_Publication(publication_ids,['id','title','link','pubdate'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying literature " + str(end - start)

#    start = datetime.datetime.now()
#    for x in literature.keys():
#        genomeObjects[g]["features"][x]["literature"] = literature[x]
#    for x in publications:
#        protein = x[1]['from_link']
#        fid = protein_ids[protein]
#        publication = x[1]['to_link']
#        if not genomeObjects[g]["features"][fid].has_key('publications'):
#            genomeObjects[g]["features"][fid]["publications"] = list()
#        genomeObjects[g]["features"][fid]["publications"].append( publication_data[publication] )
#    end = datetime.datetime.now()
#    print  >> sys.stderr, "copying literature " + str(end - start)

    # feature roles
    start = datetime.datetime.now()

#    roles = cdmi_api.fids_to_roles(fids)
    roles = cdmi_entity_api.get_relationship_HasFunctional(fids,[],['from_link','to_link'],[])
#    print >> sys.stderr, roles

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying roles " + str(end - start)

#    start = datetime.datetime.now()
#    for x in roles:
#        fid = x[1]['from_link']
#        role = x[1]['to_link']
#        if not genomeObjects[g]["features"][fid].has_key('roles'):
#            genomeObjects[g]["features"][fid]["roles"] = list()
#        genomeObjects[g]["features"][fid]["roles"].append( role )
#    end = datetime.datetime.now()
#    print  >> sys.stderr, "copying roles " + str(end - start)

    # subsystems may have to traverse a bunch of entities
    start = datetime.datetime.now()

    subsystems = cdmi_api.fids_to_subsystems(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying subsystems " + str(end - start)

    # subsystem data
    # (what is difference between subsystems and subsystem data?)
    start = datetime.datetime.now()

    subsystem_data = cdmi_api.fids_to_subsystem_data(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying subsystem_data " + str(end - start)

    # regulon data
    start = datetime.datetime.now()

    regulon_data = cdmi_api.fids_to_regulon_data(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying regulon data " + str(end - start)

    # atomic regulons
    start = datetime.datetime.now()

    atomic_regulons = cdmi_api.fids_to_atomic_regulons(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying atomic regulons " + str(end - start)

    # co-expressed fids, really slow for e.coli
    start = datetime.datetime.now()

    co_expressed_fids = dict()
#    co_expressed_fids = cdmi_api.fids_to_coexpressed_fids(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "not! querying co-expressed " + str(end - start)

    # co-occurring fids needs to go to pairset for score
    start = datetime.datetime.now()

    co_occurring_fids = cdmi_api.fids_to_co_occurring_fids(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying co-occurring " + str(end - start)

    # locations need IsLocatedIn relationship
    start = datetime.datetime.now()

#    locations = cdmi_api.fids_to_locations(fids)
    isLocatedIn = cdmi_entity_api.get_relationship_IsLocatedIn(fids,[],['from_link','to_link','ordinal','begin','len','dir'],[])

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
        locations[fid].append(location)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying locations " + str(end - start)

    genomeObjects[g]["feature_ids"] = fids[:]
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
# why do non-CDS/pegs have no dna sequence?!?
        if dna_seqs.has_key(x):
            featureObject["dna_sequence"] = dna_seqs[x]
            featureObject["dna_sequence_length"] = len(dna_seqs[x])
        if protein_families.has_key(x):
            featureObject["protein_families"] = protein_families[x]
        if annotations.has_key(x):
            featureObject["annotations"] = annotations[x]
# these are not populated yet
        featureObject["publications"] = list()
# is role a list?
        featureObject["roles"] = list()
        featureObject["subsystems"] = list()
        featureObject["subsystem_data"] = list()
# not sure of the types of these four at the moment
        featureObject["regulon_data"] = list()
        featureObject["atomic_regulons"] = list()
        featureObject["coexpressed"] = list()
        featureObject["co_occurring"] = list()

# ultimately will insert these into workspace
# need to get workspace ref back to put into the Genome object
        print simplejson.dumps(featureObject,sort_keys=True,indent=4 * ' ')

# print out json
    start = datetime.datetime.now()

    print simplejson.dumps(genomeObjects[g],sort_keys=True,indent=4 * ' ')

    end = datetime.datetime.now()
    print  >> sys.stderr, "printing json " + str(end - start)
