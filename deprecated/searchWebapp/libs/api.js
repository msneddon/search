var hostname = 'localhost';
var port = '7077';

module.exports = {

  getOperatorCount : {
    name : 'getOperatorCount'
    ,api : '/search/OperatorCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"opr"&q=function:'
  },
  getProteinBindingSiteCount : {
    name : 'getProteinBindingSiteCount'
    ,api : '/search/ProteinBindingSiteCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"pbs"&q=function:'
  },
  getGeneCount : {
    name : 'getGeneCount'
    ,api : '/search/GeneCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"CDS"&q=function:'
  },
  getPromoterCount : {
    name : 'getPromoterCount'
    ,api : '/search/PromoterCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"prm"&q=function:'
  },
  getRNACount : {
    name : 'getRNACount'
    ,api : '/search/RNACount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"rna"&q=function:'
  },
  getSSMotifsCount : {
    name : 'getSSMotifsCount'
    ,api : '/search/SSMotifsCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"trm"&q=function:'
  },
  getCRISPRCount : {
    name : 'getCRISPRCount'
    ,api : '/search/CRISPRCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"crispr"&q=function:'
  },
  getCRSCount : {
    name : 'getCRSCount'
    ,api : '/search/CRSCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"crs"&q=function:'
  },
  getATTCount : {
    name : 'getATTCount'
    ,api : '/search/ATTCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"att"&q=function:'
  },
  getProphageCount : {
    name : 'getProphageCount'
    ,api : '/search/ProphageCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"pp"&q=function:'
  },
  getPseudogeneCount : {
    name : 'getPseudogeneCount'
    ,api : '/search/PseudogeneCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"pseudo"&q=function:'
  },
  getTransposonCount : {
    name : 'getTransposonCount'
    ,api : '/search/TransposonCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"trnspn"&q=function:'
  },
  getSRNACount : {
    name : 'getSRNACount'
    ,api : '/search/SRNACount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"SRNA"&q=function:'
  },
  getRiboswitchCount : {
    name : 'getRiboswitchCount'
    ,api : '/search/RiboswitchCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"rsw"&q=function:'
  },
  getLocusCount : {
    name : 'getLocusCount'
    ,api : '/search/LocusCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"locus"&q=function:'
  },
  getMRNACount : {
    name : 'getMRNACount'
    ,api : '/search/MRNACount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"mRNA"&q=function:'
  },
  getBindingSiteCount : {
    name : 'getBindingSiteCount'
    ,api : '/search/BindingSiteCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"bs"&q=function:'
  },
  getPathogenicityIslandCount : {
    name : 'getPathogenicityIslandCount'
    ,api : '/search/PathogenicityIslandCount'
    ,url : 'http://'+hostname+':'+port+'/search/features/select?wt=json&facet=true&rows=0&fq={!tag=feature_typeTag}feature_type:"pi"&q=function:'
    ,url : ''
  },
  getGenomeCount : {
    name : 'getGenomeCount'
    ,api : '/search/GenomeCount'
    ,url : 'http://'+hostname+':'+port+'/search/genomes/select?wt=json&rows=0&q=scientific_name:'
  },
  getLiteratureCount : {
    name : 'getLiteratureCount'
    ,api : '/search/LiteratureCount'
    ,url : 'http://'+hostname+':'+port+'/search/literature/select?wt=json&rows=0&q=title:'
  }
}
