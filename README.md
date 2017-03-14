# KBase Search Service

This is a stripped down fork of the kbase search service that removes much of the legacy configurations and install/deployment files.  It is designed to be run as a docker container.  Here's a a quickstart:

    # build the container
    docker build . -t kbase/search

    # start the service (mounts config into container to set configuration)
    docker run -p 7078:7078 -v $PWD/config:/kb/module/search/config --name mykbsearch -d kbase/search

    curl localhost:7078
    {
      "message": "KBase Search Service"
    }

    curl localhost:7078/categories

    curl "localhost:7078/getResults?itemsPerPage=20&page=1&q=*&category=genomes"