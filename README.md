# KBase Search

The KBase Search module is responsible for providing a search capability that guides users to KBase data of interest.
A public facing web service provides core search capabilities on KBase data types, 
and a search web UI found in https://github.com/kbase/ui-common and seen from https://narrative.kbase.us provides a
rich client interface to guide users toward KBase data that best meet their criteria.

KBase Search layers on top of [Apache Solr](http://lucene.apache.org/solr/) to provide full-text search of KBase public data.

## KBase Search Deployment

### Dependencies

- [Apache Tomcat](http://tomcat.apache.org)

### Installation

    cd /kb/dev_container/modules
    git clone https://git.kbase.us/search.git
    cd search
    make deploy

    # service must be running for testing    
    /kb/deployment/services/search/start_service
    
    # make test loads real (or for some data types example) data
    make test


