var hostname = 'localhost';
var port = 7077;

var request = require('request');
var CONFIG = require('config').conf;

var _  = require('underscore');
_.str = require('underscore.string');
_.mixin(_.str.exports());

//var API = require('../libs/api');

exports.index = function(req,res) {
  var result = {
    status : 200
    , service : 'KBase Search Service - Check out www.kbase.us for usage info'
    , version : CONFIG.version
  }
  res.jsonp(result);
};


exports.search = function(req, res) {
    var url = 'http://' + hostname + ':' + port;

    var categoryToCore = {"all": "n/a", "Genomes": "genomes", "Genes": "features", "Publications": "literature", "WSGenomes": "wsGenomeFeatures", "WSGenes": "wsGenomeFeatures"};

    var start = 0;
    var count = 0;
    var sort = null;
    var category = 'all';
    var mapping = '/search';
    var core = null;

    var requestURL = req.url;

    var auth_token = null;

    // check for auth token
    if (req.query.hasOwnProperty('token') && req.query.token !== null && req.query.token !== '') {
        auth_token = req.query.token;

        //make sure it is is a valid token
    }

    // check for and set the category, which will determine which core we search within
    if (req.query.hasOwnProperty('category') && req.query.category !== null && req.query.category !== '') {
        var category = req.query.category;

        if (categoryToCore.hasOwnProperty(category)) {
            core = categoryToCore[category];

            if (category === 'all') {
                url += mapping;
                core = null;
            }
            else {
                url += mapping + '/' + core;
            }
        }
        else {
            res.send(404, "No such category '" + category + "' !");
        }
    }
    else {
        url += mapping;
    }

    url += '/select?wt=json';

    // check for and set the number of items per page
    if (req.query.hasOwnProperty('itemsPerPage') && req.query.itemsPerPage !== null && req.query.itemsPerPage !== '') {
        count = parseInt(req.query.itemsPerPage);
    }

    // check for and set the current page
    if (req.query.hasOwnProperty('page') && req.query.page !== null && req.query.page !== '') {
        var currentPage = parseInt(req.query.page);

        if (currentPage < 1) {
            res.send(404, "Page : " + currentPage + ", No such page!");
        }

        start = (currentPage - 1) * count;
        url += '&start=' + start + '&rows=' + count;
    }
    else {
        url += '&start=' + start + '&rows=' + count;
    }

       
    // check for and set the type of sort, and then the sort order
    if (req.query.hasOwnProperty('sortType') && req.query.sortType !== null && req.query.sortType !== '') {
        var sortType = req.query.sortType;

        console.log(req.query.params);

        if (sortType === "alphabetical") {
            if (core === "genomes" || core === "features") {
                sort = "scientific_name_sort";
            }
            else if (core === "literature") {
                sort = "title";
            }
            else {
                sort = "score";
            }

            var sortOrder = 'asc';
            if (req.query.hasOwnProperty('sortOrder') && req.query.sortOrder !== null && (req.query.sortOrder === 'asc' || req.query.sortOrder === 'desc')) {
                sort += " " + req.query.sortOrder;
            }
            else {
                sort += " " + sortOrder;
            }

            url += '&sort=' + sort;
        }
        else if (sortType === "relevance") {
            sort = "score";

            var sortOrder = 'asc';
            if (req.query.hasOwnProperty('sortOrder') && req.query.sortOrder !== null && (req.query.sortOrder === 'asc' || req.query.sortOrder === 'desc')) {
                sort += " " + req.query.sortOrder;
            }
            else {
                sort += " " + sortOrder;
            }

            url += '&sort=' + sort;            
        }
        else {
            // unknown sort type
            res.send(404, "" + sortType + " is not a valid sort type!");
        }
    }

    // check for the presence of a query
    if (req.query.hasOwnProperty('q') && req.query.q !== null && req.query.q !== '') {
        url += '&q=' + req.query.q;
    }
    else {
        url += "&q=''";   
    }



    //By default its a fuzzy search
    //
    //keyword = '*' + keyword + '*';

    console.log(url);

    request(url, function (error, response, body) {
        if (!error && response.statusCode == 200) {
            var allResp = JSON.parse(body);

            console.log(allResp);

            req.result = {};

            req.result.status = response.statusCode;
            req.result.found = allResp.response.numFound;
            req.result.items = allResp.response.docs;
            req.result.itemCount = allResp.response.docs.length;
            req.result.itemsPerPage = count;
            req.result.page = allResp.response.start/count + 1;
            req.result.url = req.url;
            
            res.jsonp(req.result);
        } 
        else {
            //console.log(error);
            //console.log(response);
            //console.log(body);

            //req.result.status = response.statusCode;
          
            res.jsonp(req.result);
        }
    });
};



