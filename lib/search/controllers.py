import flask
import requests
import search.service
import logging
import search.exceptions

#import biokbase.workspace.client

from exceptions import InvalidSearchRequestError

logger = search.service.getLogger()

def get_results(request, config):
    capture_metrics(request)

    # validate all of the required inputs
    validated = validate_inputs(request.args, config)
    validated['request'] = request.url

     # compute the solr url based on the user query
    computed_solr_url = compute_solr_query(validated, config)
    
    logger.info(computed_solr_url)
    logger.info("CHECK")

    solr_results = dict()
    # call solr and retrieve result set
    try:
        if config['search']['solr_auth_required'] == True:
            response = requests.get(computed_solr_url, auth=requests.auth.HTTPBasicAuth(config['search']['solr_user'], config['search']['solr_pass']))
        else:
            response = requests.get(computed_solr_url)

        if response.status_code == requests.codes.ok:
            solr_results = response.json()
        else:
            raise search.exceptions.SolrError('Error connecting to solr: response code:' + str(response.status_code) +
                                              ' message=' + str(response.text))
    except Exception, e:
        logger.error(str(computed_solr_url))
        logger.exception(e)
        raise 

    try:
        # transform the json into the output format    
        results = transform_solr_json(solr_results, validated)
    except Exception, e:
         logger.exception(e)
         logger.info(solr_results)
         raise

    if validated.has_key("callback"):
        response = validated["callback"] + "(" + flask.json.dumps(results) + ")"
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
    
    if transform["itemsPerPage"] > 0:    
        if transform["totalResults"] % transform["itemsPerPage"] == 0:
            remainder = 0
        else:
            remainder = 1

    transform["navigation"] = dict()
    transform["navigation"]["self"] = params["request"]

    pageSplits = params["request"].split("page=")
    
    # no page parameter present in request url
    if len(pageSplits) == 1 and params["page"] == 1:
        transform["navigation"]["first"] = params["request"] + "&page=1"
        
        if (params["start"] + params["count"]) < results["response"]["numFound"]:
            transform["navigation"]["next"] = params["request"] + "&page=2"

        if params["count"] > 0:
            transform["navigation"]["last"] = params["request"] + "&page=" + str(transform["totalResults"]/transform["itemsPerPage"] + remainder)
    # page parameter present in request url
    elif len(pageSplits) == 2:
        startSubstring = pageSplits[1].find(str(params["page"]))
        pageSuffix = pageSplits[1][startSubstring:]
        
        transform["navigation"]["first"] = pageSplits[0] + "page=1" + pageSuffix        

        if params["page"] > 1:
            transform["navigation"]["previous"] = pageSplits[0] + "page=" + str(params["page"] - 1) + pageSuffix

        if (params["start"] + params["count"]) < results["response"]["numFound"]:
            transform["navigation"]["next"] = pageSplits[0] + "page=" + str(params["page"] + 1) + pageSuffix

        if params["count"] > 0:
            if transform["totalResults"] > 0:
                transform["navigation"]["last"] = pageSplits[0] + "page=" + str(transform["totalResults"]/transform["itemsPerPage"] + remainder) + pageSuffix
            else:
                transform["navigation"]["last"] = pageSplits[0] + "page=1" + pageSuffix

    # handle faceting
    if results.has_key("facet_counts"):
        transform["facets"] = results["facet_counts"]["facet_fields"]

    return transform


def validate_inputs(query, config):
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
        sortFields = sortQuery.split(',')
        
        outFields = list()
        
        for x in sortFields:
            try:
                field, order = x.split(' ')
            except:
                raise InvalidSearchRequestError(x + " is not in the format of 'sort_field sort_order'!")

            if not field in config['plugins'][validatedParams['category']]['solr']['sort_fields']:
                raise InvalidSearchRequestError(field + " is not a valid sorting field!")

            if not order in ['asc', 'desc']:
                raise InvalidSearchRequestError(order + " is not a valid sorting order!")                                                            
            
            if config['plugins'][validatedParams['category']]['solr'].has_key('mapped_sort_fields') and field in config['plugins'][validatedParams['category']]['solr']['mapped_sort_fields'].keys():
                outFields.append(config['plugins'][validatedParams['category']]['solr']['mapped_sort_fields'][field] + " " + order)
            else:
                outFields.append(field + " " + order)            
        
        validatedParams['sort'] = ",".join(outFields)

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
        default_query_field = None
        if 'default_query_field' in config['plugins'][query['category']]['solr']:
            default_query_field = config['plugins'][query['category']]['solr']['default_query_field']

        if default_query_field:
            validatedParams['userText'] = "&q=" + default_query_field + ':' + query['q']
        else:
            validatedParams['userText'] = "&q=" + query['q']
    else:
        validatedParams['userText'] = "&q=*"

    return validatedParams
            

def capture_metrics(request):
    headersString = ",".join([str(k) + " = " + str(request.headers[k]) for k in request.headers.keys()])
    
    logger.info("METRICS -- " + " URL : " + request.url + " HEADERS : " + headersString)


def compute_solr_query(options, config):
    paramString = ""
    facet_fields = ""

    solr_url = config['search']['solr_url']

    if config['plugins'].has_key(options['category']):
        core = config['plugins'][options['category']]['solr']['core']

        solr_url += '/' + core
        
        paramString = config['plugins'][options['category']]['solr']['query_string']

    else:
        raise InvalidSearchRequestError("No such category \"" + options['category'] + "\" !")

    solr_url += '/select?wt=json'

    paramString += "&start=" + str(options['start']) + "&rows=" + str(options['count'])


    # limit the output to the set of visible fields defined for this category
    solr_url += "&fl=" + ','.join(config['plugins'][options['category']]['solr']['visible_fields'])

    if options.has_key('sort') and options['sort'] is not None:
        paramString += "&sort=" + options['sort']
    #else:
    #    paramString += "&sort=score desc"

    # add faceting options, if present
    if len(config['plugins'][options['category']]['solr']['facet_fields']) > 0:
        solr_url += "&facet=true"

        if options.has_key('facets') and options['facets'] is not None:
            facetDict = dict()
            facetOrder = list()

            for x in options['facets'].split(','):
                facetKey, facetValue = x.split(":")
                if not facetDict.has_key(facetKey):
                    facetDict[facetKey] = facetValue.replace("*",",").replace("^",":")
                    facetOrder.append(facetKey)
                else:
                    facetDict[facetKey] += " OR " + facetValue.replace("*",",").replace("^", ":")

            for k in xrange(len(facetOrder)):    
                logger.info(facetDict[facetOrder[k]])
                facet_fields += "&facet.field={!ex=" + facetOrder[k] + "}" + facetOrder[k]
                paramString += "&fq={!tag=" + facetOrder[k] + "}" + facetOrder[k] + ":" + "(" + facetDict[facetOrder[k]] + ")"

            for x in config['plugins'][options['category']]['solr']['facet_fields']:
                if not facetDict.has_key(x):
                    facet_fields += "&facet.field={!ex=" + x + "}" + x
        else:
            for x in config['plugins'][options['category']]['solr']['facet_fields']:
                facet_fields += "&facet.field=" + x

    solr_url += facet_fields + options['userText'] + paramString

    if config['plugins'][options['category']]['solr'].has_key('secure') and config['plugins'][options['category']]['solr']['secure'] == True:
        if not options.has_key('username') or options['username'] is None:
            raise InvalidSearchRequestError("Missing or invalid authentication token!")

    print('SOLR REQUEST:' + str(solr_url))
    return solr_url


