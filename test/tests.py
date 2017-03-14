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


def check_statuscode(response, code):
    return response.status_code == code


#def test_tomcat_alive():
#    import requests
#
#    response = requests.get("http://localhost:7077")
#    assert check_statuscode(response,200)
#    print "Tomcat is alive and listening at http://localhost:7077"


def test_solr_alive():
    import requests

    response = requests.get("http://localhost:7077/search/")
    assert check_statuscode(response,200)
    print "Solr is alive and listening at http://localhost:7077/search/"


def test_solr_cores_nonempty():
    import os
    import requests

    solr_url = "http://localhost:7077/search/"

    print "Test to see if each solr core is active."
    cores = os.listdir(os.path.join(os.environ["TARGET"], "services/search/solr/data/"))
    for c in cores:
        response = requests.get(solr_url + "/#/" + c + "/")
        print "core: " + c
        assert check_statuscode(response,200)


def test_service_alive():
    import requests
    
    response = requests.get("http://localhost:7078")    
    assert check_statuscode(response,200)
    print "KBase Search service is alive and listening at http://localhost:7078"


def getCategories():
    return [x.split('.')[0] for x in os.listdir(os.path.join(os.environ["TARGET"], "services/search/config/plugins/categories/")) if ".json" in x]

def getInvalidCategories():
    return [x for x in os.listdir(os.path.join(os.environ["TARGET"], "services/search/config/plugins/categories/")) if ".json" in x]


def invalid_query_service_categories(queryString):
    import requests
    
    service_url = "http://localhost:7078/getResults?q=" + queryString + "&category="

    for c in getInvalidCategories():
        print "\tcategory: " + c
        response = requests.get(service_url + c)
        print "\tChecking for status 400"
        assert check_statuscode(response,400)
        print "\tChecking for response body"
        try:
            search_result = response.json()    
        except Exception, e:
            print e

        print "\tSearched for " + queryString + "\n\n"

def query_service_categories(queryString):
    import requests
    
    service_url = "http://localhost:7078/getResults?q=" + queryString + "&category="

    for c in getCategories():
        print "\tcategory: " + c
        response = requests.get(service_url + c)
        print "\tChecking for status 200"
        assert check_statuscode(response,200)
        print "\tChecking for response body"
        try:
            search_result = response.json()
        except Exception, e:
            print e

        print "\tSearched for " + queryString

        if search_result["totalResults"] == 0:
            print "\tNo results found."
            print "\t" + str(search_result) + "\n\n"
        else:
            print "\tFound " + str(search_result["totalResults"]) + " results"
            print "\tFirst item : " + str(search_result["items"][0]) + "\n\n"

def test_invalid_service_queries():
    for n in ["*", "s*", "arabidopsis", "dnaa", "e. coli"]:
        invalid_query_service_categories(n)

def test_service_queries():
    for n in ["*", "s*", "arabidopsis", "dnaa", "e. coli"]:
        query_service_categories(n)
