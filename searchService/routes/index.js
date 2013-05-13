
var request = require('request');
var CONFIG = require('config').conf;

var _  = require('underscore');
_.str = require('underscore.string');
_.mixin(_.str.exports());

var API = require('../libs/api');

exports.index = function(req,res) {
  var result = {
    status : 200
    , service : 'KBase Search Service - Check out www.kbase.us for usage info'
    , version : CONFIG.version
  }
  res.jsonp(result);

};

_.each(API, function( apiCall, callName ) {
  exports[callName] = function(req, res){


    var start = 0;
    var count = 10;

    if ( req.query.start != null && req.query.start != '' ) {
      start = req.query.start;
    }
   
    if ( req.query.count != null && req.query.count != '' ) {
      count = req.query.count;
    }
   

    var keyword = req.params.keyword;


    var path = req.path;
    var callName = _.words(path,'/')[1];
    var apiCall = _.values(_.pick(API, 
        'get'+callName.toLowerCase()))[0]; 

    //console.dir(apiCall);

    var result = { 
      status: 0
      , search: callName
      , query: req.path
      , keyword : keyword
      , start : start
      , returned : 0
      , found : 0
      , body: [] 
    };


    req.result = result;

    //By default its a fuzzy search
    //
    //keyword = '*' + keyword + '*';

    var url = apiCall.url + keyword + '&start=' + start + '&rows=' + count; 
    console.log(url);
    //res.jsonp({a:1});
    request(url, function (error, response, body) {
      if (!error && response.statusCode == 200) {
        var allResp = JSON.parse(body);
        req.result.found = allResp.response.numFound;
        req.result.status = response.statusCode;
        req.result.body = allResp.response.docs;
        req.result.returned = allResp.response.docs.length;
        res.jsonp(req.result);
      } else {
		console.dir(error);
		console.dir(response);
		console.dir(body);
        //req.result.status = response.statusCode;
        res.jsonp(req.result);
      }
    });
  };
});

