#Very brief notes on extracting data

#CDM:

#use all_entities_Genome, all_entities_Feature, genomes_to_taxonomy
#to get tables
#run Flatten script to combine to one
# Split script on combined feature file for easier solr loading
#(may need to generate scientific_name_sort field)

#for genomes core, need to combine Genome and Taxonomy files, and
#generate scientific_name_sorted column (tr/ /_/;tr /[A-Z]/[a-z]/;)

#for features core:

# need to strip out " characters
#generate scientific_name_sorted column (tr/ /_/;tr /[A-Z]/[a-z]/;)
 perl -F\\t -ane '$sortName=$F[9];$sortName=~tr/ /_/;$sortName=~tr/[A-Z]/[a-z]/;print join "\t",$F[0],$sortName;print "\n"' /kb/indexing/IndexFiles/IndexFile_*.txt > fids2scientificsortname.tab

#run smartpaste script with external id files to add to split files
cat kbTo*.tab | perl smartPaste.pl extids /kb/indexing/IndexFiles/IndexFile_*.txt 2> err.extids
#run collate script with domain files to generate smartpaste input
#run smartpaste script with collated domain file to add to split files
#(need better notes on generating these files)

#generate external ids:

# -q: don't cache; reduces client memory footprint
# -B: don't decorate output
# these queries not well tested: i used the MO dumps instead
mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
 'select k.identifier as fid,e.identifier as externalid,d.name as externaldb from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join idmapping.idmapping_externaldb d on (e.externaldb_id=d.id) limit 5'

# HMM domains
mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
'select k.identifier as fid,ld.locusId,ld.domainId,seqBegin,seqEnd,domainBegin,domainEnd,score,evalue,domainDb,domainName,iprId,iprName from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join genomics_dev.Locus2Domain ld on (e.identifier=ld.locusId) join genomics_dev.DomainInfo di using (domainId) where e.externaldb_id=5 limit 5'

# COG families
# Need to join the COG table to not select every single rpsblast hit to COG
mysql -q -B -uidmappingselect -p -h devdb1.newyork.kbase.us idmapping -e \
 'select k.identifier as fid,ld.locusId,CONCAT("COG",ld.subject) as domainId,qBegin as seqBegin,qEnd as seqEnd,sBegin as domainBegin,sEnd as domainEnd,score,evalue,"COG",di.description,funCode,cf.description from idmapping.idmapping_kbaseid k join idmapping.idmapping_kbaseid_externalids ke on (k.id=ke.kbaseid_id) join idmapping.idmapping_externalid e on (e.id=ke.externalid_id) join genomics_dev.COGrpsblast ld on (e.identifier=ld.locusId) join genomics_dev.COG c on (ld.subject=c.cogInfoId and ld.locusId=c.locusId) join genomics_dev.COGInfo di USING (cogInfoId) join genomics_dev.COGFun cf USING (funCode) where e.externaldb_id=5 limit 5'

# old COG query; captured all hits, not just assignments
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
