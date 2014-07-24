#!/usr/bin/env python

# use this script to take genomes and features from CS and create WS objects
# use the ws-url command-line tool to set the active workspace service URL
# use kbase-login to set the appropriate auth token

import datetime
import sys
import simplejson
import time
import random
import pprint

import biokbase.cdmi.client
import biokbase.workspace.client

pp = pprint.PrettyPrinter(indent=4)

skipExistingGenomes = False

# production instance
cdmi_api = biokbase.cdmi.client.CDMI_API()
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI()
# private instance
#cdmi_api = biokbase.cdmi.client.CDMI_API('http://192.168.1.163:7032')
#cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI('http://192.168.1.163:7032')


def insert_genome(g,genome_entities,ws,wsname):
    print >> sys.stderr, "processing genome " + g + ' ' + genome_entities[g]['scientific_name']

    try:
        ws.get_object_info([{"workspace":wsname,"name":g}],0)
        if skipExistingGenomes == True:
            print >> sys.stderr, 'genome '  + g + ' found, skipping'
            return
        print >> sys.stderr, 'genome '  + g + ' found, updating'
    except biokbase.workspace.client.ServerError:
        print >> sys.stderr, 'genome '  + g + ' not found, adding to ws'

    start = time.time()
    all_genome_data = cdmi_api.genomes_to_genome_data([g])
    genome_data = dict()
    if all_genome_data.has_key(g):
        genome_data = all_genome_data[g]
    else:
        print >> sys.stderr, 'genome ' + g + ' has no entry in cdmi, skipping'
        return

    end = time.time()
    print >> sys.stderr, "querying genome_data " + str(end - start)

    genomeObject = dict()
    featureSet = dict()
    featureSet['features'] = dict()

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
    # these sequences are too big for ws (250MB), need to refactor
    contig_sequences = dict()
    for contig_id in contig_ids:
#        contig_seq = cdmi_api.contigs_to_sequences([contig_id])
#        contig_sequences[contig_id] = contig_seq[contig_id]
        # for debugging, don't get contig seqs
        contig_sequences[contig_id] = ''

    end = time.time()
    print  >> sys.stderr, "(not) querying contig seqs " + str(end - start)

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

#    if args.debug:
#        print >> sys.stderr, '--debug active, not doing anything'
#        return

    start = time.time()

    # this will reference a ContigSet object
    #print simplejson.dumps(contigSet,sort_keys=True,indent=4 * ' ')
    # another try block here?
#    contigset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.ContigSet","data":contigSet,"name":contigSet['id']}]})

    end = time.time()
    print >> sys.stderr, "(not) inserting contigset into ws " + str(end - start)
#    print >> sys.stderr, contigset_info

#    contigset_ref = wsname + '/' + contigSet['id']
#    genomeObject["contigset_ref"] = contigset_ref

###########################
    # build Feature objects


    # collect all data needed for building Feature objects

    # feature ids
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    # locations need IsLocatedIn relationship
    isLocatedIn = cdmi_entity_api.get_relationship_IsLocatedIn(fids,[],['from_link','to_link','ordinal','begin','len','dir'],[])

#    hasAliasAssertedFrom = cdmi_entity_api.get_relationship_HasAliasAssertedFrom(fids,[],['from_link','to_link','alias'],[])

    # feature annotations
    start = time.time()

    isAnnotatedBy = cdmi_entity_api.get_relationship_IsAnnotatedBy(fids,[],['from_link','to_link'],[])
    annotation_ids = [ x[1]['to_link'] for x in isAnnotatedBy ]
#    print >> sys.stderr, annotation_ids
    cds_annotations = dict()
    if len(annotation_ids) > 0:
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
    families = dict()
    if len(family_ids) > 0:
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
    publication_data = dict()
    if len(publication_ids) > 0:
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
    #genomeObject["feature_ids"] = fids[:]

    aliases = dict()
#    for x in hasAliasAssertedFrom:
#        fid = x[1]['from_link']

#        if not aliases.has_key(fid):
#            aliases[fid] = dict()
#        if not aliases[fid].has_key(x[1]['to_link']):
#            aliases[fid][x[1]['to_link']] = list()

#        aliases[fid][x[1]['to_link']].append(x[1]['alias'])
        
#    print >> sys.stderr, 'processed hasAliasAssertedFrom'

    #copy location info
    locations = dict()
    for x in isLocatedIn:
        fid = x[1]['from_link']

        if not locations.has_key(fid):
            locations[fid] = list()
        
        # need to have these locations sorted by ordinal
        # (if they're not already)
        location = list()
        location.append(x[1]['to_link'])
        # this is supposed to be a contig_ref, but ws doesn't support that yet
#        location.append(contigset_ref + '/' + x[1]['to_link'])
        location.append(int(x[1]['begin']))
        location.append(x[1]['dir'])
        location.append(int(x[1]['len']))
        location.append(int(x[1]['ordinal']))
#        location['ordinal'] = x[1]['ordinal']
        locations[fid].append(location)

    print >> sys.stderr, 'processed isLocatedIn'

    #copy annotation info
    annotations = dict()
    for x in isAnnotatedBy:
        fid = x[1]['from_link']

        if not annotations.has_key(fid):
            annotations[fid] = list()
        
        current_cds_annotation = cds_annotations[x[1]['to_link']]
        
        object_annotation = list()
        object_annotation.append(current_cds_annotation['comment'])
        object_annotation.append(current_cds_annotation['annotator'])
        object_annotation.append(int(current_cds_annotation['annotation_time']))
        annotations[fid].append(object_annotation)

    print >> sys.stderr, 'processed isAnnotatedBy'

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

    print >> sys.stderr, 'processed isMemberOf'

    protein_ids = dict()
    proteins = dict()
    for x in produces:
        proteins[x[1]['from_link']] = x[1]['to_link']
        protein_ids[x[1]['to_link']] = x[1]['from_link']

    print >> sys.stderr, 'processed produces'

    publications = dict()
    for x in isATopicOf:
        protein_id = x[1]['from_link']
        fid = protein_ids[protein_id]
        
        if not publications.has_key(fid):
            publications[fid] = list()
        
        # need to convert this structure to Feature spec
        # do here, or later?
        this_pub = publication_data[x[1]['to_link']]
        pub = list()
        pub.append(int(this_pub['id']))
        # we don't have a source_db in the CS
        pub.append('')
        pub.append(this_pub['title'])
        pub.append(this_pub['link'])
        pub.append(this_pub['pubdate'])
        # we don't have authors or journal name in CS either
        pub.append('')
        pub.append('')
        publications[fid].append(pub)

    print >> sys.stderr, 'processed isATopicOf'

    roles = dict()
    for x in hasFunctional:
        fid = x[1]['from_link']
        if not roles.has_key(fid):
            roles[fid] = list()
        roles[fid].append( x[1]['to_link'] )

    print >> sys.stderr, 'processed hasFunctional'

    start = time.time()

    print >> sys.stderr, 'processing features, if lots of coexpression data may take a long time'

    featureObjects = dict()
# something in this loop is intolerably slow
    for x in fids:
        featureObject = dict()
        featureObject["feature_id"] = x
        featureObject["genome_id"] = g
        featureObject["source"] = 'KBase Central Store'
        
        if aliases.has_key(x):
            featureObject["aliases"] = aliases[x]
        
        if locations.has_key(x):
            featureObject["location"] = locations[x]
        
        if features.has_key(x):
            featureObject["feature_type"] = features[x]['feature_type']
            featureObject["function"] = features[x]['function']
            featureObject["dna_sequence_length"] = int(features[x]['sequence_length'])
            featureObject["feature_source_id"] = features[x]['source_id']
            
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

        featureObjects[x] = featureObject

    end = time.time()
    print  >> sys.stderr, " processing features, queried coexpressed, elapsed time " + str(end - start)

    for feature in featureObjects:
#        print feature
        individualFeature = dict()
        individualFeature['data'] = featureObjects[feature]
        featureSet['features'][feature] = individualFeature

    featureset_id = genomeObject['genome_id'] + '.featureset'

    start  = time.time()

    featureset_info = ws.save_objects({"workspace":wsname,"objects":[ { "type":"KBaseSearch.SearchFeatureSet","data":featureSet,"name":featureset_id}]})
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

    parser = argparse.ArgumentParser(description='Create a KBaseSearch.Genome object from the CS.')
    parser.add_argument('genomes', nargs='*', help='genomes to load (default "kb|g.0")')
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('--skip-existing',action='store_true',help='skip processing genomes which already exist in ws')
    parser.add_argument('--debug',action='store_true',help='debugging')

    args = parser.parse_args()

    wsname = args.wsname[0]

    # ws public instance
    ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")
    # ws team dev instance
    if args.debug:
#        ws = biokbase.workspace.client.Workspace("http://140.221.84.209:7058", user_id='***REMOVED***', password='***REMOVED***')
        ws = biokbase.workspace.client.Workspace("http://dev04.berkeley.kbase.us:7058", user_id='***REMOVED***', password='***REMOVED***')

    if args.skip_existing:
        skipExistingGenomes = True

    print >> sys.stderr, wsname
    try:
        retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":"Search CS workspace"})
        print >> sys.stderr, 'created workspace ' + wsname + ' at ws url ' + ws.url
        print >> sys.stderr, retval
    # want this to catch only workspace exists errors
    except biokbase.workspace.client.ServerError, e:
#        print >> sys.stderr, e
        print >> sys.stderr, 'workspace ' + wsname + ' at ws url ' + ws.url + ' may already exist, trying to use'

    genome_entities = cdmi_entity_api.all_entities_Genome(0,15000,['id','scientific_name','source_id'])
#    genomes = genome_entities

    genomes = ['kb|g.0']
#    genomes = random.sample(genome_entities,500)
    if args.genomes:
        genomes=args.genomes

#genomes = sys.argv[1:]
# DvH, E.coli
# takes 4min (total) without dna_seqs, with coexpressed_fids
# takes 5min (total) with retrieving everything
#genomes = ['kb|g.3562','kb|g.0']
# arabidopsis--takes 50m with individual dna_seq calls (coexpressed_fids untested)
# takes much less time when cached
#genomes = ['kb|g.3899']
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

#genomeObjects = dict()

    for g in genomes:
        insert_genome(g,genome_entities,ws,wsname)

