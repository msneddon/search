import nose
import os
import ConfigParser

# future improvement for advanced testing
def setup():
    #config = ConfigParser.ConfigParser()
    pass
    
# future improvement for advanced testing
def teardown():
    pass


def is_status500(response):
    return response.status_code == 500

def is_status200(response):
    return response.status_code == 200


def test_tomcat_alive():
    import requests

    response = requests.get("http://localhost:7077")
    assert is_status200(response)
    print "Tomcat is alive and listening at http://localhost:7077"


def test_solr_alive():
    import requests

    response = requests.get("http://localhost:7077/search/")
    assert is_status200(response)
    print "Solr is alive and listening at http://localhost:7077/search/"


def test_solr_cores_nonempty():
    import os
    import requests

    solr_url = "http://localhost:7077/search/"

    print "Test to see if each solr core is active."
    cores = os.listdir("/kb/deployment/services/search/solr/data/")
    for c in cores:
        response = requests.get(solr_url + "/#/" + c + "/")
        print "core: " + c
        assert is_status200(response)


def test_service_alive():
    import requests
    
    response = requests.get("http://localhost:7078")    
    assert is_status200(response)
    print "KBase Search service is alive and listening at http://localhost:7078"


def getCategories():
    return [x.split('.')[0] for x in os.listdir("/kb/deployment/services/search/config/plugins/categories/") if ".json" in x]

def getBadCategories():
    return [x for x in os.listdir("/kb/deployment/services/search/config/plugins/categories/") if ".json" in x]


def bad_query_service_categories(queryString):
    import requests
    
    service_url = "http://localhost:7078/getResults?q=" + queryString + "&category="

    for c in getBadCategories():
        print "category: " + c
        response = requests.get(service_url + c)
        print "Checking for status 500"
        assert is_status500(response)
        print "Checking for response body"
        try:
            search_result = response.json    
        except Exception, e:
            print e

        print "Searched for " + queryString

        if search_result["totalResults"] == 0:
            print "No results found."
            print str(search_result)
        else:
            print "Found " + str(search_result["totalResults"]) + " results"
            print "First item : " + str(search_result["items"][0])

def query_service_categories(queryString):
    import requests
    
    service_url = "http://localhost:7078/getResults?q=" + queryString + "&category="

    for c in getCategories():
        print "category: " + c
        response = requests.get(service_url + c)
        print "Checking for status 200"
        assert is_status200(response)
        print "Checking for response body"
        try:
            search_result = response.json    
        except Exception, e:
            print e

        print "Searched for " + queryString

        if search_result["totalResults"] == 0:
            print "No results found."
            print str(search_result)
        else:
            print "Found " + str(search_result["totalResults"]) + " results"
            print "First item : " + str(search_result["items"][0])

def test_bad_service_queries():
    for n in ["*", "s*", "arabidopsis", "dnaa", "e. coli"]:
        bad_query_service_categories(n)

def test_service_queries():
    for n in ["*", "s*", "arabidopsis", "dnaa", "e. coli"]:
        query_service_categories(n)
