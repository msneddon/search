
var exec = require('child_process').execFile;
var request = require('request');
 
var _  = require('underscore');
 _.str = require('underscore.string');

var protocol = 'http://';
var host = 'localhost';
var port = 7078;
var subdeploy = '/search/';

exports.index = function(req, res){
  var searchType = '';
  //res.render('standby', { type: searchType } );
  res.render('index', { type: searchType } );
};

exports.advanced = function(req, res){
  var searchType = '';
  res.render('advanced', { type: searchType } );
};

exports.f1 = function(req, res){
  var id = req.params.keyword;
  res.render('feature', { id: id } );
};

exports.f2 = function(req, res){
  var id = req.params.keyword;
  res.render('feature2', { id: id } );
};

exports.f3 = function(req, res){
  var id = req.params.keyword;
  console.log(id);
  res.render('feature3', { id: id } );
};

exports.process = function(req, res){
  var keyword = req.body.keyword;
  var qcall = 'general';

  //var url = 'http://' + host2 + ':8080/search/select?wt=json&q='+keyword ;
  var url = protocol + host + ':' + port + subdeploy + qcall + '/' + keyword;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      console.log(allResp.found);
      //console.log(allResp.response.docs[1]);
      /*
      res.render('process', { keyword: req.body.keyword, 
                  type: 'General',
                  size: allResp.response.numFound,
                  start: 0,
                  rowcount: 10,
                  results: allResp.response.docs })
                  */
      res.render('process', { keyword: req.body.keyword, 
                  type: 'General',
                  size: allResp.found,
                  start: 0,
                  rowcount: 10,
                  results: allResp.body })
    } else {
      console.log('----------');
      console.log(error);
      console.log('----------');
      console.log(response);
      console.log('----------');
      console.log(body);
      console.log('----------');
      res.end();
	}
  })
};

exports.processadvanced = function(req, res){

  var query = req.params.query;
  var type = req.params.type;
  var start = 0;
  var count = 5;
  var qcall = 'literature';

  var result =  {"options": []};

  if ( type === 'Literature' || type === 'literature' ) {var qcall = 'literature';} 
  else if ( type === 'Bacteria' || type === 'bacteria' ) { qcall = 'bacteria'; }
  else if ( type === 'Viruses' || type === 'viruses' ) { qcall = 'viruses'; }
  else if ( type === 'Eukaryota' || type === 'eukaryota' ) { qcall = 'eukaryota'; }
  else if ( type === 'Archaea' || type === 'archaea' ) { qcall = 'archaea'; }
  else if ( type === 'Genes' || type === 'gene' ) { qcall = 'gene'; }
  else if ( type === 'Locus' || type === 'locus' ) { qcall = 'locus'; }
  else if ( type === 'Prophage' || type === 'prophage' ) { qcall = 'prophage'; }
  else if ( type === 'Pseudogene' || type === 'pseudogene' ) { qcall = 'pseudogene'; }
  else if ( type === 'Promoter' || type === 'promoter' ) { qcall = 'promoter'; }
  else if ( type === 'Operator' || type === 'operator' ) { qcall = 'operator'; }
  else if ( type === 'Protein Binding Site' || type === 'proteinbindingsite' ) { qcall = 'proteinbindingsite'; }
  else if ( type === 'Binding Site' || type === 'bindingsite' ) { qcall = 'bindingsite'; }
  else if ( type === 'Riboswitch' || type === 'riboswitch' ) { qcall = 'riboswitch'; }
  else if ( type === 'RNA' || type === 'rna' ) { qcall = 'rna'; }
  else if ( type === 'Transposon' || type === 'transposon' ) { qcall = 'transposon'; }
  else if ( type === 'mRNA' || type === 'mrna' ) { qcall = 'mrna'; }
  else if ( type === 'Small RNA' || type === 'smallrna' ) { qcall = 'smallrna'; }
  else { var qcall = 'literature';}

  //var url = protocol + host + subdeploy + qcall + '/*' + query +'*';
  var url = protocol + host + ':' + port + subdeploy + qcall + '/*' + query +'*'
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      var body = allResp.body;
      console.log(allResp.found);

      switch (type) {

	case 'Literature':
	      for (var i in body) {
		result.options.push(body[i].title.substring(0,50) + '<br/>' + body[i].title.substring(51,85) + '...');
	      }
	      break;
	case 'Bacteria':
	case 'Viruses':
	case 'Eukaryota':
	case 'Archaea':
	      for (var i in body) {
		result.options.push(body[i].scientific_name.substring(0,50) + '<br/>' + body[i].scientific_name.substring(51,85) );
	      }
	      break;
	default:
	      for (var i in body) {
		result.options.push(body[i].function.substring(0,50) + '<br/>' + body[i].function.substring(51,85) );
	      }
      }
      res.json(200,result);
    } else {
      res.json(200,result);
	}

  })
};

exports.processget = function(req, res){
  var keyword = req.params.keyword;
  var start = 1;
  var count = 10;
  var qcall = 'general';

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }


  /*
  var url = 'http://localhost:8080/search/literature/select?wt=json&q=title:'+keyword ;
                */

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render('process', { keyword: keyword, 
                  type: 'General',
                  size: allResp.found,
                  start: start,
                  rowcount: count,
                  results: allResp.body })
    } else {
      res.end();
	}
  })
};

exports.details = function(req, res){
  var keyword = req.params.keyword;
  var type = 'Feature';
  console.dir(req.query);
  if ( req.query.type != null && req.query.type.length != 0 )
    type = req.query.type;
  var start = 1;
  var count = 10;
  var qcall = 'literature';

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  res.render('details2', { keyword: keyword, 
              type: type,
              start: start
              });
};

exports.genomedetails = function(req, res){
  var keyword = req.params.keyword;
  var type = 'Genome';
  console.dir(req.query);
  if ( req.query.type != null && req.query.type.length != 0 )
    type = req.query.type;
  var start = 1;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  res.render('genomedetails', { keyword: keyword, 
              type: type,
              start: start
              });
};

exports.literaturedetails = function(req, res){
  var keyword = req.body.keyword;
  var qcall = 'Literature';
  var pubmedId = req.query.pubmedid;

  var url = 'http://pipes.yahoo.com/pipes/pipe.run';
  var params = {
      _id: "1b39ecc3914d5f3f2570d8800e5e80a2",
      _render: "json",
      q: pubmedId,
      n: 1,
      offset: 0,
  };

  request.post(url, params, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      //var allResp = JSON.parse(body);
      console.log(body);
      //console.log(allResp.response.docs[1]);
      /*
      res.render('process', { keyword: req.body.keyword, 
                  type: 'General',
                  size: allResp.response.numFound,
                  start: 0,
                  rowcount: 10,
                  results: allResp.response.docs })
                  */
      /*
      res.render('literaturedetails', { keyword: req.body.keyword, 
                  pubmedId: pubmedId,
                  type: qcall,
                  results: body })
                  */
      res.end();
    } else {
      console.log('----------');
      console.log(error);
      console.log('----------');
      console.log(response);
      console.log('----------');
      console.log(body);
      console.log('----------');
      res.end();
	}
  })
};


exports.showeverything = function(req, res){

  var keyword = req.params.keyword;
  var type = req.params.type;

  console.dir(req.query);
  if ( req.query.type != null && req.query.type.length != 0 )
    type = req.query.type;
  var start = 1;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  res.render('genomedetails', { keyword: keyword, 
              type: type,
              start: start
              });
};

exports.literature = function(req, res){

  var keyword = req.params.keyword;
  var qcall = 'literature';

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render('literature', { keyword: keyword, 
                  type: 'Literature',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render('bacteria', { keyword: keyword, 
                  type: 'Bacteria',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render('viruses', { keyword: keyword, 
                  type: 'Virus',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render(qcall, { keyword: keyword, 
                  type: 'Archaea',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      res.render(qcall, { keyword: keyword, 
                  type: 'Eukaryota',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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
  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      console.log(allResp.body[1]);
      res.render('gene', { keyword: keyword, 
                  type: 'Gene',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      console.log(allResp.body[1]);
      res.render('locus', { keyword: keyword, 
                  type: 'Locus',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
                + '?start=' + start + '&count=' + count;

  console.log(url);
  request(url, function (error, response, body) {
    console.log(response.statusCode);
    if (!error && response.statusCode == 200) {
      var allResp = JSON.parse(body);
      console.log(allResp.body[1]);
      res.render('prophage', { keyword: keyword, 
                  type: 'Prophage',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('pseudogene', { keyword: keyword, 
                  type: 'Pseudogene',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('promoter', { keyword: keyword, 
                  type: 'Promoter',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('operator', { keyword: keyword, 
                  type: 'Operator',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('proteinbindingsite', { keyword: keyword, 
                  type: 'Protein Binding Site',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('bindingsite', { keyword: keyword, 
                  type: 'Binding Site',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('riboswitch', { keyword: keyword, 
                  type: 'Riboswitch',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('rna', { keyword: keyword, 
                  type: 'RNA',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('transposon', { keyword: keyword, 
                  type: 'Transposon',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('mrna', { keyword: keyword, 
                  type: 'mRNA',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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

  var start = 0;
  var count = 10;

  if (req.query.start != null && req.query.start != '' ) {
    start = req.query.start;
  }

  if (req.query.count != null && req.query.count != '' ) {
    count = req.query.count;
  }

  var url = protocol + host + ':' + port +subdeploy + qcall + '/' + keyword 
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
      //console.log(allResp.response.docs[1]);
      console.log(allResp.body[1]);
      res.render('smallrna', { keyword: keyword, 
                  type: 'small RNA',
                  qcall: qcall,
                  start: start,
                  rowcount: count,
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
