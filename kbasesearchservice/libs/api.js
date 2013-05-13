var hostname2 = '140.221.92.149';
var port2 = '8080';

var hostname = 'localhost';
var port = '8080';


module.exports = {

  getgeneral : {
    name : 'getgeneral'
    ,api : '/search/general'
    ,url : 'http://'+hostname+':'+port+'/search/select?wt=json&q='
  },
  getoperatorcount : {
    name : 'getoperatorcount'
    ,api : '/search/operatorcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:opr&q=text:'
  },
  getproteinbindingsitecount : {
    name : 'getproteinbindingsitecount'
    ,api : '/search/proteinbindingsitecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pbs&q=text:'
  },
  getgenecount : {
    name : 'getgenecount'
    ,api : '/search/genecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:cds&q=text:'
  },
  getpromotercount : {
    name : 'getpromotercount'
    ,api : '/search/promotercount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:prm&q=text:'
  },
  getrnacount : {
    name : 'getrnacount'
    ,api : '/search/rnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:rna&q=text:'
  },
  getssmotifscount : {
    name : 'getssmotifscount'
    ,api : '/search/ssmotifscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:trm&q=text:'
  },
  getcrisprcount : {
    name : 'getcrisprcount'
    ,api : '/search/crisprcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:crispr&q=text:'
  },
  getcrscount : {
    name : 'getcrscount'
    ,api : '/search/crscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:crs&q=text:'
  },
  getattcount : {
    name : 'getattcount'
    ,api : '/search/attcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:att&q=text:'
  },
  getprophagecount : {
    name : 'getprophagecount'
    ,api : '/search/prophagecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pp&q=text:'
  },
  getpseudogenecount : {
    name : 'getpseudogenecount'
    ,api : '/search/pseudogenecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pseudo&q=text:'
  },
  gettransposoncount : {
    name : 'gettransposoncount'
    ,api : '/search/transposoncount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:trnspn&q=text:'
  },
  getsrnacount : {
    name : 'getsrnacount'
    ,api : '/search/srnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:srna&q=text:'
  },
  getriboswitchcount : {
    name : 'getriboswitchcount'
    ,api : '/search/riboswitchcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:rsw&q=text:'
  },
  getlocuscount : {
    name : 'getlocuscount'
    ,api : '/search/locuscount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:locus&q=text:'
  },
  getmrnacount : {
    name : 'getmrnacount'
    ,api : '/search/mrnacount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:mrna&q=text:'
  },
  getbindingsitecount : {
    name : 'getbindingsitecount'
    ,api : '/search/bindingsitecount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:bs&q=text:'
  },
  getpathogenicityislandcount : {
    name : 'getpathogenicityislandcount'
    ,api : '/search/pathogenicityislandcount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typetag}feature_type:pi&q=text:'
    ,url : ''
  },
  getgenomecount : {
    name : 'getgenomecount'
    ,api : '/search/genomecount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&rows=0&q=text:'
  },
  getliteraturecount : {
    name : 'getliteraturecount'
    ,api : '/search/literaturecount'
    ,url : 'http://'+hostname+':'+port+'/search/literature/select?wt=json&rows=0&q=title:'
  },
  getvirusescount : {
    name : 'getvirusescount'
    ,api : '/search/virusescount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Viruses&q=text:'
  },
  getarchaeacount : {
    name : 'getarchaeacount'
    ,api : '/search/archaeacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Archaea&q=text:'
  },
  getbacteriacount : {
    name : 'getliteraturecount'
    ,api : '/search/bacteriacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Bacteria&q=text:'
  },
  geteukaryotacount : {
    name : 'geteukaryotacount'
    ,api : '/search/eukaryotacount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}domain:Eukaryota&q=text:'
  },
  getviruses: {
    name : 'getviruses'
    ,api : '/search/viruses'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Viruses&q=text:'
  },
  getarchaea: {
    name : 'getarchaea'
    ,api : '/search/archaea'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Archaea&q=text:'
  },
  getbacteria: {
    name : 'getliterature'
    ,api : '/search/bacteria'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Bacteria&q=text:'
  },
  geteukaryota: {
    name : 'geteukaryota'
    ,api : '/search/eukaryota'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&facet=true&fq={!tag=feature_typeTag}domain:Eukaryota&q=text:'
  },
  getoperator : {
    name : 'getoperator'
    ,api : '/search/operator'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:opr&q=text:'
  },
  getproteinbindingsite : {
    name : 'getproteinbindingsite'
    ,api : '/search/proteinbindingsite'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pbs&q=text:'
  },
  getgene : {
    name : 'getgene'
    ,api : '/search/gene'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:cds&q=text:'
  },
  getpromoter : {
    name : 'getpromoter'
    ,api : '/search/promoter'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:prm&q=text:'
  },
  getrna : {
    name : 'getrna'
    ,api : '/search/rna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:rna&q=text:'
  },
  getssmotifs : {
    name : 'getssmotifs'
    ,api : '/search/ssmotifs'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:trm&q=text:'
  },
  getcrispr : {
    name : 'getcrispr'
    ,api : '/search/crispr'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:crispr&q=text:'
  },
  getcrs : {
    name : 'getcrs'
    ,api : '/search/crs'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:crs&q=text:'
  },
  getatt : {
    name : 'getatt'
    ,api : '/search/att'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:att&q=text:'
  },
  getprophage : {
    name : 'getprophage'
    ,api : '/search/prophage'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pp&q=text:'
  },
  getpseudogene : {
    name : 'getpseudogene'
    ,api : '/search/pseudogene'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pseudo&q=text:'
  },
  gettransposon : {
    name : 'gettransposon'
    ,api : '/search/transposon'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:trnspn&q=text:'
  },
  getsrna : {
    name : 'getsrna'
    ,api : '/search/srna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:srna&q=text:'
  },
  getriboswitch : {
    name : 'getriboswitch'
    ,api : '/search/riboswitch'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:rsw&q=text:'
  },
  getlocus : {
    name : 'getlocus'
    ,api : '/search/locus'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:locus&q=text:'
  },
  getmrna : {
    name : 'getmrna'
    ,api : '/search/mrna'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:mrna&q=text:'
  },
  getbindingsite : {
    name : 'getbindingsite'
    ,api : '/search/bindingsite'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:bs&q=text:'
  },
  getpathogenicityisland : {
    name : 'getpathogenicityisland'
    ,api : '/search/pathogenicityisland'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&fq={!tag=feature_typetag}feature_type:pi&q=text:'
    ,url : ''
  },
  getgenome : {
    name : 'getgenome'
    ,api : '/search/genome'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&q=text:'
  },
  getliterature : {
    name : 'getliterature'
    ,api : '/search/literature'
    ,url : 'http://'+hostname+':'+port+'/search/literature/select?wt=json&q=text:'
  },
  getadm : {
    name : 'getadm'
    ,api : '/search/adm'
    ,url : 'http://'+hostname+':'+port+'/search/adm/select?wt=json&q='
  },
  getontologies : {
    name : 'getontologies'
    ,api : '/search/ontologies'
    ,url : 'http://'+hostname+':'+port+'/search/ontologies/select?wt=json&q='
  },
  getnetworks : {
    name : 'getnetworks'
    ,api : '/search/networks'
    ,url : 'http://'+hostname+':'+port+'/search/networks/select?wt=json&q='
  },
  getpathways : {
    name : 'getpathways'
    ,api : '/search/pathways'
    ,url : 'http://'+hostname+':'+port+'/search/pathways/select?wt=json&q='
  },
  getworkspace : {
    name : 'getworkspace'
    ,api : '/search/workspace'
    ,url : 'http://'+hostname+':'+port+'/search/workspace/select?wt=json&q='
  },
  getadmcount : {
    name : 'getadmcount'
    ,api : '/search/admcount'
    ,url : 'http://'+hostname+':'+port+'/search/adm/select?rows=0&wt=json&q='
  },
  getontologiescount : {
    name : 'getontologiescount'
    ,api : '/search/ontologiescount'
    ,url : 'http://'+hostname+':'+port+'/search/ontologies/select?rows=0&wt=json&q='
  },
  getnetworkscount : {
    name : 'getnetworkscount'
    ,api : '/search/networkscount'
    ,url : 'http://'+hostname+':'+port+'/search/networks/select?rows=0&wt=json&q='
  },
  getpathwayscount : {
    name : 'getpathwayscount'
    ,api : '/search/pathwayscount'
    ,url : 'http://'+hostname+':'+port+'/search/pathways/select?rows=0&wt=json&q='
  },
  getworkspacecount : {
    name : 'getworkspacecount'
    ,api : '/search/workspacecount'
    ,url : 'http://'+hostname+':'+port+'/search/workspace/select?rows=0&wt=json&q='
  }



}
