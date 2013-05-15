#!/bin/bash

log() {
  printf "  \033[36m%10s\033[0m : \033[90m%s\033[0m\n" $1 "$2"
}

alert() {
	printf "\n  \033[31mError: $@\033[0m\n\n" && exit 1
}


log starting tomcat
log setting environment
SERVICE="solr"
DEPLOYMENT=${DEPLOY-/kb/deployment}
RUNTIME=${RUNTIME-/kb/runtime}
CATALINA_HOME="$RUNTIME/tomcat"
CATALINE_PID="$DEPLOYMENT/services/$SERVICE/run/tomcat.pid"

log executing startup

pushd $CATALINA_HOME > /dev/null
bin/startup.sh > /dev/null
popd > dev/null

log status OK
echo ;


