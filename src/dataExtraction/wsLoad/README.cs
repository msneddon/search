# very quick notes on getting CS objects into workspace

##### dump central store into flat files
# configure my.cnf file in cwd, example in csToFlatFiles/my.cnf
# (keep on local storage, not ~ NFS, or nfs will croak and your run will die)
# this gets full dump
bash csToFlatFiles/dumpFeatureTables
# for debugging, can do
# limit=' LIMIT 50000 ' bash csToFlatFiles/dumpFeatureTables

# one time only: get publication info from pubmed
cut -f2 fids2pubs.tab | sort -u | python ~/dev_container/modules/search/src/dataExtraction/solrLoad/publications_to_solr.py

##### load flat files into workspace
# switches:
# --sorted-file-dir=. path to where above dump is (defaults to .)
# --skip-last for handling a partial dump
# --debug uses ***REMOVED*** against dev04.berkeley; no switch uses production
# --wsname to specify name of workspace
# --skip-existing to skip Genome objects that already exist (default is to overwrite)
# (--skip-existing does not look at objects referenced in Genome object! (e.g., FeatureSet, ContigSet)

# example for test run
python search/src/dataExtraction/wsLoad/csFlatFiles_to_ws.py --debug --skip-last --wsname=JunkWS06062014

# example for loading to production ws
# use kbase-login to get credentials
kbase-login kbasesearch
python search/src/dataExtraction/wsLoad/csFlatFiles_to_ws.py --wsname=KBaseRichGenomesLoad  > out 2> err
