
var cdmi = require( 'kbase').KBaseCDMI;
var _  = require('underscore');
_.str = require('underscore.string');

var kbaseapi = new cdmi();

exports.coexpressed = function (req, res) {
  var keyword = req.params.id;
  var fids = [keyword];  

  var entireReturn = {};
  var returns = [];
  selfres = res;
  var coResults = kbaseapi.fids_to_coexpressed_fids([fids]
      , function( data ) {

          var first;
          var returnSize = 10;


          for (first in data) break;

          var dataobjs = _.object(data[first]);
          
          var allfids2 = _.keys(_.object(data[first]));
          entireReturn.count = allfids2.length;

          var fids2 = _.first(allfids2, returnSize);
          entireReturn.returned = fids2.length;

          if ( entireReturn.count - entireReturn.returned < 0 )
            entireReturn.remaining = 0;
          else
            entireReturn.remaining = entireReturn.count - entireReturn.returned ;

          entireReturn.data = returns;

          if (entireReturn.returned != 0 ) {

            var res = kbaseapi.fids_to_functions([fids2]
              , function(data2) {
                var i;
                for (i in data2 ) {
                  var obj = { 
                              id : i
                             ,function: data2[i]
                             ,pc : dataobjs[i]
                  };

                  // NOTE: Did this to avoid adding all ids with empty feature entry
                  if ( obj.function.length != 0 ) { 
                    returns.push(obj);
                  } else {
                    obj.function = "FUNCTION MISSING - Showing KBase Id instead: " + obj.id;
                    returns.push(obj);
                  }   
                }
                entireReturn.data = returns;
                selfres.json(entireReturn);

              }
              , function( errorCode2 ) { 
                  selfres.json({ error: errorCode2 } );
            });
          } else {
            selfres.json(entireReturn);
          }

      }
      , function( errorCode ) {
          selfres.json({ error: errorCode } );
  });



 };

exports.cooccurences = function (req, res) {
  var keyword = req.params.id;
  var fids = [keyword];  

  var entireReturn = {};
  var returns = [];
  selfres = res;
  var coResults = kbaseapi.fids_to_co_occurring_fids([fids]
      , function( data ) {

          var first;
          var returnSize = 10;


          for (first in data) break;

          var dataobjs = _.object(data[first]);
          
          var allfids2 = _.keys(_.object(data[first]));
          entireReturn.count = allfids2.length;

          var fids2 = _.first(allfids2, returnSize);
          entireReturn.returned = fids2.length;

          if ( entireReturn.count - entireReturn.returned < 0 )
            entireReturn.remaining = 0;
          else
            entireReturn.remaining = entireReturn.count - entireReturn.returned ;

          entireReturn.data = returns;

          if (entireReturn.returned != 0 ) {

            var res = kbaseapi.fids_to_functions([fids2]
              , function(data2) {
                var i;
                for (i in data2 ) {
                  var obj = { 
                              id : i
                             ,function: data2[i]
                             ,cooccur : dataobjs[i]
                  };

                  // NOTE: Did this to avoid adding all ids with empty feature entry
                  if ( obj.function.length != 0 ) { 
                    returns.push(obj);
                  } else {
                    obj.function = "FUNCTION MISSING - Showing KBase Id instead: " + obj.id;
                    returns.push(obj);
                  }   
                }
                entireReturn.data = returns;
                selfres.json(entireReturn);

              }
              , function( errorCode2 ) { 
                  selfres.json({ error: errorCode2 } );
            });
          } else {
            selfres.json(entireReturn);
          }

      }
      , function( errorCode ) {
          selfres.json({ error: errorCode } );
  });



 };

exports.getFunctions = function (req, res) {
  var keyword = req.params.id;
  var type = req.params.type;
  var fids = [keyword];  
  var types = [type];  
  var full = req.query.count;

  console.log(req.query);

  var entireReturn = {};
  var returns = [];
  selfres = res;


  var fResults = kbaseapi.genomes_to_fids([fids,types]
      , function( data ) {
          var first;

          var returnSize = 10;
          for (first in data) break;
          
          var allfids2 = data[first];
          entireReturn.count = allfids2.length;

          entireReturn.data = returns;

          if (full === 'all') {
            console.log('********its full request');
            returnSize = entireReturn.count;
            entireReturn.returned = entireReturn.count;
          }


          var fids2 = _.first(allfids2, returnSize);
          entireReturn.returned = fids2.length;

          if ( entireReturn.count - entireReturn.returned <= 0 ) {
            entireReturn.remaining = 0;
          } else {
            entireReturn.remaining = entireReturn.count - entireReturn.returned ;
          }


          if (entireReturn.returned != 0 ) {


            var res = kbaseapi.fids_to_functions([fids2]
              , function(data2) {
                var i;
                for (i in data2 ) {
                  var obj = { 
                              id : i
                             ,function: data2[i]
                  };

                  // NOTE: Did this to avoid adding all ids with empty feature entry
                  if ( obj.function.length != 0 ) {
                    returns.push(obj);
                  } else {
                    obj.function = "FUNCTION MISSING - Showing KBase Id instead: " + obj.id;
                    returns.push(obj);
                  }

                }
                entireReturn.data = returns;
                selfres.json(entireReturn);

              }
              , function( errorCode2 ) { 
                  console.log(errorCode2);
                  selfres.json({ error: errorCode2 } );
            });
          } else {
            console.log(entireReturn);
            selfres.json(entireReturn);
          }

      }
      , function( errorCode ) {
          console.log(errorCode);
          selfres.json({ error: errorCode2 } );
  });

 };

exports.getContigs = function (req, res) {
  var keyword = req.params.id;
  var fids = [keyword];  

  var entireReturn = {};
  var returns = [];
  selfres = res;


  var fResults = kbaseapi.genomes_to_contigs([fids]
      , function( data ) {
          var first;
          var returnSize = 10;
          for (first in data) break;

          
          var allfids2 = data[first];
          entireReturn.count = allfids2.length;

          var fids2 = _.first(allfids2, returnSize);
          entireReturn.returned = fids2.length;
          entireReturn.data = returns;

          if ( entireReturn.count - entireReturn.returned < 0 )
            entireReturn.remaining = 0;
          else
            entireReturn.remaining = entireReturn.count - entireReturn.returned ;

          if (entireReturn.returned != 0 ) {

            var res = kbaseapi.fids_to_functions([fids2]
              , function(data2) {
              //console.dir(data2);
                var i;
                for (i in data2 ) {
                  var obj = { 
                              id : i
                             ,function: 'KBase Contig ID: ' + i
                  };

                  // NOTE: Did this to avoid adding all ids with empty feature entry
                  if ( obj.function.length != 0 ) {
                    returns.push(obj);
                  } else {
                    obj.function = "FUNCTION MISSING - Showing KBase Id instead: " + obj.id;
                    returns.push(obj);
                  }

                }
                entireReturn.data = returns;
                selfres.json(entireReturn);

              }
              , function( errorCode2 ) { 
                  console.log(errorCode2);
                  selfres.json({ error: errorCode2 } );
            });
          } else {
            console.log(entireReturn);
            selfres.json(entireReturn);
          }

      }
      , function( errorCode ) {
          console.log(errorCode);
          selfres.json({ error: errorCode2 } );
  });

 };

exports.index = function(req, res){
  var searchType = '';
  res.render('index', { type: searchType } );
};

