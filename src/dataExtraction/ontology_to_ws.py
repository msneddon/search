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

ws = biokbase.workspace.client.Workspace("http://localhost:7058", user_id='***REMOVED***', password='***REMOVED***')

wsname = 'KBasePublicOntologies'
wsdescription = 'Search Ontology workspace'

# set up a try block here?
try:
    retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":wsdescription})
# want this to catch only workspace exists errors
except biokbase.workspace.client.ServerError, e:
    pass
#    print >> sys.stderr, e

ws.set_global_permission({"workspace":wsname,"new_permission":"r"})

currentOntologyID = ''
currentSName = ''
ontology = dict()
evidence_codes = dict()

for line in sys.stdin:
#    line=line.strip('\n')
    (SName,TranscriptID,OntologyID,OntologyDescription,OntologyDomain,OntologyEvidenceCode,OntologyType,GeneID,kbtrid,kblocusid) = line.strip('\n').split('\t')
    if not ( ontology.has_key(OntologyID) ):
        ontology[OntologyID] = dict()
    ontology[OntologyID]['ontology_id'] = OntologyID
    ontology[OntologyID]['ontology_type'] = OntologyType
    ontology[OntologyID]['ontology_domain'] = OntologyDomain
    ontology[OntologyID]['ontology_description'] = OntologyDescription
    if not (evidence_codes.has_key(OntologyID) ):
        evidence_codes[OntologyID] = dict()
    evidence_codes[OntologyID][OntologyEvidenceCode] = 1
    if not (ontology[OntologyID].has_key('gene_list') ):
        ontology[OntologyID]['gene_list'] = dict()
    if not (ontology[OntologyID]['gene_list'].has_key(SName) ):
        ontology[OntologyID]['gene_list'][SName] = list()
    ontology[OntologyID]['gene_list'][SName].append(TranscriptID)
    ontology[OntologyID]['gene_list'][SName].append(GeneID)
    ontology[OntologyID]['gene_list'][SName].append(kbtrid)
    ontology[OntologyID]['gene_list'][SName].append(kblocusid)

for ontology_id in ontology:
    ontology[ontology_id]['evidence_codes'] = evidence_codes[ontology_id].keys()
    # to do: insert into workspace
    ws_object_list = list()
    ws_obj_name = string.replace(ontology_id,':','')
    ws_object_list.append( { "type":"Ontology.Ontology","data":ontology[ontology_id],"name":ws_obj_name})
    print simplejson.dumps(ontology[ontology_id],sort_keys=True,indent=4 * ' ')

    wsobj_info = ws.save_objects({"workspace":wsname,"objects":ws_object_list})
    print >> sys.stderr, wsobj_info

