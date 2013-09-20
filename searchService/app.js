
/**
 * Module dependencies.
 */

var express = require('express')
  , routes = require('./routes')
  , https = require('https')
  , http = require('http')
  , fs = require('fs')
  , _ = require('underscore')
  , CONFIG = require('config').conf;
//  , api = require('./libs/api');


var privateKey = fs.readFileSync(CONFIG.system.key).toString();
var certificate = fs.readFileSync(CONFIG.system.certificate).toString();

var options = { 
    key: privateKey,
    cert: certificate
};

var app = module.exports = express();


// Configuration

app.configure(function(){
  app.use(express.bodyParser());
  app.use(express.methodOverride());
  app.disable('x-powered-by');
  app.use(app.router);
});

app.configure('development', function(){
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
});

app.configure('production', function(){
  app.use(express.errorHandler());
});


// Routes
app.get('/', routes.index);
app.get('/search', routes.search);

/*
_.each(API, function( apiCall, callName ) {
  app.get(apiCall.api, routes[apiCall.name] + 'q=keyword');
});
*/

app.get('*', routes.index );

http.createServer(app).listen(CONFIG.system.securePort, function() {
  console.log("**   KBase Search API running on localhost:" + CONFIG.system.securePort);
});

/*
https.createServer(options, app).listen(CONFIG.system.securePort, function() {
  console.log("**   KBase Search API running on localhost:" + CONFIG.system.securePort);
});

https.createServer(app).listen(CONFIG.system.securePort, function() {
  console.log("**   KBase Search API running on localhost:" + CONFIG.system.securePort);
});
*/
