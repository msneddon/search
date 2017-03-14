#!/bin/bash
if [ $# -eq 0 ] ; then
  if [ ! -f /kb/module/search/config/search_config.ini ]; then
    echo "Config file: /kb/module/search/config/search_config.ini not found! Exiting."
    exit 1;
  fi
  if [ ! -f /kb/module/search/config/uwsgi_search.ini ]; then
    echo "Config file: /kb/module/search/config/uwsgi_search.ini not found! Exiting."
    exit 1;
  fi
  if [ ! -f /kb/module/search/config/categoryInfo.json ]; then
    echo "Config file: /kb/module/search/config/categoryInfo.json not found! Exiting."
    exit 1;
  fi
  sh ./scripts/start_service.sh
elif [ "${1}" = "bash" ] ; then
  bash
else
  echo "Unknown command- use 'start', 'bash', or nothing to enter bash"
fi