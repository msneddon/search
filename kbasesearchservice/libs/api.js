var hostname = 'localhost';
var port = '8080';

module.exports = {

  getoperatorcount : {
    name : 'getoperatorcount'
    ,api : '/search/operatorcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:opr&q=function:'
  },
  getproteinbindingsitecount : {
    name : 'getproteinbindingsitecount'
    ,api : '/search/proteinbindingsitecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pbs&q=function:'
  },
  getgenecount : {
    name : 'getgenecount'
    ,api : '/search/genecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:cds&q=function:'
  },
  getpromotercount : {
    name : 'getpromotercount'
    ,api : '/search/promotercount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:prm&q=function:'
  },
  getrnacount : {
    name : 'getrnacount'
    ,api : '/search/rnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:rna&q=function:'
  },
  getssmotifscount : {
    name : 'getssmotifscount'
    ,api : '/search/ssmotifscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:trm&q=function:'
  },
  getcrisprcount : {
    name : 'getcrisprcount'
    ,api : '/search/crisprcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:crispr&q=function:'
  },
  getcrscount : {
    name : 'getcrscount'
    ,api : '/search/crscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:crs&q=function:'
  },
  getattcount : {
    name : 'getattcount'
    ,api : '/search/attcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:att&q=function:'
  },
  getprophagecount : {
    name : 'getprophagecount'
    ,api : '/search/prophagecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pp&q=function:'
  },
  getpseudogenecount : {
    name : 'getpseudogenecount'
    ,api : '/search/pseudogenecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pseudo&q=function:'
  },
  gettransposoncount : {
    name : 'gettransposoncount'
    ,api : '/search/transposoncount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:trnspn&q=function:'
  },
  getsrnacount : {
    name : 'getsrnacount'
    ,api : '/search/srnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:srna&q=function:'
  },
  getriboswitchcount : {
    name : 'getriboswitchcount'
    ,api : '/search/riboswitchcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:rsw&q=function:'
  },
  getlocuscount : {
    name : 'getlocuscount'
    ,api : '/search/locuscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:locus&q=function:'
  },
  getmrnacount : {
    name : 'getmrnacount'
    ,api : '/search/mrnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:mrna&q=function:'
  },
  getbindingsitecount : {
    name : 'getbindingsitecount'
    ,api : '/search/bindingsitecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:bs&q=function:'
  },
  getpathogenicityislandcount : {
    name : 'getpathogenicityislandcount'
    ,api : '/search/pathogenicityislandcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pi&q=function:'
    ,url : ''
  },
  getgenomecount : {
    name : 'getgenomecount'
    ,api : '/search/genomecount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&rows=0&q=scientific_name:'
  },
  getliteraturecount : {
    name : 'getliteraturecount'
    ,api : '/search/literaturecount'
    ,url : 'http://'+hostname+':'+port+'/search/literature/select?wt=json&rows=0&q=title:'
  },
  getvirusescount : {
    name : 'getvirusescount'
    ,api : '/search/virusescount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Viruses&q=scientific_name:'
  },
  getarchaeacount : {
    name : 'getarchaeacount'
    ,api : '/search/archaeacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Archaea&q=scientific_name:'
  },
  getbacteriacount : {
    name : 'getliteraturecount'
    ,api : '/search/bacteriacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Bacteria&q=scientific_name:'
  },
  geteukaryotacount : {
    name : 'geteukaryotacount'
    ,api : '/search/eukaryotacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Eukaryota&q=scientific_name:'
  },
  getviruses: {
    name : 'getviruses'
    ,api : '/search/viruses'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Viruses&q=scientific_name:'
  },
  getarchaea: {
    name : 'getarchaea'
    ,api : '/search/archaea'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Archaea&q=scientific_name:'
  },
  getbacteria: {
    name : 'getliterature'
    ,api : '/search/bacteria'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Bacteria&q=scientific_name:'
  },
  geteukaryota: {
    name : 'geteukaryota'
    ,api : '/search/eukaryota'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Eukaryota&q=scientific_name:'
  },
  getoperator : {
    name : 'getoperator'
    ,api : '/search/operator'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:opr&q=function:'
  },
  getproteinbindingsite : {
    name : 'getproteinbindingsite'
    ,api : '/search/proteinbindingsite'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pbs&q=function:'
  },
  getgene : {
    name : 'getgene'
    ,api : '/search/gene'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:cds&q=function:'
  },
  getpromoter : {
    name : 'getpromoter'
    ,api : '/search/promoter'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:prm&q=function:'
  },
  getrna : {
    name : 'getrna'
    ,api : '/search/rna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:rna&q=function:'
  },
  getssmotifs : {
    name : 'getssmotifs'
    ,api : '/search/ssmotifs'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:trm&q=function:'
  },
  getcrispr : {
    name : 'getcrispr'
    ,api : '/search/crispr'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:crispr&q=function:'
  },
  getcrs : {
    name : 'getcrs'
    ,api : '/search/crs'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:crs&q=function:'
  },
  getatt : {
    name : 'getatt'
    ,api : '/search/att'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:att&q=function:'
  },
  getprophage : {
    name : 'getprophage'
    ,api : '/search/prophage'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pp&q=function:'
  },
  getpseudogene : {
    name : 'getpseudogene'
    ,api : '/search/pseudogene'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pseudo&q=function:'
  },
  gettransposon : {
    name : 'gettransposon'
    ,api : '/search/transposon'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:trnspn&q=function:'
  },
  getsrna : {
    name : 'getsrna'
    ,api : '/search/srna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:srna&q=function:'
  },
  getriboswitch : {
    name : 'getriboswitch'
    ,api : '/search/riboswitch'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:rsw&q=function:'
  },
  getlocus : {
    name : 'getlocus'
    ,api : '/search/locus'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:locus&q=function:'
  },
  getmrna : {
    name : 'getmrna'
    ,api : '/search/mrna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:mrna&q=function:'
  },
  getbindingsite : {
    name : 'getbindingsite'
    ,api : '/search/bindingsite'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:bs&q=function:'
  },
  getpathogenicityisland : {
    name : 'getpathogenicityisland'
    ,api : '/search/pathogenicityisland'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pi&q=function:'
    ,url : ''
  },
  getgenome : {
    name : 'getgenome'
    ,api : '/search/genome'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&q=scientific_name:'
  },
  getliterature : {
    name : 'getliterature'
    ,api : '/search/literature'
    ,url : 'http://'+hostname+':'+port+'/search/literature/select?wt=json&q=title:'
  }
}
