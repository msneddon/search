#!/bin/bash

# this script is completely untested

core=$1

DATA_EXTR_PATH=$HOME/dev_container/modules/search/src/dataExtraction
#cat ontologies_int.sorted| python $DATA_EXTR_PATH/wsLoad/${core}_to_ws.py
time python $DATA_EXTR_PATH/solrLoad/ws${core}_to_solr.py

mkdir -p solrImport
rm solrImport/*

split -a3 -l500000 ${core}ToSolr.tab solrImport/${core}ToSolr.tab.

for file in solrImport/*
do
    echo $file
    cat ${core}ToSolr.tab.headers $file  | curl -q http://localhost:7077/search/${core}/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8' 
    curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=${core}"
done

# do a final reload
curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=${core}"
