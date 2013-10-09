#Very brief notes on extracting data

#CDM:

#use all_entities_Genome, all_entities_Feature, genomes_to_taxonomy
#to get tables
#run Flatten script to combine to one

#for genomes core, need to combine Genome and Taxonomy files, and
#generate scientific_name_sorted column (tr/ /_/;tr /[A-Z]/[a-z]/;)
perl -F\\t -ane '$sortName=$F[3];$sortName=~tr/ /_/;$sortName=~tr/[A-Z]/[a-z]/;print join "\t",$F[0],$sortName;print "\n"' Genome.txt > genomes2scientificsortname.tab
# use smartPaste to paste to Genome.txt?
perl ~/kbase/git/dev_container/modules/search.workspace/dataExtraction/smartPaste.pl 1 taxonomies Genome.txt < GenomeTaxonomies.txt
perl ~/kbase/git/dev_container/modules/search.workspace/dataExtraction/smartPaste.pl 1 scinamesort Genome.txt.taxonomies < genomes2scientificsortname.tab

# loading into solr

# delete old records (this is destructive!)
curl "http://localhost:7077/search/genomes/update?stream.body=<delete><query>*:*</query></delete>"
curl "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=genomes"
# add the new genomes
#cat ./genomeHeaders.tab Genome.txt.taxonomies.scinamesort | curl http://localhost:7077/search/genomes/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8'
# no MD5 field currently in the schema
cut -f1-12,14- ./genomeHeaders.tab Genome.txt.taxonomies.scinamesort | curl http://localhost:7077/search/genomes/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8'
curl "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=genomes"


#for features core:

# need to strip out " characters
# should strip ' characters too?
#generate scientific_name_sorted column (tr/ /_/;tr /[A-Z]/[a-z]/;)
perl -F\\t -ane '$sortName=$F[9];$sortName=~tr/ /_/;$sortName=~tr/[A-Z]/[a-z]/;print join "\t",$F[0],$sortName;print "\n"' /kb/indexing/IndexFiles/IndexFile_*.txt > fids2scientificsortname.tab
cat fids2scientificsortname.tab | perl smartPaste.pl 1 alphasort solrSplitFiles/FeatureGenomeTaxonomy.tab.* 2> err.alphasort

#run smartpaste script with external id files to add to split files
cat externalids/kbFidTo*.tab | perl smartPaste.pl 1 extids solrSplitFiles/FeatureGenomeTaxonomy.tab.*.alphasort 2> err.extids

# sort domains by fid
#run collate script with sorted domain file to generate smartpaste input
# this takes many hours
perl ~/kbase/git/dev_container/modules/search.workspace/dataExtraction/collate_format_and_enum_domains.pl fid2allDomains.sorted.tab > fid2allDomains.sorted.collated
#run smartpaste script with collated domain file to add to split files
# (currently uses ~35GB memory for ~41m rows (but is relatively fast))
# (could be rewritten to go through both sets of input files simultaneously
# in order to save lots of memory; would need to sort FeatureGenomeTaxonomy files)
cat proteinDomains/fid2allDomains.sorted.collated | perl ~/kbase/git/dev_container/modules/search.workspace/dataExtraction/smartPaste.pl 2 domains solrSplitFiles/FeatureGenomeTaxonomy.tab.*.extids 2> err.domains

#(need better notes on generating these files)

# loading into solr

# delete old records (this is destructive!)
curl "http://localhost:7077/search/features/update?stream.body=<delete><query>*:*</query></delete>"
curl "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=features"

# add new ones
# will take a long time! predicted ~8hr for ~40m rows
for file in solrSplitFiles/FeatureGenomeTaxonomy.tab.sj.alphasort.extids.domains
do
  date
  echo $file
  cat ./featureHeaders.tab $file | curl http://localhost:7077/search/features/update?wt=json\&separator=%09 --data-binary @- -H 'Content-type:application/csv; charset=utf-8'
  date
  sleep 10
  curl "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=features"
done > features.log


#generate external ids:

# -q: don't cache; reduces client memory footprint
# -B: don't decorate output
# these queries not well tested: i used the MO dumps instead
mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
 'select k.identifier as fid,e.identifier as externalid,d.name as externaldb from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join idmapping.idmapping_externaldb d on (e.externaldb_id=d.id) limit 5'

# HMM domains
## TIGRFAM/Pfam
mysql -q -B -ugenomicsselect -p -h devdb1.newyork.kbase.us genomics_dev -e \
'select f2d.fid,f2d.domainId,seqBegin,seqEnd,domainBegin,domainEnd,score,evalue,domainDb,domainName,iprId,iprName from Fid2Domain f2d join DomainInfo di using (domainId) limit 5'
# all the rest: still need MO mappings (and some fids will not have)
# eventually all domains should go into Fid2Domain
mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
'select k.identifier as fid,ld.locusId,ld.domainId,seqBegin,seqEnd,domainBegin,domainEnd,score,evalue,domainDb,domainName,iprId,iprName from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join genomics_dev.Locus2Domain ld on (e.identifier=ld.locusId) join genomics_dev.DomainInfo di using (domainId) where domainDb NOT IN ("PFAM","TIGRFAMs") AND e.externaldb_id=5 limit 5'

# COG families
# Need to join the COG table to not select every single rpsblast hit to COG
### new query using kbase fids
mysql -q -B -ugenomicsselect -p -h devdb1.newyork.kbase.us genomics_dev -e \
 'select rps.fid,CONCAT("COG",rps.subject) as domainId,qBegin as seqBegin,qEnd as seqEnd,sBegin as domainBegin,sEnd as domainEnd,score,evalue,"COG",di.description,funCode,cf.description from genomics_dev.Fid2COGrpsblast rps join Fid2COG c on (rps.subject=c.cogInfoId and rps.fid=c.fid) join COGInfo di USING (cogInfoId) join COGFun cf USING (funCode) limit 5'


### old query using MO ids
#mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
# 'select k.identifier as fid,ld.locusId,CONCAT("COG",ld.subject) as domainId,qBegin as seqBegin,qEnd as seqEnd,sBegin as domainBegin,sEnd as domainEnd,score,evalue,"COG",di.description,funCode,cf.description from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join genomics_dev.COGrpsblast ld on (e.identifier=ld.locusId) join genomics_dev.COG c on (ld.subject=c.cogInfoId and ld.locusId=c.locusId) join genomics_dev.COGInfo di USING (cogInfoId) join genomics_dev.COGFun cf USING (funCode) where e.externaldb_id=5 limit 5'

# old old COG query; captured all hits, not just assignments
#  'select k.identifier as fid,ld.locusId,CONCAT("COG",ld.subject) as domainId,qBegin as seqBegin,qEnd as seqEnd,sBegin as domainBegin,sEnd as domainEnd,score,evalue,"COG",di.description,funCode,cf.description from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join genomics_dev.COGrpsblast ld on (e.identifier=ld.locusId) join genomics_dev.COGInfo di on (subject=cogInfoId) join genomics_dev.COGFun cf USING (funCode) where e.externaldb_id=5 limit 5'

# need to combine and sort the HMM and COG files on the first column
# in order to run collate script
#
# example load script
for file in /kb/indexing/IndexFiles/IndexFile_*.txt.sortname.extids.domains
do
  echo $file
  date
  cat featureHeaders $file | perl -p -e 's/"//g;' | curl http://localhost:7077/search/features/update?separator=%09\&wt=json  --data-binary @- -H 'Content-type:text/csv; charset=utf-8'
  sleep 10
  curl "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=features"
  date
done > solrLoad.log
