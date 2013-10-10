var hostname = 'localhost';
var port = 7077;

var hostURL = "http://localhost:7077/";
var solrURL = hostURL;
var solr_user = 'admin';
var solr_pass = '***REMOVED***';

var currentRequest;
var currentResponse;
var validated;
var finished;

var fs = require('fs');
var url = require('url');
var https = require('https');
var zlib = require('zlib');
//var rsa = require('ursa');
var request = require('request');
var CONFIG = require('config').conf;
var watchr = require('watchr');
var kbase = require('../libs/kbase.js');
var async = require('async');

var _  = require('underscore');
_.str = require('underscore.string');
_.mixin(_.str.exports());

//var api = require('../libs/api');

exports.index = function(req,res) {
  var result = {
    status : 404
    , service : 'KBase Search Service - Check out www.kbase.us for usage info'
    , version : CONFIG.version
  }
  res.jsonp(result);
};


var pluginPath = fs.realpathSync("plugins/categories");
var pluginFiles = fs.readdirSync(pluginPath);
var plugins = {};
    
function loadPlugins() {
    var temp;
    for (var i = 0; i < pluginFiles.length; i++) {
        temp = JSON.parse(fs.readFileSync(fs.realpathSync(pluginPath + "/" + pluginFiles[i]), {encoding: 'utf8'}));        
        plugins[temp.category] = temp;
    }
}

exports.loadPlugins = loadPlugins;

watchr.watch({
    path: pluginPath,
    listeners: {
        // when anything in the path changes, reload all the plugins
        change: function(changeType, filePath, fileCurrentStat, filePreviousStat) {
            loadPlugins();
        }
    },
    next: function(err, watchers) {
        // if all watchers have completed, close them down
        setTimeout(function () {
            for (var i = 0; i < watchers.length; i++) {
                watchers[i].close();
            }
        }, 60*1000); // wait 60 seconds
    }
});


function validateInputs(req, res) {
    var validatedParams = {};

    // check for auth token
    if (req.query.hasOwnProperty('token') && req.query.token !== null && req.query.token !== '') {
        var auth_token = req.query.token;
        validatedParams.auth_token = req.query.token;
        validatedParams.username = auth_token.substr(0,auth_token.indexOf('|')).split('=')[1];

        //make sure it is is a valid token
        //console.log(validatedParams.username);

/*
        var marker = "SigningSubject=";
        var verify_start = auth_token.search(marker);
        var verify_url = auth_token.substr(verify_start + marker.length, auth_token.length); 
        verify_url = verify_url.substr(0,verify_url.indexOf('|'));

        //console.log(verify_url);
     
        function verifyData(error, data) {
            if (error) {
                console.log("Unpacking threw an error");
                console.log(error);
            }

            if (data !== null && data !== 'undefined') {
                console.log("Got back unpacked data");
                console.log(data);

                var tokenSignature = auth_token.substr(auth_token.indexOf("sig=") + 4, auth_token.length);
                console.log(tokenSignature);

                var tokenVerify = rsa.createVerifier().verify(tokenSignature, verify_url, pubkey);
                console.log(tokenVerify);
            }
        }

   
        https.get(verify_url, function (verify_response) {
            console.log(verify_response.headers);

            if (verify_response.headers['content-encoding'] && verify_response.headers['content-encoding'].toLowerCase().indexOf('gzip') > -1) {
                var buffer = [];
                var unzip = zlib.createGunzip();
                verify_response.pipe(unzip);     

                unzip.on('data', function (response_data) {
                    buffer.push(response_data.toString());
                }).on('end', function () {
                    verifyData(null, buffer.join(""));
                }).on('error', function (e) {
                    verifyData(e);
                });
            }
            else {
                verify_response.on('data', function (response_data) {
                    var jsonResponse = response_data.toString('utf8');

                    console.log(jsonResponse);

                    //verifyData(null, jsonResponse.pubkey);
            }
        }).on('error', function (e) {
            console.log("Verification error");
            console.log(e);
        });
*/

    }

    // check for and set the category, which will determine which core we search within
    if (req.query.hasOwnProperty('category') && req.query.category !== null && req.query.category !== '') {
        validatedParams.category = req.query.category;
    }

    // check for and set the number of items per page
    if (req.query.hasOwnProperty('itemsPerPage') && req.query.itemsPerPage !== null && req.query.itemsPerPage !== '') {
        validatedParams.count = parseInt(req.query.itemsPerPage);
    }

    // check for and set the current page
    if (req.query.hasOwnProperty('page') && req.query.page !== null && req.query.page !== '') {
        var currentPage = parseInt(req.query.page);

        if (currentPage < 1) {
            res.send(404, "Page : " + currentPage + ", No such page!");
        }

        validatedParams.start = (currentPage - 1) * validatedParams.count;
    }

       
    // check for and set the type of sort, and then the sort order
    if (req.query.hasOwnProperty('sortType') && req.query.sortType !== null && req.query.sortType !== '') {
        var sortType = req.query.sortType;

        if (sortType !== "alphabetical" && sortType !== "relevance") {
            throw new Error("Unrecognized sort : " + sortType);
        }

        if (sortType === "alphabetical") {
            if (plugins[validatedParams.category].solr.core === "genomes" || plugins[validatedParams.category].solr.core === "features") {
                validatedParams.sort = "scientific_name_sort";
            }
            else if (plugins[validatedParams.category].solr.core === "metagenomes") {
                validatedParams.sort = "mixs_project_and_mg_name_sort";
            }
            else if (plugins[validatedParams.category].solr.core === "literature") {
                validatedParams.sort = "title";
            }
            else {
                validatedParams.sort = "score";
            }

            var sortOrder = 'asc';
            if (req.query.hasOwnProperty('sortOrder') && req.query.sortOrder !== null && (req.query.sortOrder === 'asc' || req.query.sortOrder === 'desc')) {
                validatedParams.sort += " " + req.query.sortOrder;
            }
            else {
                validatedParams.sort += " " + sortOrder;
            }
        }
        else if (sortType === "relevance") {
            validatedParams.sort = "score";

            var sortOrder = 'asc';
            if (req.query.hasOwnProperty('sortOrder') && req.query.sortOrder !== null && (req.query.sortOrder === 'asc' || req.query.sortOrder === 'desc')) {
                validatedParams.sort += " " + req.query.sortOrder;
            }
            else {
                validatedParams.sort += " " + sortOrder;
            }
        }
        else {
            // unknown sort type
            res.send(404, "" + sortType + " is not a valid sort type!");
        }
    }   

    // check for the presence of a query string
    if (req.query.hasOwnProperty('q') && req.query.q !== null && req.query.q !== '') {
        validatedParams.queryString = '&q=text:' + req.query.q;
    }
    else {
        validatedParams.queryString = "&q=''";   
    }

    return validatedParams;
}



function computeSolrQuery(options) {
    solr_url = hostURL;
    var mapping = "search";
    var paramString = "";

    //var workspaceJoin = "&fq=(owner: OR shared_with:***REMOVED*** OR global:a OR global:r OR global:w)";

    //console.log(plugins);
    //console.log(options);

    // if category plugin is found, use that to compute the url
    if (plugins.hasOwnProperty(options.category)) {
        var core = plugins[options.category].solr.core;

        solr_url += mapping + '/' + core;

        paramString = plugins[options.category].solr.query_string;
    }
    else {
        console.log(plugins);
        console.log(options);
        throw new Error("No such category '" + options.category + "' !");
    }

    solr_url += '/select?wt=json';

    paramString += '&start=' + options.start + '&rows=' + options.count;

    if (options.hasOwnProperty('sort') && options.sort !== null) {
        paramString += '&sort=' + options.sort;
    }

    //console.log(plugins[options.category]);

    solr_url += options.queryString + paramString;

    if (plugins[options.category].solr.hasOwnProperty('secure') && plugins[options.category].solr.secure === true) {        
        if (!options.hasOwnProperty('username') || options.username === null) {
            throw new Error("Missing or invalid authentication token!");
        }        

        var workspace_url = "https://kbase.us/services/workspace_service/";

        //console.log(kbase);

        var workspace_service = new kbase.workspaceService(workspace_url);

        workspace_service.list_workspaces({"auth_token": options.auth_token}, processRequest);
    }

    return solr_url;
}


function processRequest(ws_list) {
    var workspace_filter = "";

    for (var i = ws_list.length - 1; i >= 0; i--) {
        if (ws_list[i][4] !== 'n' || ws_list[i][5] !== 'n') {
            workspace_filter += "&fq=workspace_id:'" + ws_list[i][0] + "'";
        }
    }

    solr_url += workspace_filter;
}



exports.search = function(req, res) {
    validated = validateInputs(req, res);

    currentRequest = req;
    currentResponse = res;

    var solr_request;

    async.each([validated], function(input, callback) {
        solr_request = computeSolrQuery(input); 
    }, function(err) {
        console.log(err);
    });

    console.log(solr_request);

//    request(solr_request, function (error, response, body) {
    request({
	'uri':solr_request,
	'auth': {
		'user':solr_user,
		'pass':solr_pass,
		},
	} , function (error, response, body) {
        if (!error && response.statusCode == 200) {
            var allResp = JSON.parse(body);

            req.result = {};

            req.result.status = response.statusCode;
            req.result.found = allResp.response.numFound;
            req.result.items = allResp.response.docs;
            req.result.itemCount = allResp.response.docs.length;
            req.result.itemsPerPage = validated.count;
            req.result.page = allResp.response.start/validated.count + 1;
            req.result.url = req.url;            

            res.jsonp(req.result);
        } 
        else {
            console.log(error);
            console.log(response);
            //console.log(body);

            //req.result.status = response.statusCode;
            res.jsonp(req.result);
        }
    });


};



