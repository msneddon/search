
/**
 * Module dependencies.
 */

var express = require('express')
  , routes = require('./routes/index')
  , ajax= require('./routes/ajax')
  , _ = require('underscore')
  , CONFIG = require('config').conf
  , API = require('./libs/api');

var app = module.exports = express();

// Configuration

app.configure(function(){
  app.set('views', __dirname + '/views');
  app.set('view engine', 'ejs');
  app.set('view options', {layout: false});
  app.use(express.bodyParser());
  app.use(express.methodOverride());
  app.use(app.router);
  app.use(express.static(__dirname + '/public'));
});

app.configure('development', function(){
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
});

app.configure('production', function(){
  app.use(express.errorHandler());
});

// Routes


// New Routes
app.get('/', routes.index);
app.post('/process', routes.process);
app.get('/processget/:keyword', routes.processget);

app.get('/advanced', routes.advanced);
app.get('/processadvanced/:query/:type', routes.processadvanced);

app.get('/details/:keyword', routes.details);
app.get('/genomedetails/:keyword', routes.genomedetails);

app.get('/longform/:type/:keyword', routes.showeverything);

app.get('/literature/:keyword', routes.literature);
app.get('/literaturedetails/:keyword', routes.literaturedetails);

app.get('/bacteria/:keyword', routes.bacteria);
app.get('/viruses/:keyword', routes.viruses);
app.get('/archaea/:keyword', routes.archaea);
app.get('/eukaryota/:keyword', routes.eukaryota);

app.get('/gene/:keyword', routes.gene);
app.get('/locus/:keyword', routes.locus);
app.get('/prophage/:keyword', routes.prophage);
app.get('/pseudogene/:keyword', routes.pseudogene);
app.get('/promoter/:keyword', routes.promoter);
app.get('/operator/:keyword', routes.operator);
app.get('/proteinbindingsite/:keyword', routes.proteinbindingsite);
app.get('/bindingsite/:keyword', routes.bindingsite);
app.get('/riboswitch/:keyword', routes.riboswitch);
app.get('/rna/:keyword', routes.rna);
app.get('/transposon/:keyword', routes.transposon);
app.get('/mrna/:keyword', routes.mrna);
app.get('/smallrna/:keyword', routes.smallrna);

// Test
app.get('/f1/:keyword', routes.f1);
app.get('/f2/:keyword', routes.f2);
app.get('/f3/:keyword', routes.f3);

// Ajax
//
app.post('/ajax/coexpressed/:id', ajax.coexpressed );
app.post('/ajax/cooccurences/:id', ajax.cooccurences );
app.post('/ajax/features/:type/:id', ajax.getFunctions );
app.post('/ajax/contigs/:id', ajax.getContigs );


//Old

app.get('/test', routes.test);

/*
app.get('/genomes', routes.genomes);
app.post('/genomes', routes.genomesSearch);

app.get('/genes', routes.genes);
app.post('/genes', routes.genesSearch);

app.get('/promoter', routes.promoter);
app.post('/promoter', routes.promoterSearch);

app.get('/rna', routes.rna);
app.post('/rna', routes.rnaSearch);

app.get('/prophage', routes.prophage);
app.post('/prophage', routes.prophageSearch);


app.get('/smallrna', routes.smallrna);
app.post('/smallrna', routes.smallrnaSearch);

app.get('/riboswitch', routes.riboswitch);
app.post('/riboswitch', routes.riboswitchSearch);

app.get('/locus', routes.locus);
app.post('/locus', routes.locusSearch);

app.get('/mrna', routes.mrna);
app.post('/mrna', routes.mrnaSearch);


app.get('/testCountCalls/:keyword', function(req, res ) {
  res.render( 'testCount', {keyword: req.params.keyword});
});

*/

app.listen(CONFIG.system.port, function(){
  console.log("**   KBase Search is running on localhost:" + CONFIG.system.port);
  console.log("**   Please point your browser to <hostname>:" + CONFIG.system.port);
});
