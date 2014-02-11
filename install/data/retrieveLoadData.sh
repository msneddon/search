#!/bin/bash

tmpsolrdir=tmp/solrLoad
mkdir -p $tmpsolrdir
echo retrieving load data
curl http://dev07.berkeley.kbase.us/searchSolrData/searchSolrData.tar.gz > tmp/searchSolrData.tar.gz
echo extracting load data
tar xzf tmp/searchSolrData.tar.gz -C $tmpsolrdir

# full cores
for core in gwas ontology metagenomes expression
do
    ./deploy.py --load-solr-data $core $tmpsolrdir/$core/${core}ToSolr.tab.headers $tmpsolrdir/$core/${core}ToSolr.tab
#    echo loading data into $core
#    cat $tmpsolrdir/$core/${core}ToSolr.tab.headers $tmpsolrdir/$core/${core}ToSolr.tab  | curl -q http://localhost:7077/search/$core/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8'
#    curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=$core"
done

# example data only cores
for core in genomes
do
    echo loading example data into $core
    ./deploy.py --load-solr-data $core $tmpsolrdir/$core/${core}ToSolr.tab.headers $tmpsolrdir/$core/${core}ToSolr.tab
#    echo loading example data into $core
#    cat $tmpsolrdir/$core/${core}ToSolr.tab.headers $tmpsolrdir/$core/${core}ToSolr.tab  | curl -q http://localhost:7077/search/$core/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8'
#    curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=$core"
done

