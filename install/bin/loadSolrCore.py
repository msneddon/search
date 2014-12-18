import requests
import sys
import io
import json

def push_tab_to_solr(host="http://localhost:7077/search/", headerfilepath=None, filepath=None, core=None, overwrite=False):
    try:
        solrheaderdata = io.open(headerfilepath, 'r').read().replace('\t',',').replace('\n','')    
        solr_url = host + core + "/update?wt=json&separator=%09&header=false&overwrite"

        if overwrite:
            solr_url += "true"
        else:
            solr_url += "false"

        if core in ['genomes', 'models']:
            solr_url += "&f.taxonomy.split=true&f.taxonomy.separator=%3B"

        solr_url += "&fieldnames=" + solrheaderdata

        postheaders = {'content-type':'application/csv; charset=utf-8'}
        with io.open(filepath,'rb') as csvdata:
            req = requests.post(solr_url, data=csvdata, headers=postheaders)    
            print req.text
        
        commit_url = host + "/admin/cores?wt=json&action=RELOAD&core=" + core
        
        req = requests.get(commit_url)
        print req.text
    except Exception, e:
        print str(e)

def push_json_to_solr(host, json, core):
    try:
        #add ontology info to genomes core
    
        ontology_json = open('ontologies.json', 'r')
        
        ontology_strings = ontology_json.read()
        ontology_json.close()
    
        ontology_chunks = ontology_strings.split("}\n{")
        ontology_records = list()
    
        ontology_records.append(json.loads(ontology_chunks[0] + "}"))
        for i in xrange(1, len(ontology_chunks) - 1):
            ontology_records.append(json.loads("{" + ontology_chunks[i] + "}"))
        ontology_records.append(json.loads("{" + ontology_chunks[-1]))
                            
    except Exception, e:
        print str(e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Upload tab delimited data to solr.')
    parser.add_argument('--host', nargs='?', default="http://localhost:7077/search/", help='http://hostname:port/search/')
    parser.add_argument('--header', nargs='?', help='path to header file', required=True)
    parser.add_argument('--data', nargs='?', help='path to data file', required=True)
    parser.add_argument('--core', nargs='?', help='solr core', required=True)
    parser.add_argument('--overwrite', action="store_true", help='overwrite documents with the same unique key')

    args = parser.parse_args()
    
    host = args.host
    headerfilepath = args.header
    filepath = args.data
    core = args.core
    
    if hasattr(args, 'overwrite'):
        push_tab_to_solr(host,headerfilepath,filepath,core,args.overwrite)
    else:
        push_tab_to_solr(host,headerfilepath,filepath,core)
