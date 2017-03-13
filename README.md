# KBase Search Service

This is a stripped down fork of the kbase search service that only includes the
basic Flask app wrapper around solr.

    # build the container
    docker build . -t kbsearch

    # start the service (mounts config into container to set configuration)
    docker run -p 7078:7078 -v $PWD/config:/kb/module/search/config --name mykbsearch -d kbsearch

    curl localhost:7078