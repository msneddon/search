#!/bin/bash
if [ $# -eq 0 ] ; then
  bash
elif [ "${1}" = "start" ] ; then
  sh ./scripts/start_service.sh
elif [ "${1}" = "bash" ] ; then
  bash
else
  echo "Unknown command- use 'start', 'bash', or nothing to enter bash"
fi