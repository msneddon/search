## KBase Search Deployment

All the source code necessary to deploy KBase Search module independently.

## Installation

cd /kb/dev_container/modules
git clone https://git.kbase.us/search.git
cd search
make deploy
# service must be running for testing
/kb/deployment/services/search/start_service
# make test loads real (or for some data types example) data
make test


