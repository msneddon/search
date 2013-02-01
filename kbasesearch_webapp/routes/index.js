
var exec = require('child_process').execFile;
var request = require('request');
 
var _  = require('underscore');
 _.str = require('underscore.string');

var protocol = 'https://';
var host = 'localhost';
var port = 443;
var subdeploy = '/search/';

exports.index = function(req, res){
  var searchType = '';
  res.render('index', { type: searchType } );
};

exports.process = function(req, res){
  var keyword = req.body.keyword;

  var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      console.log(allResp.response.docs[1]);
      res.render('process', { keyword: req.body.keyword, 
                  type: 'Literature',
                  size: allResp.response.numFound,
                  start: 1,
                  rowcount: 10,
                  results: allResp.response.docs })
    } else {
      res.end();
	}
  })
};

exports.processget = function(req, res){
  var keyword = req.params.keyword;
  var start = 1;
  var count = 10;
  var qcall = 'literature';

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }


  /*
  var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
                */

  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword ;
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      res.render('process', { keyword: keyword, 
                  type: 'Literature',
                  size: allResp.found,
                  start: start,
                  rowcount: count,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.literature = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'literature';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      res.render('literature', { keyword: keyword, 
                  type: 'Literature',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.bacteria = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'bacteria';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      res.render('bacteria', { keyword: keyword, 
                  type: 'Bacteria',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.viruses = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'viruses';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      res.render('viruses', { keyword: keyword, 
                  type: 'Virus',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.archaea = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'archaea';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      res.render(qcall, { keyword: keyword, 
                  type: 'Archaea',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.eukaryota = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'eukaryota';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      res.render(qcall, { keyword: keyword, 
                  type: 'Eukaryota',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.gene = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'gene';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('gene', { keyword: keyword, 
                  type: 'Gene',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.locus = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'locus';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('locus', { keyword: keyword, 
                  type: 'Locus',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.prophage = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'prophage';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('prophage', { keyword: keyword, 
                  type: 'Prophage',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.pseudogene = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'pseudogene';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('pseudogene', { keyword: keyword, 
                  type: 'Pseudogene',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.promoter = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'promoter';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('promoter', { keyword: keyword, 
                  type: 'Promoter',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.operator = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'operator';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('operator', { keyword: keyword, 
                  type: 'Operator',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.proteinbindingsite = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'proteinbindingsite';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('proteinbindingsite', { keyword: keyword, 
                  type: 'Protein Binding Site',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.bindingsite = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'bindingsite';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('bindingsite', { keyword: keyword, 
                  type: 'Binding Site',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.riboswitch = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'riboswitch';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('riboswitch', { keyword: keyword, 
                  type: 'Riboswitch',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.rna = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'rna';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('rna', { keyword: keyword, 
                  type: 'RNA',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.transposon = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'transposon';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('transposon', { keyword: keyword, 
                  type: 'Transposon',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.mrna = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'mrna';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('mrna', { keyword: keyword, 
                  type: 'mRNA',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.smallrna = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'smallrna';

  //var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      /*
      console.dir(JSON.stringify(allResp.response.docs));
      console.log(JSON.stringify(allResp.responseHeader));
      console.log(allResp.response.numFound);
      */
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('smallrna', { keyword: keyword, 
                  type: 'small RNA',
                  size: allResp.found,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.test = function(req, res){
  var searchType = '';
  res.render('test', { type: searchType } );
};
