#!/bin/bash

##
# Script to deploy KBase search in KBase runtime
##

echo 
echo "   _  ______                    _____                     _      " 
echo "  | |/ /  _ \                  / ____|                   | |     " 
echo "  | ' /| |_) | __ _ ___  ___  | (___   ___  __ _ _ __ ___| |__   " 
echo "  |  < |  _ < / _' / __|/ _ \  \___ \ / _ \/ _' | '__/ __| '_ \  " 
echo "  | . \| |_) | (_| \__ \  __/  ____) |  __/ (_| | | | (__| | | | " 
echo "  |_|\_\____/ \__,_|___/\___| |_____/ \___|\__,_|_|  \___|_| |_| " 
echo 

## 
# Globals
##
VERSION="0.1.0"
SERVICE="search"
LOCALBASE=`pwd`
L_PREFIX=$LOCALBASE/build
PREFIX=${PREFIX-/kb/deployment}
RUNTIME=${RUNTIME-/kb/runtime}
SEARCH_KEYWORD="coli"
DATA_URL="http://pmi.ornl.gov:8080/data/kbase"
INSTANCE="localhost"

# Apps 
JAVA=""
GIT=""
WGET=""
CURL=""
NODE=""

# Tomcat
TOMCAT_BASE="$RUNTIME/tomcat"
TOMCAT_ETC="$TOMCAT_BASE/conf"
TOMCAT_INIT="$TOMCAT_BASE/bin"
TOMCAT_PID="$TOMCAT_BASE/tomcat.pid"
TOMCAT_PORT=7077
TOMCAT_USER=root

# Solr
SOLR_L_PREFIX=$L_PREFIX/solr
SOLR_PREFIX=$PREFIX/services/$SERVICE/solr
SOLR_DESCRIPTOR=$TOMCAT_ETC/Catalina/localhost/search.xml
SOLR_DATA_DIR=$SOLR_PREFIX/data

# Search API
API=$LOCALBASE/searchService
API_PREFIX=$PREFIX/services/$SERVICE/searchService
API_HOST="localhost"
API_PORT=7078

# Search Application
#APPN=$LOCALBASE/searchWebapp
#APPN_PREFIX=$PREFIX/services/$SERVICE/searchWebapp
#APPN_HOST="localhost"
#APPN_PORT=7079

# Search Doc Application
#APPDOC=$LOCALBASE/searchDocapp
#APPDOC_PREFIX=$PREFIX/services/$SERVICE/searchDocapp
#APPDOC_HOST="localhost"
#APPDOC_PORT=7080


##
# Help
##
displayHelp() {
  cat <<-help

  Usage: setup.sh [options]


  Options:

    -V, --version            Output current version of search
    -h, --help               Display help information
    -c, --check	             Make dependency checks
    -I, --import             Import the data into Solr
    -i, --install            Install tomcat and service code
    -s, --start              Start all search related services/apps
    -x, --stop               Stop all search related services/apps
    -t, --test               Test all the services and apps

    --install-tomcat         Install tomcat
    --test-tomcat            Test tomcat

    --test-pubs              Test literature
    --test-genomes           Test genomes
    --test-model             Test models
    --test-features          Test features
    
    --start-service          Start just the service
    --start-app              Start just the web app
    --start-docapp           Start just the search doc app
    
    --test-service           Test just the service
    --test-app               Test just the web app
    --test-docapp            Test just the search doc app

    --stop-service           Stop just the service
    --stop-app               Stop just the web app
    --stop-docapp            Stop just the search doc app

    --check-redis            Check if redis is running, if not run it
    --check-catalina         Check if catalina is available.
    --restart-redis          Check tomcat, if running restart it.
    --purge-contents [core]  Purge all the contents of the core
    
  Examples:

    setup.sh --help
    setup.sh --import
    setup.sh --install
    setup.sh --start
    setup.sh --test


help
  exit 0
}

##
# version
##
displayVersion() {
	log version "$VERSION"
}


##
# Log <type> <msg>
##
log() {
	printf "  \033[36m%10s\033[0m : \033[90m%s\033[0m\n" $1 "$2"
}

##
# Exit with the given <msg ...>
##

abort() {
	printf "\n  \033[31mError: $@\033[0m\n\n" && exit 1
}

## 
# Check if you've got enough permission to do this
##
checkPermission() {
	log checking privileges;
	test $EUID != 0 &&  abort "You need to have elevated previliges to do this."
	log status OK;
	echo ;
}


## 
# Test and see if git is installed 
##
checkGit() {
	log checking git;
	a=`type -P git` &> /dev/null \
		&& {
			log found "$a";
			GIT=$a;
		} \
		|| {
			abort "Need git, please install it."
		}
	echo ;
}
                                                               

## 
# Test and see if JDK is installed 
##
checkJava() {
	log checking java
	test -n "$JAVA_HOME" || \
		abort 'JAVA_HOME variable not set, Did you source user_env.sh ?'
	log status "\$JAVA_HOME - $JAVA_HOME"
	echo ;
}

## 
# Test and see if wget is installed 
##
checkWget() {
	log checking wget;
	a=`type -P wget` &> /dev/null \
		&& {
			log found "$a";
			WGET=$a;
		} \
		|| {
			abort "Need wget, please install it."
		}

	echo ;
}

## 
# Test and see if curl is installed 
##
checkCurl() {
	log checking curl;
	a=`type -P curl` &> /dev/null \
		&& {
			log found "$a";
			CURL=$a;
		} \
		|| {
			abort "Need curl, please install it."
		}

	echo ;
}

## 
# Test and see if node is installed 
##
checkNode() {
	log checking node;
	a=`type -P node` &> /dev/null \
		&& {
			log found "$a";
			NODE=$a;
		} \
		|| {
			abort "Need node, please install it."
		}

	echo ;
}


##
# Check for tomcat
##
checkTomcat() {
	log checking tomcat
	test -n "$CATALINA_HOME" || \
		abort 'CATALINA_HOME variable not set, Did you source user_env.sh ?'
	log status "\$CATALINA_HOME - $CATALINA_HOME"
	echo ;
}

##
# Check for redis server
##
checkRedis() {
	log checking redis
	redisServer=`which redis-server`
	redisClient=`which redis-cli`

	(test -x "$redisServer" && \
		test -x "$redisClient")  || \
	abort "Redis missing, please install it."
	log status OK
	echo ;

}

##
# Check if redis is running
##
redis_running() {
	log running "redis"
	redisResponse=`redis-cli PING`
	test $redisResponse != "PONG" && \
		/etc/init.d/redis-server start > /dev/null
	log status OK;

	echo;
}

##
# API test function. Looking for 200 HTTP return code.
##
is_ok() {

	#log status "`curl -Is $1 | head -n 1 | grep 200 > /dev/null
	log status "`curl -Is $1 | head -n 1 | grep 200 `"

	## How to call this function
	#is_ok http://google.com || abort "invalid response"
	echo;
}


##
# install tomcat
##
installTomcat() {
	checkTomcat
	log tuning "tomcat for solr"
	
	log changing "tomcat port"
	sed -i s#port=\"8080\"#port=\"${TOMCAT_PORT}\"#g $TOMCAT_ETC/server.xml


	log adding "kbase search deployment descriptor"
	test -f $SOLR_DESCRIPTOR && rm $SOLR_DESCRIPTOR
	cp  -r $LOCALBASE/solr/Catalina  $TOMCAT_ETC
	sed -i s#SOLR_PREFIX#${SOLR_PREFIX}#g $SOLR_DESCRIPTOR

	log status OK
	echo;

}

installSolr() {
	log creating "solr deployment templates"
	test -d $SOLR_PREFIX || { log creating $SOLR_PREFIX; mkdir -p $SOLR_PREFIX; }
	log creating cores
	cp -r $LOCALBASE/solr/opt/solr/* $SOLR_PREFIX
	chown -R $TOMCAT_USER:$TOMCAT_USER $SOLR_DATA_DIR
	#cp -r  $LOCALBASE/solr/run $SOLR_PREFIX/
	cp -r  $LOCALBASE/solr/bin $SOLR_PREFIX/
	pushd $SOLR_PREFIX > /dev/null
	find . -name "solrconfig.xml" -print | xargs sed -i s#SOLR_DATA_DIR#${SOLR_DATA_DIR}#g 
	popd > /dev/null

	log status OK
	echo;

}

##
# Testing Tomcat
##
testTomcat() {

	log testing "tomcat on http://$INSTANCE:$TOMCAT_PORT/search/"
	is_ok "$INSTANCE:$TOMCAT_PORT/search/#/"

}

##
# Import Publications
##
importPublications() {
	log importing $1

	pushd $LOCALBASE/dataInput > /dev/null
	curl http://$INSTANCE:$TOMCAT_PORT/search/$1/update?separator=%09  --data-binary @$2 -H 'Content-type:text/csv; charset=utf-8' > /dev/null
	sleep 5
	log waiting "Waiting for commit ..."
	sleep 10
	log reload "Reloading index $1 ..."
	curl "http://$INSTANCE:$TOMCAT_PORT/search/admin/cores?wt=json&action=RELOAD&core=$1" > /dev/null
	sleep 5
	log status OK

	log testing "$1 data in solr, checking for total number of docs"
	str=`curl -s "$INSTANCE:$TOMCAT_PORT/search/$1/select?q=*&wt=xml&rows=0" | grep numFound`
	str=`echo ${str#*numFound=\"}`
	str=`echo ${str%\" start*}`
	log found "$str number of docs"
	popd > /dev/null
	echo;
}

##
# Import Genomes
##
importGenomes() {
	log importing $1

	pushd $LOCALBASE/dataInput > /dev/null
	curl http://$INSTANCE:$TOMCAT_PORT/search/$1/update?separator=%09  --data-binary @$2 -H 'Content-type:text/csv; charset=utf-8' > /dev/null
	sleep 5
	log waiting "Waiting for commit ..."
	sleep 10
	log reload "Reloading index $1 ..."
	curl "http://$INSTANCE:$TOMCAT_PORT/search/admin/cores?wt=json&action=RELOAD&core=$1" > /dev/null
	sleep 5
	log status OK

	log testing "$1 data in solr, checking for total number of docs"
	str=`curl -s "$INSTANCE:$TOMCAT_PORT/search/$1/select?q=*&wt=xml&rows=0" | grep numFound`
	str=`echo ${str#*numFound=\"}`
	str=`echo ${str%\" start*}`
	log found "$str number of docs"
	popd > /dev/null
	echo;
}

##
# Import Models
##
importModels() {
	log importing $1

	pushd $LOCALBASE/dataInput > /dev/null
	curl http://$INSTANCE:$TOMCAT_PORT/search/$1/update?separator=%09  --data-binary @$2 -H 'Content-type:text/csv; charset=utf-8' > /dev/null
	sleep 5
	log waiting "Waiting for commit ..."
	sleep 10
	log reload "Reloading index $1 ..."
	curl "http://$INSTANCE:$TOMCAT_PORT/search/admin/cores?wt=json&action=RELOAD&core=$1" > /dev/null
	sleep 5
	log status OK

	log testing "$1 data in solr, checking for total number of docs"
	str=`curl -s "$INSTANCE:$TOMCAT_PORT/search/$1/select?q=*&wt=xml&rows=0" | grep numFound`
	str=`echo ${str#*numFound=\"}`
	str=`echo ${str%\" start*}`
	log found "$str number of docs"
	popd > /dev/null
	echo;
}

## 
# Import Features
##
importFeatures() {
	log importing $1

	pushd $LOCALBASE/dataInput > /dev/null

	declare -a featureData=(FeatureGenomeTaxonomy0.txt);

#	declare -a featureData=(FeatureGenomeTaxonomy0.txt FeatureGenomeTaxonomy1.txt FeatureGenomeTaxonomy2.txt \
#		FeatureGenomeTaxonomy3.txt FeatureGenomeTaxonomy4.txt FeatureGenomeTaxonomy5.txt \
#		FeatureGenomeTaxonomy6.txt FeatureGenomeTaxonomy7.txt FeatureGenomeTaxonomy8.txt \
#		FeatureGenomeTaxonomy9.txt FeatureGenomeTaxonomy10.txt FeatureGenomeTaxonomy11.txt \
#		FeatureGenomeTaxonomy12.txt FeatureGenomeTaxonomy13.txt FeatureGenomeTaxonomy14.txt \
#		FeatureGenomeTaxonomy15.txt FeatureGenomeTaxonomy16.txt FeatureGenomeTaxonomy17.txt \
#		FeatureGenomeTaxonomy18.txt FeatureGenomeTaxonomy19.txt FeatureGenomeTaxonomy20.txt \
#		FeatureGenomeTaxonomy21.txt FeatureGenomeTaxonomy22.txt FeatureGenomeTaxonomy23.txt \
#		FeatureGenomeTaxonomy24.txt FeatureGenomeTaxonomy25.txt FeatureGenomeTaxonomy26.txt \
#		FeatureGenomeTaxonomy27.txt FeatureGenomeTaxonomy28.txt FeatureGenomeTaxonomy29.txt \
#		FeatureGenomeTaxonomy30.txt FeatureGenomeTaxonomy31.txt FeatureGenomeTaxonomy32.txt);

	for i in ${featureData[@]}
	do
		log fetching "$DATA_URL/$i"
		cmd="wget $DATA_URL/$i";
		$cmd 2> /dev/null
		importFeatureData $1 $i
	done
	log status OK

	popd > /dev/null
	echo;
}

importFeatureData() {
	log importing $1 - $2

	pushd $LOCALBASE/dataInput > /dev/null
	curl http://$INSTANCE:$TOMCAT_PORT/search/$1/update?separator=%09  --data-binary @$2 -H 'Content-type:text/csv; charset=utf-8' > /dev/null
	sleep 5
	log waiting "Waiting for commit ..."
	sleep 10
	log reload "Reloading index $1 ..."
	curl "http://$INSTANCE:$TOMCAT_PORT/search/admin/cores?wt=json&action=RELOAD&core=$1" > /dev/null
	sleep 5
	echo ;

}
##
# Check list & order.
##
checks() {
	checkPermission
	checkGit
	checkWget
	checkCurl
	checkNode
	checkJava
	checkTomcat
	#checkRedis
}

##
# Import All
##
importAll() {

	log importing "Data"
	test -d $SOLR_PREFIX || alert "Please run make first."
	checks
	importPublications literature publication.txt
	importGenomes genomes GenomeTaxonomy.txt
	importModels models ModelGenomeTaxonomy.txt
	importFeatures features

	log status "import done"
}


##
# Service Config
##
configService() {
	log setup "KBase Search API Service"
	
	log adding "KBase Search API configuration"
	test -d $API_PREFIX && rm -rf $API_PREFIX
	test -d $API_PREFIX || { log creating $API_PREFIX; mkdir -p $API_PREFIX; }
	cp  -r $API  $API_PREFIX

	log install "KBase Search API dependencies"
	pushd $API_PREFIX > /dev/null
	npm install -q &> /dev/null
	popd > /dev/null
	log status OK
	echo ;

}

##
# Test Service
##
testService() {

	log testing "KBase API Service"
	is_ok  "$INSTANCE:$API_PORT/search/literature/coli"
	echo ;
}



##
# Search Application Config
##
configApp() {
	log setup "KBase Search Application"
	
	log adding "KBase Search Appn configuration"
	test -d $APPN_PREFIX && rm -rf $APPN_PREFIX
	cp  -r $APPN  $APPN_PREFIX

	log install "KBase Search Appn dependencies"
	pushd $APPN_PREFIX > /dev/null
	npm install -q &> /dev/null
	popd > /dev/null
	log status OK
	echo ;

}


##
# Test Application
##
testApp() {

	log testing "KBase Search Application"
	is_ok  "$INSTANCE:$APPN_PORT"
	echo ;
}

##
# Search Doc Application Config
##
configAppDoc() {
	log setup "KBase Search Doc Application"
	
	log adding "KBase Search Doc Appn configuration"
	test -d $APPDOC_PREFIX && rm -rf $APPDOC_PREFIX
	cp  -r $APPDOC  $APPDOC_PREFIX

	log install "KBase Search doc app dependencies"
	apt-get install redis-server  &> /dev/null
	add-apt-repository -y ppa:chris-lea/redis-server &> /dev/null
	apt-get update &> /dev/null
	apt-get install -y redis-server &> /dev/null
	pushd $APPDOC_PREFIX > /dev/null
	npm install -q &> /dev/null
	popd > /dev/null
	log status OK
	echo ;

}


##
# Test Search Doc Appn
##
testAppDoc() {

	log testing "KBase Search Doc Application"
	is_ok  "$INSTANCE:$APPDOC_PORT"
	echo ;
}

##
# Test App, API, Service, Doc Service
##
testAll() {

	log setup "KBase All Tests"
	echo ;

	testService
	testAppDoc
	testApp
	echo ;

	log status OK
}

##
# Install
##
installAll() {
	checks
	installTomcat
	configService
#	configApp
#	configAppDoc
	
	cp start_service $PREFIX/services/$SERVICE
	cp stop_service $PREFIX/services/$SERVICE
}

##
# Tomcat start
##
startTomcat() {
	log restarting tomcat

	pushd $TOMCAT_BASE/bin > /dev/null
	./startup.sh &> /dev/null
	popd > /dev/null

	log status OK

	echo ;
}


##
# Import All
##
importAll() {
	test -d $SOLR_PREFIX || alert "Run --install-solr before importing"
	checks
	startTomcat
	importPublications literature publication.txt
	importGenomes genomes GenomeTaxonomy.txt
	importModels models ModelGenomeTaxonomy.txt
	importFeatures features
}


##
# Handle arguments
##

if test $# -eq 0; then
  displayHelp
else
  while test $# -ne 0; do
    case $1 in
      -V|--version) displayVersion ;;
      -h|--help|help) displaHelp ;;
      -c|--check) checks; exit ;;
      -I|--import|import) importAll; exit ;;
      -i|--install|install) installAll; exit ;;
      -s|--start|startall) startAll; exit ;;
      -x|--stop|stopall) stopAll; exit ;;
      -t|--test|test) testAll; exit ;;
			--install-tomcat) installTomcat; exit;;
			--install-solr) installSolr; exit;;
			--install-service) configService; exit;;
			--install-app) configApp; exit;;
			--install-doc) configAppDoc; exit;;
			--test-service) testService; exit;;
			--test-app) testApp; exit;;
			--test-doc) testAppDoc; exit;;
			--test-tomcat) testTomcat; exit;;
			--check-redis) redis_running; exit;;
			--check-catalina) checkCatalina; exit;;
			--purge-contents) purgeContents $2; exit;;
			--restart-tomcat) restartTomcat; exit;;
			--test-tomcat) testTomcat; exit;;
			--test-pubs) testPublications literature; exit;;
			--test-genomes) testGenomes genomes; exit;;
			--test-models) testModels models; exit;;
			--test-features) testFeatures features; exit;;
			--test-service) testService; exit;;
			--test-app) testApp; exit;;
			--test-docapp) testAppDoc; exit;;
			--start-service) startService; exit;;
			--start-app) startApp; exit;;
			--start-docapp) startAppDoc; exit;;
			--stop-service) stopService; exit;;
			--stop-app) stopApp; exit;;
			--stop-docapp) stopAppDoc; exit;;
      *) displayHelp; exit ;;
    esac
    shift
  done
fi

#checkPermission

