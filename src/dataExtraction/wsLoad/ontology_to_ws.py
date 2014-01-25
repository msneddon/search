#!/usr/bin/env python

# this script takes the ontology_int table from the kbase_plants db on devdb1.newyork
# and creates ws objects for them

import datetime
import sys
import simplejson
import time
import random
import string

#import biokbase.cdmi.client
import biokbase.workspace.client

#ws = biokbase.workspace.client.Workspace("http://localhost:7058", user_id='***REMOVED***', password='***REMOVED***')
# need to use kbase-login to obtain a proper token for the kbasesearch user
ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")

wsname = 'KBasePublicOntologies'
wsdescription = 'Search Ontology workspace'
# bug in ws?  should not need to specify major version
# gavin knows and is investigating
wstype = 'KBaseSearch.Ontology-1'

# organismStrings_to_kbase_gids = {'Athaliana':'kb|g.3899', 'Bdistachyon':'kb|g.140073','Ptrichocarpa':'kb|g.3907','Sbicolor':'kb|g.140095'}

# set up a try block here?
try:
    retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":wsdescription})
# want this to catch only workspace exists errors
except biokbase.workspace.client.ServerError, e:
    pass
#    print >> sys.stderr, e

ws.set_global_permission({"workspace":wsname,"new_permission":"r"})

currentOntologyID = ''
currentkb_gid = ''
ontology = dict()
evidence_codes = dict()

for line in sys.stdin:
#    line=line.strip('\n')
    (kb_gid,TranscriptID,OntologyID,OntologyDescription,OntologyDomain,OntologyEvidenceCode,OntologyType,GeneID,kbtrid,kblocusid) = line.strip('\n').split('\t')
    if not ( ontology.has_key(OntologyID) ):
        ontology[OntologyID] = dict()
    ontology[OntologyID]['ontology_id'] = OntologyID
    ontology[OntologyID]['ontology_type'] = OntologyType
    ontology[OntologyID]['ontology_domain'] = OntologyDomain
    ontology[OntologyID]['ontology_description'] = OntologyDescription

    (kb_prefix,kb_genome_id,kb_type,kb_id) = kblocusid.split('.')
    kb_gid = kb_prefix+'.'+kb_genome_id

    if not (evidence_codes.has_key(OntologyID) ):
        evidence_codes[OntologyID] = dict()
    evidence_codes[OntologyID][OntologyEvidenceCode] = 1
    if not (ontology[OntologyID].has_key('gene_list') ):
        ontology[OntologyID]['gene_list'] = dict()
    if not (ontology[OntologyID]['gene_list'].has_key(kb_gid) ):
        ontology[OntologyID]['gene_list'][kb_gid] = list()
    ontology[OntologyID]['gene_list'][kb_gid].append(TranscriptID)
    ontology[OntologyID]['gene_list'][kb_gid].append(GeneID)
    ontology[OntologyID]['gene_list'][kb_gid].append(kbtrid)
    ontology[OntologyID]['gene_list'][kb_gid].append(kblocusid)

ws_object_list=list()
for ontology_id in ontology:
    ontology[ontology_id]['evidence_codes'] = evidence_codes[ontology_id].keys()
    # workspace doesn't like colons in object name
    # (the original id will still be in the object)
    ws_obj_name = string.replace(ontology_id,':','')
    ws_object_list.append( { "type":wstype,"data":ontology[ontology_id],"name":ws_obj_name})
#    print simplejson.dumps(ontology[ontology_id],sort_keys=True,indent=4 * ' ')

    if len(ws_object_list) > 99:
        wsobj_info = ws.save_objects({"workspace":wsname,"objects":ws_object_list})
        ws_object_list = list()
        print >> sys.stderr, wsobj_info

# final insert
if len(ws_object_list) > 0:
    wsobj_info = ws.save_objects({"workspace":wsname,"objects":ws_object_list})
    print >> sys.stderr, wsobj_info
