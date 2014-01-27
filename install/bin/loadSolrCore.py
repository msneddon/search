import requests
import sys

def push_to_solr(headerfilepath,filepath,core):
    solr_url = "http://localhost:7077/search/"+core+"/update?wt=json&separator=%09"

    commit_url = "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=" + core

    solrheaderdata = open (headerfilepath, 'r')
    csvdata = open(filepath, "r")

    alldata = solrheaderdata.read() + csvdata.read()
    postheaders = {'content-type':'application/csv; charset=utf-8'}

#    req = requests.post(solr_url,data=sys.stdin,headers=postheaders)
    req = requests.post(solr_url,data=alldata,headers=postheaders)
    print req.text
    req = requests.get(commit_url)
    print req.text


if __name__ == "__main__":

    import argparse

    headerfilepath = sys.argv[1]
    filepath = sys.argv[2]
    core = sys.argv[3]
    push_to_solr(headerfilepath,filepath,core)
