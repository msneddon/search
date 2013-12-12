#!/usr/bin/env python

import datetime
import sys

import biokbase.cdmi.client

cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')

genomes = ['kb|g.3562','kb|g.0']

genomeObjects = dict()

for g in genomes:
    genomeObjects[g] = dict()

    start = datetime.datetime.now()

    genomeObjects[g]["genomes_to_genome_data"] = cdmi_api.genomes_to_genome_data([g])[g]

    end = datetime.datetime.now()
    print >> sys.stderr, "querying genome_data " + str(end - start)

    start = datetime.datetime.now()

    genomeObjects[g]["genomes_to_taxonomies"] = cdmi_api.genomes_to_taxonomies([g])[g]

    end = datetime.datetime.now()
    print >> sys.stderr, "querying taxonomies " + str(end - start)

    start = datetime.datetime.now()

    genomeObjects[g]["genomes_to_contigs"] = cdmi_api.genomes_to_contigs([g])[g]

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying contig ids " + str(end - start)

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
        genomeObjects[g]["features"][x]

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

    start = datetime.datetime.now()

# literature might have to traverse proteinsequence
    literature = cdmi_api.fids_to_literature(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying literature " + str(end - start)

    start = datetime.datetime.now()

    for x in literature.keys():
        genomeObjects[g]["features"][x]["literature"] = literature[x]

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

    start = datetime.datetime.now()

# subsystems may have to traverse a bunch of entities
    subsystems = cdmi_api.fids_to_subsystems(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying subsystems " + str(end - start)

    start = datetime.datetime.now()

    for x in subsystems.keys():
        genomeObjects[g]["features"][x]["subsystems"] = subsystems[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying subsystems " + str(end - start)

    start = datetime.datetime.now()

# co-occurring fids needs to go to pairset for score
    co_occurring_fids = cdmi_api.fids_to_co_occurring_fids(fids)

    end = datetime.datetime.now()
    print  >> sys.stderr, "querying co-occurring " + str(end - start)

    start = datetime.datetime.now()

    for x in co_occurring_fids.keys():
        genomeObjects[g]["features"][x]["co_occurring"] = co_occurring_fids[x]

    end = datetime.datetime.now()
    print  >> sys.stderr, "copying co-occurring " + str(end - start)

    start = datetime.datetime.now()

# need IsLocatedIn relationship
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

    print genomeObjects[g]
