#!/bin/bash

echo 
echo "   _  ______                    _____                     _      " 
echo "  | |/ /  _ \                  / ____|                   | |     " 
echo "  | ' /| |_) | __ _ ___  ___  | (___   ___  __ _ _ __ ___| |__   " 
echo "  |  < |  _ < / _' / __|/ _ \  \___ \ / _ \/ _' | '__/ __| '_ \  " 
echo "  | . \| |_) | (_| \__ \  __/  ____) |  __/ (_| | | | (__| | | | " 
echo "  |_|\_\____/ \__,_|___/\___| |_____/ \___|\__,_|_|  \___|_| |_|2" 
echo 

log() {
  printf "  \033[36m%10s\033[0m : \033[90m%s\033[0m\n" $1 "$2"
}
error() {
    printf "\n  \033[31mError: $@\033[0m\n\n" && exit 1
}

start_service() {
    log starting "search service"
    export PYTHONPATH=$PYTHONPATH:$(pwd)/lib
    export SEARCH_CONFIG_DIRECTORY=$(pwd)/config
    uwsgi --ini $SEARCH_CONFIG_DIRECTORY/uwsgi_search.ini
    if [ "$?" = "0" ]; then
        log status "Service successfully started"
    else
        error "Could not start service"
    fi
}

log pwd $(pwd)
start_service
echo ;
