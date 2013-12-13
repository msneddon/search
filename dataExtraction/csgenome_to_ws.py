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

    genomeObjects[g]["source_db"] = 'KBase Central Store'
    start = datetime.datetime.now()

    genome_data = cdmi_api.genomes_to_genome_data([g])[g]
    for x in genome_data.keys():
        genomeObjects[g][x] = genome_data[x]

    end = datetime.datetime.now()
    print >> sys.stderr, "querying genome_data " + str(end - start)

    start = datetime.datetime.now()

    genomeObjects[g]["taxonomy"] = cdmi_api.genomes_to_taxonomies([g])[g]

    end = datetime.datetime.now()
    print >> sys.stderr, "querying taxonomies " + str(end - start)

    start = datetime.datetime.now()

    contig_ids = cdmi_api.genomes_to_contigs([g])
    genomeObjects[g]["contig_ids"] = contig_ids[g]

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig ids " + str(end - start)

# do we need contig sequences?
# the CDMI calls take a while, but chasing down the ER properly
# might be a mess, and might not be any faster

    start = datetime.datetime.now()

    contig_sequences = cdmi_api.contigs_to_sequences(contig_ids[g])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig seqs " + str(end - start)

    start = datetime.datetime.now()

    genomeObjects[g]["contig_sequences"] = dict()
    for x in contig_sequences.keys():
        genomeObjects[g]["contig_sequences"][x] = contig_sequences[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying contig seqs " + str(end - start)

    start = datetime.datetime.now()
    
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying genome features " + str(end - start)

    start = datetime.datetime.now()

    genomeObjects[g]["features"] = dict()
    for x in fids:
        genomeObjects[g]["features"][x] = dict()

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying genome features " + str(end - start)

    start = datetime.datetime.now()

#    annotations = cdmi_api.fids_to_annotations(fids)
    annotations = cdmi_entity_api.get_entity_Annotation(fids,['id','annotator','comment','annotation_time'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying annotations " + str(end - start)

    start = datetime.datetime.now()

    for x in annotations.keys():
        genomeObjects[g]["features"][x]["annotation"] = annotations[x]

# functions are in feature entity?
    start = datetime.datetime.now()

#    functions = cdmi_api.fids_to_functions(fids)
    features = cdmi_entity_api.get_entity_Feature(fids,['id','feature-type','source-id','sequence-length','function','alias'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying feature entity for functions " + str(end - start)

#    print >> sys.stderr, features
    start = datetime.datetime.now()

    for x in features.keys():
        genomeObjects[g]["features"][x]["feature_data"] = features[x]

    end = datetime.datetime.now()
    print >> sys.stderr, "copying feature entity for functions " + str(end - start)

    start = datetime.datetime.now()

#    protein_families = cdmi_api.fids_to_protein_families(fids)
    protein_families = cdmi_entity_api.get_relationship_IsMemberOf(fids,[],['from_link','to_link'],[])

#[[{},{from_link:blah1,to_link:blaa2h},{}],...]
# want protein_families[*][1]['from_link']
    family_ids = [ x[1]['to_link'] for x in protein_families   ]
#    print >> sys.stderr, family_ids
    families = cdmi_entity_api.get_entity_Family(family_ids,['id','type','release','family_function'])
#    print >> sys.stderr, families

#    print protein_families

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying protein_families " + str(end - start)

    start = datetime.datetime.now()

    for x in protein_families:
#        genomeObjects[g]["features"][x]["protein_families"] = protein_families[x]
        fid = x[1]['from_link']
        family_id = x[1]['to_link']
        if not genomeObjects[g]["features"][fid].has_key('protein_families'):
            genomeObjects[g]["features"][fid]["protein_families"] = list()
        genomeObjects[g]["features"][fid]["protein_families"].append( families[family_id])

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying protein_families " + str(end - start)

# proteins CDMI seems fast
# hmm, maybe not?
    start = datetime.datetime.now()
    proteins = cdmi_api.fids_to_proteins(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying proteins " + str(end - start)

    start = datetime.datetime.now()

    protein_ids=dict()
    for x in proteins.keys():
        genomeObjects[g]["features"][x]["protein"] = proteins[x]
        protein_ids[proteins[x]] = x
	

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying proteins " + str(end - start)

# protein sequences
    start = datetime.datetime.now()
    protein_seqs = cdmi_entity_api.get_entity_ProteinSequence(protein_ids.keys(),['id','sequence'])

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying protein seqs " + str(end - start)

#    print >> sys.stderr, features
    start = datetime.datetime.now()

    for x in protein_seqs.keys():
        genomeObjects[g]["features"][protein_ids[x]]["protein_seq"]=protein_seqs[x]['sequence']

    end = datetime.datetime.now()
    print >> sys.stderr, "copying feature entity for functions " + str(end - start)

# dna sequences will be slow no matter what
    start = datetime.datetime.now()
    dna_seqs = dict()
    dna_seqs = cdmi_api.fids_to_dna_sequences(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying dna seqs " + str(end - start)

    start = datetime.datetime.now()

    for x in dna_seqs.keys():
        genomeObjects[g]["features"][x]["dna_seqs"] = dna_seqs[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying dna seqs " + str(end - start)

    start = datetime.datetime.now()

# literature might have to traverse proteins
# (which we may need anyway?)
#    literature = cdmi_api.fids_to_literature(fids)
    publications = cdmi_entity_api.get_relationship_IsATopicOf(protein_ids.keys(),[],['from_link','to_link'],[])
#    print >> sys.stderr, publications

    publication_ids = [ x[1]['to_link'] for x in publications   ]

    publication_data = cdmi_entity_api.get_entity_Publication(publication_ids,['id','title','link','pubdate'])
    end = datetime.datetime.now()
    print  >> sys.stderr, "querying literature " + str(end - start)

    start = datetime.datetime.now()

#    for x in literature.keys():
#        genomeObjects[g]["features"][x]["literature"] = literature[x]
    for x in publications:
        protein = x[1]['from_link']
        fid = protein_ids[protein]
        publication = x[1]['to_link']
        if not genomeObjects[g]["features"][fid].has_key('publications'):
            genomeObjects[g]["features"][fid]["publications"] = list()
        genomeObjects[g]["features"][fid]["publications"].append( publication_data[publication] )


    end = datetime.datetime.now()
    print  >> sys.stderr, "copying literature " + str(end - start)

    start = datetime.datetime.now()

#    roles = cdmi_api.fids_to_roles(fids)
    roles = cdmi_entity_api.get_relationship_HasFunctional(fids,[],['from_link','to_link'],[])
#    print >> sys.stderr, roles

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying roles " + str(end - start)

    start = datetime.datetime.now()

    for x in roles:
        fid = x[1]['from_link']
        role = x[1]['to_link']
        if not genomeObjects[g]["features"][fid].has_key('roles'):
            genomeObjects[g]["features"][fid]["roles"] = list()
        genomeObjects[g]["features"][fid]["roles"].append( role )

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying roles " + str(end - start)

# subsystems may have to traverse a bunch of entities
    start = datetime.datetime.now()

    subsystems = cdmi_api.fids_to_subsystems(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying subsystems " + str(end - start)

    start = datetime.datetime.now()

    for x in subsystems.keys():
        genomeObjects[g]["features"][x]["subsystems"] = subsystems[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying subsystems " + str(end - start)

# subsystem data
# (what is difference between subsystems and subsystem data?)
    start = datetime.datetime.now()

    subsystem_data = cdmi_api.fids_to_subsystem_data(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying subsystem_data " + str(end - start)

    start = datetime.datetime.now()

    for x in subsystem_data.keys():
        genomeObjects[g]["features"][x]["subsystem_data"] = subsystem_data[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying subsystem_data " + str(end - start)

# regulon data
    start = datetime.datetime.now()

    regulon_data = cdmi_api.fids_to_regulon_data(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying regulon data " + str(end - start)

    start = datetime.datetime.now()

    for x in regulon_data.keys():
        genomeObjects[g]["features"][x]["regulon_data"] = regulon_data[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying regulon data " + str(end - start)

# atomic regulons
    start = datetime.datetime.now()

    atomic_regulons = cdmi_api.fids_to_atomic_regulons(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying atomic regulons " + str(end - start)

    start = datetime.datetime.now()

    for x in atomic_regulons.keys():
        genomeObjects[g]["features"][x]["atomic_regulons"] = atomic_regulons[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying atomic regulons " + str(end - start)

# co-expressed fids
# really slow for e.coli
    start = datetime.datetime.now()

    co_expressed_fids = dict()
#    co_expressed_fids = cdmi_api.fids_to_coexpressed_fids(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "not! querying co-expressed " + str(end - start)

    start = datetime.datetime.now()

    for x in co_expressed_fids.keys():
        genomeObjects[g]["features"][x]["co_expressed"] = co_expressed_fids[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying co-expressed " + str(end - start)

# co-occurring fids needs to go to pairset for score
    start = datetime.datetime.now()

    co_occurring_fids = cdmi_api.fids_to_co_occurring_fids(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying co-occurring " + str(end - start)

    start = datetime.datetime.now()

    for x in co_occurring_fids.keys():
        genomeObjects[g]["features"][x]["co_occurring"] = co_occurring_fids[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying co-occurring " + str(end - start)

# locations need IsLocatedIn relationship
    start = datetime.datetime.now()

#    locations = cdmi_api.fids_to_locations(fids)
    locations = cdmi_entity_api.get_relationship_IsLocatedIn(fids,[],['from_link','to_link','ordinal','begin','len','dir'],[])
#    print >> sys.stderr, locations

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying locations " + str(end - start)

    start = datetime.datetime.now()

    for x in locations:
#        genomeObjects[g]["features"][x]["location"] = locations[x]
        fid = x[1]['from_link']
        if not genomeObjects[g]["features"][fid].has_key('locations'):
            genomeObjects[g]["features"][fid]["locations"] = list()
        genomeObjects[g]["features"][fid]["locations"].append( x[1] )

    
    end = datetime.datetime.now()
    print  >> sys.stderr, "copying locations " + str(end - start)

# print out json
    start = datetime.datetime.now()
    print simplejson.dumps(genomeObjects[g],sort_keys=True,indent=4 * ' ')
    end = datetime.datetime.now()
    print  >> sys.stderr, "printing json " + str(end - start)
