import flask
import json
import requests
import logging

import biokbase.workspace.client

from exceptions import InvalidSearchRequestError

categories = dict()
plugins = dict()

logger = logging.getLogger()

def get_results(request):
    capture_metrics(request)

    # validate all of the required inputs
    validated = validate_inputs(request.args)
    validated['request'] = request.url

     # compute the solr url based on the user query
    solr_url = compute_solr_query(validated)
    
    logger.info(solr_url)

    solr_results = dict()
    # call solr and retrieve result set
    try:
        solr_user = "admin"
        solr_pass = "***REMOVED***"

        try :
            response = requests.get(solr_url, auth=requests.auth.HTTPBasicAuth(solr_user, solr_pass))
            solr_results = response.json()
        except:
            logger.error(solr_url)
            response = requests.get(solr_url)
            solr_results = response.json()
    except Exception, e:
        logger.exception(e)

    try:
        # transform the json into the output format    
        results = transform_solr_json(solr_results, validated)
    except Exception, e:
         logger.exception(e)
         raise

    if validated.has_key("callback"):
        response = validated["callback"] + "(" + str(json.dumps(results)) + ")"
    else:
        response = flask.jsonify(results)

    #logger.info(str(response))

    # send it back to the client
    return response


def transform_solr_json(results, params):
    #logger.info(results)

    transform = dict()
    transform["items"] = list()
    
    for n in results["response"]["docs"]:
        del n['_version_']
        transform["items"].append(n)

    transform["currentPage"] = params["page"]
    transform["totalResults"] = results["response"]["numFound"]
    transform["itemCount"] = len(results["response"]["docs"])
    transform["itemsPerPage"] = params["count"]

    # find the page number in the request url to modify it for first, next, previous, last
    pageSubstringStart = params["request"].find("&page=") + 6
    pageSubstringEnd = params["request"].find("&", pageSubstringStart)

    transform["navigation"] = dict()
    transform["navigation"]["self"] = params["request"]
    transform["navigation"]["first"] = params["request"][:pageSubstringStart] + "1" + params["request"][pageSubstringEnd:]
        
    if params["page"] > 1:
        transform["navigation"]["previous"] = params["request"][:pageSubstringStart] + str(params["page"] - 1) + params["request"][pageSubstringEnd:]

    if (params["start"] + transform["itemsPerPage"]) < transform["totalResults"]:
        transform["navigation"]["next"] = params["request"][:pageSubstringStart] + str(params["page"] + 1) + params["request"][pageSubstringEnd:]
        
    if transform["totalResults"] % transform["itemsPerPage"] == 0:
        remainder = 0
    else:
        remainder = 1
    
    transform["navigation"]["last"] = params["request"][:pageSubstringStart] + str(transform["totalResults"]/transform["itemsPerPage"] + remainder) + params["request"][pageSubstringEnd:]


    # handle faceting
    if results.has_key("facet_counts"):
        logger.info(results["facet_counts"])
        
        transform["facets"] = results["facet_counts"]["facet_fields"]

    #logger.info(transform)
    
    return transform


def validate_inputs(query):
    validatedParams = dict()

    # check for a jsonp callback
    if query.has_key('callback') and query['callback'] is not None:
        validatedParams['callback'] = query['callback'][:]

    # check for the auth token
    if query.has_key('token') and query['token'] is not None:
        auth_token = query['token']
        validatedParams['auth_token'] = query['token'][:]
        validatedParams['username'] = auth_token[0:auth_token.find('|')].split('=')[1]

    # check for and set the category, which will determine which core to search
    if query.has_key('category') and query['category'] is not None:
        validatedParams['category'] = query['category'][:]

    # check for and set the number of items per page
    if query.has_key('itemsPerPage') and query['itemsPerPage'] is not None:
        validatedParams['count'] = int(query['itemsPerPage'])
    else:
        validatedParams['count'] = 10

    # check for and set the current page
    if query.has_key('page') and query['page'] is not None:
        currentPage = int(query['page'])

        if currentPage < 1:
            raise InvalidSearchRequestError(query['page'] + " is not a valid page number in this result set!")

        validatedParams['page'] = currentPage
        validatedParams['start'] = (currentPage - 1) * validatedParams['count']
    else:
        validatedParams['page'] = 1
        validatedParams['start'] = 0

    # check for and set the fields to sort on
    if query.has_key('sort') and query['sort'] is not None:
        sortQuery = query['sort'][:]
        sortString = ""

        sortFields = sortQuery.split(',')
        
        for x in sortFields:
            try:
                field, order = x.split(' ')
            except:
                raise InvalidSearchRequestError(x + " is not in the format of 'sort_field sort_order'!")
            
            if not field in plugins[validatedParams['category']]['solr']['fields']:
                raise InvalidSearchRequestError(field + " is not a valid sorting field!")
            
            if not order in ['asc', 'desc']:
                raise InvalidSearchRequestError(order + " is not a valid sorting order!")
                                                
            sortString += x
        
        validatedParams['sort'] = sortString

    # check for any facet selections
    if query.has_key('facets') and query['facets'] is not None:
        individualFacets = query['facets'].split(',')
        
        for x in individualFacets:
            field_name, field_query = x.split(":")
            
            if not field_name in plugins[validatedParams['category']]['solr']['fields']:
                raise InvalidSearchRequestError(field_name + " is not a valid faceting field!")
            
            # the query should be one of, a single int, a single float, a range of int or float, or an alpha string
            
                                
        validatedParams['facets'] = query['facets'][:]

    # check for the presence of a query string
    if query.has_key('q') and query['q'] is not None:
        validatedParams['queryString'] = "&q=text:" + query['q']
    else:
        validatedParams['queryString'] = "&q=''"

    return validatedParams
            

def capture_metrics(request):
    logger.info(str(request))


def compute_solr_query(options):
    solr_url = "http://140.221.84.237:7077/"
    mapping = "search"
    paramString = ""

    if plugins.has_key(options['category']):
        core = plugins[options['category']]['solr']['core']

        solr_url += mapping + '/' + core
        
        paramString = plugins[options['category']]['solr']['query_string']
    else:
        raise Exception("No such category \"" + options['category'] + "\" !")

    solr_url += '/select?wt=json'

    paramString += "&start=" + str(options['start']) + "&rows=" + str(options['count'])

    if options.has_key('sort') and options['sort'] is not None:
        paramString += "&sort=" + options['sort']

    if options.has_key('facets') and options['facets'] is not None:
        facetDict = dict()
    
        for x in options['facets'].split(','):
            facetKey, facetValue = x.split(":")
            if not facetDict.has_key(facetKey):
                facetDict[facetKey] = facetValue
            else:
                facetDict[facetKey] += " OR " + facetValue
        
        for k in facetDict.keys():    
            paramString += "&fq=" + k + ":" + facetDict[k]

    solr_url += options['queryString'] + paramString

    if plugins[options['category']]['solr'].has_key('secure') and plugins[options['category']]['solr']['secure'] == True:
        if not options.has_key('username') or options['username'] is None:
            raise Exception("Missing or invalid authentication token!")

        workspace_url = "https://kbase.us/services/ws/"

        workspace_service = workspaceClient.workspaceService(workspace_url)
        workpace_service.list_workspaces({"auth_token": options['auth_token']})

    return solr_url


def get_categories():
    categoriesJSON = load_categories()

    return flask.jsonify(categoriesJSON)


#create a categories.json file that can be loaded and sent to the client
def load_categories():
    categories = dict()
    try:
        import os
        import os.path

        categoryFile = open(os.path.join(os.path.abspath(os.curdir),'config/categoryInfo.json'))
        categories = json.loads(categoryFile.read())
    except:        
        logger.error(categories)

    return categories


#load up all the category json plugins
def load_plugins():
    try:
        import os
        import os.path    

        pluginsDir = os.path.join(os.path.abspath(os.curdir),'config/plugins/categories')
        categoryPlugins = os.listdir(pluginsDir)

        for c in categoryPlugins:
            if ".json" in c:
                categoryInfoFile = open(os.path.join(pluginsDir,c))
                plugins[c.split(".json")[0]] = json.loads(categoryInfoFile.read())
                categoryInfoFile.close()
    except Exception, e:
        logger.exception(e)



if len(categories.keys()) == 0:
    load_categories()

if len(plugins.keys()) == 0:
    load_plugins()
