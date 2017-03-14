import requests
import sys
import io
import json

def delete_solr_core(host="http://localhost:7077/search/", core=None):
    try:
        solr_url = host + core + "/update?wt=json"
        deleteQuery = '{"delete": {"query": "*:*"}}'

        postheaders = {'content-type':'application/json'}
        req = requests.post(solr_url, data=deleteQuery, headers=postheaders)    
        print req.text
        
        commit_url = host + "/admin/cores?wt=json&action=RELOAD&core=" + core
        
        req = requests.get(commit_url)
        print req.text
    except Exception, e:
        print str(e)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Delete documents from a solr core.')
    parser.add_argument('--host', nargs='?', default="http://localhost:7077/search/", help='http://hostname:port/search/')
    parser.add_argument('--core', nargs='?', help='solr core', required=True)

    args = parser.parse_args()
    
    host = args.host
    core = args.core
    
    delete_solr_core(host,core)
