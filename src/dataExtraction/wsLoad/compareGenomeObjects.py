#!/usr/bin/env python

import datetime
import sys
import simplejson
import time
import random
import pprint

import biokbase.cdmi.client
import biokbase.workspace.client

pp = pprint.PrettyPrinter(indent=4)

# production CDMI instance
cdmi_api = biokbase.cdmi.client.CDMI_API()
cdmi_entity_api = biokbase.cdmi.client.CDMI_EntityAPI()

def verify_genome(g,genome_entities,ws,wsname):
    all_genome_data = cdmi_api.genomes_to_genome_data([g])
    fids = cdmi_api.genomes_to_fids([g],[])[g]

    try:
#        wsObjects = ws.get_objects( [ {"workspace":wsname,"name":g} ] )
        # getting a subset might be faster?
        wsObjects = ws.get_object_subset( [ {"workspace":wsname,"name":g,"included":['/features/[*]/id']} ] )
    except:
        print >> sys.stderr, 'workspace genome ' + g + ' might be missing, skipping'
        return

    features = wsObjects[0]['data']['features']

    if (len(fids) == len(features)):
        print "genome " + g + " feature count consistent (" + str(len(features)) + " features)"
    else:
        print "genome " + g + " feature count inconsistent!"
        print "number of fids in CDM genome " + g + " is " + str(len(fids))
        print "number of fids in workspace genome " + wsname + '/' + g + " is " + str(len(features))
        

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Compare objects in the CDM with objects in the WS. Currently compares feature count only.')
    parser.add_argument('genomes', nargs='*', help='genomes to compare (default all)')
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('--debug',action='store_true',help='debugging')

    args = parser.parse_args()

# default to production ws
    ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")

    wsname = args.wsname[0]

    genome_entities = cdmi_entity_api.all_entities_Genome(0,15000,['id','scientific_name','source_id'])
    genomes = sorted(genome_entities)
    if args.genomes:
        genomes=args.genomes

    for g in genomes:
        verify_genome(g,genome_entities,ws,wsname)
