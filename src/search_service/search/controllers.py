import flask
import json
import requests
import logging

#import biokbase.workspace.client

from exceptions import InvalidSearchRequestError

def get_results(request, config):
    capture_metrics(request)

    # validate all of the required inputs
    validated = validate_inputs(request.args)
    validated['request'] = request.url

     # compute the solr url based on the user query
    computed_solr_url = compute_solr_query(validated, config['search']['solr_url'])
    
    logger.info(computed_solr_url)

    solr_results = dict()
    # call solr and retrieve result set
    try:
        if config['search']['solr_auth_required'] == True:
            response = requests.get(computed_solr_url, auth=requests.auth.HTTPBasicAuth(config['search']['solr_user'], config['search']['solr_pass']))
        else:
            response = requests.get(computed_solr_url)

        solr_results = response.json()
    except Exception, e:
        logger.error(computed_solr_url)
        logger.exception(e)
        raise

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

    # send it back to the client
    return response


def transform_solr_json(results, params):
    #logger.info(results)

    transform = dict()
    transform["items"] = list()
    
    for n in results["response"]["docs"]:
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
        if query['category'] not in config['plugins'].keys():
            raise InvalidSearchRequestError(query['category'] + " is not a valid search category.")
        
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
            
            if not field in config['plugins'][validatedParams['category']]['solr']['sort_fields']:
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
            
            if not field_name in config['plugins'][validatedParams['category']]['solr']['facet_fields']:
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
    headersString = ",".join([str(k) + " = " + str(request.headers[k]) for k in request.headers.keys()])
    
    logger.info("METRICS -- " + " URL : " + request.url + " HEADERS : " + headersString)


def compute_solr_query(options, base_solr_url = None):
    mapping = "search"
    paramString = ""

    solr_url = base_solr_url

    if config['plugins'].has_key(options['category']):
        core = config['plugins'][options['category']]['solr']['core']

        solr_url += mapping + '/' + core
        
        paramString = config['plugins'][options['category']]['solr']['query_string']
    else:
        raise InvalidSearchRequestError("No such category \"" + options['category'] + "\" !")

    solr_url += '/select?wt=json'

    paramString += "&start=" + str(options['start']) + "&rows=" + str(options['count'])


    # limit the output to the set of visible fields defined for this category
    solr_url += "&fl=" + ','.join(config['plugins'][options['category']]['solr']['visible_fields'])

    # add faceting options, if present
    if len(config['plugins'][options['category']]['solr']['facet_fields']) > 0:
        solr_url += "&facet=true"
        for x in config['plugins'][options['category']]['solr']['facet_fields']:
            solr_url += "&facet.field=" + x
        
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
            

    if config['plugins'][options['category']]['solr'].has_key('secure') and config['plugins'][options['category']]['solr']['secure'] == True:
        if not options.has_key('username') or options['username'] is None:
            raise InvalidSearchRequestError("Missing or invalid authentication token!")

        #workspace_url = "https://kbase.us/services/ws/"

        #workspace_service = workspaceClient.workspaceService(workspace_url)
        #workpace_service.list_workspaces({"auth_token": options['auth_token']})

    return solr_url


